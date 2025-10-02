# nodes/human_reference_node_multi.py
from langchain_core.messages import HumanMessage
from pydantic import BaseModel
from langchain.output_parsers import PydanticOutputParser
from services.groq_service import chat_groq
from typing import Dict, Any

# -----------------------------
# 1️⃣ Model JSON chuẩn cho output mỗi chuyên gia
# -----------------------------
class ExpertOutput(BaseModel):
    health: str
    finance: str
    psychology: str
    work: str
    trend: str
    family: str
    spiritual: str
    community: str

# -----------------------------
# 2️⃣ Định nghĩa 8 chuyên gia với tên và chuyên môn
# -----------------------------
EXPERTS = [
    {"name": "Expert_Health", "field": "Sức khỏe", "key": "health"},
    {"name": "Expert_Finance", "field": "Tài chính", "key": "finance"},
    {"name": "Expert_Psychology", "field": "Tâm lý", "key": "psychology"},
    {"name": "Expert_Work", "field": "Công việc", "key": "work"},
    {"name": "Expert_Trend", "field": "Xu hướng / Thời sự", "key": "trend"},
    {"name": "Expert_Family", "field": "Gia đình / Quan hệ", "key": "family"},
    {"name": "Expert_Spiritual", "field": "Tinh thần / Triết lý", "key": "spiritual"},
    {"name": "Expert_Community", "field": "Cộng đồng / Xã hội", "key": "community"},
]

# -----------------------------
# 3️⃣ Node AI đa chuyên gia (trả về 1 JSON duy nhất)
# -----------------------------
def human_reference_node(state: Dict[str, Any]):
    record = state.get("daily", {})
    input_data = record.get("input", {})
    base_qua = record.get("base", {})
    transformed_qua = record.get("transformed", {})
    llm_summary = record.get("llm_summary", "")

    final_result = {
        "health": "",
        "finance": "",
        "psychology": "",
        "work": "",
        "trend": "",
        "family": "",
        "spiritual": "",
        "community": ""
    }

    for expert in EXPERTS:
        parser = PydanticOutputParser(pydantic_object=ExpertOutput)

        prompt = (
            f"Bạn là chuyên gia về lĩnh vực: {expert['field']}\n"
            f"Dữ liệu đầu vào:\n"
            f"- Thiên: {input_data.get('Thien','')}\n"
            f"- Địa: {input_data.get('Dia','')}\n"
            f"- Nhân: {input_data.get('Nhan','')}\n"
            f"- Sự kiện nổi bật: {input_data.get('KeyEvent','')}\n"
            f"- Tóm tắt LLM: {llm_summary}\n"
            f"- Quẻ gốc: {base_qua.get('name','')}, bitstring: {base_qua.get('bitstring','')}\n"
            f"- Quẻ biến: {transformed_qua.get('name','')}, bitstring: {transformed_qua.get('bitstring','')}\n"
            f"- Quan hệ quẻ: Opposite, Transform, Ally, Support\n\n"
            f"Hãy phân tích chuyên sâu lĩnh vực của bạn và trả về JSON đúng format:\n{parser.get_format_instructions()}"
        )

        raw_result = chat_groq(prompt)

        try:
            result = parser.parse(raw_result)
        except Exception:
            result = ExpertOutput(
                health="Fallback",
                finance="Fallback",
                psychology="Fallback",
                work="Fallback",
                trend="Fallback",
                family="Fallback",
                spiritual="Fallback",
                community="Fallback"
            )

        # Gán nội dung chuyên môn chính vào JSON cuối cùng
        key = expert["key"]
        final_result[key] = getattr(result, key)

    print("📌 3 - human_reference_node_multi - ok", final_result)
    msg = HumanMessage(content="human_reference_node_multi completed")

    return {
        "status": "done",
        "messages": [msg],
        "daily": final_result  # JSON duy nhất 8 key
    }
