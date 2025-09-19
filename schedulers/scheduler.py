import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from . import jobs

logger = logging.getLogger("scheduler")

def init_scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.start()

    # Job 1: task_blog → 2 tiếng 1 lần
    scheduler.add_job(
        jobs.task_blog_auto,
        CronTrigger(hour="*/2"),
        id="task_blog",
        replace_existing=True,
    )
    logger.info("✅ Job 'task_blog' chạy mỗi 2 giờ")

    # Job 2: task_ping → 5 phút 1 lần trong khung giờ 5h–19h
    # scheduler.add_job(
    #     jobs.task_ping,
    #     CronTrigger(hour="5-19", minute="*/5"),
    #     id="task_ping",
    #     replace_existing=True,
    # )
    # logger.info("✅ Job 'task_ping' chạy mỗi 5 phút (5h–19h)")

    # In giờ hiện tại
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"⏰ Giờ hiện tại: {now}")

    # In preview các job
    scheduler.print_jobs()

    return scheduler
