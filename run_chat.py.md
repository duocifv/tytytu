"""
Entry point Chatbot AI (LangChain + APScheduler)
Giữ gọn, dễ hiểu: serve (deploy) hoặc chạy trực tiếp 1 câu hỏi / interactive.
"""

import asyncio
import os
import argparse
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_run_logger():
    """Get the logger instance for tasks"""
    return logger

def banner():
    print("""
╔══════════════════════════════════════════╗
║     🤖 CHATBOT AI - APSCHEDULER + LANGCHAIN ║
╚══════════════════════════════════════════╝
""")

async def luong_chinh(question: str = None):
    """
    Luồng chính: nếu question có -> trả về phản hồi cho 1 lần,
    nếu không -> vào chế độ interactive CLI.
    """
    logger = get_run_logger()

    if not os.getenv("GOOGLE_API_KEY"):
        raise ValueError("❌ Thiếu GOOGLE_API_KEY trong biến môi trường")

    logger.info("🟢 Bắt đầu xử lý yêu cầu...")

    # Khởi tạo flow xử lý tin nhắn
    from flows.telegram_flow import process_message_flow
    
    if question:
        # Chế độ 1 câu hỏi
        response = await process_message_flow(
            message=question,
            user_id="console_user"
        )
        print(f"🤖 {response.get('reply', 'Không có phản hồi')}")
    else:
        # Chế độ interactive
        banner()
        print("Nhập 'thoat' hoặc 'exit' để thoất\n")
        
        while True:
            try:
                user_input = input("👤 Bạn: ").strip()
                if user_input.lower() in ['thoat', 'exit', 'quit']:
                    print("👋 Tạm biệt!")
                    break
                    
                if not user_input:
                    continue
                    
                response = await process_message_flow(
                    message=user_input,
                    user_id="console_user"
                )
                print(f"\n🤖 {response.get('reply', 'Xin lỗi, tôi không hiểu câu hỏi của bạn.')}\n")
                
            except KeyboardInterrupt:
                print("\n👋 Tạm biệt!")
                break
            except Exception as e:
                logger.error(f"Lỗi: {str(e)}")
                print(f"\n❌ Đã xảy ra lỗi: {str(e)}\n")

async def main():
    parser = argparse.ArgumentParser(description="Chatbot AI với LangChain")
    parser.add_argument("--cau-hoi", type=str, help="Câu hỏi 1 lần")
    args = parser.parse_args()

    await luong_chinh(args.cau_hoi)

if __name__ == "__main__":
    asyncio.run(main())
