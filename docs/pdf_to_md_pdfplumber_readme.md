# PDF转Markdown工具使用文档

## 1. 工具简介

`pdf_to_md_pdfplumber`是一个功能强大的PDF文档转换工具，能够将PDF文件转换为结构化的Markdown文档。它不仅可以提取文本内容，还能智能处理PDF中的图片，使用AI技术生成图片描述和标题，最终生成一个完整的、包含文本和图片的Markdown文档。

### 主要特点

- 高质量的PDF文本提取
- 自动提取PDF中的所有图片
- 使用AI为图片生成描述和标题
- 支持异步并行处理，提高处理效率
- 内置缓存机制，避免重复处理
- 集中式图片存储，便于管理和复用

## 2. 依赖项

本工具依赖以下Python库：

- pdfplumber：用于PDF文本和图片提取
- PIL/Pillow：图像处理
- asyncio：异步任务处理
- concurrent.futures：并发处理
- 其他基础库：os, re, uuid, base64, json等

## 3. 核心功能模块

### 3.1 文本提取功能

使用pdfplumber提取PDF文档中的文本内容，并按页组织，转换为Markdown格式。

```python
extract_text(pdf_path, output_dir=None, db_root_dir=None)
```

### 3.2 图片提取功能

从PDF中提取所有图片，并保存为PNG格式。

```python
extract_images(pdf_path, output_dir=None, db_root_dir=None)
```

### 3.3 图片智能处理

使用AI模型为图片生成描述和标题：

```python
process_image_description_and_title(image_path, index=None, total=None, api_key=None)
```

### 3.4 Markdown报告生成

将文本和处理后的图片合并为完整的Markdown文档：

```python
generate_markdown_report_async(text_content_dict, image_paths, output_dir, api_key=None)
```

### 3.5 缓存机制

使用SQLite数据库存储处理结果，避免重复处理：

```python
# 通过get_pdf_cache()和get_image_store()实现
```

## 4. 工作流程

1. **文本提取**：读取PDF文件，提取文本内容
2. **图片提取**：分离PDF中的所有图片，保存为独立文件
3. **并行处理图片**：异步为每张图片生成描述和标题
4. **生成Markdown**：整合文本和图片，生成最终的Markdown文档
5. **缓存结果**：将处理结果存入数据库，便于后续复用

## 5. 使用方法

### 5.1 命令行调用

```bash
python pdf_to_md_pdfplumber.py /path/to/your.pdf -o /output/directory -k your_api_key -d /database/directory
```

参数说明：
- `pdf_path`：要处理的PDF文件路径（必需）
- `-o, --output`：输出目录（可选，默认为当前目录下的outputs子目录）
- `-k, --api-key`：API密钥（可选，用于AI图像处理）
- `-d, --cached_db-dir`：数据库根目录（可选）

### 5.2 作为Python模块调用

```python
from src.tools.everything_to_text.pdf_to_md_pdfplumber import process_pdf

# 同步处理PDF
text_content_dict, image_paths, md_path = process_pdf(
    "example.pdf",
    output_dir="./outputs",
    api_key="your_api_key"
)

# 使用转换器接口
from src.tools.everything_to_text.pdf_to_md_pdfplumber import pdfplumber_pdf2md

result = pdfplumber_pdf2md(
    file_path="example.pdf",
    config={
        "api_key": "your_api_key",
        "output_dir": "./outputs",
        "db_root_dir": "./db"
    }
)
```

## 6. 输出结果

处理完成后，将在指定的输出目录中生成：

1. Markdown文档（与PDF同名）
2. images子目录，包含所有提取的图片
3. 在数据库中缓存处理结果，便于后续查询

Markdown文档中，每个图片会包含：
- 智能生成的标题作为图片alt文本
- 图片相对链接
- 图片下方显示AI生成的图片描述

## 7. 高级配置

可以通过config字典传入更多配置参数：

```python
config = {
    "api_key": "your_api_key",      # API密钥
    "output_dir": "./outputs",      # 输出目录
    "db_root_dir": "./db",          # 数据库目录
    "url": "custom_url_for_cache"   # 用于缓存的自定义URL
}
```

## 8. 缓存机制说明

工具使用SQLite数据库存储：
- PDF处理结果缓存：避免重复处理相同的文档
- 图片数据存储：以base64格式存储图片数据

缓存查询基于文件路径或自定义URL，可以显著提高重复文档的处理速度。