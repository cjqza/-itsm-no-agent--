from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.config import get_settings
from app.database import get_db, AsyncSessionLocal
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)
settings = get_settings()
security = HTTPBearer()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.JWT_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = decode_token(credentials.credentials)
    user_id = payload.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=401, detail="无效的Token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="用户不存在")

    return user


def require_permission(permission_field: str):
    """权限检查装饰器工厂"""
    async def check_permission(
        current_user: User = Depends(get_current_user),
    ):
        from app.models.permission import Permission
        from app.models.user import UserRole

        # 管理员和超级管理员自动拥有所有权限
        if current_user.role in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
            return current_user

        # 普通用户查Permission表
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Permission).where(Permission.user_id == current_user.id)
            )
            perm = result.scalar_one_or_none()

            if perm is None:
                logger.warning(f"PERM DENIED: user={current_user.id} ({current_user.name}), no permission record")
                raise HTTPException(status_code=403, detail="没有权限，请先申请权限")

            perm_value = getattr(perm, permission_field, False)
            if not perm_value:
                logger.warning(f"PERM DENIED: user={current_user.id} ({current_user.name}), {permission_field}={perm_value}")
                raise HTTPException(status_code=403, detail="没有访问权限")

        return current_user

    return check_permission
