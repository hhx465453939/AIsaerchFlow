"""
简化版API服务
专注于核心的多平台搜索聚合功能
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
import asyncio
import json
import os
from datetime import datetime

# 导入核心模块
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from core.stream_aggregator import MultiPlatformStreamAggregator
from ragflow_utils.simple_aggregator import aggregate_platform_results

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI多平台搜索聚合器",
    description="流式监控多平台AI搜索并聚合结果",
    version="2.0.0"
)

# CORS设置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据模型
class SearchRequest(BaseModel):
    query: str
    platforms: List[str] = ["DeepSeek", "Kimi", "智谱清言"]
    enable_ai_processing: bool = False
    ai_config: Optional[Dict[str, Any]] = None

class SearchResponse(BaseModel):
    query: str
    platforms: List[str]
    results: List[Dict[str, Any]]
    aggregated_content: str
    processing_time: str
    source_count: int
    success: bool

class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str

# 全局变量
aggregator = MultiPlatformStreamAggregator()

@app.get("/", response_model=HealthResponse)
async def health_check():
    """健康检查"""
    return HealthResponse(
        status="running",
        version="2.0.0",
        timestamp=datetime.now().isoformat()
    )

@app.post("/search", response_model=SearchResponse)
async def search_platforms(request: SearchRequest):
    """多平台搜索聚合"""
    try:
        logger.info(f"开始搜索: {request.query}")
        logger.info(f"目标平台: {request.platforms}")
        
        # 启动流式聚合
        ai_config = request.ai_config if request.enable_ai_processing else None
        
        result = aggregator.start_aggregation(
            platforms=request.platforms,
            query=request.query,
            ai_processor_config=ai_config
        )
        
        # 格式化响应
        aggregated_content = result["aggregated_result"].get("merged_content", "")
        if result["aggregated_result"].get("ai_processed"):
            ai_result = result["aggregated_result"]["ai_result"]
            aggregated_content = ai_result.get("content", aggregated_content)
        
        return SearchResponse(
            query=request.query,
            platforms=request.platforms,
            results=result["stream_results"],
            aggregated_content=aggregated_content,
            processing_time=result["processing_time"],
            source_count=len(result["stream_results"]),
            success=True
        )
        
    except Exception as e:
        logger.error(f"搜索失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

@app.post("/quick-search")
async def quick_search(query: str, platforms: Optional[str] = None):
    """快速搜索接口"""
    try:
        platform_list = platforms.split(",") if platforms else ["DeepSeek"]
        
        request = SearchRequest(
            query=query,
            platforms=platform_list,
            enable_ai_processing=False
        )
        
        return await search_platforms(request)
        
    except Exception as e:
        logger.error(f"快速搜索失败: {e}")
        raise HTTPException(status_code=500, detail=f"快速搜索失败: {str(e)}")

@app.get("/config")
async def get_config():
    """获取配置信息"""
    try:
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config
        else:
            return {"error": "配置文件不存在"}
    except Exception as e:
        logger.error(f"获取配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")

@app.post("/config")
async def update_config(config: Dict[str, Any]):
    """更新配置信息"""
    try:
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        logger.info("配置已更新")
        return {"success": True, "message": "配置已更新"}
        
    except Exception as e:
        logger.error(f"更新配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新配置失败: {str(e)}")

@app.get("/platforms")
async def get_platforms():
    """获取支持的平台列表"""
    platforms = {
        "DeepSeek": {
            "name": "DeepSeek",
            "status": "ready",
            "selector": ".c08e6e93",
            "url": "https://chat.deepseek.com"
        },
        "Kimi": {
            "name": "Kimi",
            "status": "ready", 
            "selector": ".message-list .message-item:last-child",
            "url": "https://kimi.moonshot.cn"
        },
        "智谱清言": {
            "name": "智谱清言",
            "status": "ready",
            "selector": ".message-area-LmU13Q .markdown-body:last-child", 
            "url": "https://chatglm.cn"
        }
    }
    return platforms

@app.post("/stop")
async def stop_search():
    """停止当前搜索"""
    try:
        aggregator.stop_aggregation()
        return {"success": True, "message": "搜索已停止"}
    except Exception as e:
        logger.error(f"停止搜索失败: {e}")
        raise HTTPException(status_code=500, detail=f"停止搜索失败: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 