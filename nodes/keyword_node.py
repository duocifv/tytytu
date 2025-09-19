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

    # 2️⃣ Lấy dữ liệu từ SEO pipeline
    pipeline = SEOContentPipeline()
    seo_data = pipeline.run(topic)
    seo_keywords = seo_data.get("seo_keywords", [])
    competitors = seo_data.get("competitor_titles", [])

    # 3️⃣ Parser JSON
    parser = PydanticOutputParser(pydantic_object=KeywordOutput)

    # 4️⃣ Prompt templates
    p1 = ChatPromptTemplate.from_messages([
        ("system", "Bạn là Neil Patel, chuyên gia SEO. Phong cách trực tiếp, dữ liệu-driven."),
        ("user",
         "Viết 3 ý tưởng blog mới cho chủ đề: {topic}, từ khóa: {seo_keywords}, tiêu đề đối thủ: {competitors}. "
         "Ý tưởng ≤20 từ. Trả về JSON với keys: ideas, selected_title, meta_description.")
    ])

    # 5️⃣ Chain: Prompt → LLM → Parse JSON
    chain = (
        p1 | llm
        | RunnableLambda(lambda x: parser.parse(x.content))  # parse JSON trực tiếp
    )

    # 6️⃣ Invoke chain
    final_result = chain.invoke({
        "topic": topic,
        "seo_keywords": ", ".join(seo_keywords) if seo_keywords else "Không có",
        "competitors": ", ".join(competitors) if competitors else "Không có"
    })

    msg = HumanMessage(content=f"Generated ideas & title for topic '{topic}'")

    # 7️⃣ Trả về JSON chuẩn, dễ lưu Notion
    return {
        "status": "done",
        "messages": [msg],
        "keywords": {
            "seo_keywords": seo_keywords,
            "competitors": competitors,
            **final_result.model_dump()  # ideas, selected_title, meta_description
        }
    }
