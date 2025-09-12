# tools/list_blogs_tool.py
from typing import Dict, Any
import os
import httpx

BASE_URL = os.getenv("IOT_SCHEDULE_API_BASE")
TOKEN = os.getenv("IOT_SCHEDULE_API_TOKEN") 

# -----------------------------
# Tool model
# -----------------------------
class ListBlogs():
    """Không cần tham số nào để lấy danh sách blog."""

# -----------------------------
# Handler
# -----------------------------
async def handle_list_blogs() -> Dict[str, Any]:
    url = f"{BASE_URL}/v1/agent/blogs"
    headers = {"Accept": "*/*", "Authorization": f"Bearer {TOKEN}"}

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers)

    try:
        data: List[Dict[str, Any]] = resp.json()
        # Rút gọn chỉ lấy những trường quan trọng
        summary = [
            {
                "id": item.get("id"),
                "title": item.get("title"),
                "intro": item.get("intro"),
            }
            for item in data
        ]
        return {"ok": True, "data": summary}
    except Exception:
        return {"ok": False, "error": resp.text}