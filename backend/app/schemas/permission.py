from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class PermissionOut(BaseModel):
    id: int
    user_id: int
    user_name: Optional[str] = None
    itsm_access: bool
    ops_access: bool
    admin_access: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PermissionUpdate(BaseModel):
    itsm_access: Optional[bool] = None
    ops_access: Optional[bool] = None
    admin_access: Optional[bool] = None


class PermissionRequestCreate(BaseModel):
    request_type: str  # itsm, ops, admin
    reason: Optional[str] = None


class PermissionRequestReview(BaseModel):
    status: str  # approved, rejected


class PermissionRequestOut(BaseModel):
    id: int
    user_id: int
    user_name: Optional[str] = None
    request_type: str
    status: str
    reason: Optional[str] = None
    reviewer_name: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PermissionRequestListOut(BaseModel):
    total: int
    items: List[PermissionRequestOut]
