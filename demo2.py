from langchain_core.messages import HumanMessage
from nodes.content_node import content_node
from nodes.research_node import research_node   # ✅ import node bạn vừa viết

if __name__ == "__main__":
    # State mẫu chuẩn
    state = {
        "topic": "Sức khỏe",
        "status": "done",
        "messages": [HumanMessage(content="Generated ideas & I-Ching interpretation for topic 'Sức khỏe'")],
        "outputs": {
            "idea": [
                "Bí quyết phòng bệnh hiệu quả cho gia đình bạn: Cẩm nang toàn diện.",
                "Dinh dưỡng chuẩn Bộ Y tế: Thực đơn khỏe mạnh cho cả nhà.",
                "Chăm sóc sức khỏe tinh thần: Dấu hiệu & cách tự hỗ trợ tại nhà."
            ],
            "title": "Cẩm Nang Sức Khỏe Gia Đình: Phòng Bệnh & Chăm Sóc Toàn Diện",
            "meta_description": "Cẩm nang sức khỏe gia đình toàn diện nhất 2024. Bí quyết phòng bệnh, chăm sóc thể chất, tinh thần cho mọi thành viên."
        },
        "retries": {},
        "status": {"sequence": 1, "step": "idea", "done_nodes": ["keyword", "idea"]}
    }

    # Gọi content_node
    content = research_node(state)

    # In ra kết quả
    print("content_node output:", content)
