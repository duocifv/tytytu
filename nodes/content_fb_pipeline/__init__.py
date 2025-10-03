# nodes/content_and_facebook_node/__init__.py
import os
import uuid
import traceback
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel
from io import BytesIO
from PIL import Image as PILImage

from .content import build_content_and_insights, ContentOutput, safe_parse
from .media import generate_image_from_prompt
from .publish import post_media, cleanup_files
from services.generate_video_service import generate_video
from services.llm_service import llm
from services.facebook_service import FacebookPipeline

# Thư mục tạm (giữ y nguyên)
TEMP_DIR = "generated_images"
os.makedirs(TEMP_DIR, exist_ok=True)

def content_and_facebook_node(state: dict):
    # copy nguyên flow từ file gốc — phần lớn code giống hệt, chỉ gọi helper
    msg_list = []
    fb_success = False
    temp_image_path = None
    temp_video_path = None

    # 1️⃣ Build content (Notion, insight, RAG)
    notion_data, insight_text, rag_info, parser = build_content_and_insights()
    print("✅ Dữ liệu rút gọn từ Notion:", notion_data)

    notion_data_str = str(notion_data)
    # parser = PydanticOutputParser(pydantic_object=ContentOutput)  # parser đã từ node_content, nhưng giữ tương thích
    parser = PydanticOutputParser(pydantic_object=ContentOutput)

    # 4️⃣ Tier 2: Viết content dựa trên insight + RAG
    parser_instructions = parser.get_format_instructions()
    p_content = ChatPromptTemplate.from_messages([
        ("system", "Bạn là biên tập viên mạng xã hội, viết status Facebook đời thường, gần gũi."),
        ("user",
        """
            Dựa vào insight từ bước phân tích: {insight}
            Và dữ liệu thực tế từ RAG: {rag_info}

            Hãy viết thành một status Facebook đời thường, gần gũi và hữu ích, như một người bạn đang trò chuyện với cộng đồng.

            Yêu cầu:
            - Mở đầu: vẽ một hình ảnh cụ thể từ đời sống (quán cà phê vắng khách, trẻ nhỏ ho, xe chết máy giữa mưa…)
            - Thân bài:
            + Đời thường + tri thức: lồng ghép ảnh hưởng thực tế từ dữ liệu.
            + Lời khuyên cụ thể, dễ làm: chăm sóc sức khoẻ, an toàn, sinh hoạt.
            + Góc cộng đồng: nhắc đến sự chia sẻ, giúp đỡ nhau.
            - Kết: giọng văn ấm áp, dí dỏm, nhẹ nhàng như dặn dò người thân.
            - Daily Stoic: thêm một câu triết lý ngắn gọn, truyền năng lượng tích cực.
            - Độ dài: 150–250 từ.
            - Phong cách: thân mật, gợi cảm xúc, cân bằng giữa lo lắng và hy vọng.
            - Có thể thêm 1 hashtag cuối.
            - Không dùng ngôn ngữ học thuật, không liệt kê khô khan, không chèn dữ liệu kỹ thuật.

            Đầu ra: JSON với 6 trường:
            - fb_title (50–100 ký tự)
            - fb_description (≤500 ký tự)
            - image_prompt (≤77 ký tự)
            - daily_quote
            - quote_author
            - poster_tone (chọn từ: ["happy","sad","neutral","vibrant","warm","cool","pastel","bold","calm","dark","light","luxury","natural"])

            Chỉ xuất **JSON đúng định dạng**, không thêm text nào khác ngoài JSON.

            {parser_instructions}
        """)
    ]).partial(parser_instructions=parser_instructions)

    prompt_content = p_content.format(insight=insight_text, rag_info=rag_info)
    llm_output = llm.invoke(prompt_content)
    content_obj = safe_parse(parser, getattr(llm_output, "content", str(llm_output)))

    # -----------------------------
    # 5️⃣ Refine / Polish
    # -----------------------------
    p_refine = ChatPromptTemplate.from_messages([
    ("system", "Bạn là chuyên gia chỉnh sửa văn bản, đảm bảo ngôn ngữ Facebook tự nhiên và dí dỏm."),
    ("user", """
    Hãy tinh chỉnh JSON sau để status Facebook:
    - Mượt mà, tự nhiên, gần gũi
    - Thêm chút dí dỏm, ấm áp
    - Giữ nguyên nội dung chính và cảm xúc
    - Không thay đổi cấu trúc trường

    JSON gốc:
    {raw_json}

    Yêu cầu nghiêm ngặt:
    - Output chỉ là JSON hợp lệ, đúng schema.
    - Không thêm giải thích hay text khác.
    Schema: {parser_instructions}
    """)
    ]).partial(raw_json=content_obj.model_dump_json())

    prompt_refine_str = p_refine.format(raw_json=content_obj.model_dump_json(),parser_instructions="")
    llm_refined = llm.invoke(prompt_refine_str)
    content_obj = safe_parse(parser, getattr(llm_refined, "content", str(llm_refined)))
    print("📌 Content JSON sau refine:", content_obj)

    # -----------------------------
    # 6️⃣ Tạo ảnh + video (giữ nguyên logic)
    # -----------------------------
    if content_obj.image_prompt:
        pil_img = generate_image_from_prompt(content_obj.image_prompt)
        if pil_img:
            temp_image_path = os.path.join(TEMP_DIR, f"v_{uuid.uuid4().hex[:4]}.jpg")
            try:
                pil_img.save(temp_image_path, format="JPEG", quality=95)
            except Exception:
                traceback.print_exc()
                temp_image_path = None

            if temp_image_path:
                temp_video_path = os.path.join(TEMP_DIR, f"v_{uuid.uuid4().hex[:4]}.mp4")
                try:
                    generate_video(
                        temp_image_path,
                        content_obj.daily_stoic or content_obj.fb_description,
                        content_obj.quote_author or None,
                        output=temp_video_path,
                        size=(720,900),
                        total_frames=240,
                        fps=30
                    )
                    if not os.path.exists(temp_video_path):
                        temp_video_path = None
                except Exception:
                    traceback.print_exc()
                    temp_video_path = None

            msg_list.append(HumanMessage(content="✅ Video created" if temp_video_path else "❌ Video creation failed"))
        else:
            msg_list.append(HumanMessage(content="❌ Image generation failed"))

    # -----------------------------
    # 7️⃣ Đăng Facebook (giữ nguyên)
    # -----------------------------
    if temp_video_path or temp_image_path:
        pipeline = FacebookPipeline()
        fb_success = post_media(
            pipeline,
            video_path=temp_video_path,
            image_path=temp_image_path,
            fb_title=content_obj.fb_title,
            fb_description=content_obj.fb_description
        )
        msg_list.append(HumanMessage(content=f"Facebook: {'✅ Published' if fb_success else '❌ Failed'}"))

    # -----------------------------
    # 8️⃣ Cleanup temp files
    # -----------------------------
    cleanup_files([temp_image_path, temp_video_path])

    return {
        "status": "done",
        "messages": msg_list,
        "published": fb_success,
    }
