import concurrent.futures
from backend.account_manager import load_account
from playwright_scripts.deepseek import run as run_deepseek
from playwright_scripts.kimi import run as run_kimi
from playwright_scripts.chatglm import run as run_chatglm
from playwright_scripts.metaso import run as run_metaso
from playwright_scripts.doubao import run as run_doubao
from playwright_scripts.qwen import run as run_qwen
from playwright_scripts.minimax import run as run_minimax
from playwright_scripts.chatgpt import run as run_chatgpt
from playwright_scripts.gemini import run as run_gemini

PLATFORM_RUNNERS = {
    "DeepSeek": run_deepseek,
    "Kimi": run_kimi,
    "智谱清言": run_chatglm,
    "秘塔搜索": run_metaso,
    "豆包": run_doubao,
    "Qwen": run_qwen,
    "MiniMax": run_minimax,
    "ChatGPT": run_chatgpt,
    "Gemini": run_gemini,
}

def search_one(platform, optimized_query):
    runner = PLATFORM_RUNNERS[platform]
    account = load_account(platform)
    try:
        return platform, runner(optimized_query, account)
    except Exception as e:
        return platform, f"[运行失败] {e}"

def search_all(optimized_query, platforms):
    results = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_platform = {
            executor.submit(search_one, platform, optimized_query): platform
            for platform in platforms
        }
        for future in concurrent.futures.as_completed(future_to_platform):
            platform, result = future.result()
            results.append((platform, result))
    return results 