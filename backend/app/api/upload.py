"""文件上传API"""
import os
import uuid
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from app.utils.auth import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/upload", tags=["文件上传"])

# 上传配置
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# 允许的文件类型
ALLOWED_EXTENSIONS = {
    # 图片
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "image/bmp": ".bmp",
    # 文档
    "application/pdf": ".pdf",
    "application/msword": ".doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/vnd.ms-excel": ".xls",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "application/vnd.ms-powerpoint": ".ppt",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
    # 文本
    "text/plain": ".txt",
    "text/csv": ".csv",
    "text/html": ".html",
    "text/css": ".css",
    "text/javascript": ".js",
    "application/json": ".json",
    "application/xml": ".xml",
    # 压缩包
    "application/zip": ".zip",
    "application/x-rar-compressed": ".rar",
    "application/x-7z-compressed": ".7z",
    "application/gzip": ".gz",
    # 其他
    "application/octet-stream": ".bin",  # 通用二进制
}

# 确保上传目录存在
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """上传文件"""
    # 检查文件类型
    if file.content_type not in ALLOWED_EXTENSIONS:
        allowed_types = ", ".join(set(ALLOWED_EXTENSIONS.values()))
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {file.content_type}。允许的类型: {allowed_types}",
        )

    # 读取文件内容并检查大小
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制。最大允许: {MAX_FILE_SIZE // (1024 * 1024)}MB",
        )

    # 生成唯一文件名
    ext = ALLOWED_EXTENSIONS[file.content_type]
    date_prefix = datetime.now(timezone.utc).strftime("%Y%m%d")
    unique_name = f"{date_prefix}_{uuid.uuid4().hex[:12]}{ext}"

    # 按日期创建子目录
    date_dir = os.path.join(UPLOAD_DIR, date_prefix)
    os.makedirs(date_dir, exist_ok=True)

    file_path = os.path.join(date_dir, unique_name)

    # 写入文件
    try:
        with open(file_path, "wb") as f:
            f.write(content)
    except OSError as e:
        logger.error(f"文件写入失败: {e}")
        raise HTTPException(status_code=500, detail="文件保存失败")

    # 返回文件访问路径
    relative_path = f"uploads/{date_prefix}/{unique_name}"
    logger.info(f"文件上传成功: {relative_path}, 用户: {current_user.id}")

    return {
        "success": True,
        "filename": file.filename,
        "url": f"/{relative_path}",
        "size": len(content),
        "content_type": file.content_type,
    }
