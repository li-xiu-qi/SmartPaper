from tools.everything_to_text.pdf_to_md_fitz_with_layout_detection import fitz_pdf2md


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