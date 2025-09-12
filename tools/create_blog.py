# tools/create_blog_tool.py
from typing import Dict, Any
import os
import httpx
from pydantic import BaseModel, Field

BASE_URL = os.getenv("IOT_SCHEDULE_API_BASE")
TOKEN = os.getenv("IOT_SCHEDULE_API_TOKEN") 

class CreateBlogParams(BaseModel):
    topic: str = Field(..., description="Chủ đề blog muốn tạo")

async def handle_create_blog(topic: str) -> Dict[str, Any]:
    url = f"{BASE_URL}/v1/agent/blogs"
    headers = {"Accept": "*/*", "Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
    payload = {"topic": topic}
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, headers=headers, json=payload)
    try:
        return {"ok": True, "data": resp.json()}
    except Exception:
        return {"ok": False, "error": resp.text}
