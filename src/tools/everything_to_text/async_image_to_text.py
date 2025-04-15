"""
异步图像文本提取和描述生成模块

该模块是image_to_text.py的异步版本，提供以下功能：
1. 异步调用多模态AI模型分析图像内容
2. 异步生成图像描述和标题
3. 支持异步表格提取和OCR
4. 使用AsyncOpenAI客户端加速处理
5. 保持与同步版本相同的API结构和功能

通过异步处理，该模块可以显著提高处理大量图像时的效率，
适用于需要并行处理多个图像的批量处理场景。
"""

from openai import AsyncOpenAI
from dotenv import load_dotenv
import os
import base64
import asyncio
from PIL import Image

# Import functions from image_to_text.py
from src.tools.everything_to_text.image_to_text import (
    extract_markdown_content,
    image_to_base64,
)

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


class AsyncImageTextExtractor:
    """
    图像文本提取器的异步版本，用于将图像内容转换为 Markdown 格式的文本。
    
    该类使用AsyncOpenAI客户端处理图像分析请求，支持从本地文件或URL读取图像，
    并通过可定制的提示词指导AI模型生成特定格式的输出。
    主要用于图像OCR、内容描述和表格提取等任务。
    """

    def __init__(
            self,
            api_key: str = None,
            base_url: str = "https://api.siliconflow.cn/v1",
            prompt: str | None = None,
            prompt_path: str | None = None,
    ):
        """
        初始化 AsyncImageTextExtractor 实例。
        
        创建异步OpenAI客户端并配置默认提示词。支持通过直接传递提示字符串
        或指定提示文件路径来自定义AI的行为。

        Args:
            api_key: API 密钥，如果未提供则从环境变量中读取
            base_url: API 基础 URL，默认使用硅基流动的接口
            prompt: 提示文本，直接指定
            prompt_path: 提示文本文件路径，从文件读取
        """
        load_dotenv()
        self.api_key: str = api_key or os.getenv("API_KEY")

        if not self.api_key:
            raise ValueError("API key is required")

        self.client: AsyncOpenAI = AsyncOpenAI(
            api_key=self.api_key,
            base_url=base_url,
        )
        self._prompt: str = (
                prompt or self._read_prompt(prompt_path) or DEFAULT_PROMPT  # Use imported constant
        )

    async def aclose(self):
        """异步关闭客户端连接"""
        if hasattr(self, 'client') and self.client:
            await self.client.close()

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

    async def extract_image_text(
            self,
            image_url: str = None,
            local_image_path: str = None,
            model: str = DEFAULT_VISION_MODEL,  # Uses imported constant
            detail: str = "low",
            prompt: str = None,  # Keep prompt parameter for override
            temperature: float = 0.1,
    ) -> str:
        """
        异步提取图像中的文本并转换为 Markdown 格式。

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
                image_url.startswith("http://") or
                image_url.startswith("https://") or
                self._is_base64(image_url)
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

        prompt = prompt or self._prompt  # Use instance prompt (default or overridden)

        response = await self.client.chat.completions.create(
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
        async for chunk in response:
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
            try:
                return base64.b64encode(base64.b64decode(s)).decode("utf-8") == s
            except:
                return False
        return False

    def _get_image_extension(self, file_path: str) -> str:
        """
        获取图像文件的扩展名。

        :param file_path: 图像文件路径
        :return: 图像文件的扩展名
        """
        with Image.open(file_path) as img:
            return img.format.lower()


async def get_image_title_async(image_description,
                                model=DEFAULT_TEXT_MODEL,  # Uses imported constant
                                api_key=None, base_url="https://api.siliconflow.com/v1", timeout=30):
    """
    异步为多模态提取的图片描述生成图片的标题。

    参数:
        image_description (str): 图像的描述文本
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

    # 使用async with语句管理客户端生命周期
    try:
        async with AsyncOpenAI(api_key=api_key, base_url=base_url) as client:
            # 发送API请求
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": TITLE_SYSTEM_PROMPT,  # Use imported constant
                    },
                    {
                        "role": "user",
                        "content": TITLE_USER_PROMPT_TEMPLATE.format(description=image_description),
                        # Use imported constant
                    },
                ],
                timeout=timeout
            )

            # 提取并返回标题
            title = response.choices[0].message.content.strip()
            return title
    except Exception as e:
        print(f"Error generating image title: {e}")
        return None


async def _process_image_with_model_async(
        image_path: str,
        model: str = DEFAULT_VISION_MODEL,  # Uses imported constant
        prompt_path: str = None,
        prompt_text: str = None,  # Keep prompt_text parameter for override
        api_key: str = None,
        detail: str = "low",
        post_process_func=None,
        timeout: int = 60
) -> str:
    """异步处理图像并返回模型输出的基础函数"""
    if api_key is None:
        api_key = os.getenv("API_KEY")

    extractor = AsyncImageTextExtractor(
        api_key=api_key,
        prompt_path=prompt_path,
        prompt=prompt_text  # Pass potential override to constructor
    )

    try:
        result = await extractor.extract_image_text(
            local_image_path=image_path, model=model, detail=detail
        )

        if not result or not result.strip():
            return "No content extracted from the image"

        if post_process_func:
            return post_process_func(result)
        return extract_markdown_content(result)
    except Exception as e:
        print(f"Error processing image with model: {e}")
        return f"Error processing image: {e}"
    finally:
        # 确保在函数结束时关闭客户端
        await extractor.aclose()


async def extract_text_from_image_async(
        image_path: str,
        model: str = DEFAULT_VISION_MODEL,  # Uses imported constant
        ocr_prompt_path: str = None,
        api_key: str = None,
        timeout: int = 60
) -> str:
    """
    异步从图像中提取文本内容并转换为Markdown格式
    
    Args:
        image_path (str): 图像文件路径
        model (str): 使用的模型名称
        ocr_prompt_path (str): OCR提示文件路径
        api_key (str): API密钥
        timeout (int): 请求超时时间(秒)
        
    Returns:
        str: 提取的文本内容，如果提取失败则返回错误信息
    """
    return await _process_image_with_model_async(
        image_path=image_path,
        model=model,
        prompt_path=ocr_prompt_path,
        prompt_text=OCR_PROMPT if not ocr_prompt_path else None,  # Use imported constant
        api_key=api_key,
        detail="low",
        timeout=timeout
    )


async def describe_image_async(
        image_path: str,
        model: str = DEFAULT_DESCRIPTION_MODEL,  # Uses imported constant
        description_prompt_path: str = None,
        api_key: str = None,
        timeout: int = 60,
) -> str:
    """
    异步描述图像内容并生成文本描述
    
    Args:
        image_path (str): 图像文件路径
        model (str): 使用的模型名称
        description_prompt_path (str): 描述提示文件路径
        api_key (str): API密钥
        timeout (int): 请求超时时间(秒)
        
    Returns:
        str: 图像的描述文本，如果生成失败则返回错误信息
    """
    result = await _process_image_with_model_async(
        image_path=image_path,
        model=model,
        prompt_path=description_prompt_path,
        prompt_text=DESCRIPTION_PROMPT if not description_prompt_path else None,  # Use imported constant
        api_key=api_key,
        detail="low",
        timeout=timeout
    )

    return result


async def process_image_with_base64_async(
        image_path: str,
        output_dir: str = None,
        model: str = DEFAULT_DESCRIPTION_MODEL,  # Uses imported constant
        api_key: str = None
) -> dict:
    """
    异步处理图像并返回带有base64编码的结果
    
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
    description = await describe_image_async(image_path, model, None, api_key)  # Pass model

    # 生成图像标题
    title = await get_image_title_async(description, api_key=api_key)  # Use default text model here
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


async def extract_table_from_image_async(
        image_path: str,
        model: str = DEFAULT_VISION_MODEL,  # Uses imported constant
        extract_table_prompt_path: str = None,
        api_key: str = None,
        timeout: int = 120,
) -> str:
    """
    异步从图像中提取表格内容并转换为Markdown或HTML格式
    
    Args:
        image_path (str): 图像文件路径
        model (str): 使用的模型名称
        extract_table_prompt_path (str): 表格提取提示文件路径
        api_key (str): API密钥
        timeout (int): 请求超时时间(秒)，表格提取通常需要更长时间
        
    Returns:
        str: 提取的表格内容，如果提取失败则返回错误信息
    """
    return await _process_image_with_model_async(
        image_path=image_path,
        model=model,
        prompt_path=extract_table_prompt_path,
        prompt_text=EXTRACT_TABLE_PROMPT if not extract_table_prompt_path else None,  # Use imported constant
        api_key=api_key,
        detail="high",
        post_process_func=extract_markdown_content,
        timeout=timeout
    )


async def main():
    """示例使用异步API的主函数"""
    # 这里放置测试代码
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
    title = await get_image_title_async(image_description)  # Uses imported constants
    print("生成的标题:", title)

    # 如果有测试图片，可以在这里添加更多测试代码
    # image_path = "path/to/your/test/image.jpg"
    # description = await describe_image_async(image_path) # Uses default description model
    # print("图片描述:", description)
    # text = await extract_text_from_image_async(image_path) # Uses default vision model
    # print("提取文本:", text)
    # table = await extract_table_from_image_async(image_path) # Uses default vision model
    # print("提取表格:", table)


if __name__ == "__main__":
    asyncio.run(main())
