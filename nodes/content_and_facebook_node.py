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

# Thư mục lưu ảnh tạm
TEMP_DIR = "generated_images"
os.makedirs(TEMP_DIR, exist_ok=True)

# -----------------------------
# 1️⃣ Model JSON chuẩn với 3 trường
# -----------------------------
class ContentOutput(BaseModel):
    caption: str
    short_post: str
    image_prompt: str  # ≤77 ký tự, dùng tạo ảnh

def safe_parse(parser, text: str):
    try:
        return parser.parse(text)
    except Exception:
        traceback.print_exc()
        return ContentOutput(
            caption="Fallback caption",
            short_post="Fallback short post",
            image_prompt="Fallback prompt"
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
        # Tăng timeout lên 900 giây (15 phút)
        response = requests.post(url, json=payload, headers=headers, timeout=2000)
        response.raise_for_status()

        # Lưu file tạm
        image_path = os.path.join(TEMP_DIR, f"generated_image_{uuid.uuid4().hex}.png")
        with open(image_path, "wb") as f:
            f.write(response.content)

        print("✅ Ảnh đã lưu:", image_path)
        return image_path

    except requests.exceptions.RequestException as e:
        print("❌ Lỗi tạo ảnh (HTTP):", e)
    except Exception as e:
        print("❌ Lỗi lưu ảnh:", e)

    return None


# -----------------------------
# 3️⃣ Pipeline chính
# -----------------------------
def content_and_facebook_node(state: dict):
    msg_list = []
    fb_success = False
    image_file = None

    # 1️⃣ Lấy dữ liệu Notion
    notion_raw = get_hexagram_log()
    notion_data = extract_simple_notion(notion_raw)
    print("✅ Dữ liệu rút gọn từ Notion:", notion_data)

    # 2️⃣ Tạo content từ LLM với 3 trường JSON
    parser = PydanticOutputParser(pydantic_object=ContentOutput)
    prompt_text = f"""
    Bạn là biên tập viên mạng xã hội, ngắn gọn, đồng cảm.
    Dữ liệu JSON: {notion_data}

    Viết 3 trường JSON:
    - caption: nội dung chính Facebook bằng tiếng Việt
    - short_post: nội dung ngắn bằng tiếng Việt, ≤280 ký tự
    - image_prompt: prompt bằng tiếng Anh để tạo ảnh, ngắn gọn ≤77 ký tự

    Không thêm text ngoài JSON, chỉ xuất JSON đúng định dạng.
    {parser.get_format_instructions()}
    """
    llm_output = llm.invoke(prompt_text)
    raw_result = getattr(llm_output, "content", str(llm_output))
    content_obj = safe_parse(parser, raw_result)
    print(f"📌 Content JSON:", content_obj)

    # 3️⃣ Tạo ảnh từ image_prompt (blocking)
    if content_obj.image_prompt:
        image_file = generate_image_from_prompt(content_obj.image_prompt)
        if image_file:
            msg_list.append(HumanMessage(content=f"✅ Image generated at {image_file}"))
        else:
            msg_list.append(HumanMessage(content="❌ Image generation failed"))

    # 4️⃣ Chỉ đăng Facebook khi ảnh đã sẵn sàng
    try:
        pipeline = FacebookPipeline()
        fb_result = pipeline.run(
            caption=content_obj.caption,
            short_post=content_obj.short_post,
            image_path=image_file
        )
        fb_success = fb_result.get("published", False)
        msg_list.append(HumanMessage(content=f"Facebook: {fb_result.get('message', '✅ Done' if fb_success else '❌ Failed')}"))
    except Exception as e:
        traceback.print_exc()
        msg_list.append(HumanMessage(content=f"Facebook error: {e}"))

    # 5️⃣ Xóa file tạm sau khi đăng
    if image_file and os.path.exists(image_file):
        os.remove(image_file)
        print("🗑️ Xóa ảnh tạm:", image_file)

    return {
        "status": "done",
        "messages": msg_list,
        "published": fb_success,
    }
