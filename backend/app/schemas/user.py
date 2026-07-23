from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None


class UserCreate(UserBase):
    feishu_user_id: Optional[str] = None
    role: str = "user"


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    role: Optional[str] = None
    is_online: Optional[int] = None
    status: Optional[str] = None


class UserOut(UserBase):
    id: int
    feishu_user_id: Optional[str] = None
    avatar: Optional[str] = None
    role: str
    status: str
    is_online: int
    created_at: datetime

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    feishu_user_id: str
