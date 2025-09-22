# nodes/publish_node.py
import requests
from langchain_core.messages import HumanMessage
from services.facebook_service import FacebookPipeline


def publish_node(state):
    try:
        pipeline = FacebookPipeline()
        result = pipeline.run(state)   # để pipeline lo format + publish
        published = result.get("published", False)
        msg_text = result.get("message", "❌ Unknown error")

        # Nếu publish thành công thì trigger webhook
        if published:
            try:
                webhook_url = "https://api.cloudflare.com/client/v4/pages/webhooks/deploy_hooks/7b2f2148-293a-4589-b22b-e7062700ceeb"
                resp = requests.post(webhook_url, data="")  # tương đương curl -d ""
                if resp.status_code == 200:
                    msg_text += "\n✅ Cloudflare Pages deploy triggered"
                else:
                    msg_text += f"\n⚠️ Deploy hook failed: {resp.status_code} {resp.text}"
            except Exception as e:
                msg_text += f"\n⚠️ Error calling deploy hook: {e}"

    except Exception as e:
        published = False
        msg_text = f"❌ Error publishing to Facebook: {e}"

    msg = HumanMessage(content=msg_text)

    return {
        "status": "done",
        "messages": [msg],
        "published": published
    }
