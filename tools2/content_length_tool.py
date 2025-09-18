from langchain_core.tools import tool

@tool
def content_length_tool(text: str) -> int:
    """Trả về số ký tự trong text"""
    return len(text)
