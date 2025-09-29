# services/facebook_service.py
import requests
import os
from dotenv import load_dotenv
from services.list_to_text import list_to_text




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

        self.base_url = f"https://graph.facebook.com/v23.0/{self.page_id}"

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
        except requests.RequestException as e:
            return {"error": str(e), "response": getattr(res, "text", "")}

    def get_page_info(self) -> dict:
        """Lấy thông tin cơ bản của Page."""
        url = self.base_url
        params = {"fields": "id,name,about,fan_count", "access_token": self.access_token}
        try:
            res = requests.get(url, params=params)
            res.raise_for_status()
            return res.json()
        except requests.RequestException as e:
            return {"error": str(e), "response": getattr(res, "text", "")}

    def run(self, state: dict) -> dict:
        """
        Nhận state (topic, outputs...) → format nội dung → đăng Facebook.
        Trả về dict với published, result, message.
        """
        outputs = state.get("outputs", {})

       # --- Title & Description ---
        title_info = outputs.get("title")
        if title_info:
            if hasattr(title_info, "text"):
                title_text = title_info.text
            if hasattr(title_info, "description"):
                title_description = title_info.description

        # --- Content & Tags ---
        content_info = outputs.get("content")
        if content_info:
            if hasattr(content_info, "body"):
                content_text = content_info.body
            if hasattr(content_info, "tags"):
                tags_text = list_to_text(content_info.tags)


        # --- Images & SEO ---
        images_info = outputs.get("images") or []
        images_text = list_to_text(images_info) if images_info else "No images"

        seo_info = outputs.get("seo") or {}
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
            result = self.post_message(fb_content)
            if "error" in result:
                published = False
                msg_text = f"❌ Failed to publish: {result['error']}"
            elif "id" in result:
                published = True
                msg_text = f"✅ Published to Facebook: {title_text}"
            else:
                published = False
                msg_text = f"❌ Unknown response from Facebook: {result}"
        except Exception as e:
            published = False
            result = {"error": str(e)}
            msg_text = f"❌ Exception while publishing: {e}"

        print(msg_text)
        return {
            "published": published,
            "result": result,
            "message": msg_text
        }
