from langchain_core.messages import HumanMessage

def publish_node(state):
    msg = HumanMessage(content="Bài viết đã xuất bản")
    return {"messages": [msg]}
