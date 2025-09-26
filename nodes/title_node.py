# nodes/title_node.py
from langchain_core.messages import HumanMessage
from pydantic import BaseModel
from langchain.output_parsers import PydanticOutputParser
from services.groq_service import chat_groq  # hàm gọi Groq GPT-OSS-120B

# -----------------------------
# 1️⃣ Model chuẩn để parse JSON
# -----------------------------
class TitleOutput(BaseModel):
    text: str
    description: str

# -----------------------------
# 2️⃣ Node tạo title & meta description
# -----------------------------
def title_node(state):
    topic = state.get("topic", "Demo")
    outputs = state.get("outputs", {})
    ideas = outputs.get("ideas", []) if isinstance(outputs, dict) else []

    parser = PydanticOutputParser(pydantic_object=TitleOutput)

    # Tối giản prompt, nhúng state nhưng ẩn messages
    safe_state = {k: ("..." if k == "messages" else v) for k, v in state.items()}
    prompt = (
        f"Dữ liệu state: {safe_state}\n\n"
        f"Chủ đề: {topic}\n"
        f"Ý tưởng tham khảo: {', '.join(ideas) if ideas else 'Không có'}\n\n"
        "Hãy tạo một tiêu đề blog ngắn gọn, thu hút (≤ 60 ký tự) "
        "và một meta description chuẩn SEO (≤ 160 ký tự).\n"
        f"Trả về đúng JSON theo format:\n{parser.get_format_instructions()}"
    )

    # Gọi Groq, luôn trả về string
    raw_result = chat_groq(prompt)
    print("📌 raw_result from Groq:", raw_result)

    try:
        result = parser.parse(raw_result)
    except Exception as e:
        result = TitleOutput(
            text="Fallback Title",
            description=f"Lỗi parse JSON: {e}"
        )

    msg = HumanMessage(content=f"title_node blog cho chủ đề '{topic}'")
    return {
        "status": "done",
        "messages": [msg],
        "outputs": result
    }
