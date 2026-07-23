"""快捷回复模板API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.models.template import Template
from app.utils.auth import get_current_user, require_permission

router = APIRouter(prefix="/api/templates", tags=["快捷回复模板"])


class TemplateCreate(BaseModel):
    title: str = Field(..., max_length=100)
    content: str = Field(..., max_length=5000)
    category: str = "通用"


class TemplateUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=100)
    content: Optional[str] = Field(None, max_length=5000)
    category: Optional[str] = None


def _template_to_dict(t: Template) -> dict:
    return {
        "id": t.id,
        "title": t.title,
        "content": t.content,
        "category": t.category,
        "created_by": t.created_by,
    }


@router.get("")
async def list_templates(
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取快捷回复模板列表"""
    stmt = select(Template)
    if category:
        stmt = stmt.where(Template.category == category)
    result = await db.execute(stmt)
    templates = result.scalars().all()
    return [_template_to_dict(t) for t in templates]


@router.post("")
async def create_template(
    data: TemplateCreate,
    current_user: User = Depends(require_permission("itsm_access")),
    db: AsyncSession = Depends(get_db),
):
    """创建快捷回复模板"""
    template = Template(
        title=data.title,
        content=data.content,
        category=data.category,
        created_by=current_user.id,
    )
    db.add(template)
    await db.flush()
    await db.refresh(template)
    return _template_to_dict(template)


@router.put("/{template_id}")
async def update_template(
    template_id: int,
    data: TemplateUpdate,
    current_user: User = Depends(require_permission("itsm_access")),
    db: AsyncSession = Depends(get_db),
):
    """更新快捷回复模板"""
    result = await db.execute(select(Template).where(Template.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    if data.title is not None:
        template.title = data.title
    if data.content is not None:
        template.content = data.content
    if data.category is not None:
        template.category = data.category
    await db.flush()
    await db.refresh(template)
    return _template_to_dict(template)


@router.delete("/{template_id}")
async def delete_template(
    template_id: int,
    current_user: User = Depends(require_permission("itsm_access")),
    db: AsyncSession = Depends(get_db),
):
    """删除快捷回复模板"""
    result = await db.execute(select(Template).where(Template.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    await db.delete(template)
    return {"success": True}
