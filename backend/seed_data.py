"""种子数据 - 用户、分类体系、历史工单"""
import asyncio
from app.database import AsyncSessionLocal, init_db
from app.models.user import User, UserRole, UserStatus
from app.models.category import Category, BusinessModule, Property, Symptom, Cause, Solution
from app.models.permission import Permission
from app.models.ticket import Ticket, TicketStatus, TicketLog, SLAStatus
from app.utils.ticket_no import generate_ticket_no
from app.utils.auth import hash_password
from datetime import datetime, timedelta, timezone


ADMIN_PASSWORD = "admin123"
DEFAULT_PASSWORD = "123456"


async def seed():
    """初始化种子数据（用户 + 历史工单）"""
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
        login_seq = 0
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

        # ============ 分类（基础） ============
        categories_data = [
            {"name": "操作系统", "description": "Windows/Mac/Linux系统相关问题", "sla_hours": 3},
            {"name": "邮件系统", "description": "Outlook/邮件相关问题", "sla_hours": 2},
            {"name": "网络问题", "description": "网络连接、VPN、WiFi等", "sla_hours": 4},
            {"name": "硬件故障", "description": "电脑、打印机、显示器等硬件", "sla_hours": 8},
            {"name": "账号权限", "description": "账号注册、密码重置、权限申请", "sla_hours": 4},
            {"name": "软件安装", "description": "软件安装、更新、卸载", "sla_hours": 4},
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
        business_modules = []
        for i, (cid, name) in enumerate(modules_data):
            bm = BusinessModule(category_id=cid, name=name, sort_order=i, created_by=admin.id)
            db.add(bm)
            business_modules.append(bm)

        await db.flush()

        # ============ 性质（全局） ============
        for name in ["故障", "需求", "咨询", "变更", "投诉"]:
            db.add(Property(name=name, created_by=admin.id))

        # ============ 症状/原因/解决方法 ============
        bm_data = {
            "Windows系统": {
                "symptoms": ["蓝屏", "死机", "卡顿", "无法开机"],
                "causes": ["系统文件损坏", "驱动冲突", "内存不足", "配置错误"],
                "solutions": ["重启电脑", "重装系统", "更新驱动", "系统还原"],
            },
            "Mac系统": {
                "symptoms": ["死机", "卡顿", "无法开机"],
                "causes": ["系统文件损坏", "内存不足"],
                "solutions": ["重启电脑", "重装系统", "磁盘修复"],
            },
            "Outlook客户端": {
                "symptoms": ["无法收发邮件", "邮件丢失", "附件打不开"],
                "causes": ["配置错误", "软件版本不兼容", "网络问题"],
                "solutions": ["重新配置账号", "更新软件", "清除缓存"],
            },
            "邮件服务器": {
                "symptoms": ["无法收发邮件", "邮件延迟"],
                "causes": ["服务器故障", "配置错误"],
                "solutions": ["联系管理员", "重启服务"],
            },
            "有线网络": {
                "symptoms": ["无法连接网络", "网络断断续续"],
                "causes": ["网线故障", "交换机故障", "配置错误"],
                "solutions": ["更换网线", "重启交换机", "修改配置"],
            },
            "WiFi": {
                "symptoms": ["无法连接WiFi", "信号弱"],
                "causes": ["AP故障", "配置错误", "信号干扰"],
                "solutions": ["重启AP", "修改配置", "调整位置"],
            },
            "VPN": {
                "symptoms": ["VPN连接失败", "VPN断连"],
                "causes": ["配置错误", "网络问题", "账号被锁定"],
                "solutions": ["重新配置", "重置密码", "联系管理员"],
            },
            "笔记本电脑": {
                "symptoms": ["无法开机", "屏幕不亮", "电池不充电"],
                "causes": ["硬件故障", "电池老化", "主板问题"],
                "solutions": ["更换电池", "现场处理", "返厂维修"],
            },
            "台式电脑": {
                "symptoms": ["无法开机", "蓝屏", "噪音大"],
                "causes": ["硬件故障", "内存不足", "灰尘堆积"],
                "solutions": ["重启电脑", "增加内存", "清理灰尘"],
            },
            "打印机": {
                "symptoms": ["打印异常", "无法打印", "卡纸"],
                "causes": ["缺纸", "墨盒耗尽", "驱动故障"],
                "solutions": ["添加纸张", "更换墨盒", "重新安装驱动"],
            },
            "密码重置": {
                "symptoms": ["无法登录", "密码过期"],
                "causes": ["密码过期", "账号被锁定"],
                "solutions": ["重置密码", "解锁账号"],
            },
            "权限申请": {
                "symptoms": ["无权限访问", "权限不足"],
                "causes": ["权限未开通", "权限过期"],
                "solutions": ["申请权限", "联系管理员"],
            },
        }

        for bm_name, data in bm_data.items():
            bm = next((b for b in business_modules if b.name == bm_name), None)
            if not bm:
                continue
            for name in data["symptoms"]:
                db.add(Symptom(name=name, business_module_id=bm.id, created_by=admin.id))
            for name in data["causes"]:
                db.add(Cause(name=name, business_module_id=bm.id, created_by=admin.id))
            for name in data["solutions"]:
                db.add(Solution(name=name, business_module_id=bm.id, created_by=admin.id))

        await db.flush()

        # ============ 历史工单（仅已解决） ============
        now = datetime.now(timezone.utc)
        tickets_data = [
            {
                "title": "电脑蓝屏无法开机",
                "desc": "开机后出现蓝屏错误代码0x0000007B，已尝试重启但问题依旧。",
                "cat": 0, "user": user1, "agent": agents[0],
                "status": TicketStatus.RESOLVED,
                "created": now - timedelta(days=3),
                "rating": 5, "comment": "张三处理很快，重启后恢复正常",
            },
            {
                "title": "Outlook无法收发邮件",
                "desc": "Outlook无法发送邮件，一直显示连接超时。重启客户端和电脑都没用。",
                "cat": 1, "user": user2, "agent": agents[1],
                "status": TicketStatus.RESOLVED,
                "created": now - timedelta(days=5),
                "rating": 4, "comment": "解决了，但等了比较久",
            },
            {
                "title": "无法连接公司WiFi",
                "desc": "新员工入职第一天，无法连接公司WiFi，提示密码错误但密码是正确的。",
                "cat": 2, "user": user1, "agent": agents[2],
                "status": TicketStatus.RESOLVED,
                "created": now - timedelta(days=7),
                "rating": 5, "comment": "很快就连上了，谢谢",
            },
            {
                "title": "打印机无法打印",
                "desc": "3楼打印机显示离线状态，所有同事都无法打印。已检查电源和网络连接。",
                "cat": 3, "user": user2, "agent": agents[0],
                "status": TicketStatus.RESOLVED,
                "created": now - timedelta(days=10),
                "rating": 5, "comment": "打印机修好了，非常感谢",
            },
            {
                "title": "密码过期需要重置",
                "desc": "域账号密码过期，无法登录电脑。需要重置密码。",
                "cat": 4, "user": user1, "agent": agents[2],
                "status": TicketStatus.RESOLVED,
                "created": now - timedelta(days=2),
                "rating": 5, "comment": "重置很快，马上就能用了",
            },
            {
                "title": "VPN连接失败",
                "desc": "在家办公无法连接公司VPN，提示认证失败。",
                "cat": 2, "user": user2, "agent": agents[3],
                "status": TicketStatus.RESOLVED,
                "created": now - timedelta(days=4),
                "rating": 4, "comment": "重新配置后可以了",
            },
            {
                "title": "软件安装请求",
                "desc": "需要安装Adobe Photoshop用于设计工作。",
                "cat": 5, "user": user1, "agent": agents[4],
                "status": TicketStatus.RESOLVED,
                "created": now - timedelta(days=6),
                "rating": 5, "comment": "安装顺利，已正常使用",
            },
        ]

        for i, t in enumerate(tickets_data):
            rating = t.get("rating", 5)
            comment = t.get("comment", "")
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
                sla_deadline=t["created"] + timedelta(hours=categories[t["cat"]].sla_hours),
                sla_status=SLAStatus.GREEN,
                created_at=t["created"],
                accepted_at=t["created"] + timedelta(minutes=10),
                resolved_at=t["created"] + timedelta(hours=2),
                rating=rating,
                rating_attitude=rating,
                rating_solution=rating,
                rating_time=rating,
                rating_overall=rating,
                rating_comment=comment,
            )
            db.add(ticket)
            await db.flush()

            # 操作日志
            db.add(TicketLog(ticket_id=ticket.id, operator_id=t["user"].id, action="created",
                            content=f"工单已创建: {t['title']}", created_at=t["created"]))
            db.add(TicketLog(ticket_id=ticket.id, operator_id=t["agent"].id, action="accepted",
                            content=f"{t['agent'].name} 已接单", created_at=t["created"] + timedelta(minutes=10)))
            db.add(TicketLog(ticket_id=ticket.id, operator_id=t["agent"].id, action="status_change",
                            old_value="processing", new_value="resolved", content="问题已解决",
                            created_at=t["created"] + timedelta(hours=2)))
            db.add(TicketLog(ticket_id=ticket.id, operator_id=t["user"].id, action="rated",
                            new_value=str(rating), content=comment,
                            created_at=t["created"] + timedelta(hours=3)))

        await db.commit()
        print(f"[OK] Seed data created:")
        print(f"  Admin: login_id=admin / password={ADMIN_PASSWORD} (super_admin)")
        print(f"  Agents: {', '.join(agent_names)} (login_id U00001-U00005, password={DEFAULT_PASSWORD})")
        print(f"  Users: 刘一(U00006), 陈二(U00007) (password={DEFAULT_PASSWORD})")
        print(f"  Categories: {len(categories_data)}")
        print(f"  Business modules: {len(modules_data)}")
        print(f"  Properties: 5 (故障/需求/咨询/变更/投诉)")
        print(f"  Symptoms/Causes/Solutions: {sum(len(d['symptoms']) for d in bm_data.values())}/{sum(len(d['causes']) for d in bm_data.values())}/{sum(len(d['solutions']) for d in bm_data.values())}")
        print(f"  Resolved tickets: {len(tickets_data)} (all with ratings)")


if __name__ == "__main__":
    asyncio.run(seed())
