from langchain_core.messages import HumanMessage
from tools2.content_length_tool import content_length_tool

def content_node(state):
    draft = "Demo content"
    length = content_length_tool.invoke({"text": draft}) 
    msg = HumanMessage(content=f"Draft length = {length}")
    
    return {
        "messages": [msg],   # luôn có key messages
        "length": length     # bạn vẫn có thể thêm data phụ
    }
