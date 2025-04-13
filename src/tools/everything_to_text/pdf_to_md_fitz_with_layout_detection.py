import hashlib
import os
import pymupdf as pm
import re
import time
from typing import List, Any, Union, Tuple, Dict
from src.tools.everything_to_text.layout_detection import LayoutDetector, LayoutSorter, init_layout_model
from src.tools.everything_to_text.layout_detection.image_processing import normalize_coordinates, crop_image, \
    page2image, extract_images_from_layout,  sort_page_layout

from pathlib import Path

# 导入缓存相关模块
from src.tools.cached_db.data_store import get_image_store, get_pdf_cache


"""
PDF内容提取工具 (简化版)

这个脚本用于从PDF文件中提取文本内容和图像，并生成Markdown文档。

"""

# 初始化版面分析模型
def init_models():
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

def process_rendered_image(rendered_image_path, 
                           output_dir,
                           page_num, 
                           image_labels, 
                           image_store):
    """
    处理已渲染的页面图像，进行版面分析和图像提取
    
    Args:
        rendered_image_path: 已渲染的页面图像路径
        output_dir: 输出目录
        image_output_dir: 图像输出目录
        page_num: 页码
        image_labels: 图像标签集
        image_store: 图像存储对象
        
    Returns:
        str: 图像Markdown文本
    """
    # 版面分析
    layout_result = sort_page_layout(rendered_image_path, output_dir, page_num)

    # 提取图像内容
    image_markdown = extract_images_from_layout(
        layout_result, rendered_image_path, output_dir, image_labels, image_store
    )
    
    return image_markdown

def process_page(pdf_document,
                 page_num,
                 output_dir,
                 image_output_dir, 
                 image_labels,
                 strip_references, 
                 image_store=None
                ):
    """
    处理单页PDF - 提取文本和渲染图像，然后处理图像
    
    Args:
        pdf_document: PDF文档对象
        page_num: 页码
        output_dir: 输出目录
        image_output_dir: 图像输出目录
        image_labels: 图像标签集
        dpi: 渲染分辨率
        strip_references: 是否检查参考文献
        image_store: 图像存储对象

    Returns:
        dict: 包含文本和图像路径的字典
    """
    # 第一阶段：提取文本并渲染页面
    text, rendered_image_path = extract_text_and_render_page(
        pdf_document, page_num, output_dir, strip_references
    )
    
    # 第二阶段：处理渲染的图像
    image_markdown = process_rendered_image(
        rendered_image_path, output_dir, page_num, image_labels, image_store
    )

    # 将图像Markdown添加到文本上方
    enhanced_text = image_markdown + text

    # 返回处理结果
    return {
        'text': enhanced_text,
        'image': rendered_image_path
    }

def extract_pdf_content(pdf_path, output_dir, dpi=300, strip_references=False, 
                       generate_markdown=True,
                       db_root_dir=None):
    """
    从PDF中提取文本内容和每页的图像，并使用版面分析处理图像
    Args:
        pdf_path (str): PDF文件路径
        output_dir (str): 输出目录
        dpi (int): 渲染图像的分辨率
        strip_references (bool): 是否在检测到参考文献部分后停止处理
        generate_markdown (bool): 是否生成Markdown文件
        enable_image_desc (bool): 是否启用图片描述功能
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
    
    # 创建图片输出目录
    image_output_dir = os.path.join(output_dir, "images")
    os.makedirs(image_output_dir, exist_ok=True)
    
    # 初始化集中式图片存储数据库
    image_store = get_image_store(db_root_dir)
    
    # 获取PDF文件名
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    print(f"使用图像存储进行处理PDF: {pdf_name}")
    

    total_pages = len(pdf_document)
    print(f"开始处理PDF：共 {total_pages} 页")
    
    references_found = False # 添加标志位
    # 遍历PDF中的每一页
    for page_num in range(total_pages):
        print(f"处理第 {page_num + 1}/{total_pages} 页...")
        
        # 处理当前页面
        page_content = process_page(
            pdf_document, 
            page_num,
            output_dir,
            image_output_dir, 
            image_labels,
            strip_references,
            image_store
        )
        
        # 如果启用了 strip_references，检查当前页是否包含参考文献标题
        if strip_references and isinstance(page_content, dict) and 'text' in page_content:
            # 使用正则表达式查找以 "References" 或 "参考文献" 开头的行（忽略大小写和前后空格，多行模式）
            # ^ 匹配行首, \s* 匹配零个或多个空白字符, $ 匹配行尾, | 表示或
            match = re.search(r"^\s*(References|参考文献)\s*$", page_content['text'], re.IGNORECASE | re.MULTILINE)
            
            if match:
                keyword = match.group(1) # 获取匹配到的关键词 (References 或 参考文献)
                print(f"在第 {page_num + 1} 页检测到 '{keyword}'。")
                # 获取匹配行的起始位置
                reference_start_index = match.start()
                # 截断当前页的文本内容，只保留匹配关键词之前的部分
                page_content['text'] = page_content['text'][:reference_start_index].rstrip() # 使用 rstrip() 移除末尾可能多余的换行符
                references_found = True
                # 存储截断后的页面内容
                page_texts[page_num + 1] = page_content
                print(f"已移除第 {page_num + 1} 页 '{keyword}' 及其之后的内容，并停止处理后续页面。")
                break # 跳出外层循环 (page loop)

        # 如果没有找到参考文献，或者未启用 strip_references，正常存储页面内容
        if not references_found:
            page_texts[page_num + 1] = page_content
        
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
    


# fitz_pdf2md函数,是用来适配外部调用的接口的，不能动传递方式
def fitz_pdf2md(
    file_path: str,
    llm_client: Any = None,
    llm_model: str = None,
    config: Dict = None,
    ocr_enabled: bool = False,
) -> Dict:
    """将PDF文件转换为Markdown，兼容注册转换器接口"""
    # 版面分析模型只需要初始化一次
    init_models()
    
    # 配置参数
    dpi = 300
    strip_references = True
    db_root_dir = None

    
    # 从config中获取参数（如果有）
    if config:
        if 'dpi' in config:
            dpi = config['dpi']
        if 'strip_references' in config:
            strip_references = config['strip_references']
        if 'enable_image_desc' in config:
            enable_image_desc = config['enable_image_desc']
        if 'db_root_dir' in config:
            db_root_dir = config['db_root_dir']

    
    # 确定输出目录
    output_dir = None
    
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

    # 记录开始处理时间
    start_time = time.time()

    result = extract_pdf_content(
        file_path,
        output_dir,
        dpi=dpi,
        strip_references=strip_references,
        generate_markdown=True,
        db_root_dir=db_root_dir,  # 传递数据库路径
    )
        
    # 保存到缓存 - 适配修改后的接口，不再传递output_dir参数
    pdf_cache.save_pdf(
        url=url,
        md_content=result["text_content"],
    )

    # 计算总处理时间
    end_time = time.time()
    total_duration = end_time - start_time
    print(f"PDF转换完成，总处理耗时: {total_duration:.2f}秒")
    return result


def main():
    pdf_file = "test_pdf_to_md_pdfplumber.pdf"  # PDF文件路径
    output_directory = "extracted_content"  # 输出目录

    # 配置提取选项
    dpi_option = 300              # 渲染分辨率
    strip_refs_option = True      # 是否忽略参考文献后的内容
    enable_image_desc = True      # 启用图片描述功能

    # 提取PDF内容并生成Markdown
    result = fitz_pdf2md(
        pdf_file,
        config={'output_dir': output_directory,'dpi': dpi_option,
            'strip_references': strip_refs_option,
            'enable_image_desc': enable_image_desc
        }
    )

    # 显示结果摘要
    print(f"结果已保存在目录: {output_directory}")

if __name__ == "__main__":
    main()
