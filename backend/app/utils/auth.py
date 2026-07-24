from datetime import datetime, timedelta, timezone
from time import time
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext
import logging

from app.config import get_settings
from app.database import get_db, AsyncSessionLocal
from app.models.user import User, UserRole, UserStatus

logger = logging.getLogger(__name__)
settings = get_settings()
security = HTTPBearer()

# 密码哈希上下文（bcrypt）
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """生成密码哈希"""
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: Optional[str]) -> bool:
    """校验密码；password_hash 为空时一律失败"""
    if not password_hash:
        return False
    try:
        return pwd_context.verify(password, password_hash)
    except Exception:
        return False


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

    # 仅允许 active 状态的用户通过鉴权（pending/inactive 一律拒绝）
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(status_code=401, detail="账号未激活或已被禁用")

    return user


async def generate_next_login_id(db: "AsyncSession") -> str:
    """生成下一个专属ID号，格式 U%05d（U00001 起递增）"""
    result = await db.execute(
        select(User.login_id).where(User.login_id.like("U%"))
    )
    max_seq = 0
    for (lid,) in result.all():
        if lid and lid.startswith("U") and lid[1:].isdigit():
            max_seq = max(max_seq, int(lid[1:]))
    return f"U{max_seq + 1:05d}"


# 权限缓存：{ user_id: (itsm_access, ops_access, admin_access, expire_ts) }
_perm_cache: dict[int, tuple[bool, bool, bool, float]] = {}
_PERM_CACHE_TTL = 60  # 秒
_PERM_CACHE_MAX = 1000


def _invalidate_perm_cache(user_id: int) -> None:
    """清除指定用户的权限缓存"""
    _perm_cache.pop(user_id, None)


def _invalidate_all_perm_cache() -> None:
    """清空全部权限缓存"""
    _perm_cache.clear()


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

        uid = current_user.id
        now = time()

        # 检查缓存
        cached = _perm_cache.get(uid)
        if cached and cached[3] > now:
            itsm, ops, admin = cached[0], cached[1], cached[2]
        else:
            # 查 DB
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(Permission).where(Permission.user_id == uid)
                )
                perm = result.scalar_one_or_none()

            if perm is None:
                logger.warning(f"PERM DENIED: user={uid} ({current_user.name}), no permission record")
                raise HTTPException(status_code=403, detail="没有权限，请先申请权限")

            itsm = bool(perm.itsm_access)
            ops = bool(perm.ops_access)
            admin = bool(perm.admin_access)

            # 防内存泄漏：缓存过大时清空
            if len(_perm_cache) >= _PERM_CACHE_MAX:
                _perm_cache.clear()

            _perm_cache[uid] = (itsm, ops, admin, now + _PERM_CACHE_TTL)

        # 校验对应字段
        field_map = {"itsm_access": itsm, "ops_access": ops, "admin_access": admin}
        perm_value = field_map.get(permission_field, False)
        if not perm_value:
            logger.warning(f"PERM DENIED: user={uid} ({current_user.name}), {permission_field}={perm_value}")
            raise HTTPException(status_code=403, detail="没有访问权限")

        return current_user

    return check_permission
