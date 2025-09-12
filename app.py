import os
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from telegram import Update, Bot
from telegram.ext import Application, MessageHandler, filters, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from handlers.message_handler import MessageHandler as MessageHandlerClass
from flows.telegram_flow import process_message_flow

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN missing in .env")

PORT = int(os.environ.get("PORT", 10000))

# -----------------------------
# FastAPI app
# -----------------------------
app = FastAPI()
handler = MessageHandlerClass()

# Init Telegram bot Application (no polling)
bot_app = Application.builder().token(BOT_TOKEN).build()

# Add message handlers
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handler.handle_message))
bot_app.add_handler(CommandHandler("start", handler.handle_start))
bot_app.add_handler(CommandHandler("help", handler.handle_help))

# Add startup event to set up the webhook
@app.on_event("startup")
async def on_startup():
    webhook_url = os.getenv("webhook")
    if webhook_url:
        logger.info(f"🌍 Setting webhook to: {webhook_url}")
        await bot_app.initialize()
        await bot_app.start()
        await bot_app.bot.set_webhook(webhook_url)
    
    # Start the scheduler
    if not scheduler.running:
        scheduler.start()
        logger.info("⏰ Scheduler started")

@app.on_event("shutdown")
async def on_shutdown():
    logger.info("🛑 Shutting down...")
    
    # Remove webhook
    if 'bot_app' in globals():
        await bot_app.bot.delete_webhook()
        await bot_app.stop()
        await bot_app.shutdown()
    
    # Shutdown scheduler
    if 'scheduler' in globals() and scheduler.running:
        scheduler.shutdown()
        logger.info("⏰ Scheduler stopped")

# -----------------------------
# Webhook endpoint
# -----------------------------
@app.post("webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, Bot(BOT_TOKEN))
    # Đẩy update vào bot
    await bot_app.update_queue.put(update)
    return {"ok": True}

# -----------------------------
# APScheduler tasks
# -----------------------------
# Initialize the async scheduler
scheduler = AsyncIOScheduler()

async def scheduled_task_1():
    """Example scheduled task that logs user statistics"""
    try:
        logger.info("📊 Running scheduled task: User statistics")
        if hasattr(handler, 'user_sessions'):
            active_sessions = len(handler.user_sessions)
            logger.info(f"👥 Active user sessions: {active_sessions}")
            
            # Log some basic statistics
            if active_sessions > 0:
                usernames = [
                    f"@{session.get('username', 'unknown')}" 
                    for session in handler.user_sessions.values()
                    if session.get('username')
                ]
                if usernames:
                    logger.info(f"   Active users: {', '.join(usernames[:5])}" + 
                               ("..." if len(usernames) > 5 else ""))
    except Exception as e:
        logger.error(f"❌ Error in scheduled task: {e}", exc_info=True)

# Schedule tasks to run every 5 minutes from 5:00 to 20:00
scheduler.add_job(scheduled_task_1, CronTrigger(hour="5-20", minute="*/5"))

# -----------------------------
# Run FastAPI via Uvicorn
# -----------------------------
if __name__ == "__main__":
    import uvicorn
    logger.info("🤖 Starting FastAPI + Telegram webhook + APScheduler...")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
