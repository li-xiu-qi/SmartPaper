"""
SmartPaper Web 应用配置模块

该模块包含应用的各种配置选项，包括日志设置、环境初始化、UI设置和示例数据。
将配置相关的功能集中在此模块可以使主程序更加清晰，并便于维护。
"""

import os  # 用于文件和目录操作
import sys  # 用于系统相关操作，如标准输出
import uuid # 用于生成唯一标识符
import streamlit as st # Web界面库
from loguru import logger  # 用于高级日志记录


def setup_logging() -> None:
    """
    配置日志记录系统

    设置loguru记录器，包括日志格式、级别和输出目标。
    将日志输出到标准输出，并设置合适的格式和颜色。

    Returns:
        None: 该函数无返回值
    """
    logger.remove()  # 移除默认处理器
    # 只输出到控制台，不记录到文件
    logger.add(
        sys.stdout,
        level="INFO",  # 设置日志级别为INFO
        format="{time:HH:mm:ss} | <level>{level: <8}</level> | {message}",  # 自定义日志格式
        colorize=True,  # 启用彩色输出
    )


def setup_environment() -> None:
    """
    设置应用运行环境

    创建必要的目录结构，初始化环境变量，以及执行其他启动前的准备工作。

    Returns:
        None: 该函数无返回值
    """
    logger.info("=== SmartPaperGUI启动 ===")
    # 创建输出目录（如果不存在）
    os.makedirs("outputs", exist_ok=True)


def setup_page_config() -> None:
    """
    设置Streamlit页面配置

    配置应用的基本外观和行为，包括标题、图标、布局和侧边栏状态。
    应在应用启动时最先调用，以确保正确设置页面。

    Returns:
        None: 该函数无返回值
    """
    st.set_page_config(
        page_title="SmartPaper",  # 浏览器标签页标题
        page_icon="📄",  # 标签页图标
        layout="wide",  # 使用宽屏布局
        initial_sidebar_state="expanded"  # 侧边栏默认展开
    )


def apply_custom_css() -> None:
    """
    应用自定义CSS样式

    使用HTML/CSS定义应用的视觉样式，使界面更加美观。
    包括颜色、字体、边框、阴影和动画效果等样式定义。

    Returns:
        None: 该函数无返回值
    """
    st.markdown(
        """
    <style>
        /* 整体页面样式 - 设置背景色和内边距 */
        .main {
            background-color: #f8f9fa;
            padding: 20px;
        }

        /* 标题样式 - 定义颜色、字重和底部边框 */
        h1 {
            color: #1e3a8a;
            font-weight: 700;
            margin-bottom: 30px;
            text-align: center;
            padding-bottom: 10px;
            border-bottom: 2px solid #3b82f6;
        }

        /* 副标题样式 - 左侧添加彩色边框 */
        h3 {
            color: #1e40af;
            font-weight: 600;
            margin-top: 20px;
            margin-bottom: 15px;
            padding-left: 10px;
            border-left: 4px solid #3b82f6;
        }

        /* 聊天消息容器 - 添加圆角和阴影效果 */
        .stChatMessage {
            border-radius: 10px;
            margin-bottom: 15px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }

        /* 按钮样式 - 设置圆角和悬停动画效果 */
        .stButton>button {
            border-radius: 8px;
            font-weight: 500;
            transition: all 0.3s ease;
        }

        /* 按钮悬停效果 - 微小上浮和阴影增强 */
        .stButton>button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }

        /* 下载按钮样式 - 紫色背景白色文字 */
        .stDownloadButton>button {
            background-color: #4f46e5;
            color: white;
            border: none;
            padding: 5px 15px;
            border-radius: 6px;
        }

        /* 侧边栏样式 - 浅灰色背景 */
        .css-1d391kg {
            background-color: #f1f5f9;
            padding: 20px 10px;
        }

        /* 输入框样式 - 圆角和边框 */
        .stTextInput>div>div>input {
            border-radius: 8px;
            border: 1px solid #d1d5db;
            padding: 10px;
        }

        /* URL输入框高亮样式 - 突出显示重要输入框 */
        .url-input {
            border: 2px solid #3b82f6 !important;
            background-color: #eff6ff !important;
            box-shadow: 0 0 10px rgba(59, 130, 246, 0.3) !important;
        }

        /* 选择框样式 - 圆角 */
        .stSelectbox>div>div {
            border-radius: 8px;
        }
    </style>
    """,
        unsafe_allow_html=True,  # 允许HTML渲染
    )


def initialize_session_state():
    """初始化会话状态变量"""
    if "messages" not in st.session_state:
        logger.debug("初始化会话状态: messages")
        st.session_state.messages = []

    if "processed_papers" not in st.session_state:
        logger.debug("初始化会话状态: processed_papers")
        st.session_state.processed_papers = {}

    if "session_id" not in st.session_state:
        st.session_state.session_id = uuid.uuid4().hex


def initialize_app() -> None:
    """
    初始化整个应用程序

    调用所有必要的设置函数来准备应用环境和界面。
    """
    setup_logging()
    setup_environment()
    setup_page_config()
    apply_custom_css()
    initialize_session_state()
    logger.info("应用程序初始化完成")


def get_example_urls() -> list:
    """
    获取示例论文URL列表

    提供一组预先定义的arXiv论文URL，作为用户可以直接使用的示例。
    包含不同格式（pdf和abs）的arXiv链接，展示系统的自动转换能力。

    Returns:
        list: 含有示例arXiv论文URL的列表
    """
    return [
        "https://arxiv.org/pdf/2305.12002",
        "https://arxiv.org/pdf/2303.08774",
        "https://arxiv.org/abs/2310.06825",
        "https://arxiv.org/abs/2307.09288",
        "https://arxiv.org/pdf/2312.11805",
    ]
