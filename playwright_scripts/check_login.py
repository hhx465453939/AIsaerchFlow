from playwright.sync_api import sync_playwright

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

def check_login_status(platform, cookie):
    url = PLATFORM_URLS.get(platform)
    if not url:
        return "未知平台"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        if cookie:
            try:
                context.add_cookies(cookie)
            except Exception:
                pass
        page = context.new_page()
        page.goto(url)
        # TODO: 针对每个平台定制检测已登录的元素
        try:
            if platform == "DeepSeek":
                page.wait_for_selector(".user-avatar", timeout=5000)
            elif platform == "Kimi":
                page.wait_for_selector(".user-info", timeout=5000)
            # ... 其他平台可补充
            else:
                page.wait_for_timeout(3000)
            browser.close()
            return "已登录"
        except Exception:
            browser.close()
            return "未登录" 