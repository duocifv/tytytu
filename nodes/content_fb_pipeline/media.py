# nodes/content_and_facebook_node/node_media.py
import requests
import traceback
from PIL import Image as PILImage
from io import BytesIO

def generate_image_from_prompt(prompt: str) -> PILImage.Image | None:
    """
    Giữ nguyên: gọi HF Space, trả về PIL Image hoặc None
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
        traceback.print_exc()
        return None
