"""认证API"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db
from app.models.user import User, UserRole
from app.models.permission import Permission
from app.utils.auth import create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["认证"])


class LoginRequest(BaseModel):
    feishu_user_id: Optional[str] = None
    name: Optional[str] = None  # 开发模式下支持用名字登录


class LoginResponse(BaseModel):
    token: str
    user: dict
    permissions: dict


@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """登录 - 支持飞书ID或用户名"""
    if not req.feishu_user_id and not req.name:
        raise HTTPException(status_code=400, detail="请提供飞书用户ID或用户名")

    user = None

    # 优先用飞书ID查找
    if req.feishu_user_id:
        result = await db.execute(select(User).where(User.feishu_user_id == req.feishu_user_id))
        user = result.scalar_one_or_none()

    # 其次用名字查找
    if not user and req.name:
        result = await db.execute(select(User).where(User.name == req.name))
        user = result.scalar_one_or_none()

    # 自动创建用户
    if not user:
        user = User(
            feishu_user_id=req.feishu_user_id,
            name=req.name or f"用户_{(req.feishu_user_id or 'anon')[:8]}",
            role=UserRole.USER,
        )
        db.add(user)
        await db.flush()

        perm = Permission(user_id=user.id)
        db.add(perm)
        await db.flush()

    token = create_access_token({"user_id": user.id, "role": user.role.value})

    # 获取权限
    perm_result = await db.execute(select(Permission).where(Permission.user_id == user.id))
    perm = perm_result.scalar_one_or_none()

    # 管理员和超级管理员自动拥有所有权限
    is_admin = user.role in (UserRole.ADMIN, UserRole.SUPER_ADMIN)
    print(f"DEBUG LOGIN: user={user.name}, role={user.role}, is_admin={is_admin}", flush=True)

    return {
        "token": token,
        "user": {
            "id": user.id,
            "name": user.name,
            "role": user.role.value,
            "feishu_user_id": user.feishu_user_id,
        },
        "permissions": {
            "itsm": True if is_admin else (perm.itsm_access if perm else False),
            "ops": True if is_admin else (perm.ops_access if perm else False),
            "admin": True if is_admin else (perm.admin_access if perm else False),
        },
    }


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """获取当前用户信息"""
    perm_result = await db.execute(select(Permission).where(Permission.user_id == current_user.id))
    perm = perm_result.scalar_one_or_none()

    # 管理员和超级管理员自动拥有所有权限
    is_admin = current_user.role in (UserRole.ADMIN, UserRole.SUPER_ADMIN)
    print(f"DEBUG ME: user={current_user.name}, role={current_user.role}, is_admin={is_admin}", flush=True)

    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role.value,
        "feishu_user_id": current_user.feishu_user_id,
        "permissions": {
            "itsm": True if is_admin else (perm.itsm_access if perm else False),
            "ops": True if is_admin else (perm.ops_access if perm else False),
            "admin": True if is_admin else (perm.admin_access if perm else False),
        },
    }

