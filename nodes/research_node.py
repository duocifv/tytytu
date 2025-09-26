# nodes/research_node.py
from langchain_core.messages import HumanMessage
from pydantic import BaseModel
from langchain.output_parsers import PydanticOutputParser
from services.groq_service import chat_groq  # Groq GPT
from langchain_community.document_loaders import WebBaseLoader
from typing import List, Dict

# -----------------------------
# 1️⃣ Model JSON chuẩn
# -----------------------------
class ResearchOutput(BaseModel):
    sources: List[Dict[str, str]]  # {"title": str, "url": str}
    insights: List[str]

# -----------------------------
# 2️⃣ Node research đơn giản kiểu title_node
# -----------------------------
def research_node(state):
    topic = state.get("topic", "Demo topic")

    # Load trang web tham khảo
    url = "https://vnexpress.net/suc-khoe"
    loader = WebBaseLoader(url)
    docs = loader.load()
    doc_text = "\n\n".join([d.page_content for d in docs])

    # Parser JSON
    parser = PydanticOutputParser(pydantic_object=ResearchOutput)

    # Tối giản prompt nhúng state
    safe_state = {k: ("..." if k == "messages" else v) for k, v in state.items()}
    prompt = (
        f"Dữ liệu state: {safe_state}\n\n"
        f"Chủ đề: {topic}\n\n"
        f"Nội dung tham khảo từ {url}:\n{doc_text}\n\n"
        "Hãy trích xuất:\n"
        "- Danh sách nguồn tham khảo (title + url)\n"
        "- Các insight chính liên quan đến chủ đề\n\n"
        f"Trả về JSON đúng format:\n{parser.get_format_instructions()}"
    )

    # Gọi Groq GPT, trả về string JSON
    raw_result = chat_groq(prompt)
    print("📌 raw_result from Groq:", raw_result)

    # Parse an toàn
    try:
        result = parser.parse(raw_result)
    except Exception as e:
        result = ResearchOutput(
            sources=[{"title": "Fallback source", "url": ""}],
            insights=["Fallback insight"]
        )

    msg = HumanMessage(content=f"research_node completed for topic '{topic}'")
    return {
        "status": "done",
        "messages": [msg],
        "outputs": result
    }
