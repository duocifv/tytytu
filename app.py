# app.py
import os
import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from telegram import Update, Bot
from telegram.ext import (
    Application,
    MessageHandler as TGMessageHandler,
    filters,
    CommandHandler,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from handlers.message_handler import MessageHandler as MessageHandlerClass

# -----------------------------
# Logging và env
# -----------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app")
load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN missing in .env")

PORT = int(os.environ.get("PORT", 10000))
WEBHOOK_URL = os.getenv("WEBHOOK")  # e.g. https://yourdomain.com/webhook

# -----------------------------
# App, handler, bot, scheduler
# -----------------------------
handler = MessageHandlerClass()
bot_app = Application.builder().token(BOT_TOKEN).build()

# Add telegram handlers (use alias TGMessageHandler to avoid name conflict)
bot_app.add_handler(TGMessageHandler(filters.TEXT & ~filters.COMMAND, handler.handle_message))
bot_app.add_handler(CommandHandler("start", handler.handle_start))
bot_app.add_handler(CommandHandler("help", handler.handle_help))

scheduler = AsyncIOScheduler()


async def scheduled_task_1():
    """Task đơn giản chỉ in log ra"""
    logger.info("⏰ Running scheduled task 1...")


# -----------------------------
# Lifespan (startup / shutdown)
# -----------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- startup ---
    logger.info("🚀 Lifespan startup: initializing bot and scheduler...")
    try:
        # initialize and start telegram Application
        try:
            await bot_app.initialize()
            await bot_app.start()
            logger.info("🟢 Telegram Application started")
        except Exception as e:
            logger.exception("Failed to initialize/start Telegram Application: %s", e)

        # set webhook if provided (safe to call even if already set)
        if WEBHOOK_URL:
            try:
                await bot_app.bot.set_webhook(WEBHOOK_URL)
                logger.info("🌍 Webhook set to: %s", WEBHOOK_URL)
            except Exception as e:
                logger.exception("Failed to set webhook: %s", e)

        # start scheduler and add job AFTER starting scheduler to avoid tentative warnings
        if not scheduler.running:
            scheduler.start()
            logger.info("⏰ Scheduler started")
        # Ensure we don't add duplicate jobs on reload: remove if exists then add
        try:
            if "scheduled_task_1" in [job.id for job in scheduler.get_jobs()]:
                logger.debug("Scheduled job already exists - skipping add")
            else:
                scheduler.add_job(
                    scheduled_task_1,
                    CronTrigger(hour="5-20", minute="*/5"),
                    id="scheduled_task_1",
                    replace_existing=True,
                )
                logger.info("✅ Scheduled job 'scheduled_task_1' added")
        except Exception:
            # fallback: always try add (safe)
            scheduler.add_job(
                scheduled_task_1,
                CronTrigger(hour="5-20", minute="*/5"),
                id="scheduled_task_1",
                replace_existing=True,
            )
            logger.info("✅ Scheduled job 'scheduled_task_1' added (fallback)")

        yield  # <-- FastAPI runs while yielded

    finally:
        # --- shutdown ---
        logger.info("🛑 Lifespan shutdown: cleaning up...")
        # DO NOT delete webhook here (we want webhook to persist)
        # stop scheduler if running
        try:
            if scheduler.running:
                scheduler.shutdown(wait=False)
                logger.info("⏰ Scheduler stopped")
        except Exception as e:
            logger.exception("Error shutting down scheduler: %s", e)

        # stop the telegram application gracefully (but don't delete webhook)
        try:
            await bot_app.stop()
            await bot_app.shutdown()
            logger.info("🔴 Telegram Application stopped")
        except Exception as e:
            logger.exception("Error stopping Telegram Application: %s", e)


app = FastAPI(lifespan=lifespan)

# -----------------------------
# Health & root endpoints
# -----------------------------
@app.get("/health")
@app.head("/health")
async def health():
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"service": "telegram-bot", "status": "running"}

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

    # Use Bot(BOT_TOKEN) or bot_app.bot - both ok; using explicit Bot for safety
    update = Update.de_json(data, Bot(BOT_TOKEN))
    # Put update into Application's update_queue so handlers process it
    await bot_app.update_queue.put(update)
    return {"ok": True}

# -----------------------------
# Run by direct python (dev convenience)
# -----------------------------
if __name__ == "__main__":
    import uvicorn

    logger.info("🤖 Starting FastAPI + Telegram webhook + APScheduler (dev)...")
    # On deployment platforms like Render, use their provided $PORT
    uvicorn.run("app:app", host="0.0.0.0", port=PORT, log_level="info")
