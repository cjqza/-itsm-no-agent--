from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.ticket import Ticket


async def generate_ticket_no(db: AsyncSession) -> str:
    """生成工单号: IT + 日期(YYYYMMDD) + 序号(001, 002, ...)"""
    today = datetime.now().strftime("%Y%m%d")
    prefix = f"IT{today}"

    # 查询今天最大的工单号
    result = await db.execute(
        select(func.max(Ticket.ticket_no))
        .where(Ticket.ticket_no.like(f"{prefix}%"))
    )
    max_no = result.scalar()

    if max_no:
        # 提取序号部分并+1
        seq = int(max_no[-3:]) + 1
    else:
        seq = 1

    return f"{prefix}{seq:03d}"
