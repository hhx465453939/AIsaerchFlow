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
            print('[DeepSeek] 打开首页...')
            page.goto("https://chat.deepseek.com/")
            page.screenshot(path="debug_deepseek_1_home.png")
            try:
                print('[DeepSeek] 尝试开启网络搜索...')
                page.click("#web-search-toggle")
            except Exception as e:
                print('[DeepSeek] 网络搜索按钮未找到:', e)
            print('[DeepSeek] 填写输入框...')
            page.fill("textarea", optimized_query)
            page.screenshot(path="debug_deepseek_2_filled.png")
            print('[DeepSeek] 点击发送按钮...')
            page.click(".ds-icon-button")
            print('[DeepSeek] 等待AI回复...')
            page.wait_for_selector(".c08e6e93", timeout=20000)
            page.screenshot(path="debug_deepseek_3_result.png")
            all_msgs = page.query_selector_all(".c08e6e93")
            latest = all_msgs[-1].inner_text() if all_msgs else ''
            print('[DeepSeek] 最新AI回复:', latest)
        except Exception as e:
            print('[DeepSeek] 脚本异常:', e)
            page.screenshot(path="debug_deepseek_error.png")
            latest = ''
        browser.close()
        return latest 