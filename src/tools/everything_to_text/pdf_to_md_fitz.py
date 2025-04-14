import hashlib
import os
import pymupdf as pm
import re
import time
from typing import List, Any, Union, Tuple, Dict

from pathlib import Path

# 移除缓存相关模块
# from src.tools.cached_db.data_store import get_pdf_cache # 移除 get_image_store


"""
PDF内容提取工具 (简化版)

这个脚本用于从PDF文件中提取文本内容，并生成Markdown文档。
移除了图像提取和版面分析功能。
"""

def save_as_markdown(page_texts, output_dir):
    """
    保存提取的内容为Markdown文件
    Args:
        page_texts (dict): 包含每页文本内容的字典 {page_num: text}
        output_dir (str/Path): 输出目录
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "extracted_content.md"

    markdown_content = []
    # 直接使用 page_texts 的值（文本）
    for page_num in sorted(page_texts.keys()):
        markdown_content.append(page_texts[page_num])

    with open(output_path, "w", encoding="utf-8") as md_file:
        md_file.write("\n\n".join(markdown_content))

    return output_path

def extract_pdf_content(pdf_path, output_dir, strip_references=False,
                       generate_markdown=True):
    """
    从PDF中提取文本内容
    Args:
        pdf_path (str): PDF文件路径
        output_dir (str): 输出目录
        strip_references (bool): 是否在检测到参考文献部分后停止处理
        generate_markdown (bool): 是否生成Markdown文件
    Returns:
        dict: 包含文本内容的字典
    """
    # 使用pymupdf库打开PDF文件
    try:
        pdf_document = pm.open(pdf_path)
    except Exception as e:
        print(f"打开PDF文件失败: {pdf_path}, 错误: {e}")
        return {"text_content": "", "metadata": {}, "images": []} # 保持接口一致性

    # 创建一个字典，用于存储每页的文本内容
    page_texts = {}

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    print(f"开始处理PDF: {pdf_name}")

    total_pages = len(pdf_document)
    print(f"共 {total_pages} 页")

    references_found = False # 添加标志位
    # 遍历PDF中的每一页
    for page_num in range(total_pages):
        print(f"处理第 {page_num + 1}/{total_pages} 页...")

        # 直接提取文本
        page = pdf_document[page_num]
        current_page_text = page.get_text()

        # 如果启用了 strip_references，检查当前页是否包含参考文献标题
        if strip_references:
            # 使用正则表达式查找以 "References" 或 "参考文献" 开头的行（忽略大小写和前后空格，多行模式）
            match = re.search(r"^\s*(References|参考文献)\s*$", current_page_text, re.IGNORECASE | re.MULTILINE)

            if match:
                keyword = match.group(1) # 获取匹配到的关键词
                print(f"在第 {page_num + 1} 页检测到 '{keyword}'。")
                # 获取匹配行的起始位置
                reference_start_index = match.start()
                # 截断当前页的文本内容，只保留匹配关键词之前的部分
                current_page_text = current_page_text[:reference_start_index].rstrip() # 使用 rstrip() 移除末尾可能多余的换行符
                references_found = True
                # 存储截断后的页面内容
                page_texts[page_num + 1] = current_page_text
                print(f"已移除第 {page_num + 1} 页 '{keyword}' 及其之后的内容，并停止处理后续页面。")
                break # 跳出循环

        # 如果没有找到参考文献，或者未启用 strip_references，正常存储页面内容
        if not references_found:
            page_texts[page_num + 1] = current_page_text

    # 处理完毕后关闭PDF文档
    pdf_document.close()

    # 如果需要，生成Markdown文件
    if generate_markdown and page_texts:
        markdown_path = save_as_markdown(page_texts, output_dir)
        print(f"已生成Markdown文件: {markdown_path}")

    # 准备结果 - 移除 images 字段，保持接口一致性
    result = {
        "text_content": "\n\n".join([text for page_num, text in sorted(page_texts.items())]),
        "metadata": {},
        "images": [], # 返回空列表以保持接口兼容性
    }

    return result


# fitz_pdf2md函数,是用来适配外部调用的接口的，不能动传递方式
def fitz_pdf2md(
    file_path: str,
    # 移除 llm_client, llm_model, ocr_enabled 参数
    config: Dict = None,
) -> Dict:
    """将PDF文件转换为Markdown (纯文本提取)，兼容注册转换器接口"""
    # 移除模型初始化调用

    # 配置参数 - 移除 dpi, enable_image_desc, db_root_dir
    strip_references = True

    # 从config中获取参数（如果有）
    if config:
        if 'strip_references' in config:
            strip_references = config['strip_references']
        # 移除 db_root_dir 处理

    # 确定输出目录
    output_dir = None
    if config and 'output_dir' in config:
        output_dir = config['output_dir']
    else:
        pdf_name = os.path.splitext(os.path.basename(file_path))[0]
        output_dir = os.path.join(os.getcwd(), "outputs", pdf_name)

    # 移除缓存检查逻辑
    # pdf_cache = get_pdf_cache(db_root_dir)
    # url = f"file://{file_path}"
    # if config and 'url' in config:
    #     url = config['url']
    # md_content = pdf_cache.get_pdf(url)
    # if md_content:
    #     print(f"缓存命中，直接返回缓存的Markdown内容")
    #     return {
    #         "text_content": md_content,
    #         "metadata": {},
    #         "images": []
    #     }

    # 记录开始处理时间
    start_time = time.time()

    # 调用简化的提取函数 - 移除 dpi
    result = extract_pdf_content(
        file_path,
        output_dir,
        strip_references=strip_references,
        generate_markdown=True,
    )

    # 移除保存到缓存的逻辑
    # pdf_cache.save_pdf(
    #     url=url,
    #     md_content=result["text_content"],
    # )

    # 计算总处理时间
    end_time = time.time()
    total_duration = end_time - start_time
    print(f"PDF文本提取完成，总处理耗时: {total_duration:.2f}秒")
    return result


def main():
    pdf_file = "test_pdf_to_md_pdfplumber.pdf"  # PDF文件路径
    output_directory = "extracted_content_text_only"  # 输出目录

    # 配置提取选项 - 移除 dpi, enable_image_desc
    strip_refs_option = True      # 是否忽略参考文献后的内容

    # 提取PDF内容并生成Markdown
    result = fitz_pdf2md(
        pdf_file,
        config={'output_dir': output_directory,
            'strip_references': strip_refs_option,
        }
    )

    # 显示结果摘要
    print(f"\n提取的文本内容:\n{result['text_content'][:500]}...") # 显示部分文本
    print(f"\n结果已保存在目录: {output_directory}")

if __name__ == "__main__":
    main()
