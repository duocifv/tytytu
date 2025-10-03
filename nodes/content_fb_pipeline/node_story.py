# nodes/content_and_facebook_node/node_story.py
import os
import uuid
import traceback
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel
from .content import build_content_and_insights, safe_parse
from .publish import post_media
from services.llm_service import llm
from services.facebook_service import FacebookPipeline

class StoryOutput(BaseModel):
    fb_title: str
    story_text: str
    lesson: str

def node_story(state: dict):
    msg_list = []
    fb_success = False

    # 1️⃣ Build content (Notion, insight, RAG)
    notion_data, insight_text, rag_info, parser = build_content_and_insights()
    
    parser = PydanticOutputParser(pydantic_object=StoryOutput)

    p_story = ChatPromptTemplate.from_messages([
        ("system", "Bạn là người kể chuyện cho mạng xã hội."),
        ("user", """
        Dựa vào insight từ bước phân tích: {insight}
        Và dữ liệu thực tế từ RAG: {rag_info}
         
        Hãy viết một mini story ngắn gọn (100–150 từ), có bài học rút ra.
        Phong cách: đời thường, dễ hiểu, cảm xúc nhẹ nhàng.

        JSON gồm:
        - fb_title
        - story_text
        - lesson
        {parser_instructions}
        """)
    ]).partial(parser_instructions=parser.get_format_instructions())

    llm_output = llm.invoke(p_story.format(insight=insight_text, rag_info=rag_info))
    content_obj = safe_parse(parser, getattr(llm_output, "content", str(llm_output)))
    print("📌 Story JSON:", content_obj)

    # Đăng FB
    # pipeline = FacebookPipeline()
    # fb_success = post_media(
    #     pipeline,
    #     fb_title=content_obj.fb_title,
    #     fb_description=f"{content_obj.story_text}\n\n👉 Bài học: {content_obj.lesson}"
    # )
    # msg_list.append(HumanMessage(content=f"Facebook: {'✅ Published' if fb_success else '❌ Failed'}"))

    # return {"status": "done", "messages": msg_list, "published": fb_success}
