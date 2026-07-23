"""公司桌面IT服务台 - FastAPI入口"""
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from collections import defaultdict
import logging
import logging.handlers
import os
import time
import asyncio

from app.config import get_settings
from app.database import init_db
from app.api.auth import router as auth_router
from app.api.itsm import router as itsm_router
from app.api.ops import router as ops_router
from app.api.chat import router as chat_router
from app.api.admin import (
    router as admin_router,
    category_router, business_module_router,
    property_router, symptom_router, cause_router, solution_router,
)
from app.api.upload import router as upload_router
from app.api.templates import router as template_router

settings = get_settings()

# 日志配置：控制台 + 文件（RotatingFileHandler）
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

_log_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

_console_handler = logging.StreamHandler()
_console_handler.setFormatter(_log_formatter)

_file_handler = logging.handlers.RotatingFileHandler(
    os.path.join(LOG_DIR, "app.log"),
    maxBytes=10 * 1024 * 1024,  # 10MB
    backupCount=5,
    encoding="utf-8",
)
_file_handler.setFormatter(_log_formatter)

logging.basicConfig(
    level=logging.INFO,
    handlers=[_console_handler, _file_handler],
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    logger.info("正在初始化数据库...")
    await init_db()
    logger.info("数据库初始化完成")

    from app.tasks.sla_checker import start_sla_checker
    start_sla_checker()

    logger.info(f"{settings.APP_NAME} v{settings.APP_VERSION} 已启动")
    yield

    logger.info("应用关闭")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# CORS - 允许三个前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # 用户端
        "http://localhost:5174",   # 客服端
        "http://localhost:5175",   # 后台管理
        "http://localhost:5176",   # OPS统计
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://127.0.0.1:5176",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ 限流 ============
# 存储结构: {client_ip: {path_group: [timestamps]}}
_rate_limit_store: dict = defaultdict(lambda: defaultdict(list))
RATE_LIMIT_CLEANUP_INTERVAL = 60  # 每60秒清理一次过期记录
_last_cleanup = time.time()


def _get_client_ip(request: Request) -> str:
    """获取客户端真实IP"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _check_rate_limit(client_ip: str, path: str, limit: int, window: int = 60) -> bool:
    """检查是否超过限流，返回True表示允许，False表示限流"""
    global _last_cleanup
    now = time.time()

    # 定期清理过期记录
    if now - _last_cleanup > RATE_LIMIT_CLEANUP_INTERVAL:
        _last_cleanup = now
        expired_ips = []
        for ip in list(_rate_limit_store.keys()):
            for group in list(_rate_limit_store[ip].keys()):
                _rate_limit_store[ip][group] = [
                    t for t in _rate_limit_store[ip][group] if now - t < window
                ]
                if not _rate_limit_store[ip][group]:
                    del _rate_limit_store[ip][group]
            if not _rate_limit_store[ip]:
                expired_ips.append(ip)
        for ip in expired_ips:
            del _rate_limit_store[ip]

    # 确定限流分组
    if "/auth/login" in path:
        group = "login"
    else:
        group = "api"

    timestamps = _rate_limit_store[client_ip][group]
    # 清除窗口外的记录
    timestamps[:] = [t for t in timestamps if now - t < window]

    if len(timestamps) >= limit:
        return False

    timestamps.append(now)
    return True


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """限流中间件"""
    path = request.url.path

    # 跳过非API路径和WebSocket
    if path in ("/", "/health", "/docs", "/openapi.json", "/redoc"):
        return await call_next(request)
    if path.startswith("/api/chat/ws/"):
        return await call_next(request)

    client_ip = _get_client_ip(request)

    # 登录接口: 10次/分钟
    if "/auth/login" in path:
        if not _check_rate_limit(client_ip, path, limit=10, window=60):
            logger.warning(f"限流: {client_ip} 登录接口请求过于频繁")
            return JSONResponse(
                status_code=429,
                content={"detail": "请求过于频繁，请稍后再试"},
            )
    # 其他API: 120次/分钟
    elif path.startswith("/api/") or path.startswith("/admin/"):
        if not _check_rate_limit(client_ip, path, limit=120, window=60):
            logger.warning(f"限流: {client_ip} API请求过于频繁")
            return JSONResponse(
                status_code=429,
                content={"detail": "请求过于频繁，请稍后再试"},
            )

    return await call_next(request)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """请求日志"""
    start = time.time()
    response = await call_next(request)
    duration = round((time.time() - start) * 1000, 1)
    if request.url.path not in ("/health", "/"):
        logger.info(f"{request.method} {request.url.path} [{response.status_code}] {duration}ms")
    return response


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"未处理异常: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "服务器内部错误，请稍后重试"})


# 注册路由
app.include_router(auth_router)
app.include_router(itsm_router)
app.include_router(ops_router)
app.include_router(chat_router)
app.include_router(admin_router)
app.include_router(category_router)
app.include_router(business_module_router)
app.include_router(property_router)
app.include_router(symptom_router)
app.include_router(cause_router)
app.include_router(solution_router)
app.include_router(upload_router)
app.include_router(template_router)


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
