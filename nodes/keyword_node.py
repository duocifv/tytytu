from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel
from services.llm_service import llm
from services.seo_service import SEOContentPipeline
from typing import List

# -----------------------------
# 1️⃣ Định nghĩa model JSON chuẩn
# -----------------------------
class KeywordOutput(BaseModel):
    ideas: List[str]
    keywords: List[str]

# -----------------------------
# Helper parse an toàn
# -----------------------------
def safe_parse(parser, text: str):
    try:
        return parser.parse(text)
    except Exception as e:
        return KeywordOutput(
            ideas=["Fallback idea 1", "Fallback idea 2", "Fallback idea 3"],
            keywords=["Fallback keyword"]
        )

# -----------------------------
# Node keyword
# -----------------------------
def keyword_node(state):
    topic = state.get("topic", "Demo topic")

    # 2️⃣ Lấy dữ liệu SEO
    pipeline = SEOContentPipeline()
    seo_data = pipeline.run(topic)
    print(seo_data)
    seo_keywords = seo_data.get("seo_keywords", [])
    competitors = seo_data.get("competitor_titles", [])

    # 3️⃣ Parser JSON
    parser = PydanticOutputParser(pydantic_object=KeywordOutput)

    # 4️⃣ Prompt phân tích nhu cầu + vấn đề user
    p_analysis = ChatPromptTemplate.from_messages([
        ("system", "Bạn là chuyên gia SEO, nhiệm vụ là phân tích nhu cầu người dùng."),
        ("user",
         "Dựa vào 8 tiêu đề cạnh tranh sau đây:\n{competitors}\n\n"
         "Hãy xác định:\n"
         "- Các nhu cầu chính của người dùng\n"
         "- Các mối quan tâm nổi bật\n"
         "- Những vấn đề họ đang gặp phải\n"
         "Sau đó chọn ra 3 ý tưởng nội dung blog (≤20 từ) "
         "và các từ khóa SEO liên quan.\n"
         "Trả về JSON.\n{format_instructions}")
    ]).partial(format_instructions=parser.get_format_instructions())

    # 5️⃣ Prompt Kinh Dịch diễn giải
    p_i_ching = ChatPromptTemplate.from_messages([
        ("system", "Bạn là bậc thầy Kinh Dịch, chuyên dùng quẻ để soi chiếu nhu cầu con người."),
        ("user",
         "Dựa vào nhu cầu & vấn đề đã phân tích từ tiêu đề đối thủ:\n{competitors}\n\n"
         "Hãy diễn giải theo Kinh Dịch:\n"
         "- Ý nghĩa sâu xa\n"
         "- Lời khuyên định hướng\n"
         "- Cách cân bằng sức khỏe, đời sống\n\n"
         "Kết quả trả về JSON.\n{format_instructions}")
    ]).partial(format_instructions=parser.get_format_instructions())

    # 6️⃣ Chain
    chain = (
        p_analysis
        | llm
        | RunnableLambda(lambda x: safe_parse(parser, x.content))
        | p_i_ching
        | llm
        | RunnableLambda(lambda x: safe_parse(parser, x.content))
    )

    # 7️⃣ Run chain
    result = chain.invoke({
        "topic": topic,
        "competitors": ", ".join(competitors) if competitors else "Không có"
    })

    msg = HumanMessage(content=f"Generated ideas & I-Ching interpretation for topic '{topic}'")
    return {
        "status": "done",
        "messages": [msg],
        "outputs": result
    }
