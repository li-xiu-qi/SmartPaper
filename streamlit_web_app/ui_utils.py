"""
UI 工具和自定义样式

该模块包含与用户界面相关的工具函数和样式定义，
用于美化应用界面、提供一致的用户体验，以及封装常用的UI元素。
"""

import streamlit as st  # Web界面库




def add_url_highlight_script() -> None:
    """
    添加高亮URL输入框的JavaScript
    
    使用JavaScript动态修改URL输入框样式，使其更加突出显示。
    脚本在页面加载后执行，查找特定输入框并添加自定义CSS类。
    
    Returns:
        None: 该函数无返回值
    """
    st.markdown(
        """
    <script>
        // 等待页面加载完成后执行
        setTimeout(function() {
            // 获取URL输入框并添加高亮样式
            const urlInput = document.querySelector('[data-testid="stTextInput"] input');
            if (urlInput) {
                urlInput.classList.add('url-input');
            }
        }, 500);  // 延迟500毫秒执行，确保DOM已加载
    </script>
    """,
        unsafe_allow_html=True,  # 允许执行JavaScript
    )


def render_header() -> None:
    """
    渲染应用头部
    
    创建应用标题和简短描述，包含项目链接和简介。
    提供统一的应用顶部视觉元素。
    
    Returns:
        None: 该函数无返回值
    """
    # 显示主标题
    st.title("SmartPaper")
    # 显示项目简介和链接
    st.markdown(
        """
    <div style="color: gray; font-size: 0.8em;">
        <b>SmartPaper</b>: <a href="https://github.com/sanbuphy/SmartPaper">GitHub</a> -
        一个迷你助手，帮助您快速阅读论文
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_usage_instructions() -> None:
    """
    渲染使用说明
    
    创建一个美观的使用说明卡片，向用户展示如何使用应用的基本步骤。
    使用蓝色背景和左侧边框设计，突出显示重要信息。
    
    Returns:
        None: 该函数无返回值
    """
    st.markdown(
        """
    <div style="margin-top: 30px; padding: 15px; background-color: #e0f2fe; border-radius: 8px; border-left: 4px solid #0ea5e9;">
        <h4 style="margin-top: 0; color: #0369a1;">使用说明</h4>
        <p style="font-size: 0.9em; color: #0c4a6e;">
            1. 输入arXiv论文URL<br>
            2. 选择合适的提示词模板<br>
            3. 点击"开始分析"按钮<br>
            4. 等待分析完成后可下载结果
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )
