"""
Telegram Bot + Prefect + LangChain (tối giản, hiệu quả)
"""

import os
import logging
from typing import Dict, Any
from dotenv import load_dotenv

# Telegram
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Prefect
from prefect import flow, get_run_logger

# Task imports
from tasks.llm_tasks import phan_tich_y_dinh, tao_phat_bieu
from tasks.tool_tasks import thuc_thi_cong_cu, agent_chat
from tasks.vector_tasks import truy_van_du_lieu

# Load .env
load_dotenv()

# Logging chuẩn Python
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Token Telegram
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("Thiếu TELEGRAM_BOT_TOKEN trong biến môi trường")

# Lưu ngữ cảnh người dùng
USER_CONTEXT: Dict[int, Dict[str, Any]] = {}

# -------------------------------
# Flow xử lý tin nhắn
# -------------------------------
@flow(name="telegram-message-flow")
async def process_message_flow(message: str, user_id: int) -> str:
    """Flow chính: phân tích ý định, gọi tool, tạo phản hồi."""
    logger_flow = get_run_logger()
    try:
        logger_flow.info(f"Phân tích ý định: {message}")
        intent = await phan_tich_y_dinh(message)
        logger_flow.info(f"Ý định: {intent}")
        
        context = ""
        
        if intent == "tim_kiem_thong_tin":
            # Tìm kiếm thông tin từ vector store
            results = await truy_van_du_lieu(message, top_k=3)
            context = "\n".join(results) if results else "Không tìm thấy thông tin liên quan."
        logger_flow.info(f"Tìm kiếm thông tin từ vector store: {context}")

        # Gọi công cụ xử lý
        # tool_result = await thuc_thi_cong_cu({
        #     "tool_name": intent,
        #     "params": {"truy_van": message}
        # })
        # logger_flow.info(f"tool_result: {tool_result}")

        # Gọi công cụ/agent để xử lý
        tool_result = await agent_chat(message)
        logger_flow.info(f"tool_result: {tool_result}")

        # 1) Nếu agent đã tổng hợp reply (LLM synthesize) -> trả ngay
        reply = tool_result.get("reply")
        if reply:
            logger_flow.info("Agent trả về reply đã được tổng hợp, trả cho user.")
            return reply

        # 2) Nếu có tool_results -> lấy kết quả đầu tiên để build response qua tao_phat_bieu
        tool_results = tool_result.get("tool_results", [])
        if tool_results:
            first = tool_results[0]
            dispatch = first.get("dispatch", {})

            if dispatch.get("ok"):
                # dispatch result là dict (handler trả về dict)
                tool_output_obj = dispatch.get("result", {})
                # convert to string (chuỗi/gợi ý) để đưa vào tao_phat_bieu
                tool_output = (
                    tool_output_obj.get("summary")
                    if isinstance(tool_output_obj, dict) and tool_output_obj.get("summary")
                    else str(tool_output_obj)
                )
            else:
                # handler lỗi -> truyền thông báo lỗi
                tool_output = f"[Tool error] {dispatch.get('error', 'Unknown error')}"

            logger_flow.info(f"Using first tool result to build reply: {tool_output}")

            response = await tao_phat_bieu(
                cau_hoi=message,
                nguyen_canh=context,
                phan_hoi_cong_cu=tool_output
            )
            return response

        # 3) Fallback: không có reply lẫn tool result
        logger_flow.info("No reply and no tool results -> fallback response.")
        return await tao_phat_bieu(
            cau_hoi=message,
            nguyen_canh=context,
            phan_hoi_cong_cu="Không có kết quả từ công cụ."
        )

    except Exception as e:
        logger_flow.error(f"Lỗi flow: {e}")
        return "Xin lỗi, đã xảy ra lỗi khi xử lý yêu cầu của bạn."

# -------------------------------
# Handler Telegram
# -------------------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in USER_CONTEXT:
        USER_CONTEXT[user_id] = {"history": []}

    logger.info(f"Tin nhắn từ {user_id}: {text}")

    try:
        resp = await process_message_flow(text, user_id)
        await update.message.reply_text(resp)
    except Exception as e:
        logger.error(f"Lỗi handler: {e}")
        await update.message.reply_text("Xin lỗi, có lỗi xảy ra.")

# -------------------------------
# Khởi động bot
# -------------------------------
def start_bot():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("🤖 Bot Telegram đang chạy...")
    app.run_polling(drop_pending_updates=True)

# -------------------------------
if __name__ == "__main__":
    start_bot()
