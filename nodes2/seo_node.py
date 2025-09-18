from langchain_core.messages import HumanMessage
import random
from brain.llm_tools import llm_tools

def seo_node(state):
    text = state.get("content", "")
    resp = llm_tools.invoke(f"Phân tích SEO cho nội dung: {text}")
    score = random.randint(50, 100)

    msg = HumanMessage(
        content=f"SEO analysis done (score={score})\nTool response: {resp}"
    )
    return {"messages": [msg], "seo_score": score}
