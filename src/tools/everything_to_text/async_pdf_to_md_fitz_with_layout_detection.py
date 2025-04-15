"""
异步版PDF转Markdown工具 - PyMuPDF实现

该模块提供了基于PyMuPDF(fitz)的PDF转Markdown异步处理功能：
1. 使用异步编程模型加速处理流程
2. 并行处理多个PDF页面
3. 集成版面分析技术识别文档结构
4. 异步提取和处理图像内容
5. 支持缓存机制减少重复处理

相比同步版本，此模块在处理多页PDF或包含大量图像的文档时
具有显著的性能优势。特别适合批量处理大型PDF文档。
"""

import hashlib
import os
import pymupdf as pm
import re
import time
import asyncio
from typing import List, Any, Union, Tuple, Dict
from pathlib import Path

# 导入版面分析相关模块
from src.tools.everything_to_text.layout_detection import  init_layout_model
from src.tools.everything_to_text.async_image_processing import (
    page2image,
    sort_page_layout,
    extract_images_from_layout_async
)

# 导入缓存相关模块
from src.tools.cached_db.data_store import get_image_store, get_pdf_cache

"""
PDF内容提取工具 (异步版本)

这个脚本用于从PDF文件中提取文本内容和图像，并生成Markdown文档。
使用异步处理来加速图像描述和标题生成。
"""

# 初始化版面分析模型
def init_models():
    """
    初始化版面分析模型
    
    尝试加载并初始化版面检测模型，如果初始化失败则终止程序。
    版面分析是本模块的核心功能，没有它无法正常工作。
    
    Raises:
        SystemExit: 当模型初始化失败时退出程序
    """
    try:
        init_layout_model()
    except Exception as e:
        print(f"版面分析模型初始化失败: {e}")
        exit(1)

# 定义图像标签集
image_labels = {"image", "seal", "chart", "header_image", "footer_image"}

def save_as_markdown(page_texts, output_dir):
    """
    保存提取的内容为Markdown文件
    Args:
        page_texts (dict): 包含每页文本内容的字典
        output_dir (str/Path): 输出目录
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / "extracted_content.md"
    
    markdown_content = []
    for page_num in sorted(page_texts.keys()):
        page_data = page_texts[page_num]
        if isinstance(page_data, dict):
            markdown_content.append(page_data['text'])
    
    with open(output_path, "w", encoding="utf-8") as md_file:
        md_file.write("\n\n".join(markdown_content))
    
    return output_path

def extract_text_and_render_page(pdf_document, page_num, output_dir, strip_references):
    """
    从PDF中提取页面文本并渲染页面图像
    
    Args:
        pdf_document: PDF文档对象
        page_num: 页码
        output_dir: 输出目录
        strip_references: 是否检查参考文献
        
    Returns:
        tuple: (页面文本, 渲染图像路径)
    """
    # 获取当前页面对象
    page = pdf_document[page_num]
    
    # 提取当前页面的文本内容
    text = page.get_text()
    
    # 渲染页面为图像
    dpi = 300  # 默认DPI
    zoom_factor = dpi / 72.0  # 将DPI转换为缩放因子
    image_filename = f"page_{page_num + 1}_highres.png"
    image_path = os.path.join(output_dir, image_filename)
    
    # 渲染页面为高分辨率图像
    rendered_image_path = page2image(page, image_path, zoom_factor)
    
    return text, rendered_image_path

async def process_page_async(pdf_document,
                      page_num,
                      output_dir,
                      image_labels,
                      strip_references, 
                      image_store=None,
                      api_key=None):
    """
    异步处理单页PDF - 提取文本和渲染图像，然后处理图像
    
    Args:
        pdf_document: PDF文档对象
        page_num: 页码
        output_dir: 输出目录
        image_labels: 图像标签集
        strip_references: 是否检查参考文献
        image_store: 图像存储对象
        api_key: API密钥，用于模型调用

    Returns:
        dict: 包含文本和图像路径的字典
    """
    print(f"异步处理第 {page_num + 1} 页...")
    
    # 第一阶段：提取文本并渲染页面
    text, rendered_image_path = extract_text_and_render_page(
        pdf_document, page_num, output_dir, strip_references
    )
    
    # 第二阶段：处理渲染的图像并进行版面分析
    layout_result = sort_page_layout(rendered_image_path, output_dir, page_num)
    
    # 第三阶段：异步提取图像和生成描述
    image_markdown = await extract_images_from_layout_async(
        layout_result=layout_result,
        rendered_image_path=rendered_image_path,
        output_dir=output_dir,
        image_labels=image_labels,
        image_store=image_store,
        api_key=api_key
    )

    # 将图像Markdown添加到文本上方
    enhanced_text = image_markdown + text

    # 返回处理结果
    return {
        'text': enhanced_text,
        'image': rendered_image_path
    }

async def extract_pdf_content_async(pdf_path, 
                            output_dir, 
                            strip_references=False, 
                            generate_markdown=True,
                            api_key=None,
                            db_root_dir=None):
    """
    异步从PDF中提取文本内容和每页的图像，并使用版面分析处理图像
    Args:
        pdf_path (str): PDF文件路径
        output_dir (str): 输出目录
        strip_references (bool): 是否在检测到参考文献部分后停止处理
        generate_markdown (bool): 是否生成Markdown文件
        api_key (str): API密钥，用于模型调用
        db_root_dir (str, optional): 数据库根目录，如不指定则使用默认路径
    Returns:
        dict: 包含文本内容、元数据的字典
    """
    # 使用pymupdf库打开PDF文件
    pdf_document = pm.open(pdf_path)
    
    # 创建一个字典，用于存储每页的文本内容
    page_texts = {}
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 初始化集中式图片存储数据库
    image_store = get_image_store(db_root_dir)
    
    # 获取PDF文件名
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    print(f"使用图像存储进行异步处理PDF: {pdf_name}")
    
    total_pages = len(pdf_document)
    print(f"开始处理PDF：共 {total_pages} 页")
    
    # 创建任务列表，每页并行处理
    tasks = [
        process_page_async(
            pdf_document=pdf_document,
            page_num=page_num,
            output_dir=output_dir,
            image_labels=image_labels,
            strip_references=strip_references,
            image_store=image_store,
            api_key=api_key
        )
        for page_num in range(total_pages)
    ]
    
    # 并行等待所有页面处理完成
    results = await asyncio.gather(*tasks)
    
    # 将结果存储到字典中
    for page_num, result in enumerate(results):
        page_texts[page_num + 1] = result
    
    # 处理完毕后关闭PDF文档
    pdf_document.close()
    
    # 如果需要，生成Markdown文件
    if generate_markdown and page_texts:
        markdown_path = save_as_markdown(page_texts, output_dir)
        print(f"已生成Markdown文件: {markdown_path}")
    
    result = {
        "text_content": "\n\n".join([page_data['text'] for page_num, page_data in sorted(page_texts.items()) if isinstance(page_data, dict)]),
        "metadata": {},
        "images": [],
    }
    
    return result

async def async_fitz_pdf2md(
    file_path: str,
    llm_client: Any = None,
    llm_model: str = None,
    config: Dict = None,
    ocr_enabled: bool = False,
) -> Dict:
    """将PDF文件转换为Markdown的异步版本，兼容注册转换器接口"""
    # 版面分析模型只需要初始化一次
    init_models()
    
    # 配置参数
    strip_references = True
    db_root_dir = None
    api_key = None

    # 从config中获取参数（如果有）
    if config:
        if 'strip_references' in config:
            strip_references = config['strip_references']
        if 'db_root_dir' in config:
            db_root_dir = config['db_root_dir']
        if 'api_key' in config:
            api_key = config['api_key']
    

    if config and 'output_dir' in config:
        output_dir = config['output_dir']
    else:
        # 获取文件名（不含扩展名）用作目录名
        pdf_name = os.path.splitext(os.path.basename(file_path))[0]
        output_dir = os.path.join(os.getcwd(), "outputs", pdf_name)
    
    # 获取文件名（不含扩展名）
    pdf_name = os.path.splitext(os.path.basename(file_path))[0]
    
    # 检查是否有缓存，传递数据库路径
    pdf_cache = get_pdf_cache(db_root_dir)
    
    # 生成用于缓存查询的URL
    url = f"file://{file_path}"
    if config and 'url' in config:
        url = config['url']  # 如果提供了URL，使用传入的URL
    
    # 尝试从缓存获取结果
    md_content = pdf_cache.get_pdf(url)
    
    if md_content:
        print(f"缓存命中，直接返回缓存的Markdown内容")
        # 如果缓存存在，直接返回缓存的内容
        return {
            "text_content": md_content,
            "metadata": {},
            "images": []   
        }
    else:
        print(f"缓存未命中，开始处理PDF文件: {pdf_name}")

    # 记录开始处理时间
    start_time = time.time()

    # 异步调用PDF提取函数
    result = await extract_pdf_content_async(
        pdf_path=file_path,
        output_dir=output_dir,
        strip_references=strip_references,
        generate_markdown=True,
        api_key=api_key,
        db_root_dir=db_root_dir,  # 传递数据库路径
    )
        
    # 保存到缓存
    pdf_cache.save_pdf(
        url=url,
        md_content=result["text_content"],
    )

    # 计算总处理时间
    end_time = time.time()
    total_duration = end_time - start_time
    print(f"PDF异步转换完成，总处理耗时: {total_duration:.2f}秒")
    return result

def sync_fitz_pdf2md(
    file_path: str,
    llm_client: Any = None,
    llm_model: str = None,
    config: Dict = None,
    ocr_enabled: bool = False,
) -> Dict:
    """同步版本的PDF转Markdown函数"""
    result =asyncio.run(async_fitz_pdf2md(
        file_path=file_path,
        llm_client=llm_client,
        llm_model=llm_model,
        config=config,
        ocr_enabled=ocr_enabled
    ))
    print("同步PDF转Markdown完成")

    return result

async def main():
    """异步主函数"""
    pdf_file = "test_pdf_to_md_pdfplumber.pdf"  # PDF文件路径
    output_directory = "extracted_content"  # 输出目录

    # 配置提取选项
    strip_refs_option = True      # 是否忽略参考文献后的内容

    # 异步提取PDF内容并生成Markdown
    # 直接 await 异步函数，而不是调用同步包装器
    result = await async_fitz_pdf2md(
        pdf_file,
        config={
            'output_dir': output_directory,
            'strip_references': strip_refs_option,
        }
    )

    # 显示结果摘要
    print(f"结果已保存在目录: {result}")

if __name__ == "__main__":
    asyncio.run(main())
