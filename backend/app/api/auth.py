"""认证API"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, UserRole, UserStatus
from app.models.permission import Permission
from app.utils.auth import create_access_token, get_current_user, verify_password, hash_password

router = APIRouter(prefix="/api/auth", tags=["认证"])


class LoginRequest(BaseModel):
    account: str = Field(..., min_length=1, max_length=64, description="专属ID或电话")
    password: str = Field(..., min_length=1, max_length=128)


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    phone: str = Field(..., min_length=5, max_length=32, pattern=r"^[0-9+\-() ]{5,32}$")
    password: str = Field(..., min_length=6, max_length=128)


class LoginResponse(BaseModel):
    token: str
    user: dict
    permissions: dict


def _build_permissions(user: User, perm: Permission | None) -> dict:
    is_admin = user.role in (UserRole.ADMIN, UserRole.SUPER_ADMIN)
    return {
        "itsm": True if is_admin else (perm.itsm_access if perm else False),
        "ops": True if is_admin else (perm.ops_access if perm else False),
        "admin": True if is_admin else (perm.admin_access if perm else False),
    }


@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """登录 - 账号（专属ID或电话）+ 密码"""
    account = req.account.strip()

    # 按 login_id 或 phone 查找用户
    result = await db.execute(
        select(User).where((User.login_id == account) | (User.phone == account))
    )
    user = result.scalar_one_or_none()

    # 统一错误信息，避免账号枚举
    if user is None or user.status != UserStatus.ACTIVE or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="账号或密码错误")

    token = create_access_token({"user_id": user.id, "role": user.role.value})

    perm_result = await db.execute(select(Permission).where(Permission.user_id == user.id))
    perm = perm_result.scalar_one_or_none()

    return {
        "token": token,
        "user": {
            "id": user.id,
            "name": user.name,
            "role": user.role.value,
            "login_id": user.login_id,
            "phone": user.phone,
        },
        "permissions": _build_permissions(user, perm),
    }


@router.post("/register")
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """账号申请 - 提交后进入待审批状态（无需鉴权）"""
    phone = req.phone.strip()

    # 电话全局唯一（任意状态）
    existing = await db.execute(select(User).where(User.phone == phone))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="该电话已注册")

    user = User(
        name=req.name.strip(),
        phone=phone,
        password_hash=hash_password(req.password),
        role=UserRole.USER,
        status=UserStatus.PENDING,
    )
    db.add(user)
    await db.flush()

    return {
        "success": True,
        "message": "申请已提交，等待管理员审批",
        "user_id": user.id,
    }


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """获取当前用户信息"""
    perm_result = await db.execute(select(Permission).where(Permission.user_id == current_user.id))
    perm = perm_result.scalar_one_or_none()

    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role.value,
        "login_id": current_user.login_id,
        "phone": current_user.phone,
        "permissions": _build_permissions(current_user, perm),
    }
