"""
流式多平台搜索聚合器
专注于实时监控和动态内容聚合
"""

import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import threading
import queue
import os
import sys

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class StreamContent:
    """流式内容数据结构"""
    platform: str
    content: str
    timestamp: str
    is_complete: bool = False
    confidence: float = 1.0

class PlatformStreamMonitor:
    """单个平台的流式监控器"""
    
    def __init__(self, platform_name: str, page_selector: str):
        self.platform_name = platform_name
        self.page_selector = page_selector
        self.content_queue = queue.Queue()
        self.is_monitoring = False
        self.last_content = ""
        
    def monitor_stream(self, page, timeout: int = 60) -> StreamContent:
        """监控页面的流式输出"""
        self.is_monitoring = True
        start_time = time.time()
        last_update = time.time()
        accumulated_content = ""
        
        logger.info(f"开始监控 {self.platform_name} 的流式输出")
        
        while self.is_monitoring and (time.time() - start_time) < timeout:
            try:
                # 获取当前页面内容
                current_content = page.inner_text(self.page_selector)
                
                # 检查是否有新内容
                if current_content != self.last_content and current_content:
                    accumulated_content = current_content
                    self.last_content = current_content
                    last_update = time.time()
                    
                    logger.debug(f"{self.platform_name} 内容更新: {len(current_content)} 字符")
                
                # 检查是否输出完成（5秒无新内容）
                if time.time() - last_update > 5 and accumulated_content:
                    logger.info(f"{self.platform_name} 输出完成")
                    self.is_monitoring = False
                    return StreamContent(
                        platform=self.platform_name,
                        content=accumulated_content,
                        timestamp=datetime.now().isoformat(),
                        is_complete=True
                    )
                
                time.sleep(0.5)  # 避免过度查询
                
            except Exception as e:
                logger.error(f"{self.platform_name} 监控异常: {e}")
                time.sleep(1)
        
        # 超时或异常，返回已收集的内容
        return StreamContent(
            platform=self.platform_name,
            content=accumulated_content,
            timestamp=datetime.now().isoformat(),
            is_complete=False,
            confidence=0.8 if accumulated_content else 0.0
        )
    
    def stop_monitoring(self):
        """停止监控"""
        self.is_monitoring = False

class MultiPlatformStreamAggregator:
    """多平台流式聚合器"""
    
    def __init__(self):
        self.platform_monitors = {}
        self.aggregated_content = []
        self.is_aggregating = False
        
        # 平台配置 - 简化版，专注于流式监控
        self.platform_configs = {
            "DeepSeek": ".c08e6e93",  # 消息内容选择器
            "Kimi": ".message-list .message-item:last-child",
            "智谱清言": ".message-area-LmU13Q .markdown-body:last-child",
            # 其他平台可以继续添加
        }
    
    def start_aggregation(self, platforms: List[str], query: str, 
                         ai_processor_config: Optional[Dict] = None) -> Dict[str, Any]:
        """开始多平台流式聚合"""
        logger.info(f"开始多平台流式聚合: {platforms}")
        
        self.is_aggregating = True
        self.aggregated_content = []
        
        # 收集流式内容（模拟版本，实际需要集成playwright脚本）
        stream_results = []
        for platform in platforms:
            if platform in self.platform_configs:
                try:
                    logger.info(f"启动 {platform} 搜索...")
                    # 这里是模拟数据，实际需要调用相应的playwright脚本
                    content = self._run_platform_with_stream(platform, query)
                    if content:
                        stream_results.append(content)
                except Exception as e:
                    logger.error(f"{platform} 执行失败: {e}")
        
        # 第二阶段：实时聚合
        aggregated_result = self._aggregate_streams(stream_results)
        
        # 第三阶段：AI处理（如果配置了）
        if ai_processor_config:
            final_result = self._process_with_ai(aggregated_result, ai_processor_config)
        else:
            final_result = self._simple_merge(aggregated_result)
        
        self.is_aggregating = False
        
        return {
            "query": query,
            "platforms": platforms,
            "stream_results": [
                {
                    "platform": content.platform,
                    "content": content.content,
                    "timestamp": content.timestamp,
                    "is_complete": content.is_complete,
                    "confidence": content.confidence
                }
                for content in stream_results
            ],
            "aggregated_result": final_result,
            "processing_time": datetime.now().isoformat()
        }
    
    def _run_platform_with_stream(self, platform: str, query: str) -> Optional[StreamContent]:
        """运行单个平台并进行流式监控（模拟版本）"""
        # 模拟搜索内容
        mock_content = f"""
## {platform} 搜索结果

关于 "{query}" 的回答：

{platform} 是一个强大的AI助手平台，能够提供高质量的回答。

### 主要特点：
1. 智能对话能力
2. 多领域知识覆盖
3. 实时交互体验
4. 准确的信息提供

### 使用建议：
- 提供清晰的问题描述
- 指定具体的需求
- 善用上下文信息

这是一个模拟的搜索结果，用于测试项目的基础功能。
        """.strip()
        
        return StreamContent(
            platform=platform,
            content=mock_content,
            timestamp=datetime.now().isoformat(),
            is_complete=True,
            confidence=0.9
        )
    
    def _aggregate_streams(self, stream_results: List[StreamContent]) -> Dict[str, Any]:
        """聚合流式结果"""
        logger.info("开始聚合流式结果")
        
        # 简单聚合策略
        high_confidence_results = [
            result for result in stream_results 
            if result.confidence > 0.7 and result.is_complete
        ]
        
        return {
            "total_sources": len(stream_results),
            "high_confidence_sources": len(high_confidence_results),
            "contents": [
                {
                    "platform": result.platform,
                    "content": result.content,
                    "confidence": result.confidence
                }
                for result in high_confidence_results
            ]
        }
    
    def _process_with_ai(self, aggregated_data: Dict[str, Any], 
                        config: Dict[str, Any]) -> Dict[str, Any]:
        """使用AI处理聚合结果"""
        logger.info("开始AI处理聚合结果")
        
        # 构建提示词
        contents = aggregated_data["contents"]
        content_text = "\n".join([
            f"**{item['platform']}** (可信度: {item['confidence']:.1f}):\n{item['content']}\n"
            for item in contents
        ])
        
        # 加载提示词模板
        prompt_template = self._load_prompt_template(config.get("prompt_type", "default"))
        
        final_prompt = prompt_template.format(
            query=config.get("original_query", ""),
            content=content_text,
            requirements=config.get("requirements", "请整理并总结以上信息")
        )
        
        # 调用AI服务（模拟）
        ai_result = self._call_ai_service(final_prompt, config)
        
        return {
            "ai_processed": True,
            "original_aggregation": aggregated_data,
            "ai_result": ai_result,
            "prompt_used": prompt_template,
            "processing_config": config
        }
    
    def _simple_merge(self, aggregated_data: Dict[str, Any]) -> Dict[str, Any]:
        """简单合并（无AI处理）"""
        contents = aggregated_data["contents"]
        
        merged_content = "# 多平台搜索结果汇总\n\n"
        for i, item in enumerate(contents, 1):
            merged_content += f"## 来源 {i}: {item['platform']}\n"
            merged_content += f"**可信度**: {item['confidence']:.1f}\n\n"
            merged_content += f"{item['content']}\n\n---\n\n"
        
        return {
            "ai_processed": False,
            "merged_content": merged_content,
            "source_count": len(contents)
        }
    
    def _load_prompt_template(self, prompt_type: str) -> str:
        """加载提示词模板"""
        templates = {
            "default": """
请基于以下多平台搜索结果，进行信息整理和事实核查：

**原始查询**: {query}

**搜索结果**:
{content}

**处理要求**: {requirements}

请提供：
1. 核心信息总结
2. 关键要点提取
3. 信息可信度评估
4. 潜在风险提示
5. 建议行动方案
""",
            "fact_check": """
请对以下信息进行专业的事实核查和分析：

**查询内容**: {query}

**待核查信息**:
{content}

请提供：
1. 事实准确性验证
2. 信息来源可信度分析
3. 潜在偏见或误导识别
4. 建议进一步验证的方向
5. 综合可信度评分（1-10分）
""",
            "summary": """
请将以下多源信息整理成清晰的总结报告：

**主题**: {query}

**信息来源**:
{content}

**要求**: {requirements}

请按以下结构输出：
- 📋 执行摘要
- 🔍 详细分析  
- 💡 关键洞察
- ⚠️ 注意事项
- 🎯 行动建议
"""
        }
        return templates.get(prompt_type, templates["default"])
    
    def _call_ai_service(self, prompt: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """调用AI服务（模拟版本）"""
        # 模拟AI处理结果
        return {
            "content": f"""# AI整理结果

基于多平台搜索结果的综合分析：

## 📋 核心要点总结
通过对比多个AI平台的回答，发现了以下关键信息：
- 各平台在回答质量上表现一致
- 主要观点具有较高的一致性
- 信息来源可信度良好

## 🔍 详细分析
{prompt[:200]}...

## 💡 关键洞察
- AI平台聚合搜索能够提供更全面的信息
- 多源验证提高了信息可信度
- 流式监控确保了内容的完整性

## ⚠️ 注意事项
- 建议对关键信息进行进一步验证
- 注意不同平台可能存在的偏见
- 考虑信息的时效性

## 🎯 行动建议
1. 根据聚合结果制定行动计划
2. 持续监控相关信息变化
3. 必要时进行深度调研

*本结果由AI自动生成，仅供参考*
""",
            "model": config.get("model", "simulation"),
            "tokens_used": len(prompt) // 4,  # 模拟token使用量
            "processing_time": 2.5
        }
    
    def stop_aggregation(self):
        """停止聚合"""
        self.is_aggregating = False
        for monitor in self.platform_monitors.values():
            monitor.stop_monitoring()

# 导出主要接口
__all__ = ["MultiPlatformStreamAggregator", "StreamContent", "PlatformStreamMonitor"]

# 测试代码
if __name__ == "__main__":
    # 简单测试
    aggregator = MultiPlatformStreamAggregator()
    result = aggregator.start_aggregation(
        platforms=["DeepSeek", "Kimi"],
        query="什么是人工智能？"
    )
    
    print("=== 测试结果 ===")
    print(f"查询: {result['query']}")
    print(f"平台: {result['platforms']}")
    print(f"结果数: {len(result['stream_results'])}")
    print("\n聚合内容:")
    print(result['aggregated_result']['merged_content']) 