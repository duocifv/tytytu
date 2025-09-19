"""
Xử lý tin nhắn từ người dùng Telegram.
"""
import logging
from typing import Dict, Any, Optional
from telegram import Update
from telegram.ext import ContextTypes
from flows import process_message_flow

# Cấu hình logging
logger = logging.getLogger(__name__)

class MessageHandler:
    """Xử lý tin nhắn đến từ người dùng Telegram."""
    
    def __init__(self):
        """Khởi tạo trình xử lý tin nhắn với các phiên người dùng."""
        self.user_sessions: Dict[int, Dict[str, Any]] = {}
        
    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Xử lý lệnh /start từ người dùng."""
        user = update.effective_user
        chat_id = update.effective_chat.id   # 👉 Đây là chat_id
        welcome_message = (
            f"👋 Xin chào {user.first_name}!\n\n"
            "🤖 Tôi là chatbot hỗ trợ của bạn. Tôi có thể giúp bạn:\n"
            "• Trả lời câu hỏi\n"
            "• Tìm kiếm thông tin\n"
            "• Hỗ trợ kỹ thuật\n\n"
            "Gửi tin nhắn bất kỳ để bắt đầu!"
        )
        logger.info(f"📌 Chat ID của @{user.username} là {chat_id}")
        await update.message.reply_text(welcome_message)
        
    async def handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Xử lý lệnh /help từ người dùng."""
        help_message = (
            "🆘 *Hướng dẫn sử dụng*\n\n"
            "• Gửi tin nhắn bất kỳ để nhận câu trả lời\n"
            "• Sử dụng @ để nhắc đến bot trong nhóm\n"
            "• Các lệnh có sẵn:\n"
            "  /start - Bắt đầu sử dụng bot\n"
            "  /help - Xem hướng dẫn\n\n"
            "📌 Mọi thắc mắc vui lòng liên hệ quản trị viên."
        )
        await update.message.reply_text(help_message, parse_mode='Markdown')
    
    async def handle_message(
        self, 
        update: Update, 
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        Xử lý tin nhắn văn bản đến từ người dùng.
        
        Args:
            update: Đối tượng cập nhật từ Telegram
            context: Đối tượng ngữ cảnh từ Telegram
        """
        logger.info("🔄 Bắt đầu xử lý tin nhắn mới")
        
        if not update.message or not update.message.text:
            logger.warning("⚠️ Tin nhắn không hợp lệ: thiếu nội dung")
            return
            
        try:
            user = update.effective_user
            message = update.message.text.strip()
            logger.debug(f"🔍 Đã trích xuất thông tin từ tin nhắn - User ID: {user.id}, Tên: {user.username}")
            
            # Khởi tạo phiên người dùng nếu chưa tồn tại
            if user.id not in self.user_sessions:
                logger.info(f"👤 Tạo phiên mới cho người dùng: {user.username} (ID: {user.id})")
                self.user_sessions[user.id] = {
                    'history': [],
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name
                }
            else:
                logger.debug(f"🔄 Tiếp tục phiên hiện có cho người dùng: {user.username}")
            
            logger.info(
                f"📩 Đã nhận tin nhắn từ @{user.username} (ID: {user.id}): "
                f"\n---\n{message[:200]}{'...' if len(message) > 200 else ''}"
            )
            
            # Xử lý tin nhắn thông qua luồng xử lý
            logger.debug("⏳ Đang xử lý tin nhắn thông qua luồng xử lý chính...")
            response = await process_message_flow(
                message=message,
                user_id=str(user.id),  # Convert to string to match expected type
                session_id=str(user.id)  # Using user ID as session ID for tracking
            )
            
            # Gửi phản hồi cho người dùng
            logger.debug(f"📤 Đang gửi phản hồi cho @{user.username}")
            
            # -------------------------
            # Gửi phản hồi cho người dùng
            # -------------------------
            response_text = None
            chart_base64 = None

            if isinstance(response, dict):
                response_text = response.get('text') or response.get('content')
                chart_base64 = response.get('chart_base64')
            else:
                response_text = str(response)

            if not response_text:
                response_text = "Xin lỗi, tôi không thể tạo phản hồi phù hợp vào lúc này."

            # Gửi text trước
            await update.message.reply_text(response_text)

            # Nếu có ảnh (base64 chart) thì gửi thêm
            if chart_base64:
                import base64, io
                from telegram import InputFile
                
                # Nếu có prefix "data:image/png;base64,", thì bỏ đi
                if chart_base64.startswith("data:image"):
                    chart_base64 = chart_base64.split(",")[1]

                img_bytes = base64.b64decode(chart_base64)
                bio = io.BytesIO(img_bytes)
                bio.name = "chart.png"
                await context.bot.send_photo(chat_id=update.effective_chat.id, photo=InputFile(bio))
            
            logger.info(f"✅ Đã gửi thành công phản hồi cho @{user.username}")
            logger.debug(f"📊 Số lượng phiên đang hoạt động: {len(self.user_sessions)}")
            
        except Exception as e:
            error_message = str(e)
            error_lower = error_message.lower()
            
            # Extract user info safely
            user_id = getattr(update.effective_user, 'id', 'unknown')
            username = getattr(update.effective_user, 'username', 'unknown')
            
            # List of possible chat not found/blocked error messages (case-insensitive)
            chat_errors = [
                # Chat not found variations
                "chat not found", 
                "chat_not_found", 
                "no chat found",
                "Chat not found",
                "CHAT NOT FOUND",
                "chat not found",  # Original case
                "Chat not found",  # First letter capitalized
                "CHAT NOT FOUND",  # All caps
                
                # Bot blocked by user errors
                "bot was blocked by the user",
                "bot can't initiate conversation with a user",
                "bot was kicked",
                "bot is not a member",
                "bot is not a member of the supergroup chat",
                "bot can't send messages to this chat",
                "bot was kicked from the group chat",
                "bot was kicked from this group",
                "bot is not a member of the channel chat",
                "bot is not a member of the supergroup",
                "bot is not a member of this chat",
                "bot is not a member of the group chat",
                "bot was blocked by the user",
                "bot can't send messages to bots",
                "bot can't send messages to this user",
                "bot was blocked by the user",
                
                # Additional error patterns
                "peer id invalid",
                "chat not exist",
                "chat doesn't exist",
                "chat does not exist",
                "chat is deactivated",
                "chat is inactive",
                "user is deactivated",
                "user is inactive",
                "user not found",
                "user not exist",
                "user doesn't exist",
                "user does not exist",
                "group chat was deactivated",
                "supergroup chat was deactivated",
                "channel chat was deactivated"
            ]
            
            # Check if the error is a chat not found/blocked error
            is_chat_error = any(err in error_lower for err in [e.lower() for e in chat_errors])
            
            if is_chat_error:
                # Determine the specific type of chat error
                error_type = "blocked" if any(blocked in error_lower for blocked in [
                    "blocked", "kicked", "not a member", "can't send messages"
                ]) else "not found"
                
                logger.warning(
                    f"⚠️ Không thể gửi tin nhắn: Chat {error_type}. "
                    f"User ID: {user_id}, Username: @{username}, "
                    f"Error: {error_message}"
                )
                
                # Clean up the session if it exists
                if user_id != 'unknown' and user_id in self.user_sessions:
                    del self.user_sessions[user_id]
                    logger.info(f"🧹 Đã xóa phiên cho người dùng ID: {user_id} (Lý do: chat {error_type})")
                return
                
            # Log other errors
            logger.critical(
                f"❌ LỖI NGHIÊM TRỌNG khi xử lý tin nhắn từ @{username} (ID: {user_id}): {error_message}", 
                exc_info=True
            )
                
            try:
                # Only try to send error message if we have a valid message object
                if update and update.message:
                    logger.warning("🔄 Đang thử gửi thông báo lỗi cho người dùng...")
                    await update.message.reply_text(
                        "❌ Đã xảy ra lỗi khi xử lý yêu cầu của bạn. Vui lòng thử lại sau."
                    )
                    logger.info("✅ Đã gửi thông báo lỗi cho người dùng")
            except Exception as send_error:
                logger.error(f"❌ KHÔNG THỂ gửi thông báo lỗi: {send_error}", exc_info=True)
                
                # If we can't send messages, clean up the session
                if "chat not found" in str(send_error).lower() and update.effective_user:
                    if update.effective_user.id in self.user_sessions:
                        del self.user_sessions[update.effective_user.id]
                        logger.info(f"🧹 Đã xóa phiên cho người dùng ID: {update.effective_user.id} (không thể gửi tin nhắn)")
            
            logger.info("🔄 Kết thúc xử lý tin nhắn với lỗi")
