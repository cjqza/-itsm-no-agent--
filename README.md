# 公司桌面IT服务台

公司IT服务台管理系统，包含用户服务台、ITSM客服端、OPS统计和后台管理四大模块。

## 功能特性

### 🖥️ 用户服务台 (frontend-client)
- 首页机器人对话（关键词识别、自动回复）
- 一键转人工创建工单
- 工单列表与详情查看
- 实时聊天（WebSocket）
- 工单评价
- 催办/取消工单

### 📋 ITSM客服端 (frontend-agent)
- 仪表盘（今日工单、待处理、我的工单、预警）
- 工单池（手动接单）
- 工单详情（状态流转、分类、备注）
- 实时聊天（WebSocket）
- 工单转派
- SLA暂停/恢复
- 消息管理（未读提醒）

### 📊 OPS统计 (frontend-ops)
- 总览统计（工单数、评分、SLA达标率）
- 工单趋势图（ECharts）
- 按管理单元/客服/状态统计
- 评价统计与排名
- SLA达标率分析
- 历史工单查询
- 报表导出（Excel）

### ⚙️ 后台管理 (frontend)
- 用户管理（列表、启用/禁用）
- 权限管理（ITSM/OPS/后台三套权限）
- 权限申请与审批
- 分类配置CRUD（管理单元、业务模块、性质、症状、原因、解决方法）
- 客服管理

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.12+ / FastAPI |
| 数据库 | SQLite (开发) / MySQL (生产) |
| ORM | SQLAlchemy (异步) |
| 定时任务 | APScheduler |
| 前端 | Vue 3 / Element Plus / ECharts |
| 认证 | JWT |
| 实时通信 | WebSocket |

## 快速开始

### 一键启动

```bash
start.bat    # 启动所有服务
stop.bat     # 停止所有服务
```

### 单独启动

```bash
cd backend && python run.py                       # 后端 :8000
cd frontend-client && npm install && npm run dev  # 用户服务台 :5173
cd frontend-agent && npm install && npm run dev   # ITSM客服端 :5174
cd frontend && npm run dev -- --port 5175         # 后台管理 :5175
cd frontend-ops && npm install && npm run dev     # OPS统计 :5176
```

### 重置数据库

```bash
rm backend/it_ops.db && cd backend && python seed_data.py
```

## 默认账号

| 角色 | 飞书用户ID | 说明 |
|------|-----------|------|
| 管理员 | `admin` | 超级管理员，拥有所有权限 |
| 客服 | `agent_1` ~ `agent_5` | IT客服人员 |
| 用户 | `user1`, `user2` | 普通用户 |

登录时输入飞书用户ID即可，无需密码。

## 项目结构

```
program_last/
├── backend/                 # 后端服务
│   ├── app/
│   │   ├── api/            # API路由 (auth, itsm, chat, admin, ops, upload, templates)
│   │   ├── models/         # 数据模型 (user, ticket, category, permission, chat)
│   │   ├── schemas/        # Pydantic Schemas
│   │   ├── services/       # 业务逻辑 (ticket_service, sla_service)
│   │   ├── tasks/          # 定时任务 (sla_checker)
│   │   └── utils/          # 工具函数 (auth, websocket, ticket_no)
│   ├── tests/              # API测试
│   ├── seed_data.py        # 种子数据
│   └── run.py              # 启动入口
├── frontend-client/         # 用户服务台 :5173
├── frontend-agent/          # ITSM客服端 :5174
├── frontend/                # 后台管理 :5175
├── frontend-ops/            # OPS统计 :5176
├── start.bat               # 一键启动
├── stop.bat                # 一键停止
└── CLAUDE.md               # 开发指南
```

## API概览 (49个端点)

| 模块 | 端点数 | 主要功能 |
|------|--------|----------|
| 认证 | 3 | 登录、获取当前用户 |
| ITSM | 18 | 工单CRUD、生命周期、转派、取消、催办、SLA控制 |
| 聊天 | 7 | 房间管理、消息、WebSocket、已读状态 |
| 后台 | 15 | 用户管理、权限、分类CRUD |
| OPS | 7 | 统计、导出、趋势分析 |
| 上传 | 1 | 文件上传（图片/文档） |
| 模板 | 4 | 快捷回复模板 |
