from langchain_core.messages import HumanMessage

def title_node(state):
    print(f"title_node", state)
    msg = HumanMessage(content=f"title_node blog:")
    outputs = {
        "text": "Top 7 địa điểm check-in hot ở Đà Lạt",
        "description": "Khám phá những địa điểm sống ảo được giới trẻ yêu thích nhất khi đến Đà Lạt."
    }
    return {
        "status": "done",
        "messages": [msg],
        "outputs": outputs
    }