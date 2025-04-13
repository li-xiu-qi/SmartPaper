"""
测试pdf_to_md_pdfplumber.py文件，用于测试process_pdf函数
"""

import os
import pytest
import json
import tempfile
import shutil

from src.tools.everything_to_text.pdf_to_md_pdfplumber import process_pdf
from src.tools.db.image_store import get_image_store, get_pdf_cache


def test_pdf_to_md_conversion():
    # 定义测试文件和输出路径
    test_pdf_path = "test_datas/test_pdf_to_md_pdfplumber.pdf"
    output_dir = "./output"
    
    # 创建临时数据库目录
    temp_db_dir = tempfile.mkdtemp(prefix="test_pdf_db_")
    
    try:
        # 获取输入文件名（不含扩展名）
        input_filename = os.path.splitext(os.path.basename(test_pdf_path))[0]
        expected_md_file = os.path.join(output_dir, f"{input_filename}.md")
        
        # 如果输出文件已存在，先删除它以确保测试的准确性
        if os.path.exists(expected_md_file):
            os.remove(expected_md_file)
        
        # 处理PDF文件，指定使用临时数据库目录
        result = process_pdf(test_pdf_path, output_dir, None, temp_db_dir)
        
        # 验证返回值格式
        assert isinstance(result, tuple), "返回值应为元组"
        assert len(result) == 3, "返回值元组应包含三个元素"
        
        # 验证返回的文本内容是否是字典格式
        text_content = result[0]
        assert isinstance(text_content, dict), "文本内容应为字典格式"
        assert "text_content" in text_content, "文本内容字典中应包含'text_content'键"
        assert "metadata" in text_content, "文本内容字典中应包含'metadata'键"
        assert "images" in text_content, "文本内容字典中应包含'images'键"
        
        # 验证图片列表
        image_paths = result[1]
        assert isinstance(image_paths, list), "图片路径应为列表"
        
        # 验证Markdown文件路径
        md_path = result[2]
        assert os.path.exists(md_path), f"Markdown文件 {md_path} 应存在"
        
        # 验证图片目录是否存在
        images_dir = os.path.join(output_dir, "images")
        assert os.path.isdir(images_dir), f"图片目录 {images_dir} 应存在"
        
        # 检查是否至少有一些图片被提取
        image_files = [f for f in os.listdir(images_dir) if f.endswith('.png')]
        assert len(image_files) > 0, "应至少提取一些图片"
        
        # 测试数据库中的图片保存，指定使用临时数据库目录
        image_store = get_image_store(temp_db_dir)
        pdf_name = input_filename
        
        # 验证数据库中的图片数量
        db_images = image_store.get_all_images(pdf_name)
        assert len(db_images) > 0, "数据库中应存在图片记录"
        
        # 对于每个提取的图片，验证其在数据库中是否存在
        for image_info in text_content["images"]:
            image_key = image_info["key"]
            image_data = image_store.get_image(image_key)
            assert image_data is not None, f"图片 {image_key} 应存在于数据库中"
            assert len(image_data) > 0, f"图片 {image_key} 的数据不应为空"
        
        # 测试PDF缓存功能，指定使用临时数据库目录
        pdf_cache = get_pdf_cache(temp_db_dir)
        url = f"file://{test_pdf_path}"
        
        # 由于process_pdf函数没有直接保存缓存，我们需要手动保存缓存进行测试
        # 手动保存缓存结果
        saved = pdf_cache.save_cache(
            url=url,
            pdf_name=pdf_name,
            output_dir=os.path.dirname(md_path),
            text_content=text_content["text_content"],
            has_images=len(text_content["images"]) > 0
        )
        assert saved, "缓存应该保存成功"
        
        # 现在尝试获取缓存
        cached_result = pdf_cache.get_cache(url)
        assert cached_result is not None, "PDF处理结果应该被缓存"
        assert cached_result["text_content"] is not None, "缓存应包含文本内容"
        assert cached_result["has_images"] == True, "缓存应标记包含图片"
    
    finally:
        # 测试完成后清理临时数据库目录
        shutil.rmtree(temp_db_dir, ignore_errors=True)


if __name__ == "__main__":
    pytest.main(["-v", __file__])
