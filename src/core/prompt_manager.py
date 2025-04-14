import os
from typing import Dict, Optional
import yaml
import logging


class PromptLibrary:
    def __init__(self, text_prompt_file: Optional[str] = None, image_text_prompt_file: Optional[str] = None):
        """初始化提示词库，加载文本和图文两种提示词

        Args:
            text_prompt_file (Optional[str]): 纯文本提示词配置文件路径. Defaults to None.
            image_text_prompt_file (Optional[str]): 图文提示词配置文件路径. Defaults to None.
        """
        # 获取项目根目录的绝对路径
        root_dir = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )

        # 设置默认文件路径
        if text_prompt_file is None:
            text_prompt_file = os.path.join(root_dir, "config", "prompts_llm.yaml")
        if image_text_prompt_file is None:
            image_text_prompt_file = os.path.join(root_dir, "config", "prompts_llm_with_image.yaml")

        self.text_prompt_file = text_prompt_file
        self.image_text_prompt_file = image_text_prompt_file

        self.prompts_text = self._load_prompts(self.text_prompt_file, "text")
        self.prompts_image_text = self._load_prompts(self.image_text_prompt_file, "image_text")

        logging.info(f"成功加载了 {len(self.prompts_text)} 个 'text' 提示词模板")
        logging.info(f"成功加载了 {len(self.prompts_image_text)} 个 'image_text' 提示词模板")


    def _load_prompts(self, file_path: str, version_name: str) -> Dict:
        """从指定文件加载提示词配置

        Args:
            file_path (str): 配置文件路径
            version_name (str): 版本名称 (用于日志记录)

        Returns:
            Dict: 提示词配置, 如果文件不存在或加载失败则返回空字典
        """
        if not os.path.exists(file_path):
            logging.warning(f"提示词配置文件 '{file_path}' 不存在，跳过加载 '{version_name}' 版本。")
            return {}
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                if config and "prompts" in config:
                    return config["prompts"]
                else:
                    logging.warning(f"配置文件 '{file_path}' 格式不正确或缺少 'prompts' 键。")
                    return {}
        except Exception as e:
            logging.error(f"加载 '{version_name}' 提示词配置失败 ({file_path}): {str(e)}")
            return {}

    def get_prompt(self, prompt_name: str, prompt_version: str = "text") -> str:
        """获取指定名称和版本的提示词模板

        Args:
            prompt_name (str): 提示词名称
            prompt_version (str): 提示词版本 ('text' 或 'image_text'). Defaults to "text".

        Returns:
            str: 提示词模板

        Raises:
            ValueError: 如果版本无效或未找到指定名称的提示词模板
        """
        prompts_dict = None
        if prompt_version == "text":
            prompts_dict = self.prompts_text
        elif prompt_version == "image_text":
            prompts_dict = self.prompts_image_text
        else:
            raise ValueError(f"无效的提示词版本: '{prompt_version}'. 请使用 'text' 或 'image_text'.")

        if prompt_name not in prompts_dict:
            raise ValueError(f"在 '{prompt_version}' 版本中未找到名为 '{prompt_name}' 的提示词模板")
        if "template" not in prompts_dict[prompt_name]:
             raise ValueError(f"在 '{prompt_version}' 版本 '{prompt_name}' 模板中未找到 'template' 键")
        return prompts_dict[prompt_name]["template"]

    def list_prompts(self, prompt_version: str = "text") -> Dict[str, str]:
        """列出指定版本所有可用的提示词模板

        Args:
            prompt_version (str): 提示词版本 ('text' 或 'image_text'). Defaults to "text".

        Returns:
            Dict[str, str]: 提示词名称和描述的字典

        Raises:
            ValueError: 如果版本无效
        """
        prompts_dict = None
        if prompt_version == "text":
            prompts_dict = self.prompts_text
        elif prompt_version == "image_text":
            prompts_dict = self.prompts_image_text
        else:
            raise ValueError(f"无效的提示词版本: '{prompt_version}'. 请使用 'text' 或 'image_text'.")

        return {name: info.get("description", "No description") for name, info in prompts_dict.items()}

    def reload(self):
        """重新加载所有版本的提示词配置"""
        logging.info("重新加载提示词库...")
        self.prompts_text = self._load_prompts(self.text_prompt_file, "text")
        self.prompts_image_text = self._load_prompts(self.image_text_prompt_file, "image_text")
        logging.info(f"重新加载完成: {len(self.prompts_text)} 个 'text', {len(self.prompts_image_text)} 个 'image_text' 提示词模板")


# 创建全局实例 (现在包含两个版本)
_prompt_library = PromptLibrary()


# 导出便捷函数
def get_prompt(prompt_name: str, prompt_version: str = "text") -> str:
    """获取指定名称和版本的提示词模板

    Args:
        prompt_name (str): 提示词名称
        prompt_version (str): 提示词版本 ('text' 或 'image_text'). Defaults to "text".

    Returns:
        str: 提示词模板
    """
    return _prompt_library.get_prompt(prompt_name, prompt_version)


def list_prompts(prompt_version: str = "text") -> Dict[str, str]:
    """列出指定版本所有可用的提示词模板

    Args:
        prompt_version (str): 提示词版本 ('text' 或 'image_text'). Defaults to "text".

    Returns:
        Dict[str, str]: 提示词名称和描述的字典
    """
    return _prompt_library.list_prompts(prompt_version)


def reload_prompts():
    """重新加载所有版本的提示词配置"""
    _prompt_library.reload()
