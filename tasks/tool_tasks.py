from typing import Dict, Any, List, Optional
from tasks.tool_agent import dispatch_tool_call, TOOLS, TOOL_HANDLERS, TOOL_NAME_TO_MODEL
from tasks.llm_client import llm
from langgraph.prebuilt import create_react_agent
from langchain_core.output_parsers import PydanticToolsParser
from pydantic import ValidationError
import json
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Simple task decorator that does nothing (replaces the scheduler.task decorator)
def task(*args, **kwargs):
    def decorator(func):
        return func
    return decorator

def get_run_logger():
    """Get the logger instance for tasks"""
    return logger

# -----------------------
# LLM + Parser + Agent
# -----------------------

# 1️⃣ LLM đã bind với tool schemas
llm_with_tools = llm.bind_tools(TOOLS)

# 2️⃣ Parser để convert tool_calls -> Pydantic objects
parser = PydanticToolsParser(tools=TOOLS)

# 3️⃣ Agent tự bind tools
agent_executor = create_react_agent(llm, TOOLS)

# -----------------------
# Tool Execution
# -----------------------

async def execute_tool(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a single tool with the given input data."""
    logger = get_run_logger()
    tool_name = input_data.get("tool_name")
    params = input_data.get("params", {})
    logger.info(f"⚙️ Executing tool {tool_name} with params {params}")
    
    try:
        result = await dispatch_tool_call(tool_name, params)
        return {"ok": True, "result": result}
    except Exception as e:
        error_msg = f"Error executing tool {tool_name}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {"ok": False, "error": error_msg}

# -----------------------
# Task Definitions
# -----------------------

def lay_danh_sach_cong_cu() -> Dict[str, str]:
    return {
        "tim_kiem_thong_tin": "Tìm kiếm thông tin trên internet",
        "tinh_toan": "Thực hiện các phép tính toán cơ bản",
        "thoi_tiet": "Xem thông tin thời tiết",
        "chuyen_doi_tien_te": "Chuyển đổi tiền tệ",
    }

def get_available_tools() -> Dict[str, str]:
    return lay_danh_sach_cong_cu()

async def process_with_agent(input_data: Dict[str, Any]) -> Dict[str, Any]:
    logger_task = get_run_logger()
    tool_name = input_data.get("tool_name")
    content = input_data.get("content")
    logger_task.info(f"⚙️ Dispatching tool {tool_name} with params {content}")

    try:
        response = agent_executor.invoke({"messages": [{"role": "user", "content": content}]})
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

            # Duyệt từng tool_call (tc) và gọi dispatcher
            for idx, tc in enumerate(tool_calls):
                tool_name = tc.get("name")
                params = tc.get("args", {})  # args chứa tham số thực tế

                # nhẹ nhàng chuẩn hoá tham số (ví dụ tên thành phố)
                if "thanh_pho" in params and isinstance(params["thanh_pho"], str):
                    params["thanh_pho"] = params["thanh_pho"].strip()

                logger_task.info(f"⚙️ Agent requested tool: {tool_name} with args: {params}")

                # Dispatch to handler
                dispatch_res = await dispatch_tool_call(tool_name, params)
                tool_results.append({"tool_name": tool_name, "args": params, "dispatch": dispatch_res})

        # Build reply: let LLM synthesize a user-facing reply in Vietnamese based on tool_results + user query
        reply = None
        llm_raw = None
        if tool_results:
            # Compose synthesis prompt (concise, in Vietnamese)
            synthesis_payload = {
                "user_query": content,
                "tool_results": tool_results,
            }
            synth_prompt = (
                "Bạn là trợ lý hữu ích. Dưới đây là truy vấn của người dùng và kết quả từ các công cụ thực thi.\n\n"
                f"Truy vấn: {content}\n\n"
                f"Kết quả công cụ (JSON): {json.dumps(tool_results, ensure_ascii=False)}\n\n"
                "Hãy tổng hợp một câu trả lời ngắn gọn, thân thiện, bằng tiếng Việt, dựa trên kết quả công cụ. "
                "Nếu có lỗi hoặc công cụ báo lỗi, hãy thông báo lỗi một cách lịch sự và gợi ý bước tiếp theo cho người dùng.\n\n"
                "Trả lời ngắn gọn:"
            )

            # Call llm (non-tool) to synthesize final reply
            try:
                ai_msg = await llm.ainvoke(synth_prompt)
                llm_raw = ai_msg
                reply_text = getattr(ai_msg, "content", None)
                if reply_text and reply_text.strip():
                    reply = reply_text.strip()
                else:
                    # fallback: try to extract summary from last tool result
                    last = tool_results[-1]
                    if last.get("dispatch", {}).get("ok"):
                        res = last["dispatch"]["result"]
                        if isinstance(res, dict):
                            reply = res.get("summary") or res.get("converted") or res.get("value") or str(res)
                        else:
                            reply = str(res)
                    else:
                        reply = f"Error: {last.get('dispatch', {}).get('error')}"
            except Exception as e:
                logger_task.exception(f"❌ Error while calling llm to synthesize reply: {e}")
                # fallback to previous rule-based reply
                last = tool_results[-1]
                if last.get("dispatch", {}).get("ok"):
                    res = last["dispatch"]["result"]
                    if isinstance(res, dict):
                        reply = res.get("summary") or res.get("converted") or res.get("value") or str(res)
                    else:
                        reply = str(res)
                else:
                    reply = f"Error: {last.get('dispatch', {}).get('error')}"

        return {"messages": messages, "tool_results": tool_results, "reply": reply, "llm_raw": llm_raw}

    except Exception as e:
        logger_task.exception(f"❌ Lỗi khi chạy agent: {e}")
        return {"messages": [], "tool_results": [], "error": str(e)}

# Export required variables for other modules
__all__ = [
    'execute_tool',
    'get_available_tools',
    'process_with_agent',
    'agent_executor',
    'TOOLS',
    'TOOL_HANDLERS',
    'TOOL_NAME_TO_MODEL'
]
