# nodes/publish_node.py
import requests
import traceback
from langchain_core.messages import HumanMessage
from services.facebook_service import FacebookPipeline


def publish_node(state):
    """
    Publish bài viết đồng thời lên Facebook và Webhook.
    Trả về published = True nếu ít nhất một kênh thành công.
    """
    print(f"publish_node called with state:", state)

    outputs = state.get("outputs", {})
    publish_info = outputs.get("publish", {})

    # 🔒 Chặn publish nếu đã chạy rồi
    if publish_info.get("done"):
        msg = HumanMessage(content="⏭️ Bỏ qua publish vì đã đăng trước đó")
        return {
            "status": "skipped",
            "messages": [msg],
            "published": True,
            "outputs": publish_info,
        }

    fb_success = False
    web_success = False
    msg_texts = []

    # -------------------------------
    # 1. Đăng bài Facebook
    # -------------------------------
    try:
        pipeline = FacebookPipeline()
        fb_result = pipeline.run(state) or {}
        print("Facebook publish result:", fb_result)

        fb_success = fb_result.get("published", False)
        fb_message = fb_result.get("message", "✅ Facebook done" if fb_success else "❌ Facebook failed")
        msg_texts.append(f"Facebook: {fb_message}")
    except Exception as e:
        fb_success = False
        msg_texts.append(f"Facebook error: {e}")
        traceback.print_exc()

    # -------------------------------
    # 2. Gọi Webhook Cloudflare
    # -------------------------------
    try:
        webhook_url = "https://api.cloudflare.com/client/v4/pages/webhooks/deploy_hooks/7b2f2148-293a-4589-b22b-e7062700ceeb"
        resp = requests.post(webhook_url, json={})
        print("Webhook response:", resp.status_code, resp.text)

        if resp.status_code == 200:
            web_success = True
            msg_texts.append("✅ Web deployed successfully")
        else:
            web_success = False
            msg_texts.append(f"⚠️ Web deploy failed: {resp.status_code} {resp.text}")
    except Exception as e:
        web_success = False
        msg_texts.append(f"Webhook error: {e}")
        traceback.print_exc()

    # -------------------------------
    # 3. Trả về published = True nếu ít nhất một kênh thành công
    # -------------------------------
    published = fb_success or web_success
    msg = HumanMessage(content="\n".join(msg_texts))

    return {
        "status": "done",
        "messages": [msg],
        "published": published,
        "outputs": {
            "publish": {
                "done": True,
                "details": {
                    "facebook": fb_success,
                    "webhook": web_success
                }
            }
        }
    }
