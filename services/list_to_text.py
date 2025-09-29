from typing import Any


def list_to_text(data: Any) -> str:
    """Nếu là list thì join thành text, nếu là dict thì dump, còn lại cast str"""
    if not data:
        return ""
    if isinstance(data, list):
        return "\n".join([f"- {item}" for item in data])
    elif isinstance(data, dict):
        return "\n".join([f"{k}: {v}" for k, v in data.items()])
    return str(data)