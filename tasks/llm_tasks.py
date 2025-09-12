"""
Các tác vụ xử lý ngôn ngữ tự nhiên sử dụng mô hình ngôn ngữ lớn (LLM).
"""

from prefect import task
from typing import Dict, Any, Optional
from langchain.chat_models import init_chat_model
import logging
from dotenv import load_dotenv
from tasks.tool_tasks import lay_danh_sach_cong_cu
from tasks.llm_client import llm

load_dotenv()

# Logger chuẩn Python
logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

@task(name="phan-tich-y-dinh")
async def phan_tich_y_dinh(cau_hoi: str) -> str:
    """
    Phân tích ý định của câu hỏi người dùng.

    Args:
        cau_hoi: Nội dung câu hỏi cần phân tích

    Returns:
        str: Tên công cụ hoặc hành động phù hợp
    """
    logger.info(f"🔍 Phân tích ý định: {cau_hoi[:50]}...")
    # Lấy tool list động
    tools = lay_danh_sach_cong_cu()
    tool_text = "\n".join([f"- {k}: {v}" for k, v in tools.items()])
    
    prompt_text = f"""
Bạn là một trợ lý thông minh. Hãy phân tích câu hỏi và chọn công cụ phù hợp.

Các công cụ có sẵn:
{tool_text}

Câu hỏi: {cau_hoi}

Trả lời bằng tên công cụ phù hợp nhất.
"""
    try:
        response = await llm.ainvoke(prompt_text)
        return response.content.strip().lower()
    except Exception as e:
        logger.error(f"❌ Lỗi khi phân tích ý định: {e}")
        return "hoi_dap"  # Mặc định

@task(name="tao-phat-bieu")
async def tao_phat_bieu(
    cau_hoi: str,
    nguyen_canh: str = "",
    phan_hoi_cong_cu: str = ""
) -> str:
    """
    Tạo phản hồi tự nhiên dựa trên câu hỏi và ngữ cảnh.

    Args:
        cau_hoi: Nội dung câu hỏi của người dùng
        nguyen_canh: Thông tin bổ sung từ cơ sở dữ liệu
        phan_hoi_cong_cu: Kết quả từ các công cụ đã thực thi

    Returns:
        str: Phản hồi được tạo ra
    """
    logger.info("💭 Tạo phản hồi...")

    prompt_text = f"""
Bạn là một trợ lý AI hữu ích. Hãy trả lời câu hỏi dựa trên thông tin được cung cấp.

Câu hỏi: {cau_hoi}

Ngữ cảnh bổ sung:
{nguyen_canh or "Không có thông tin bổ sung."}

Kết quả từ công cụ:
{phan_hoi_cong_cu or "Không có kết quả từ công cụ."}

Hãy trả lời một cách ngắn gọn và chính xác.
"""
    try:
        response = await llm.ainvoke(prompt_text)
        return response.content.strip()
    except Exception as e:
        logger.error(f"❌ Lỗi khi tạo phản hồi: {e}")
        return "Xin lỗi, tôi gặp khó khăn khi xử lý yêu cầu của bạn. Vui lòng thử lại sau."
