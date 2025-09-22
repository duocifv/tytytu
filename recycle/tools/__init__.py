"""
Initialize the tools package and expose the main interfaces.
"""
from typing import Dict, Any, List, Callable, Awaitable
from pydantic import BaseModel

# Re-export tool models and handlers from respective modules
from .search_tools import TimKiemThongTin, handle_tim_kiem_thong_tin
from .math_tools import TinhToan, handle_tinh_toan, safe_eval_expr
from .weather_tools import ThoiTiet, handle_thoi_tiet
from .chuyen_doi_tien_te import ChuyenDoiTienTe, handle_chuyen_doi_tien_te

# List of all available tools
TOOLS = [TimKiemThongTin, TinhToan, ThoiTiet, ChuyenDoiTienTe]

# Mapping of tool names to their handler functions
TOOL_HANDLERS: Dict[str, Callable[..., Awaitable[Dict[str, Any]]]] = {
    "TimKiemThongTin": handle_tim_kiem_thong_tin,
    "TinhToan": handle_tinh_toan,
    "ThoiTiet": handle_thoi_tiet,
    "ChuyenDoiTienTe": handle_chuyen_doi_tien_te,
}

# Mapping of tool names to their Pydantic models
TOOL_NAME_TO_MODEL: Dict[str, BaseModel] = {
    "TimKiemThongTin": TimKiemThongTin,
    "TinhToan": TinhToan,
    "ThoiTiet": ThoiTiet,
    "ChuyenDoiTienTe": ChuyenDoiTienTe,
}

__all__ = [
    'TOOLS',
    'TOOL_HANDLERS',
    'TOOL_NAME_TO_MODEL',
    'TimKiemThongTin',
    'TinhToan',
    'ThoiTiet',
    'ChuyenDoiTienTe',
    'handle_tim_kiem_thong_tin',
    'handle_tinh_toan',
    'handle_thoi_tiet',
    'handle_chuyen_doi_tien_te',
    'safe_eval_expr',
]
