from langchain_core.messages import HumanMessage
from tools2.content_length_tool import content_length_tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from services.llm_service import llm  # Gemini instance

def content_node(state):
    """
    Node 4: Quản trị Thương hiệu
    - Kiểm tra tone, hình ảnh
    - Đối chiếu guideline
    - Duyệt ý tưởng ban đầu
    """

    title = state["status"].get("node_data", {}).get("title", {}).get("title", "Demo Title")
    draft_content = f"This is the content of the blog titled '{title}'. It explains everything about {title}."

    # 1️⃣ Prompt templates
    p1 = ChatPromptTemplate.from_messages([
        ("system", "Bạn là An - chuyên viên biên tập."),
        ("user", "Đưa ra 3 ý tưởng blog mới về chủ đề: {topic}. Quy định: Ý tưởng ≤ 20 từ, Liên quan đến {topic}")
    ])

    p2 = ChatPromptTemplate.from_messages([
        ("system", "Bạn là An - chuyên viên biên tập."),
        ("user", "Bạn vừa nghĩ ra các ý tưởng: {step1_ideas}. Chọn ý tưởng hay nhất và viết tiêu đề hấp dẫn. Quy định: Tiêu đề ≤ 12 từ, Có từ khóa chính, Không clickbait quá đà")
    ])

    p3 = ChatPromptTemplate.from_template(
        "Dựa trên đối chiếu guideline: {step2_guideline}, duyệt ý tưởng ban đầu và tổng hợp kết quả."
    )

    # 2️⃣ Chain
    chain3 = (
        p1 | llm
        | RunnableLambda(lambda x: {"step1_ideas": x.content})
        | p2 | llm
        | RunnableLambda(lambda x: {"step2_guideline": x.content})
        | p3 | llm
    )

    # 3️⃣ Invoke
    final_result = chain3.invoke({"topic": title})

    # 4️⃣ Tính độ dài content
    length = content_length_tool.invoke({"text": draft_content})

    msg = HumanMessage(content=f"Generated content length = {length}")

    return {
        "status": "done",
        "messages": [msg],
        "content": final_result.content,
        "length": length
    }
