from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime, timezone

from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    operator_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # 操作人
    action = Column(String(50), nullable=False)  # 操作类型：create/update/delete/approve/reject
    target_type = Column(String(50), nullable=False)  # 目标类型：user/permission/agent/admin/permission_request
    target_id = Column(Integer, nullable=True)  # 目标ID
    detail = Column(String(500), nullable=True)  # 操作详情
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
