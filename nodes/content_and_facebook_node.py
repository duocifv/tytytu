# nodes/content_and_facebook_node.py
import traceback
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from langchain.output_parsers import PydanticOutputParser
from brain.notion_logger import get_hexagram_log
from services.llm_service import llm
from services.facebook_service import FacebookPipeline
import requests
import os

# Thư mục lưu ảnh tạm
TEMP_DIR = "generated_images"
os.makedirs(TEMP_DIR, exist_ok=True)

# 1️⃣ Model JSON chuẩn
class ContentOutput(BaseModel):
    caption: str
    short_post: str

def safe_parse(parser, text: str):
    try:
        return parser.parse(text)
    except Exception:
        traceback.print_exc()
        return ContentOutput(
            caption="Fallback caption",
            short_post="Fallback short post",
        )

def extract_simple_notion(notion_raw: dict, keys=None):
    """Lấy ra dict chỉ gồm các key cần thiết từ dữ liệu Notion."""
    if keys is None:
        keys = ["Summary", "Health", "Work", "Nhan", "Effect", "Trend", "Thien", "Dia", "Finance", "Psychology", "KeyEvent"]

    simple = {}
    try:
        results = notion_raw.get("results", [])
        if not results:
            return simple
        page = results[0]  # chỉ lấy page đầu tiên
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

def generate_image_from_prompt(prompt: str) -> str:
    """
    Gọi API Hugging Face Space tạo ảnh từ prompt.
    Trả về đường dẫn file ảnh tạm.
    """
    url = "https://duocifv-tytytu-image.hf.space/generate-image"
    params = {"prompt": prompt}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        # Lưu ảnh tạm
        image_path = os.path.join(TEMP_DIR, "generated_image.png")
        with open(image_path, "wb") as f:
            f.write(response.content)
        return image_path
    except Exception as e:
        print("❌ Lỗi tạo ảnh:", e)
        return None

def content_and_facebook_node(state: dict):
    msg_list = []

    # 1️⃣ Lấy và rút gọn dữ liệu từ Notion
    notion_raw = get_hexagram_log()
    notion_data = extract_simple_notion(notion_raw)
    print("✅ Dữ liệu rút gọn từ Notion:", notion_data)

    # 2️⃣ Tạo content từ LLM
    parser = PydanticOutputParser(pydantic_object=ContentOutput)
    prompt_text = f"""
Bạn là biên tập viên mạng xã hội, ngắn gọn, đồng cảm.
Dữ liệu JSON: {notion_data}

Viết 2 trường JSON: caption, short_post.
Không thêm text ngoài JSON, tiếng Việt, dễ đọc, thân thiện, ≤280 ký tự cho short_post.
{parser.get_format_instructions()}
"""
    llm_output = llm.invoke(prompt_text)
    raw_result = getattr(llm_output, "content", str(llm_output))
    content_obj = safe_parse(parser, raw_result)
    print(f"facebook ----->", content_obj)

    # 3️⃣ Tạo ảnh từ caption + short_post
    image_prompt = f"{content_obj.caption}. {content_obj.short_post}"
    image_file = generate_image_from_prompt(image_prompt)
    if image_file:
        msg_list.append(HumanMessage(content=f"✅ Image generated at {image_file}"))
    else:
        msg_list.append(HumanMessage(content="❌ Image generation failed"))

    # 4️⃣ Đăng Facebook kèm ảnh
    fb_success = False
    try:
        pipeline = FacebookPipeline()
        fb_result = pipeline.run(
            caption=content_obj.caption,
            short_post=content_obj.short_post,
            image_path=image_file
        ) or {}
        fb_success = fb_result.get("published", False)
        msg_list.append(HumanMessage(content=f"Facebook: {fb_result.get('message', '✅ Done' if fb_success else '❌ Failed')}"))
    except Exception as e:
        traceback.print_exc()
        msg_list.append(HumanMessage(content=f"Facebook error: {e}"))

    return {
        "status": "done",
        "messages": msg_list,
        "published": fb_success,
    }
