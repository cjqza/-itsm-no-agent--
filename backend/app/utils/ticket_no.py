import asyncio
import logging
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from app.models.ticket import Ticket

logger = logging.getLogger(__name__)


async def generate_ticket_no(db: AsyncSession, max_retries: int = 5) -> str:
    """生成工单号: IT + 日期(YYYYMMDD) + 序号(001, 002, ...)

    使用重试机制防止并发生成重复工单号（SQLite 不支持 FOR UPDATE 行锁）。
    最终依赖数据库 UNIQUE 约束保证唯一性。
    """
    today = datetime.now().strftime("%Y%m%d")
    prefix = f"IT{today}"

    for attempt in range(max_retries):
        # 查询今天最大的工单号
        result = await db.execute(
            select(func.max(Ticket.ticket_no))
            .where(Ticket.ticket_no.like(f"{prefix}%"))
        )
        max_no = result.scalar()

        if max_no:
            # 正确提取序号部分：去掉前缀后转整数
            seq = int(max_no[len(prefix):]) + 1
        else:
            seq = 1

        ticket_no = f"{prefix}{seq:03d}"

        # 验证此工单号不存在（防止并发重复）
        exists_result = await db.execute(
            select(Ticket.id).where(Ticket.ticket_no == ticket_no)
        )
        if not exists_result.scalar():
            return ticket_no

        # 工单号已存在，短暂等待后重试
        logger.warning(f"工单号 {ticket_no} 已存在，重试 ({attempt + 1}/{max_retries})")
        await asyncio.sleep(0.05 * (attempt + 1))

    raise RuntimeError("无法生成唯一工单号，请稍后重试")
