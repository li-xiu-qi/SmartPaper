import base64
import hashlib
import os
import time
import uuid
import asyncio
from typing import List, Any, Union, Tuple, Dict
from PIL import Image
import pymupdf as pm

# 导入异步版本的图像处理函数
from src.tools.everything_to_text.async_image_to_text import (
    describe_image_async, 
    get_image_title_async,
)
from src.tools.everything_to_text.layout_detection import LayoutDetector, LayoutSorter

"""
图像处理相关功能(异步版本)
包含：坐标处理、图像裁剪、PDF页面渲染、异步图像描述生成等功能
"""

def normalize_coordinates(coordinates: Any) -> List[Tuple[int, int]]:
    """
    标准化坐标格式为点列表[(x1,y1), (x2,y2)]
    
    Args:
        coordinates: 输入的坐标，可能有多种格式
        
    Returns:
        标准化后的坐标点列表
    """
    if len(coordinates) == 4:
        # 格式: [x1, y1, x2, y2]
        x1, y1, x2, y2 = map(int, coordinates)
        return [(x1, y1), (x2, y2)]
        
    elif len(coordinates) == 2:
        # 检查是否为点列表格式 [[x1,y1], [x2,y2]]
        if all(isinstance(p, (list, tuple)) and len(p) == 2 for p in coordinates):
            return [(int(coordinates[0][0]), int(coordinates[0][1])), 
                    (int(coordinates[1][0]), int(coordinates[1][1]))]
        elif all(isinstance(p, (int, float)) for p in coordinates):
            # 可能是 [x, y] 单点格式
            x, y = map(int, coordinates)
            # 创建一个小区域
            return [(x, y), (x + 100, y + 100)]
    
    raise ValueError(f"无法识别的坐标格式: {coordinates}")
        

def crop_image(
    image_path: str, box_coordinates: Any, return_image_path: bool = True, output_filename: str = None
) -> Union[str, Image.Image]:
    """
    根据坐标裁剪图像区域
    
    Args:
        image_path: 图像文件路径
        box_coordinates: 裁剪框坐标
        return_image_path: 是否返回保存后的图像路径，否则返回图像对象
        output_filename: 输出文件名(包含后缀)，若提供则使用该名称，否则自动生成
    
    Returns:
        裁剪后的图像路径或图像对象
    """
    image = Image.open(image_path)
    
    # 标准化坐标格式
    points = normalize_coordinates(coordinates=box_coordinates)
    
    # 将坐标转换为矩形边界框
    x_coordinates = [point[0] for point in points]
    y_coordinates = [point[1] for point in points]
    
    left, top = min(x_coordinates), min(y_coordinates)
    right, bottom = max(x_coordinates), max(y_coordinates)
    
    # 确保坐标有效
    width, height = image.size
    left = max(0, left)
    top = max(0, top)
    right = min(width, right)
    bottom = min(height, bottom)
    
    # 裁剪图像
    cropped = image.crop((left, top, right, bottom))
    
    if return_image_path:
        # 保存裁剪后的图像
        output_dir = "output/crops"
        os.makedirs(output_dir, exist_ok=True)
        
        # 使用指定文件名(保持原样，包括后缀)或生成基于时间戳的文件名
        if output_filename:
            cropped_path = os.path.join(output_dir, output_filename)
        else:
            timestamp = int(time.time() * 1000)
            cropped_path = os.path.join(output_dir, f"cropped_image_{timestamp}.jpg")
            
        cropped.save(cropped_path)
        print(f"裁剪后的图像已保存至: {cropped_path}")
        # 返回裁剪后的图像地址
        return cropped_path
    return cropped

def page2image(page, output_path, zoom_factor=4.0):
    """
    将PDF页面渲染为图像并保存
    
    Args:
        page: PyMuPDF页面对象
        output_path: 输出图像的完整路径
        zoom_factor: 渲染的缩放因子，默认为4.0（相当于约288 DPI）
        
    Returns:
        str: 保存的图像路径
    """
    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 使用缩放因子创建变换矩阵
    mat = pm.Matrix(zoom_factor, zoom_factor)
    
    # 创建像素图并保存
    pix = page.get_pixmap(matrix=mat, alpha=False)
    pix.save(output_path)
    
    print(f"已保存图像: {output_path}")
    
    return output_path


def sort_page_layout(rendered_image_path, output_dir, page_num):
    """
    分析页面布局并返回排序后的结果

    Args:
        rendered_image_path: 渲染后的页面图像路径
        output_dir: 输出目录
        page_num: 页码

    Returns:
        dict: 版面分析结果
    """

    # 文档版面分析
    detector = LayoutDetector()
    layout_result = detector.detect_layout(
        image_path=rendered_image_path,
        output_path=os.path.join(output_dir, f"layout_detection_page_{page_num + 1}.json"),
    )

    sorter = LayoutSorter()
    
    return sorter.sort_layout(layout_result=layout_result, image_path=rendered_image_path)


async def process_image_box_async(box, rendered_image_path, output_dir, image_store=None, api_key=None):
    """
    异步处理单个图像框 - 进行图像提取和保存，返回图像信息
    
    Args:
        box: 图像框信息
        rendered_image_path: 渲染后的页面图像路径
        output_dir: 图像输出目录
        image_store: 图像存储对象
        api_key: API密钥，用于模型调用
        
    Returns:
        dict: 图像信息字典
    """
    coordinate = box["coordinate"]
    
    # 使用UUID生成更短的唯一文件名
    image_filename = f"{uuid.uuid4().hex}.jpg"
    
    # 裁剪图片，直接使用UUID生成的文件名
    cropped_image_path = crop_image(
        image_path=rendered_image_path, 
        box_coordinates=coordinate, 
        return_image_path=True,
        output_filename=image_filename
    )
    
    # 获取图片名(带扩展名)
    image_name = os.path.basename(cropped_image_path)
    images_dir = os.path.join(output_dir, "images")
    new_image_path = os.path.join(images_dir, image_name)
    
    # 确保输出目录存在 - 只创建父目录而不是整个文件路径
    os.makedirs(images_dir, exist_ok=True)
    
    # 如果路径不同，将图片移动到输出目录
    if cropped_image_path != new_image_path:
        os.rename(cropped_image_path, new_image_path)
    
    # 保存到图像存储 - 使用图片文件名作为键名
    with open(file=new_image_path, mode="rb") as img_file:
        img_data = img_file.read()
        img_base64 = base64.b64encode(s=img_data).decode(encoding='utf-8')
        image_key = image_name
        image_store.save_image(key=image_key, base64_data=img_base64)
        print(f"图像已保存到存储: {image_key}")
        
    # 使用异步函数生成图像描述和标题
    description = await describe_image_async(image_path=new_image_path, api_key=api_key)
    title = await get_image_title_async(description, api_key=api_key)
    
    if not title:
        title = f"图片{image_name}"
    
    # 创建图像信息字典
    rel_path = os.path.join("images", image_name)
    
    image_info = {
        'path': new_image_path,      # 图片路径
        'rel_path': rel_path,        # 相对路径（放md文件里面）
        'description': description,  # 图片描述
        'title': title,              # 图片标题
        'image_key': image_key       # 图片存储的键名，使用文件名
    }
    
    return image_info


async def extract_images_from_layout_async(layout_result, rendered_image_path, output_dir, image_labels, image_store=None, api_key=None):
    """
    异步从布局结果中提取所有图像
    
    Args:
        layout_result: 版面分析结果
        rendered_image_path: 渲染后的页面图像路径
        output_dir: 图像输出目录
        image_labels: 图像标签集
        image_store: 图像存储对象
        api_key: API密钥，用于模型调用
        
    Returns:
        str: 图像Markdown文本
    """
    image_markdown = ""
    
    if "boxes" not in layout_result:
        return image_markdown
    
    boxes = [box for box in layout_result["boxes"] if box["label"] in image_labels]
    if not boxes:
        return image_markdown

    # 创建任务列表，并行处理所有图像框
    tasks = [
        process_image_box_async(
            box=box,
            rendered_image_path=rendered_image_path,
            output_dir=output_dir,
            image_store=image_store,
            api_key=api_key
        )
        for box in boxes
    ]
    
    # 并行等待所有图像处理完成
    image_infos = await asyncio.gather(*tasks)
    
    # 从图像信息创建Markdown
    for image_info in image_infos:
        title = image_info.get('title', '图像')
        description = image_info.get('description', '')
        rel_path = image_info['rel_path']
        
        # 创建Markdown
        image_markdown += f"![{title}]({rel_path})\n\n> {description}\n\n"
    
    return image_markdown
