import base64
import json
import requests

API_KEY = "sk-c4yoOQRo0Awpov1PgGhPBVRXdK9TOfzIwSp4l2W8XqXYXcxX"
url = "https://api.stability.ai/v2beta/stable-image/generate/ultra"

files = {
    "prompt": (None, "Lighthouse on a cliff overlooking the ocean"),
    "height": (None, "512"),
    "width": (None, "512"),
    "samples": (None, "1"),
    "output_format": (None, "png")
}

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/json"
}

response = requests.post(url, headers=headers, files=files)

if response.status_code == 200:
    data = json.loads(response.content)
    image_base64 = response.content["image"]
    image_bytes = base64.b64decode(image_base64)
    # ghi file
    with open("lighthouse.webp", "wb") as f:
        f.write(image_bytes)
    print("Saved lighthouse.webp ✅")
else:
    print("Error:", response.status_code, response.text)