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

# Run tests
cd backend && python tests/test_api.py    # ~73 cases, ~3.5min

# Docker deployment
docker-compose up -d
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
                         │   SQLite/MySQL  │
                         └─────────────────┘
                                  │
                         ┌────────▼────────┐
                         │   shared/       │
                         │   Vue 共享层    │
                         └─────────────────┘
```

### Backend (`backend/`)

- **Framework**: FastAPI with async SQLAlchemy (aiosqlite for dev, aiomysql for prod)
- **Auth**: JWT tokens + bcrypt password hashing + CAPTCHA + account locking
- **Config**: `app/config.py` — Pydantic Settings, reads `.env`, cached via `@lru_cache`
- **Database**: `app/database.py` — `get_db()` dependency yields a session, auto-commits on success
- **API routes**: `app/api/` — `auth.py`, `itsm.py`, `chat.py`, `admin.py`, `ops.py`, `upload.py`, `templates.py`, `captcha.py`
- **Services**: `app/services/` — `ticket_service.py` (core ticket logic), `sla_service.py` (SLA timer checks)
- **Models**: `app/models/` — `user.py`, `ticket.py`, `category.py`, `permission.py`, `chat.py`, `template.py`, `audit_log.py`
- **Cache**: `app/utils/redis.py` — Redis cache with automatic fallback to in-memory when Redis unavailable
- **WebSocket**: Two separate WS systems — global notification WS in `utils/websocket.py`, chat-specific WS in `api/chat.py`
- **Background tasks**: `app/tasks/sla_checker.py` — APScheduler runs every minute to update SLA status colors

### Frontend Shared Layer (`shared/`)

Four frontends share common code via `@shared/` alias (configured in each `vite.config.js`):

| Module | Purpose |
|--------|---------|
| `shared/utils/status.js` | `statusType`, `statusText`, `priorityType`, `slaColor`, `slaText`, `slaTagType` |
| `shared/utils/format.js` | `formatTime`, `formatShortTime`, `formatMsgTime` |
| `shared/api/request.js` | `createApiClient()` — axios instance with token injection + 401/403/error handling |
| `shared/stores/user.js` | `createBaseStore(authApi)` — base Pinia store for login/logout/fetchMe |
| `shared/composables/useWebSocket.js` | WS connection + heartbeat + exponential backoff reconnect |
| `shared/components/BaseLogin.vue` | Configurable login component (props: title/color/showRegister/showForgotPassword) |
| `shared/components/ChatMessage.vue` | Chat message renderer (system/text/image/file, mine/other bubbles) |
| `shared/components/ChatInput.vue` | Chat input area with file upload |

Each frontend extends the base store with its own computed properties (admin adds WS connection, agent adds hasItsm, etc.).

### Agent Architecture (`.claude/agents/`)

| Agent | Model | Role |
|-------|-------|------|
| `coder` | Opus | Orchestrator: analyze → delegate to front/backend → review code → run tests → git commit |
| `front` | Sonnet | Frontend specialist: Vue/JS code in `frontend*/src/` and `shared/` |
| `backend` | Sonnet | Backend specialist: Python code in `backend/` |
| `initializer` | Sonnet | CHANGELOG.md, FEATURES.md, git operations |
| `pm` | Opus | Product analysis, PRD, competitive analysis |

**Workflow**: User request → `coder` analyzes and delegates → `front`/`backend` implement → `coder` reviews + tests + commits → `initializer` updates logs.

## Ticket Lifecycle

```
pending → accepted → processing → resolved_pending_review → resolved
  (池)     (接单)     (处理中)        (待评价)              (已解决)
```

- `pending`: Created by user, visible in agent's shared pool
- `accepted`: Agent manually accepts → auto-creates ChatRoom
- `processing`: Agent working on it
- `resolved_pending_review`: Agent marks resolved → user sees rating prompt
- `resolved`: User rates → chat room auto-closes

**状态流转验证**: `VALID_TRANSITIONS` dict in `ticket_service.py` enforces legal transitions only.

SLA color coding: green (normal) → yellow (30%+) → red (50%+) → black (overdue)

## Authentication System

### Login
- `POST /api/auth/login` — `{account, password}` (account = login_id or phone)
- Account lockout: 5 failed attempts → locked 15 minutes (423 response)
- CAPTCHA required after 3 failed attempts
- Unified error: "账号或密码错误" (prevents account enumeration)

### Registration
- `POST /api/auth/register` — `{name, phone, password}` + CAPTCHA
- Auto-creates user with ACTIVE status + auto-generates login_id (U00001 format)
- Returns token immediately (register = login)

### Forgot Password
- `POST /api/auth/reset-password` — `{name, phone, captcha_id, captcha_text, new_password}`
- Validates: CAPTCHA → name+phone match → new password ≠ old password
- Reserved `sms_code` field for future SMS integration

### Permission Model
- Three flags: `itsm_access`, `ops_access`, `admin_access`
- `admin_access` can only be modified by `super_admin` (others get 403)
- `require_permission("field")` dependency in `app/utils/auth.py` with 60s Redis/memory cache
- Admins and super_admins auto-grant all permissions

### Key Credentials
| Role | login_id | phone | password |
|------|----------|-------|----------|
| Super Admin | `admin` | `10000000000` | `admin123` |
| Agent (张三) | `U00001` | `13900000001` | `123456` |
| User (刘一) | `U00006` | `13900010001` | `123456` |

## Key Patterns

**`_ticket_to_dict` safety**: When converting Ticket ORM objects to dicts, always use the `safe_rel_name()` helper that checks `ticket.__dict__` before accessing relationships — accessing unloaded relationships in async SQLAlchemy raises `MissingGreenlet`.

**Route order**: Static routes (e.g. `/tickets/sla-warnings`) must be defined before dynamic routes (e.g. `/tickets/{ticket_id}`) or FastAPI will match the wrong endpoint.

**UNIQUE constraint on chat_rooms.ticket_id**: Always check for existing room before creating — see `ticket_service.py accept_ticket()`.

**Redis fallback**: All Redis operations (`redis.py`) wrap in try/except and fall back to in-memory storage when Redis is unavailable. The system works identically with or without Redis.

**CAPTCHA test mode**: Requests with `X-Test-Mode: true` header (localhost only) skip CAPTCHA verification in tests.

## Common Issues

**Port 8000 in use**: Multiple Python processes accumulate. Use `stop.bat` or manually `taskkill /F /PID <pid>`.

**Backend 500 errors**: Usually caused by accessing unloaded SQLAlchemy relationships in async context. Use `__dict__` checks.

**SQLite timezone issues**: SQLite returns timezone-naive datetimes. Use the `_ensure_utc()` helper in `sla_service.py`.

**SLA pause/resume**: If you see "can't subtract offset-naive and offset-aware datetimes", ensure `_ensure_utc()` is being used.

**alembic.ini encoding**: On Windows, `alembic.ini` must be GBK encoded (not UTF-8) or alembic will fail with `UnicodeDecodeError`.

**bcrypt warning**: `passlib 1.7.4` + `bcrypt 4.x` shows `AttributeError: module 'bcrypt' has no attribute '__about__'` — this is a known compatibility warning, functionality works correctly.

**Test pass rate: 73/73 (100%)**. All tests must pass before committing.

## Environment Variables

Copy `backend/.env.example` to `backend/.env`. Key vars:
- `DB_TYPE`: `sqlite` (default) or `mysql`
- `JWT_SECRET_KEY`: Change in production
- `REDIS_URL`: Redis connection (empty = use in-memory fallback)
- `FEISHU_APP_ID/SECRET`: For feishu integration (currently removed from active code)
