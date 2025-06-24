from playwright.sync_api import sync_playwright
import os

def run(optimized_query, account=None, headless=False):
    with sync_playwright() as p:
        user_data_dir = os.path.expandvars(r"%LOCALAPPDATA%\\Microsoft\\Edge\\User Data")
        browser = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            channel="msedge"
        )
        page = browser.new_page()
        try:
            print('[Kimi] 打开首页...')
            page.goto("https://kimi.moonshot.cn/")
            page.screenshot(path="debug_kimi_1_home.png")
            print('[Kimi] 填写输入框...')
            page.fill('div[contenteditable="true"]', optimized_query)
            page.screenshot(path="debug_kimi_2_filled.png")
            print('[Kimi] 聚焦输入框并回车发送...')
            page.focus('div[contenteditable="true"]')
            page.keyboard.press('Enter')
            print('[Kimi] 等待AI回复...')
            page.wait_for_selector('.message-list .message-item', timeout=20000)
            page.screenshot(path="debug_kimi_3_result.png")
            all_msgs = page.query_selector_all('.message-list .message-item')
            latest = all_msgs[-1].inner_text() if all_msgs else ''
            print('[Kimi] 最新AI回复:', latest)
        except Exception as e:
            print('[Kimi] 脚本异常:', e)
            page.screenshot(path="debug_kimi_error.png")
            latest = ''
        browser.close()
        return latest 