# main_pipeline_with_two_tier.py
import os
import uuid
import traceback
import requests
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain.output_parsers import PydanticOutputParser
from brain.notion_logger import get_hexagram_log
from services.generate_video_service import generate_video
from services.llm_service import llm
from services.facebook_service import FacebookPipeline
from services.rag_service import RAGRetriever  # giả định có RAG
from PIL import Image as PILImage
from io import BytesIO

# -----------------------------
# Thư mục lưu tạm (ảnh + video)
# -----------------------------
TEMP_DIR = "generated_images"
os.makedirs(TEMP_DIR, exist_ok=True)

# -----------------------------
# 1️⃣ Model JSON chuẩn
# -----------------------------
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
        keys = ["Nhan", "Dia", "Thien", "Summary", "KeyEvent", "Health", "Work", "Effect", "Trend", "Finance", "Psychology", "Family", "Spiritual", "Community" ]
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


# -----------------------------
# 2️⃣ Tạo ảnh từ Hugging Face Space
# -----------------------------
def generate_image_from_prompt(prompt: str) -> PILImage.Image | None:
    url = "https://duocifv-tytytu-image.hf.space/generate-image"
    payload = {"prompt": prompt}
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=2000)
        response.raise_for_status()
        img = PILImage.open(BytesIO(response.content)).convert("RGB")
        print("✅ Image generated successfully")
        return img
    except Exception as e:
        print("❌ Lỗi tạo ảnh:", e)
        traceback.print_exc()
        return None

# -----------------------------
# Helper: đăng media lên Facebook
# -----------------------------
def post_media(pipeline: FacebookPipeline, video_path=None, image_path=None, fb_title="", fb_description=""):
    fb_title_safe = fb_title[:100]
    try:
        if video_path:
            fb_result = pipeline.post_video(
                video_path=video_path,
                title=fb_title_safe,
                description=fb_description
            )
            success = bool(fb_result.get("id"))
        elif image_path:
            fb_result = pipeline.run(
                image_path=image_path,
                title=fb_title,
                description=fb_description
            )
            success = bool(fb_result.get("published", False))
        else:
            success = False
    except Exception:
        traceback.print_exc()
        success = False
    return success

# -----------------------------
# 3️⃣ Pipeline chính: Two-tier + RAG + Refine/Polish
# -----------------------------
def content_and_facebook_node(state: dict):
    msg_list = []
    fb_success = False
    temp_image_path = None
    temp_video_path = None

    # 1️⃣ Lấy dữ liệu Notion
    notion_raw = get_hexagram_log()
    notion_data = extract_simple_notion(notion_raw)
    print("✅ Dữ liệu rút gọn từ Notion:", notion_data)

    # ✅ Nếu notion_data rỗng, đặt mặc định
    if not notion_data:
        notion_data = {"Summary": "Không có dữ liệu hôm nay"}

    notion_data_str = str(notion_data)
    parser = PydanticOutputParser(pydantic_object=ContentOutput)

    # -----------------------------
    # 2️⃣ Tier 1: Phân tích dữ liệu
    # -----------------------------
    p_analysis = ChatPromptTemplate.from_messages([
        ("system", "Bạn là chuyên gia phân tích dữ liệu cộng đồng."),
        ("user",
         "Dữ liệu JSON từ Notion: {notion_data}\n"
         "Hãy phân tích và rút ra các insight chính:\n"
         "- Tình hình thiên tai, dịch bệnh, kinh tế, tâm lý\n"
         "- Tác động đến sức khỏe, công việc, đời sống gia đình\n"
         "- Gợi ý cách ứng phó, chăm sóc sức khỏe và tinh thần\n"
         "Trả về văn bản súc tích, dễ hiểu.")
    ]).partial(notion_data=notion_data_str)
    prompt_analysis = p_analysis.format(notion_data=notion_data_str)
    insight_text = getattr(llm.invoke(prompt_analysis), "content", "")

    # -----------------------------
    # 3️⃣ RAG: lấy dữ liệu thực tế
    # -----------------------------
    rag = RAGRetriever(sources=["VNExpress", "Khí tượng Thủy văn", "WHO"])
    rag_info = rag.retrieve(notion_data)
    if isinstance(rag_info, dict):
        rag_info = str(rag_info)

    # -----------------------------
    # 4️⃣ Tier 2: Viết content dựa trên insight + RAG
    # -----------------------------
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
        ("system", "Bạn là chuyên gia chỉnh sửa văn bản."),
        ("user",
        "Hãy tinh chỉnh JSON sau để status Facebook mượt, tự nhiên, thêm chút dí dỏm, "
        "giữ nguyên nội dung và cảm xúc.\nJSON: {raw_json}")
    ]).partial(raw_json=content_obj.model_dump_json())

    prompt_refine_str = p_refine.format(raw_json=content_obj.model_dump_json())
    llm_refined = llm.invoke(prompt_refine_str)
    content_obj = safe_parse(parser, getattr(llm_refined, "content", str(llm_refined)))
    print("📌 Content JSON sau refine:", content_obj)

    # -----------------------------
    # 6️⃣ Tạo ảnh + video
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
    # 7️⃣ Đăng Facebook
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
    for path in [temp_image_path, temp_video_path]:
        try:
            if path and os.path.exists(path):
                os.remove(path)
        except Exception:
            traceback.print_exc()

    return {
        "status": "done",
        "messages": msg_list,
        "published": fb_success,
    }
