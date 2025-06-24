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
            print('[ChatGLM] 打开首页...')
            page.goto("https://chatglm.cn/")
            page.screenshot(path="debug_chatglm_1_home.png")
            print('[ChatGLM] 等待输入框出现...')
            page.wait_for_selector('[contenteditable="true"]', timeout=30000)
            print('[ChatGLM] 填写输入框...')
            page.fill('[contenteditable="true"]', optimized_query)
            page.screenshot(path="debug_chatglm_2_filled.png")
            print('[ChatGLM] 聚焦输入框并回车发送...')
            page.focus('[contenteditable="true"]')
            page.keyboard.press('Enter')
            print('[ChatGLM] 等待AI回复...')
            page.wait_for_selector('.message-area-LmU13Q', timeout=30000)
            page.screenshot(path="debug_chatglm_3_result.png")
            all_msgs = page.query_selector_all('.message-area-LmU13Q .markdown-body')
            latest = all_msgs[-1].inner_text() if all_msgs else ''
            print('[ChatGLM] 最新AI回复:', latest)
        except Exception as e:
            print('[ChatGLM] 脚本异常:', e)
            page.screenshot(path="debug_chatglm_error.png")
            latest = ''
        browser.close()
        return latest 