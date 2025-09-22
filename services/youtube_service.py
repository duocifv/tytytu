import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from dotenv import load_dotenv

# Load biến môi trường từ .env
load_dotenv()

class YouTubeService:
    """
    Service tự động upload video lên YouTube
    Yêu cầu đã có Refresh Token và OAuth2 client ID/secret
    """

    def __init__(self):
        self.client_id = os.getenv("YOUTUBE_CLIENT_ID")
        self.client_secret = os.getenv("YOUTUBE_CLIENT_SECRET")
        self.refresh_token = os.getenv("YOUTUBE_REFRESH_TOKEN")
        self.access_token = None  # sẽ được lấy từ refresh token

        if not self.client_id or not self.client_secret or not self.refresh_token:
            raise ValueError("❌ Chưa cấu hình YOUTUBE_CLIENT_ID / CLIENT_SECRET / REFRESH_TOKEN")

        self.scopes = ["https://www.googleapis.com/auth/youtube.upload"]
        self.credentials = Credentials(
            None,
            refresh_token=self.refresh_token,
            client_id=self.client_id,
            client_secret=self.client_secret,
            token_uri="https://oauth2.googleapis.com/token",
            scopes=self.scopes
        )
        self.youtube = build("youtube", "v3", credentials=self.credentials)

    def upload_video(self, file_path: str, title: str, description: str = "", tags: list = None, privacy_status: str = "public"):
        """
        Upload video lên YouTube
        - file_path: đường dẫn file video
        - title: tiêu đề video
        - description: mô tả video
        - tags: list các tag
        - privacy_status: public / unlisted / private
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags or [],
            },
            "status": {
                "privacyStatus": privacy_status
            }
        }

        media = MediaFileUpload(file_path, chunksize=-1, resumable=True, mimetype="video/*")
        request = self.youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"Uploading... {int(status.progress() * 100)}%")

        print(f"✅ Upload completed! Video ID: {response['id']}")
        return response

# =============================
# Ví dụ sử dụng
# =============================
if __name__ == "__main__":
    yt = YouTubeService()
    video_file = "path/to/video.mp4"
    result = yt.upload_video(video_file, title="Test Video", description="Upload tự động", tags=["test", "demo"])
    print("Video uploaded:", result)
