# services/facebook_service.py
import requests
import os
from dotenv import load_dotenv
from nodes.finalize_node import list_to_text

# Load biến môi trường từ .env
load_dotenv()


class FacebookPipeline:
    """
    Service tương tác với Facebook Page:
    - Đăng bài
    - Lấy thông tin cơ bản
    """

    def __init__(self):
        self.page_id = os.getenv("FB_PAGE_ID")
        self.access_token = os.getenv("FB_PAGE_ACCESS_TOKEN")

        if not self.page_id or not self.access_token:
            raise ValueError("❌ FB_PAGE_ID hoặc FB_PAGE_ACCESS_TOKEN chưa được cấu hình!")

        self.base_url = f"https://graph.facebook.com/{self.page_id}"

    def post_message(self, message: str, link: str = None) -> dict:
        """Đăng bài lên Page. Nếu muốn gắn link thì truyền `link`."""
        data = {"message": message, "access_token": self.access_token}
        if link:
            data["link"] = link

        url = f"{self.base_url}/feed"
        try:
            res = requests.post(url, data=data)
            res.raise_for_status()
            return res.json()
        except requests.HTTPError as e:
            return {"error": str(e), "response": res.text}

    def get_page_info(self) -> dict:
        """Lấy thông tin cơ bản của Page."""
        url = self.base_url
        params = {"fields": "id,name,about,fan_count", "access_token": self.access_token}
        try:
            res = requests.get(url, params=params)
            res.raise_for_status()
            return res.json()
        except requests.HTTPError as e:
            return {"error": str(e), "response": res.text}

    def run(self, state: dict) -> dict:
        """
        Nhận state (topic, outputs...) → format nội dung → đăng Facebook.
        Trả về dict với published, result, message.
        """
        outputs = state.get("outputs", {})

        # --- Title & Description ---
        title_info = outputs.get("title", {}) if isinstance(outputs.get("title", {}), dict) else {}
        title_text = title_info.get("text", "Untitled")
        title_description = title_info.get("description", "No description")

        # --- Content & Tags ---
        content_info = outputs.get("content", {}) if isinstance(outputs.get("content", {}), dict) else {}
        content_text = content_info.get("body", "No content")
        tags_text = list_to_text(content_info.get("tags", []))

        # --- Images & SEO ---
        images_info = outputs.get("images", [])
        images_text = list_to_text(images_info) if images_info else "No images"

        seo_info = outputs.get("seo", {})
        seo_text = f"Title: {seo_info.get('title', '')}, Description: {seo_info.get('description', '')}" if seo_info else "No SEO meta"

        # --- Format nội dung đẹp ---
        fb_content = (
            f"📰 {title_text}\n"
            f"💬 {title_description}\n\n"
            f"📄 {content_text[:300]}...\n\n"
            f"🏷 Tags: {tags_text}\n"
            f"🖼 Images: {images_text}\n"
            f"🔍 SEO: {seo_text}"
        )

        # --- Đăng lên Facebook ---
        try:
            result = self.post_message(fb_content)  # 🔥 sửa lại chỗ này
            published = "id" in result
            msg_text = f"✅ Published to Facebook: {title_text}" if published else f"❌ Failed: {result}"
        except Exception as e:
            published = False
            result = None
            msg_text = f"❌ Error publishing to Facebook: {e}"

        return {
            "published": published,
            "result": result,
            "message": msg_text
        }
