import random
import time
import requests
import traceback
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from langchain.output_parsers import PydanticOutputParser
from services.groq_service import chat_groq
from services.seo_service import SEOContentPipeline
import feedparser  # để parse RSS Google News


MAX_NEWS_LENGTH = 8000  # giới hạn ký tự cho field news


# -----------------------------
# 1️⃣ Định nghĩa schema output (4 field)
# -----------------------------
class DataAnalysisOutput(BaseModel):
    thien: str
    dia: str
    nhan: str
    key_event: str


# -----------------------------
# 2️⃣ Thu thập dữ liệu đa nguồn
# -----------------------------
def collect_data():
    results = {"heaven": {}, "earth": {}, "human": {}}

    try:
        # Thiên – NOAA Kp Index
        try:
            kp_url = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"
            kp_data = requests.get(kp_url, timeout=10).json()
            results["heaven"]["kp_index"] = kp_data[-1] if kp_data else {}
        except Exception as e:
            results["heaven"]["error"] = str(e)

        # Địa – USGS Earthquakes
        try:
            quake_url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"
            quake_data = requests.get(quake_url, timeout=10).json()
            results["earth"]["earthquakes"] = quake_data.get("features", [])[:5]
        except Exception as e:
            results["earth"]["error"] = str(e)

        # Nhân – Google News RSS
        try:
            news_url = "https://news.google.com/rss?hl=vi&gl=VN&ceid=VN:vi"
            feed = feedparser.parse(news_url)
            news_items = []
            for entry in feed.entries[:50]:  # gom 50 tin mới nhất
                news_items.append(f"{entry.title} - {entry.link}")
            news_text = "\n".join(news_items)
            # Cắt giới hạn ký tự
            if len(news_text) > MAX_NEWS_LENGTH:
                news_text = news_text[:MAX_NEWS_LENGTH] + "\n[...]"
            results["human"]["news"] = news_text

           # -----------------------------
            # SEO / Trends (thay thế phần gốc)
            # -----------------------------
            seo = SEOContentPipeline()
            seed_keywords = ["thiên tai", "dịch bệnh", "kinh tế", "thời sự"]
            seo_data = {}

            RETRY_COUNT = 3
            DELAY_BETWEEN_REQUESTS = 1.5  # giây

            def safe_fetch(fetch_fn):
                """Thử lại nhiều lần nếu fetch lỗi"""
                for i in range(RETRY_COUNT):
                    try:
                        return fetch_fn()
                    except Exception as e:
                        wait = 2 ** i + random.random()
                        time.sleep(wait)
                return {"status": "error", "error": "Failed after retries"}

            for kw in seed_keywords:
                seo_data[kw] = {}

                # Lấy related keywords
                seo_data[kw]["related_keywords"] = safe_fetch(lambda: seo.fetch_keywords(kw))
                time.sleep(DELAY_BETWEEN_REQUESTS)

                # Lấy competitor titles
                seo_data[kw]["competitor_titles"] = safe_fetch(lambda: seo.fetch_competitor_titles(kw))
                time.sleep(DELAY_BETWEEN_REQUESTS)

            results["human"]["seo_trends"] = seo_data

        except Exception as e:
            results["human"]["error"] = str(e)

    except Exception as e:
        results["error"] = str(e)

    return results


# -----------------------------
# 3️⃣ Node chính: gom + phân tích
# -----------------------------
def data_analysis_node(state: dict) -> dict:
    topic = state.get("topic", "Tổng hợp Thiên – Địa – Nhân")

    # 1. Gom dữ liệu thô
    raw_data = collect_data()
    print("📌 1 - data_analysis_node - ok", raw_data)
    # 2. Chuẩn bị parser JSON (4 trường)
    parser = PydanticOutputParser(pydantic_object=DataAnalysisOutput)

    # 3. Prompt Groq
    safe_state = {k: ("..." if k == "messages" else v) for k, v in state.items()}
    prompt = (
        f"Dữ liệu state: {safe_state}\n\n"
        f"Chủ đề: {topic}\n\n"
        f"Dữ liệu thu thập:\n{raw_data}\n\n"
        "Bạn là một chuyên gia phân tích dữ liệu đa chiều.\n"
        "Hãy đọc kỹ dữ liệu trên và phân tích chi tiết theo 4 yếu tố:\n\n"
        "1. Thiên (Heaven / Thiên văn – Khí quyển – Vũ trụ)\n"
        "- Phân tích dữ liệu bão từ, hoạt động mặt trời, khí quyển, hiện tượng vũ trụ.\n"
        "- Nhận định tác động tới khí hậu, viễn thông, vệ tinh, hàng không.\n\n"
        "2. Địa (Earth / Địa chất – Địa lý – Môi trường)\n"
        "- Phân tích dữ liệu địa chấn, động đất, núi lửa, biến đổi môi trường, khí hậu.\n"
        "- Làm rõ khu vực chịu tác động, mức độ nguy hiểm và hệ quả lâu dài.\n\n"
        "3. Nhân (Human / Xã hội – Y khoa – Đời sống)\n"
        "- Phân tích tác động tới con người: sức khỏe cộng đồng, y tế, xã hội, kinh tế, chính trị.\n"
        "- Nếu có thiên tai/dịch bệnh/khủng hoảng, làm rõ ảnh hưởng tới cộng đồng.\n\n"
        "4. Key Event (Sự kiện chính nổi bật nhất)\n"
        "- Xác định sự kiện quan trọng nhất trong ngày.\n"
        "- Giải thích tại sao sự kiện này nổi bật và liên hệ tới Thiên – Địa – Nhân.\n\n"
        "---\n\n"
        "🎯 Yêu cầu xuất JSON\n"
        "Trả về đúng định dạng JSON với 4 trường:\n\n"
        "{\n"
        '  "thien": "Phân tích chi tiết Thiên...",\n'
        '  "dia": "Phân tích chi tiết Địa...",\n'
        '  "nhan": "Phân tích chi tiết Nhân...",\n'
        '  "key_event": "Mô tả sự kiện chính nổi bật nhất."\n'
        "}\n\n"
        f"Trả về JSON đúng format:\n{parser.get_format_instructions()}"
    )

    # 4. Gọi Groq GPT
    try:
        raw_result = chat_groq(prompt)
        result = parser.parse(raw_result)
    except Exception as e:
        traceback.print_exc()
        result = DataAnalysisOutput(
            thien="Không lấy được",
            dia="Không lấy được",
            nhan="Không lấy được",
            key_event="Error",
        )

    # print("📌 1 - data_analysis_node - ok", result.model_dump())
    msg = HumanMessage(content=f"data_analysis_node completed for '{topic}'")
    return {
        "status": "done",
        "messages": [msg],
        "daily": result.model_dump(),
    }


# -----------------------------
# 5️⃣ Example chạy thử
# -----------------------------
if __name__ == "__main__":
    state = {"topic": "Tổng hợp Thiên – Địa – Nhân"}
    output = data_analysis_node(state)
    print(output)
