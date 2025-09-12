# tools/list_blogs_tool.py
from typing import Dict, Any, List
import os
import httpx
from collections import defaultdict
import matplotlib.pyplot as plt
import io
import base64
from pydantic import BaseModel

BASE_URL = os.getenv("IOT_SCHEDULE_API_BASE", "https://vegetable-container.onrender.com")
TOKEN = os.getenv("IOT_SCHEDULE_API_TOKEN")

# -----------------------------
# Tool model
# -----------------------------
class ListBlogs(BaseModel):
    """Dùng để lấy danh sách blog và thống kê số lượng blog theo ngày."""

# -----------------------------
# Helper tạo biểu đồ
# -----------------------------
def create_blog_chart(data: Dict[str, int]) -> str:
    """
    Nhận dict {ngày: số lượng} và trả về base64 chart PNG
    """
    dates = list(data.keys())
    counts = list(data.values())
    
    plt.figure(figsize=(8, 4))
    plt.bar(dates, counts, color="skyblue")
    plt.xlabel("Ngày")
    plt.ylabel("Số blog")
    plt.title("Thống kê blog theo ngày")
    plt.xticks(rotation=45)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    plt.close()
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode("utf-8")
    return f"data:image/png;base64,{img_base64}"

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

        # Rút gọn dữ liệu
        summary = [
            {
                "id": item.get("id"),
                "title": item.get("title"),
                "intro": item.get("intro"),
                "createdAt": item.get("createdAt"),
            }
            for item in data
        ]

        # Thống kê số blog theo ngày
        count_per_day = defaultdict(int)
        for item in data:
            created = item.get("createdAt")
            if created:
                date_str = created.split("T")[0]  # YYYY-MM-DD
                count_per_day[date_str] += 1

        sorted_days = dict(sorted(count_per_day.items()))
        chart_base64 = create_blog_chart(sorted_days)  # tạo chart

        return {
            "ok": True,
            "total_blogs": len(data),
            "total_days": len(count_per_day),
            "blogs": summary,
            "blogs_per_day": sorted_days,
            "chart_base64": chart_base64  # trả về base64 để agent phân tích hoặc gửi
        }

    except Exception:
        return {"ok": False, "error": resp.text}
