import requests
import traceback
from langchain_core.messages import HumanMessage
from pydantic import BaseModel
from langchain.output_parsers import PydanticOutputParser
from services.groq_service import chat_groq  # Groq GPT


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

        # Nhân – Google News RSS (dùng WebBaseLoader)
        try:
            from langchain_community.document_loaders import WebBaseLoader

            news_url = "https://news.google.com/rss?hl=vi&gl=VN&ceid=VN:vi"
            loader = WebBaseLoader(news_url)
            docs = loader.load()
            news_text = "\n\n".join([d.page_content for d in docs])
            results["human"]["news"] = news_text[:2000]  # lấy gọn 2000 ký tự
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
        "- Nếu có thiên tai/dịch bệnh/khủng hoảng, hãy làm rõ ảnh hưởng tới cộng đồng.\n\n"
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
        print(f"raw_result------------------->" , raw_result)
        result = parser.parse(raw_result)
    except Exception as e:
        traceback.print_exc()
        result = DataAnalysisOutput(
            thien="Không lấy được",
            dia="Không lấy được",
            nhan="Không lấy được",
            key_event="Error",
        )

    msg = HumanMessage(content=f"data_analysis_node completed for '{topic}'")
    return {
        "status": "done",
        "messages": [msg],
        "daily": result.model_dump(),
    }
