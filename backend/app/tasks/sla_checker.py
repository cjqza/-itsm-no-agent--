"""SLA定时检查任务"""
import asyncio
import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


async def check_sla_task():
    """定时检查SLA状态"""
    from app.database import AsyncSessionLocal
    from app.services.sla_service import sla_service

    try:
        async with AsyncSessionLocal() as db:
            await sla_service.check_sla(db)
    except Exception as e:
        logger.error(f"SLA检查任务异常: {e}")


def start_sla_checker():
    """启动SLA检查定时任务（每分钟执行一次）"""
    try:
        scheduler.add_job(
            check_sla_task,
            "interval",
            minutes=1,
            id="sla_checker",
            replace_existing=True,
        )
        scheduler.start()
        logger.info("SLA检查定时任务已启动")
    except Exception as e:
        logger.error(f"启动SLA检查任务失败: {e}")


def stop_sla_checker():
    """停止SLA检查定时任务"""
    scheduler.shutdown()
    logger.info("SLA检查定时任务已停止")
