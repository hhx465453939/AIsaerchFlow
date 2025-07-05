from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
from backend.account_manager import save_account, load_cookie
from backend.search_runner import search_all_legacy, search_and_integrate
from langchain_agents.prompt_optimizer import get_optimized_prompt
from ragflow_utils.deduplicate import deduplicate_results
from playwright_scripts.check_login import check_login_status

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="多平台AI搜索API", version="2.0.0")

class LoginRequest(BaseModel):
    platform: str
    account: dict

class SearchRequest(BaseModel):
    user_input: str
    platforms: list

class CheckLoginRequest(BaseModel):
    platform: str

# 新增：AI增强搜索请求
class AISearchRequest(BaseModel):
    user_input: str
    platforms: List[str]
    llm_config: Optional[Dict[str, Any]] = None
    browser_config: Optional[Dict[str, Any]] = None
    enable_fact_check: bool = True
    use_ai_integration: bool = True
    
class LLMConfigRequest(BaseModel):
    base_url: str
    api_key: str
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.3
    max_tokens: int = 4000

@app.post("/login")
def login(req: LoginRequest):
    """保存账号信息"""
    try:
        save_account(req.platform, req.account)
        logger.info(f"账号保存成功: {req.platform}")
        return {"status": "ok", "message": "账号保存成功"}
    except Exception as e:
        logger.error(f"账号保存失败: {e}")
        raise HTTPException(status_code=500, detail=f"账号保存失败: {e}")

@app.post("/search")
def search(req: SearchRequest):
    """传统搜索接口 - 保持兼容性"""
    try:
        logger.info(f"开始传统搜索: {req.user_input}")
        
        # 优化提示词
        optimized_query = get_optimized_prompt(req.user_input)
        
        # 执行搜索
        results = search_all_legacy(optimized_query, req.platforms)
        
        # 简单去重
        merged = deduplicate_results([r[1] for r in results])
        
        logger.info(f"传统搜索完成，结果数: {len(merged)}")
        return {
            "results": merged,
            "raw": results,
            "query": optimized_query,
            "method": "traditional"
        }
    except Exception as e:
        logger.error(f"传统搜索失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {e}")

@app.post("/ai-search")
def ai_search(req: AISearchRequest):
    """AI增强搜索接口"""
    try:
        logger.info(f"开始AI增强搜索: {req.user_input}")
        
        # 验证LLM配置
        if req.use_ai_integration and not req.llm_config:
            logger.warning("启用AI整合但未提供LLM配置，将禁用AI整合")
            req.use_ai_integration = False
        
        # 优化提示词
        optimized_query = get_optimized_prompt(req.user_input)
        logger.info(f"优化后查询: {optimized_query}")
        
        # 执行AI增强搜索和整合
        result = search_and_integrate(
            optimized_query=optimized_query,
            platforms=req.platforms,
            llm_config=req.llm_config,
            browser_config=req.browser_config,
            enable_fact_check=req.enable_fact_check,
            use_ai_integration=req.use_ai_integration
        )
        
        logger.info("AI增强搜索完成")
        return {
            "success": True,
            "data": result,
            "method": "ai_enhanced"
        }
        
    except Exception as e:
        logger.error(f"AI增强搜索失败: {e}")
        raise HTTPException(status_code=500, detail=f"AI搜索失败: {e}")

@app.post("/check_login")
def check_login(req: CheckLoginRequest):
    """检查登录状态"""
    try:
        cookie = load_cookie(req.platform)
        status = check_login_status(req.platform, cookie)
        return {"status": status}
    except Exception as e:
        logger.error(f"登录状态检查失败: {e}")
        return {"status": "检测失败"}

@app.post("/validate-llm-config")
def validate_llm_config(req: LLMConfigRequest):
    """验证LLM配置"""
    try:
        import requests
        
        # 测试LLM连接
        headers = {
            "Authorization": f"Bearer {req.api_key}",
            "Content-Type": "application/json"
        }
        
        test_data = {
            "model": req.model,
            "messages": [{"role": "user", "content": "Hello"}],
            "max_tokens": 10
        }
        
        response = requests.post(
            f"{req.base_url}/chat/completions",
            headers=headers,
            json=test_data,
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info("LLM配置验证成功")
            return {
                "valid": True,
                "message": "LLM配置有效",
                "model_info": response.json().get("model", req.model)
            }
        else:
            logger.warning(f"LLM配置验证失败: {response.status_code}")
            return {
                "valid": False,
                "message": f"连接失败: {response.status_code}",
                "error": response.text[:200]
            }
            
    except Exception as e:
        logger.error(f"LLM配置验证异常: {e}")
        return {
            "valid": False,
            "message": f"验证异常: {str(e)[:100]}",
            "error": str(e)
        }

@app.get("/health")
def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "features": {
            "traditional_search": True,
            "ai_integration": True,
            "fact_checking": True,
            "semantic_deduplication": True
        }
    }

@app.get("/platforms")
def get_platforms():
    """获取支持的平台列表"""
    from backend.search_runner import PLATFORM_RUNNERS
    
    platforms = []
    for platform_name in PLATFORM_RUNNERS.keys():
        platforms.append({
            "name": platform_name,
            "status": "available",  # 可以后续添加平台状态检测
            "features": {
                "search": True,
                "login_required": True
            }
        })
    
    return {"platforms": platforms}

# 保持向后兼容的路由
@app.post("/search_legacy")
def search_legacy(req: SearchRequest):
    """向后兼容的搜索接口"""
    return search(req) 