"""工单Schemas"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class TicketCreate(BaseModel):
    title: str = Field(..., max_length=200)
    description: Optional[str] = Field(None, max_length=5000)
    priority: str = "P3"
    category_id: Optional[int] = None


class TicketUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    category_id: Optional[int] = None
    business_module_id: Optional[int] = None
    property_id: Optional[int] = None
    symptom_id: Optional[int] = None
    cause_id: Optional[int] = None
    solution_id: Optional[int] = None
    solution_text: Optional[str] = Field(None, max_length=500)
    remark: Optional[str] = None


class TicketStatusUpdate(BaseModel):
    status: str
    remark: Optional[str] = None


class TicketAssign(BaseModel):
    assignee_id: int


class TicketRate(BaseModel):
    rating_attitude: int = Field(..., ge=0, le=5, description="服务态度 0-5")
    rating_solution: int = Field(..., ge=0, le=5, description="解决方法 0-5")
    rating_time: int = Field(..., ge=0, le=5, description="解决时间 0-5")
    rating_overall: int = Field(..., ge=0, le=5, description="总体评价 0-5")
    rating_comment: Optional[str] = Field(None, max_length=500)


class TicketRemark(BaseModel):
    remark: str
    pause_ola: bool = False


class TicketMessage(BaseModel):
    content: str
    sender_id: int


class TicketLogOut(BaseModel):
    id: int
    ticket_id: int
    operator_id: Optional[int] = None
    operator_name: Optional[str] = None
    action: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    content: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TicketOut(BaseModel):
    id: int
    ticket_no: str
    title: str
    description: Optional[str] = None
    status: str
    priority: str
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    business_module_id: Optional[int] = None
    business_module_name: Optional[str] = None
    property_id: Optional[int] = None
    property_name: Optional[str] = None
    symptom_id: Optional[int] = None
    symptom_name: Optional[str] = None
    cause_id: Optional[int] = None
    cause_name: Optional[str] = None
    solution_id: Optional[int] = None
    solution_name: Optional[str] = None
    creator_id: int
    creator_name: Optional[str] = None
    assignee_id: Optional[int] = None
    assignee_name: Optional[str] = None
    sla_hours: int
    sla_deadline: Optional[datetime] = None
    sla_status: str
    is_sla_paused: bool
    rating: Optional[int] = None
    rating_comment: Optional[str] = None
    remark: Optional[str] = None
    created_at: datetime
    accepted_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TicketListOut(BaseModel):
    total: int
    items: List[TicketOut]
