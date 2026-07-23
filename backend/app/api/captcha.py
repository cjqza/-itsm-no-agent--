"""验证码模块 — 图片验证码生成与验证"""
import uuid
import time
import base64
import io
import random
import string
import threading
import logging

from captcha.image import ImageCaptcha
from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["验证码"])

# 内存存储: {captcha_id: (text, expire_time)}
_captcha_store: dict[str, tuple[str, float]] = {}
_CAPTCHA_TTL = 300  # 5 分钟
_CAPTCHA_CLEANUP_INTERVAL = 60  # 每 60 秒清理一次
_last_cleanup = time.time()


def _cleanup_expired():
    """清理过期验证码"""
    global _last_cleanup
    now = time.time()
    if now - _last_cleanup < _CAPTCHA_CLEANUP_INTERVAL:
        return
    _last_cleanup = now
    expired = [k for k, (_, exp) in _captcha_store.items() if now > exp]
    for k in expired:
        del _captcha_store[k]
    if expired:
        logger.info(f"清理过期验证码: {len(expired)} 个")


def _generate_text(length: int = 4) -> str:
    """生成随机验证码文本（字母+数字，排除易混淆字符）"""
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789"
    return "".join(random.choices(chars, k=length))


def generate_captcha() -> dict:
    """生成验证码，返回 {captcha_id, image(base64)}"""
    _cleanup_expired()

    captcha_id = uuid.uuid4().hex
    text = _generate_text()

    # 生成图片
    image_captcha = ImageCaptcha(width=160, height=60)
    image_data = image_captcha.generate(text)
    image_bytes = image_data.read()
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    # 存储（带过期时间）
    _captcha_store[captcha_id] = (text, time.time() + _CAPTCHA_TTL)

    return {
        "captcha_id": captcha_id,
        "image": f"data:image/png;base64,{image_b64}",
    }


def verify_captcha(captcha_id: str | None, text: str | None, test_mode: bool = False) -> bool:
    """验证验证码（一次性使用，验证后删除）。返回 True 表示通过。
    test_mode=True 时仅验证 captcha_id 是否存在（跳过文本比对，用于自动化测试）。
    """
    if not captcha_id:
        return False

    if not test_mode and not text:
        return False

    entry = _captcha_store.pop(captcha_id, None)
    if entry is None:
        return False

    expected_text, expire_time = entry
    if time.time() > expire_time:
        return False

    if test_mode:
        return True

    return text.strip().lower() == expected_text.lower()


@router.get("/captcha")
async def get_captcha():
    """获取验证码图片"""
    return generate_captcha()
