from pydantic import BaseModel, Field
from typing import Dict, Any

class ChuyenDoiTienTe(BaseModel):
    so_tien: float = Field(..., description="Số tiền")
    tu: str = Field(..., description="Loại tiền gốc (VD: USD)")
    sang: str = Field(..., description="Loại tiền muốn đổi (VD: VND)")

async def handle_chuyen_doi_tien_te(so_tien: float, tu: str, sang: str) -> Dict[str, Any]:
    rates = {("USD","VND"):24000, ("VND","USD"):0.000042}
    rate = rates.get((tu.upper(), sang.upper()), 1.0)
    return {"from": tu.upper(), "to": sang.upper(), "rate": rate, "converted": so_tien*rate}
