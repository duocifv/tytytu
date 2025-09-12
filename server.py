# server.py
import os
import threading
import asyncio
from flask import Flask
from main import main  # import main() từ main.py

flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "🤖 Telegram bot is running on Render!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    # dev server ok for Render healthcheck
    flask_app.run(host="0.0.0.0", port=port)

def _start_bot_in_thread():
    """
    Tạo event loop mới cho thread này -> đặt nó -> gọi main().
    main() sẽ gọi Application.run_polling(...) và PTB sẽ tìm thấy event loop.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        main()
    except Exception:
        # để log lỗi lên console / Render logs nếu cần
        import logging, traceback
        logging.getLogger("server").exception("Bot crashed in thread:\n%s", traceback.format_exc())
    finally:
        # đóng loop nếu main() kết thúc
        try:
            loop.close()
        except Exception:
            pass

if __name__ == "__main__":
    # Start bot in background thread (thread has its own asyncio loop)
    bot_thread = threading.Thread(target=_start_bot_in_thread, name="bot-thread", daemon=True)
    bot_thread.start()

    # Start Flask HTTP server for Render healthcheck (main thread)
    run_flask()
