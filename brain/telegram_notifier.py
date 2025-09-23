import asyncio
from services.telegram_service import send_telegram


def notify(message: str):
    """
    Gửi thông báo Telegram an toàn cho cả async và sync context.
    - Nếu đã có event loop → dùng run_coroutine_threadsafe
    - Nếu chưa có → dùng asyncio.run()
    """
    try:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            future = asyncio.run_coroutine_threadsafe(send_telegram(message), loop)
            return future.result()
        else:
            return asyncio.run(send_telegram(message))
    except Exception as e:
        # Không làm crash workflow chính nếu gửi Telegram thất bại
        print(f"⚠️ Telegram notify failed: {e}")


def notify_node_status(node_name: str, status: str):
    notify(f"📌 Node *{node_name}* → {status}")


def notify_blog_published(title: str):
    notify(f"✅ Blog đã publish: {title}")
