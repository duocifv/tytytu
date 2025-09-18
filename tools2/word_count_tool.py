from langchain_core.tools import tool

@tool
def word_count_tool(text: str) -> int:
    """Trả về số từ trong text"""
    return len(text.split())
