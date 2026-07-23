"""快捷回复模板API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.utils.auth import get_current_user, require_permission

router = APIRouter(prefix="/api/templates", tags=["快捷回复模板"])

# 内存存储（生产环境应使用数据库）
_templates: list[dict] = [
    {"id": 1, "title": "问候语", "content": "您好，我是IT客服{agent_name}，请问有什么可以帮您？", "category": "通用"},
    {"id": 2, "title": "需要更多信息", "content": "为了更好地帮助您，请提供以下信息：\n1. 问题截图\n2. 错误提示信息\n3. 问题发生时间", "category": "通用"},
    {"id": 3, "title": "远程协助", "content": "我将为您发起远程协助，请保持电脑联网状态。", "category": "技术支持"},
    {"id": 4, "title": "问题已解决", "content": "您的问题已解决，请确认是否恢复正常。如有其他问题随时联系。", "category": "通用"},
    {"id": 5, "title": "密码重置", "content": "您的密码已重置为：{temp_password}\n请登录后立即修改密码。", "category": "账号"},
    {"id": 6, "title": "等待处理", "content": "您的问题正在处理中，预计{eta}内完成，请耐心等待。", "category": "通用"},
]
_next_id = 7


class TemplateCreate(BaseModel):
    title: str
    content: str
    category: str = "通用"


class TemplateUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None


@router.get("")
async def list_templates(
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """获取快捷回复模板列表"""
    if category:
        return [t for t in _templates if t["category"] == category]
    return _templates


@router.post("")
async def create_template(
    data: TemplateCreate,
    current_user: User = Depends(require_permission("itsm_access")),
):
    """创建快捷回复模板"""
    global _next_id
    template = {
        "id": _next_id,
        "title": data.title,
        "content": data.content,
        "category": data.category,
        "created_by": current_user.id,
    }
    _next_id += 1
    _templates.append(template)
    return template


@router.put("/{template_id}")
async def update_template(
    template_id: int,
    data: TemplateUpdate,
    current_user: User = Depends(require_permission("itsm_access")),
):
    """更新快捷回复模板"""
    for t in _templates:
        if t["id"] == template_id:
            if data.title is not None:
                t["title"] = data.title
            if data.content is not None:
                t["content"] = data.content
            if data.category is not None:
                t["category"] = data.category
            return t
    raise HTTPException(status_code=404, detail="模板不存在")


@router.delete("/{template_id}")
async def delete_template(
    template_id: int,
    current_user: User = Depends(require_permission("itsm_access")),
):
    """删除快捷回复模板"""
    global _templates
    before = len(_templates)
    _templates = [t for t in _templates if t["id"] != template_id]
    if len(_templates) == before:
        raise HTTPException(status_code=404, detail="模板不存在")
    return {"success": True}
