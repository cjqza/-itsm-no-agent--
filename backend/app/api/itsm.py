"""ITSM API - 工单管理"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import datetime, timezone
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User
from app.models.ticket import Ticket, TicketStatus, TicketLog
from app.schemas.ticket import (
    TicketCreate, TicketUpdate, TicketStatusUpdate,
    TicketRate, TicketRemark, TicketMessage,
)
from app.utils.auth import get_current_user, require_permission
from app.services.ticket_service import ticket_service
from app.services.sla_service import sla_service

router = APIRouter(prefix="/api/itsm", tags=["ITSM"])


class TicketTransferRequest(BaseModel):
    assignee_id: int
    reason: str = ""


class TicketUrgeRequest(BaseModel):
    message: Optional[str] = None


@router.get("/dashboard")
async def dashboard(
    current_user: User = Depends(require_permission("itsm_access")),
    db: AsyncSession = Depends(get_db),
):
    """首页仪表盘"""
    from sqlalchemy import func, case, and_
    from app.models.ticket import Ticket, TicketStatus

    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    # 合并为单条 SQL，减少数据库往返
    result = await db.execute(
        select(
            func.count(case((Ticket.created_at >= today, 1))).label("today_count"),
            func.count(case((Ticket.status == TicketStatus.PENDING, 1))).label("pending_count"),
            func.count(case(
                (and_(
                    Ticket.assignee_id == current_user.id,
                    Ticket.status.in_([TicketStatus.ACCEPTED, TicketStatus.PROCESSING]),
                ), 1),
            )).label("my_count"),
            func.count(case((Ticket.status == TicketStatus.RESOLVED_PENDING_REVIEW, 1))).label("review_count"),
            func.count(case((Ticket.status == TicketStatus.RESOLVED, 1))).label("resolved_count"),
        )
    )
    row = result.one()

    return {
        "today_count": row.today_count or 0,
        "pending_count": row.pending_count or 0,
        "my_count": row.my_count or 0,
        "review_count": row.review_count or 0,
        "resolved_count": row.resolved_count or 0,
    }


@router.post("/tickets")
async def create_ticket(
    data: TicketCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建工单"""
    # 如果未指定creator_id，自动使用当前用户ID
    creator_id = data.creator_id if data.creator_id is not None else current_user.id
    ticket = await ticket_service.create_ticket(
        db=db,
        title=data.title,
        description=data.description or "",
        creator_id=creator_id,
        priority=data.priority,
        category_id=data.category_id,
    )
    await db.commit()
    return {
        "id": ticket.id,
        "ticket_no": ticket.ticket_no,
        "title": ticket.title,
        "status": ticket.status.value,
    }


@router.get("/tickets")
async def list_tickets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    assignee_id: Optional[int] = None,
    creator_id: Optional[int] = None,
    category_id: Optional[int] = None,
    keyword: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """工单列表"""
    return await ticket_service.list_tickets(
        db=db,
        page=page,
        page_size=page_size,
        status=status,
        assignee_id=assignee_id,
        creator_id=creator_id,
        category_id=category_id,
        keyword=keyword,
    )


@router.get("/tickets/search")
async def search_tickets(
    keyword: str = Query(..., min_length=1),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """搜索工单"""
    return await ticket_service.list_tickets(
        db=db,
        keyword=keyword,
        page_size=50,
    )


@router.get("/tickets/sla-warnings")
async def get_sla_warning_tickets(
    current_user: User = Depends(require_permission("itsm_access")),
    db: AsyncSession = Depends(get_db),
):
    """获取SLA预警工单"""
    from app.models.ticket import SLAStatus
    result = await db.execute(
        select(Ticket)
        .where(
            Ticket.sla_status.in_([SLAStatus.YELLOW, SLAStatus.RED]),
            Ticket.status.not_in([TicketStatus.RESOLVED, TicketStatus.RESOLVED_PENDING_REVIEW]),
        )
        .order_by(Ticket.sla_deadline)
        .limit(20)
    )
    tickets = result.scalars().all()
    return [ticket_service._ticket_to_dict(t) for t in tickets]


@router.get("/tickets/{ticket_id}")
async def get_ticket(
    ticket_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """工单详情"""
    import logging
    logger = logging.getLogger(__name__)
    try:
        ticket = await ticket_service.get_ticket(db, ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="工单不存在")
        return ticket
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"get_ticket error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取工单失败: {str(e)}")


@router.put("/tickets/{ticket_id}")
async def update_ticket(
    ticket_id: int,
    data: TicketUpdate,
    current_user: User = Depends(require_permission("itsm_access")),
    db: AsyncSession = Depends(get_db),
):
    """更新工单信息"""
    update_data = data.model_dump(exclude_unset=True)
    ticket = await ticket_service.update_ticket(
        db=db,
        ticket_id=ticket_id,
        operator_id=current_user.id,
        **update_data,
    )
    return {"success": True, "ticket_no": ticket.ticket_no}


@router.put("/tickets/{ticket_id}/accept")
async def accept_ticket(
    ticket_id: int,
    current_user: User = Depends(require_permission("itsm_access")),
    db: AsyncSession = Depends(get_db),
):
    """接单（客服手动接单）"""
    ticket = await ticket_service.accept_ticket(
        db=db,
        ticket_id=ticket_id,
        agent_id=current_user.id,
    )
    return {"success": True, "status": ticket.status.value}


@router.put("/tickets/{ticket_id}/status")
async def update_status(
    ticket_id: int,
    data: TicketStatusUpdate,
    current_user: User = Depends(require_permission("itsm_access")),
    db: AsyncSession = Depends(get_db),
):
    """更改工单状态"""
    ticket = await ticket_service.update_status(
        db=db,
        ticket_id=ticket_id,
        new_status=data.status,
        operator_id=current_user.id,
        remark=data.remark,
    )
    return {"success": True, "status": ticket.status.value}


@router.put("/tickets/{ticket_id}/resolve")
async def resolve_ticket(
    ticket_id: int,
    current_user: User = Depends(require_permission("itsm_access")),
    db: AsyncSession = Depends(get_db),
):
    """解决工单"""
    ticket = await ticket_service.update_status(
        db=db,
        ticket_id=ticket_id,
        new_status=TicketStatus.RESOLVED_PENDING_REVIEW.value,
        operator_id=current_user.id,
    )
    return {"success": True, "status": ticket.status.value}


@router.put("/tickets/{ticket_id}/rate")
async def rate_ticket(
    ticket_id: int,
    data: TicketRate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """评价工单"""
    if data.rating < 1 or data.rating > 5:
        raise HTTPException(status_code=400, detail="评分必须在1-5之间")

    ticket = await ticket_service.rate_ticket(
        db=db,
        ticket_id=ticket_id,
        rating=data.rating,
        comment=data.rating_comment,
    )
    return {"success": True, "rating": ticket.rating}


@router.put("/tickets/{ticket_id}/remark")
async def add_remark(
    ticket_id: int,
    data: TicketRemark,
    current_user: User = Depends(require_permission("itsm_access")),
    db: AsyncSession = Depends(get_db),
):
    """添加备注"""
    ticket = await ticket_service.add_remark(
        db=db,
        ticket_id=ticket_id,
        operator_id=current_user.id,
        remark=data.remark,
        pause_sla=data.pause_ola,
    )
    return {"success": True}


@router.put("/tickets/{ticket_id}/pause-sla")
async def pause_sla(
    ticket_id: int,
    reason: str = "",
    current_user: User = Depends(require_permission("itsm_access")),
    db: AsyncSession = Depends(get_db),
):
    """暂停SLA计时"""
    await sla_service.pause_sla(db, ticket_id, reason)
    return {"success": True}


@router.put("/tickets/{ticket_id}/resume-sla")
async def resume_sla(
    ticket_id: int,
    current_user: User = Depends(require_permission("itsm_access")),
    db: AsyncSession = Depends(get_db),
):
    """恢复SLA计时"""
    await sla_service.resume_sla(db, ticket_id)
    return {"success": True}


@router.get("/tickets/{ticket_id}/logs")
async def get_ticket_logs(
    ticket_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """工单操作记录"""
    return await ticket_service.get_ticket_logs(db, ticket_id)


@router.put("/tickets/{ticket_id}/transfer")
async def transfer_ticket(
    ticket_id: int,
    data: TicketTransferRequest,
    current_user: User = Depends(require_permission("itsm_access")),
    db: AsyncSession = Depends(get_db),
):
    """转派工单"""
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="工单不存在")

    # 检查目标客服是否存在
    target_result = await db.execute(select(User).where(User.id == data.assignee_id))
    target_user = target_result.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=404, detail="目标客服不存在")

    old_assignee_id = ticket.assignee_id
    ticket.assignee_id = data.assignee_id
    ticket.status = TicketStatus.ACCEPTED

    # 记录日志
    log = TicketLog(
        ticket_id=ticket_id,
        operator_id=current_user.id,
        action="transfer",
        old_value=str(old_assignee_id),
        new_value=str(data.assignee_id),
        content=f"工单转派给{target_user.name}，原因：{data.reason}",
    )
    db.add(log)
    await db.commit()

    # 通知新客服
    try:
        from app.utils.websocket import ws_manager
        ticket_dict = ticket_service._ticket_to_dict(ticket)
        await ws_manager.notify_ticket_update(ticket_dict, [data.assignee_id])
    except Exception:
        pass

    return {"success": True, "assignee_name": target_user.name}


@router.put("/tickets/{ticket_id}/cancel")
async def cancel_ticket(
    ticket_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """取消工单（仅pending状态可取消）"""
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="工单不存在")

    # 只有创建者可以取消，且只能取消pending状态的工单
    if ticket.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="只有创建者可以取消工单")
    if ticket.status != TicketStatus.PENDING:
        raise HTTPException(status_code=400, detail="只有待接单状态的工单可以取消")

    old_status = ticket.status.value
    ticket.status = TicketStatus.RESOLVED
    ticket.resolved_at = datetime.now(timezone.utc)
    ticket.remark = "用户取消"

    log = TicketLog(
        ticket_id=ticket_id,
        operator_id=current_user.id,
        action="cancel",
        old_value=old_status,
        new_value="resolved",
        content="用户取消工单",
    )
    db.add(log)
    await db.commit()

    return {"success": True}


@router.put("/tickets/{ticket_id}/urge")
async def urge_ticket(
    ticket_id: int,
    data: TicketUrgeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """催办工单"""
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="工单不存在")

    if ticket.status in [TicketStatus.RESOLVED, TicketStatus.RESOLVED_PENDING_REVIEW]:
        raise HTTPException(status_code=400, detail="已解决的工单不能催办")

    # 记录催办日志
    urge_msg = data.message or "用户催办，请尽快处理"
    log = TicketLog(
        ticket_id=ticket_id,
        operator_id=current_user.id,
        action="urge",
        content=f"催办：{urge_msg}",
    )
    db.add(log)
    await db.commit()

    # 通知客服
    if ticket.assignee_id:
        try:
            from app.utils.websocket import ws_manager
            await ws_manager.send_to_user(ticket.assignee_id, {
                "type": "ticket_urge",
                "data": {
                    "ticket_id": ticket_id,
                    "ticket_no": ticket.ticket_no,
                    "message": urge_msg,
                },
            })
        except Exception:
            pass

    return {"success": True, "message": "催办已发送"}
