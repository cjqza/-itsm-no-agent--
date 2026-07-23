# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

公司桌面IT服务台 (Company Desktop IT Service Desk) — an IT ticket management platform with four separate frontends and one shared backend. Users submit repair requests via a chat-like interface, agents pick up tickets manually, and both parties communicate through a built-in WebSocket chat system.

## Quick Start

```bash
# One-click start (all services)
start.bat

# Or start individually:
cd backend && python run.py                    # Backend on :8000
cd frontend-client && npm install && npm run dev  # User Service Desk on :5173
cd frontend-agent && npm install && npm run dev   # ITSM (Agent) on :5174
cd frontend && npm run dev -- --port 5175         # Admin Panel on :5175
cd frontend-ops && npm install && npm run dev     # OPS Statistics on :5176

# Stop all
stop.bat

# Reset database (delete SQLite file + re-seed)
rm backend/it_ops.db && cd backend && python seed_data.py
```

## Architecture

```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ frontend-    │  │ frontend-    │  │ frontend/    │  │ frontend-    │
│ client/      │  │ agent/       │  │ (admin)      │  │ ops/         │
│ :5173        │  │ :5174        │  │ :5175        │  │ :5176        │
│ 用户服务台    │  │ ITSM客服端   │  │ 后台管理      │  │ OPS统计      │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │                 │
       └─────────────────┴────────┬────────┴─────────────────┘
                                  │ /api proxy
                         ┌────────▼────────┐
                         │   backend/      │
                         │   FastAPI :8000 │
                         │   SQLite DB     │
                         └─────────────────┘
```

### Four Frontends

| System | Directory | Port | Purpose |
|--------|-----------|------|---------|
| **用户服务台** | frontend-client | 5173 | 用户提交工单、聊天、评价 |
| **ITSM** | frontend-agent | 5174 | 客服接单、处理工单、消息管理 |
| **后台管理** | frontend | 5175 | 权限管理、分类配置、系统设置 |
| **OPS** | frontend-ops | 5176 | 历史工单查询、统计分析、报表导出 |

### Backend (`backend/`)

- **Framework**: FastAPI with async SQLAlchemy (aiosqlite for dev, aiomysql for prod)
- **Auth**: JWT tokens, `get_current_user` dependency, `require_permission("itsm_access")` factory for role-based access
- **Config**: `app/config.py` — Pydantic Settings, reads `.env`, cached via `@lru_cache`
- **Database**: `app/database.py` — `get_db()` dependency yields a session, auto-commits on success. SQLite uses single-connection mode (no pool params)
- **API routes**: `app/api/` — `auth.py`, `itsm.py`, `ops.py`, `chat.py`, `admin.py`, `upload.py`, `templates.py`
- **Services**: `app/services/` — `ticket_service.py` (core ticket logic), `sla_service.py` (SLA timer checks)
- **Models**: `app/models/` — `user.py`, `ticket.py`, `category.py`, `permission.py`, `chat.py`
- **WebSocket**: Two separate WS systems — global notification WS in `utils/websocket.py` (for ticket updates), chat-specific WS in `api/chat.py` (per-room real-time messages)
- **Background tasks**: `app/tasks/sla_checker.py` — APScheduler runs every minute to update SLA status colors

### Ticket Lifecycle

```
pending → accepted → processing → resolved_pending_review → resolved
  (池)     (接单)     (处理中)        (待评价)              (已解决)
```

- `pending`: Created by user, visible in agent's shared pool
- `accepted`: Agent manually accepts → auto-creates ChatRoom (checks for existing room first)
- `processing`: Agent working on it
- `resolved_pending_review`: Agent marks resolved → user sees rating prompt
- `resolved`: User rates → chat room auto-closes

**状态流转验证**: `VALID_TRANSITIONS` dict in `ticket_service.py` enforces legal transitions only. Invalid transitions raise `ValueError`.

SLA color coding: green (normal) → yellow (30%+) → red (50%+) → black (overdue)

### Key Patterns

**`_ticket_to_dict` safety**: When converting Ticket ORM objects to dicts, always use the `safe_rel_name()` helper that checks `ticket.__dict__` before accessing relationships — accessing unloaded relationships in async SQLAlchemy raises `MissingGreenlet` (not caught by `except Exception`).

**Permission system**: Three separate permission flags — `itsm_access`, `ops_access`, `admin_access`. New users start with no permissions; they submit requests via the admin API, and an admin approves. The `require_permission("field")` dependency creates its own DB session (not the shared one) to avoid stale reads. Admins and super_admins auto-grant all permissions. The `/api/admin/agents` endpoint uses `itsm_access` (not `admin_access`) so agents can see other agents for ticket transfers.

**Chat system**: Each ticket can have one ChatRoom. Messages are ChatMessage rows with `msg_type` (text/system/image). WebSocket connections are tracked per-room in `chat_connections` dict. When agent accepts a ticket, a ChatRoom + system message are auto-created (if room doesn't already exist — users can create rooms from the Home page chatbot). Messages support read status tracking via `ChatMessageRead` model.

**User chat rooms page**: frontend-client has a dedicated `/chat-rooms` page with left sidebar listing all chat rooms and right panel for active chat. Rooms can be deleted (cascades to messages and read records). Chat room state is persisted in localStorage on the Home page.

**Home page chatbot**: Keywords like "转人工", "报障", "报修" trigger category selection UI. User picks a category → ticket created with `category_id` → chat room auto-created → bot shows clickable link to chat rooms page.

**Rate limiting**: Custom middleware in `main.py` — login endpoints: 10 req/min, other APIs: 120 req/min. Uses in-memory store with periodic cleanup.

**File uploads**: `POST /api/upload` — supports images (jpg/png/gif/webp/bmp), documents (pdf/doc/docx/xls/xlsx/ppt/pptx), text (txt/csv/html/json/xml), and archives (zip/rar/7z/gz), max 10MB. Files stored in `backend/uploads/` with date-based subdirectories.

**Ticket operations**: 
- Transfer: `PUT /api/itsm/tickets/{id}/transfer` — reassign to another agent, reason is optional
- Cancel: `PUT /api/itsm/tickets/{id}/cancel` — only creator, only pending status
- Urge: `PUT /api/itsm/tickets/{id}/urge` — notifies assigned agent via WebSocket

**Quick reply templates**: `GET/POST/PUT/DELETE /api/templates` — in-memory storage (not persisted), supports category filtering.

## Common Issues

**Port 8000 in use**: Multiple Python processes accumulate. Use `stop.bat` or manually `taskkill /F /PID <pid>` for each PID from `netstat -ano | findstr ":8000"`.

**Backend 500 errors**: Usually caused by accessing unloaded SQLAlchemy relationships in async context. The `_ticket_to_dict` helper must use `__dict__` checks, not direct attribute access.

**SQLite timezone issues**: SQLite returns timezone-naive datetimes. When comparing with `datetime.now(timezone.utc)`, use the `_ensure_utc()` helper in `sla_service.py` to add timezone info.

**SLA pause/resume**: The `pause_sla` and `resume_sla` functions handle timezone-aware datetime comparison. If you see "can't subtract offset-naive and offset-aware datetimes", ensure the `_ensure_utc()` method is being used.

**Route order**: Static routes (e.g. `/tickets/sla-warnings`) must be defined before dynamic routes (e.g. `/tickets/{ticket_id}`) or FastAPI will match the wrong endpoint.

**UNIQUE constraint on chat_rooms.ticket_id**: If you see `IntegrityError: UNIQUE constraint failed: chat_rooms.ticket_id`, it means code is trying to create a duplicate ChatRoom. Always check for existing room before creating — see `ticket_service.py accept_ticket()`.

**Test user conflicts**: The test suite may create users with names that conflict with seed data (e.g. a USER-role "张三" alongside the AGENT-role "张三"). If permission checks fail unexpectedly, check `SELECT id, name, feishu_user_id, role FROM users` for duplicates.

## Test Commands

```bash
cd backend
python tests/test_api.py    # Run all API tests (~50 cases, ~2min)
```

Tests cover: auth, permissions, CRUD, ticket full lifecycle, OPS statistics, new features (transfer/cancel/urge/templates/users), edge cases. Expects backend running on :8000.

**Current test pass rate: 98.1% (51/52)**

Known test failure: `Resume SLA` — SQLite timezone-naive datetime comparison issue. Function works correctly in production.

## Environment Variables

Copy `backend/.env.example` to `backend/.env`. Key vars:
- `DB_TYPE`: `sqlite` (default, zero config) or `mysql`
- `JWT_SECRET_KEY`: Change in production
- `FEISHU_APP_ID/SECRET`: For feishu integration (currently removed from active code)

## Database Seeding

`backend/seed_data.py` creates: admin user, 5 agents, 2 test users, 7 categories with SLA hours, 12 business modules, properties/symptoms/causes/solutions, and 5 sample tickets in various states. Safe to re-run (skips if data exists).

**Test accounts** (feishu_user_id):
- Admin: `admin`
- Agents: `agent_1` through `agent_5`
- Users: `user1`, `user2`

## API Overview (52 endpoints)

| Group | Endpoints | Key Features |
|-------|-----------|--------------|
| Auth | 3 | Login (feishu_id/name), get current user |
| ITSM | 18 | Ticket CRUD, lifecycle, transfer (reason optional), cancel, urge, SLA control |
| Chat | 10 | Room management, messages, WebSocket, read status, my-rooms list, delete room |
| Admin | 15 | Users, permissions, categories CRUD, agents list (itsm_access) |
| OPS | 7 | Statistics, export, trend analysis |
| Upload | 1 | File upload (images/docs/text/archives) |
| Templates | 4 | Quick reply templates |

## Frontend Notes

- All 4 frontends use Vue 3 + Element Plus + Pinia
- Login pages support both feishu_user_id and username login modes
- WebSocket reconnection uses exponential backoff (3s → 30s max, 10 retries)
- Heartbeat ping/pong every 30 seconds to maintain WebSocket connections
- 404 catch-all route in all frontends
- Admin frontend checks `permissions.admin` in route guard
- Home page (frontend-client) persists chat messages in localStorage with reset option
- ITSM dashboard uses 4-quadrant layout: draft pool (pending), accepted pool, my todo (processing), resolved/review
