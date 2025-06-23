import os
from playwright.sync_api import sync_playwright
from backend.account_manager import save_cookie

EDGE_USER_DATA_DIR = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data")
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

# 支持容错的名称映射
PLATFORM_NAME_MAP = {k.lower(): k for k in PLATFORM_URLS}


def main():
    print("支持平台：", list(PLATFORM_URLS.keys()))
    raw_input_name = input("请输入平台名（如 DeepSeek）：").strip()
    # 去除前后引号和空格，忽略大小写
    input_name = raw_input_name.strip("'\" ").lower()
    platform = PLATFORM_NAME_MAP.get(input_name)
    if not platform:
        print("不支持的平台名！")
        return
    url = PLATFORM_URLS[platform]
    print(f"请确保 Edge 浏览器已关闭！\n正在读取 {platform} 登录状态...")
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(EDGE_USER_DATA_DIR, headless=False, channel="msedge")
        page = browser.new_page()
        page.goto(url)
        input(f"请确保页面已登录并加载完成，然后按回车继续...")
        cookies = browser.cookies()
        save_cookie(platform, cookies)
        print(f"{platform} 的Cookie已加密保存，可用于自动化登录！")
        browser.close()

if __name__ == "__main__":
    main() 