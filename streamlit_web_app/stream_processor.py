"""
流式输出处理模块

提供处理流式输出内容的功能。
"""

import os
from typing import Dict, Generator
from loguru import logger


def process_paper_stream(
        paper_url: str,
        selected_prompt: str,
        selected_prompt_version: str,
        progress_placeholder,
        paper_processor
) -> Dict:
    """
    处理论文的流式输出，并实时更新显示。
    图片替换现在由 paper_processor (即 process_paper) 处理。

    Args:
        paper_url (str): 论文URL
        selected_prompt (str): 选择的提示词模板
        progress_placeholder: Streamlit占位符，用于实时更新进度
        paper_processor: 论文处理器函数 (来自 paper_processor.py)

    Returns:
        Dict: 包含处理结果的字典
    """
    logger.info(f"开始流式处理论文: {paper_url}")

    # 初始化结果
    full_output = ""  # 存储完整输出 (现在已包含base64图片)
    result_info = {"success": False}  # 存储处理结果

    # 调用process_paper生成器函数处理论文
    for result in paper_processor(paper_url, selected_prompt, selected_prompt_version):
        if result["type"] == "chunk":
            # 收到内容片段 (已经过图片处理)
            chunk = result["content"]
            full_output += chunk  # 添加到完整输出

            # 更新显示，直接使用累积的 full_output
            progress_placeholder.markdown(full_output, unsafe_allow_html=True)

        elif result["type"] == "final":
            # 收到最终结果
            result_info = {
                "success": result["success"],
                "processed_output": full_output, # 使用累积的 full_output 作为处理后的输出
            }

            if result["success"]:
                result_info["file_path"] = result["file_path"]
                result_info["file_name"] = os.path.basename(result["file_path"])
                result_info["pdf_name"] = os.path.splitext(result_info["file_name"])[0].split('_prompt_')[0].split('_')[-1] # 尝试从文件名解析
            else:
                result_info["error"] = result["error"]

            break  # 处理完成，退出循环

    return result_info
