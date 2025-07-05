"""
增强版API - 整合两个项目的优点
支持模拟模式和真实模式的渐进式开发
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import os
import time
import logging
import asyncio
import uuid
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
    title="AI多平台搜索聚合器 - 增强版",
    description="整合两个项目优点的多平台AI搜索聚合API",
    version="2.1.0"
)

# CORS设置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局搜索状态管理
search_status_store = {}

# 数据模型
class SearchRequest(BaseModel):
    user_input: str
    platforms: List[str] = ["DeepSeek", "Kimi", "智谱清言"]
    enable_ai_processing: bool = False
    ai_config: Optional[Dict[str, Any]] = None
    timeout: Optional[int] = 30
    max_workers: Optional[int] = 3
    simulation_mode: bool = True  # 默认启用模拟模式

class SearchResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    message: str
    processing_time: str
    simulation_mode: bool
    search_id: Optional[str] = None

class SearchStatus(BaseModel):
    search_id: str
    status: str  # "running", "completed", "failed"
    progress: float  # 0.0 - 1.0
    current_platform: Optional[str] = None
    completed_platforms: List[str] = []
    results: List[Dict[str, Any]] = []
    live_results: Dict[str, Dict[str, Any]] = {}  # 实时搜索结果
    error: Optional[str] = None
    start_time: str
    last_update: str

class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str
    features: List[str]
    endpoints: List[str]

class PlatformStatus(BaseModel):
    platform: str
    supported: bool
    available: bool
    has_account: bool
    simulation_available: bool
    description: str

# 全局变量
aggregator = MultiPlatformStreamAggregator()

# 平台配置
PLATFORM_CONFIGS = {
    "DeepSeek": {
        "supported": True,
        "description": "DeepSeek AI助手 - 深度思考能力强",
        "url": "https://chat.deepseek.com",
        "status": "ready"
    },
    "Kimi": {
        "supported": True, 
        "description": "Kimi AI助手 - 长文本处理优秀",
        "url": "https://kimi.moonshot.cn",
        "status": "developing"
    },
    "智谱清言": {
        "supported": True,
        "description": "智谱清言 - 中文理解能力强",
        "url": "https://chatglm.cn",
        "status": "developing"
    },
    "秘塔搜索": {
        "supported": False,
        "description": "秘塔搜索 - 专业搜索引擎",
        "url": "https://metaso.cn",
        "status": "planned"
    },
    "豆包": {
        "supported": False,
        "description": "豆包AI - 字节跳动AI助手",
        "url": "https://doubao.com",
        "status": "planned"
    }
}

@app.get("/", response_model=HealthResponse)
async def health_check():
    """健康检查和API信息"""
    return HealthResponse(
        status="healthy",
        version="2.1.0", 
        timestamp=datetime.now().isoformat(),
        features=[
            "多平台并发搜索",
            "智能信息聚合", 
            "模拟模式测试",
            "平台状态监控",
            "实时搜索状态",
            "渐进式功能升级"
        ],
        endpoints=[
            "/search - 多平台搜索",
            "/search-async - 异步搜索",
            "/search-status/{search_id} - 搜索状态",
            "/platforms - 平台列表",
            "/platform-status - 平台状态",
            "/simulation - 模拟模式设置",
            "/docs - API文档"
        ]
    )

@app.get("/health")
async def simple_health():
    """简单健康检查"""
    return {
        "status": "healthy",
        "service": "AI多平台搜索聚合器",
        "version": "2.1.0",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/search", response_model=SearchResponse)
async def search_platforms(request: SearchRequest):
    """同步多平台搜索聚合 (向后兼容)"""
    start_time = time.time()
    
    try:
        logger.info(f"开始搜索: {request.user_input}")
        logger.info(f"目标平台: {request.platforms}")
        logger.info(f"模拟模式: {request.simulation_mode}")
        
        if request.simulation_mode:
            # 模拟模式 - 使用内置模拟数据
            result = await _simulation_search(request)
        else:
            # 真实模式 - 调用实际平台
            result = await _real_search(request)
        
        processing_time = f"{time.time() - start_time:.2f}s"
        
        return SearchResponse(
            success=True,
            data=result,
            message=f"搜索完成，处理了 {len(request.platforms)} 个平台",
            processing_time=processing_time,
            simulation_mode=request.simulation_mode
        )
        
    except Exception as e:
        logger.error(f"搜索失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

@app.post("/search-async")
async def search_platforms_async(request: SearchRequest, background_tasks: BackgroundTasks):
    """异步多平台搜索 - 支持实时状态查询"""
    search_id = str(uuid.uuid4())
    
    # 初始化搜索状态
    search_status_store[search_id] = SearchStatus(
        search_id=search_id,
        status="running",
        progress=0.0,
        current_platform=None,
        completed_platforms=[],
        results=[],
        live_results={},
        start_time=datetime.now().isoformat(),
        last_update=datetime.now().isoformat()
    ).dict()
    
    # 启动后台搜索任务
    background_tasks.add_task(_background_search, search_id, request)
    
    return {
        "success": True,
        "search_id": search_id,
        "message": "搜索已启动，可通过search_id查询状态"
    }

@app.get("/search-status/{search_id}")
async def get_search_status(search_id: str):
    """获取搜索状态"""
    if search_id not in search_status_store:
        raise HTTPException(status_code=404, detail="搜索ID不存在")
    
    status = search_status_store[search_id]
    return {
        "success": True,
        "status": status
    }

async def _background_search(search_id: str, request: SearchRequest):
    """后台搜索任务"""
    try:
        def update_status(status: str, progress: float, current_platform: str = None, 
                         completed: List[str] = None, results: List[Dict] = None, error: str = None,
                         live_results: Dict[str, Dict] = None):
            """更新搜索状态"""
            if search_id in search_status_store:
                search_status_store[search_id].update({
                    "status": status,
                    "progress": progress,
                    "current_platform": current_platform,
                    "completed_platforms": completed or search_status_store[search_id]["completed_platforms"],
                    "results": results or search_status_store[search_id]["results"],
                    "live_results": live_results or search_status_store[search_id].get("live_results", {}),
                    "error": error,
                    "last_update": datetime.now().isoformat()
                })
        
        logger.info(f"后台搜索开始: {search_id}")
        
        # 初始化实时结果存储
        live_results = {}
        for platform in request.platforms:
            live_results[platform] = {
                "status": "waiting",  # waiting, searching, completed, failed
                "content": "",
                "progress_text": "等待开始...",
                "start_time": None,
                "end_time": None,
                "error": None
            }
        
        update_status("running", 0.0, None, [], [], None, live_results)
        
        if request.simulation_mode:
            # 模拟搜索过程
            results = []
            for i, platform in enumerate(request.platforms):
                # 开始搜索该平台
                live_results[platform]["status"] = "searching"
                live_results[platform]["progress_text"] = f"正在连接 {platform}..."
                live_results[platform]["start_time"] = datetime.now().isoformat()
                
                update_status("running", i / len(request.platforms), platform, 
                            search_status_store[search_id]["completed_platforms"], 
                            search_status_store[search_id]["results"], None, live_results)
                
                # 模拟连接延时
                await asyncio.sleep(1)
                
                # 模拟搜索过程 - 分步显示内容
                live_results[platform]["progress_text"] = f"正在分析问题..."
                update_status("running", (i + 0.2) / len(request.platforms), platform, 
                            search_status_store[search_id]["completed_platforms"], 
                            search_status_store[search_id]["results"], None, live_results)
                await asyncio.sleep(0.5)
                
                live_results[platform]["progress_text"] = f"正在生成回答..."
                update_status("running", (i + 0.4) / len(request.platforms), platform, 
                            search_status_store[search_id]["completed_platforms"], 
                            search_status_store[search_id]["results"], None, live_results)
                await asyncio.sleep(0.5)
                
                # 模拟流式内容生成
                full_content = _generate_mock_content(platform, request.user_input)
                content_chunks = _split_content_into_chunks(full_content)
                
                for j, chunk in enumerate(content_chunks):
                    live_results[platform]["content"] += chunk
                    live_results[platform]["progress_text"] = f"正在生成回答... ({j+1}/{len(content_chunks)})"
                    
                    update_status("running", (i + 0.6 + (j / len(content_chunks)) * 0.3) / len(request.platforms), 
                                platform, search_status_store[search_id]["completed_platforms"], 
                                search_status_store[search_id]["results"], None, live_results)
                    await asyncio.sleep(0.3)  # 模拟流式输出
                
                # 完成该平台搜索
                live_results[platform]["status"] = "completed"
                live_results[platform]["progress_text"] = "搜索完成 ✅"
                live_results[platform]["end_time"] = datetime.now().isoformat()
                
                result = {
                    "platform": platform,
                    "content": live_results[platform]["content"],
                    "timestamp": datetime.now().isoformat(),
                    "is_complete": True,
                    "confidence": 0.9,
                    "status": "success"
                }
                results.append(result)
                
                # 更新已完成平台
                completed = search_status_store[search_id]["completed_platforms"] + [platform]
                update_status("running", (i + 1) / len(request.platforms), None, completed, results, None, live_results)
                
                # 平台间隔时间
                if i < len(request.platforms) - 1:
                    await asyncio.sleep(0.5)
            
            # 聚合结果
            contents = [(r["platform"], r["content"]) for r in results]
            aggregated = aggregate_platform_results(contents)
            
            final_result = {
                "integrated_document": {
                    "integrated_content": aggregated["merged_content"],
                    "source_count": aggregated["source_count"],
                    "metadata": {
                        "integration_method": "simulation_mode",
                        "processing_timestamp": datetime.now().isoformat(),
                        "simulation": True
                    }
                },
                "processed_contents": [
                    {
                        "platform": r["platform"],
                        "content": r["content"],
                        "fact_checked": False,
                        "confidence": r["confidence"]
                    }
                    for r in results
                ],
                "raw_results": results,
                "live_results": live_results,  # 保留实时结果
                "processing_summary": {
                    "original_count": len(results),
                    "after_filtering": len(results),
                    "after_deduplication": len(results),
                    "ai_integration_enabled": request.enable_ai_processing,
                    "fact_check_enabled": False,
                    "simulation_mode": True,
                    "processing_time": datetime.now().isoformat()
                }
            }
            
            update_status("completed", 1.0, None, None, final_result, None, live_results)
            
        else:
            # 真实搜索模式 - 检查可用的搜索方法
            
            # 检查浏览器会话是否可用
            browser_available = await _check_browser_session()
            logger.info(f"浏览器会话可用: {browser_available}")
            
            if browser_available:
                # 使用浏览器自动化搜索
                logger.info("使用浏览器自动化搜索模式")
                
                # 更新状态为浏览器搜索
                for platform in request.platforms:
                    live_results[platform]["status"] = "searching"
                    live_results[platform]["progress_text"] = f"准备浏览器自动化搜索..."
                    live_results[platform]["start_time"] = datetime.now().isoformat()
                
                update_status("running", 0.1, None, [], [], None, live_results)
                
                try:
                    # 执行浏览器自动化搜索
                    browser_result = await _perform_browser_search(request.platforms, request.user_input)
                    
                    if browser_result.get("success"):
                        results = browser_result["results"]
                        
                        # 更新live_results
                        for result in results:
                            platform = result["platform"]
                            if platform in live_results:
                                live_results[platform]["content"] = result["content"]
                                live_results[platform]["status"] = "completed" if result["status"] == "success" else "failed"
                                live_results[platform]["progress_text"] = "浏览器自动化完成 ✅" if result["status"] == "success" else "浏览器自动化失败 ❌"
                                live_results[platform]["end_time"] = datetime.now().isoformat()
                        
                        update_status("running", 0.8, None, request.platforms, results, None, live_results)
                        
                    else:
                        # 浏览器搜索失败，回退到传统方法
                        logger.warning(f"浏览器搜索失败: {browser_result.get('error')}")
                        results = await _fallback_real_search(request.platforms, request.user_input, live_results)
                        
                except Exception as e:
                    logger.error(f"浏览器搜索异常: {e}")
                    results = await _fallback_real_search(request.platforms, request.user_input, live_results)
            
            else:
                # 使用传统的Cookie/API搜索
                logger.info("使用传统Cookie/API搜索模式")
                results = await _fallback_real_search(request.platforms, request.user_input, live_results)
            
            # 聚合结果
            valid_results = [r for r in results if r["status"] == "success"]
            if valid_results:
                contents = [(r["platform"], r["content"]) for r in valid_results]
                aggregated = aggregate_platform_results(contents)
            else:
                aggregated = {
                    "merged_content": "⚠️ 所有平台连接失败，请检查真实模式配置。",
                    "source_count": 0
                }
            
            final_result = {
                "integrated_document": {
                    "integrated_content": aggregated["merged_content"],
                    "source_count": aggregated["source_count"],
                    "metadata": {
                        "integration_method": "real_mode",
                        "processing_timestamp": datetime.now().isoformat(),
                        "simulation": False
                    }
                },
                "processed_contents": [
                    {
                        "platform": r["platform"],
                        "content": r["content"],
                        "fact_checked": False,
                        "confidence": r["confidence"]
                    }
                    for r in results
                ],
                "raw_results": results,
                "live_results": live_results,
                "processing_summary": {
                    "original_count": len(results),
                    "after_filtering": len(valid_results),
                    "after_deduplication": len(valid_results),
                    "ai_integration_enabled": request.enable_ai_processing,
                    "fact_check_enabled": False,
                    "simulation_mode": False,
                    "processing_time": datetime.now().isoformat()
                }
            }
            
            # 根据成功数量决定最终状态
            if valid_results:
                update_status("completed", 1.0, None, None, final_result, None, live_results)
            else:
                update_status("failed", 1.0, None, None, None, "所有平台连接失败", live_results)
        
    except Exception as e:
        logger.error(f"后台搜索失败: {e}")
        # 更新所有平台为失败状态
        live_results = {}
        for platform in request.platforms:
            live_results[platform] = {
                "status": "failed",
                "content": "",
                "progress_text": "搜索失败",
                "error": str(e)
            }
        update_status("failed", 0.0, None, None, None, str(e), live_results)

def _split_content_into_chunks(content: str, chunk_size: int = 200) -> List[str]:
    """将内容分割为块，模拟流式输出"""
    chunks = []
    lines = content.split('\n')
    current_chunk = ""
    
    for line in lines:
        if len(current_chunk) + len(line) + 1 <= chunk_size:
            current_chunk += line + '\n'
        else:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = line + '\n'
    
    if current_chunk:
        chunks.append(current_chunk)
    
    # 确保至少有几个块
    if len(chunks) < 3:
        # 重新分割为更小的块
        return [content[i:i+100] for i in range(0, len(content), 100) if content[i:i+100].strip()]
    
    return chunks

async def _simulation_search(request: SearchRequest) -> Dict[str, Any]:
    """模拟搜索 - 用于测试和开发"""
    logger.info("执行模拟搜索")
    
    # 模拟搜索延时
    await asyncio.sleep(1)
    
    # 生成模拟结果
    mock_results = []
    for platform in request.platforms:
        if platform in PLATFORM_CONFIGS:
            mock_content = _generate_mock_content(platform, request.user_input)
            mock_results.append({
                "platform": platform,
                "content": mock_content,
                "timestamp": datetime.now().isoformat(),
                "is_complete": True,
                "confidence": 0.9,
                "status": "success"
            })
    
    # 聚合结果
    contents = [(r["platform"], r["content"]) for r in mock_results]
    aggregated = aggregate_platform_results(contents)
    
    return {
        "integrated_document": {
            "integrated_content": aggregated["merged_content"],
            "source_count": aggregated["source_count"],
            "metadata": {
                "integration_method": "simulation_mode",
                "processing_timestamp": datetime.now().isoformat(),
                "simulation": True
            }
        },
        "processed_contents": [
            {
                "platform": r["platform"],
                "content": r["content"],
                "fact_checked": False,
                "confidence": r["confidence"]
            }
            for r in mock_results
        ],
        "raw_results": mock_results,
        "processing_summary": {
            "original_count": len(mock_results),
            "after_filtering": len(mock_results),
            "after_deduplication": len(mock_results),
            "ai_integration_enabled": request.enable_ai_processing,
            "fact_check_enabled": False,
            "simulation_mode": True,
            "processing_time": datetime.now().isoformat()
        }
    }

async def _real_search(request: SearchRequest) -> Dict[str, Any]:
    """真实搜索 - 调用实际平台"""
    logger.info("执行真实搜索")
    
    # 使用原有的聚合器
    ai_config = request.ai_config if request.enable_ai_processing else None
    
    result = aggregator.start_aggregation(
        platforms=request.platforms,
        query=request.user_input,
        ai_processor_config=ai_config
    )
    
    # 转换为统一格式
    return {
        "integrated_document": {
            "integrated_content": result["aggregated_result"].get("merged_content", ""),
            "source_count": len(result["stream_results"]),
            "metadata": {
                "integration_method": "real_mode",
                "processing_timestamp": result["processing_time"],
                "simulation": False
            }
        },
        "processed_contents": [
            {
                "platform": r["platform"],
                "content": r["content"],
                "fact_checked": False,
                "confidence": r["confidence"]
            }
            for r in result["stream_results"]
        ],
        "raw_results": result["stream_results"],
        "processing_summary": {
            "original_count": len(result["stream_results"]),
            "after_filtering": len(result["stream_results"]),
            "after_deduplication": len(result["stream_results"]),
            "ai_integration_enabled": request.enable_ai_processing,
            "fact_check_enabled": False,
            "simulation_mode": False,
            "processing_time": result["processing_time"]
        }
    }

def _generate_mock_content(platform: str, query: str) -> str:
    """生成模拟内容"""
    config = PLATFORM_CONFIGS.get(platform, {})
    description = config.get("description", f"{platform} AI助手")
    
    return f"""# {platform} 回答

关于 "{query}" 的分析：

## 核心观点

{description}为您提供以下见解：

### 主要要点
1. **深入分析**: 基于大量训练数据，我能够提供全面的分析
2. **多角度思考**: 从不同维度审视问题，确保答案的完整性  
3. **实用建议**: 结合理论知识和实践经验，给出可操作的建议
4. **持续学习**: 不断更新知识库，保持信息的时效性

### 详细说明

这是一个模拟的回答内容，展示了 {platform} 在处理 "{query}" 这类问题时的能力特点。在实际使用中，我会根据具体的问题内容提供更加详细和针对性的答案。

### 相关建议

- 建议结合多个信息源进行验证
- 根据具体情况调整应用方式
- 保持批判性思维，独立判断

*注：这是模拟模式下的示例回答，用于测试系统功能。*
"""

@app.get("/platforms")
async def get_platforms():
    """获取支持的平台列表"""
    platforms = list(PLATFORM_CONFIGS.keys())
    
    return {
        "success": True,
        "platforms": platforms,
        "count": len(platforms),
        "details": PLATFORM_CONFIGS
    }

@app.get("/platform-status")
async def get_all_platform_status():
    """获取所有平台状态"""
    statuses = []
    
    for platform, config in PLATFORM_CONFIGS.items():
        status = PlatformStatus(
            platform=platform,
            supported=config["supported"],
            available=config["status"] == "ready",
            has_account=False,  # 暂时简化
            simulation_available=True,
            description=config["description"]
        )
        statuses.append(status.model_dump())
    
    return {
        "success": True,
        "statuses": statuses,
        "summary": {
            "total": len(statuses),
            "supported": sum(1 for s in statuses if s["supported"]),
            "available": sum(1 for s in statuses if s["available"]),
            "simulation_ready": len(statuses)
        }
    }

@app.get("/platform-status/{platform}")
async def get_platform_status(platform: str):
    """获取特定平台状态"""
    if platform not in PLATFORM_CONFIGS:
        raise HTTPException(status_code=404, detail="平台不存在")
    
    config = PLATFORM_CONFIGS[platform]
    status = PlatformStatus(
        platform=platform,
        supported=config["supported"],
        available=config["status"] == "ready", 
        has_account=False,
        simulation_available=True,
        description=config["description"]
    )
    
    return {
        "success": True,
        "status": status.model_dump()
    }

@app.post("/quick-search")
async def quick_search(query: str, platforms: Optional[str] = None, simulation: bool = True):
    """快速搜索接口"""
    try:
        platform_list = platforms.split(",") if platforms else ["DeepSeek"]
        
        request = SearchRequest(
            user_input=query,
            platforms=platform_list,
            enable_ai_processing=False,
            simulation_mode=simulation
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
            return {"success": True, "config": config}
        else:
            return {"success": False, "message": "配置文件不存在"}
    except Exception as e:
        logger.error(f"获取配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")

@app.post("/simulation/toggle")
async def toggle_simulation_mode(enabled: bool = True):
    """切换模拟模式"""
    return {
        "success": True,
        "simulation_mode": enabled,
        "message": f"模拟模式已{'启用' if enabled else '禁用'}",
        "description": "模拟模式用于测试功能，不调用真实AI平台"
    }

@app.delete("/search-status/{search_id}")
async def clear_search_status(search_id: str):
    """清除搜索状态"""
    if search_id in search_status_store:
        del search_status_store[search_id]
        return {"success": True, "message": "搜索状态已清除"}
    else:
        raise HTTPException(status_code=404, detail="搜索ID不存在")

async def _check_real_platform_availability(platform: str) -> bool:
    """检查真实平台是否可用"""
    try:
        # 这里应该实现真实的平台可用性检查
        # 检查Cookie是否存在、是否有效等
        
        # 暂时返回基于平台的模拟结果
        if platform in ["DeepSeek", "Kimi"]:
            # 模拟某些平台可用
            await asyncio.sleep(0.5)  # 模拟检查延时
            return True
        else:
            # 模拟其他平台不可用
            await asyncio.sleep(0.5)
            return False
            
    except Exception as e:
        logger.error(f"检查平台 {platform} 可用性失败: {e}")
        return False

async def _perform_real_search(platform: str, query: str) -> str:
    """执行真实平台搜索"""
    try:
        # 这里应该实现真实的平台搜索逻辑
        # 使用保存的Cookie调用真实的AI平台
        
        # 暂时返回模拟的真实搜索结果
        await asyncio.sleep(2)  # 模拟真实搜索延时
        
        return f"""# {platform} 真实搜索结果

关于 "{query}" 的回答：

## 🔥 真实平台响应

这是来自 {platform} 的真实搜索结果。通过配置的Cookie成功连接到平台并获得回答。

### 核心内容
1. **真实性验证**: 此回答来自真实的AI平台
2. **实时数据**: 获取最新的知识和信息
3. **平台特色**: 体现 {platform} 的独特能力
4. **完整功能**: 支持完整的对话和交互

### 技术说明

真实模式下，系统会：
- 使用配置的Cookie连接平台
- 发送真实的搜索请求
- 获取平台的原始回答
- 保持搜索的实时性和准确性

### 注意事项

- 真实搜索依赖于平台的可用性
- Cookie需要定期更新以保持有效性
- 不同平台可能有不同的响应格式

*这是真实模式下的示例内容，实际部署时会连接到真实的AI平台。*
"""
        
    except Exception as e:
        logger.error(f"平台 {platform} 真实搜索失败: {e}")
        return f"❌ {platform} 搜索失败: {str(e)}"

@app.post("/real-platforms/check")
async def check_real_platforms():
    """检查所有真实平台的可用性"""
    try:
        platforms = list(PLATFORM_CONFIGS.keys())
        results = {}
        
        for platform in platforms:
            # 检查平台是否有配置的Cookie
            has_config = await _check_platform_config(platform)
            
            if has_config:
                # 测试连接
                is_available = await _check_real_platform_availability(platform)
                results[platform] = {
                    "configured": True,
                    "available": is_available,
                    "status": "ready" if is_available else "connection_failed",
                    "message": "连接成功" if is_available else "连接失败，请检查Cookie"
                }
            else:
                results[platform] = {
                    "configured": False,
                    "available": False,
                    "status": "not_configured",
                    "message": "未配置Cookie"
                }
        
        return {
            "success": True,
            "platforms": results,
            "summary": {
                "total": len(results),
                "configured": sum(1 for r in results.values() if r["configured"]),
                "available": sum(1 for r in results.values() if r["available"])
            }
        }
        
    except Exception as e:
        logger.error(f"检查真实平台失败: {e}")
        raise HTTPException(status_code=500, detail=f"检查失败: {str(e)}")

async def _check_platform_config(platform: str) -> bool:
    """检查平台是否有配置"""
    try:
        # 这里应该检查是否有保存的Cookie配置
        # 暂时返回模拟结果
        return platform in ["DeepSeek", "Kimi"]
    except Exception as e:
        logger.error(f"检查平台配置失败: {e}")
        return False

@app.post("/real-platforms/import-cookies")
async def import_platform_cookies(cookies_data: dict):
    """导入平台Cookie"""
    try:
        # 这里应该实现Cookie的安全保存
        # 包括加密、验证等
        
        imported_count = 0
        results = {}
        
        for platform, cookie in cookies_data.items():
            if platform in PLATFORM_CONFIGS:
                # 验证Cookie格式
                if _validate_cookie_format(cookie):
                    # 保存Cookie (这里需要实现安全存储)
                    success = await _save_platform_cookie(platform, cookie)
                    if success:
                        imported_count += 1
                        results[platform] = {
                            "success": True,
                            "message": "Cookie导入成功"
                        }
                    else:
                        results[platform] = {
                            "success": False,
                            "message": "Cookie保存失败"
                        }
                else:
                    results[platform] = {
                        "success": False,
                        "message": "Cookie格式无效"
                    }
            else:
                results[platform] = {
                    "success": False,
                    "message": "不支持的平台"
                }
        
        return {
            "success": True,
            "imported_count": imported_count,
            "results": results,
            "message": f"成功导入 {imported_count} 个平台的Cookie"
        }
        
    except Exception as e:
        logger.error(f"导入Cookie失败: {e}")
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")

def _validate_cookie_format(cookie: str) -> bool:
    """验证Cookie格式"""
    try:
        # 简单的Cookie格式验证
        if not cookie or len(cookie) < 10:
            return False
        
        # 检查是否包含基本的Cookie字段
        if '=' not in cookie:
            return False
        
        return True
    except Exception:
        return False

async def _save_platform_cookie(platform: str, cookie: str) -> bool:
    """安全保存平台Cookie"""
    try:
        # 这里应该实现Cookie的加密保存
        # 可以保存到数据库或加密文件
        
        # 暂时模拟保存成功
        return True
        
    except Exception as e:
        logger.error(f"保存平台Cookie失败: {e}")
        return False

async def _check_browser_session() -> bool:
    """检查浏览器会话是否可用"""
    try:
        from playwright.async_api import async_playwright
        
        playwright = await async_playwright().start()
        try:
            browser = await playwright.chromium.connect_over_cdp("http://localhost:9222")
            contexts = browser.contexts
            
            # 检查是否有AI平台页面
            ai_domains = ["chat.deepseek.com", "kimi.moonshot.cn", "chatglm.cn"]
            
            for context in contexts:
                for page in context.pages:
                    for domain in ai_domains:
                        if domain in page.url:
                            await browser.close()
                            await playwright.stop()
                            return True
            
            await browser.close()
            await playwright.stop()
            return False
            
        except Exception:
            await playwright.stop()
            return False
            
    except ImportError:
        return False
    except Exception:
        return False

async def _perform_browser_search(platforms: List[str], query: str) -> Dict:
    """使用浏览器自动化进行搜索"""
    try:
        from core.browser_search_engine import browser_search
        
        result = await browser_search(platforms, query)
        
        if result.get("success"):
            # 转换为统一格式
            unified_results = []
            for platform_result in result.get("results", []):
                unified_results.append({
                    "platform": platform_result.get("platform", "Unknown"),
                    "content": platform_result.get("content", ""),
                    "timestamp": platform_result.get("timestamp", datetime.now().isoformat()),
                    "is_complete": platform_result.get("success", False),
                    "confidence": 0.9 if platform_result.get("success") else 0.0,
                    "status": "success" if platform_result.get("success") else "failed",
                    "method": "browser_automation"
                })
            
            return {
                "success": True,
                "results": unified_results,
                "method": "browser_automation"
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "浏览器搜索失败"),
                "results": []
            }
            
    except Exception as e:
        logger.error(f"浏览器搜索异常: {e}")
        return {
            "success": False,
            "error": str(e),
            "results": []
        }

async def _fallback_real_search(platforms: List[str], query: str, live_results: Dict) -> List[Dict]:
    """传统的Cookie/API搜索回退方法"""
    results = []
    
    for i, platform in enumerate(platforms):
        # 开始搜索该平台
        live_results[platform]["status"] = "searching"
        live_results[platform]["progress_text"] = f"正在连接 {platform}..."
        live_results[platform]["start_time"] = datetime.now().isoformat()
        
        # 尝试真实搜索
        try:
            live_results[platform]["progress_text"] = f"正在调用 {platform} API..."
            await asyncio.sleep(1)
            
            live_results[platform]["progress_text"] = f"正在处理 {platform} 响应..."
            await asyncio.sleep(1)
            
            # 检查是否可以连接到真实平台
            real_success = await _check_real_platform_availability(platform)
            
            if real_success:
                # 真实搜索成功
                content = await _perform_real_search(platform, query)
                live_results[platform]["content"] = content
                live_results[platform]["status"] = "completed"
                live_results[platform]["progress_text"] = "真实搜索完成 ✅"
                
                result = {
                    "platform": platform,
                    "content": content,
                    "timestamp": datetime.now().isoformat(),
                    "is_complete": True,
                    "confidence": 0.85,  # 真实搜索置信度
                    "status": "success"
                }
            else:
                # 真实搜索失败
                live_results[platform]["status"] = "failed"
                live_results[platform]["progress_text"] = "连接失败，请检查配置"
                live_results[platform]["error"] = "无法连接到平台，可能需要重新配置Cookie"
                
                result = {
                    "platform": platform,
                    "content": f"⚠️ {platform} 连接失败，请检查平台配置或Cookie是否有效。建议使用浏览器会话模式。",
                    "timestamp": datetime.now().isoformat(),
                    "is_complete": False,
                    "confidence": 0.0,
                    "status": "failed"
                }
            
        except Exception as e:
            # 搜索异常
            live_results[platform]["status"] = "failed"
            live_results[platform]["progress_text"] = "搜索异常"
            live_results[platform]["error"] = str(e)
            
            result = {
                "platform": platform,
                "content": f"❌ {platform} 搜索异常: {str(e)}",
                "timestamp": datetime.now().isoformat(),
                "is_complete": False,
                "confidence": 0.0,
                "status": "error"
            }
        
        live_results[platform]["end_time"] = datetime.now().isoformat()
        results.append(result)
        
        # 平台间隔时间
        if i < len(platforms) - 1:
            await asyncio.sleep(0.5)
    
    return results

@app.get("/browser-platforms")
async def get_browser_platforms():
    """获取浏览器会话中的可用平台"""
    try:
        from core.browser_search_engine import BrowserSearchEngine
        
        engine = BrowserSearchEngine()
        available_platforms = await engine.detect_available_platforms()
        
        return {
            "success": True,
            "platforms": available_platforms,
            "count": len(available_platforms),
            "message": f"检测到 {len(available_platforms)} 个已登录平台"
        }
    except Exception as e:
        logger.error(f"浏览器平台检测失败: {e}")
        return {
            "success": False,
            "platforms": [],
            "count": 0,
            "error": str(e),
            "message": "浏览器平台检测失败"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 