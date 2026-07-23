from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum

from app.database import Base


class RequestStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Permission(Base):
    """用户权限表"""
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    itsm_access = Column(Boolean, default=False)
    ops_access = Column(Boolean, default=False)
    admin_access = Column(Boolean, default=False)
    admin_approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="permission")
    approver = relationship("User", foreign_keys=[admin_approved_by])


class PermissionRequest(Base):
    """权限申请表"""
    __tablename__ = "permission_requests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    request_type = Column(String(32), nullable=False)  # itsm, ops, admin
    status = Column(SQLEnum(RequestStatus), default=RequestStatus.PENDING)
    reason = Column(String(512), nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
