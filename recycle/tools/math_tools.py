"""
Math-related tools and handlers.
"""
import ast
import operator as op
from typing import Dict, Any
from pydantic import BaseModel, Field

class TinhToan(BaseModel):
    """Thực hiện các phép tính toán cơ bản."""
    bieu_thuc: str = Field(..., description="Biểu thức toán học")

# Supported operators
_ALLOWED_OPERATORS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.USub: op.neg,
    ast.UAdd: op.pos,
    ast.Mod: op.mod,
}

def _safe_eval(node):
    """Evaluate a node in a safe manner."""
    if isinstance(node, ast.Num):  # <number>
        return node.n
    if isinstance(node, ast.BinOp):  # <left> <op> <right>
        left = _safe_eval(node.left)
        right = _safe_eval(node.right)
        oper = _ALLOWED_OPERATORS[type(node.op)]
        return oper(left, right)
    if isinstance(node, ast.UnaryOp):  # - <operand> e.g. -1
        operand = _safe_eval(node.operand)
        oper = _ALLOWED_OPERATORS[type(node.op)]
        return oper(operand)
    raise ValueError(f"Unsupported expression: {ast.dump(node)}")

def safe_eval_expr(expr: str):
    """
    Evaluate a mathematical expression safely.
    
    Args:
        expr: The mathematical expression to evaluate (as a string)
        
    Returns:
        Kết quả của biểu thức
        
    Raises:
        ValueError: Nếu biểu thức không hợp lệ
    """
    try:
        parsed = ast.parse(expr, mode="eval")
        return _safe_eval(parsed.body)
    except Exception as e:
        raise ValueError(f"Invalid expression: {e}")

async def handle_tinh_toan(bieu_thuc: str) -> Dict[str, Any]:
    """
    Xử lý yêu cầu tính toán.
    
    Args:
        bieu_thuc: Biểu thức cần tính toán
        
    Returns:
        Dict chứa kết quả tính toán hoặc thông báo lỗi
    """
    try:
        value = safe_eval_expr(bieu_thuc)
        return {"expression": bieu_thuc, "value": value}
    except Exception as e:
        return {"error": str(e)}
