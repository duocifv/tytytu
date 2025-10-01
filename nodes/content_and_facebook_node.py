# main_pipeline.py
import os
import uuid
import traceback
import requests
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from langchain.output_parsers import PydanticOutputParser
from brain.notion_logger import get_hexagram_log
from services.llm_service import llm
from services.facebook_service import FacebookPipeline
from services.poster_service import generate_poster
from PIL import Image as PILImage
from io import BytesIO

# Thư mục lưu ảnh tạm
TEMP_DIR = "generated_images"
os.makedirs(TEMP_DIR, exist_ok=True)

# -----------------------------
# 1️⃣ Model JSON chuẩn với 3 trường
# -----------------------------
class ContentOutput(BaseModel):
    caption: str
    short_post: str
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
def generate_image_from_prompt(prompt: str) -> str | None:
    """
    Gửi prompt tới endpoint Hugging Face Space và lưu ảnh về TEMP_DIR.
    Trả về đường dẫn file hoặc None nếu lỗi.
    """
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
        return None


# -----------------------------
# 3️⃣ Pipeline chính
# -----------------------------
def content_and_facebook_node(state: dict):
    msg_list = []
    fb_success = False

    # 1️⃣ Lấy dữ liệu Notion
    notion_raw = get_hexagram_log()
    notion_data = extract_simple_notion(notion_raw)
    print("✅ Dữ liệu rút gọn từ Notion:", notion_data)

    # 2️⃣ Tạo content từ LLM
    parser = PydanticOutputParser(pydantic_object=ContentOutput)
    prompt_text = f"""
        Bạn là biên tập viên mạng xã hội, ngắn gọn, đồng cảm.
        Dữ liệu JSON: {notion_data}

        Viết 6 trường JSON:
        - caption: nội dung chính Facebook bằng tiếng Việt
        - short_post: nội dung ngắn bằng tiếng Việt, ≤280 ký tự
        - image_prompt: prompt bằng tiếng Anh để tạo ảnh, ngắn gọn ≤77 ký tự
        - daily_stoic: một câu trích dẫn ngắn, sâu sắc, truyền cảm hứng, dịch ra tiếng Việt.
        - author: tên tác giả của câu trích dẫn (ví dụ: Marcus Aurelius, Seneca, Epictetus…)
        - tone: gợi ý tông màu/thiết kế poster, ngắn gọn. Chỉ chọn trong danh sách:
            ["happy", "sad", "neutral", "vibrant", "warm", "cool", "pastel", 
            "bold", "calm", "dark", "light", "luxury", "natural"]
        Có thể kết hợp nhiều tone (ví dụ: "warm, serene" → "warm, calm").
        Nếu tone nằm ngoài danh sách, hãy ánh xạ về gần nhất.

        Không thêm text ngoài JSON, chỉ xuất JSON đúng định dạng.
        {parser.get_format_instructions()}
    """

    llm_output = llm.invoke(prompt_text)
    raw_result = getattr(llm_output, "content", str(llm_output))
    content_obj = safe_parse(parser, raw_result)
    print("📌 Content JSON:", content_obj)

    poster = None
    temp_path = None

    # 3️⃣ Tạo ảnh từ image_prompt
    if content_obj.image_prompt:
        pil_img = generate_image_from_prompt(content_obj.image_prompt)
        if pil_img:
            poster = generate_poster(
                pil_image=pil_img,
                text=content_obj.daily_stoic,
                author=content_obj.author,
                size=512,
                padding=38,
                font_size=30,
                line_spacing=4,
                brightness=0.6,
                saturation=1.4,
                gradient_alpha=38,
                tone=content_obj.tone,
            )
            msg_list.append(HumanMessage(content="✅ Poster created"))
        else:
            msg_list.append(HumanMessage(content="❌ Image generation failed"))

    # 4️⃣ Đăng Facebook nếu có poster
    if poster:
        temp_path = os.path.join(TEMP_DIR, f"poster_{uuid.uuid4().hex}.png")
        poster.save(temp_path, format="PNG")
        try:
            pipeline = FacebookPipeline()
            fb_result = pipeline.run(
                caption=content_obj.caption,
                short_post=content_obj.short_post,
                image_path=temp_path
            )
            fb_success = fb_result.get("published", False)
            msg_list.append(HumanMessage(content=f"Facebook: {fb_result.get('message', '✅ Done' if fb_success else '❌ Failed')}"))
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

    return {
        "status": "done",
        "messages": msg_list,
        "published": fb_success,
    }
