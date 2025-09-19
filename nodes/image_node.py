from langchain_core.messages import HumanMessage

def image_node(state):
    content = state["status"].get("node_data", {}).get("content", {}).get("content", "")
    
    # Giả lập chia content thành các đoạn nhỏ
    sections = content.split(". ")[:3]  # 3 hình ảnh minh họa
    
    image_urls = [f"https://example.com/images/section{i}.png" for i, sec in enumerate(sections, 1)]
    msg = HumanMessage(content=f"Generated images for sections: {', '.join(image_urls)}")

    return {
        "status": "done",
        "messages": [msg],
        "image_urls": image_urls
    }
