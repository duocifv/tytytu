from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel
from services.llm_service import llm
from services.seo_service import SEOContentPipeline


# 1️⃣ Định nghĩa model JSON chuẩn
class KeywordOutput(BaseModel):
    ideas: list[str]
    selected_title: str
    meta_description: str


def keyword_node(state):
    topic = state.get("topic", "Demo topic")
    # # 2️⃣ Lấy dữ liệu SEO
    # pipeline = SEOContentPipeline()
    # seo_data = pipeline.run(topic)
    # seo_keywords = seo_data.get("seo_keywords", [])
    # competitors = seo_data.get("competitor_titles", [])

    # # 3️⃣ Parser JSON
    # parser = PydanticOutputParser(pydantic_object=KeywordOutput)

    # # 4️⃣ Prompt template (ép format chuẩn)
    # p1 = ChatPromptTemplate.from_messages([
    #     ("system", "Bạn là Neil Patel, chuyên gia SEO. Phong cách trực tiếp, dữ liệu-driven."),
    #     ("user",
    #      "Viết 3 ý tưởng blog mới cho chủ đề: {topic}, "
    #      "từ khóa: {seo_keywords}, tiêu đề đối thủ: {competitors}. "
    #      "Ý tưởng ≤20 từ. Trả về JSON.\n{format_instructions}")
    # ]).partial(format_instructions=parser.get_format_instructions())

    # # 5️⃣ Chain
    # chain = (
    #     p1 | llm
    #     | RunnableLambda(lambda x: safe_parse(parser, x.content))
    # )

    # # 6️⃣ Run chain
    # result = chain.invoke({
    #     "topic": topic,
    #     "seo_keywords": ", ".join(seo_keywords) if seo_keywords else "Không có",
    #     "competitors": ", ".join(competitors) if competitors else "Không có"
    # })

    result =  {
        "keywords": ["du lịch Đà Lạt", "ẩm thực Đà Lạt", "check-in cảnh đẹp"],
        "intent": "Tìm hiểu trải nghiệm du lịch Đà Lạt"
    }
    msg = HumanMessage(content=f"Generated ideas & title for topic '{topic}'")
    return {
        "status": "done",
        "messages": [msg],
        "outputs": result   # ✅ dữ liệu của node luôn nằm ở đây
    }


# Helper: parse an toàn
def safe_parse(parser, text: str):
    try:
        return parser.parse(text)
    except Exception as e:
        return KeywordOutput(
            ideas=["Fallback idea 1", "Fallback idea 2", "Fallback idea 3"],
            selected_title="Fallback Title",
            meta_description=f"Lỗi parse JSON: {e}"
        )
