from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum

from app.database import Base


class UserRole(str, enum.Enum):
    USER = "user"           # 普通用户（提单人）
    AGENT = "agent"         # 客服
    ADMIN = "admin"         # 管理员
    SUPER_ADMIN = "super_admin"  # 超级管理员


class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"  # 待审批（注册申请中）


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    feishu_user_id = Column(String(64), unique=True, index=True, nullable=True)
    login_id = Column(String(32), unique=True, index=True, nullable=True)  # 专属ID号，审批通过时生成，如 U00001
    password_hash = Column(String(256), nullable=True)  # 密码哈希（bcrypt）
    name = Column(String(128), nullable=False)
    email = Column(String(256), nullable=True)
    phone = Column(String(32), unique=True, index=True, nullable=True)  # 登录键，全局唯一
    avatar = Column(String(512), nullable=True)
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    department = Column(String(128), nullable=True)
    status = Column(SQLEnum(UserStatus), default=UserStatus.ACTIVE, nullable=False)
    is_online = Column(Boolean, default=False)  # 客服在线状态
    login_fail_count = Column(Integer, default=0)  # 密码错误计数
    locked_until = Column(DateTime, nullable=True)  # 锁定截止时间
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    created_tickets = relationship("Ticket", foreign_keys="Ticket.creator_id", back_populates="creator")
    assigned_tickets = relationship("Ticket", foreign_keys="Ticket.assignee_id", back_populates="assignee")
    permission = relationship("Permission", foreign_keys="Permission.user_id", back_populates="user", uselist=False)
