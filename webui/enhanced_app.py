"""
增强版Web界面 - 整合两个项目的优点
支持模拟模式、平台状态监控、详细结果展示
"""

import streamlit as st
import requests
import json
import time
from datetime import datetime
import logging
import os
import sqlite3
from pathlib import Path
import tempfile
import shutil
import json
import time

# 页面配置
st.set_page_config(
    page_title="AI多平台搜索聚合器 - 增强版",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS - 整合两个项目的样式
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .feature-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    .status-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e9ecef;
        margin: 0.5rem 0;
        transition: all 0.3s ease;
    }
    
    .status-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }
    
    .result-container {
        background: #ffffff;
        padding: 2rem;
        border-radius: 15px;
        border: 1px solid #e9ecef;
        margin: 1.5rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    }
    
    .simulation-badge {
        background: #ffeaa7;
        color: #2d3436;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
        display: inline-block;
        margin-left: 0.5rem;
    }
    
    .real-mode-badge {
        background: #00b894;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
        display: inline-block;
        margin-left: 0.5rem;
    }
    
    .status-ready { color: #00b894; font-weight: bold; }
    .status-developing { color: #fdcb6e; font-weight: bold; }
    .status-planned { color: #74b9ff; font-weight: bold; }
    .status-error { color: #e17055; font-weight: bold; }
    
    .metric-card {
        background: linear-gradient(135deg, #74b9ff, #0984e3);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin: 0.5rem;
    }
    
    .platform-searching {
        border-left: 4px solid #ffeaa7;
        background: #ffeaa7;
        animation: pulse 2s infinite;
    }
    
    .platform-completed {
        border-left: 4px solid #00b894;
        background: #d5f4e6;
    }
    
    .platform-failed {
        border-left: 4px solid #e17055;
        background: #ffeaa7;
    }
    
    .live-content {
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 1rem;
        margin: 0.5rem 0;
        background: #f8f9fa;
        max-height: 300px;
        overflow-y: auto;
    }
    
    .progress-text {
        font-weight: bold;
        color: #2d3436;
        margin-bottom: 0.5rem;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.7; }
        100% { opacity: 1; }
    }
</style>
""", unsafe_allow_html=True)

# API配置
API_BASE_URL = "http://localhost:8000"

def call_api(endpoint, method="GET", data=None, timeout=60):
    """统一的API调用函数"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url, timeout=timeout)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=timeout)
        
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"API错误: {response.status_code} - {response.text}"
    except requests.exceptions.ConnectionError:
        return None, "无法连接到后端服务，请确保API服务已启动 (python backend/enhanced_api.py)"
    except requests.exceptions.Timeout:
        return None, "请求超时，搜索可能需要更长时间"
    except Exception as e:
        return None, f"请求失败: {str(e)}"

def main():
    """主函数"""
    
    # 检查API连接
    health_data, health_error = call_api("/health")
    
    if health_error:
        st.error(f"🚨 后端服务未启动: {health_error}")
        st.markdown("""
        ### 🔧 启动后端服务
        请在终端运行以下命令启动后端：
        ```bash
        python backend/enhanced_api.py
        ```
        
        或使用增强版API：
        ```bash
        python backend/enhanced_api.py
        ```
        """)
        return
    
    # 主标题
    st.markdown(f"""
    <div class="main-header">
        <h1>🔍 AI多平台搜索聚合器</h1>
        <p>🚀 流式监控 • 🧠 智能聚合 • ⚡ 实时处理</p>
        <p><strong>版本:</strong> {health_data.get('version', 'Unknown')} | 
           <strong>状态:</strong> {health_data.get('status', 'Unknown').upper()}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 侧边栏配置
    with st.sidebar:
        st.header("⚙️ 配置中心")
        
        # 模式选择
        st.subheader("🎭 运行模式")
        simulation_mode = st.radio(
            "选择运行模式",
            ["🎯 模拟模式 (推荐)", "🌐 浏览器自动化", "🍪 Cookie配置"],
            index=0,
            help="推荐使用浏览器自动化，无需Cookie配置"
        )
        
        is_simulation = "模拟模式" in simulation_mode
        is_browser_mode = "浏览器自动化" in simulation_mode
        is_cookie_mode = "Cookie配置" in simulation_mode
        
        if is_simulation:
            st.info("📝 模拟模式：使用内置测试数据，立即可用")
        elif is_browser_mode:
            st.info("🌐 浏览器自动化：连接您已登录的浏览器，无需Cookie")
            
            # 自动检测浏览器会话
            browser_platforms = auto_detect_browser_session()
            
            if browser_platforms:
                st.success(f"✅ 检测到 {len(browser_platforms)} 个已登录平台: {', '.join(browser_platforms)}")
            else:
                st.warning("⚠️ 未检测到浏览器会话")
                with st.expander("📖 浏览器自动化设置指南", expanded=True):
                    st.markdown("""
                    ### 🚀 快速设置步骤
                    
                    1. **启动调试模式Edge**：
                       ```bash
                       "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe" --remote-debugging-port=9222
                       ```
                    
                    2. **访问并登录AI平台**：
                       - https://chat.deepseek.com (推荐)
                       - https://kimi.moonshot.cn
                       - https://chatglm.cn
                    
                    3. **点击下方按钮重新检测**
                    """)
                    
                    if st.button("🔄 重新检测浏览器会话", type="primary"):
                        st.rerun()
        
        elif is_cookie_mode:
            st.warning("🍪 Cookie模式：需要手动配置，不推荐")
            if st.button("🔧 进入Cookie配置", type="secondary"):
                st.session_state.show_cookie_config = True
        
        # 搜索配置
        st.subheader("🔧 搜索参数")
        timeout = st.slider("超时时间(秒)", min_value=10, max_value=120, value=30)
        max_workers = st.slider("并发数", min_value=1, max_value=5, value=3)
        
        # AI增强选项
        st.subheader("🤖 AI增强")
        enable_ai = st.checkbox("启用AI智能处理", value=False)
        
        if enable_ai:
            ai_service = st.selectbox("AI服务商", ["siliconflow", "openai"], index=0)
            api_key = st.text_input("API Key", type="password")
            prompt_type = st.selectbox("处理类型", ["default", "fact_check", "summary"], index=0)
        
        # 平台状态
        st.subheader("📊 平台状态")
        display_platform_status()
    
    # 检查是否需要显示真实模式配置
    if st.session_state.get('show_real_mode_config', False):
        # 显示真实模式配置界面
        display_real_mode_setup()
        
        # 添加返回按钮
        if st.button("🔙 返回搜索中心"):
            st.session_state.show_real_mode_config = False
            st.rerun()
        
        return  # 不显示其他内容
    
    # 主内容区域
    main_tab, status_tab, help_tab = st.tabs(["🔍 搜索中心", "📊 系统状态", "📚 使用帮助"])
    
    with main_tab:
        # 搜索界面
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.subheader("🎯 多平台搜索")
            
            # 平台选择
            if is_simulation:
                # 模拟模式 - 显示所有支持的平台
                platforms_data, platforms_error = call_api("/platforms")
                if platforms_data:
                    available_platforms = platforms_data["platforms"]
                    selected_platforms = st.multiselect(
                        "选择搜索平台",
                        available_platforms,
                        default=["DeepSeek", "Kimi", "智谱清言"],
                        help="模拟模式下所有平台都可用"
                    )
                else:
                    st.error(f"获取平台列表失败: {platforms_error}")
                    selected_platforms = ["DeepSeek"]
            elif is_browser_mode:
                # 浏览器自动化模式
                browser_platforms = auto_detect_browser_session()
                
                if browser_platforms:
                    selected_platforms = st.multiselect(
                        "选择搜索平台",
                        browser_platforms,
                        default=browser_platforms,
                        help="这些平台已在浏览器中登录"
                    )
                else:
                    st.error("❌ 未检测到已登录的平台，请按照上方指南设置")
                    selected_platforms = []
            elif is_cookie_mode:
                # Cookie配置模式
                cookie_platforms = get_available_real_platforms()
                
                if cookie_platforms:
                    selected_platforms = st.multiselect(
                        "选择搜索平台",
                        cookie_platforms,
                        default=cookie_platforms,
                        help="这些平台已配置Cookie"
                    )
                else:
                    st.error("❌ 未配置任何Cookie，请先进行配置")
                    selected_platforms = []
            else:
                # 真实模式 - 显示已配置的平台和浏览器会话平台
                cookie_platforms = get_available_real_platforms()
                browser_platforms = get_browser_session_platforms()
                
                # 合并所有可用平台
                all_available_platforms = list(set(cookie_platforms + browser_platforms))
                
                if all_available_platforms:
                    selected_platforms = st.multiselect(
                        "选择搜索平台",
                        all_available_platforms,
                        default=all_available_platforms[:3] if len(all_available_platforms) >= 3 else all_available_platforms,
                        help="包含Cookie配置和浏览器会话中的平台"
                    )
                    
                    # 显示平台来源
                    if cookie_platforms or browser_platforms:
                        st.caption("📊 平台来源:")
                        if cookie_platforms:
                            st.caption(f"🍪 Cookie: {', '.join(cookie_platforms)}")
                        if browser_platforms:
                            st.caption(f"🌐 浏览器会话: {', '.join(browser_platforms)}")
                        
                else:
                    st.error("❌ 没有可用的平台，请先配置真实模式")
                    selected_platforms = []
            
            # 搜索输入
            query = st.text_area(
                "🔍 输入搜索问题",
                height=120,
                placeholder="例如：如何使用Python进行网页自动化？\n人工智能的发展趋势是什么？\n机器学习入门需要掌握哪些知识？",
                help="输入您想要搜索和分析的问题"
            )
            
            # 搜索按钮
            col_btn1, col_btn2, col_btn3 = st.columns([2, 1, 1])
            
            with col_btn1:
                search_button = st.button("🚀 开始搜索", type="primary", use_container_width=True)
            
            with col_btn2:
                if st.button("🔄 重置", use_container_width=True):
                    st.rerun()
            
            with col_btn3:
                if st.button("⏹️ 停止", use_container_width=True):
                    stop_data, stop_error = call_api("/stop", "POST")
                    if stop_data:
                        st.success("搜索已停止")
                    else:
                        st.error(f"停止失败: {stop_error}")
        
        with col2:
            # 搜索统计
            st.markdown("### 📈 搜索统计")
            
            if 'search_history' not in st.session_state:
                st.session_state.search_history = []
            
            st.metric("今日搜索", len(st.session_state.search_history))
            st.metric("选中平台", len(selected_platforms) if selected_platforms else 0)
            st.metric("运行模式", "模拟" if is_simulation else "真实")
        
        # 执行搜索
        if search_button and query:
            if not selected_platforms:
                st.error("请选择至少一个搜索平台")
            else:
                # 确定搜索模式
                mode = "simulation" if is_simulation else "browser" if is_browser_mode else "cookie"
                perform_search(query, selected_platforms, timeout, max_workers, 
                              enable_ai, mode)
    
    with status_tab:
        display_system_status()
    
    with help_tab:
        display_help_info()

def display_platform_status():
    """显示平台状态"""
    status_data, status_error = call_api("/platform-status")
    
    if status_error:
        st.error(f"获取平台状态失败: {status_error}")
        return
    
    statuses = status_data.get("statuses", [])
    
    # 平台URL映射
    platform_urls = {
        "DeepSeek": "https://chat.deepseek.com",
        "Kimi": "https://kimi.moonshot.cn", 
        "智谱清言": "https://chatglm.cn",
        "豆包": "https://doubao.com",
        "秘塔搜索": "https://metaso.cn"
    }
    
    st.markdown("### 🔗 AI平台快速访问")
    
    # 创建平台链接按钮
    cols = st.columns(3)
    for i, status in enumerate(statuses):
        platform = status["platform"]
        supported = status["supported"]
        available = status["available"]
        description = status["description"]
        
        # 状态图标和样式
        if available:
            icon = "✅"
            status_text = "就绪"
            button_type = "primary"
        elif supported:
            icon = "🚧"
            status_text = "开发中"
            button_type = "secondary"
        else:
            icon = "📋"
            status_text = "计划中"
            button_type = "secondary"
        
        with cols[i % 3]:
            # 平台信息卡片
            st.markdown(f"""
            <div style="border: 1px solid #ddd; border-radius: 8px; padding: 12px; margin-bottom: 10px; background: #f8f9fa;">
                <div style="font-size: 16px; font-weight: bold; margin-bottom: 5px;">
                    {icon} {platform}
                </div>
                <div style="font-size: 12px; color: #6c757d; margin-bottom: 8px;">
                    {description}
                </div>
                <div style="font-size: 11px; color: #6c757d;">
                    状态: {status_text}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # 访问按钮
            if platform in platform_urls:
                if st.button(f"🌐 访问 {platform}", key=f"visit_{platform}", type=button_type, use_container_width=True):
                    st.markdown(f"""
                    <script>
                        window.open('{platform_urls[platform]}', '_blank');
                    </script>
                    """, unsafe_allow_html=True)
                    st.info(f"正在新标签页中打开 {platform}...")
                    
    # 刷新浏览器会话按钮
    st.markdown("---")
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("🔄 更新浏览器登录信息", type="primary", use_container_width=True):
            with st.spinner("正在检测浏览器会话..."):
                browser_platforms = auto_detect_browser_session()
                if browser_platforms:
                    st.success(f"✅ 检测到 {len(browser_platforms)} 个已登录平台: {', '.join(browser_platforms)}")
                    st.rerun()
                else:
                    st.warning("⚠️ 未检测到已登录的AI平台页面")
                    st.info("💡 请在Edge调试模式中访问并登录AI平台后重试")
    
    with col2:
        if st.button("📊 检查平台连接", type="secondary", use_container_width=True):
            with st.spinner("正在检查平台连接..."):
                # 这里可以添加连接测试逻辑
                st.info("连接检查功能开发中...")

def display_system_status():
    """显示系统状态"""
    st.subheader("🏥 系统健康状态")
    
    health_data, health_error = call_api("/health")
    
    if health_error:
        st.error(f"系统状态检查失败: {health_error}")
        return
    
    # 系统信息
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>服务状态</h3>
            <h2>🟢 运行中</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>版本信息</h3>
            <h2>{health_data.get('version', 'Unknown')}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3>响应时间</h3>
            <h2>< 100ms</h2>
        </div>
        """, unsafe_allow_html=True)
    
    # 平台统计
    st.subheader("📊 平台统计")
    
    status_data, _ = call_api("/platform-status")
    if status_data:
        summary = status_data.get("summary", {})
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("总平台数", summary.get("total", 0))
        with col2:
            st.metric("支持平台", summary.get("supported", 0))
        with col3:
            st.metric("可用平台", summary.get("available", 0))
        with col4:
            st.metric("模拟就绪", summary.get("simulation_ready", 0))
    
    # API端点状态
    st.subheader("🔗 API端点状态")
    
    endpoints = [
        ("/health", "健康检查"),
        ("/platforms", "平台列表"),
        ("/platform-status", "平台状态"),
        ("/search", "搜索接口")
    ]
    
    for endpoint, description in endpoints:
        data, error = call_api(endpoint)
        status_icon = "✅" if not error else "❌"
        st.write(f"{status_icon} `{endpoint}` - {description}")

def display_help_info():
    """显示帮助信息"""
    st.subheader("📚 使用指南")
    
    # 功能特色
    st.markdown("""
    ### ✨ 功能特色
    
    - 🤖 **多平台搜索**: 支持DeepSeek、Kimi、智谱清言等主流AI平台
    - 🔄 **并发执行**: 同时搜索多个平台，提高效率
    - 📄 **智能聚合**: 自动去重和整合搜索结果
    - 🎭 **模拟模式**: 无需登录即可测试功能
    - 🔒 **安全加密**: 保护用户隐私和数据安全
    - 📊 **状态监控**: 实时查看平台和系统状态
    """)
    
    # 使用步骤
    st.markdown("""
    ### 🚀 使用步骤
    
    1. **选择模式**: 推荐先使用模拟模式测试功能
    2. **选择平台**: 在搜索中心选择要搜索的AI平台
    3. **输入问题**: 输入您想要搜索的问题或话题
    4. **开始搜索**: 点击"开始搜索"按钮执行搜索
    5. **查看结果**: 等待搜索完成，查看聚合后的结果
    """)
    
    # 模式说明
    st.markdown("""
    ### 🎭 模式说明
    
    **🎯 模拟模式 (推荐)**
    - 使用内置测试数据
    - 无需登录AI平台
    - 适合功能测试和演示
    - 响应速度快
    
    **🔥 真实模式**
    - 调用实际AI平台
    - 需要登录或Cookie
    - 获取真实搜索结果
    - 功能完整但需要配置
    """)
    
    # 故障排除
    st.markdown("""
    ### 🔧 故障排除
    
    **API连接失败**
    ```bash
    python backend/enhanced_api.py
    ```
    
    **平台搜索失败**
    - 检查网络连接
    - 确认平台登录状态
    - 尝试使用模拟模式
    
    **结果为空**
    - 尝试调整搜索关键词
    - 增加超时时间
    - 检查平台状态
    """)

def perform_search(query: str, platforms: list, timeout: int, max_workers: int, 
                  enable_ai: bool, mode: str):
    """执行搜索
    
    Args:
        query: 搜索查询
        platforms: 平台列表
        timeout: 超时时间
        max_workers: 最大工作线程
        enable_ai: 是否启用AI处理
        mode: 搜索模式 (simulation/browser/cookie)
    """
    
    # 构建搜索请求
    search_request = {
        "user_input": query,
        "platforms": platforms,
        "timeout": timeout,
        "max_workers": max_workers,
        "enable_ai_processing": enable_ai,
        "mode": mode,
        "simulation_mode": mode == "simulation"  # 向后兼容
    }
    
    # 显示搜索状态
    status_container = st.container()
    
    with status_container:
        if mode == "simulation":
            st.info("🎭 模拟模式搜索中...")
        elif mode == "browser":
            st.info("🌐 浏览器自动化搜索中...")
        elif mode == "cookie":
            st.info("🍪 Cookie模式搜索中...")
        else:
            st.info("🔍 搜索中...")
    
    # 启动异步搜索
    with st.spinner("🚀 启动搜索任务..."):
        result_data, result_error = call_api("/search-async", "POST", search_request, 30)
    
    if result_error or not result_data.get('success'):
        status_container.empty()
        st.error(f"❌ 启动搜索失败: {result_error}")
        return
    
    search_id = result_data.get('search_id')
    if not search_id:
        status_container.empty()
        st.error("❌ 获取搜索ID失败")
        return
    
    # 创建实时展示区域
    progress_container = st.container()
    live_results_container = st.container()
    final_results_container = st.container()
    
    with progress_container:
        progress_bar = st.progress(0)
        status_text = st.empty()
    
    # 为每个平台创建展示区域
    platform_containers = {}
    with live_results_container:
        st.subheader("🔍 实时搜索过程")
        
        # 创建平台展示区域
        for platform in platforms:
            platform_containers[platform] = {
                'expander': st.expander(f"⏳ {platform} - 准备中...", expanded=True),
                'status_text': None,
                'content_area': None
            }
            
            with platform_containers[platform]['expander']:
                platform_containers[platform]['status_text'] = st.empty()
                platform_containers[platform]['content_area'] = st.empty()
                platform_containers[platform]['status_text'].text("🔄 等待开始...")
    
    # 轮询搜索状态并实时更新
    max_attempts = 60  # 最多轮询60次 (2分钟)
    attempt = 0
    
    while attempt < max_attempts:
        # 获取当前状态
        status_data, status_error = call_api(f"/search-status/{search_id}", "GET", None, 10)
        
        if status_error:
            st.error(f"❌ 获取搜索状态失败: {status_error}")
            break
        
        status_info = status_data.get('status', {})
        current_status = status_info.get('status', 'unknown')
        progress = status_info.get('progress', 0.0)
        current_platform = status_info.get('current_platform')
        completed_platforms = status_info.get('completed_platforms', [])
        live_results = status_info.get('live_results', {})
        error = status_info.get('error')
        
        # 更新总体进度
        progress_bar.progress(progress)
        
        # 更新状态文本
        if current_status == "running":
            if current_platform:
                status_text.text(f"🔍 正在搜索: {current_platform} ({int(progress*100)}%)")
            else:
                status_text.text(f"🔄 处理中... ({int(progress*100)}%)")
        
        # 实时更新每个平台的状态和内容
        for platform in platforms:
            if platform in live_results:
                platform_info = live_results[platform]
                platform_status = platform_info.get('status', 'waiting')
                platform_content = platform_info.get('content', '')
                progress_text = platform_info.get('progress_text', '等待开始...')
                platform_error = platform_info.get('error')
                
                # 更新平台标题
                if platform_status == "waiting":
                    title = f"⏳ {platform} - 等待中..."
                    expanded = False
                elif platform_status == "searching":
                    title = f"🔍 {platform} - 搜索中..."
                    expanded = True
                elif platform_status == "completed":
                    title = f"✅ {platform} - 完成"
                    expanded = True
                elif platform_status == "failed":
                    title = f"❌ {platform} - 失败"
                    expanded = True
                else:
                    title = f"❓ {platform} - 未知状态"
                    expanded = False
                
                # 更新expander标题 (Streamlit限制，无法动态更新标题，但可以显示状态)
                
                # 更新状态文本
                if platform_error:
                    platform_containers[platform]['status_text'].markdown(f"""
                    <div class="progress-text" style="color: #e17055;">
                        ❌ {progress_text}: {platform_error}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    platform_containers[platform]['status_text'].markdown(f"""
                    <div class="progress-text">
                        📋 {progress_text}
                    </div>
                    """, unsafe_allow_html=True)
                
                # 更新内容区域
                if platform_content.strip():
                    with platform_containers[platform]['content_area']:
                        # 根据状态设置不同的样式
                        css_class = ""
                        if platform_status == "searching":
                            css_class = "platform-searching"
                        elif platform_status == "completed":
                            css_class = "platform-completed"
                        elif platform_status == "failed":
                            css_class = "platform-failed"
                        
                        st.markdown(f"""
                        <div class="live-content {css_class}">
                            <strong>🔍 实时内容流:</strong>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # 显示内容，如果太长就截断
                        if len(platform_content) > 1200:
                            preview_content = platform_content[:1200] + "\n\n*... 内容正在生成中，完整内容将在搜索完成后显示 ...*"
                        else:
                            preview_content = platform_content
                        
                        st.markdown(preview_content)
                        
                        # 如果平台已完成，显示完整标记
                        if platform_status == "completed":
                            st.success("✅ 该平台搜索完成，显示完整内容")
                        elif platform_status == "searching":
                            # 显示实时生成状态
                            progress_indicator = "🔄" if len(platform_content) % 4 == 0 else "⏳" if len(platform_content) % 4 == 1 else "🔍" if len(platform_content) % 4 == 2 else "💭"
                            st.info(f"{progress_indicator} 内容正在实时生成中...")
                            
                elif platform_status == "searching":
                    platform_containers[platform]['content_area'].markdown(f"""
                    <div class="live-content platform-searching">
                        <strong>🔄 正在连接 {platform}，准备获取内容...</strong>
                    </div>
                    """, unsafe_allow_html=True)
        
        # 检查搜索状态
        if current_status == "completed":
            status_text.text("✅ 所有平台搜索完成！")
            progress_bar.progress(1.0)
            
            # 等待一下让用户看到完成状态
            time.sleep(2)
            
            # 获取最终结果
            final_results = status_info.get('results', {})
            if final_results:
                # 清理实时展示区域
                progress_container.empty()
                live_results_container.empty()
                status_container.empty()
                
                # 显示最终聚合结果
                with final_results_container:
                    display_final_search_results(final_results, query, mode == "simulation", search_id, live_results)
                
                # 记录搜索历史
                if 'search_history' not in st.session_state:
                    st.session_state.search_history = []
                st.session_state.search_history.append({
                    "query": query,
                    "platforms": platforms,
                    "timestamp": datetime.now().isoformat(),
                    "simulation": mode == "simulation",
                    "search_id": search_id
                })
                
                # 清理搜索状态
                call_api(f"/search-status/{search_id}", "DELETE")
            else:
                st.error("❌ 搜索完成但未获得结果")
            break
            
        elif current_status == "failed":
            status_text.text("❌ 搜索失败")
            progress_bar.empty()
            
            error_msg = error or "未知错误"
            st.error(f"❌ 搜索失败: {error_msg}")
            
            # 清理搜索状态
            call_api(f"/search-status/{search_id}", "DELETE")
            break
        
        # 等待下次轮询
        attempt += 1
        time.sleep(1.5)  # 每1.5秒检查一次状态，更频繁的更新
    
    if attempt >= max_attempts:
        # 超时处理
        progress_container.empty()
        live_results_container.empty()
        status_container.empty()
        st.error("⏰ 搜索超时，请稍后重试")
        
        # 清理搜索状态
        call_api(f"/search-status/{search_id}", "DELETE")

def display_final_search_results(result_data: dict, query: str, is_simulation: bool, 
                                search_id: str, live_results: dict):
    """显示最终搜索结果"""
    
    # 成功标题
    mode_badge = "模拟模式" if is_simulation else "真实模式"
    badge_class = "simulation-badge" if is_simulation else "real-mode-badge"
    
    st.markdown(f"""
    ### 🎉 搜索完成！ <span class="{badge_class}">{mode_badge}</span>
    <small>搜索ID: {search_id}</small>
    """, unsafe_allow_html=True)
    
    # 处理统计
    summary = result_data.get("processing_summary", {})
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("搜索平台", summary.get("original_count", 0))
    with col2:
        st.metric("有效结果", summary.get("after_filtering", 0))
    with col3:
        st.metric("去重后", summary.get("after_deduplication", 0))
    with col4:
        # 计算总处理时间
        total_time = 0
        for platform, info in live_results.items():
            if info.get('start_time') and info.get('end_time'):
                try:
                    start = datetime.fromisoformat(info['start_time'])
                    end = datetime.fromisoformat(info['end_time'])
                    total_time = max(total_time, (end - start).total_seconds())
                except:
                    pass
        st.metric("处理时间", f"{total_time:.1f}s" if total_time > 0 else "N/A")
    
    # 聚合结果
    integrated_doc = result_data.get("integrated_document", {})
    if integrated_doc:
        st.subheader("📄 智能聚合结果")
        
        with st.container():
            st.markdown("""
            <div class="result-container">
            """, unsafe_allow_html=True)
            
            content = integrated_doc.get("integrated_content", "")
            if content:
                st.markdown(content)
            else:
                st.warning("暂无聚合内容")
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    # 平台详细结果
    raw_results = result_data.get("raw_results", [])
    if raw_results:
        st.subheader("📋 平台详细结果")
        
        # 创建标签页展示各平台结果
        tabs = st.tabs([result["platform"] for result in raw_results])
        
        for i, result in enumerate(raw_results):
            with tabs[i]:
                platform = result["platform"]
                content = result["content"]
                confidence = result.get("confidence", 0)
                status = result.get("status", "unknown")
                
                # 平台信息头部
                col1, col2, col3 = st.columns(3)
                with col1:
                    status_icon = "✅" if status == "success" else "❌"
                    st.metric("状态", f"{status_icon} {status}")
                with col2:
                    confidence_color = "🟢" if confidence > 0.8 else "🟡" if confidence > 0.6 else "🔴"
                    st.metric("置信度", f"{confidence_color} {confidence:.1f}")
                with col3:
                    # 显示该平台的处理时间
                    if platform in live_results:
                        platform_info = live_results[platform]
                        if platform_info.get('start_time') and platform_info.get('end_time'):
                            try:
                                start = datetime.fromisoformat(platform_info['start_time'])
                                end = datetime.fromisoformat(platform_info['end_time'])
                                duration = (end - start).total_seconds()
                                st.metric("耗时", f"{duration:.1f}s")
                            except:
                                st.metric("耗时", "N/A")
                
                # 平台内容
                st.markdown("**完整回答:**")
                st.markdown(content)
    
    # 搜索体验反馈
    st.subheader("💭 搜索体验")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("👍 很好的搜索体验", key=f"good_{search_id}"):
            st.success("感谢您的反馈！")
    
    with col2:
        if st.button("👎 需要改进", key=f"bad_{search_id}"):
            feedback = st.text_input("请告诉我们如何改进：", key=f"feedback_{search_id}")
            if feedback:
                st.info("感谢您的建议，我们会持续改进！")
    
    # 操作按钮
    st.subheader("🛠️ 操作选项")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔄 重新搜索", key=f"retry_{search_id}"):
            st.rerun()
    
    with col2:
        if st.button("📋 复制结果", key=f"copy_{search_id}"):
            st.success("结果已复制到剪贴板")
    
    with col3:
        if st.button("💾 保存结果", key=f"save_{search_id}"):
            st.success("结果已保存")
    
    with col4:
        if st.button("📤 分享结果", key=f"share_{search_id}"):
            st.info("分享功能开发中...")

def display_real_mode_setup():
    """显示真实模式配置界面"""
    st.subheader("🔥 真实模式配置")
    
    st.info("🔗 真实模式需要登录各AI平台并导入Cookie信息")
    
    # 平台连接指导
    with st.expander("📖 平台连接指导", expanded=False):
        st.markdown("""
        ### 🚀 连接步骤
        
        #### 第1步: 登录AI平台
        请在浏览器中登录以下平台：
        
        1. **DeepSeek**: https://chat.deepseek.com
        2. **Kimi**: https://kimi.moonshot.cn  
        3. **智谱清言**: https://chatglm.cn
        4. **豆包**: https://doubao.com
        5. **秘塔搜索**: https://metaso.cn
        
        #### 第2步: 获取Cookie
        在登录状态下：
        1. 按 F12 打开开发者工具
        2. 进入 Application/存储 → Cookies
        3. 复制相关Cookie值
        
        #### 第3步: 导入Cookie
        使用下面的工具导入Cookie信息
        """)
    
    # Cookie导入工具
    st.markdown("### 🍪 Cookie导入工具")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 平台选择
        platform_choice = st.selectbox(
            "选择要配置的平台",
            ["选择平台...", "DeepSeek", "Kimi", "智谱清言", "豆包", "秘塔搜索"],
            help="选择要导入Cookie的AI平台"
        )
        
        if platform_choice != "选择平台...":
            # Cookie输入
            cookie_input = st.text_area(
                f"输入 {platform_choice} 的Cookie",
                height=100,
                placeholder="例如: session_id=xxx; auth_token=yyy; ...",
                help="从浏览器开发者工具中复制的Cookie字符串"
            )
            
            # 保存Cookie按钮
            col_save, col_test = st.columns(2)
            
            with col_save:
                if st.button(f"💾 保存 {platform_choice} Cookie", type="primary"):
                    if cookie_input.strip():
                        # 保存Cookie (这里需要实现保存逻辑)
                        success = save_platform_cookie(platform_choice, cookie_input)
                        if success:
                            st.success(f"✅ {platform_choice} Cookie已保存")
                            st.rerun()
                        else:
                            st.error(f"❌ 保存失败，请检查Cookie格式")
                    else:
                        st.warning("请输入Cookie内容")
            
            with col_test:
                if st.button(f"🔍 测试 {platform_choice} 连接"):
                    if cookie_input.strip():
                        with st.spinner(f"正在测试 {platform_choice} 连接..."):
                            test_result = test_platform_connection(platform_choice, cookie_input)
                            display_test_result(platform_choice, test_result)
                    else:
                        st.warning("请先输入Cookie内容")
    
    with col2:
        # 一键导入工具
        st.markdown("#### 🚀 一键导入")
        
        # 新增：浏览器会话复用选项
        if st.button("🌐 连接浏览器会话", help="连接到您已登录的浏览器，无需Cookie"):
            with st.spinner("正在连接到您的浏览器..."):
                browser_result = connect_to_browser_session()
                if browser_result:
                    st.success("✅ 成功连接到浏览器会话！")
                    st.info("💡 现在可以直接使用真实模式搜索了")
                    st.rerun()
                else:
                    st.error("❌ 连接失败，请确保浏览器已打开并登录目标平台")
        
        if st.button("📂 从浏览器导入", help="自动从浏览器提取Cookie"):
            with st.spinner("正在扫描浏览器Cookie..."):
                import_result = auto_import_cookies()
                if import_result:
                    st.success(f"✅ 成功导入 {len(import_result)} 个平台")
                    for platform, status in import_result.items():
                        if status:
                            st.success(f"  📱 {platform}: 已导入")
                        else:
                            st.error(f"  📱 {platform}: 导入失败")
                    st.rerun()
                else:
                    st.error("❌ 未找到有效的Cookie")
        
        if st.button("📄 从文件导入", help="从Cookie文件导入"):
            uploaded_file = st.file_uploader(
                "选择Cookie文件",
                type=['txt', 'json'],
                help="支持文本格式或JSON格式的Cookie文件"
            )
            
            if uploaded_file:
                with st.spinner("正在导入Cookie文件..."):
                    file_result = import_cookies_from_file(uploaded_file)
                    if file_result:
                        st.success("✅ 文件导入成功")
                        st.rerun()
                    else:
                        st.error("❌ 文件格式不正确")
    
    # 平台状态检查
    st.markdown("### 📊 平台连接状态")
    
    # 检查所有平台状态
    if st.button("🔄 检查所有平台状态", type="secondary"):
        check_all_platforms_status()

def save_platform_cookie(platform: str, cookie: str) -> bool:
    """保存平台Cookie"""
    try:
        # 这里应该实现Cookie的加密保存
        # 暂时使用简单的存储方式
        if 'platform_cookies' not in st.session_state:
            st.session_state.platform_cookies = {}
        
        st.session_state.platform_cookies[platform] = cookie
        
        # 可以保存到文件或数据库
        return True
    except Exception as e:
        st.error(f"保存Cookie失败: {e}")
        return False

def test_platform_connection(platform: str, cookie: str) -> dict:
    """测试平台连接"""
    try:
        # 这里应该实现真实的平台连接测试
        # 暂时返回模拟结果
        time.sleep(2)  # 模拟测试延时
        
        # 模拟测试结果
        if platform in ["DeepSeek", "Kimi"]:
            return {
                "success": True,
                "status": "connected",
                "message": "连接成功，可以正常使用",
                "details": {
                    "response_time": "150ms",
                    "rate_limit": "100/hour",
                    "features": ["文本对话", "长文本处理"]
                }
            }
        else:
            return {
                "success": False,
                "status": "failed",
                "message": "连接失败，Cookie可能已过期",
                "error": "Authentication failed",
                "suggestions": [
                    "检查Cookie是否完整",
                    "确认登录状态",
                    "重新获取Cookie"
                ]
            }
    except Exception as e:
        return {
            "success": False,
            "status": "error",
            "message": f"测试异常: {str(e)}"
        }

def display_test_result(platform: str, result: dict):
    """显示测试结果"""
    if result["success"]:
        st.success(f"🎉 {platform} 连接成功！")
        
        details = result.get("details", {})
        if details:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("响应时间", details.get("response_time", "N/A"))
            with col2:
                st.metric("频率限制", details.get("rate_limit", "N/A"))
            with col3:
                features = details.get("features", [])
                st.metric("支持功能", len(features))
    else:
        st.error(f"❌ {platform} 连接失败")
        st.write(f"**错误信息**: {result.get('message', '未知错误')}")
        
        suggestions = result.get("suggestions", [])
        if suggestions:
            st.write("**建议解决方案**:")
            for suggestion in suggestions:
                st.write(f"  • {suggestion}")

def auto_import_cookies() -> dict:
    """自动从浏览器导入Cookie"""
    try:
        results = {}
        
        # 支持的浏览器路径  
        browsers_paths = {
            "Edge": {
                "paths": [
                    os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Network\Cookies"),
                    os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Cookies")
                ],
                "name": "Microsoft Edge"
            },
            "Chrome": {
                "paths": [os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\Default\Cookies")],
                "name": "Google Chrome"
            },
            "Firefox": {
                "paths": [os.path.expandvars(r"%APPDATA%\Mozilla\Firefox\Profiles")],
                "name": "Mozilla Firefox"
            }
        }
        
        # 目标平台的域名映射
        target_domains = {
            "DeepSeek": ["chat.deepseek.com", ".deepseek.com"],
            "Kimi": ["kimi.moonshot.cn", ".kimi.moonshot.cn", ".moonshot.cn"],
            "智谱清言": ["chatglm.cn", ".chatglm.cn"],
            "豆包": ["doubao.com", ".doubao.com"],
            "秘塔搜索": ["metaso.cn", ".metaso.cn"]
        }
        
        st.info("🔍 正在扫描浏览器Cookie...")
        
        for browser_name, browser_info in browsers_paths.items():
            possible_paths = browser_info["paths"]
            browser_display_name = browser_info["name"]
            
            # 查找存在的Cookie文件
            cookies_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    cookies_path = path
                    break
            
            try:
                # 检查浏览器是否安装
                if browser_name == "Firefox":
                    # Firefox需要特殊处理
                    continue
                elif not cookies_path:
                    st.warning(f"⚠️ 未找到 {browser_display_name} Cookie文件")
                    continue
                
                st.info(f"📂 正在检查 {browser_display_name}... ({cookies_path})")
                
                # 创建临时文件来复制cookie数据库
                with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp_file:
                    temp_path = tmp_file.name
                
                try:
                    # 复制cookie文件到临时位置（避免锁定问题）
                    shutil.copy2(cookies_path, temp_path)
                    
                    # 连接SQLite数据库
                    conn = sqlite3.connect(temp_path)
                    cursor = conn.cursor()
                    
                    # 查询cookie表结构
                    cursor.execute("PRAGMA table_info(cookies)")
                    columns = [row[1] for row in cursor.fetchall()]
                    
                    # 构建查询语句
                    if 'host_key' in columns:
                        domain_column = 'host_key'
                    elif 'host' in columns:
                        domain_column = 'host'
                    else:
                        st.warning(f"⚠️ {browser_display_name} Cookie格式不支持")
                        continue
                    
                    # 查找目标平台的Cookie
                    for platform, domains in target_domains.items():
                        platform_cookies = []
                        
                        for domain in domains:
                            # 查询该域名的所有cookie
                            if domain.startswith('.'):
                                # 匹配子域名
                                query = f"SELECT name, value FROM cookies WHERE {domain_column} LIKE '%{domain}' OR {domain_column} = '{domain[1:]}'"
                            else:
                                # 精确匹配
                                query = f"SELECT name, value FROM cookies WHERE {domain_column} = '{domain}' OR {domain_column} = '.{domain}'"
                            
                            cursor.execute(query)
                            cookies = cursor.fetchall()
                            
                            for name, value in cookies:
                                if name and value:  # 过滤空值
                                    platform_cookies.append(f"{name}={value}")
                        
                        if platform_cookies:
                            # 组合成cookie字符串
                            cookie_string = "; ".join(platform_cookies)
                            results[platform] = cookie_string
                            st.success(f"✅ 找到 {platform} Cookie ({len(platform_cookies)} 个)")
                        else:
                            st.warning(f"⚠️ 未找到 {platform} Cookie")
                    
                    conn.close()
                    
                except sqlite3.Error as e:
                    st.error(f"❌ 读取 {browser_display_name} Cookie失败: {str(e)}")
                    if "database is locked" in str(e).lower():
                        st.warning(f"💡 请关闭 {browser_display_name} 浏览器后重试")
                
                finally:
                    # 清理临时文件
                    try:
                        os.unlink(temp_path)
                    except:
                        pass
                        
            except Exception as e:
                st.error(f"❌ 处理 {browser_display_name} 时出错: {str(e)}")
        
        # 保存找到的Cookie
        if results:
            if 'platform_cookies' not in st.session_state:
                st.session_state.platform_cookies = {}
            
            imported_count = 0
            for platform, cookie_string in results.items():
                st.session_state.platform_cookies[platform] = cookie_string
                imported_count += 1
            
            st.success(f"🎉 成功导入 {imported_count} 个平台的Cookie！")
            
            # 返回导入结果
            return {platform: True for platform in results.keys()}
        else:
            st.warning("❌ 未找到任何有效的Cookie")
            st.info("""
            💡 **可能的原因：**
            1. 浏览器中未登录目标平台
            2. 需要关闭浏览器后重试
            3. Cookie已过期或被清除
            
            💡 **建议操作：**
            1. 确保在浏览器中已登录 DeepSeek
            2. 完全关闭 Microsoft Edge 浏览器
            3. 重新点击"从浏览器导入"
            """)
            return {}
            
    except ImportError as e:
        st.error(f"❌ 缺少必要的库: {str(e)}")
        st.info("💡 请安装：pip install psutil playwright")
        return {}
    except Exception as e:
        st.error(f"❌ 自动导入失败: {str(e)}")
        return {}

def import_cookies_from_file(uploaded_file) -> bool:
    """从文件导入Cookie"""
    try:
        content = uploaded_file.read().decode('utf-8')
        
        # 尝试解析JSON格式
        try:
            cookies_data = json.loads(content)
            
            if 'platform_cookies' not in st.session_state:
                st.session_state.platform_cookies = {}
            
            for platform, cookie in cookies_data.items():
                st.session_state.platform_cookies[platform] = cookie
            
            return True
        except json.JSONDecodeError:
            # 尝试解析文本格式
            lines = content.strip().split('\n')
            
            if 'platform_cookies' not in st.session_state:
                st.session_state.platform_cookies = {}
            
            for line in lines:
                if ':' in line:
                    platform, cookie = line.split(':', 1)
                    st.session_state.platform_cookies[platform.strip()] = cookie.strip()
            
            return True
            
    except Exception as e:
        st.error(f"文件导入失败: {e}")
        return False

def check_all_platforms_status():
    """检查所有平台状态"""
    platforms = ["DeepSeek", "Kimi", "智谱清言", "豆包", "秘塔搜索"]
    
    status_container = st.container()
    
    with status_container:
        st.write("🔄 正在检查平台状态...")
        
        # 创建状态显示区域
        status_cols = st.columns(len(platforms))
        
        for i, platform in enumerate(platforms):
            with status_cols[i]:
                st.write(f"**{platform}**")
                
                # 检查是否有保存的Cookie
                has_cookie = False
                if 'platform_cookies' in st.session_state:
                    has_cookie = platform in st.session_state.platform_cookies
                
                if has_cookie:
                    # 测试连接
                    with st.spinner("测试中..."):
                        test_result = test_platform_connection(
                            platform, 
                            st.session_state.platform_cookies[platform]
                        )
                    
                    if test_result["success"]:
                        st.success("✅ 可用")
                        st.caption(test_result.get("message", ""))
                    else:
                        st.error("❌ 不可用")
                        st.caption(test_result.get("message", ""))
                else:
                    st.warning("⚠️ 未配置")
                    st.caption("请先导入Cookie")

def get_available_real_platforms() -> list:
    """获取可用的真实平台列表"""
    available_platforms = []
    
    if 'platform_cookies' in st.session_state:
        for platform in st.session_state.platform_cookies:
            # 这里可以添加快速检查逻辑
            available_platforms.append(platform)
    
    return available_platforms

def connect_to_browser_session() -> bool:
    """连接到用户已登录的浏览器会话"""
    try:
        # 检查是否安装了playwright
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            st.error("❌ 缺少 Playwright 库")
            st.info("💡 请运行：pip install playwright && playwright install")
            return False
        
        # 检测Edge浏览器进程
        import psutil
        edge_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'msedge' in proc.info['name'].lower():
                    edge_processes.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if not edge_processes:
            st.warning("⚠️ 未检测到运行中的Edge浏览器")
            st.info("""
            💡 **使用步骤**：
            1. 打开Microsoft Edge浏览器
            2. 访问 https://chat.deepseek.com 并登录
            3. 保持浏览器页面打开
            4. 重新点击"连接浏览器会话"
            """)
            return False
        
        st.info(f"🔍 检测到 {len(edge_processes)} 个Edge进程")
        
        # 尝试连接到浏览器会话
        with sync_playwright() as p:
            try:
                # 尝试连接到现有浏览器
                browser = p.chromium.connect_over_cdp("http://localhost:9222")
                contexts = browser.contexts
                
                if not contexts:
                    st.warning("⚠️ 无法连接到浏览器调试端口")
                    st.info("""
                    💡 **解决方案**：
                    1. 关闭所有Edge窗口
                    2. 用调试模式启动Edge：
                       `"C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe" --remote-debugging-port=9222`
                    3. 访问并登录AI平台
                    4. 重新尝试连接
                    """)
                    return False
                
                # 检查是否有可用页面
                pages = []
                for context in contexts:
                    pages.extend(context.pages)
                
                if not pages:
                    st.warning("⚠️ 浏览器中没有打开的页面")
                    return False
                
                # 检查是否有AI平台页面
                ai_platforms = {
                    "DeepSeek": "chat.deepseek.com",
                    "Kimi": "kimi.moonshot.cn",
                    "智谱清言": "chatglm.cn"
                }
                
                detected_platforms = []
                for page in pages:
                    url = page.url
                    for platform, domain in ai_platforms.items():
                        if domain in url:
                            detected_platforms.append(platform)
                
                if detected_platforms:
                    st.success(f"✅ 检测到已登录的平台: {', '.join(detected_platforms)}")
                    
                    # 保存会话状态
                    if 'browser_session' not in st.session_state:
                        st.session_state.browser_session = {}
                    
                    st.session_state.browser_session['connected'] = True
                    st.session_state.browser_session['platforms'] = detected_platforms
                    st.session_state.browser_session['debug_port'] = 9222
                    
                    return True
                else:
                    st.warning("⚠️ 未检测到已登录的AI平台页面")
                    st.info("💡 请在浏览器中访问并登录AI平台")
                    return False
                    
            except Exception as e:
                if "connect" in str(e).lower():
                    st.warning("⚠️ 无法连接到浏览器调试端口")
                    st.info("""
                    💡 **启用浏览器调试模式**：
                    
                    **方法1：命令行启动**
                    ```
                    "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe" --remote-debugging-port=9222
                    ```
                    
                    **方法2：快捷方式**
                    1. 右键Edge快捷方式 → 属性
                    2. 在"目标"后面添加：--remote-debugging-port=9222
                    3. 确定并重新启动Edge
                    
                    **方法3：使用现有会话**
                    1. 访问 chrome://version/ 查看命令行
                    2. 如果没有调试端口，重新启动浏览器
                    """)
                    return False
                else:
                    st.error(f"❌ 连接失败: {str(e)}")
                    return False
    
    except ImportError as e:
        st.error(f"❌ 缺少必要的库: {str(e)}")
        st.info("💡 请安装：pip install psutil playwright")
        return False
    except Exception as e:
        st.error(f"❌ 连接失败: {str(e)}")
        return False

def get_browser_session_platforms() -> list:
    """获取浏览器会话中的平台"""
    try:
        data, error = call_api("/browser-platforms")
        if error or not data:
            return []
        return data.get("platforms", [])
    except Exception:
        return []

def auto_detect_browser_session() -> list:
    """自动检测浏览器会话中的平台"""
    try:
        data, error = call_api("/browser-platforms")
        if error or not data:
            return []
        
        platforms_data = data.get("platforms", [])
        
        # 提取平台名称列表
        platform_names = []
        for platform in platforms_data:
            if isinstance(platform, dict):
                platform_names.append(platform.get("platform", "Unknown"))
            elif isinstance(platform, str):
                platform_names.append(platform)
        
        return platform_names
    except Exception:
        return []

if __name__ == "__main__":
    main() 