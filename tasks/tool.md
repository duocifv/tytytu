"""
Các tác vụ thực thi công cụ (tools) trong hệ thống.
Dùng LangChain bind_tools + PydanticToolsParser để LLM chọn và parse tool.
"""

from prefect import task, get_run_logger
import logging
from langchain.chat_models import init_chat_model
from langchain_core.output_parsers import PydanticToolsParser
from pydantic import BaseModel, Field, ValidationError
from typing import Dict, Any, List, Optional
from tasks.llm_client import llm  # LLM đã khởi tạo sẵn
from langgraph.prebuilt import create_react_agent

logger = logging.getLogger(__name__)

# -----------------------
# Định nghĩa tool schemas
# -----------------------
class TimKiemThongTin(BaseModel):
    truy_van: str = Field(..., description="Nội dung cần tìm kiếm")

class TinhToan(BaseModel):
    bieu_thuc: str = Field(..., description="Biểu thức toán học")

class ThoiTiet(BaseModel):
    thanh_pho: str = Field(..., description="Tên thành phố")

class ChuyenDoiTienTe(BaseModel):
    so_tien: float = Field(..., description="Số tiền")
    tu: str = Field(..., description="Loại tiền gốc (VD: USD)")
    sang: str = Field(..., description="Loại tiền muốn đổi (VD: VND)")

TOOLS = [TimKiemThongTin, TinhToan, ThoiTiet, ChuyenDoiTienTe]

# LLM biết tool schemas
llm_with_tools = llm.bind_tools(TOOLS)

# Parser để convert tool_calls -> Pydantic objects
parser = PydanticToolsParser(tools=TOOLS)

# -----------------------
# Task thực thi tool
# -----------------------
@task(name="thuc-thi-cong-cu")
async def thuc_thi_cong_cu(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Thực thi tool theo input_data.
    """
    logger_task = get_run_logger()
    try:
        tool_name = input_data.get("tool_name")
        params = input_data.get("params", {})
        logger_task.info(f"⚙️ Xử lý tool {tool_name} với params: {params}")

        cau_hoi = f"{tool_name}: {params}"
        ai_msg = await llm_with_tools.ainvoke(cau_hoi)

        # Trường hợp model gọi tool
        if getattr(ai_msg, "tool_calls", None):
            parsed_objs = parser.invoke(ai_msg)
            logger_task.info(f"✅ Parsed tool objects: {parsed_objs}")
            return {"tool_calls": parsed_objs, "clarification": None, "raw": ai_msg}

        # Trường hợp không cần gọi tool, chỉ trả content
        content = getattr(ai_msg, "content", None)
        if content and content.strip():
            logger_task.info(f"ℹ️ Content từ model (không gọi tool): {content.strip()}")
            return {"tool_calls": [], "clarification": content.strip(), "raw": ai_msg}

        # Không tool, không content
        logger_task.warning("⚠️ Không có tool_calls và không có content trả về.")
        return {"tool_calls": [], "clarification": None, "raw": ai_msg}

    except ValidationError as ve:
        logger_task.error(f"❌ Lỗi validate tool_calls: {ve}")
        return {"tool_calls": [], "clarification": None, "error": str(ve), "raw": ai_msg}
    except Exception as e:
        logger_task.error(f"❌ Lỗi khi thực thi LLM + tool: {e}")
        return {"tool_calls": [], "clarification": None, "error": str(e), "raw": None}

# -----------------------
# Task lấy danh sách tool
# -----------------------
@task(name="lay-danh-sach-cong-cu")
def lay_danh_sach_cong_cu() -> Dict[str, str]:
    return {
        "tim_kiem_thong_tin": "Tìm kiếm thông tin trên internet",
        "tinh_toan": "Thực hiện các phép tính toán cơ bản",
        "thoi_tiet": "Cung cấp thông tin thời tiết",
        "chuyen_doi_tien_te": "Chuyển đổi tiền tệ",
    }

# -----------------------
# 4️⃣ Tạo Agent
# -----------------------
agent_executor = create_react_agent(llm, TOOLS)  # agent tự bind tools

# -----------------------
# 5️⃣ Chạy agent
# a) Không cần tool
# b) Trường hợp cần gọi tool
# -----------------------
@task(name="agent-chat")
async def agent_chat(query: str) -> Dict[str, Any]:
    logger_task = get_run_logger()
    try:
        response = agent_executor.invoke({"messages": [{"role": "user", "content": query}]})
        messages = response["messages"]  # list of Message objects

        logger_task.info("=== Messages từ Agent ===")
        for msg in messages:
            logger_task.info(f"📨 content='{getattr(msg, 'content', None)}' id='{getattr(msg, 'id', None)}'")

        tool_results: List[Dict[str, Any]] = []

        # Tìm các AIMessage có tool_calls và xử lý từng tool_call
        for msg in messages:
            tool_calls = getattr(msg, "tool_calls", None)
            if not tool_calls:
                continue

            logger_task.info(f"⚙️ Found tool_calls in message id={getattr(msg, 'id', None)}")

            # Parse Pydantic objects từ chính ai_msg (parser.invoke nhận ai_msg)
            try:
                parsed_objs = parser.invoke(msg)  # list of pydantic objects (order matches tool_calls)
                logger_task.info(f"✅ Parsed Pydantic objects: {parsed_objs}")
            except ValidationError as ve:
                logger_task.error(f"❌ Validation error while parsing tool_calls: {ve}")
                parsed_objs = []

            # Duyệt từng tool_call (tc) và mapped parsed object (nếu có)
            for idx, tc in enumerate(tool_calls):
                tool_name = tc.get("name")
                params = tc.get("args", {})  # args chứa tham số thực tế
                logger_task.info(f"⚙️ Agent muốn gọi tool: {tool_name} với input: {params}")

                # Thực thi tool (sử dụng task hiện có)
                input_data = {"tool_name": tool_name, "params": params}
                result = await thuc_thi_cong_cu(input_data)
                tool_results.append(result)

        return {"messages": messages, "tool_results": tool_results}

    except Exception as e:
        logger_task.error(f"❌ Lỗi khi chạy agent: {e}")
        return {"messages": [], "tool_results": [], "error": str(e)}
