import asyncio
import os
from telegram import Bot

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
bot = Bot(token=BOT_TOKEN)


async def send_telegram(message: str):
    """Gửi tin nhắn tới Telegram (async)."""
    if not BOT_TOKEN or not CHAT_ID:
        raise ValueError("⚠️ TELEGRAM_TOKEN hoặc CHAT_ID chưa được cấu hình")
    await bot.send_message(chat_id=CHAT_ID, text=message)


def send_telegram_safe(message: str):
    """
    Gửi tin nhắn Telegram an toàn cho cả sync & async context.
    - Nếu đang trong loop đang chạy → dùng run_coroutine_threadsafe
    - Nếu không có loop → dùng asyncio.run
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # Trường hợp gọi trong thread / async context
        future = asyncio.run_coroutine_threadsafe(send_telegram(message), loop)
        return future.result()
    else:
        # Trường hợp sync bình thường
        return asyncio.run(send_telegram(message))