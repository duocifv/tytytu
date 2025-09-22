import logging
from typing import Dict, Any, Optional
from flows.workflow_run import start_workflow, running 
from services.llm_service import llm

logger = logging.getLogger(__name__)

async def analyze_message_for_workflow(message: str, user_id: str) -> bool:
    """
    Phân tích xem tin nhắn có muốn bật workflow không.
    Trả về True nếu muốn bật, False nếu không.
    """
    # Ví dụ giả lập: nếu tin nhắn chứa từ 'bật workflow', 'start', 'run'
    triggers = ["bật workflow", "start workflow", "run workflow", "bật", "khởi chạy"]
    lower_msg = message.lower()
    for t in triggers:
        if t in lower_msg:
            return True
    return False


async def process_message(
    message: str,
    user_id: str,
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Flow xử lý tin nhắn:
    1. Phân tích tin nhắn để xem có bật workflow không
    2. Nếu LLM xác nhận bật workflow, gọi start_workflow()
    3. Trả về phản hồi (text)
    """
    logger.info(f"🚀 Bắt đầu flow xử lý tin nhắn cho user {user_id}")

    # Kiểm tra xem workflow có đang chạy không
    workflow_running = running

    # 1️⃣ Phân tích tin nhắn để quyết định bật workflow
    want_to_start = await analyze_message_for_workflow(message, user_id)

    if want_to_start and not workflow_running:
        logger.info(f"💡 LLM quyết định bật workflow cho user {user_id}")
        start_workflow()
        llm_response = "✅ Workflow đã được bật!"
    elif want_to_start and workflow_running:
        llm_response = "⚠️ Workflow đang chạy rồi."
    else:
        # Trả lời bình thường qua LLM
        llm_response = await llm.ainvoke(message)

    response = {
        "text": llm_response,
        "chart_base64": None
    }

    logger.info(f"✅ Flow hoàn tất cho user {user_id}")
    return response
