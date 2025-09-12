"""
Entry point Chatbot AI (Prefect + LangChain)
Giữ gọn, dễ hiểu: serve (deploy) hoặc chạy trực tiếp 1 câu hỏi / interactive.
"""

import asyncio
import os
import argparse
from dotenv import load_dotenv
from prefect import flow, get_run_logger

load_dotenv()

def banner():
    print("""
╔══════════════════════════════════════════╗
║     🤖 CHATBOT AI - PREFECT + LANGCHAIN   ║
╚══════════════════════════════════════════╝
""")

@flow(name="luong-chinh")
async def luong_chinh(question: str = None):
    """
    Luồng chính: nếu question có -> trả về phản hồi cho 1 lần,
    nếu không -> vào chế độ interactive CLI.
    """
    logger = get_run_logger()

    if not os.getenv("GOOGLE_API_KEY"):
        raise ValueError("❌ Thiếu GOOGLE_API_KEY trong biến môi trường")

    logger.info("🟢 Bắt đầu xử lý yêu cầu...")

    # chạy 1 lần nếu có question
    if question:
        from flows.chat_flow import chat_flow
        resp = await chat_flow(question)
        # nếu trả về dataclass PhanHoi thì lấy .noi_dung, còn không thì in nguyên
        text = getattr(resp, "noi_dung", resp)
        logger.info(f"🤖 Đã nhận phản hồi: {text}")
        return text

    # interactive mode
    logger.info("💬 Chế độ interactive (gõ 'thoat' để kết thúc)")
    from flows.chat_flow import chat_flow
    while True:
        q = input("\n👤 Bạn: ").strip()
        if q.lower() in ("thoat", "exit", "quit"):
            break
        resp = await chat_flow(q)
        print("\n🤖 Chatbot:", getattr(resp, "noi_dung", resp))

async def main():
    banner()
    parser = argparse.ArgumentParser(description="Chatbot AI với Prefect + LangChain")
    parser.add_argument("--serve", action="store_true", help="Đăng ký deployment lên Prefect server")
    parser.add_argument("--cau-hoi", type=str, help="Câu hỏi 1 lần")
    args = parser.parse_args()

    if args.serve:
        # đăng ký deployment (xuất hiện trên dashboard)
        await luong_chinh.deploy(
            name="chatbot-ai-deployment",
            work_pool_name="default-agent-pool",
            tags=["chatbot"]
        )
        print("✅ Deployment đã được đăng ký trên server (kiểm tra dashboard).")
    else:
        await luong_chinh(args.cau_hoi)

if __name__ == "__main__":
    asyncio.run(main())
