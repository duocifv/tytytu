from langchain_core.messages import HumanMessage

def idea_node(state):
    msg = HumanMessage(content=f"idea_node blog:")
    outputs = {
        "blog_posts": [
            "Khám phá ẩm thực Đà Lạt: 5 món nhất định phải thử",
            "Top 7 địa điểm check-in hot tại Đà Lạt 2025"
        ],
        "itinerary": [
            "Gợi ý lịch trình Đà Lạt 3N2Đ: Ăn gì, chơi gì, ở đâu?"
        ]
    }
    return {
        "status": "done",
        "messages": [msg],
        "outputs": outputs
    }