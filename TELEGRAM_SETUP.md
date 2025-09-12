# Hướng dẫn cài đặt và chạy Telegram Bot

## Yêu cầu
- Python 3.8+
- Tài khoản Telegram
- Bot Token từ @BotFather

## Cài đặt

1. Tạo bot mới trên Telegram:
   - Mở Telegram và tìm @BotFather
   - Gửi lệnh `/newbot` và làm theo hướng dẫn
   - Lưu lại token được cung cấp

2. Cấu hình biến môi trường:
   Tạo hoặc chỉnh sửa file `.env` với nội dung:
   ```
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
   GOOGLE_API_KEY=your_google_ai_key_here
   ```

3. Cài đặt các thư viện cần thiết:
   ```bash
   pip install -r requirements.txt
   ```

## Chạy bot

1. Khởi động bot:
   ```bash
   python telegram_bot.py
   ```

2. Mở Telegram và tìm bot của bạn bằng tên @your_bot_username

## Tính năng chính

- **Tự động phản hồi** tin nhắn từ người dùng
- **Hỗ trợ đa ngữ cảnh** với lịch sử hội thoại
- **Tích hợp RAG** để tìm kiếm thông tin
- **Xử lý đa luồng** với Prefect

## Gỡ lỗi

- Kiểm tra log để xem lỗi chi tiết
- Đảm bảo đã cấu hình đúng các biến môi trường
- Kiểm tra kết nối Internet và quyền truy cập API

## Mở rộng

Bạn có thể mở rộng bot bằng cách thêm các công cụ mới trong thư mục `tasks/` và cập nhật hàm `process_message_flow` trong `telegram_bot.py`.
