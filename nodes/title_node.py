from langchain_core.messages import HumanMessage

def title_node(state):
    msg = HumanMessage(content=f"title_node blog:")
    outputs = {
        "text": "10 quán cà phê view đẹp ở Đà Lạt",
        "description": "Thưởng thức cà phê trong không gian lãng mạn và check-in với những góc chụp cực chill ở Đà Lạt."
    }
    return {
        "status": "done",
        "messages": [msg],
        "outputs": outputs
    }