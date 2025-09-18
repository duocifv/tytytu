import logging
import asyncio
from nodes2.manager import Manager  # dùng Manager thay vì ManagerNode
from services.notion_service import NotionService

logger = logging.getLogger("jobs")
logging.basicConfig(level=logging.INFO)

# Tạo client Notion
notion = NotionService()
manager = Manager(notion)  # Khởi tạo Manager với Notion client

async def task_ping():
    logger.info("⏰ Running scheduled ping task")

async def task_blog_auto():
    """Task tự động tạo blog (không cần customer_request)"""
    try:
        logger.info("⏰ [Scheduler] Bắt đầu tạo blog tự động...")
        await manager.run_auto()   # chạy workflow tự động
        logger.info("✅ [Scheduler] Hoàn tất tạo blog tự động")
    except Exception as e:
        logger.exception("⚠️ [Scheduler] Lỗi khi chạy Manager: %s", e)

async def task_blog_manual():
    """Task chạy thủ công theo quyết định admin"""
    try:
        logger.info("⏰ [Manual] Bắt đầu tạo blog theo lệnh admin...")
        await manager.run_manual()
        logger.info("✅ [Manual] Hoàn tất tạo blog theo lệnh admin")
    except Exception as e:
        logger.exception("⚠️ [Manual] Lỗi khi chạy Manager: %s", e)
