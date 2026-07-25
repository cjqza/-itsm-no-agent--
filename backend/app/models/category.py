from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum

from app.database import Base


class StatusEnum(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class Category(Base):
    """管理单元 - 工单类型分类（如：操作系统、邮件系统、网络问题等）"""
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    sla_hours = Column(Integer, default=4)  # 该类型的SLA时间（小时）
    sort_order = Column(Integer, default=0)
    status = Column(SQLEnum(StatusEnum), default=StatusEnum.ACTIVE)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    tickets = relationship("Ticket", back_populates="category")
    business_modules = relationship("BusinessModule", back_populates="category")
    creator = relationship("User", foreign_keys=[created_by])


class BusinessModule(Base):
    """业务模块 - 管理单元下的子分类"""
    __tablename__ = "business_modules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    sort_order = Column(Integer, default=0)
    status = Column(SQLEnum(StatusEnum), default=StatusEnum.ACTIVE)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    category = relationship("Category", back_populates="business_modules")
    tickets = relationship("Ticket", back_populates="business_module")
    symptoms = relationship("Symptom", back_populates="business_module")
    causes = relationship("Cause", back_populates="business_module")
    solutions = relationship("Solution", back_populates="business_module")
    creator = relationship("User", foreign_keys=[created_by])


class Property(Base):
    """性质"""
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    sort_order = Column(Integer, default=0)
    status = Column(SQLEnum(StatusEnum), default=StatusEnum.ACTIVE)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    tickets = relationship("Ticket", back_populates="property")
    creator = relationship("User", foreign_keys=[created_by])


class Symptom(Base):
    """症状"""
    __tablename__ = "symptoms"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    business_module_id = Column(Integer, ForeignKey("business_modules.id"), nullable=True, index=True)
    sort_order = Column(Integer, default=0)
    status = Column(SQLEnum(StatusEnum), default=StatusEnum.ACTIVE)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    business_module = relationship("BusinessModule", back_populates="symptoms")
    tickets = relationship("Ticket", back_populates="symptom")
    creator = relationship("User", foreign_keys=[created_by])


class Cause(Base):
    """原因"""
    __tablename__ = "causes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    business_module_id = Column(Integer, ForeignKey("business_modules.id"), nullable=True, index=True)
    sort_order = Column(Integer, default=0)
    status = Column(SQLEnum(StatusEnum), default=StatusEnum.ACTIVE)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    business_module = relationship("BusinessModule", back_populates="causes")
    tickets = relationship("Ticket", back_populates="cause")
    creator = relationship("User", foreign_keys=[created_by])


class Solution(Base):
    """解决方法"""
    __tablename__ = "solutions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    business_module_id = Column(Integer, ForeignKey("business_modules.id"), nullable=True, index=True)
    sort_order = Column(Integer, default=0)
    status = Column(SQLEnum(StatusEnum), default=StatusEnum.ACTIVE)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    business_module = relationship("BusinessModule", back_populates="solutions")
    tickets = relationship("Ticket", back_populates="solution")
    creator = relationship("User", foreign_keys=[created_by])
