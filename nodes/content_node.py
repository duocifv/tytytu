from langchain_core.messages import HumanMessage

def content_node(state):
    msg = HumanMessage(content=f"content_node blog:")
    outputs = {
        "body": "...",
        "excerpt": "Danh sách 7 địa điểm check-in hot ở Đà Lạt 2025.",
        "tags": ["Đà Lạt", "Du lịch", "Check-in", "2025"]
    }
    return {
        "status": "done",
        "messages": [msg],
        "outputs": outputs
    }