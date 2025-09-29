from langchain_core.messages import HumanMessage
from nodes.human_reference_node import human_reference_node
from nodes.data_analysis_node import data_analysis_node
from nodes.content_node import content_node
from nodes.research_node import research_node   # node tham khảo
from services.daily_hexagram_service import DailyHexagramService
import json

if __name__ == "__main__":
    # State mẫu chuẩn
    state = {
        "topic": "Thiên – Địa – Nhân data",
        "messages": [HumanMessage(content="Demo run")],
    }
    svc = DailyHexagramService()

    # Gọi data_analysis_node
    result = data_analysis_node(state)
    print("📌 1/data_analysis_node output:", result.get("outputs"))
    que= result.get("outputs")

    node = svc.create_daily_node(que["thien"], que["dia"], que["nhan"], que["key_event"])
    print("📌 2/create_daily_node output:", node)

    data = human_reference_node(node)
    print("📌 3/human_reference_node output:", data)
    #In ra kết quả
    
