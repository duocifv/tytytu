from langchain_core.messages import HumanMessage

def content_node(state):
    msg = HumanMessage(content=f"content_node blog:")
    outputs = {
        "body": "7 địa điểm check-in hot Đà Lạt 2025 gồm: Horizon Coffee view săn mây, Kombi Land sa mạc xương rồng, Đồi Vô Ảnh 2.0 gương khổng lồ, Làng Boho Valley phong cách Bohemian, cầu gỗ săn mây Trại Mát, Ga Đà Lạt Retro và rừng thông Tà Nung lãng mạn.",
        "excerpt": "Danh sách 7 địa điểm check-in hot ở Đà Lạt 2025.",
        "tags": ["Đà Lạt", "Du lịch", "Check-in", "2025"]
    }
    return {
        "status": "done",
        "messages": [msg],
        "outputs": outputs
    }