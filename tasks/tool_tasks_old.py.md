# tasks/tool_tasks.py
"""
Các tác vụ thực thi công cụ (tools) trong hệ thống.
Dùng LangChain bind_tools + PydanticToolsParser để LLM chọn và parse tool.
Dispatcher mapping: tên tool -> hàm async handler (không dùng if-elif).
"""

from prefect import task, get_run_logger
import logging
import ast
import operator as op
import json
from langchain.chat_models import init_chat_model
from langchain_core.output_parsers import PydanticToolsParser
from pydantic import BaseModel, Field, ValidationError
from typing import Dict, Any, List, Callable, Awaitable
from tasks.llm_client import llm  # LLM đã khởi tạo sẵn
from langgraph.prebuilt import create_react_agent

logger = logging.getLogger(__name__)

# -----------------------
# Định nghĩa tool schemas (Pydantic)
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

# Mapping tên tool -> Model
TOOL_NAME_TO_MODEL: Dict[str, BaseModel] = {
    "TimKiemThongTin": TimKiemThongTin,
    "TinhToan": TinhToan,
    "ThoiTiet": ThoiTiet,
    "ChuyenDoiTienTe": ChuyenDoiTienTe,
}

# -----------------------
# Safe evaluator cho TinhToan (an toàn hơn eval)
# -----------------------
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
    try:
        parsed = ast.parse(expr, mode="eval")
        return _safe_eval(parsed.body)
    except Exception as e:
        raise ValueError(f"Invalid expression: {e}")

# -----------------------
# Handlers (async) cho mỗi tool
# Thay stub bằng gọi API thật khi cần
# -----------------------
async def handle_tim_kiem_thong_tin(truy_van: str) -> Dict[str, Any]:
    # TODO: gọi search engine / tavily / google custom search ở đây
    # Stub trả về empty results
    return {"query": truy_van, "results": []}

async def handle_tinh_toan(bieu_thuc: str) -> Dict[str, Any]:
    try:
        value = safe_eval_expr(bieu_thuc)
        return {"expression": bieu_thuc, "value": value}
    except Exception as e:
        return {"error": str(e)}

async def handle_thoi_tiet(thanh_pho: str) -> Dict[str, Any]:
    # TODO: gọi weather API thật (OpenWeather/WeatherAPI)
    # Stub trả về văn bản tóm tắt
    summary = f"Thời tiết ở {thanh_pho} hôm nay có nắng, nhiệt độ cao nhất là 32°C, thấp nhất 25°C."
    return {"city": thanh_pho, "summary": summary}

async def handle_chuyen_doi_tien_te(so_tien: float, tu: str, sang: str) -> Dict[str, Any]:
    # TODO: gọi FX API (fixer, exchangerate) để lấy tỷ giá thật
    # Stub giả sử một vài tỷ giá
    rates = {
        ("VND", "USD"): 0.000042,
        ("USD", "VND"): 24000.0,
        ("EUR", "USD"): 1.08,
        ("USD", "EUR"): 0.925,
    }
    rate = rates.get((tu.upper(), sang.upper()), None)
    if rate is None:
        # fallback: giả rate = 1.0 (không chính xác)
        rate = 1.0
    converted = so_tien * rate
    return {"from": tu.upper(), "to": sang.upper(), "rate": rate, "converted": converted}

# Dispatcher mapping: tool name -> handler function
# Handler functions must be async and accept keyword args matching Pydantic model fields
TOOL_HANDLERS: Dict[str, Callable[..., Awaitable[Dict[str, Any]]]] = {
    "TimKiemThongTin": handle_tim_kiem_thong_tin,
    "TinhToan": handle_tinh_toan,
    "ThoiTiet": handle_thoi_tiet,
    "ChuyenDoiTienTe": handle_chuyen_doi_tien_te,
}

# -----------------------
# Generic dispatcher
# -----------------------
async def dispatch_tool_call(tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    logger.debug(f"dispatch_tool_call: {tool_name} with params: {params}")
    # 1) Validate params via Pydantic model if exists
    Model = TOOL_NAME_TO_MODEL.get(tool_name)
    if Model is None:
        return {"error": f"Unknown tool: {tool_name}"}

    try:
        validated = Model(**params)
    except ValidationError as ve:
        return {"error": f"Validation error: {ve}"}

    # 2) Find handler
    handler = TOOL_HANDLERS.get(tool_name)
    if handler is None:
        return {"error": f"No handler registered for tool: {tool_name}"}

    # 3) Call handler with validated params
    try:
        result = await handler(**validated.dict())
        return {"ok": True, "result": result}
    except Exception as e:
        logger.exception(f"Error executing handler for {tool_name}: {e}")
        return {"error": str(e)}

# -----------------------
# Task thực thi tool (backwards-compatible wrapper)
# Sử dụng dispatcher thay cho gọi LLM lần nữa
# -----------------------
@task(name="thuc-thi-cong-cu")
async def thuc_thi_cong_cu(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Thực thi tool theo input_data.
    input_data = {"tool_name": "ThoiTiet", "params": {"thanh_pho": "Đà Nẵng"}}
    """
    logger_task = get_run_logger()
    try:
        tool_name = input_data.get("tool_name")
        params = input_data.get("params", {}) or {}
        logger_task.info(f"⚙️ Dispatching tool {tool_name} with params: {params}")

        dispatch_res = await dispatch_tool_call(tool_name, params)
        if dispatch_res.get("ok"):
            # trả về dạng consistent với pipeline trước
            parsed_model = TOOL_NAME_TO_MODEL[tool_name](**params)
            return {"tool_calls": [parsed_model], "clarification": None, "raw": dispatch_res["result"]}
        else:
            return {"tool_calls": [], "clarification": None, "error": dispatch_res.get("error"), "raw": None}
    except Exception as e:
        logger_task.exception(f"❌ Exception in thuc_thi_cong_cu: {e}")
        return {"tool_calls": [], "clarification": None, "error": str(e), "raw": None}

# -----------------------
# Task lấy danh sách tool
# -----------------------
@task(name="lay-danh-sach-cong-cu")
def lay_danh_sach_cong_cu() -> Dict[str, str]:
    return {
        "tim_kiem_thong_tin": "Tìm kiếm thông tin trên internet",
        "tinh_toan": "Thực hiện các phép tính toán cơ bản",
        "thoi_tiet": "Xem thông tin thời tiết",
        "chuyen_doi_tien_te": "Chuyển đổi tiền tệ",
    }

def get_available_tools() -> Dict[str, str]:
    """
    Lấy danh sách các công cụ có sẵn và mô tả của chúng.
    
    Returns:
        Dict với key là tên công cụ và value là mô tả
    """
    return {
        "tim_kiem_thong_tin": "Tìm kiếm thông tin trên internet",
        "tinh_toan": "Thực hiện các phép tính toán cơ bản",
        "thoi_tiet": "Xem thông tin thời tiết",
        "chuyen_doi_tien_te": "Chuyển đổi tiền tệ",
    }

# -----------------------
# 3️⃣ Tool Execution
# -----------------------
@task(name="execute-tool")
async def execute_tool(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Thực thi một công cụ với các tham số đầu vào.
    
    Args:
        input_data: Dữ liệu đầu vào chứa tên công cụ và các tham số
            Ví dụ: {"tool_name": "ThoiTiet", "params": {"thanh_pho": "Đà Nẵng"}}
            
    Returns:
        Dict chứa kết quả thực thi công cụ
    """
    logger_task = get_run_logger()
    try:
        tool_name = input_data.get("tool_name")
        params = input_data.get("params", {}) or {}
        logger_task.info(f"⚙️ Dispatching tool {tool_name} with params: {params}")

        dispatch_res = await dispatch_tool_call(tool_name, params)
        if dispatch_res.get("ok"):
            # Return in a format compatible with the existing code
            return {
                "tool_calls": [{"name": tool_name, "args": params}],
                "clarification": None,
                "error": None,
                "raw": dispatch_res.get("result", {})
            }
        else:
            return {
                "tool_calls": [],
                "clarification": None,
                "error": dispatch_res.get("error", "Unknown error"),
                "raw": None
            }
    except Exception as e:
        logger_task.exception(f"❌ Error in execute_tool: {e}")
        return {
            "tool_calls": [],
            "clarification": None,
            "error": str(e),
            "raw": None
        }

# -----------------------
# 4️⃣ Tạo Agent
# -----------------------
agent_executor = create_react_agent(llm, TOOLS)  # agent tự bind tools

# -----------------------
# 5️⃣ Chạy agent (agent_chat)
# - Lấy tool_calls từ AIMessage, parse bằng parser.invoke(ai_msg),
# - Dispatch từng tool_call qua dispatch_tool_call
# - GỬI kết quả tool cho LLM để LLM tổng hợp reply người dùng (Tiếng Việt)
# -----------------------
@task(name="process_with_agent")
async def process_with_agent(query: str) -> Dict[str, Any]:
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
                "user_query": query,
                "tool_results": tool_results,
            }
            synth_prompt = (
                "Bạn là trợ lý hữu ích. Dưới đây là truy vấn của người dùng và kết quả từ các công cụ thực thi.\n\n"
                f"Truy vấn: {query}\n\n"
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
