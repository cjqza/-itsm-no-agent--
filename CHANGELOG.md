# 变更日志（CHANGELOG）

> 本文件由 initializer（记录管家 agent）维护，记录项目的开发进展与变更。最新条目在最上方。

## [2026-07-23] 集中代码优化：数据库索引、N+1 查询修复、Dashboard 合并、上传安全、前端代码质量（7 项）
- **变更**：七项集中优化打包交付。(1) 数据库索引：Ticket 的 status/created_at/assignee_id/creator_id/category_id 加 index=True，TicketLog 加 ticket_id 索引，ChatMessage 加 room_id 索引，ChatMessageRead 加 message_id/user_id 索引，共 9 个索引通过 alembic 迁移 `f7a8b9c0d1e2` 创建。(2) N+1 查询修复：`get_my_rooms` 从 1+3N 次查询优化为 4 次批量查询（rooms→last_messages→unread_counts→tickets 一次取回）。(3) Dashboard 查询合并：`/api/itsm/dashboard` 从 5 次独立 SELECT 合并为 1 条 CASE SQL，减少数据库往返。(4) 上传安全：移除 text/html、text/javascript、text/css 三种危险 MIME 类型白名单。(5) 前端空 catch 补错误提示：TicketDetail.vue 6 处、Dashboard.vue 2 处、Layout.vue/Categories.vue/Permissions.vue 各 1 处，共 11 处空 catch 块补 ElMessage.error。(6) 死代码清理：Home.vue 删除未使用 openInNewTab 函数及 onMounted import，AgentChat.vue 移除未使用 watch import，NoPermission.vue 移除未使用 `import api from '@/api'`。(7) frontend-ops main.js 补 zhCn locale 导入对齐其他三端。
- **原因**：高频查询字段缺少索引导致大数据量下查询变慢；get_my_rooms 存在经典 N+1 问题；dashboard 多次独立查询可合并减少开销；上传白名单含 HTML/JS/CSS 存在 XSS 风险；前端空 catch 静默吞异常不利于排查；存在未使用的导入和函数属于死代码。
- **影响**：`backend/app/models/ticket.py`（Ticket/TicketLog 索引）；`backend/app/models/chat.py`（ChatMessage/ChatMessageRead 索引）；`backend/alembic/versions/f7a8b9c0d1e2_add_performance_indexes.py`（迁移文件）；`backend/app/api/chat.py`（get_my_rooms 批量查询重写）；`backend/app/api/itsm.py`（dashboard CASE SQL 合并）；`backend/app/api/upload.py`（移除危险 MIME）；`frontend-agent/src/views/TicketDetail.vue`（6 处空 catch）；`frontend-agent/src/views/Dashboard.vue`（2 处空 catch）；`frontend-agent/src/views/Layout.vue`（1 处空 catch）；`frontend/src/views/admin/Categories.vue`（1 处空 catch）；`frontend/src/views/admin/Permissions.vue`（1 处空 catch）；`frontend-client/src/views/Home.vue`（删除死代码）；`frontend-agent/src/views/AgentChat.vue`（删除死代码）；`frontend/src/views/auth/NoPermission.vue`（删除死代码）；`frontend-ops/src/main.js`（补 zhCn locale）。前后端均有改动，涉及数据库索引迁移。
- **提交**：`58ba73f`
- **测试**：`cd backend && python tests/test_api.py` 67/67 全部通过，无回归。

## [2026-07-23] P1 安全余项：全局异常日志、删除 DEBUG print、401 清理一致性、输入校验（v2 优化 #6/#7/#9/#10）
- **变更**：(1) #6 全局异常与日志：`main.py` 500 响应体改为通用文案不再泄露内部错误信息，日志增加 `RotatingFileHandler` 落盘 `backend/logs/app.log`（10MB 轮转 5 份），`print` 改用 `logger.error`。(2) #7 删除 DEBUG print：确认 `auth.py` 中已无遗留 `print`，无需改动。(3) #9 401 清理一致性：四端前端 `api/index.js` 的 401 拦截器统一清理 `token`、`user`、`permissions`（admin 前端原先只清 token 和 user，现已补齐 permissions）。(4) #10 输入校验：`chat.py` MessageType 转换增加 try/except 防御非法 `msg_type` 返回 400；`templates.py` TemplateCreate/Update 的 `title` 和 `content` 增加 `max_length` 约束；`schemas/ticket.py` TicketRate.rating 增加 `ge=1/le=5`、TicketCreate.title 增加 `max_length=200`、description 增加 `max_length=5000`。
- **原因**：v2 优化方案 P0 已完成，P1 安全余项需补齐：生产环境 500 不应泄露内部错误；日志应落盘便于排查；前端 401 清理不一致会导致权限缓存残留；关键输入缺少长度/范围校验存在越界风险。
- **影响**：`backend/app/main.py`（500 通用文案 + RotatingFileHandler + logger.error）；`backend/app/api/chat.py`（MessageType 防御）；`backend/app/api/templates.py`（max_length 校验）；`backend/app/schemas/ticket.py`（rating/title/description 校验）；`frontend-client/src/api/index.js`（401 清理 user+permissions）；`frontend-agent/src/api/index.js`（同上）；`frontend-ops/src/api/index.js`（同上）；`frontend/src/api/index.js`（401 清理 permissions）。前后端均有改动，不涉及数据库。
- **提交**：`d7d73ec`
- **测试**：`cd backend && python tests/test_api.py` 67/67 全部通过，无回归。

## [2026-07-23] 认证改造前端三项：用户注册入口、账号审批页、admin_access 规则提示（任务 C）
- **变更**：前端三项打包交付。(1) C-1 用户端登录页底部增加「申请注册」入口，点击弹出注册对话框（姓名/电话/密码/确认密码，含前后端校验），authApi 新增 register 方法。(2) C-2 admin 前端新建 AccountRequests.vue 页面，展示待审批申请列表，支持批准（批准后显示分配的 login_id）与拒绝操作，adminApi 新增 getAccountRequests/reviewAccountRequest，路由与侧边栏菜单同步注册。(3) C-3 Permissions.vue 中 admin_access 权限开关对非 super_admin 用户禁用并附 tooltip 提示；403 拦截器改为展示后端 detail 错误信息；updatePermission 正确透传 admin_access 参数。
- **原因**：任务 A 完成后端密码认证与账号审批接口，任务 B 完成登录页适配，任务 C 补齐前端交互层：用户注册入口、管理员审批页面、admin_access 权限规则的前端约束与提示。
- **影响**：frontend-client/src/views/Login.vue（注册对话框）、frontend-client/src/api/index.js（register 方法）；frontend/src/views/admin/AccountRequests.vue（新建审批页）、frontend/src/views/admin/Permissions.vue（admin_access 禁用+tooltip）、frontend/src/views/admin/Layout.vue（菜单项）、frontend/src/router/index.js（路由）、frontend/src/api/index.js（403 detail + 审批 API）。纯前端改造，后端无变更。
- **提交**：`d029a22`
- **测试**：后端 `cd backend && python tests/test_api.py` 67/67 全部通过，无回归。

## [2026-07-23] 认证改造：四端前端登录页适配新接口（任务 B）
- **变更**：四个前端 Login.vue（client/agent/ops/admin）统一去掉 el-tabs（飞书ID/用户名双 tab）与 quickLogin 测试账号快捷标签，改为「账号（login_id 或手机号）+ 密码」双输入框，调用 `store.login({ account, password })` 对齐后端 `POST /api/auth/login` 新契约；登录失败显示后端 detail 错误信息。admin 前端 api/index.js 移除 feishu_user_id 特判逻辑，store/user.js 移除字符串转 feishu_user_id 逻辑、fetchMe 补存 login_id/phone。
- **原因**：后端认证体系已从 feishu_user_id 改为 login_id/手机号+密码（任务 A），前端需同步适配新接口契约。
- **影响**：frontend-client/src/views/auth/Login.vue；frontend-agent/src/views/Login.vue；frontend-ops/src/views/Login.vue；frontend/src/views/auth/Login.vue；frontend/src/api/index.js；frontend/src/store/user.js。纯前端改造，后端无变更。
- **提交**：`8e9efd4`
- **测试**：67/67 全部通过，无回归。

## [2026-07-23] 认证改造：密码认证 + 账号申请审批 + admin_access 规则（P1 #4/#5）
- **变更**：认证体系从"无密码登录 + 自动建号"升级为"密码认证 + 账号申请审批"。User 模型新增 login_id（专属ID号 U00001 递增）、password_hash（bcrypt）、PENDING 审批状态，phone 改为 unique index 作为登录键。登录接口改为 account（login_id 或 phone）+ password，移除自动建号逻辑。新增 POST /api/auth/register（账号申请，创建后 status=PENDING）。新增 GET/PUT /api/admin/account-requests（审批接口，approve 时自动分配 login_id）。admin_access 权限只能由 super_admin 修改（非 super_admin 尝试修改返回 403）。get_current_user 增加 status==ACTIVE 校验（PENDING/禁用用户无法访问）。seed_data 重建：admin/admin123 + agent U00001-U00005/123456 + user U00006-U00007/123456。新增 alembic 迁移（login_id、password_hash 列 + phone 唜一索引）。测试用例从 52 扩展到 67（新增 11 个注册/审批 + 3 个 admin_access 规则 + 1 个登录格式），67/67 全部通过。
- **原因**：原认证体系无密码、自动建号，安全性不足且无法区分审批状态，需升级为企业级认证流程。
- **影响**：backend/app/models/user.py（login_id/password_hash/PENDING 状态/phone 唯一索引）；backend/app/api/auth.py（登录改为 account+password、新增 register 端点）；backend/app/api/admin.py（新增 account-requests 审批端点、admin_access super_admin 限制）；backend/app/utils/auth.py（get_current_user 增加 ACTIVE 校验）；backend/seed_data.py（测试账号重建）；backend/tests/test_api.py（用例扩展至 67 个）；backend/alembic/ + backend/alembic.ini（数据库迁移）。涉及全部认证链路，前端登录页面需适配新接口格式。
- **提交**：`545b97c`
- **测试**：`cd backend && python tests/test_api.py` 67/67 全部通过。

## [2026-07-23] 修复 admin 全局 WebSocket 心跳定时器泄漏与无限重连（v2 优化 P0 #3）
- **变更**：admin 后台全局 WebSocket 的心跳 `setInterval` 句柄化（`heartbeatTimer`），在 `onclose`、重连前及 `logout` 时统一 `clearInterval`；重连策略改为指数退避 `min(3000*2^n, 30000)` 并设 `MAX_RECONNECT=10` 上限，`reconnectTimer` 句柄可清理，连接成功（`onopen`）时重置重连计数；新增 `manualClose` 标志，主动登出后 `onclose` 不再触发重连。同时修复 OPS 概览页导出的空 catch，补齐成功/失败 ElMessage 提示（对齐 TicketHistory.vue）。
- **原因**：原心跳定时器创建后从不清理，重连也无退避、无次数上限，断线重连会不断累积僵尸定时器与连接，长时间运行下资源持续泄漏；Overview.vue 导出的空 catch 会静默吞掉失败异常，用户无从得知导出结果。
- **影响**：frontend/src/store/user.js（admin 全局 WS 心跳/重连/登出逻辑）；frontend-ops/src/views/Overview.vue（导出成功/失败提示）。纯健壮性修复，不涉及功能增减、不改后端。
- **提交**：`ed57015`
- **测试**：`cd backend && python tests/test_api.py` 52/52 全部通过，无后端回归。

## [2026-07-23] 修复 OPS 历史工单导出（v2 优化 P0 #1）
- **变更**：OPS 历史工单导出改为按当前页面筛选条件导出（不再硬编码固定 30 天全量），并补全导出成功/失败的用户提示。
- **原因**：原导出忽略页面上的状态/分类/关键字筛选，导出结果与用户所见列表不一致；且 catch 为空吞掉了失败异常，用户无从得知导出失败原因。
- **影响**：backend/app/api/ops.py（`/api/ops/export` 新增 `status`/`category_id`/`keyword` 查询参数，筛选语义与工单列表一致，关键字模糊匹配 ticket_no/title）；frontend-ops/src/api/index.js（`exportTickets` 改为接收 params 对象，默认 days=30）；frontend-ops/src/views/TicketHistory.vue（`handleExport` 透传页面 filters，成功提示成功、失败以 ElMessage.error 展示原因）。不涉及其他模块。
- **提交**：`49b3eb9`
- **测试**：`cd backend && python tests/test_api.py` 52/52 全部通过（含 OPS Export 用例）。

## [2026-07-23] 初始化 Git 版本控制与记录体系
- **变更**：初始化 Git 仓库；新增 `.gitignore`；建立 `initializer` 记录管家 agent（`.claude/agents/initializer.md`）；创建本变更日志。
- **原因**：项目此前无版本控制，需要一个专职角色持续维护开发日志、Git 提交与功能清单，且不介入业务代码。
- **影响**：项目根目录（新增 `.gitignore`、`CHANGELOG.md`）、`.claude/agents/`（新增 agent 定义）。不涉及任何业务代码。
- **提交**：`5ebb94c`
