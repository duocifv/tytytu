# nodes2/notify_node.py
from langchain_core.messages import HumanMessage

def telegram_node(state):
    try:
        title = state["status"].get("node_data", {}).get("title", {}).get("title", "")
        url = state["results"]["outputs"].get("publish", {}).get("url", "")

        # Gửi sang Facebook, Telegram, v.v...
        print(f"🚀 Notify: Published '{title}' at {url}")
        msg = HumanMessage(content=f"🔔 Notified external services: {title}")
        return {"status": "done", "messages": [msg]}
    except Exception as e:
        return {"status": "failed", "messages": [HumanMessage(content=f"Notify error: {e}")]}
