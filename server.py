# server.py
import os
import logging
from flask import Flask, request, jsonify
from main import TelegramBot  # main.py phải expose class TelegramBot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

flask_app = Flask(__name__)

# Khởi tạo bot
bot = TelegramBot()
bot.setup_handlers()

# Webhook route để Telegram gửi update
@flask_app.route("/webhook", methods=["POST"])
def webhook():
    update = request.get_json(force=True)
    # Đẩy update vào bot handler
    try:
        import asyncio
        asyncio.run(bot.app.update_queue.put(update))
    except Exception as e:
        logger.exception("❌ Lỗi khi xử lý webhook: %s", e)
        return jsonify({"ok": False, "error": str(e)}), 500
    return jsonify({"ok": True})

# Healthcheck route
@flask_app.route("/")
def home():
    return "🤖 Telegram bot webhook is running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    # Render: listen 0.0.0.0
    flask_app.run(host="0.0.0.0", port=port)
