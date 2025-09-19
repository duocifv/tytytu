import logging
from services.notion_service import NotionService

logger = logging.getLogger("jobs")
logging.basicConfig(level=logging.INFO)

# Tạo client Notion
notion = NotionService()


async def task_ping():
    logger.info("⏰ Running scheduled ping task")

async def task_blog_auto():
    """Task tự động tạo blog (không cần customer_request)"""
    try:
        logger.info("⏰ [Scheduler] Bắt đầu tạo blog tự động...")
        # await manager.run_auto()   # chạy workflow tự động
        logger.info("✅ [Scheduler] Hoàn tất tạo blog tự động")
    except Exception as e:
        logger.exception("⚠️ [Scheduler] Lỗi khi chạy Manager: %s", e)
