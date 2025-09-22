import os
from google_auth_oauthlib.flow import InstalledAppFlow

# Scopes cần thiết để upload video
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

# Thay YOUR_CLIENT_ID & SECRET
CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID", "YOUR_CLIENT_ID")
CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET", "YOUR_CLIENT_SECRET")

flow = InstalledAppFlow.from_client_config(
    {
        "installed": {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        }
    },
    scopes=SCOPES
)

creds = flow.run_console()  # sẽ in link ra terminal → bạn đăng nhập Google và cấp quyền
print("Access Token:", creds.token)
print("Refresh Token:", creds.refresh_token)


# Cách 1: Cài từng gói riêng
pip install google-auth-oauthlib
pip install google-api-python-client google-auth google-auth-oauthlib python-dotenv

# Cách 2: Cài tất cả trong 1 lệnh
pip install google-api-python-client google-auth google-auth-oauthlib python-dotenv
