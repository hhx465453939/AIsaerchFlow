# 注意：ChatGPT 需VPN+邮箱验证码登录
from playwright.sync_api import sync_playwright

def run(optimized_query, account=None, headless=False):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://chatgpt.com/")
        # TODO: 自动登录可用account参数
        page.fill("#prompt-textarea", optimized_query)
        page.click("button:has-text('发送')")
        page.wait_for_selector(".chat-message", timeout=15000)
        results = [el.inner_text() for el in page.query_selector_all(".chat-message")]
        browser.close()
        return results 