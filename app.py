import os
import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from telegram import Update, Bot
from telegram.ext import Application, MessageHandler as TGMessageHandler, filters, CommandHandler
from handlers.message_handler import MessageHandler as MessageHandlerClass
from schedulers.scheduler import init_scheduler

# -----------------------------
# Logging & env
# -----------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app")
load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN missing in .env")

PORT = int(os.environ.get("PORT", 10000))
WEBHOOK_URL = os.getenv("WEBHOOK")

# -----------------------------
# Telegram bot setup
# -----------------------------
handler = MessageHandlerClass()
bot_app = Application.builder().token(BOT_TOKEN).build()
bot_app.add_handler(TGMessageHandler(filters.TEXT & ~filters.COMMAND, handler.handle_message))
bot_app.add_handler(CommandHandler("start", handler.handle_start))
bot_app.add_handler(CommandHandler("help", handler.handle_help))

scheduler = None

# -----------------------------
# Lifespan
# -----------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    global scheduler
    logger.info("🚀 Startup...")

    try:
        await bot_app.initialize()
        await bot_app.start()
        logger.info("🟢 Telegram bot started")

        if WEBHOOK_URL:
            await bot_app.bot.set_webhook(WEBHOOK_URL)
            logger.info("🌍 Webhook set: %s", WEBHOOK_URL)

        scheduler = init_scheduler()
        yield

    finally:
        logger.info("🛑 Shutdown...")
        if scheduler and scheduler.running:
            scheduler.shutdown(wait=False)
            logger.info("⏰ Scheduler stopped")
        await bot_app.stop()
        await bot_app.shutdown()
        logger.info("🔴 Telegram bot stopped")

app = FastAPI(lifespan=lifespan)

# -----------------------------
# Endpoints
# -----------------------------
@app.get("/health")
@app.head("/health")
async def health():
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"service": "telegram-bot", "status": "running"}

@app.post("/webhook")
async def telegram_webhook(request: Request):
    try:
        data = await request.json()
    except Exception:
        return {"ok": False, "error": "invalid JSON"}

    update = Update.de_json(data, Bot(BOT_TOKEN))
    await bot_app.update_queue.put(update)
    return {"ok": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=PORT, log_level="info")
