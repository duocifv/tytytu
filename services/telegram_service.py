# services/telegram_service.py
import os
import asyncio
from dotenv import load_dotenv
from telegram import Bot

load_dotenv() 

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
bot = Bot(token=BOT_TOKEN)

async def send_telegram(message: str):
    """Gửi tin nhắn tới Telegram (async)."""
    if not BOT_TOKEN or not CHAT_ID:
        raise ValueError("⚠️ TELEGRAM_TOKEN hoặc CHAT_ID chưa được cấu hình")
    await bot.send_message(chat_id=CHAT_ID, text=message)

# Nếu muốn gọi trong sync context:
def send_telegram_sync(message: str):
    asyncio.run(send_telegram(message))
