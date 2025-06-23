from fastapi import FastAPI, Request
from pydantic import BaseModel
from backend.account_manager import save_account, load_cookie
from backend.search_runner import search_all
from langchain_agents.prompt_optimizer import get_optimized_prompt
from ragflow_utils.deduplicate import deduplicate_results
from playwright_scripts.check_login import check_login_status

app = FastAPI()

class LoginRequest(BaseModel):
    platform: str
    account: dict

class SearchRequest(BaseModel):
    user_input: str
    platforms: list

class CheckLoginRequest(BaseModel):
    platform: str

@app.post("/login")
def login(req: LoginRequest):
    save_account(req.platform, req.account)
    return {"status": "ok"}

@app.post("/search")
def search(req: SearchRequest):
    optimized_query = get_optimized_prompt(req.user_input)
    results = search_all(optimized_query, req.platforms)
    merged = deduplicate_results([r[1] for r in results])
    return {"results": merged, "raw": results}

@app.post("/check_login")
def check_login(req: CheckLoginRequest):
    cookie = load_cookie(req.platform)
    status = check_login_status(req.platform, cookie)
    return {"status": status} 