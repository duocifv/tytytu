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
                user_id=str(user.id),  # Convert to string to match expected type
                message=message,
                session_id=str(user.id)  # Using user ID as session ID for tracking
            )
            
            # Gửi phản hồi cho người dùng
            logger.debug(f"📤 Đang gửi phản hồi cho @{user.username}")
            await update.message.reply_text(response)
            
            logger.info(f"✅ Đã gửi thành công phản hồi cho @{user.username}")
            logger.debug(f"📊 Số lượng phiên đang hoạt động: {len(self.user_sessions)}")
            
        except Exception as e:
            logger.critical(f"❌ LỖI NGHIÊM TRỌNG khi xử lý tin nhắn: {str(e)}", exc_info=True)
            try:
                logger.warning("🔄 Đang thử gửi thông báo lỗi cho người dùng...")
                await update.message.reply_text(
                    "❌ Đã xảy ra lỗi khi xử lý yêu cầu của bạn. Vui lòng thử lại sau."
                )
                logger.info("✅ Đã gửi thông báo lỗi cho người dùng")
            except Exception as send_error:
                logger.error(f"❌ KHÔNG THỂ gửi thông báo lỗi: {send_error}", exc_info=True)
            
            logger.info("🔄 Kết thúc xử lý tin nhắn với lỗi")
