from playwright.sync_api import sync_playwright

def run(optimized_query, account=None, headless=False):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()
        # 1. 打开首页
        page.goto("https://chat.qwen.ai/")
        # 2. 登录（手机号+验证码，留空）
        # TODO: 输入手机号
        # page.fill("手机号输入框选择器", "")
        # TODO: 触发验证码发送
        # page.click("发送验证码按钮选择器")
        # TODO: 输入验证码
        # page.fill("验证码输入框选择器", "")
        # page.click("登录按钮选择器")
        # 3. 搜索操作
        page.fill("#prompt-textarea", optimized_query)
        page.click("button:has-text('发送')")
        page.wait_for_selector(".chat-message", timeout=15000)
        results = [el.inner_text() for el in page.query_selector_all(".chat-message")]
        browser.close()
        return results 