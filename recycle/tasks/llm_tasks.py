"""
Natural Language Processing tasks using Large Language Models (LLM).
"""
from typing import Dict, Any, Optional
import logging
from dotenv import load_dotenv
from tasks.llm_client import llm
from tasks.tool_agent import TOOLS

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Task decorator for compatibility
def task(name: str):
    """Decorator to maintain compatibility with task functions"""
    def decorator(func):
        return func
    return decorator

async def analyze_intent(question: str) -> str:
    """
    Phân tích ý định của câu hỏi người dùng.
    
    Args:
        question: Nội dung câu hỏi cần phân tích
        
    Returns:
        str: Tên công cụ hoặc hành động phù hợp
    """
    logger.info(f"[LLM] Đang phân tích ý định: {question[:50]}...")
    
    # Lấy danh sách công cụ
    tool_descriptions = {}
    for tool in TOOLS:
        schema = tool.schema()
        tool_name = tool.__name__
        tool_descriptions[tool_name] = schema.get('description', 'No description available')
    
    tool_text = "\n".join([f"- {k}: {v}" for k, v in tool_descriptions.items()])
    
    prompt_text = f"""
Bạn là một trợ lý thông minh. Hãy phân tích câu hỏi và chọn công cụ phù hợp.

Các công cụ có sẵn:
{tool_text}

Câu hỏi: {question}

Trả lời bằng tên công cụ phù hợp nhất.
"""
    try:
        response = await llm.ainvoke(prompt_text)
        intent = response.content.strip().lower()
        logger.info(f"[LLM] Đã xác định ý định: {intent}")
        return intent
    except Exception as e:
        logger.error(f"[LLM] Lỗi khi phân tích ý định: {e}")
        return "general_qa"  # Giá trị mặc định

async def generate_response(
    question: str,
    context: str = "",
    tool_output: str = ""
) -> str:
    """
    Tạo phản hồi tự nhiên dựa trên câu hỏi và ngữ cảnh.
    
    Args:
        question: Nội dung câu hỏi của người dùng
        context: Thông tin bổ sung từ cơ sở dữ liệu
        tool_output: Kết quả từ các công cụ đã thực thi
        
    Returns:
        str: Phản hồi được tạo ra
    """
    logger.info("[LLM] Đang tạo phản hồi...")
    
    prompt_text = f"""
Bạn là một trợ lý AI hữu ích. Hãy trả lời câu hỏi dựa trên thông tin được cung cấp.

Câu hỏi: {question}

Ngữ cảnh bổ sung:
{context or "Không có thông tin bổ sung."}

Kết quả từ công cụ:
{tool_output or "Không có kết quả từ công cụ."}

Hãy trả lời một cách ngắn gọn và chính xác.
"""
    try:
        response = await llm.ainvoke(prompt_text)
        return response.content.strip()
    except Exception as e:
        logger.error(f"[LLM] Lỗi khi tạo phản hồi: {e}")
        return "❌ Đã xảy ra lỗi khi xử lý yêu cầu của bạn. Vui lòng thử lại sau."
