# --- Model Definitions ---

DEFAULT_VISION_MODEL = "Qwen/Qwen2.5-VL-72B-Instruct"
DEFAULT_TEXT_MODEL = "Pro/Qwen/Qwen2.5-7B-Instruct"  # "Qwen/Qwen2.5-32B-Instruct"
DEFAULT_DESCRIPTION_MODEL = "Pro/Qwen/Qwen2.5-VL-7B-Instruct"

# 打印这里是__name__ 的定义模型选择
print(__name__, ":", DEFAULT_VISION_MODEL)
print(__name__,":",DEFAULT_TEXT_MODEL)
print(__name__,":",DEFAULT_DESCRIPTION_MODEL)


# --- End Model Definitions ---


# --- Prompt Definitions ---

# 默认提示文本
DEFAULT_PROMPT = """
你是一个可以识别图片的AI，你可以基于图片与用户进行友好的对话。
"""

# 图像标题生成的系统提示
TITLE_SYSTEM_PROMPT = """你是一个专业图像标题生成助手。
任务：根据提供的图像描述生成一个简短、准确且具有描述性的标题。

输出要求：
- 标题应简洁（通常控制在5-20个字之间）
- 突出图像的核心主题或最显著特征
- 使用具体而非抽象的词语
- 不要包含"这是"、"这张图片"等冗余词语
- 学术论文或技术图像应保留专业术语的准确性
- 直接输出标题文本，无需额外说明或引号

示例：
描述：茂密森林中，阳光透过树叶洒落在地面，形成斑驳光影。远处小溪流淌，水面反射着周围绿色植被。
标题：晨光森林溪流

描述：年轻女性在实验室使用显微镜观察样本。她穿白色实验服，戴护目镜，专注调整显微镜。旁边放着试管和实验笔记。
标题：科研人员显微观察

描述：学术论文封面，白色背景。标题"ISAM-MTL: Cross-subject multi-task learning model with identifiable spikes and associative memory networks"位于顶部，黑色字体。下方是作者名字"Junyan Li", "Bin Hu", "Zhi-Hong Guan"。摘要部分介绍EEG信号跨主体变化性和ISAM-MTL模型。页面右下角显示DOI和版权信息。
标题：ISAM-MTL 论文封面首页
"""

# 图像标题生成的用户提示模板
TITLE_USER_PROMPT_TEMPLATE = """基于以下图像描述，提供一个简洁、专业的标题：
----
描述：{description}
----
直接输出标题（5-15字）："""

# 各种图像处理的提示文本
OCR_PROMPT = """
使用OCR的模式提取图像中的文本内容，并转换为Markdown格式。
注意：不要输出图片以外的内容。
其中表格输出为Markdown格式，或者html格式，公式输出为带有$或者$$风格的LaTeX格式。
"""

DESCRIPTION_PROMPT = """
# PDF图像内容描述提示

## 任务

使用视觉语言模型生成从PDF提取的图像内容的简洁描述。

## 背景

- 图像来源于PDF文档
- 需要清晰理解图像的主要内容和用途
- 避免冗余描述，保持精简

## 输入

- 从PDF提取的图像

## 输出

请简洁使用50字以内，描述图像的以下关键方面：

1. 图像类型（图表、示意图、照片等）
2. 主要内容/主题
3. 包含的关键信息点
4. 图像的可能用途

示例格式：
"这是一张[图像类型]，展示了[主要内容]。包含[关键信息]。[其他相关细节]。"
"""

EXTRACT_TABLE_PROMPT = """
提取图片当中的表格，并输出为支持markdown格式的html语法。
注意：不要输出图片以外的内容。
"""
# --- End Prompt Definitions ---
