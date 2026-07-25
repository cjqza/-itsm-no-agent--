"""工单模型"""
from sqlalchemy import (
    Column, Integer, String, Text, DateTime,
    ForeignKey, Enum as SQLEnum, Boolean
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum

from app.database import Base


class TicketStatus(str, enum.Enum):
    PENDING = "pending"                         # 待接单（客服工单池）
    ACCEPTED = "accepted"                       # 已接单
    PROCESSING = "processing"                   # 处理中
    RESOLVED_PENDING_REVIEW = "resolved_pending_review"  # 解决待评价
    RESOLVED = "resolved"                       # 已解决


class TicketPriority(str, enum.Enum):
    P1 = "P1"  # 紧急
    P2 = "P2"  # 高
    P3 = "P3"  # 中
    P4 = "P4"  # 低


class SLAStatus(str, enum.Enum):
    GREEN = "green"     # 正常
    YELLOW = "yellow"   # 预警
    RED = "red"         # 警告
    BLACK = "black"     # 超时


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_no = Column(String(32), unique=True, index=True, nullable=False)
    title = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)

    # 状态
    status = Column(SQLEnum(TicketStatus), default=TicketStatus.PENDING, nullable=False, index=True)
    priority = Column(SQLEnum(TicketPriority), default=TicketPriority.P3, nullable=False)

    # 分类
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True, index=True)
    business_module_id = Column(Integer, ForeignKey("business_modules.id"), nullable=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=True)
    symptom_id = Column(Integer, ForeignKey("symptoms.id"), nullable=True)
    cause_id = Column(Integer, ForeignKey("causes.id"), nullable=True)
    solution_id = Column(Integer, ForeignKey("solutions.id"), nullable=True)
    solution_text = Column(String(500), nullable=True)  # 自由填写的解决方法

    # 人员
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    # SLA
    sla_hours = Column(Integer, default=4)
    sla_deadline = Column(DateTime, nullable=True)
    sla_status = Column(SQLEnum(SLAStatus), default=SLAStatus.GREEN)
    is_sla_paused = Column(Boolean, default=False)
    sla_paused_at = Column(DateTime, nullable=True)
    sla_paused_reason = Column(String(512), nullable=True)
    sla_paused_seconds = Column(Integer, default=0)

    # 评价（四维评分）
    rating_attitude = Column(Integer, nullable=True)   # 服务态度 1-5
    rating_solution = Column(Integer, nullable=True)    # 解决方法 1-5
    rating_time = Column(Integer, nullable=True)       # 解决时间 1-5
    rating_overall = Column(Integer, nullable=True)    # 总体评价 1-5
    rating = Column(Integer, nullable=True)            # 总体评价（兼容旧字段）
    rating_comment = Column(Text, nullable=True)       # 反馈文字
    rated_at = Column(DateTime, nullable=True)

    # 备注
    remark = Column(Text, nullable=True)

    # 时间
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    accepted_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    # 关系
    creator = relationship("User", foreign_keys=[creator_id], back_populates="created_tickets")
    assignee = relationship("User", foreign_keys=[assignee_id], back_populates="assigned_tickets")
    category = relationship("Category", back_populates="tickets")
    business_module = relationship("BusinessModule", back_populates="tickets")
    property = relationship("Property", back_populates="tickets")
    symptom = relationship("Symptom", back_populates="tickets")
    cause = relationship("Cause", back_populates="tickets")
    solution = relationship("Solution", back_populates="tickets")
    logs = relationship("TicketLog", back_populates="ticket", order_by="TicketLog.created_at")
    chat_room = relationship("ChatRoom", back_populates="ticket", uselist=False)


class TicketLog(Base):
    __tablename__ = "ticket_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False, index=True)
    operator_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(64), nullable=False)
    old_value = Column(String(256), nullable=True)
    new_value = Column(String(256), nullable=True)
    content = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    ticket = relationship("Ticket", back_populates="logs")
    operator = relationship("User", foreign_keys=[operator_id])
