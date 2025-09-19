import asyncio
from services.telegram_service import send_telegram, send_telegram_sync


def notify(message: str):
    """
    Hàm tiện lợi để gửi thông báo Telegram.
    - Nếu đang ở async context → dùng await send_telegram()
    - Nếu đang ở sync context → dùng send_telegram_sync()
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        return send_telegram(message)
    else:
        return send_telegram_sync(message)


def notify_node_status(node_name: str, status: str):
    """Gửi thông báo trạng thái Node lên Telegram."""
    notify(f"📌 Node *{node_name}* → {status}")


def notify_blog_published(title: str):
    """Gửi thông báo khi blog được publish."""
    msg = f"✅ Blog đã publish: {title}"
    notify(msg)
