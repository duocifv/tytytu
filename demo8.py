# demo8_fetch_url_base64.py
import requests
import json
import base64
import binascii
import time
import os

API_URL = "https://modelslab.com/api/v6/images/text2img"
API_KEY = "Cgax9O9wFAFuHuSW45yKBmf3xNPeEh82eWvsqcUbHXA7VFrFWsHVs4lMTnLs"

def _clean_base64(s: str) -> str:
    if not isinstance(s, str):
        return s
    # remove data:...;base64, prefix if any
    if s.startswith("data:") and "base64," in s:
        s = s.split("base64,", 1)[1]
    return s.strip()

def _detect_and_save_bytes(b: bytes, out_base="output_image"):
    if b.startswith(b"\x89PNG"):
        out = out_base + ".png"
    elif b.startswith(b"\xff\xd8\xff"):
        out = out_base + ".jpg"
    else:
        out = out_base + ".bin"
    with open(out, "wb") as f:
        f.write(b)
    return out

def download_text_from_url(url: str, timeout=60):
    """Tải return text từ URL (dùng cho .base64 files)"""
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
        return

    # Lấy fetch URL / future_links
    fetch_url = result.get("fetch_result") or (result.get("future_links")[0] if result.get("future_links") else None)
    if not fetch_url:
        print("❌ Không có fetch_result/future_links trong phản hồi:")
        print(json.dumps(result, indent=2))
        return

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

        # Nếu trả future_links (đã thấy), ưu tiên thử tải chúng
        if isinstance(fetch_data, dict) and fetch_data.get("future_links"):
            for idx, link in enumerate(fetch_data["future_links"]):
                print("🔗 Thử future_link:", link)
                # Nếu file .base64 -> tải text -> decode -> lưu
                if link.endswith(".base64") or link.endswith(".txt"):
                    txt = download_text_from_url(link)
                    if txt:
                        b64 = _clean_base64(txt)
                        try:
                            img_bytes = base64.b64decode(b64, validate=True)
                        except Exception:
                            mod = len(b64) % 4
                            if mod != 0:
                                try:
                                    img_bytes = base64.b64decode(b64 + ("=" * (4 - mod)), validate=True)
                                except Exception as e:
                                    print("⚠️ Không decode được future_link base64:", e)
                                    continue
                            else:
                                continue
                        out = _detect_and_save_bytes(img_bytes, out_base + f"_futurelink{idx}")
                        print("✅ Image saved from future_link:", out)
                        return
                else:
                    # try download as bytes (image)
                    content, ctype = download_bytes_from_url(link)
                    if content:
                        # if it is textual base64 inside response, try that first
                        if ctype.startswith("text") or link.endswith(".base64"):
                            txt = content.decode("utf-8", errors="ignore").strip()
                            if len(txt) > 100:
                                try:
                                    img_bytes = base64.b64decode(_clean_base64(txt), validate=True)
                                    out = _detect_and_save_bytes(img_bytes, out_base + f"_futurelink{idx}")
                                    print("✅ Image saved from future_link text:", out)
                                    return
                                except Exception:
                                    pass
                        # otherwise treat as image bytes
                        out = _detect_and_save_bytes(content, out_base + f"_futurelink{idx}")
                        print("✅ Image saved from future_link bytes:", out)
                        return
            # if future_links present but not successful -> save debug and continue
            with open(f"debug_fetch_future_{i}.json", "w", encoding="utf-8") as dbg:
                json.dump(fetch_data, dbg, ensure_ascii=False, indent=2)
            time.sleep(sleep_sec)
            continue

        # normal output candidate
        candidate = None
        if isinstance(output, str):
            candidate = output
        elif isinstance(output, list) and len(output) > 0:
            candidate = output[0]

        if not candidate:
            print(f"⏳ Output trống. Lưu debug -> debug_fetch_{i}.json")
            with open(f"debug_fetch_{i}.json", "w", encoding="utf-8") as dbg:
                json.dump(fetch_data, dbg, ensure_ascii=False, indent=2)
            time.sleep(sleep_sec)
            continue

        candidate = candidate.strip()
        # Nếu candidate là URL (.base64 hay S3 link)
        if candidate.startswith("http://") or candidate.startswith("https://"):
            print("🔗 Output là URL:", candidate)
            # nếu link chỉ chứa base64 text
            if candidate.endswith(".base64") or candidate.endswith(".txt"):
                txt = download_text_from_url(candidate)
                if txt:
                    b64 = _clean_base64(txt)
                    try:
                        img_bytes = base64.b64decode(b64, validate=True)
                    except Exception:
                        mod = len(b64) % 4
                        if mod != 0:
                            try:
                                img_bytes = base64.b64decode(b64 + ("=" * (4 - mod)), validate=True)
                            except Exception as e:
                                print("⚠️ Không decode base64 từ URL:", e)
                                with open(f"debug_fetch_{i}.json", "w", encoding="utf-8") as dbg:
                                    json.dump(fetch_data, dbg, ensure_ascii=False, indent=2)
                                time.sleep(sleep_sec)
                                continue
                        else:
                            print("⚠️ Base64 không hợp lệ từ URL.")
                            with open(f"debug_fetch_{i}.json", "w", encoding="utf-8") as dbg:
                                json.dump(fetch_data, dbg, ensure_ascii=False, indent=2)
                            time.sleep(sleep_sec)
                            continue
                    out = _detect_and_save_bytes(img_bytes, out_base + f"_fromurl_{i}")
                    print("✅ Image saved from .base64 URL ->", out)
                    return
            # khác: thử tải bytes trực tiếp (nếu là image)
            content, ctype = download_bytes_from_url(candidate)
            if content:
                # nếu content là text base64 inside -> xử lý
                if ctype.startswith("text") or candidate.endswith(".base64"):
                    try:
                        txt = content.decode("utf-8", errors="ignore").strip()
                        img_bytes = base64.b64decode(_clean_base64(txt), validate=True)
                        out = _detect_and_save_bytes(img_bytes, out_base + f"_fromurl_{i}")
                        print("✅ Image saved from URL (text) ->", out)
                        return
                    except Exception:
                        pass
                # else treat as image bytes
                out = _detect_and_save_bytes(content, out_base + f"_fromurl_{i}")
                print("✅ Image saved from URL (bytes) ->", out)
                return
            else:
                print("⚠️ Không tải được URL, lưu debug và chờ.")
                with open(f"debug_fetch_{i}.json", "w", encoding="utf-8") as dbg:
                    json.dump(fetch_data, dbg, ensure_ascii=False, indent=2)
                time.sleep(sleep_sec)
                continue

        # Nếu candidate trông như base64 trực tiếp
        candidate_clean = _clean_base64(candidate)
        if len(candidate_clean) < 300:
            print(f"⚠️ Chuỗi base64 quá ngắn ({len(candidate_clean)} chars). Lưu debug và chờ.")
            with open(f"debug_fetch_{i}.json", "w", encoding="utf-8") as dbg:
                json.dump(fetch_data, dbg, ensure_ascii=False, indent=2)
            time.sleep(sleep_sec)
            continue

        try:
            img_bytes = base64.b64decode(candidate_clean, validate=True)
        except Exception:
            mod = len(candidate_clean) % 4
            if mod != 0:
                try:
                    img_bytes = base64.b64decode(candidate_clean + ("=" * (4 - mod)), validate=True)
                except Exception as e:
                    print("⚠️ Decode base64 thất bại:", e)
                    with open(f"debug_fetch_{i}.json", "w", encoding="utf-8") as dbg:
                        json.dump(fetch_data, dbg, ensure_ascii=False, indent=2)
                    time.sleep(sleep_sec)
                    continue
            else:
                print("⚠️ Decode base64 thất bại.")
                with open(f"debug_fetch_{i}.json", "w", encoding="utf-8") as dbg:
                    json.dump(fetch_data, dbg, ensure_ascii=False, indent=2)
                time.sleep(sleep_sec)
                continue

        out = _detect_and_save_bytes(img_bytes, out_base + f"_{i}")
        print("✅ Image saved:", out)
        return

    print("❌ Hết thời gian chờ — kiểm tra các file debug_fetch_*.json để biết chi tiết.")

if __name__ == "__main__":
    prompt_text = "Consistent characters: female like Boa Hancock (shoulder-length hair, beige sweater, small necklace) & male like Zoro (short black hair, navy jacket, white shirt); keep same face/hair/outfit/accessories across all scenes (same seed/reference) — Bus stop at dusk: Minh kneels and places a folded note near Linh’s hand, cool sunset light, 3:2, 35mm film, shallow DOF, cinematic color grading."
    generate_image_direct(prompt_text)
