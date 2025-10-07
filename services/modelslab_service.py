import requests
import json
import base64
import time
import os

API_URL = "https://modelslab.com/api/v6/images/text2img"
API_KEY = "Cgax9O9wFAFuHuSW45yKBmf3xNPeEh82eWvsqcUbHXA7VFrFWsHVs4lMTnLs"

# Đảm bảo thư mục chứa ảnh tồn tại
OUTPUT_DIR = "generated_reels"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def _clean_base64(s: str) -> str:
    if not isinstance(s, str):
        return s
    if s.startswith("data:") and "base64," in s:
        s = s.split("base64,", 1)[1]
    return s.strip()


def _detect_and_save_bytes(b: bytes, out_base="output_image"):
    if b.startswith(b"\x89PNG"):
        out = f"{out_base}.png"
    elif b.startswith(b"\xff\xd8\xff"):
        out = f"{out_base}.jpg"
    else:
        out = f"{out_base}.bin"
    with open(out, "wb") as f:
        f.write(b)
    return out


def download_text_from_url(url: str, timeout=60):
    try:
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print("⚠️ Lỗi khi tải URL:", e)
        return None


def download_bytes_from_url(url: str, timeout=60):
    try:
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        return r.content, r.headers.get("Content-Type", "")
    except Exception as e:
        print("⚠️ Lỗi khi tải URL (bytes):", e)
        return None, None


def generate_image_direct(prompt: str, out_base="output_image", max_attempts=60, sleep_sec=5):
    payload = {
        "model_id": "fluxdev",
        "prompt": prompt,
        "samples": "1",
        "negative_prompt": "(worst quality:2), (low quality:2), watermark, text, logo, ugly, blurry",
        "width": "768",
        "height": "1024",
        "clip_skip": "1",
        "enhance_prompt": "false",
        "guidance_scale": "7.5",
        "safety_checker": "false",
        "watermark": "no",
        "base64": "yes",
        "seed": "0",
        "num_inference_steps": "20",
        "key": API_KEY
    }

    print("🔄 Sending generation request...")
    try:
        resp = requests.post(API_URL, json=payload, timeout=30)
        result = resp.json()
    except Exception as e:
        print("❌ Lỗi khi gửi request:", e)
        return None

    fetch_url = result.get("fetch_result") or (result.get("future_links")[0] if result.get("future_links") else None)
    if not fetch_url:
        print("❌ Không có fetch_result/future_links trong phản hồi:")
        print(json.dumps(result, indent=2))
        return None

    print("⏳ Fetching from:", fetch_url)

    for i in range(1, max_attempts + 1):
        try:
            fetch_resp = requests.post(fetch_url, json={"key": API_KEY}, timeout=30)
            fetch_data = fetch_resp.json()
        except Exception as e:
            print(f"⚠️ Fetch lỗi ({i}/{max_attempts}):", e)
            time.sleep(sleep_sec)
            continue

        status = fetch_data.get("status")
        output = fetch_data.get("output") or fetch_data.get("image") or None
        print(f"[{i}/{max_attempts}] status={status} output_present={bool(output)}")

        # --- Khi có output hợp lệ ---
        if status == "success" and output:
            candidate = output[0] if isinstance(output, list) else output
            if not candidate:
                continue

            candidate = candidate.strip()

            # Nếu là URL
            if candidate.startswith("http"):
                print("🔗 Output là URL:", candidate)
                if candidate.endswith(".base64") or candidate.endswith(".txt"):
                    txt = download_text_from_url(candidate)
                    if txt:
                        b64 = _clean_base64(txt)
                        try:
                            img_bytes = base64.b64decode(b64, validate=True)
                        except Exception:
                            print("⚠️ Decode lỗi từ base64 URL")
                            continue
                        # Lưu trong generated_reels/
                        out_path = os.path.join(OUTPUT_DIR, f"{out_base}_fromurl_{i}.jpg")
                        _detect_and_save_bytes(img_bytes, out_path[:-4])
                        print("✅ Image saved ->", out_path)
                        return out_path

                else:
                    content, _ = download_bytes_from_url(candidate)
                    if content:
                        out_path = os.path.join(OUTPUT_DIR, f"{out_base}_fromurl_{i}.jpg")
                        _detect_and_save_bytes(content, out_path[:-4])
                        print("✅ Image saved ->", out_path)
                        return out_path

            # Nếu là base64 trực tiếp
            else:
                b64 = _clean_base64(candidate)
                try:
                    img_bytes = base64.b64decode(b64, validate=True)
                except Exception as e:
                    print("⚠️ Decode base64 lỗi:", e)
                    continue
                out_path = os.path.join(OUTPUT_DIR, f"{out_base}_{i}.jpg")
                _detect_and_save_bytes(img_bytes, out_path[:-4])
                print("✅ Image saved ->", out_path)
                return out_path

        time.sleep(sleep_sec)

    print("❌ Hết thời gian chờ — kiểm tra debug_fetch_*.json để biết chi tiết.")
    return None


if __name__ == "__main__":
    test_prompt = "A cinematic portrait of a couple at a bus stop during sunset, film color tone."
    path = generate_image_direct(test_prompt, "scene_test")
    print("🖼️ Done:", path)
