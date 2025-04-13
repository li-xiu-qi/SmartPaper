"""
图片处理模块

提供处理Markdown中图片引用的功能，将图片引用替换为base64编码的内嵌图片。
"""

import os
import re
import traceback
from loguru import logger
from src.tools.cached_db.data_store import get_image_store

def process_markdown_images(markdown_content: str, pdf_name: str) -> str:
    """
    处理Markdown内容中的图片引用，将其替换为base64编码的内嵌图片
    
    Args:
        markdown_content (str): 包含图片引用的Markdown内容
        output_dir (str): 输出目录路径，不再用于定位图片数据库，仅用于日志记录
        pdf_name (str): PDF文件名（不含扩展名），用于查询特定PDF的图片
    
    Returns:
        str: 处理后的Markdown内容，其中图片引用已替换为base64编码
    """
    # 如果内容为空，直接返回
    if not markdown_content:
        return markdown_content
        
    # 获取集中式图片数据库实例
    try:
        image_store = get_image_store()
        
        # 获取指定PDF的所有图片的base64数据
        all_images = image_store.get_all_images(pdf_name)
        
        if not all_images:
            logger.warning(f"数据库中没有PDF {pdf_name} 的图片数据")
            return markdown_content
            
        # 正则表达式匹配Markdown图片引用格式，更加宽松的匹配模式
        # 考虑到可能跨行的情况和特殊格式
        img_pattern = r'!\[(.*?)\]\((.*?)\)'
        
        def replace_with_base64(match):
            alt_text = match.group(1)  # 图片替代文本
            img_path = match.group(2)  # 图片路径
            
            # 去除可能存在的空格
            img_path = img_path.strip()
            # img_path 一般是["images/key.jpg"]或者["images\key.jpg"]格式，我们需要提取文件名作为key
            image_key = os.path.basename(img_path) # 使用os.path.basename处理不同平台的路径分隔符
            base64_data = image_store.get_image(image_key)
            
            # 确定图片MIME类型（假设是jpg格式）
            mime_type = "image/jpeg"
            
            # 创建内嵌的base64图片引用
            return f'<br><img src="data:{mime_type};base64,{base64_data}" alt="{alt_text}" style="max-width: 50%;"><br>'
        
        # 替换所有图片引用
        processed_content = re.sub(img_pattern, replace_with_base64, markdown_content)
        return processed_content
        
    except Exception as e:
        logger.error(f"处理Markdown图片时出错: {e}")
        logger.error(traceback.format_exc())
        # 出错时返回原内容，确保不会丢失信息
        return markdown_content


def find_and_replace_image_in_stream(chunk: str,
                                     img_ref_buffer: str, 
                                     collecting_img_ref: bool, 
                                    pdf_info: dict) -> tuple:
    """
    在流式输出的块中查找并替换图片引用
    
    Args:
        chunk (str): 当前接收到的内容块
        img_ref_buffer (str): 当前已收集的图片引用缓冲区
        collecting_img_ref (bool): 是否正在收集图片引用
        pdf_info (dict): PDF信息，包含pdf_name用于查询图片
    
    Returns:
        tuple: (处理后的内容, 更新后的img_ref_buffer, 更新后的collecting_img_ref状态)
    """
    processed_text = ""
    i = 0
    
    while i < len(chunk):
        char = chunk[i]
        
        # 检测图片引用开始标记
        if not collecting_img_ref and char == '!':
            # 查看下一个字符，确认是否是图片引用开始
            if i + 1 < len(chunk) and chunk[i + 1] == '[':
                collecting_img_ref = True
                img_ref_buffer = '!'
                i += 1
                continue
        
        # 正在收集图片引用
        if collecting_img_ref:
            img_ref_buffer += char
            
            # 检测图片引用结束
            if char == ')':
                # 使用正则检查是否是完整的图片引用
                if re.match(r'!\[.*?\]\(.*?\)', img_ref_buffer):
                    # 找到完整的图片引用，准备替换为base64
                    if pdf_info and "pdf_name" in pdf_info:
                        try:
                            # 从img_ref_buffer中提取图片信息
                            img_match = re.match(r'!\[(.*?)\]\((.*?)\)', img_ref_buffer)
                            if img_match:
                                alt_text = img_match.group(1).strip()
                                img_path = img_match.group(2).strip()
                                # img_path 一般是["images/key.jpg"]或者["images\key.jpg"]格式，我们需要提取文件名作为key
                                image_key = os.path.basename(img_path) # 使用os.path.basename处理不同平台的路径分隔符
                                logger.debug(f"流式处理找到图片引用，尝试获取key: {image_key}")
                                
                                # 获取图片数据库实例
                                image_store = get_image_store()
                                pdf_name = pdf_info["pdf_name"] # pdf_name 暂时未使用，但保留以备将来可能需要区分不同PDF
                                
                                # 直接尝试获取指定key的图片base64数据
                                base64_data = image_store.get_image(image_key)
                                
                                if base64_data:
                                    logger.debug(f"成功获取图片 {image_key} 的base64数据")
                                    # 创建base64图片引用
                                    # 默认图片格式为jpg
                                    mime_type = "image/jpeg" 
                                    processed_text += f'<br><img src="data:{mime_type};base64,{base64_data}" alt="{alt_text}" style="max-width: 50%;"><br>'
                                else:
                                    # 没有找到对应的图片数据，保留原引用
                                    logger.warning(f"在数据库中未找到图片key: {image_key}，保留原始引用")
                                    processed_text += img_ref_buffer
                            else:
                                # 正则匹配失败，保留原引用
                                logger.warning(f"无法从缓冲区解析图片引用: {img_ref_buffer}")
                                processed_text += img_ref_buffer
                        except Exception as e:
                            logger.error(f"流式处理图片引用失败: {e}")
                            logger.error(traceback.format_exc())
                            processed_text += img_ref_buffer
                    else:
                        # 没有PDF名称信息，保留原引用
                        logger.warning("缺少pdf_info或pdf_name，无法处理图片引用")
                        processed_text += img_ref_buffer
                    
                    # 重置图片引用收集状态
                    collecting_img_ref = False
                    img_ref_buffer = ""
                else:
                    # 可能是伪图片引用或不完整的图片引用，继续收集更多字符
                    pass
            elif len(img_ref_buffer) > 500:  # 设置最大缓冲区大小，防止内存溢出
                # 图片引用过长，可能是错误格式，放弃收集
                processed_text += img_ref_buffer
                collecting_img_ref = False
                img_ref_buffer = ""
        else:
            # 不在收集图片引用状态，直接添加字符到输出
            processed_text += char
        
        i += 1
    
    return processed_text, img_ref_buffer, collecting_img_ref

