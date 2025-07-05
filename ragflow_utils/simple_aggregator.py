"""
简化版信息聚合器
专注于基础聚合和去重功能
"""

from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

def simple_deduplicate(results: List[str]) -> List[str]:
    """简单去重"""
    if not results:
        return []
    
    # 使用集合去重，保持顺序
    seen = set()
    unique_results = []
    
    for result in results:
        if result and result.strip():
            # 简单的内容指纹
            content_hash = hash(result.strip().lower()[:100])
            if content_hash not in seen:
                seen.add(content_hash)
                unique_results.append(result)
    
    logger.info(f"去重: {len(results)} -> {len(unique_results)}")
    return unique_results

def aggregate_platform_results(platform_results: List[tuple], 
                             merge_similar: bool = True) -> Dict[str, Any]:
    """聚合平台结果"""
    if not platform_results:
        return {"merged_content": "", "source_count": 0}
    
    # 过滤有效结果
    valid_results = []
    for platform, content in platform_results:
        if isinstance(content, str) and content.strip() and not content.startswith('['):
            valid_results.append((platform, content.strip()))
    
    if not valid_results:
        return {"merged_content": "未获取到有效结果", "source_count": 0}
    
    # 去重处理
    if merge_similar:
        contents = [content for _, content in valid_results]
        deduplicated = simple_deduplicate(contents)
        
        # 重建结果，保持平台信息
        result_map = {}
        for platform, content in valid_results:
            if content in deduplicated:
                result_map[content] = platform
        
        final_results = [(result_map[content], content) for content in deduplicated]
    else:
        final_results = valid_results
    
    # 生成聚合内容
    merged_content = "# 多平台搜索结果\n\n"
    
    for i, (platform, content) in enumerate(final_results, 1):
        merged_content += f"## 来源 {i}: {platform}\n\n"
        merged_content += f"{content}\n\n"
        merged_content += "---\n\n"
    
    return {
        "merged_content": merged_content,
        "source_count": len(final_results),
        "platforms": [platform for platform, _ in final_results],
        "raw_results": platform_results
    } 