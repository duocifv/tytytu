# main.py
import os
import sys
import logging
from dotenv import load_dotenv
from telegram.ext import Application, MessageHandler, filters, CommandHandler
from handlers.message_handler import MessageHandler as MessageHandlerClass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

class TelegramBot:
    """Telegram bot setup (for webhook mode)."""
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN missing in .env")
        self.app = Application.builder().token(self.token).build()
        self.message_handler = MessageHandlerClass()

    def setup_handlers(self):
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,
                                            self.message_handler.handle_message))
        self.app.add_handler(CommandHandler("start", self._handle_start))
        self.app.add_handler(CommandHandler("help", self._handle_help))

    async def _handle_start(self, update, context):
        await update.message.reply_text("🤖 Chào mừng bạn đến với AI Assistant!")

    async def _handle_help(self, update, context):
        await update.message.reply_text("❓ Trợ giúp: /start /help")
