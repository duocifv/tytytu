from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from pydantic import BaseModel
from langchain.output_parsers import PydanticOutputParser
from services.llm_service import llm  # hoặc Groq wrapper
from typing import List

# 1️⃣ Model JSON chuẩn
class ContentOutput(BaseModel):
    body: str
    excerpt: str
    tags: List[str]

# 2️⃣ Helper parse an toàn
def safe_parse(parser, text: str):
    try:
        return parser.parse(text)
    except Exception as e:
        return ContentOutput(
            body="Fallback content body",
            excerpt="Fallback excerpt",
            tags=["Fallback"]
        )

# 3️⃣ Node content tối giản
def content_node(state):
    topic = state.get("topic", "Demo topic")
    outputs = state.get("outputs", {})
    ideas = outputs.get("ideas", [])
    title = outputs.get("selected_title", "")
    meta_description = outputs.get("meta_description", "")

    parser = PydanticOutputParser(pydantic_object=ContentOutput)

    # Prompt tạo content
    prompt_text = (
        f"Chủ đề: {topic}\n"
        f"Tiêu đề: {title}\n"
        f"Meta description: {meta_description}\n"
        f"Ý tưởng:\n- " + "\n- ".join(ideas) + "\n\n"
        "Hãy viết nội dung blog đầy đủ, chuẩn SEO, kết hợp diễn giải theo Kinh Dịch:\n"
        "- Ý nghĩa sâu xa của từng ý tưởng\n"
        "- Lời khuyên định hướng\n"
        "- Cách cân bằng sức khỏe và đời sống\n\n"
        "Trả về JSON theo format:\n"
        f"{parser.get_format_instructions()}"
    )


    # Lấy output từ LLM
    llm_output = llm.invoke(prompt_text)
    raw_result = llm_output.content if hasattr(llm_output, "content") else str(llm_output)

    # Parse JSON an toàn
    result = safe_parse(parser, raw_result)

    msg = HumanMessage(content=f"content_node blog cho chủ đề '{topic}'")
    return {
        "status": "done",
        "messages": [msg],
        "outputs": result
    }
