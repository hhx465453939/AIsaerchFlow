import streamlit as st
import requests
import os
import json
from typing import Dict, Any, Optional

API_URL = "http://localhost:8000"
PLATFORMS = [
    "DeepSeek", "Kimi", "智谱清言", "秘塔搜索", "豆包", "Qwen", "MiniMax", "ChatGPT", "Gemini"
]
PLATFORM_URLS = {
    "DeepSeek": "https://chat.deepseek.com/",
    "Kimi": "https://kimi.moonshot.cn/",
    "智谱清言": "https://chatglm.cn/main/alltoolsdetail?lang=zh",
    "秘塔搜索": "https://metaso.cn/",
    "豆包": "https://www.doubao.com/chat/",
    "Qwen": "https://chat.qwen.ai/",
    "MiniMax": "https://chat.minimaxi.com/",
    "ChatGPT": "https://chatgpt.com/",
    "Gemini": "https://gemini.google.com/app?hl=zh-cn",
}

st.set_page_config(page_title="多平台AI搜索 v2.0", layout="wide")
st.title("🤖 多平台AI搜索聚合 v2.0")
st.markdown("*集成AI整合、事实核查、语义去重的智能搜索平台*")

# 初始化会话状态
if "accounts" not in st.session_state:
    st.session_state["accounts"] = {}
if "login_status" not in st.session_state:
    st.session_state["login_status"] = {}
if "llm_config" not in st.session_state:
    st.session_state["llm_config"] = {
        "base_url": "https://api.openai.com/v1",
        "api_key": "",
        "model": "gpt-3.5-turbo",
        "temperature": 0.3,
        "max_tokens": 4000
    }
if "agg_prompt" not in st.session_state:
    # 默认加载文档架构师提示词
    try:
        with open("prompt/# Role：文档架构师.md", encoding="utf-8") as f:
            st.session_state["agg_prompt"] = f.read()
    except Exception:
        st.session_state["agg_prompt"] = "请填写聚合提示词"
if "browser_choice" not in st.session_state:
    st.session_state["browser_choice"] = "Edge"
if "user_data_dir" not in st.session_state:
    st.session_state["user_data_dir"] = ""
if "ai_features" not in st.session_state:
    st.session_state["ai_features"] = {
        "use_ai_integration": True,
        "enable_fact_check": True,
        "semantic_deduplication": True
    }

# 主界面
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("🔍 搜索配置")
    user_input = st.text_input("请输入你的搜索内容：", key="search_input")
    platforms = st.multiselect("选择平台：", PLATFORMS, default=["DeepSeek", "Kimi"], key="platforms")
    
    # AI功能控制
    st.subheader("🧠 AI增强功能")
    col_ai1, col_ai2, col_ai3 = st.columns(3)
    
    with col_ai1:
        use_ai_integration = st.checkbox(
            "启用AI整合", 
            value=st.session_state["ai_features"]["use_ai_integration"],
            help="使用AI模型进行智能去重和信息整合"
        )
        st.session_state["ai_features"]["use_ai_integration"] = use_ai_integration
    
    with col_ai2:
        enable_fact_check = st.checkbox(
            "启用事实核查", 
            value=st.session_state["ai_features"]["enable_fact_check"],
            help="对搜索结果进行联网事实核查"
        )
        st.session_state["ai_features"]["enable_fact_check"] = enable_fact_check
    
    with col_ai3:
        semantic_deduplication = st.checkbox(
            "语义去重", 
            value=st.session_state["ai_features"]["semantic_deduplication"],
            help="基于语义相似度进行智能去重"
        )
        st.session_state["ai_features"]["semantic_deduplication"] = semantic_deduplication

with col2:
    st.subheader("⚙️ 状态监控")
    
    # 显示API健康状态
    try:
        health_resp = requests.get(f"{API_URL}/health", timeout=5)
        if health_resp.ok:
            health_data = health_resp.json()
            st.success(f"✅ API状态: {health_data['status']}")
            st.info(f"版本: {health_data['version']}")
        else:
            st.error("❌ API连接失败")
    except:
        st.error("❌ API不可用")
    
    # LLM配置状态
    if st.session_state["llm_config"]["api_key"]:
        st.success("✅ LLM已配置")
    else:
        st.warning("⚠️ 未配置LLM")

# 侧边栏：详细配置
st.sidebar.header("🔧 详细配置")

# LLM配置
st.sidebar.subheader("🤖 LLM配置")
st.sidebar.markdown("*AI整合和事实核查需要LLM支持*")

llm_base_url = st.sidebar.text_input(
    "LLM Base URL", 
    value=st.session_state["llm_config"]["base_url"],
    help="如: https://api.openai.com/v1 或 https://api.siliconflow.cn/v1"
)
llm_api_key = st.sidebar.text_input(
    "API Key", 
    type="password",
    value=st.session_state["llm_config"]["api_key"],
    help="LLM服务的API密钥"
)
llm_model = st.sidebar.text_input(
    "模型名称", 
    value=st.session_state["llm_config"]["model"],
    help="如: gpt-3.5-turbo, qwen-vl-plus"
)

col_temp, col_tokens = st.sidebar.columns(2)
with col_temp:
    llm_temperature = st.number_input(
        "Temperature", 
        min_value=0.0, max_value=2.0, 
        value=st.session_state["llm_config"]["temperature"],
        step=0.1
    )
with col_tokens:
    llm_max_tokens = st.number_input(
        "Max Tokens", 
        min_value=100, max_value=8000,
        value=st.session_state["llm_config"]["max_tokens"],
        step=100
    )

# 更新LLM配置
st.session_state["llm_config"].update({
    "base_url": llm_base_url,
    "api_key": llm_api_key,
    "model": llm_model,
    "temperature": llm_temperature,
    "max_tokens": llm_max_tokens
})

# 验证LLM配置
if st.sidebar.button("🔍 验证LLM配置"):
    if llm_api_key and llm_base_url:
        with st.sidebar.spinner("验证中..."):
            try:
                resp = requests.post(f"{API_URL}/validate-llm-config", json={
                    "base_url": llm_base_url,
                    "api_key": llm_api_key,
                    "model": llm_model,
                    "temperature": llm_temperature,
                    "max_tokens": llm_max_tokens
                })
                if resp.ok:
                    result = resp.json()
                    if result["valid"]:
                        st.sidebar.success(f"✅ {result['message']}")
                    else:
                        st.sidebar.error(f"❌ {result['message']}")
                else:
                    st.sidebar.error("❌ 验证失败")
            except Exception as e:
                st.sidebar.error(f"❌ 验证异常: {e}")
    else:
        st.sidebar.warning("⚠️ 请填写完整的LLM配置")

# 浏览器配置
st.sidebar.subheader("🌐 浏览器配置")
browser_choice = st.sidebar.selectbox(
    "选择自动化浏览器", 
    ["Edge", "Chrome", "自定义路径"], 
    key="browser_choice"
)
if browser_choice == "自定义路径":
    user_data_dir = st.sidebar.text_input("浏览器用户数据目录", key="user_data_dir")
else:
    user_data_dir = ""

# 账号管理
st.sidebar.subheader("👤 账号管理")
if st.sidebar.button("🔄 一键检测/导入登录状态"):
    with st.sidebar.spinner("检测中..."):
        # 这里可以添加自动导入逻辑
        st.sidebar.info("请使用 import_edge_cookie.py 导入Cookie")

# 显示登录状态
for platform in platforms:
    status = st.session_state["login_status"].get(platform, "未检测")
    if status == "已登录":
        st.sidebar.success(f"✅ {platform}")
    else:
        st.sidebar.warning(f"⚠️ {platform}: {status}")
        if st.sidebar.button(f"前往 {platform} 登录", key=f"goto_{platform}"):
            st.sidebar.markdown(f"[点击前往]({PLATFORM_URLS[platform]})")

# 搜索执行
st.markdown("---")
col_search1, col_search2 = st.columns(2)

with col_search1:
    if st.button("🚀 AI增强搜索", type="primary", use_container_width=True):
        if not user_input:
            st.error("请输入搜索内容")
        elif not platforms:
            st.error("请选择至少一个平台")
        else:
            # 检查AI功能配置
            if use_ai_integration and not llm_api_key:
                st.warning("启用了AI整合但未配置LLM，将使用传统搜索")
                use_ai_integration = False
            
            with st.spinner("🔄 AI增强搜索中..."):
                try:
                    # 准备请求数据
                    search_data = {
                        "user_input": user_input,
                        "platforms": platforms,
                        "use_ai_integration": use_ai_integration,
                        "enable_fact_check": enable_fact_check and use_ai_integration,
                        "browser_config": {
                            "browser": browser_choice,
                            "user_data_dir": user_data_dir
                        }
                    }
                    
                    # 添加LLM配置
                    if use_ai_integration and llm_api_key:
                        search_data["llm_config"] = st.session_state["llm_config"]
                    
                    # 发送请求
                    resp = requests.post(f"{API_URL}/ai-search", json=search_data, timeout=300)
                    
                    if resp.ok:
                        result = resp.json()
                        if result["success"]:
                            data = result["data"]
                            
                            # 显示处理信息
                            st.success("🎉 AI增强搜索完成！")
                            
                            # 显示处理统计
                            processing_info = data["processing_info"]
                            col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
                            
                            with col_stat1:
                                st.metric("原始结果", processing_info["total_results_count"])
                            with col_stat2:
                                st.metric("有效结果", processing_info["valid_results_count"])
                            with col_stat3:
                                st.metric("AI整合", "✅" if processing_info["ai_integration_enabled"] else "❌")
                            with col_stat4:
                                st.metric("事实核查", "✅" if processing_info["fact_check_enabled"] else "❌")
                            
                            # 显示整合结果
                            st.subheader("📄 整合文档")
                            integration_result = data["integration_result"]
                            integrated_content = integration_result["integrated_document"]["integrated_content"]
                            st.markdown(integrated_content)
                            
                            # 显示处理详情
                            with st.expander("🔍 处理详情"):
                                for i, content in enumerate(integration_result["processed_contents"]):
                                    st.write(f"**来源 {i+1}: {content['platform']}**")
                                    st.write(f"可信度: {content['confidence_score']:.2f}")
                                    st.write(f"事实核查: {'✅' if content['fact_checked'] else '❌'}")
                                    st.text_area(f"内容 {i+1}", content['content'], height=100, key=f"content_{i}")
                                    st.markdown("---")
                            
                            # 显示原始结果
                            with st.expander("📊 原始结果"):
                                for platform, raw_result in data["raw_results"]:
                                    st.write(f"**{platform}:**")
                                    st.text(raw_result)
                                    st.markdown("---")
                        else:
                            st.error("搜索失败")
                    else:
                        st.error(f"请求失败: {resp.status_code}")
                        
                except Exception as e:
                    st.error(f"搜索异常: {e}")

with col_search2:
    if st.button("🔍 传统搜索", use_container_width=True):
        if not user_input:
            st.error("请输入搜索内容")
        elif not platforms:
            st.error("请选择至少一个平台")
        else:
            with st.spinner("🔄 传统搜索中..."):
                try:
                    resp = requests.post(f"{API_URL}/search", json={
                        "user_input": user_input,
                        "platforms": platforms
                    }, timeout=300)
                    
                    if resp.ok:
                        data = resp.json()
                        st.success("✅ 传统搜索完成")
                        
                        st.subheader("📄 去重后结果")
                        for i, item in enumerate(data["results"]):
                            st.text_area(f"结果 {i+1}", item, height=100, key=f"trad_{i}")
                        
                        with st.expander("📊 原始结果"):
                            for platform, result in data["raw"]:
                                st.write(f"**{platform}:**")
                                st.text(result)
                                st.markdown("---")
                    else:
                        st.error("搜索失败")
                        
                except Exception as e:
                    st.error(f"搜索异常: {e}")

# 底部信息
st.markdown("---")
st.markdown("### 💡 使用提示")
st.markdown("""
- **AI增强搜索**: 使用AI模型进行智能去重、信息整合和事实核查
- **传统搜索**: 使用简单去重，无需LLM配置
- **配置LLM**: 支持OpenAI、SiliconFlow等兼容OpenAI API的服务
- **事实核查**: 对搜索结果进行可信度评估和事实验证
- **语义去重**: 基于内容语义而非文本相似度进行去重
""")

# 状态栏
if st.session_state["ai_features"]["use_ai_integration"]:
    if st.session_state["llm_config"]["api_key"]:
        st.success("🤖 AI增强模式已启用")
    else:
        st.warning("⚠️ AI增强模式需要配置LLM")
else:
    st.info("ℹ️ 当前使用传统模式") 