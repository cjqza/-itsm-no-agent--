"""SLA管理服务"""
import logging
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ticket import Ticket, TicketStatus, SLAStatus
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class SLAService:

    async def check_sla(self, db: AsyncSession):
        """检查所有进行中工单的SLA状态"""
        now = datetime.now(timezone.utc)

        result = await db.execute(
            select(Ticket).where(
                Ticket.status.not_in([
                    TicketStatus.RESOLVED,
                    TicketStatus.RESOLVED_PENDING_REVIEW,
                ])
            )
        )
        tickets = result.scalars().all()

        updated_count = 0
        for ticket in tickets:
            old_sla_status = ticket.sla_status
            new_sla_status = self._calculate_sla_status(ticket, now)

            if new_sla_status != old_sla_status:
                ticket.sla_status = new_sla_status
                updated_count += 1

                if new_sla_status == SLAStatus.BLACK:
                    logger.warning(f"工单 {ticket.ticket_no} SLA超时!")

        if updated_count > 0:
            await db.commit()

    def _ensure_utc(self, dt) -> datetime:
        """确保datetime有时区信息（处理SQLite返回的naive datetime或字符串）"""
        if dt is None:
            return None
        # 如果是字符串，先转换为datetime
        if isinstance(dt, str):
            try:
                dt = datetime.fromisoformat(dt)
            except ValueError:
                dt = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S.%f")
        # 确保有时区信息
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt

    def _calculate_sla_status(self, ticket: Ticket, now: datetime) -> SLAStatus:
        """计算工单SLA状态"""
        if not ticket.sla_deadline:
            return SLAStatus.GREEN

        # 待接单：检查超时
        if ticket.status == TicketStatus.PENDING:
            if ticket.created_at:
                created_at = self._ensure_utc(ticket.created_at)
                elapsed_minutes = (now - created_at).total_seconds() / 60
                if elapsed_minutes >= 30:
                    return SLAStatus.BLACK
                if elapsed_minutes >= 20:
                    return SLAStatus.RED
                if elapsed_minutes >= 10:
                    return SLAStatus.YELLOW
            return SLAStatus.GREEN

        # 已接单：检查SLA时间
        sla_deadline = self._ensure_utc(ticket.sla_deadline)
        created_at = self._ensure_utc(ticket.created_at)
        total_seconds = (sla_deadline - created_at).total_seconds()
        elapsed_seconds = (now - created_at).total_seconds()

        # 减去暂停时间
        if ticket.is_sla_paused and ticket.sla_paused_at:
            paused_at = self._ensure_utc(ticket.sla_paused_at)
            paused_seconds = (now - paused_at).total_seconds()
            elapsed_seconds -= paused_seconds
        elapsed_seconds -= ticket.sla_paused_seconds or 0

        if elapsed_seconds <= 0:
            return SLAStatus.GREEN

        progress = elapsed_seconds / total_seconds

        if progress >= 1.0:
            return SLAStatus.BLACK
        elif progress >= settings.SLA_WARNING_PERCENT / 100:
            return SLAStatus.RED
        elif progress >= 0.3:
            return SLAStatus.YELLOW
        else:
            return SLAStatus.GREEN

    async def pause_sla(self, db: AsyncSession, ticket_id: int, reason: str):
        """暂停SLA计时"""
        result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
        ticket = result.scalar_one_or_none()
        if not ticket:
            raise ValueError("工单不存在")

        ticket.is_sla_paused = True
        ticket.sla_paused_at = datetime.now(timezone.utc)
        ticket.sla_paused_reason = reason
        await db.commit()

    async def resume_sla(self, db: AsyncSession, ticket_id: int):
        """恢复SLA计时"""
        result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
        ticket = result.scalar_one_or_none()
        if not ticket:
            raise ValueError("工单不存在")

        if ticket.is_sla_paused and ticket.sla_paused_at:
            try:
                # 获取当前时间（UTC时区）
                now = datetime.now(timezone.utc)
                # 获取暂停时间并确保有时区信息
                paused_at = ticket.sla_paused_at
                if isinstance(paused_at, str):
                    paused_at = datetime.fromisoformat(paused_at)
                if paused_at.tzinfo is None:
                    paused_at = paused_at.replace(tzinfo=timezone.utc)
                # 计算暂停秒数
                paused_seconds = (now - paused_at).total_seconds()
                ticket.sla_paused_seconds = (ticket.sla_paused_seconds or 0) + int(paused_seconds)
            except Exception as e:
                # 如果时区处理失败，使用默认值
                logger.warning(f"计算暂停时间失败: {e}，使用默认值")
                ticket.sla_paused_seconds = ticket.sla_paused_seconds or 0

        ticket.is_sla_paused = False
        ticket.sla_paused_at = None
        ticket.sla_paused_reason = None
        await db.commit()


sla_service = SLAService()
