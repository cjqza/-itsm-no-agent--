"""后台管理API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from pydantic import BaseModel
from datetime import datetime, timezone

from app.database import get_db
from app.models.user import User, UserRole, UserStatus
from app.models.permission import Permission, PermissionRequest, RequestStatus
from app.models.category import (
    Category, BusinessModule, Property, Symptom, Cause, Solution,
)
from app.schemas.category import (
    CategoryCreate, CategoryUpdate, CategoryOut,
    BusinessModuleCreate, BusinessModuleUpdate, BusinessModuleOut,
    GenericItemCreate, GenericItemUpdate, GenericItemOut,
)
from app.utils.auth import require_permission, get_current_user

router = APIRouter(prefix="/api/admin", tags=["后台管理"])


# ============ 用户管理 Schemas ============

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None


class UserStatusUpdate(BaseModel):
    status: str  # active / inactive


# ============ 用户管理 ============

@router.get("/users")
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    role: Optional[str] = None,
    current_user: User = Depends(require_permission("admin_access")),
    db: AsyncSession = Depends(get_db),
):
    """用户列表（分页）"""
    conditions = []
    if keyword:
        conditions.append(
            (User.name.like(f"%{keyword}%")) | (User.email.like(f"%{keyword}%"))
        )
    if role:
        conditions.append(User.role == role)

    # 计数
    count_query = select(func.count(User.id))
    if conditions:
        count_query = count_query.where(*conditions)
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 数据
    query = select(User)
    if conditions:
        query = query.where(*conditions)
    query = query.order_by(User.id)
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    users = result.scalars().all()

    return {
        "total": total,
        "items": [
            {
                "id": u.id,
                "name": u.name,
                "email": u.email,
                "phone": u.phone,
                "login_id": u.login_id,
                "role": u.role.value,
                "department": u.department,
                "status": u.status.value,
                "is_online": u.is_online,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ],
    }


@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    data: UserUpdate,
    current_user: User = Depends(require_permission("admin_access")),
    db: AsyncSession = Depends(get_db),
):
    """更新用户信息"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if data.name is not None:
        user.name = data.name
    if data.email is not None:
        user.email = data.email
    if data.phone is not None:
        user.phone = data.phone
    if data.department is not None:
        user.department = data.department

    user.updated_at = datetime.now(timezone.utc)
    await db.commit()
    return {"success": True}


@router.put("/users/{user_id}/status")
async def update_user_status(
    user_id: int,
    data: UserStatusUpdate,
    current_user: User = Depends(require_permission("admin_access")),
    db: AsyncSession = Depends(get_db),
):
    """启用/禁用用户"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 不能禁用自己
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="不能修改自己的状态")

    # 不能修改超级管理员
    if user.role == UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=400, detail="不能修改超级管理员状态")

    if data.status not in ("active", "inactive"):
        raise HTTPException(status_code=400, detail="状态值无效，必须为 active 或 inactive")

    user.status = UserStatus(data.status)
    user.updated_at = datetime.now(timezone.utc)
    await db.commit()
    return {"success": True, "status": user.status.value}


# ============ 权限管理 ============

@router.get("/permissions")
async def list_permissions(
    current_user: User = Depends(require_permission("admin_access")),
    db: AsyncSession = Depends(get_db),
):
    """权限列表"""
    result = await db.execute(
        select(Permission, User)
        .join(User, Permission.user_id == User.id)
        .order_by(User.id)
    )
    return [
        {
            "id": perm.id,
            "user_id": perm.user_id,
            "user_name": user.name,
            "user_role": user.role.value,
            "itsm_access": perm.itsm_access,
            "ops_access": perm.ops_access,
            "admin_access": perm.admin_access,
        }
        for perm, user in result.all()
    ]


@router.put("/permissions/{user_id}")
async def update_permission(
    user_id: int,
    itsm_access: Optional[bool] = None,
    ops_access: Optional[bool] = None,
    admin_access: Optional[bool] = None,
    current_user: User = Depends(require_permission("admin_access")),
    db: AsyncSession = Depends(get_db),
):
    """更新用户权限"""
    # 检查目标用户是否存在
    user_result = await db.execute(select(User).where(User.id == user_id))
    target_user = user_result.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 管理员和超级管理员的权限不可修改
    if target_user.role in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=400, detail="管理员权限不可修改")

    result = await db.execute(select(Permission).where(Permission.user_id == user_id))
    perm = result.scalar_one_or_none()

    if not perm:
        perm = Permission(user_id=user_id)
        db.add(perm)

    # 后台权限（admin_access）只能由 super_admin 修改
    if admin_access is not None and admin_access != bool(perm.admin_access):
        if current_user.role != UserRole.SUPER_ADMIN:
            raise HTTPException(status_code=403, detail="后台权限只能由 admin 修改，请联系 admin")

    if itsm_access is not None:
        perm.itsm_access = itsm_access
    if ops_access is not None:
        perm.ops_access = ops_access
    if admin_access is not None:
        perm.admin_access = admin_access
        if admin_access:
            perm.admin_approved_by = current_user.id

    await db.commit()
    return {"success": True}


# ============ 权限申请 ============

@router.post("/permission-requests")
async def create_permission_request(
    request_type: str,
    reason: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """用户提交权限申请（无需admin权限）"""
    # 检查是否已有待审批的同类申请
    existing = await db.execute(
        select(PermissionRequest).where(
            PermissionRequest.user_id == current_user.id,
            PermissionRequest.request_type == request_type,
            PermissionRequest.status == RequestStatus.PENDING,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="已有待审批的同类申请")

    req = PermissionRequest(
        user_id=current_user.id,
        request_type=request_type,
        reason=reason,
    )
    db.add(req)
    await db.commit()
    return {"success": True, "message": "权限申请已提交"}


@router.get("/permission-requests")
async def list_permission_requests(
    status: Optional[str] = None,
    current_user: User = Depends(require_permission("admin_access")),
    db: AsyncSession = Depends(get_db),
):
    """权限申请列表"""
    query = (
        select(PermissionRequest, User)
        .join(User, PermissionRequest.user_id == User.id)
    )
    if status:
        query = query.where(PermissionRequest.status == status)
    query = query.order_by(PermissionRequest.created_at.desc())

    result = await db.execute(query)
    return [
        {
            "id": req.id,
            "user_id": req.user_id,
            "user_name": user.name,
            "request_type": req.request_type,
            "status": req.status.value,
            "reason": req.reason,
            "created_at": req.created_at.isoformat() if req.created_at else None,
        }
        for req, user in result.all()
    ]


@router.put("/permission-requests/{request_id}")
async def review_permission_request(
    request_id: int,
    action: str,  # approved, rejected
    current_user: User = Depends(require_permission("admin_access")),
    db: AsyncSession = Depends(get_db),
):
    """审批权限申请"""
    result = await db.execute(
        select(PermissionRequest).where(PermissionRequest.id == request_id)
    )
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail="申请不存在")

    req.status = action
    req.reviewed_by = current_user.id
    from datetime import datetime, timezone
    req.reviewed_at = datetime.now(timezone.utc)

    # 如果批准，自动开通权限
    if action == "approved":
        perm_result = await db.execute(select(Permission).where(Permission.user_id == req.user_id))
        perm = perm_result.scalar_one_or_none()
        if not perm:
            perm = Permission(user_id=req.user_id)
            db.add(perm)

        if req.request_type == "itsm":
            perm.itsm_access = True
        elif req.request_type == "ops":
            perm.ops_access = True
        elif req.request_type == "admin":
            perm.admin_access = True
            perm.admin_approved_by = current_user.id

    await db.commit()
    return {"success": True}


# ============ 账号申请审批 ============

async def _generate_next_login_id(db: AsyncSession) -> str:
    """生成下一个专属ID号，格式 U%05d（U00001 起递增）"""
    result = await db.execute(
        select(User.login_id).where(User.login_id.like("U%"))
    )
    max_seq = 0
    for (lid,) in result.all():
        if lid and lid.startswith("U") and lid[1:].isdigit():
            max_seq = max(max_seq, int(lid[1:]))
    return f"U{max_seq + 1:05d}"


@router.get("/account-requests")
async def list_account_requests(
    status: str = Query("pending"),
    current_user: User = Depends(require_permission("admin_access")),
    db: AsyncSession = Depends(get_db),
):
    """账号申请列表（默认列出待审批账号）"""
    try:
        target_status = UserStatus(status)
    except ValueError:
        raise HTTPException(status_code=400, detail="状态值无效")

    result = await db.execute(
        select(User).where(User.status == target_status).order_by(User.created_at.desc())
    )
    users = result.scalars().all()
    return [
        {
            "id": u.id,
            "name": u.name,
            "phone": u.phone,
            "login_id": u.login_id,
            "role": u.role.value,
            "status": u.status.value,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in users
    ]


@router.put("/account-requests/{user_id}")
async def review_account_request(
    user_id: int,
    action: str = Query(..., description="approve 或 reject"),
    current_user: User = Depends(require_permission("admin_access")),
    db: AsyncSession = Depends(get_db),
):
    """审批账号申请：approve 分配 login_id 并激活；reject 置为 inactive"""
    if action not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="action 必须为 approve 或 reject")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if user.status != UserStatus.PENDING:
        raise HTTPException(status_code=400, detail="该账号不在待审批状态")

    if action == "approve":
        # 生成专属ID号（若已有则保留）
        if not user.login_id:
            user.login_id = await _generate_next_login_id(db)
        user.status = UserStatus.ACTIVE
        user.updated_at = datetime.now(timezone.utc)

        # 建立空权限记录
        perm_result = await db.execute(select(Permission).where(Permission.user_id == user.id))
        if not perm_result.scalar_one_or_none():
            db.add(Permission(user_id=user.id))

        await db.commit()
        return {"success": True, "action": "approve", "login_id": user.login_id}
    else:
        user.status = UserStatus.INACTIVE
        user.updated_at = datetime.now(timezone.utc)
        await db.commit()
        return {"success": True, "action": "reject"}


# ============ 分类管理 CRUD ============

def make_crud_router(
    model, create_schema, update_schema, out_schema,
    name: str, name_zh: str, prefix: str,
):
    """生成CRUD路由的工厂函数"""
    crud_router = APIRouter(prefix=f"/api/admin{prefix}", tags=[f"后台管理-{name_zh}"])

    @crud_router.get("/")
    async def list_items(
        current_user: User = Depends(require_permission("admin_access")),
        db: AsyncSession = Depends(get_db),
    ):
        result = await db.execute(select(model).order_by(model.sort_order, model.id))
        items = result.scalars().all()
        return [
            {k: v for k, v in item.__dict__.items() if not k.startswith("_")}
            for item in items
        ]

    @crud_router.post("/")
    async def create_item(
        data: create_schema,
        current_user: User = Depends(require_permission("admin_access")),
        db: AsyncSession = Depends(get_db),
    ):
        item = model(**data.model_dump(), created_by=current_user.id)
        db.add(item)
        await db.commit()
        return {"success": True, "id": item.id}

    @crud_router.get("/{item_id}")
    async def get_item(
        item_id: int,
        current_user: User = Depends(require_permission("admin_access")),
        db: AsyncSession = Depends(get_db),
    ):
        result = await db.execute(select(model).where(model.id == item_id))
        item = result.scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=404, detail=f"{name_zh}不存在")
        return {k: v for k, v in item.__dict__.items() if not k.startswith("_")}

    @crud_router.put("/{item_id}")
    async def update_item(
        item_id: int,
        data: update_schema,
        current_user: User = Depends(require_permission("admin_access")),
        db: AsyncSession = Depends(get_db),
    ):
        result = await db.execute(select(model).where(model.id == item_id))
        item = result.scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=404, detail=f"{name_zh}不存在")

        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(item, key, value)

        await db.commit()
        return {"success": True}

    @crud_router.delete("/{item_id}")
    async def delete_item(
        item_id: int,
        current_user: User = Depends(require_permission("admin_access")),
        db: AsyncSession = Depends(get_db),
    ):
        result = await db.execute(select(model).where(model.id == item_id))
        item = result.scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=404, detail=f"{name_zh}不存在")

        await db.delete(item)
        await db.commit()
        return {"success": True}

    return crud_router


# 注册各分类的CRUD路由
category_router = make_crud_router(Category, CategoryCreate, CategoryUpdate, CategoryOut, "category", "管理单元", "/categories")
business_module_router = make_crud_router(BusinessModule, BusinessModuleCreate, BusinessModuleUpdate, BusinessModuleOut, "business_module", "业务模块", "/business-modules")
property_router = make_crud_router(Property, GenericItemCreate, GenericItemUpdate, GenericItemOut, "property", "性质", "/properties")
symptom_router = make_crud_router(Symptom, GenericItemCreate, GenericItemUpdate, GenericItemOut, "symptom", "症状", "/symptoms")
cause_router = make_crud_router(Cause, GenericItemCreate, GenericItemUpdate, GenericItemOut, "cause", "原因", "/causes")
solution_router = make_crud_router(Solution, GenericItemCreate, GenericItemUpdate, GenericItemOut, "solution", "解决方法", "/solutions")


# ============ 客服管理 ============

@router.get("/agents")
async def list_agents(
    current_user: User = Depends(require_permission("itsm_access")),
    db: AsyncSession = Depends(get_db),
):
    """客服列表"""
    result = await db.execute(
        select(User).where(User.role == UserRole.AGENT).order_by(User.id)
    )
    agents = result.scalars().all()
    return [
        {
            "id": a.id,
            "name": a.name,
            "email": a.email,
            "is_online": a.is_online,
            "status": a.status.value,
        }
        for a in agents
    ]
