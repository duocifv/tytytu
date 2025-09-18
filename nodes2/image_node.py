from langchain_core.messages import HumanMessage
import random

def image_node(state):
    msg = HumanMessage(content="Ảnh minh họa")
    return {"messages": [msg]}
