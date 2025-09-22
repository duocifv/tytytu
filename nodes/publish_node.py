# nodes/publish_node.py
from langchain_core.messages import HumanMessage
from services.facebook_service import FacebookPipeline


def publish_node(state):
    try:
        pipeline = FacebookPipeline()
        result = pipeline.run(state)   # để pipeline lo format + publish
        published = result.get("published", False)
        msg_text = result.get("message", "❌ Unknown error")
    except Exception as e:
        published = False
        msg_text = f"❌ Error publishing to Facebook: {e}"

    msg = HumanMessage(content=msg_text)

    return {
        "status": "done",
        "messages": [msg],
        "published": published
    }
