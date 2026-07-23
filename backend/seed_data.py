"""种子数据 - 初始化系统基础数据"""
import asyncio
from app.database import AsyncSessionLocal, init_db
from app.models.user import User, UserRole, UserStatus
from app.models.category import Category, BusinessModule, Property, Symptom, Cause, Solution
from app.models.permission import Permission
from app.models.ticket import Ticket, TicketStatus, TicketLog, SLAStatus
from app.utils.ticket_no import generate_ticket_no
from app.utils.auth import hash_password
from datetime import datetime, timedelta, timezone


# 初始密码（种子账号统一密码，生产环境请修改）
ADMIN_PASSWORD = "admin123"
DEFAULT_PASSWORD = "123456"


async def seed():
    """初始化种子数据"""
    await init_db()

    async with AsyncSessionLocal() as db:
        from sqlalchemy import select, func
        count = await db.execute(select(func.count(User.id)))
        if count.scalar() > 0:
            print("[SKIP] Database already has data")
            return

        print("[INIT] Seeding database...")

        # ============ 用户 ============
        admin = User(
            feishu_user_id="admin",
            login_id="admin",
            password_hash=hash_password(ADMIN_PASSWORD),
            name="系统管理员",
            email="admin@company.com",
            phone="10000000000",
            role=UserRole.SUPER_ADMIN,
            status=UserStatus.ACTIVE,
            is_online=1,
        )
        db.add(admin)

        agents = []
        agent_names = ["张三", "李四", "王五", "赵六", "钱七"]
        default_hash = hash_password(DEFAULT_PASSWORD)
        login_seq = 0  # 专属ID序号（U00001 起）
        for i, name in enumerate(agent_names):
            login_seq += 1
            agent = User(
                feishu_user_id=f"agent_{i+1}",
                login_id=f"U{login_seq:05d}",
                password_hash=default_hash,
                name=name,
                email=f"agent{i+1}@company.com",
                phone=f"1390000{i+1:04d}",
                role=UserRole.AGENT,
                status=UserStatus.ACTIVE,
                is_online=1 if i < 3 else 0,
            )
            db.add(agent)
            agents.append(agent)

        # 测试用户
        login_seq += 1
        user1 = User(feishu_user_id="user1", login_id=f"U{login_seq:05d}", password_hash=default_hash,
                     name="刘一", email="user1@company.com", phone="13900010001",
                     role=UserRole.USER, status=UserStatus.ACTIVE)
        login_seq += 1
        user2 = User(feishu_user_id="user2", login_id=f"U{login_seq:05d}", password_hash=default_hash,
                     name="陈二", email="user2@company.com", phone="13900010002",
                     role=UserRole.USER, status=UserStatus.ACTIVE)
        db.add(user1)
        db.add(user2)

        await db.flush()

        # ============ 权限 ============
        db.add(Permission(user_id=admin.id, itsm_access=True, ops_access=True, admin_access=True, admin_approved_by=admin.id))
        for agent in agents:
            db.add(Permission(user_id=agent.id, itsm_access=True, ops_access=True))
        db.add(Permission(user_id=user1.id))
        db.add(Permission(user_id=user2.id))

        # ============ 管理单元 ============
        categories_data = [
            {"name": "操作系统", "description": "Windows/Mac/Linux系统相关问题", "sla_hours": 3},
            {"name": "邮件系统", "description": "Outlook/邮件相关问题", "sla_hours": 2},
            {"name": "网络问题", "description": "网络连接、VPN、WiFi等", "sla_hours": 4},
            {"name": "硬件故障", "description": "电脑、打印机、显示器等硬件", "sla_hours": 8},
            {"name": "账号权限", "description": "账号注册、密码重置、权限申请", "sla_hours": 4},
            {"name": "软件安装", "description": "软件安装、更新、卸载", "sla_hours": 4},
            {"name": "咨询", "description": "不属于IT问题的咨询", "sla_hours": 24},
        ]

        categories = []
        for i, cat_data in enumerate(categories_data):
            cat = Category(name=cat_data["name"], description=cat_data["description"], sla_hours=cat_data["sla_hours"], sort_order=i, created_by=admin.id)
            db.add(cat)
            categories.append(cat)

        await db.flush()

        # ============ 业务模块 ============
        modules_data = [
            (categories[0].id, "Windows系统"), (categories[0].id, "Mac系统"),
            (categories[1].id, "Outlook客户端"), (categories[1].id, "邮件服务器"),
            (categories[2].id, "有线网络"), (categories[2].id, "WiFi"), (categories[2].id, "VPN"),
            (categories[3].id, "笔记本电脑"), (categories[3].id, "台式电脑"), (categories[3].id, "打印机"),
            (categories[4].id, "密码重置"), (categories[4].id, "权限申请"),
        ]
        for i, (cid, name) in enumerate(modules_data):
            db.add(BusinessModule(category_id=cid, name=name, sort_order=i, created_by=admin.id))

        # ============ 性质/症状/原因/解决方法 ============
        for name in ["故障", "需求", "咨询", "变更", "投诉"]:
            db.add(Property(name=name, created_by=admin.id))

        for name in ["蓝屏", "死机", "卡顿", "无法开机", "无法连接网络", "无法收发邮件", "软件闪退", "打印异常", "无法登录"]:
            db.add(Symptom(name=name, created_by=admin.id))

        for name in ["系统文件损坏", "驱动冲突", "内存不足", "配置错误", "网络设备故障", "账号被锁定", "软件版本不兼容", "操作失误"]:
            db.add(Cause(name=name, created_by=admin.id))

        for name in ["重启电脑", "重装系统", "更新驱动", "重置密码", "修改配置", "重新安装软件", "远程协助", "现场处理"]:
            db.add(Solution(name=name, created_by=admin.id))

        await db.flush()

        # ============ 示例工单 ============
        sample_tickets = [
            {"title": "电脑蓝屏无法开机", "desc": "今天早上开机后出现蓝屏错误代码0x0000007B", "cat": 0, "user": user1, "agent": agents[0], "status": TicketStatus.ACCEPTED},
            {"title": "Outlook无法收发邮件", "desc": "从昨天开始Outlook就无法发送邮件，一直显示连接超时", "cat": 1, "user": user2, "agent": agents[1], "status": TicketStatus.PROCESSING},
            {"title": "无法连接公司WiFi", "desc": "新员工入职第一天，无法连接公司WiFi", "cat": 2, "user": user1, "agent": None, "status": TicketStatus.PENDING},
            {"title": "打印机无法打印", "desc": "3楼打印机显示离线状态，所有同事都无法打印", "cat": 3, "user": user2, "agent": agents[0], "status": TicketStatus.RESOLVED_PENDING_REVIEW},
            {"title": "密码过期需要重置", "desc": "域账号密码过期，无法登录电脑", "cat": 4, "user": user1, "agent": agents[2], "status": TicketStatus.RESOLVED},
        ]

        for i, t in enumerate(sample_tickets):
            ticket = Ticket(
                ticket_no=await generate_ticket_no(db),
                title=t["title"],
                description=t["desc"],
                status=t["status"],
                priority="P2" if i < 2 else "P3",
                category_id=categories[t["cat"]].id,
                creator_id=t["user"].id,
                assignee_id=t["agent"].id if t["agent"] else None,
                sla_hours=categories[t["cat"]].sla_hours,
                sla_deadline=datetime.now(timezone.utc) + timedelta(hours=categories[t["cat"]].sla_hours),
                sla_status=SLAStatus.GREEN,
                accepted_at=datetime.now(timezone.utc) - timedelta(hours=1) if t["agent"] else None,
                resolved_at=datetime.now(timezone.utc) - timedelta(minutes=30) if t["status"] == TicketStatus.RESOLVED else None,
                rating=5 if t["status"] == TicketStatus.RESOLVED else None,
                rating_comment="非常满意" if t["status"] == TicketStatus.RESOLVED else None,
            )
            db.add(ticket)
            await db.flush()

            # 操作日志
            db.add(TicketLog(ticket_id=ticket.id, operator_id=t["user"].id, action="created", content=f"工单已创建: {t['title']}"))
            if t["agent"]:
                db.add(TicketLog(ticket_id=ticket.id, operator_id=t["agent"].id, action="accepted", content=f"{t['agent'].name} 已接单"))
            if t["status"] == TicketStatus.RESOLVED:
                db.add(TicketLog(ticket_id=ticket.id, operator_id=t["agent"].id, action="status_change", old_value="processing", new_value="resolved", content="问题已解决"))
                db.add(TicketLog(ticket_id=ticket.id, operator_id=t["user"].id, action="rated", new_value="5", content="非常满意"))

        await db.commit()
        print(f"[OK] Seed data created:")
        print(f"  Admin: login_id=admin / password={ADMIN_PASSWORD} (super_admin)")
        print(f"  Agents: {', '.join(agent_names)} (login_id U00001-U00005, password={DEFAULT_PASSWORD})")
        print(f"  Users: 刘一(U00006), 陈二(U00007) (password={DEFAULT_PASSWORD})")
        print(f"  Categories: {len(categories_data)}")
        print(f"  Sample tickets: {len(sample_tickets)}")


if __name__ == "__main__":
    asyncio.run(seed())
