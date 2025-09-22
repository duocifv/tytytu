from langchain_core.messages import HumanMessage

def insight_node(state):
    """
    ✅ Node phân tích mối quan tâm người dùng, tạo insights.
    """
    print(f"interest_node", state)
    msg = HumanMessage(content=f"interest_node blog:")
    outputs = {
        "interest": "Du lịch trải nghiệm",
        "audience": "Người trẻ thích phượt, khám phá địa điểm mới",
        "pain_points": [
        "Chưa rõ mùa đẹp để đi",
        "Thiếu thông tin về đặc sản",
        "Không biết địa điểm check-in nổi bật"
        ]
    }
    return {
        "status": "done",
        "messages": [msg],
        "outputs": outputs
    }