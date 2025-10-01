# main_pipeline.py (optimized & fixed)
import os
import uuid
import traceback
import requests
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from langchain.output_parsers import PydanticOutputParser
from brain.notion_logger import get_hexagram_log
from services.generate_video_service import generate_video
from services.llm_service import llm
from services.facebook_service import FacebookPipeline
from PIL import Image as PILImage
from io import BytesIO

# Thư mục lưu tạm (ảnh + video)
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
    author: str
    tone: str

def safe_parse(parser, text: str):
    try:
        return parser.parse(text)
    except Exception:
        traceback.print_exc()
        return ContentOutput(
            caption="Fallback caption",
            short_post="Fallback short post",
            image_prompt="Fallback prompt",
            daily_stoic="Fallback stoic",
            author="Unknown",
            tone="neutral"
        )

def extract_simple_notion(notion_raw: dict, keys=None):
    """Rút gọn dữ liệu từ Notion"""
    if keys is None:
        keys = ["Summary", "Health", "Work", "Nhan", "Effect", "Trend",
                "Thien", "Dia", "Finance", "Psychology", "KeyEvent"]
    simple = {}
    try:
        results = notion_raw.get("results", [])
        if not results:
            return simple
        page = results[0]
        props = page.get("properties", {})
        for k in keys:
            v = props.get(k)
            if not v:
                continue
            rich_text = v.get("rich_text", [])
            if rich_text and isinstance(rich_text, list):
                simple[k] = " ".join(rt.get("plain_text", "") for rt in rich_text).strip()
    except Exception:
        traceback.print_exc()
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
# 3️⃣ Pipeline chính
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

    # 2️⃣ Tạo content từ LLM
    parser = PydanticOutputParser(pydantic_object=ContentOutput)
    prompt_text = f"""
    Bạn là biên tập viên mạng xã hội, viết nội dung ngắn gọn, đồng cảm.
    Dữ liệu JSON: {notion_data}

    Viết 6 trường JSON với tên dễ nhận biết và tuân theo giới hạn ký tự:
    - fb_title: tiêu đề chính cho Facebook, dài từ 50–100 ký tự, bắt buộc ≤100 ký tự
    - fb_description: nội dung tóm tắt ngắn gọn, ≤500 ký tự, dùng cho bài post tóm tắt
    - image_prompt: prompt bằng tiếng Anh để tạo ảnh, ngắn gọn ≤77 ký tự
    - daily_quote: một câu trích dẫn ngắn, sâu sắc, truyền cảm hứng, dịch ra tiếng Việt
    - quote_author: tên tác giả của câu trích dẫn
    - poster_tone: gợi ý tông màu/thiết kế poster, ngắn gọn, chỉ chọn trong danh sách:
    ["happy", "sad", "neutral", "vibrant", "warm", "cool", "pastel", 
    "bold", "calm", "dark", "light", "luxury", "natural"]

    Chỉ xuất **JSON đúng định dạng**, không thêm text nào khác ngoài JSON.
    {parser.get_format_instructions()}
    """

    llm_output = llm.invoke(prompt_text)
    raw_result = getattr(llm_output, "content", str(llm_output))
    content_obj = safe_parse(parser, raw_result)
    print("📌 Content JSON:", content_obj)

    # 3️⃣ Tạo ảnh + video
    if content_obj.image_prompt:
        pil_img = generate_image_from_prompt(content_obj.image_prompt)
        if pil_img:
            temp_image_path = os.path.join(TEMP_DIR, f"v_{uuid.uuid4().hex[:4]}.jpg")
            try:
                pil_img.save(temp_image_path, format="JPEG", quality=95)
                print("✅ Saved temp image to:", temp_image_path)
            except Exception:
                traceback.print_exc()
                temp_image_path = None

            if temp_image_path:
                temp_video_path = os.path.join(TEMP_DIR, f"v_{uuid.uuid4().hex[:4]}.mp4")
                try:
                    print("⏳ Generating video...")
                    generate_video(temp_image_path, content_obj.daily_stoic or content_obj.caption, content_obj.author or None,
                                   output=temp_video_path, size=(720,1280), total_frames=240, fps=30)
                    if os.path.exists(temp_video_path):
                        print("✅ Video generated:", temp_video_path)
                    else:
                        print("❌ Video generation did not produce expected file")
                        temp_video_path = None
                except Exception:
                    traceback.print_exc()
                    temp_video_path = None

            msg_list.append(HumanMessage(content="✅ Video created" if temp_video_path else "❌ Video creation failed"))
        else:
            msg_list.append(HumanMessage(content="❌ Image generation failed"))

    # 4️⃣ Đăng Facebook
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

    # 5️⃣ Cleanup temp files
    # for path in [temp_image_path, temp_video_path]:
    #     try:
    #         if path and os.path.exists(path):
    #             os.remove(path)
    #     except Exception:
    #         traceback.print_exc()

    return {
        "status": "done",
        "messages": msg_list,
        "published": fb_success,
    }
