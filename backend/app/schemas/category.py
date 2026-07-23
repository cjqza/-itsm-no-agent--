from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# Category (管理单元)
class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None
    sla_hours: int = 4
    sort_order: int = 0


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    sla_hours: Optional[int] = None
    sort_order: Optional[int] = None
    status: Optional[str] = None


class CategoryOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    sla_hours: int
    sort_order: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# BusinessModule (业务模块)
class BusinessModuleCreate(BaseModel):
    category_id: int
    name: str
    description: Optional[str] = None
    sort_order: int = 0


class BusinessModuleUpdate(BaseModel):
    category_id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    sort_order: Optional[int] = None
    status: Optional[str] = None


class BusinessModuleOut(BaseModel):
    id: int
    category_id: int
    category_name: Optional[str] = None
    name: str
    description: Optional[str] = None
    sort_order: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# Generic for Property, Symptom, Cause, Solution
class GenericItemCreate(BaseModel):
    name: str
    description: Optional[str] = None
    sort_order: int = 0


class GenericItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    sort_order: Optional[int] = None
    status: Optional[str] = None


class GenericItemOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    sort_order: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
