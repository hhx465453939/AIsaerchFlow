import sys
from langchain_agents.prompt_optimizer import get_optimized_prompt
from ragflow_utils.deduplicate import deduplicate_results

# 各平台脚本导入
from playwright_scripts.deepseek import run as run_deepseek
from playwright_scripts.kimi import run as run_kimi
from playwright_scripts.chatglm import run as run_chatglm
from playwright_scripts.metaso import run as run_metaso
from playwright_scripts.doubao import run as run_doubao
from playwright_scripts.qwen import run as run_qwen
from playwright_scripts.minimax import run as run_minimax
from playwright_scripts.chatgpt import run as run_chatgpt
from playwright_scripts.gemini import run as run_gemini

PLATFORMS = [
    ("DeepSeek", run_deepseek),
    ("Kimi", run_kimi),
    ("智谱清言", run_chatglm),
    ("埃塔AI搜索", run_metaso),
    ("豆包", run_doubao),
    ("Qwen", run_qwen),
    ("MiniMax", run_minimax),
    ("ChatGPT", run_chatgpt),
    ("Gemini", run_gemini),
]

def main():
    if len(sys.argv) < 2:
        print("用法: python run_all_platforms.py <你的原始问题>")
        sys.exit(1)
    user_input = sys.argv[1]
    optimized_query = get_optimized_prompt(user_input)
    print(f"优化后搜索内容: {optimized_query}")
    all_results = []
    for name, runner in PLATFORMS:
        print(f"\n==== {name} ====")
        try:
            result = runner(optimized_query)
            if isinstance(result, list):
                all_results.extend(result)
                print("\n".join(result))
            elif isinstance(result, str):
                all_results.append(result)
                print(result)
            else:
                print("[无结果或未实现返回]")
        except Exception as e:
            print(f"[运行失败] {e}")
    # 聚合去重
    merged = deduplicate_results(all_results)
    print("\n==== 聚合去重后结果 ====")
    for item in merged:
        print(item)
    with open("results_merged.txt", "w", encoding="utf-8") as f:
        for item in merged:
            f.write(str(item) + "\n")
    print("\n已保存到 results_merged.txt")

if __name__ == "__main__":
    main() 