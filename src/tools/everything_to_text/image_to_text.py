"""
图像文本提取和描述生成模块

该模块提供一系列功能，用于从图像中提取文本内容或生成描述：
1. 使用多模态AI模型分析图像内容并提取文本
2. 生成图像的自然语言描述
3. 为图像创建简短标题
4. 识别并提取图像中的表格
5. 支持多种模型和配置选项

主要用于增强文档处理系统对图像内容的理解能力，
尤其适用于PDF转换、图像归档和内容索引等场景。
"""

from openai import OpenAI, AsyncOpenAI
from dotenv import load_dotenv
import os
import base64
# Import constants from the new constants file
from .image_to_text_constants import (
    DEFAULT_VISION_MODEL,
    DEFAULT_TEXT_MODEL,
    DEFAULT_DESCRIPTION_MODEL,
    DEFAULT_PROMPT,
    TITLE_SYSTEM_PROMPT,
    TITLE_USER_PROMPT_TEMPLATE,
    OCR_PROMPT,
    DESCRIPTION_PROMPT,
    EXTRACT_TABLE_PROMPT
)

load_dotenv()

def extract_markdown_content(text: str) -> str:
    """
    从文本中提取Markdown内容，自动去除markdown和html代码块标记。
    
    该函数能够识别并清理由多模态AI模型生成的文本中的代码块标记，
    保留真正的内容部分。支持处理markdown和html格式的代码块。
    
    参数:
    text (str): 输入文本，可能包含markdown或html代码块标记。
    
    返回:
    str: 提取的内容，如果没有找到Markdown或HTML标记，则返回原始文本。
          如果输入为None则返回None。
    """
    md_start_marker = "```markdown"
    html_start_marker = "```html"
    end_marker = "```"

    # 处理markdown代码块
    md_start_index = text.find(md_start_marker)
    if (md_start_index != -1):
        start_index = md_start_index + len(md_start_marker)
        end_index = text.find(end_marker, start_index)
        
        if (end_index == -1):
            return text[start_index:].strip()
        return text[start_index:end_index].strip()
    
    # 处理html代码块
    html_start_index = text.find(html_start_marker)
    if (html_start_index != -1):
        start_index = html_start_index + len(html_start_marker)
        end_index = text.find(end_marker, start_index)
        
        if (end_index == -1):
            return text[start_index:].trip()
        return text[start_index:end_index].strip()
    
    # 如果没有找到特定标记，返回原始文本
    return text.strip() if text else None


def image_to_base64(image_path: str) -> str:
    """
    将图像文件转换为Base64编码的字符串。

    参数:
    image_path (str): 图像文件路径。

    返回:
    str: Base64编码的字符串。
    """
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
    return encoded_string


class ImageTextExtractor:
    """
    图像文本提取器类，用于将图像内容转换为 Markdown 格式的文本。
    """

    def __init__(
        self,
        api_key: str = None,
        base_url: str = "https://api.siliconflow.cn/v1",
        prompt: str | None = None,
        prompt_path: str | None = None,
    ):
        """
        初始化 ImageTextExtractor 实例。

        :param api_key: API 密钥，如果未提供则从环境变量中读取
        :param base_url: API 基础 URL
        :param prompt: 提示文本
        :param prompt_path: 提示文本文件路径
        """
        load_dotenv()
        self.api_key: str = api_key or os.getenv("API_KEY")

        if not self.api_key:
            raise ValueError("API key is required")

        self.client: OpenAI = OpenAI(
            api_key=self.api_key,
            base_url=base_url,
        )
        self._prompt: str = (
            prompt or self._read_prompt(prompt_path)  or DEFAULT_PROMPT # Use imported constant
        )

    def _read_prompt(self, prompt_path: str) -> str:
        """
        从文件中读取提示文本。

        :param prompt_path: 提示文本文件路径
        :return: 提示文本内容
        """
        if not prompt_path or not os.path.exists(prompt_path):
            return None
            
        if not prompt_path.endswith((".md", ".txt")):
            raise ValueError("Prompt file must be a .md or .txt file")
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()

    def extract_image_text(
        self,
        image_url: str = None,
        local_image_path: str = None,
        model: str = DEFAULT_VISION_MODEL, # Uses imported constant
        detail: str = "low",
        prompt: str = None, # Keep prompt parameter for override
        temperature: float = 0.1,
    ) -> str:
        """
        提取图像中的文本并转换为 Markdown 格式。

        :param image_url: 图像的 URL
        :param local_image_path: 本地图像文件路径
        :param model: 使用的模型名称
        :param detail: 细节级别，允许值为 'low', 'high', 'auto'
        :param prompt: 提示文本
        :param temperature: 生成文本的温度参数
        :return: 提取的 Markdown 格式文本
        """

        if not image_url and not local_image_path:
            raise ValueError("Either image_url or local_image_path is required")

        if image_url and not (
            image_url.startswith("http://")
            or image_url.startswith("https://")
            or self._is_base64(image_url)
        ):
            raise ValueError(
                "Image URL must be a valid HTTP/HTTPS URL or a Base64 encoded string"
            )

        if local_image_path:
            if not os.path.exists(local_image_path):
                raise FileNotFoundError(f"The file {local_image_path} does not exist.")
            image_extension: str = self._get_image_extension(local_image_path)
            with open(local_image_path, "rb") as image_file:
                base64_image: str = base64.b64encode(image_file.read()).decode("utf-8")
                image_url = f"data:image/{image_extension};base64,{base64_image}"

        if detail not in ["low", "high", "auto"]:
            raise ValueError(
                "Invalid detail value. Allowed values are 'low', 'high', 'auto'"
            )

        if detail == "auto":
            detail = "low"

        prompt = prompt or self._prompt # Use instance prompt (default or overridden)

        response = self.client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": image_url, "detail": detail},
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
            stream=True,
            temperature=temperature,
        )

        result: str = ""
        for chunk in response:
            chunk_message: str = chunk.choices[0].delta.content
            if chunk_message is not None:
                result += chunk_message
        return result

    def _is_base64(self, s: str) -> bool:
        """
        检查字符串是否为 Base64 编码。

        :param s: 待检查的字符串
        :return: 如果是 Base64 编码则返回 True，否则返回 False
        """
        if isinstance(s, str):
            if s.strip().startswith("data:image"):
                return True
            return base64.b64encode(base64.b64decode(s)).decode("utf-8") == s
        return False

    def _get_image_extension(self, file_path: str) -> str:
        """
        获取图像文件的扩展名。

        :param file_path: 图像文件路径
        :return: 图像文件的扩展名
        """
        from PIL import Image

        with Image.open(file_path) as img:
            return img.format.lower()


def get_image_title(image_description,
                    model=DEFAULT_TEXT_MODEL, # Uses imported constant
                    api_key=None, base_url="https://api.siliconflow.com/v1", timeout=30):
    """
    使用硅基流动的deepseek v3 为多模态提取的图片描述生成图片的标题。

    参数:
        image_description (str): 图像的描述文本
        model (str): 使用的模型名称
        api_key (str): 您的OpenAI API密钥
        base_url (str): API基础URL
        timeout (int): API请求超时时间(秒)

    返回:
        str: 为图像生成的标题，如果生成失败则返回None
    """
    if not image_description:
        return None

    if not api_key:
        api_key = os.getenv("API_KEY")
    
    # 使用Silicon Flow基础URL初始化客户端
    client = OpenAI(api_key=api_key, base_url=base_url)

    # 发送API请求
    response = client.chat.completions.create(
        model=model, # Use parameter
        messages=[
            {
                "role": "system",
                "content": TITLE_SYSTEM_PROMPT, # Use imported constant
            },
            {
                "role": "user",
                "content": TITLE_USER_PROMPT_TEMPLATE.format(description=image_description), # Use imported constant
            },
        ],
        timeout=timeout
    )

    # 提取并返回标题
    title = response.choices[0].message.content.strip()
    return title


def _process_image_with_model(
    image_path: str,
    model: str = DEFAULT_VISION_MODEL, # Uses imported constant
    prompt_path: str = None,
    prompt_text: str = None, # Keep prompt_text parameter for override
    api_key: str = None,
    detail: str = "low",
    post_process_func = None,
    timeout: int = 60
) -> str:
    """处理图像并返回模型输出的基础函数"""
    if api_key is None:
        api_key = os.getenv("API_KEY")
    
    extractor = ImageTextExtractor(
        api_key=api_key,
        prompt_path=prompt_path,
        prompt=prompt_text # Pass potential override to constructor
    )

    result = extractor.extract_image_text(
        local_image_path=image_path, model=model, detail=detail
    )
    
    if not result or not result.strip():
        return "No content extracted from the image"
    
    if post_process_func:
        return post_process_func(result)
    return extract_markdown_content(result)


def extract_text_from_image(
    image_path: str,
    model: str = DEFAULT_VISION_MODEL, # Uses imported constant
    ocr_prompt_path: str = None,
    api_key: str = None,
    timeout: int = 60
) -> str:
    """
    从图像中提取文本内容并转换为Markdown格式
    
    Args:
        image_path (str): 图像文件路径
        model (str): 使用的模型名称
        ocr_prompt_path (str): OCR提示文件路径
        api_key (str): API密钥
        timeout (int): 请求超时时间(秒)
        
    Returns:
        str: 提取的文本内容，如果提取失败则返回错误信息
    """
    return _process_image_with_model(
        image_path=image_path,
        model=model,
        prompt_path=ocr_prompt_path,
        prompt_text=OCR_PROMPT if not ocr_prompt_path else None, # Use imported constant
        api_key=api_key,
        detail="low",
        timeout=timeout
    )


def describe_image(
    image_path: str,
    model: str = DEFAULT_DESCRIPTION_MODEL, # Uses imported constant
    description_prompt_path: str = None,
    api_key: str = None,
    timeout: int = 60,
) -> str:
    """
    描述图像内容并生成文本描述
    
    Args:
        image_path (str): 图像文件路径
        model (str): 使用的模型名称
        description_prompt_path (str): 描述提示文件路径
        api_key (str): API密钥
        timeout (int): 请求超时时间(秒)
        fallback_text (str): 如果描述失败时的备用文本
        
    Returns:
        str: 图像的描述文本，如果生成失败则返回fallback_text
    """
    result = _process_image_with_model(
        image_path=image_path,
        model=model,
        prompt_path=description_prompt_path,
        prompt_text=DESCRIPTION_PROMPT if not description_prompt_path else None, # Use imported constant
        api_key=api_key,
        detail="low",
        timeout=timeout
    )
    
    return result


def process_image_with_base64(
    image_path: str, 
    output_dir: str = None,
    model: str = DEFAULT_DESCRIPTION_MODEL, # Uses imported constant for description
    api_key: str = None
) -> dict:
    """
    处理图像并返回带有base64编码的结果
    
    Args:
        image_path (str): 图像文件路径
        output_dir (str): 输出目录，用于计算相对路径
        model (str): 使用的模型名称
        api_key (str): API密钥
        
    Returns:
        dict: 包含以下键的字典：
            - key (str): 图像键名
            - filename (str): 图像文件名
            - path (str): 图像绝对路径
            - rel_path (str): 图像相对路径
            - base64 (str): base64编码的图像数据
            - description (str): 图像描述
            - title (str): 图像标题
    """
    if output_dir is None:
        output_dir = os.path.dirname(image_path)
    
    # 生成图像键名和相对路径
    image_filename = os.path.basename(image_path)
    image_key = os.path.splitext(image_filename)[0]
    rel_path = os.path.relpath(image_path, output_dir)
    
    # 转换为base64
    base64_data = image_to_base64(image_path)
    
    # 获取图像描述
    description = describe_image(image_path, model, None, api_key)
    
    # 生成图像标题
    title = get_image_title(description, api_key=api_key) # Uses DEFAULT_TEXT_MODEL by default
    if not title:
        title = f"图片{image_filename}"
    
    return {
        "key": image_key,
        "filename": image_filename,
        "path": image_path,
        "rel_path": rel_path,
        "base64": base64_data,
        "description": description,
        "title": title
    }


def extract_table_from_image(
    image_path: str,
    model: str = DEFAULT_VISION_MODEL, # Uses imported constant
    extract_table_prompt_path: str = None,
    api_key: str = None,
    timeout: int = 120,
) -> str:
    """
    从图像中提取表格内容并转换为Markdown或HTML格式
    
    Args:
        image_path (str): 图像文件路径
        model (str): 使用的模型名称
        extract_table_prompt_path (str): 表格提取提示文件路径
        api_key (str): API密钥
        timeout (int): 请求超时时间(秒)，表格提取通常需要更长时间
        
    Returns:
        str: 提取的表格内容，如果提取失败则返回错误信息
    """
    return _process_image_with_model(
        image_path=image_path,
        model=model,
        prompt_path=extract_table_prompt_path,
        prompt_text=EXTRACT_TABLE_PROMPT if not extract_table_prompt_path else None, # Use imported constant
        api_key=api_key,
        detail="high",
        post_process_func=extract_markdown_content,
        timeout=timeout
    )


if __name__ == "__main__" and __file__ == "image_to_text.py":
    image_description = """
    这张图片显示了一篇学术论文的封面。
    封面的背景是白色的，标题
    "ISAM-MTL: Cross-subject multi-task learning model with identifiable spikes and associative memory networks"
    位于页面的顶部，使用了黑色的字体。
    标题下方是作者的名字，分别是"Junyan Li", "Bin Hu", 和"Zhi-Hong Guan"。再往下是摘要部分，使用了较小的字体。
    摘要的标题是"Abstract"，内容是关于EEG（脑电图）信号的跨主体变化性，
    以及一种新的模型"ISAM-MTL"（Identifiable Spikes and Associative Memory Multi-Task Learning）的介绍。
    摘要的最后是"Introduction"部分的开头，介绍了脑机接 口（BCI）系统和EEG信号的相关背景。
    页面的右下角显示了论文的引用信息，包括DOI（数字对象标识符）和版权信息。
    整体构图简洁明了，信息层次分明。
    """
    title = get_image_title(image_description) # Uses imported default text model
    print(title)
