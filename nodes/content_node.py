from langchain_core.messages import HumanMessage

def content_node(state):
    msg = HumanMessage(content=f"content_node blog:")
    outputs = {
        "body": "Khám phá 10 quán cà phê view đẹp nhất Đà Lạt 2025 như Tiệm Cà Phê Túi Mơ To, Dalat Mountain View, Panorama Café, Cầu Đất Farm, In The Forest Dalat, Kokoro Café, The Married Beans, Tiệm Cafe Tháng Ba, Still Café và An Cafe. Đây là những điểm hẹn vừa thưởng thức cà phê vừa ngắm cảnh núi rừng lãng mạn.",
        "excerpt": "Danh sách 10 quán cà phê view đẹp ở Đà Lạt 2025.",
        "tags": ["Đà Lạt", "Cà phê", "View đẹp", "2025"]
    }
    return {
        "status": "done",
        "messages": [msg],
        "outputs": outputs
    }