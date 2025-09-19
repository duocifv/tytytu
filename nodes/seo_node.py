from langchain_core.messages import HumanMessage
from brain.llm_tools import llm_tools

def seo_node(state):
    # Lấy dữ liệu từ node_data hoặc results
    content = (
        state["status"].get("node_data", {}).get("content", {}).get("content")
        or state["results"].get("content", "")
    )
    title = (
        state["status"].get("node_data", {}).get("title", {}).get("title")
        or state["results"].get("title", "")
    )

    # Nếu thiếu content thì fail
    if not content:
        return {
            "status": "failed",
            "messages": [HumanMessage(content="❌ No content to analyze for SEO")],
        }

    # Tính điểm SEO & meta
    seo_score = (len(content) + len(title)) % 100
    meta = {
        "title": title or "Untitled",
        "description": (content[:150] + "...") if content else ""
    }

    # Gọi tool phân tích
    resp = llm_tools.invoke(f"Phân tích SEO cho nội dung: {content[:300]}")

    msg = HumanMessage(
        content=f"SEO analysis done (score={seo_score})\nTool response: {resp}"
    )

    return {
        "status": "done",
        "messages": [msg],
        "seo_score": seo_score,
        "meta": meta
    }
