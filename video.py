import requests
import time

API_KEY = "6f136cbc6e79403792dc7662ea42f6da"  # 🔑 Thay bằng API key của bạn
BASE_URL = "https://api.aimlapi.com/v2/generate/video/kling/generation"

def create_kling_video(image_url, prompt="cinematic motion", duration=5):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "kling-video/v1/standard/image-to-video",
        "image_url": image_url,
        "prompt": prompt,
        "duration": duration
    }
    res = requests.post(BASE_URL, headers=headers, json=payload)
    print("📤 Create video:", res.status_code)
    print(res.text)
    if res.status_code not in (200, 201):
        return None
    return res.json().get("id")

def check_status(generation_id):
    headers = {"Authorization": f"Bearer {API_KEY}"}
    url = f"{BASE_URL}?generation_id={generation_id}"
    res = requests.get(url, headers=headers)
    return res.json()

def main():
    image_url = "https://example.com/your_image.jpg"
    prompt = "A cinematic slow camera movement, realistic lighting"
    duration = 5

    gen_id = create_kling_video(image_url, prompt, duration)
    if not gen_id:
        print("❌ Không tạo được video.")
        return

    print("🆔 Generation ID:", gen_id)
    print("⏳ Đang chờ video hoàn thành...")

    for _ in range(20):  # kiểm tra trong ~3 phút
        time.sleep(10)
        result = check_status(gen_id)
        status = result.get("status")
        print("📡 Status:", status)
        if status == "completed":
            print("✅ Video URL:", result.get("video", {}).get("url"))
            break
        elif status == "failed":
            print("❌ Failed:", result)
            break

if __name__ == "__main__":
    main()
