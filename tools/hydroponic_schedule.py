# tools/iot_schedule_tool.py
import os
from typing import Any, Dict
import httpx
from pydantic import BaseModel, Field

# -----------------------------
# Pydantic model tĩnh
# -----------------------------
class HydroponicSchedule(BaseModel):
    """Lấy lịch thủy canh cho thiết bị IoT."""
    # Không cần trường nào, vì tất cả đều cố định

# -----------------------------
# Thông số tĩnh
# -----------------------------
DEVICE_ID = "device-001"
BASE_URL = os.getenv("IOT_SCHEDULE_API_BASE")
TOKEN = os.getenv("IOT_SCHEDULE_API_TOKEN")
TIMEOUT = float(os.getenv("IOT_SCHEDULE_API_TIMEOUT", "10.0"))

# -----------------------------
# Async handler tĩnh
# -----------------------------
async def handle_hydroponic_schedule() -> Dict[str, Any]:
    """Lấy lịch thủy canh cho thiết bị IoT, thông số tĩnh"""
    url = f"{BASE_URL.rstrip('/')}/v1/schedule/{DEVICE_ID}"
    headers = {"Accept": "*/*"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            resp = await client.get(url, headers=headers)
        except httpx.RequestError as e:
            return {"ok": False, "error": f"Request error: {str(e)}"}
        except Exception as e:
            return {"ok": False, "error": f"Unexpected error: {str(e)}"}

    try:
        content = resp.json()
    except Exception:
        content = resp.text

    if 200 <= resp.status_code < 300:
        return {"ok": True, "status_code": resp.status_code, "data": content}
    else:
        return {"ok": False, "status_code": resp.status_code, "error": content or resp.text}

# -----------------------------
# Synchronous wrapper
# -----------------------------
def get_hydroponic_schedule_sync() -> Dict[str, Any]:
    import asyncio
    return asyncio.run(handle_hydroponic_schedule())
