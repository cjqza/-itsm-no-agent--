"""Redis 连接工具 — 共享异步 Redis 客户端，支持自动降级到内存存储。

当 Redis 不可用时（连接失败、REDIS_HOST 为空等），get_redis() 返回 None，
调用方应 fallback 到内存存储，保证系统不因 Redis 故障而不可用。
"""
import logging
import time
from typing import Optional

import redis.asyncio as redis

from app.config import get_settings

logger = logging.getLogger(__name__)

_redis_client: Optional[redis.Redis] = None
_redis_available: Optional[bool] = None  # None=未测试, True=可用, False=不可用
_last_retry_ts: float = 0.0
_RETRY_INTERVAL: float = 30.0  # 不可用时每 30 秒重试一次


async def get_redis() -> Optional[redis.Redis]:
    """获取 Redis 客户端。不可用时返回 None（调用方应 fallback 到内存存储）。"""
    global _redis_client, _redis_available, _last_retry_ts

    settings = get_settings()
    url = settings.REDIS_URL  # REDIS_URL 为空 → 显式禁用 Redis
    if not url:
        _redis_available = False
        return None

    # 已确认可用 → 直接返回
    if _redis_available is True and _redis_client is not None:
        return _redis_client

    # 已确认不可用 → 定期重试
    if _redis_available is False:
        now = time.time()
        if now - _last_retry_ts < _RETRY_INTERVAL:
            return None
        _last_retry_ts = now

    # 首次连接或重试
    try:
        _redis_client = redis.from_url(
            url,
            decode_responses=True,
            socket_connect_timeout=2,
        )
        await _redis_client.ping()
        _redis_available = True
        logger.info(f"Redis 连接成功: {url}")
        return _redis_client
    except Exception as e:
        logger.warning(f"Redis 连接失败，降级到内存存储: {e}")
        _redis_client = None
        _redis_available = False
        _last_retry_ts = time.time()
        return None


async def close_redis() -> None:
    """关闭 Redis 连接（应用关闭时调用）。"""
    global _redis_client, _redis_available
    if _redis_client is not None:
        try:
            await _redis_client.close()
        except Exception:
            pass
        _redis_client = None
        _redis_available = None
