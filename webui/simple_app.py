"""
简化版Web界面
专注于核心的多平台搜索聚合功能
"""

import streamlit as st
import requests
import json
import time
from datetime import datetime
import logging

# 页面配置
st.set_page_config(
    page_title="AI多平台搜索聚合器",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .search-container {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .result-container {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #dee2e6;
        margin-bottom: 1rem;
    }
    .platform-tag {
        background-color: #007bff;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 5px;
        font-size: 0.8rem;
        margin-right: 0.5rem;
    }
    .status-success {
        color: #28a745;
        font-weight: bold;
    }
    .status-error {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# API配置
API_BASE_URL = "http://localhost:8000"

def call_api(endpoint, method="GET", data=None):
    """调用API"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url, timeout=60)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=60)
        
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"API错误: {response.status_code}"
    except requests.exceptions.ConnectionError:
        return None, "无法连接到后端服务，请确保服务已启动"
    except requests.exceptions.Timeout:
        return None, "请求超时，搜索可能需要更长时间"
    except Exception as e:
        return None, f"请求失败: {str(e)}"

def main():
    # 主标题
    st.markdown('<h1 class="main-header">🔍 AI多平台搜索聚合器</h1>', unsafe_allow_html=True)
    
    # 侧边栏配置
    with st.sidebar:
        st.header("⚙️ 配置")
        
        # 后端状态检查
        health_data, health_error = call_api("/")
        if health_data:
            st.success(f"✅ 服务状态: {health_data['status']}")
            st.info(f"版本: {health_data['version']}")
        else:
            st.error(f"❌ 服务异常: {health_error}")
            return
        
        # 平台选择
        st.subheader("📱 选择平台")
        platforms_data, platforms_error = call_api("/platforms")
        
        if platforms_data:
            available_platforms = list(platforms_data.keys())
            selected_platforms = st.multiselect(
                "选择要搜索的平台",
                available_platforms,
                default=["DeepSeek"]
            )
        else:
            st.error(f"获取平台列表失败: {platforms_error}")
            selected_platforms = ["DeepSeek"]
        
        # AI处理选项
        st.subheader("🤖 AI处理")
        enable_ai = st.checkbox("启用AI智能处理", value=False)
        
        if enable_ai:
            ai_service = st.selectbox(
                "AI服务商",
                ["siliconflow", "openai"],
                index=0
            )
            api_key = st.text_input("API Key", type="password")
            prompt_type = st.selectbox(
                "处理类型",
                ["default", "fact_check", "summary"],
                index=0
            )
        else:
            ai_service = None
            api_key = None
            prompt_type = "default"
    
    # 主搜索界面
    st.markdown('<div class="search-container">', unsafe_allow_html=True)
    
    col1, col2 = st.columns([4, 1])
    
    with col1:
        query = st.text_input(
            "🔍 输入搜索问题",
            placeholder="例如: 如何使用Python进行数据分析？",
            key="search_query"
        )
    
    with col2:
        st.write("")  # 空行对齐
        search_button = st.button("🚀 开始搜索", type="primary", use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 处理搜索
    if search_button and query:
        if not selected_platforms:
            st.error("请至少选择一个搜索平台")
            return
        
        # 构建请求
        search_request = {
            "query": query,
            "platforms": selected_platforms,
            "enable_ai_processing": enable_ai
        }
        
        if enable_ai and api_key:
            search_request["ai_config"] = {
                "service": ai_service,
                "api_key": api_key,
                "prompt_type": prompt_type,
                "original_query": query,
                "requirements": "请整理并总结搜索结果"
            }
        
        # 显示搜索状态
        with st.spinner(f"正在搜索 {len(selected_platforms)} 个平台..."):
            # 搜索进度条
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, platform in enumerate(selected_platforms):
                status_text.text(f"正在搜索 {platform}...")
                progress_bar.progress((i + 1) / len(selected_platforms))
                time.sleep(0.5)  # 模拟进度
            
            # 执行搜索
            result_data, result_error = call_api("/search", "POST", search_request)
        
        # 清除进度显示
        progress_bar.empty()
        status_text.empty()
        
        # 显示结果
        if result_data and result_data.get('success'):
            st.success(f"✅ 搜索完成！共获取 {result_data['source_count']} 个有效结果")
            
            # 显示聚合结果
            st.markdown("## 📄 聚合结果")
            
            with st.container():
                st.markdown(result_data['aggregated_content'])
            
            # 显示详细结果
            with st.expander("📋 查看详细结果", expanded=False):
                for i, result in enumerate(result_data['results'], 1):
                    st.markdown(f"""
                    <div class="result-container">
                        <span class="platform-tag">{result['platform']}</span>
                        <small>完成度: {'✅' if result['is_complete'] else '⚠️'} | 
                        可信度: {result['confidence']:.1f} | 
                        时间: {result['timestamp']}</small>
                        <hr>
                        {result['content'][:500]}{'...' if len(result['content']) > 500 else ''}
                    </div>
                    """, unsafe_allow_html=True)
            
            # 显示元数据
            with st.expander("ℹ️ 搜索信息", expanded=False):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("搜索平台", len(selected_platforms))
                with col2:
                    st.metric("有效结果", result_data['source_count'])
                with col3:
                    st.metric("AI处理", "是" if enable_ai else "否")
                
                st.json({
                    "查询": query,
                    "平台": selected_platforms,
                    "处理时间": result_data['processing_time'],
                    "AI处理": enable_ai
                })
        
        else:
            st.error(f"❌ 搜索失败: {result_error}")
    
    # 快速操作
    st.markdown("---")
    st.markdown("### 🚀 快速操作")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 重新搜索", use_container_width=True):
            st.rerun()
    
    with col2:
        if st.button("⏹️ 停止搜索", use_container_width=True):
            stop_data, stop_error = call_api("/stop", "POST")
            if stop_data:
                st.success("搜索已停止")
            else:
                st.error(f"停止失败: {stop_error}")
    
    with col3:
        if st.button("📊 查看配置", use_container_width=True):
            config_data, config_error = call_api("/config")
            if config_data:
                st.json(config_data)
            else:
                st.error(f"获取配置失败: {config_error}")
    
    # 页脚
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #6c757d; font-size: 0.9rem;">
        🔍 AI多平台搜索聚合器 | 流式监控 • 智能聚合 • 实时处理
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 