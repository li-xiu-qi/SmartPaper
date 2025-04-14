"""注册所有文档转换器

这个模块负责注册所有可用的文档转换器。
新的转换器应该在这里注册。
"""

import importlib
from pathlib import Path
from typing import Dict, Any, Optional

from shapely.speedups import available

from .document_converter import DocumentConverter
# 定义要尝试注册的转换器列表
# 每个元组包含: (注册名称, 模块路径, 函数名称)
converters_to_register = [
    ("markitdown", "src.tools.everything_to_text.pdf_to_md_markitdown", "markitdown_pdf2md"),
    # ("mineru", "src.tools.everything_to_text.pdf_to_md_mineru", "mineru_pdf2md"),
    ("pdfplumber", "src.tools.everything_to_text.pdf_to_md_pdfplumber", "pdfplumber_pdf2md"),
    ("fitz", "src.tools.everything_to_text.pdf_to_md_fitz", "fitz_pdf2md"),
    ("async_fitz_with_image", "src.tools.everything_to_text.async_pdf_to_md_fitz_with_layout_detection", "sync_fitz_pdf2md"),
    # 在这里添加更多转换器...
]

def register_all_converters():
    """注册所有可用的转换器"""
    print("正在注册可用的文档转换器...")
    registered_count = 0
    available_converts = []
    for name, module_path, func_name in converters_to_register:
        try:
            # 动态导入模块
            module = importlib.import_module(module_path)
            # 获取转换函数
            converter_func = getattr(module, func_name)
            # 注册转换器
            DocumentConverter.register(name, converter_func)
            print(f"  [成功] 注册转换器: {name}")
            registered_count += 1
            available_converts.append(name)
        except AttributeError:
            print(f"  [错误] 在模块 '{module_path}' 中未找到函数 '{func_name}'")


    if registered_count == 0:
        print("警告：没有成功注册任何文档转换器。")
    else:
        print(f"共成功注册 {registered_count} 个转换器。")
        # 输出可用的转换器列表
        print("可用的转换器列表:")
        for name in available_converts:
            print(f"  - {name}")

# 自动执行注册
register_all_converters()
