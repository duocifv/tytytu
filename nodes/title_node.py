from langchain_core.messages import HumanMessage

def title_node(state):
    keywords = state["status"].get("node_data", {}).get("keyword", {}).get("keywords", [])
    if not keywords:
        keywords = ["Demo keyword"]

    # Lấy keyword đầu tiên để tạo tiêu đề
    draft_title = f"How to use {keywords[0]} effectively"

    msg = HumanMessage(content=f"Generated title: {draft_title}")

    return {
        "status": "done",
        "messages": [msg],
        "title": draft_title
    }
