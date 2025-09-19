from langchain_core.messages import HumanMessage

def publish_node(state):
    title = state["status"].get("node_data", {}).get("title", {}).get("title", "")
    images = state["status"].get("node_data", {}).get("image", {}).get("image_urls", [])
    meta = state["status"].get("node_data", {}).get("seo", {}).get("meta", {})

    msg = HumanMessage(content=f"Published blog: {title} | Images: {images} | SEO meta: {meta}")

    return {
        "status": "done",
        "messages": [msg],
        "published": True
    }
