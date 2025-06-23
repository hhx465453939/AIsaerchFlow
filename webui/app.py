import streamlit as st
import requests
import os

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

st.set_page_config(page_title="多平台AI搜索", layout="wide")
st.title("多平台AI搜索聚合")

if "accounts" not in st.session_state:
    st.session_state["accounts"] = {}
if "login_status" not in st.session_state:
    st.session_state["login_status"] = {}
if "llm_config" not in st.session_state:
    st.session_state["llm_config"] = {"baseurl": "", "api_key": "", "model": ""}
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

user_input = st.text_input("请输入你的搜索内容：")
platforms = st.multiselect("选择平台：", PLATFORMS, default=PLATFORMS)

# 侧边栏：浏览器选择与登录状态导入
st.sidebar.header("账号与环境配置")
st.sidebar.subheader("浏览器选择")
browser_choice = st.sidebar.selectbox("选择自动化浏览器", ["Edge", "Chrome", "自定义路径"], key="browser_choice")
if browser_choice == "自定义路径":
    user_data_dir = st.sidebar.text_input("浏览器用户数据目录", key="user_data_dir")
else:
    user_data_dir = ""

if st.sidebar.button("一键检测/导入登录状态"):
    # 调用后端API导入cookie
    resp = requests.post(f"{API_URL}/import_cookie", json={
        "platforms": platforms,
        "browser": browser_choice,
        "user_data_dir": user_data_dir
    })
    if resp.ok:
        st.sidebar.success("登录状态已导入！")
    else:
        st.sidebar.error("导入失败，请确认浏览器已关闭且路径正确")

# 账号输入区（仅未登录时显示）
need_login = [p for p in platforms if p not in st.session_state["accounts"]]
for p in platforms:
    st.sidebar.subheader(f"{p} 账号")
    st.sidebar.markdown(f"[前往平台登录]({PLATFORM_URLS[p]})", unsafe_allow_html=True)
    status = st.session_state["login_status"].get(p, "未检测")
    st.sidebar.write(f"当前登录状态：{status}")
    if p in need_login:
        if p in ["ChatGPT", "Gemini"]:
            email = st.sidebar.text_input(f"{p} 邮箱", key=f"{p}_email")
            code = st.sidebar.text_input(f"{p} 验证码", key=f"{p}_code")
            if st.sidebar.button(f"保存{p}账号", key=f"save_{p}"):
                st.session_state["accounts"][p] = {"邮箱": email, "验证码": code}
                requests.post(f"{API_URL}/login", json={"platform": p, "account": {"邮箱": email, "验证码": code}})
                st.sidebar.success(f"{p} 账号已保存")
                st.experimental_rerun()
        else:
            phone = st.sidebar.text_input(f"{p} 手机号", key=f"{p}_phone")
            code = st.sidebar.text_input(f"{p} 验证码", key=f"{p}_code")
            if st.sidebar.button(f"保存{p}账号", key=f"save_{p}"):
                st.session_state["accounts"][p] = {"手机号": phone, "验证码": code}
                requests.post(f"{API_URL}/login", json={"platform": p, "account": {"手机号": phone, "验证码": code}})
                st.sidebar.success(f"{p} 账号已保存")
                st.experimental_rerun()

# LLM供应商配置区
st.sidebar.header("LLM供应商配置")
st.session_state["llm_config"]["baseurl"] = st.sidebar.text_input("LLM BaseURL", value=st.session_state["llm_config"].get("baseurl", ""))
st.session_state["llm_config"]["api_key"] = st.sidebar.text_input("LLM API Key", value=st.session_state["llm_config"].get("api_key", ""))
st.session_state["llm_config"]["model"] = st.sidebar.text_input("模型名", value=st.session_state["llm_config"].get("model", ""))

# 聚合提示词区
st.sidebar.header("聚合提示词")
st.session_state["agg_prompt"] = st.sidebar.text_area("聚合提示词", value=st.session_state["agg_prompt"], height=200)

# 搜索前自动检测登录状态
def check_all_login():
    for p in platforms:
        resp = requests.post(f"{API_URL}/check_login", json={"platform": p})
        if resp.ok:
            st.session_state["login_status"][p] = resp.json()["status"]
        else:
            st.session_state["login_status"][p] = "检测失败"

if st.button("一键搜索"):
    check_all_login()
    not_logged = [p for p in platforms if st.session_state["login_status"].get(p) != "已登录"]
    if not_logged:
        st.warning(f'以下平台未登录，请点击左侧"前往平台登录"手动登录后重试：{", ".join(not_logged)}')
    else:
        with st.spinner("正在聚合搜索..."):
            resp = requests.post(f"{API_URL}/search", json={
                "user_input": user_input,
                "platforms": platforms,
                "llm_config": st.session_state["llm_config"],
                "agg_prompt": st.session_state["agg_prompt"],
                "browser": browser_choice,
                "user_data_dir": user_data_dir
            })
            if resp.ok:
                data = resp.json()
                st.subheader("聚合去重后结果：")
                for item in data["results"]:
                    st.write(item)
                st.expander("原始平台结果").write(data["raw"])
            else:
                st.error("搜索失败") 