"""聊天模型 - 内置聊天系统"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum

from app.database import Base


class RoomStatus(str, enum.Enum):
    ACTIVE = "active"      # 活跃
    CLOSED = "closed"      # 已关闭


class MessageType(str, enum.Enum):
    TEXT = "text"          # 文本
    IMAGE = "image"        # 图片
    SYSTEM = "system"      # 系统消息


class ChatRoom(Base):
    """聊天室（一个工单对应一个聊天室）"""
    __tablename__ = "chat_rooms"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), unique=True, nullable=False)
    status = Column(SQLEnum(RoomStatus), default=RoomStatus.ACTIVE)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    closed_at = Column(DateTime, nullable=True)

    # Relationships
    ticket = relationship("Ticket", back_populates="chat_room")
    messages = relationship("ChatMessage", back_populates="room", order_by="ChatMessage.created_at")


class ChatMessage(Base):
    """聊天消息"""
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    room_id = Column(Integer, ForeignKey("chat_rooms.id"), nullable=False, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # None=系统消息
    content = Column(Text, nullable=False)
    msg_type = Column(SQLEnum(MessageType), default=MessageType.TEXT)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    room = relationship("ChatRoom", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id])
    read_records = relationship("ChatMessageRead", back_populates="message")


class ChatMessageRead(Base):
    """消息已读状态"""
    __tablename__ = "chat_message_reads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(Integer, ForeignKey("chat_messages.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    read_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    message = relationship("ChatMessage", back_populates="read_records")
    user = relationship("User", foreign_keys=[user_id])
