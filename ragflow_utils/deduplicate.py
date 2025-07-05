from typing import List, Optional, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)

# 保持原有的简单去重函数
def deduplicate_results(results: List[str]) -> List[str]:
    """简单去重 - 保持原有接口兼容性"""
    if not results:
        return []
    
    # 使用set进行简单去重
    unique_results = list(set(results))
    logger.info(f"简单去重: {len(results)} -> {len(unique_results)}")
    return unique_results

# 新增：AI增强去重函数
def ai_enhanced_deduplicate(platform_results: List[Tuple[str, str]], 
                          llm_config: Optional[Dict] = None,
                          enable_fact_check: bool = True) -> Dict[str, Any]:
    """AI增强去重 - 使用AI整合器"""
    try:
        # 导入AI整合器
        from ragflow_utils.ai_integrator import AIIntegrator, LLMConfig
        
        if not llm_config:
            logger.warning("未提供LLM配置，降级到简单去重")
            return {
                "integrated_document": {
                    "integrated_content": "\n".join([result[1] for result in platform_results]),
                    "source_count": len(platform_results),
                    "metadata": {"integration_method": "simple"}
                },
                "processing_summary": {
                    "original_count": len(platform_results),
                    "after_deduplication": len(platform_results),
                    "fact_check_enabled": False
                }
            }
        
        # 创建LLM配置
        llm_cfg = LLMConfig(
            base_url=llm_config.get("base_url", ""),
            api_key=llm_config.get("api_key", ""),
            model=llm_config.get("model", "gpt-3.5-turbo"),
            temperature=llm_config.get("temperature", 0.3),
            max_tokens=llm_config.get("max_tokens", 4000)
        )
        
        # 创建AI整合器
        integrator = AIIntegrator(llm_cfg)
        
        # 处理平台结果
        result = integrator.process_platform_results(platform_results, enable_fact_check)
        
        logger.info(f"AI增强去重完成: {len(platform_results)} -> {len(result['processed_contents'])}")
        return result
        
    except ImportError as e:
        logger.error(f"AI整合器导入失败: {e}")
        return simple_fallback_integration(platform_results)
    except Exception as e:
        logger.error(f"AI增强去重失败: {e}")
        return simple_fallback_integration(platform_results)

def simple_fallback_integration(platform_results: List[Tuple[str, str]]) -> Dict[str, Any]:
    """简单降级整合方案"""
    integrated_content = "# 多平台AI搜索结果\n\n"
    
    for i, (platform, content) in enumerate(platform_results):
        integrated_content += f"## 来源 {i+1}: {platform}\n"
        integrated_content += f"{content}\n\n---\n\n"
    
    return {
        "integrated_document": {
            "integrated_content": integrated_content,
            "source_count": len(platform_results),
            "metadata": {"integration_method": "simple_fallback"}
        },
        "processed_contents": [
            {
                "content": content,
                "platform": platform,
                "confidence_score": 0.5,
                "fact_checked": False
            }
            for platform, content in platform_results
        ],
        "processing_summary": {
            "original_count": len(platform_results),
            "after_deduplication": len(platform_results),
            "fact_check_enabled": False
        }
    } 