from langchain_core.messages import HumanMessage

def research_node(state):
    msg = HumanMessage(content=f"research_node blog:")
    outputs = {
      "sources": [
        {"title": "Top 10 món ăn đặc sản Đà Lạt", "url": "https://..."},
        {"title": "Checklist cảnh đẹp Đà Lạt 2025", "url": "https://..."}
      ],
      "insights": [
        "Ẩm thực Đà Lạt nổi bật với lẩu gà lá é, bánh căn, nem nướng.",
        "Các điểm check-in hot: Hồ Xuân Hương, quảng trường Lâm Viên, đồi chè Cầu Đất."
      ]
    }
    return {
        "status": "done",
        "messages": [msg],
        "outputs": outputs
    }