# services/facebook_service.py
import requests
import os
from dotenv import load_dotenv

# Load biến môi trường từ .env
load_dotenv()

class FacebookPipeline:
    """
    Service tương tác với Facebook Page:
    - Đăng bài
    - Đăng ảnh kèm caption
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

    def post_photo(self, image_path: str, caption: str = "") -> dict:
        """Đăng ảnh lên Page kèm caption"""
        url = f"{self.base_url}/photos"
        files = {"source": open(image_path, "rb")}
        data = {"caption": caption, "access_token": self.access_token}
        try:
            res = requests.post(url, files=files, data=data)
            res.raise_for_status()
            return res.json()
        except requests.RequestException as e:
            return {"error": str(e), "response": getattr(res, "text", "")}
        finally:
            files["source"].close()

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

    def run(self, caption: str, short_post: str, image_path: str = None) -> dict:
        """
        Nhận caption và short_post → format nội dung → đăng Facebook.
        Nếu có image_path thì đăng ảnh kèm caption.
        Trả về dict với published, result, message.
        """
        fb_content = f"{caption}\n\n{short_post}"
        try:
            if image_path:
                result = self.post_photo(image_path, caption=fb_content)
            else:
                result = self.post_message(fb_content)

            if "error" in result:
                published = False
                msg_text = f"❌ Failed to publish: {result['error']}"
            elif "id" in result:
                published = True
                msg_text = f"✅ Published to Facebook: {caption}"
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
