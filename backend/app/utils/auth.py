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
    from sqlalchemy import func as sqlfunc
    result = await db.execute(
        select(sqlfunc.max(User.login_id)).where(User.login_id.like("U%"))
    )
    max_id = result.scalar()
    if max_id and max_id.startswith("U") and max_id[1:].isdigit():
        max_seq = int(max_id[1:])
    else:
        max_seq = 0
    return f"U{max_seq + 1:05d}"


# ============ 权限缓存（Redis 优先 + 内存 fallback） ============
_PERM_CACHE_TTL = 60  # 秒
_PERM_CACHE_MAX = 1000

# 内存 fallback：{ user_id: (itsm_access, ops_access, admin_access, expire_ts) }
_perm_cache: dict[int, tuple[bool, bool, bool, float]] = {}


async def _get_perm_from_cache(uid: int) -> tuple[bool, bool, bool] | None:
    """从缓存获取权限，优先 Redis，fallback 内存。返回 None 表示未命中。"""
    # 1) 尝试 Redis
    try:
        from app.utils.redis import get_redis
        r = await get_redis()
        if r is not None:
            data = await r.hgetall(f"perm:{uid}")
            if data:
                return (data.get("itsm") == "1", data.get("ops") == "1", data.get("admin") == "1")
    except Exception:
        pass

    # 2) fallback: 内存缓存
    now = time()
    cached = _perm_cache.get(uid)
    if cached and cached[3] > now:
        return (cached[0], cached[1], cached[2])
    return None


async def _set_perm_cache(uid: int, itsm: bool, ops: bool, admin: bool) -> None:
    """写入权限缓存（Redis + 内存双写）。"""
    # 1) Redis
    try:
        from app.utils.redis import get_redis
        r = await get_redis()
        if r is not None:
            key = f"perm:{uid}"
            pipe = r.pipeline()
            pipe.hset(key, mapping={
                "itsm": "1" if itsm else "0",
                "ops": "1" if ops else "0",
                "admin": "1" if admin else "0",
            })
            pipe.expire(key, _PERM_CACHE_TTL)
            await pipe.execute()
    except Exception:
        pass

    # 2) 内存 fallback
    now = time()
    if len(_perm_cache) >= _PERM_CACHE_MAX:
        _perm_cache.clear()
    _perm_cache[uid] = (itsm, ops, admin, now + _PERM_CACHE_TTL)


async def _invalidate_perm_cache(user_id: int) -> None:
    """清除指定用户的权限缓存（内存 + Redis）。"""
    _perm_cache.pop(user_id, None)
    try:
        from app.utils.redis import get_redis
        r = await get_redis()
        if r is not None:
            await r.delete(f"perm:{user_id}")
    except Exception as e:
        logger.warning(f"Redis 权限缓存删除失败: {e}")


def _invalidate_all_perm_cache() -> None:
    """清空全部权限缓存（仅内存；Redis 各 key 自带 TTL 会自动过期）。"""
    _perm_cache.clear()


async def has_permission(user: User, permission_field: str) -> bool:
    """检查用户是否拥有指定权限（带缓存），返回 bool 而非 raise。"""
    if user.role in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        return True

    cached = await _get_perm_from_cache(user.id)
    if cached is not None:
        itsm, ops, admin = cached
    else:
        async with AsyncSessionLocal() as db:
            from app.models.permission import Permission
            result = await db.execute(
                select(Permission).where(Permission.user_id == user.id)
            )
            perm = result.scalar_one_or_none()
        if perm is None:
            return False
        itsm = bool(perm.itsm_access)
        ops = bool(perm.ops_access)
        admin = bool(perm.admin_access)
        await _set_perm_cache(user.id, itsm, ops, admin)

    field_map = {"itsm_access": itsm, "ops_access": ops, "admin_access": admin}
    return field_map.get(permission_field, False)


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

        # 检查缓存（Redis 优先，fallback 内存）
        cached = await _get_perm_from_cache(uid)
        if cached is not None:
            itsm, ops, admin = cached
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

            # 写入缓存
            await _set_perm_cache(uid, itsm, ops, admin)

        # 校验对应字段
        field_map = {"itsm_access": itsm, "ops_access": ops, "admin_access": admin}
        perm_value = field_map.get(permission_field, False)
        if not perm_value:
            logger.warning(f"PERM DENIED: user={uid} ({current_user.name}), {permission_field}={perm_value}")
            raise HTTPException(status_code=403, detail="没有访问权限")

        return current_user

    return check_permission
