from langchain_core.messages import HumanMessage

def title_node(state):
    msg = HumanMessage(content="Tiêu đề bài viết tự động")
    return {"messages": [msg]}
