import concurrent.futures
import logging
from typing import Dict, List, Any, Optional, Tuple
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

logger = logging.getLogger(__name__)

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

def search_one(platform: str, optimized_query: str, 
               browser_config: Optional[Dict] = None) -> Tuple[str, str]:
    """执行单个平台搜索"""
    runner = PLATFORM_RUNNERS[platform]
    account = load_account(platform)
    
    try:
        logger.info(f"开始搜索平台: {platform}")
        
        # 如果提供了浏览器配置，传递给runner
        if browser_config:
            result = runner(optimized_query, account, **browser_config)
        else:
            result = runner(optimized_query, account)
        
        logger.info(f"平台 {platform} 搜索完成")
        return platform, result
    except Exception as e:
        error_msg = f"[运行失败] {e}"
        logger.error(f"平台 {platform} 搜索失败: {error_msg}")
        return platform, error_msg

def search_all(optimized_query: str, platforms: List[str], 
               browser_config: Optional[Dict] = None) -> List[Tuple[str, str]]:
    """并行搜索所有平台"""
    results = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(platforms)) as executor:
        # 提交所有搜索任务
        future_to_platform = {
            executor.submit(search_one, platform, optimized_query, browser_config): platform
            for platform in platforms
        }
        
        # 收集结果
        for future in concurrent.futures.as_completed(future_to_platform):
            platform = future_to_platform[future]
            try:
                platform_name, result = future.result()
                results.append((platform_name, result))
                logger.info(f"平台 {platform} 结果收集完成")
            except Exception as e:
                logger.error(f"平台 {platform} 结果收集失败: {e}")
                results.append((platform, f"[执行异常] {e}"))
    
    return results

def search_and_integrate(optimized_query: str, platforms: List[str],
                        llm_config: Optional[Dict] = None,
                        browser_config: Optional[Dict] = None,
                        enable_fact_check: bool = True,
                        use_ai_integration: bool = True) -> Dict[str, Any]:
    """搜索并使用AI整合结果"""
    logger.info(f"开始搜索并整合，平台数: {len(platforms)}, AI整合: {use_ai_integration}")
    
    # 1. 执行搜索
    search_results = search_all(optimized_query, platforms, browser_config)
    
    # 2. 过滤有效结果
    valid_results = []
    for platform, result in search_results:
        if isinstance(result, str) and result.strip() and not result.startswith('['):
            valid_results.append((platform, result))
        else:
            logger.warning(f"平台 {platform} 返回无效结果: {result}")
    
    logger.info(f"有效搜索结果: {len(valid_results)}/{len(search_results)}")
    
    # 3. 整合结果
    if use_ai_integration and llm_config:
        try:
            from ragflow_utils.deduplicate import ai_enhanced_deduplicate
            
            # 使用AI增强去重和整合
            integration_result = ai_enhanced_deduplicate(
                valid_results, 
                llm_config=llm_config,
                enable_fact_check=enable_fact_check
            )
            
            logger.info("AI整合完成")
            return {
                "integration_result": integration_result,
                "raw_results": search_results,
                "query": optimized_query,
                "platforms": platforms,
                "processing_info": {
                    "ai_integration_enabled": True,
                    "fact_check_enabled": enable_fact_check,
                    "valid_results_count": len(valid_results),
                    "total_results_count": len(search_results)
                }
            }
            
        except Exception as e:
            logger.error(f"AI整合失败，降级到简单整合: {e}")
            use_ai_integration = False
    
    # 4. 简单整合（降级方案）
    if not use_ai_integration:
        from ragflow_utils.deduplicate import deduplicate_results, simple_fallback_integration
        
        # 简单去重
        simple_results = [result for _, result in valid_results]
        deduplicated = deduplicate_results(simple_results)
        
        # 简单整合
        fallback_result = simple_fallback_integration(valid_results)
        
        logger.info("简单整合完成")
        return {
            "integration_result": fallback_result,
            "raw_results": search_results,
            "query": optimized_query,
            "platforms": platforms,
            "processing_info": {
                "ai_integration_enabled": False,
                "fact_check_enabled": False,
                "valid_results_count": len(valid_results),
                "total_results_count": len(search_results)
            }
        }

# 保持原有接口兼容性
def search_all_legacy(optimized_query: str, platforms: List[str]) -> List[Tuple[str, str]]:
    """保持原有接口兼容性"""
    return search_all(optimized_query, platforms) 