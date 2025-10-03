# nodes/content_and_facebook_node/node_reels.py
import os
import uuid
import traceback
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel
from .content import build_content_and_insights, safe_parse
from .media import generate_image_from_prompt
from .publish import post_media, cleanup_files
from services.generate_video_service import generate_video
from services.llm_service import llm
from services.facebook_service import FacebookPipeline

TEMP_DIR = "generated_reels"
os.makedirs(TEMP_DIR, exist_ok=True)

class ReelsOutput(BaseModel):
    fb_title: str
    fb_description: str
    image_prompt: str

def node_reels(state: dict):
    msg_list = []
    fb_success = False
    temp_image_path = None
    temp_video_path = None

    # 1️⃣ Build content (Notion, insight, RAG)
    notion_data, insight_text, rag_info, parser = build_content_and_insights()
    
    parser = PydanticOutputParser(pydantic_object=ReelsOutput)

    p_reels = ChatPromptTemplate.from_messages([
        ("system", "Bạn là biên tập viên Reels Facebook."),
        ("user", """
         
        Dựa vào insight từ bước phân tích: {insight}
        Và dữ liệu thực tế từ RAG: {rag_info}
         
        Hãy viết một mẹo ngắn (sức khoẻ / kỹ năng / fact thú vị) dạng Reels 30–45s.
        Output JSON:
        - fb_title
        - fb_description (script text)
        - image_prompt (ảnh nền video)
        {parser_instructions}
        """)
    ]).partial(parser_instructions=parser.get_format_instructions())

    llm_output = llm.invoke(p_reels.format(insight=insight_text, rag_info=rag_info))
    content_obj = safe_parse(parser, getattr(llm_output, "content", str(llm_output)))
    print("📌 Reels JSON:", content_obj)

    # # Tạo ảnh nền
    # if content_obj.image_prompt:
    #     pil_img = generate_image_from_prompt(content_obj.image_prompt)
    #     if pil_img:
    #         temp_image_path = os.path.join(TEMP_DIR, f"r_{uuid.uuid4().hex[:4]}.jpg")
    #         try:
    #             pil_img.save(temp_image_path, format="JPEG", quality=95)
    #         except Exception:
    #             traceback.print_exc()
    #             temp_image_path = None

    # # Render video
    # if temp_image_path:
    #     temp_video_path = os.path.join(TEMP_DIR, f"r_{uuid.uuid4().hex[:4]}.mp4")
    #     try:
    #         generate_video(
    #             temp_image_path,
    #             content_obj.fb_description,
    #             None,
    #             output=temp_video_path,
    #             size=(720,1280),
    #             total_frames=300,
    #             fps=30
    #         )
    #     except Exception:
    #         traceback.print_exc()
    #         temp_video_path = None

    # # Đăng FB
    # if temp_video_path:
    #     pipeline = FacebookPipeline()
    #     fb_success = post_media(
    #         pipeline,
    #         video_path=temp_video_path,
    #         fb_title=content_obj.fb_title,
    #         fb_description=content_obj.fb_description
    #     )
    #     msg_list.append(HumanMessage(content=f"Facebook: {'✅ Published' if fb_success else '❌ Failed'}"))

    # cleanup_files([temp_image_path, temp_video_path])
    # return {"status": "done", "messages": msg_list, "published": fb_success}
