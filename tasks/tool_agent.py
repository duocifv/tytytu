import logging
from typing import Dict, Any, Callable, Awaitable
from pydantic import BaseModel, ValidationError
from langchain_core.output_parsers import PydanticToolsParser

# Import tool models + handlers
from tools.search_tools import TimKiemThongTin, handle_tim_kiem_thong_tin
from tools.math_tools import TinhToan, handle_tinh_toan
from tools.weather_tools import ThoiTiet, handle_thoi_tiet
from tools.chuyen_doi_tien_te import ChuyenDoiTienTe, handle_chuyen_doi_tien_te

logger = logging.getLogger(__name__)

# Registry
TOOLS = [TimKiemThongTin, TinhToan, ThoiTiet, ChuyenDoiTienTe]
# parser = PydanticToolsParser(tools=TOOLS)

TOOL_NAME_TO_MODEL: Dict[str, BaseModel] = {
    "TimKiemThongTin": TimKiemThongTin,
    "TinhToan": TinhToan,
    "ThoiTiet": ThoiTiet,
    "ChuyenDoiTienTe": ChuyenDoiTienTe,
}

TOOL_HANDLERS: Dict[str, Callable[..., Awaitable[Dict[str, Any]]]] = {
    "TimKiemThongTin": handle_tim_kiem_thong_tin,
    "TinhToan": handle_tinh_toan,
    "ThoiTiet": handle_thoi_tiet,
    "ChuyenDoiTienTe": handle_chuyen_doi_tien_te,
}

# Core Agent Logic
async def dispatch_tool_call(tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    Model = TOOL_NAME_TO_MODEL.get(tool_name)
    if not Model:
        return {"error": f"Unknown tool {tool_name}"}

    try:
        validated = Model(**params)
    except ValidationError as ve:
        return {"error": f"Validation error: {ve}"}

    handler = TOOL_HANDLERS.get(tool_name)
    if not handler:
        return {"error": f"No handler for {tool_name}"}

    try:
        result = await handler(**validated.dict())
        return {"ok": True, "result": result}
    except Exception as e:
        logger.exception(f"❌ Error executing {tool_name}: {e}")
        return {"error": str(e)}
