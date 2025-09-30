# nodes/human_reference_node.py
from langchain_core.messages import HumanMessage
from pydantic import BaseModel
from langchain.output_parsers import PydanticOutputParser
from services.groq_service import chat_groq  # Hoặc openai.ChatCompletion nếu dùng GPT-4
from typing import Dict, Any, List

# -----------------------------
# 1️⃣ Model JSON chuẩn cho output
# -----------------------------
class HumanReferenceOutput(BaseModel):
    health: str
    finance: str
    psychology: str
    work: str
    trend: str
    note: str

# -----------------------------
# 2️⃣ Node AI tham chiếu quẻ
# -----------------------------
def human_reference_node(state):

    record = state.get("daily", {})

    # Nhúng dữ liệu đầu vào
    input_data = record.get("input", {})
    base_qua = record.get("base", {})
    transformed_qua = record.get("transformed", {})
    llm_summary = record.get("llm_summary", "")

    parser = PydanticOutputParser(pydantic_object=HumanReferenceOutput)
    
    # Prompt tối giản
    prompt = (
        f"Dữ liệu đầu vào:\n"
        f"- Thiên: {input_data.get('Thien','')}\n"
        f"- Địa: {input_data.get('Dia','')}\n"
        f"- Nhân: {input_data.get('Nhan','')}\n"
        f"- Sự kiện nổi bật: {input_data.get('KeyEvent','')}\n"
        f"- Tóm tắt LLM: {llm_summary}\n"
        f"- Quẻ gốc: {base_qua.get('name','')}, bitstring: {base_qua.get('bitstring','')}\n"
        f"- Quẻ biến: {transformed_qua.get('name','')}, bitstring: {transformed_qua.get('bitstring','')}\n"
        f"- Quan hệ quẻ: Opposite, Transform, Ally, Support\n\n"
        "Hãy phân tích:\n"
        "1. Dịch quẻ sang 4 lĩnh vực đời sống con người: Sức khỏe, Tài chính, Tâm lý, Công việc.\n"
        "2. Phân tích tác động gián tiếp và xu hướng theo từng lĩnh vực.\n"
        "3. Liên kết đặc tính biến hóa quẻ (Opposite, Transform, Ally, Support) để dự đoán trạng thái vạn vật.\n\n"
        f"Trả về JSON đúng format:\n{parser.get_format_instructions()}"
    )

    # Gọi AI (Groq GPT hoặc OpenAI GPT)
    raw_result = chat_groq(prompt)  # Hoặc openai_call(prompt)

    # Parse an toàn
    try:
        result = parser.parse(raw_result)
    except Exception:
        result = HumanReferenceOutput(
            health="Fallback",
            finance="Fallback",
            psychology="Fallback",
            work="Fallback",
            trend="Fallback",
            note="AI trả về không đúng JSON"
        )
    print("📌 3 - human_reference_node - ok")
    msg = HumanMessage(content="human_reference_node completed")
    return {
        "status": "done",
        "messages": [msg],  
        "daily": result
    }
