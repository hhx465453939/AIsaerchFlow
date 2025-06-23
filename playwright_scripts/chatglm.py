from playwright.sync_api import sync_playwright

def run(optimized_query, account=None, headless=False):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()
        # 1. 打开首页
        page.goto("https://chatglm.cn/main/alltoolsdetail?lang=zh")
        # 2. 登录（手机号+验证码，留空）
        # TODO: 自动登录可用account参数
        # 3. 搜索操作
        # 开启沉思+联网模式
        try:
            page.click("button:has-text('沉思')")
        except Exception:
            pass
        try:
            page.click("button:has-text('联网')")
        except Exception:
            pass
        # 输入搜索内容
        page.fill("#prompt-textarea", optimized_query)
        page.click("button:has-text('发送')")
        page.wait_for_selector(".chat-message", timeout=15000)
        # 爬取结果
        results = [el.inner_text() for el in page.query_selector_all(".chat-message")]
        browser.close()
        return results 