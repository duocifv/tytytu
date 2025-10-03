# nodes/content_and_facebook_node/node_content.py
import traceback
from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from brain.notion_logger import get_hexagram_log
from services.llm_service import llm
from services.rag_service import RAGRetriever

class ContentOutput(BaseModel):
    fb_title: str
    fb_description: str
    image_prompt: str
    daily_stoic: str
    quote_author: str
    poster_tone: str

def safe_parse(parser, text: str):
    try:
        return parser.parse(text)
    except Exception:
        traceback.print_exc()
        return ContentOutput(
            fb_title="Fallback Title",
            fb_description="Fallback description",
            image_prompt="city street rainy",
            daily_stoic="Fallback stoic",
            quote_author="Unknown",
            poster_tone="neutral"
        )

def extract_simple_notion(notion_raw: dict, keys=None):
    """Rút gọn dữ liệu từ Notion"""
    if keys is None:
        keys = ["Nhan", "Dia", "Thien", "Summary", "KeyEvent", "Health", "Work",
                "Effect", "Trend", "Finance", "Psychology", "Family", "Spiritual", "Community" ]
    simple = {}
    try:
        props = notion_raw.get("properties", {})
        for k in keys:
            v = props.get(k)
            if not v:
                continue
            rich_text = v.get("rich_text", [])
            if rich_text and isinstance(rich_text, list):
                simple[k] = " ".join(rt.get("plain_text", "") for rt in rich_text).strip()
    except Exception as e:
        print(e)
    return simple

def build_content_and_insights():
    """
    Trả về: notion_data, insight_text, rag_info, parser (PydanticOutputParser)
    """
    notion_raw = get_hexagram_log()
    notion_data = extract_simple_notion(notion_raw)
    if not notion_data:
        notion_data = {"Summary": "Không có dữ liệu hôm nay"}
    notion_data_str = str(notion_data)
    parser = PydanticOutputParser(pydantic_object=ContentOutput)

    # Tier 1: Phân tích dữ liệu
    p_analysis = ChatPromptTemplate.from_messages([
        ("system", "Bạn là chuyên gia phân tích dữ liệu cộng đồng."),
        ("user",
         "Dữ liệu JSON từ Notion: {notion_data}\n"
         "Hãy phân tích và rút ra các insight chính:\n"
         "- Tình hình thiên tai, dịch bệnh, kinh tế, tâm lý\n"
         "- Tác động đến sức khỏe, công việc, đời sống gia đình\n"
         "- Gợi ý cách ứng phó, chăm sóc sức khoẻ và tinh thần\n"
         "Trả về văn bản súc tích, dễ hiểu.")
    ]).partial(notion_data=notion_data_str)
    prompt_analysis = p_analysis.format(notion_data=notion_data_str)
    insight_text = getattr(llm.invoke(prompt_analysis), "content", "")

    # RAG
    rag = RAGRetriever(sources=["VNExpress", "Khí tượng Thủy văn", "WHO"])
    rag_info = rag.retrieve(notion_data)
    if isinstance(rag_info, dict):
        rag_info = str(rag_info)

    return notion_data, insight_text, rag_info, parser
