# nodes/content_and_facebook_node/node_quote.py
import os
import uuid
import traceback
from io import BytesIO
from PIL import Image as PILImage
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser

from .content import build_content_and_insights, safe_parse
from .media import generate_image_from_prompt
from .publish import post_media, cleanup_files
from services.llm_service import llm
from services.facebook_service import FacebookPipeline

from pydantic import BaseModel

TEMP_DIR = "generated_images"
os.makedirs(TEMP_DIR, exist_ok=True)

class QuoteOutput(BaseModel):
    fb_title: str
    daily_quote: str
    quote_author: str
    image_prompt: str

def node_quote(state: dict):
    msg_list = []
    fb_success = False
    temp_image_path = None

    # 1️⃣ Build content (Notion, insight, RAG)
    notion_data, insight_text, rag_info, parser = build_content_and_insights()
    
    parser = PydanticOutputParser(pydantic_object=QuoteOutput)

    p_quote = ChatPromptTemplate.from_messages([
        ("system", "Bạn là một nhà thiết kế Quote cho mạng xã hội."),
        ("user", """
         
        Dựa vào insight từ bước phân tích: {insight}
        Và dữ liệu thực tế từ RAG: {rag_info}
         
        Hãy tạo một quote ngắn (20–40 từ), có tác giả (hoặc ghi 'Unknown'),
        và một prompt ảnh nền đơn giản (phong cách tối giản).

        Đầu ra JSON với 4 trường:
        - fb_title
        - daily_quote
        - quote_author
        - image_prompt
        {parser_instructions}
        """)
    ]).partial(parser_instructions=parser.get_format_instructions())

    llm_output = llm.invoke(p_quote.format(insight=insight_text, rag_info=rag_info))
    content_obj = safe_parse(parser, getattr(llm_output, "content", str(llm_output)))
    print("📌 Quote JSON:", content_obj)

    # # Tạo ảnh
    # if content_obj.image_prompt:
    #     pil_img = generate_image_from_prompt(content_obj.image_prompt)
    #     if pil_img:
    #         temp_image_path = os.path.join(TEMP_DIR, f"q_{uuid.uuid4().hex[:4]}.jpg")
    #         try:
    #             pil_img.save(temp_image_path, format="JPEG", quality=95)
    #         except Exception:
    #             traceback.print_exc()
    #             temp_image_path = None
    #     msg_list.append(HumanMessage(content="✅ Quote image created"))

    # # Đăng Facebook
    # if temp_image_path:
    #     pipeline = FacebookPipeline()
    #     fb_success = post_media(
    #         pipeline,
    #         image_path=temp_image_path,
    #         fb_title=content_obj.fb_title,
    #         fb_description=content_obj.daily_quote
    #     )
    #     msg_list.append(HumanMessage(content=f"Facebook: {'✅ Published' if fb_success else '❌ Failed'}"))

    # cleanup_files([temp_image_path])
    # return {"status": "done", "messages": msg_list, "published": fb_success}
