"""
Main entry point for the Telegram Bot application.
"""

import os
import sys
import signal
import logging
from typing import Optional
from dotenv import load_dotenv
from telegram.ext import Application, MessageHandler, filters, CommandHandler
from handlers.message_handler import MessageHandler as MessageHandlerClass

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class TelegramBot:
    """Main class for managing the Telegram bot."""

    def __init__(self):
        # Load token trực tiếp từ .env
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN not found in .env file")

        # Init bot app
        self.app = Application.builder().token(self.token).build()
        self.message_handler = MessageHandlerClass()

        # Đăng ký signal handler (nếu chạy trực tiếp, không chạy trong thread)
        try:
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
        except ValueError:
            # Nếu đang chạy trong thread thì bỏ qua signal
            logger.warning("⚠️ Signal handler bị bỏ qua (chạy trong thread)")

    def setup_handlers(self) -> None:
        """Set up message & command handlers."""
        self.app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND,
                           self.message_handler.handle_message)
        )
        self.app.add_handler(CommandHandler("start", self._handle_start))
        self.app.add_handler(CommandHandler("help", self._handle_help))

    async def _handle_start(self, update, context) -> None:
        await update.message.reply_text(
            "🤖 Chào mừng bạn đến với AI Assistant!\n\n"
            "Hãy gửi tin nhắn bất kỳ để bắt đầu."
        )

    async def _handle_help(self, update, context) -> None:
        await update.message.reply_text(
            "❓ Trợ giúp\n\n"
            "• /start - Bắt đầu trò chuyện\n"
            "• /help - Hiển thị trợ giúp"
        )

    def _signal_handler(self, signum, frame) -> None:
        logger.info("📴 Nhận tín hiệu dừng. Đang tắt bot...")
        self.app.stop_running()
        sys.exit(0)

    def run(self) -> None:
        try:
            self.setup_handlers()
            logger.info("🤖 Bot đang khởi động...")
            self.app.run_polling(drop_pending_updates=True, close_loop=False)
        except Exception as e:
            logger.critical(f"Lỗi nghiêm trọng: {e}", exc_info=True)
            sys.exit(1)


def main() -> None:
    try:
        bot = TelegramBot()
        bot.run()
    except Exception as e:
        logger.critical(f"Không thể khởi động bot: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
