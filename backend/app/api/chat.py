"""聊天API"""
import asyncio
import json
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import select, func, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone

from app.database import get_db, AsyncSessionLocal
from app.models.user import User
from app.models.ticket import Ticket, TicketStatus
from app.models.chat import ChatRoom, ChatMessage, RoomStatus, MessageType, ChatMessageRead
from app.utils.auth import get_current_user, decode_token, has_permission
from app.utils.websocket import ws_manager

router = APIRouter(prefix="/api/chat", tags=["聊天"])

import logging
logger = logging.getLogger(__name__)


class SendMessageRequest(BaseModel):
    content: str
    msg_type: str = "text"


# 聊天室连接管理
MAX_CHAT_CONNECTIONS_PER_USER = 5
chat_connections: dict[int, set] = {}  # room_id -> set of (websocket, user_id)


def _count_user_chat_connections(uid: int) -> int:
    """统计指定用户在所有聊天室中的连接数"""
    count = 0
    for conns in chat_connections.values():
        for ws, conn_uid in conns:
            if conn_uid == uid:
                count += 1
    return count


async def _check_room_access(room_id: int, current_user: User, db: AsyncSession) -> ChatRoom:
    """校验用户是否有权访问聊天室：创建者、被分配客服、或有 itsm_access（复用缓存）"""
    from app.models.user import UserRole

    result = await db.execute(
        select(ChatRoom)
        .options(selectinload(ChatRoom.ticket))
        .where(ChatRoom.id == room_id)
    )
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail="聊天室不存在")

    # 管理员自动放行
    if current_user.role in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        return room

    ticket = room.ticket
    if ticket and (ticket.creator_id == current_user.id or ticket.assignee_id == current_user.id):
        return room

    # 检查 itsm_access（复用缓存）
    if await has_permission(current_user, "itsm_access"):
        return room

    raise HTTPException(status_code=403, detail="无权访问此聊天室")


@router.post("/rooms/{ticket_id}")
async def create_chat_room(
    ticket_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建聊天室（接单时调用）"""
    # 检查工单
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="工单不存在")

    # 归属校验：仅工单创建者或有 itsm_access 的用户可创建聊天室
    if ticket.creator_id != current_user.id:
        from app.models.user import UserRole
        if current_user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
            if not await has_permission(current_user, "itsm_access"):
                raise HTTPException(status_code=403, detail="无权为此工单创建聊天室")

    # 检查是否已有聊天室，有则直接返回
    existing = await db.execute(
        select(ChatRoom).where(ChatRoom.ticket_id == ticket_id)
    )
    existing_room = existing.scalar_one_or_none()
    if existing_room:
        return {"room_id": existing_room.id, "ticket_id": ticket_id}

    # 创建聊天室
    room = ChatRoom(ticket_id=ticket_id)
    db.add(room)
    await db.flush()

    # 系统消息
    msg = ChatMessage(
        room_id=room.id,
        sender_id=None,
        content=f"聊天室已创建，工单号：{ticket.ticket_no}",
        msg_type=MessageType.SYSTEM,
    )
    db.add(msg)
    await db.commit()

    return {"room_id": room.id, "ticket_id": ticket_id}


@router.get("/my-rooms")
async def get_my_rooms(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的所有聊天室（含工单信息和最后一条消息）"""
    # 查询用户相关的工单对应的聊天室
    result = await db.execute(
        select(ChatRoom)
        .options(selectinload(ChatRoom.ticket))
        .join(Ticket, ChatRoom.ticket_id == Ticket.id)
        .where((Ticket.creator_id == current_user.id) | (Ticket.assignee_id == current_user.id))
        .order_by(ChatRoom.created_at.desc())
    )
    rooms = result.scalars().all()

    if not rooms:
        return []

    room_ids = [room.id for room in rooms]

    # 批量查询：每个房间的最后一条消息（通过 max(id) 子查询）
    last_msg_subq = (
        select(
            ChatMessage.room_id,
            func.max(ChatMessage.id).label("max_id"),
        )
        .where(ChatMessage.room_id.in_(room_ids))
        .group_by(ChatMessage.room_id)
        .subquery()
    )
    last_msg_result = await db.execute(
        select(ChatMessage).join(
            last_msg_subq, ChatMessage.id == last_msg_subq.c.max_id
        )
    )
    last_msgs = {msg.room_id: msg for msg in last_msg_result.scalars().all()}

    # 批量查询：每个房间的非本人消息总数
    total_result = await db.execute(
        select(
            ChatMessage.room_id,
            func.count(ChatMessage.id).label("cnt"),
        )
        .where(
            ChatMessage.room_id.in_(room_ids),
            ChatMessage.sender_id != current_user.id,
        )
        .group_by(ChatMessage.room_id)
    )
    total_counts = {row[0]: row[1] for row in total_result.all()}

    # 批量查询：每个房间的已读消息数
    read_result = await db.execute(
        select(
            ChatMessage.room_id,
            func.count(ChatMessageRead.id).label("cnt"),
        )
        .select_from(ChatMessageRead)
        .join(ChatMessage, ChatMessageRead.message_id == ChatMessage.id)
        .where(
            ChatMessage.room_id.in_(room_ids),
            ChatMessageRead.user_id == current_user.id,
        )
        .group_by(ChatMessage.room_id)
    )
    read_counts = {row[0]: row[1] for row in read_result.all()}

    # Python 中组装结果
    rooms_data = []
    for room in rooms:
        last_msg = last_msgs.get(room.id)
        total = total_counts.get(room.id, 0)
        read_count = read_counts.get(room.id, 0)
        unread = max(0, total - read_count)

        rooms_data.append({
            "id": room.id,
            "ticket_id": room.ticket_id,
            "ticket_no": room.ticket.ticket_no if room.ticket else None,
            "ticket_title": room.ticket.title if room.ticket else None,
            "ticket_status": room.ticket.status.value if room.ticket else None,
            "status": room.status.value,
            "created_at": room.created_at.isoformat() if room.created_at else None,
            "last_message": {
                "content": last_msg.content if last_msg else None,
                "created_at": last_msg.created_at.isoformat() if last_msg else None,
            } if last_msg else None,
            "unread": unread,
        })

    return rooms_data


@router.delete("/rooms/{room_id}")
async def delete_chat_room(
    room_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除聊天室及其所有消息"""
    result = await db.execute(
        select(ChatRoom)
        .options(selectinload(ChatRoom.ticket))
        .where(ChatRoom.id == room_id)
    )
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail="聊天室不存在")

    # 验证权限：只有工单创建者可以删除
    if room.ticket and room.ticket.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权删除此聊天室")

    # 仅允许已解决/待评价状态的工单删除聊天室
    if room.ticket and room.ticket.status not in (TicketStatus.RESOLVED, TicketStatus.RESOLVED_PENDING_REVIEW):
        raise HTTPException(status_code=400, detail="工单未完成，不能删除聊天室")

    # 删除已读记录
    msg_ids_result = await db.execute(
        select(ChatMessage.id).where(ChatMessage.room_id == room_id)
    )
    msg_ids = [row[0] for row in msg_ids_result.all()]
    if msg_ids:
        await db.execute(
            sa_delete(ChatMessageRead).where(ChatMessageRead.message_id.in_(msg_ids))
        )

    # 删除消息
    await db.execute(sa_delete(ChatMessage).where(ChatMessage.room_id == room_id))

    # 删除聊天室
    await db.delete(room)
    await db.commit()

    return {"success": True}


@router.get("/rooms/{ticket_id}")
async def get_chat_room(
    ticket_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取工单对应的聊天室"""
    result = await db.execute(
        select(ChatRoom).where(ChatRoom.ticket_id == ticket_id)
    )
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail="聊天室不存在")

    # 归属校验：通过 _check_room_access 检查
    await _check_room_access(room.id, current_user, db)

    return {
        "id": room.id,
        "ticket_id": room.ticket_id,
        "status": room.status.value,
        "created_at": room.created_at.isoformat() if room.created_at else None,
    }


@router.get("/rooms/{room_id}/messages")
async def get_messages(
    room_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取聊天记录（分页）"""
    # 权限校验
    await _check_room_access(room_id, current_user, db)

    # 总数
    count_result = await db.execute(
        select(func.count(ChatMessage.id)).where(ChatMessage.room_id == room_id)
    )
    total = count_result.scalar() or 0

    # 分页查询
    result = await db.execute(
        select(ChatMessage)
        .options(selectinload(ChatMessage.sender))
        .where(ChatMessage.room_id == room_id)
        .order_by(ChatMessage.created_at)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    messages = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": msg.id,
                "sender_id": msg.sender_id,
                "sender_name": msg.sender.name if msg.sender else "系统",
                "content": msg.content,
                "msg_type": msg.msg_type.value,
                "created_at": msg.created_at.isoformat() if msg.created_at else None,
            }
            for msg in messages
        ],
    }


@router.post("/rooms/{room_id}/messages")
async def send_message(
    room_id: int,
    data: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """发送消息"""
    # 权限校验 + 检查聊天室
    room = await _check_room_access(room_id, current_user, db)
    if room.status == RoomStatus.CLOSED:
        raise HTTPException(status_code=400, detail="聊天室已关闭")

    # 验证消息类型
    try:
        msg_type = MessageType(data.msg_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"不支持的消息类型: {data.msg_type}")

    # 保存消息
    msg = ChatMessage(
        room_id=room_id,
        sender_id=current_user.id,
        content=data.content,
        msg_type=msg_type,
    )
    db.add(msg)
    await db.commit()

    # 构造消息数据
    msg_data = {
        "type": "chat_message",
        "room_id": room_id,
        "message": {
            "id": msg.id,
            "sender_id": current_user.id,
            "sender_name": current_user.name,
            "content": data.content,
            "msg_type": data.msg_type,
            "created_at": msg.created_at.isoformat() if msg.created_at else None,
        },
    }

    # 通过WebSocket广播给聊天室内的所有用户
    await _broadcast_to_room(room_id, msg_data)

    return msg_data["message"]


@router.put("/rooms/{room_id}/close")
async def close_chat_room(
    room_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """关闭聊天室"""
    room = await _check_room_access(room_id, current_user, db)

    room.status = RoomStatus.CLOSED
    room.closed_at = datetime.now(timezone.utc)

    # 系统消息
    msg = ChatMessage(
        room_id=room_id,
        sender_id=None,
        content="聊天室已关闭",
        msg_type=MessageType.SYSTEM,
    )
    db.add(msg)
    await db.commit()

    # 通知所有用户
    await _broadcast_to_room(room_id, {
        "type": "room_closed",
        "room_id": room_id,
    })

    return {"success": True}


@router.post("/rooms/{room_id}/read")
async def mark_messages_read(
    room_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """标记房间内所有消息为已读"""
    # 权限校验
    await _check_room_access(room_id, current_user, db)

    # 获取房间内该用户未读的消息
    result = await db.execute(
        select(ChatMessage.id)
        .where(
            ChatMessage.room_id == room_id,
            ChatMessage.sender_id != current_user.id,  # 不标记自己发的消息
        )
    )
    message_ids = [row[0] for row in result.all()]

    if not message_ids:
        return {"marked": 0}

    # 检查哪些消息已经标记过已读
    existing = await db.execute(
        select(ChatMessageRead.message_id)
        .where(
            ChatMessageRead.message_id.in_(message_ids),
            ChatMessageRead.user_id == current_user.id,
        )
    )
    already_read = {row[0] for row in existing.all()}

    # 插入新的已读记录
    new_reads = []
    for msg_id in message_ids:
        if msg_id not in already_read:
            new_reads.append(ChatMessageRead(
                message_id=msg_id,
                user_id=current_user.id,
                read_at=datetime.now(timezone.utc),
            ))

    if new_reads:
        db.add_all(new_reads)
        await db.commit()

    return {"marked": len(new_reads)}


@router.get("/rooms/{room_id}/unread")
async def get_unread_count(
    room_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取房间内未读消息数量"""
    # 权限校验
    await _check_room_access(room_id, current_user, db)

    # 总消息数（不含自己发的）
    total_result = await db.execute(
        select(func.count(ChatMessage.id))
        .where(
            ChatMessage.room_id == room_id,
            ChatMessage.sender_id != current_user.id,
        )
    )
    total = total_result.scalar() or 0

    # 已读消息数
    read_result = await db.execute(
        select(func.count(ChatMessageRead.id))
        .where(
            ChatMessageRead.user_id == current_user.id,
            ChatMessageRead.message_id.in_(
                select(ChatMessage.id).where(ChatMessage.room_id == room_id)
            ),
        )
    )
    read_count = read_result.scalar() or 0

    return {"unread": max(0, total - read_count)}


class UnreadSummaryRequest(BaseModel):
    room_ids: list[int]


@router.post("/unread-summary")
async def get_unread_summary(
    data: UnreadSummaryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """批量查询多个房间的未读消息数"""
    if not data.room_ids:
        return {}

    # 批量查询：每个房间的非本人消息总数
    total_result = await db.execute(
        select(
            ChatMessage.room_id,
            func.count(ChatMessage.id).label("cnt"),
        )
        .where(
            ChatMessage.room_id.in_(data.room_ids),
            ChatMessage.sender_id != current_user.id,
        )
        .group_by(ChatMessage.room_id)
    )
    total_counts = {row[0]: row[1] for row in total_result.all()}

    # 批量查询：每个房间的已读消息数
    read_result = await db.execute(
        select(
            ChatMessage.room_id,
            func.count(ChatMessageRead.id).label("cnt"),
        )
        .select_from(ChatMessageRead)
        .join(ChatMessage, ChatMessageRead.message_id == ChatMessage.id)
        .where(
            ChatMessage.room_id.in_(data.room_ids),
            ChatMessageRead.user_id == current_user.id,
        )
        .group_by(ChatMessage.room_id)
    )
    read_counts = {row[0]: row[1] for row in read_result.all()}

    return {
        str(room_id): max(0, total_counts.get(room_id, 0) - read_counts.get(room_id, 0))
        for room_id in data.room_ids
    }


# ============ WebSocket ============

@router.websocket("/ws/{room_id}")
async def websocket_chat(websocket: WebSocket, room_id: int, token: str = ""):
    """WebSocket聊天连接"""
    if not token:
        await websocket.close(code=4001, reason="缺少token")
        return

    try:
        payload = decode_token(token)
        user_id = payload.get("user_id")
        if not user_id:
            await websocket.close(code=4001, reason="无效token")
            return
    except Exception:
        await websocket.close(code=4001, reason="token验证失败")
        return

    # 权限校验：检查用户是否有权访问此聊天室
    async with AsyncSessionLocal() as access_db:
        try:
            access_result = await access_db.execute(
                select(ChatRoom)
                .options(selectinload(ChatRoom.ticket))
                .where(ChatRoom.id == room_id)
            )
            access_room = access_result.scalar_one_or_none()
            if not access_room:
                await websocket.close(code=4003, reason="聊天室不存在")
                return
            if access_room.ticket:
                from app.models.user import UserRole
                has_access = False
                ws_user = None
                if access_room.ticket.creator_id == user_id or access_room.ticket.assignee_id == user_id:
                    has_access = True
                if not has_access:
                    user_result = await access_db.execute(select(User).where(User.id == user_id))
                    ws_user = user_result.scalar_one_or_none()
                    if ws_user and ws_user.role in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
                        has_access = True
                if not has_access:
                    if ws_user and await has_permission(ws_user, "itsm_access"):
                        has_access = True
                if not has_access:
                    await websocket.close(code=4003, reason="无权访问此聊天室")
                    return
        except Exception:
            await websocket.close(code=4003, reason="权限校验失败")
            return

    # 检查每用户连接数限制
    if _count_user_chat_connections(user_id) >= MAX_CHAT_CONNECTIONS_PER_USER:
        await websocket.close(code=1008, reason="聊天连接数超限")
        return

    await websocket.accept()

    # 注册连接
    if room_id not in chat_connections:
        chat_connections[room_id] = set()
    chat_connections[room_id].add((websocket, user_id))

    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
                continue

            # 处理消息
            try:
                msg = json.loads(data)
                if msg.get("type") == "chat_message":
                    # 保存到数据库
                    async with AsyncSessionLocal() as db:
                        chat_msg = ChatMessage(
                            room_id=room_id,
                            sender_id=user_id,
                            content=msg.get("content", ""),
                            msg_type=MessageType.TEXT,
                        )
                        db.add(chat_msg)
                        await db.commit()

                        # 获取发送者名字
                        user_result = await db.execute(select(User).where(User.id == user_id))
                        user = user_result.scalar_one_or_none()

                        # 广播
                        await _broadcast_to_room(room_id, {
                            "type": "chat_message",
                            "room_id": room_id,
                            "message": {
                                "id": chat_msg.id,
                                "sender_id": user_id,
                                "sender_name": user.name if user else "用户",
                                "content": msg.get("content", ""),
                                "msg_type": "text",
                                "created_at": chat_msg.created_at.isoformat() if chat_msg.created_at else None,
                            },
                        })
            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        pass
    finally:
        # 清理连接
        if room_id in chat_connections:
            chat_connections[room_id].discard((websocket, user_id))
            if not chat_connections[room_id]:
                del chat_connections[room_id]


async def _broadcast_to_room(room_id: int, data: dict):
    """广播消息到聊天室内的所有用户"""
    connections = chat_connections.get(room_id, set())
    if not connections:
        return
    conns_list = list(connections)
    results = await asyncio.gather(
        *[ws.send_json(data) for ws, uid in conns_list],
        return_exceptions=True,
    )
    # 清理断开的连接
    dead = {conn for conn, r in zip(conns_list, results) if isinstance(r, Exception)}
    for item in dead:
        connections.discard(item)
