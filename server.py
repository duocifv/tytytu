import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application, MessageHandler, filters,
    CommandHandler, ContextTypes
)
from handlers.message_handler import MessageHandler as MessageHandlerClass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
SECRET_TOKEN = os.getenv("WEBHOOK_SECRET")
PORT = int(os.environ.get("PORT", 10000))
WEBHOOK_URL = f"https://tytytu-mc9k.onrender.com/webhook/{SECRET_TOKEN}"

# Init bot
app = Application.builder().token(BOT_TOKEN).build()
handler = MessageHandlerClass()

# Command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Chào mừng bạn đến với AI Assistant!")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❓ Trợ giúp: /start /help")

# Register handlers
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handler.handle_message))
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_cmd))

if __name__ == "__main__":
    logger.info("🤖 Starting Telegram bot webhook...")
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=WEBHOOK_URL,
        secret_token=SECRET_TOKEN
    )
