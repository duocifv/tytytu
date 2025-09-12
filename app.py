import os
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from telegram import Update, Bot
from telegram.ext import Application, MessageHandler, filters, CommandHandler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from handlers.message_handler import MessageHandler as MessageHandlerClass

# -----------------------------
# Logging và environment
# -----------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN missing in .env")

PORT = int(os.environ.get("PORT", 10000))
WEBHOOK_URL = os.getenv("WEBHOOK")  # ví dụ: https://yourdomain.com/webhook

# -----------------------------
# FastAPI app và handler
# -----------------------------
app = FastAPI()
handler = MessageHandlerClass()

# Init Telegram bot Application (no polling)
bot_app = Application.builder().token(BOT_TOKEN).build()

# Add message handlers
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handler.handle_message))
bot_app.add_handler(CommandHandler("start", handler.handle_start))
bot_app.add_handler(CommandHandler("help", handler.handle_help))

# -----------------------------
# APScheduler
# -----------------------------
scheduler = AsyncIOScheduler()

async def scheduled_task_1():
    """Task đơn giản chỉ in log ra"""
    logger.info("⏰ Running scheduled task 1...")

# Schedule task mỗi 5 phút từ 5:00 đến 20:00
scheduler.add_job(scheduled_task_1, CronTrigger(hour="5-20", minute="*/5"))

# -----------------------------
# Startup event
# -----------------------------
@app.on_event("startup")
async def on_startup():
    # Set webhook nếu có
    if WEBHOOK_URL:
        logger.info(f"🌍 Setting webhook to: {WEBHOOK_URL}")
        await bot_app.initialize()
        await bot_app.start()
        await bot_app.bot.set_webhook(WEBHOOK_URL)
    
    # Start scheduler
    if not scheduler.running:
        scheduler.start()
        logger.info("⏰ Scheduler started")

# -----------------------------
# Shutdown event
# -----------------------------
@app.on_event("shutdown")
async def on_shutdown():
    logger.info("🛑 FastAPI server is shutting down...")
    
    # Không xóa webhook và stop bot để bot chạy liên tục
    if 'scheduler' in globals() and scheduler.running:
        scheduler.shutdown()
        logger.info("⏰ Scheduler stopped")

# -----------------------------
# Webhook endpoint
# -----------------------------
@app.post("/webhook")
async def telegram_webhook(request: Request):
    try:
        data = await request.json()
    except Exception:
        logger.warning("Webhook called with empty or invalid JSON")
        return {"ok": False, "error": "invalid JSON"}
    
    update = Update.de_json(data, Bot(BOT_TOKEN))
    await bot_app.update_queue.put(update)
    return {"ok": True}

# -----------------------------
# Run FastAPI via Uvicorn
# -----------------------------
if __name__ == "__main__":
    import uvicorn
    logger.info("🤖 Starting FastAPI + Telegram webhook + APScheduler...")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
