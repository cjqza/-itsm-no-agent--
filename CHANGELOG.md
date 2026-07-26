# 变更日志（CHANGELOG）

> 本文件由 initializer（记录管家 agent）维护，记录项目的开发进展与变更。最新条目在最上方。

## [2026-07-26] AI 智能客服 RAG 系统：后端 RAG 管道 + 前端 AI 聊天 UI
- **变更**：新增完整的 AI 智能客服系统，分两个提交交付。(1) 后端新建 `backend/app/ai/` 模块，包含 7 个文件：`embeddings.py`（Embedding 抽象层，支持 BGE 本地模型 + OpenAI API）、`vectorstore.py`（ChromaDB 向量存储管理）、`llm.py`（LLM 抽象层，支持 GGUF 本地模型 + DeepSeek API）、`rag.py`（RAG 管道：检索 → 构建消息 → 生成，全局单例惰性初始化）、`knowledge.py`（知识库构建器，已解决工单 + FAQ 文档同步）、`prompts.py`（提示词模板：系统角色、RAG 上下文、兜底提示）、`models.py`（Pydantic Schema）。(2) 新增 3 个 API 端点：`POST /api/ai/chat`（AI 聊天，支持 SSE 流式输出）、`POST /api/ai/knowledge/sync`（知识库同步，需 admin_access）、`GET /api/ai/knowledge/status`（知识库状态，需 admin_access）。(3) `config.py` 新增 17 项 AI/RAG 配置（LLM_PROVIDER、EMBEDDING_PROVIDER、CHROMA 路径、RERANKER 等）。(4) `main.py` 注册 ai_chat 路由 + AI 专用限流分组（20 次/分钟/IP）。(5) `requirements.txt` 新增 chromadb、sentence-transformers 依赖。(6) 前端 `frontend-client/src/api/index.js` 新增 aiApi（chat/chatStream/knowledgeStatus）。(7) `Home.vue` 接入 AI 聊天：SSE 流式输出、来源引用卡片、转人工按钮，保留原有 getBotReply() 作为 fallback。设计要点：所有重型依赖惰性导入，不安装 AI 包不影响现有功能；同步/异步边界用 `asyncio.to_thread()` 桥接；RAG pipeline 初始化失败返回 None，API 返回 503。共 14 个文件变更，+1588 / -19。
- **原因**：用户提交工单前需要快速获得常见问题解答，人工客服响应有延迟；引入 RAG 检索增强生成系统，基于已解决工单和 FAQ 文档知识库，为用户提供即时 AI 问答，减轻人工客服压力，提升首次响应速度。
- **影响**：`backend/app/ai/__init__.py`、`backend/app/ai/embeddings.py`、`backend/app/ai/vectorstore.py`、`backend/app/ai/llm.py`、`backend/app/ai/rag.py`、`backend/app/ai/knowledge.py`、`backend/app/ai/prompts.py`、`backend/app/ai/models.py`（新建 AI 模块）；`backend/app/api/ai_chat.py`（新建 AI 聊天端点）；`backend/app/config.py`（新增 17 项 AI 配置）；`backend/app/main.py`（注册路由 + AI 限流）；`backend/requirements.txt`（新增 chromadb、sentence-transformers）；`frontend-client/src/api/index.js`（新增 aiApi）；`frontend-client/src/views/Home.vue`（AI 聊天 UI + SSE 流式 + 来源引用 + 转人工）。后端新增 3 个 API 端点（总端点数 72→75），前端用户服务台首页改造。73/73 测试全过，无回归。
- **提交**：`ba1888a`（后端 RAG 模块）、`537225a`（前端 AI 聊天 UI）
- **测试**：73/73 全部通过。

## [2026-07-26] 代码优化 13 项 — 代码卫生与架构改进
- **变更**：13 项集中代码优化，11 个文件变更，+48 / -80。(1) `websocket.py` 将 `print` 改为 `logger.debug`，统一日志输出。(2) `admin.py` 删除重复的 `datetime` import。(3) `auth.py` 的 `_ip_fail_store` 在清理时删除空 key，避免内存泄漏。(4) `itsm.py` 的 `get_ticket` 错误信息脱敏，不暴露内部 ID 格式。(5) `ticket_service.py` 的 `safe_rel_name` 添加 debug 日志，便于排查关系加载异常。(6) `admin.py` 的 `list_permissions` keyword 条件去重，避免重复 SQL 条件。(7) `itsm.py` 6 处函数内 lazy import 移至文件顶部，规范导入顺序。(8) `ops.py` 移除冗余字段覆盖逻辑。(9) `chat.py` 的 `ChatMessageRead` 模型添加复合索引，提升已读状态查询性能。(10) `config.py` + `sla_service.py` 将 SLA 阈值从硬编码改为配置项，支持通过环境变量调整。(11) `admin.py` 提取 `_get_user_or_404` 辅助函数，消除 3 处重复的用户查询+404 处理。(12) `AgentChat.vue` 用 shared `formatTime` 替换本地时间格式化函数，消除重复代码。(13) `user.py` + `admin.py` 的 `is_online` 字段从 Integer 改为 Boolean，语义更清晰。
- **原因**：项目积累了多处代码卫生问题——调试 print 残留、重复 import、空 key 内存泄漏、错误信息泄露内部细节、硬编码阈值、冗余字段覆盖、类型语义不准确等，集中修复可提升代码质量与可维护性。
- **影响**：`backend/app/utils/websocket.py`（日志规范化）；`backend/app/api/admin.py`（去重 import + keyword 去重 + _get_user_or_404 提取 + is_online Boolean）；`backend/app/api/auth.py`（空 key 清理）；`backend/app/api/itsm.py`（错误脱敏 + lazy import 顶部化）；`backend/app/api/ops.py`（移除冗余覆盖）；`backend/app/config.py`（SLA 阈值配置项）；`backend/app/models/chat.py`（复合索引）；`backend/app/models/user.py`（is_online Boolean）；`backend/app/services/sla_service.py`（SLA 阈值配置化）；`backend/app/services/ticket_service.py`（debug 日志）；`frontend-agent/src/views/AgentChat.vue`（复用 shared formatTime）。纯重构，无新增功能，73/73 测试全过。
- **提交**：`9e59058`
- **测试**：73/73 全部通过。

## [2026-07-26] 代码优化 TOP6-10 — 重复代码消除 + 配置外部化 + Docker增强 + 共享工具函数
- **变更**：(1) `chat.py` 提取 `_batch_unread_counts()` 辅助函数，`get_my_rooms` 和 `get_unread_summary` 两处相同的未读消息批量计算逻辑统一调用，消除约 60 行重复查询代码。(2) `config.py` 新增 `CORS_ORIGINS` 配置项，`main.py` 中硬编码的 8 个 CORS origin 改为从配置读取并自动补充 `127.0.0.1` 变体，新增前端域名无需改代码。(3) `docker-compose.yml` 新增 SQLite 数据文件卷挂载（`it_ops.db`）、backend 健康检查（`/api/auth/captcha`，30s 间隔）、所有前端服务添加 `restart: unless-stopped`。(4) `Dashboard.vue` 和 `TicketDetail.vue` 中各有一份相同的 `utcDate()` 函数，统一迁移到 `shared/utils/format.js` 新增的 `utcToDate()` 导出函数，两处组件改为 import 引用。(5) `shared/utils/format.js` 新增 `utcToDate(t)` 工具函数，将无时区后缀的 ISO 字符串视为 UTC 并转为 Date 对象。7 个文件变更，+92 / -95。
- **原因**：`chat.py` 中未读消息数计算逻辑在两个端点完全重复，修改时需同步两处容易遗漏；CORS 域名硬编码在 `main.py` 中，部署新环境需改代码；Docker 缺少数据持久化和健康检查，容器崩溃无自动恢复；`utcDate()` 函数在 Dashboard 和 TicketDetail 中各有一份相同实现。
- **影响**：`backend/app/api/chat.py`（提取 `_batch_unread_counts`）；`backend/app/config.py`（新增 `CORS_ORIGINS`）；`backend/app/main.py`（CORS 从配置读取）；`docker-compose.yml`（卷挂载 + 健康检查 + restart 策略）；`frontend-agent/src/views/Dashboard.vue`（改用 `utcToDate`）；`frontend-agent/src/views/TicketDetail.vue`（同上）；`shared/utils/format.js`（新增 `utcToDate`）。纯重构，无新增功能。
- **提交**：`3ea1812`（docs）；业务代码待 coder 提交。
- **测试**：待确认。

## [2026-07-26] 代码优化 TOP5 — BUG修复与重复代码消除
- **变更**：(1) 修复 `chat.py` websocket_chat 中 `ws_user` 变量未定义的 BUG，增加防御性初始化。(2) `ops.py` 提取 `_since_date()` 辅助函数，消除 7 处重复的时间计算逻辑。(3) `ops.py` list_tickets 查询条件提取为公共 `conditions` 列表，data 和 count 查询共享同一份条件，消除重复筛选代码。(4) `chat.py` 将 `datetime` 导入移至文件顶部，删除 2 处函数内联导入。(5) `shared/utils/status.js` 新增 `slaColorByPercent()` 函数，`Dashboard.vue` 和 `TicketDetail.vue` 统一引用，消除两处相同的 SLA 颜色计算函数。5 个文件变更，+51 / -60。
- **原因**：代码存在一处潜在 BUG（ws_user 未定义可能导致 NameError）和大量重复逻辑，影响可维护性和健壮性；提取公共函数可减少修改时的遗漏风险。
- **影响**：`backend/app/api/chat.py`（BUG 修复 + 导入整理）；`backend/app/api/ops.py`（提取辅助函数 + 查询条件重构）；`frontend-agent/src/views/Dashboard.vue`（引用共享 SLA 颜色函数）；`frontend-agent/src/views/TicketDetail.vue`（同上）；`shared/utils/status.js`（新增 slaColorByPercent）。纯重构，无新增功能。
- **提交**：`870d1cb`
- **测试**：73/73 全部通过。

## [2026-07-26] ITSM 工单实时更新修复：创建工单后自动通知客服端刷新
- **变更**：(1) 后端 `main.py` 新增全局通知 WebSocket 端点 `/ws`（JWT 认证 + 心跳 + 连接数限制），限流中间件跳过 `/ws` 路径。(2) 后端 `itsm.py` 的 `create_ticket` 成功后广播 `new_ticket` 事件给所有已连接的客服。(3) 前端 `frontend-agent/src/store/user.js` 新增全局 WS 连接管理（`onWsMessage` 回调机制）。(4) `Dashboard.vue` 监听 `new_ticket`/`ticket_update` 事件自动刷新看板数据。(5) `TicketList.vue` 同样监听并自动刷新工单列表。5 个文件变更，+111 / -3。
- **原因**：工单创建后客服端需要手动刷新才能看到新工单，实时性差；新增全局 WebSocket 通知机制，客服端无需轮询即可实时感知新工单和状态变更。
- **影响**：`backend/app/main.py`（新增 /ws 端点 + 限流跳过）；`backend/app/api/itsm.py`（create_ticket 后广播通知）；`frontend-agent/src/store/user.js`（WS 连接管理）；`frontend-agent/src/views/Dashboard.vue`（自动刷新）；`frontend-agent/src/views/TicketList.vue`（自动刷新）。后端新增 1 个全局 WS 端点，前端 ITSM 客服端体验增强。
- **提交**：`ee33ad3`
- **测试**：73/73 全部通过。

## [2026-07-25] OPS 统计系统增强：新增图表接口、全部时间筛选、权限修复
- **变更**：(1) 后端新增 4 个 OPS 专用接口：`/ops/tickets`（工单列表）、`/ops/status-distribution`（状态分布）、`/ops/category-stats`（管理单元统计含平均处理时长）、`/ops/rating-distribution`（评分分布）。(2) 所有 OPS 统计接口的 `days` 参数从必填（默认 30 天）改为可选（None = 全部历史数据）。(3) 前端 Overview.vue 增加「全部」时间筛选选项，改用新专用接口渲染状态分布饼图、管理单元柱状图（含平均处理时长 tooltip）、评分分布柱状图。(4) TicketHistory.vue 权限修复：`loadCategories` 改用公开的 `/itsm/categories` 接口，`loadTickets` 改用 OPS 专用工单列表接口。(5) `frontend-ops/src/api/index.js` 新增 4 个 API 方法。4 个文件变更，+203 / -38。
- **原因**：OPS 统计缺乏专用图表接口，前端依赖通用接口拼装数据效率低；`days` 硬编码 30 天无法查看全部历史数据；TicketHistory 的分类加载和工单列表使用了需要 itsm_access 权限的接口，OPS 用户无法正常访问。
- **影响**：`backend/app/api/ops.py`（新增 4 个端点 + days 参数可选化）；`frontend-ops/src/views/Overview.vue`（全部筛选 + 新图表接口）；`frontend-ops/src/views/TicketHistory.vue`（权限修复）；`frontend-ops/src/api/index.js`（新增 API 方法）。OPS 端点总数从 7 个增至 11 个。
- **提交**：`a6e8049`
- **测试**：73/73 全部通过。

## [2026-07-25] 我的工单页面 - 已评价工单弹出详情对话框
- **变更**：MyTickets.vue 改造工单操作按钮与行点击逻辑，按工单状态智能分发。(1) `resolved_pending_review`（待评价）→「去评价」按钮，跳转 `/chat-rooms?ticket_id=xxx`。(2) `resolved`（已评价）→「查看」按钮，弹出详情对话框，展示工单号、创建时间、处理人、四维评分（服务态度/解决方法/解决时间/总体评价）、反馈留言。(3) 其他状态（pending/accepted/processing）→「查看」按钮，跳转聊天室。(4) 行点击也按状态智能分发，体验与按钮一致。(5) 详情数据通过 `ticketApi.get(row.id)` 获取。
- **原因**：已评价工单之前点击仍跳转聊天室，用户无法快速回顾评分与反馈；弹出详情对话框信息更集中、操作更轻量。
- **影响**：`frontend-client/src/views/MyTickets.vue`。纯前端改动，后端无变更。
- **提交**：`2562d19`

## [2026-07-25] 评价界面从 Chat.vue 迁移到 ChatRooms.vue
- **变更**：将用户端评价功能从工单聊天页（Chat.vue）迁移到聊天室页（ChatRooms.vue）。(1) ChatRooms.vue 新增四维评分表单（服务态度/解决方法/解决时间/总体评价），待评价状态下显示评分表单并隐藏聊天输入框，已评价状态下只读展示评价结果，提交评价后自动刷新工单详情和房间列表；新增通过 query 参数 ticket_id 自动选中对应房间的能力。(2) MyTickets.vue 的「去评价」按钮改为跳转 `/chat-rooms?ticket_id=xxx`。(3) Chat.vue 移除全部评价相关代码（模板/脚本/样式共 104 行）。3 个文件变更，+147 / -108。
- **原因**：评价功能原先嵌在 Chat.vue（/chat/:ticketId）中，与聊天室页面（/chat-rooms）功能重叠且入口分散；迁移到 ChatRooms.vue 后用户在统一的聊天室界面即可完成评价，体验更连贯。
- **影响**：`frontend-client/src/views/ChatRooms.vue`（新增评价表单+只读展示+query 自动选中）；`frontend-client/src/views/MyTickets.vue`（跳转路径改为 /chat-rooms）；`frontend-client/src/views/Chat.vue`（移除评价相关代码）。纯前端改动，后端无变更。
- **提交**：`9006087`
- **测试**：73/73 全部通过。

## [2026-07-24] P3 全部完成：组件抽取 + Redis 缓存 + Docker + CI/CD + 暗色主题 + 前端测试
- **变更**：P3 优化全部交付，共 2 个提交、49 个文件变更、净减少 519 行代码（+1632 / -2151），73/73 测试全过。(1) BaseLogin 组件抽取：`shared/components/BaseLogin.vue` 将四端登录页统一为可配置组件，每端 Login.vue 从约 300 行精简至约 65 行。(2) ChatMessage/ChatInput 组件：`shared/components/ChatMessage.vue` + `ChatInput.vue` 统一三个聊天页（AgentChat / Chat / ChatRooms）的消息渲染与输入框。(3) WebSocket composable：`shared/composables/useWebSocket.js` 将三处独立的 WS 连接逻辑统一为 composable，支持自动重连与心跳。(4) store/user.js 统一：`shared/stores/user.js` 提取四端 store 公共基础（token/user/permissions/login/logout/fetchMe），各端仅保留扩展逻辑。(5) Redis 缓存替换：新建 `backend/app/utils/redis.py`（Redis 连接管理器，不可用时自动 fallback 内存）；限流改用 Redis sorted set、Permission 缓存改用 Redis hash（60s TTL）、验证码改用 Redis string + GETDEL，均保留内存 fallback。(6) Docker 化：backend Dockerfile + 4 个前端 Dockerfile + nginx.conf + docker-compose.yml + .dockerignore。(7) CI/CD：`.github/workflows/ci.yml`（backend 测试 + 4 前端构建矩阵）。(8) 前端测试配置：4 个前端添加 Vitest 配置 + test 脚本 + 示例单元测试（status.test.js）。(9) ITSM 暗色主题：`frontend-agent/src/App.vue` 新增暗色模式切换按钮（Sun/Moon 图标），localStorage 持久化偏好。
- **原因**：四端前端存在大量重复的登录页、聊天组件、WebSocket 连接、用户 store 代码，维护成本高且容易不一致；后端限流/权限/验证码缓存全部依赖内存，重启即丢失且无法水平扩展；项目缺少容器化部署与 CI/CD 流水线；前端无单元测试保障；ITSM 客服长时间工作需要暗色主题护眼。
- **影响**：`shared/components/BaseLogin.vue`、`shared/components/ChatMessage.vue`、`shared/components/ChatInput.vue`（新建组件）；`shared/composables/useWebSocket.js`（新建 composable）；`shared/stores/user.js`（新建基础 store）；`shared/index.js`（新增导出）；`backend/app/utils/redis.py`（新建 Redis 管理器）；`backend/app/main.py`（限流改用 Redis）；`backend/app/utils/auth.py`（Permission 缓存改用 Redis）；`backend/app/api/captcha.py`（验证码改用 Redis）；`backend/app/api/auth.py`、`backend/app/api/admin.py`（适配 Redis 缓存清除）；`backend/app/config.py`（新增 REDIS_URL 配置）；`backend/requirements.txt`（新增 redis 依赖）；四端 `Login.vue`（改用 BaseLogin）；`frontend-agent/src/views/AgentChat.vue`（改用 ChatMessage/ChatInput + useWebSocket）；`frontend-client/src/views/Chat.vue`、`ChatRooms.vue`（同上）；四端 `store/user.js`（改用 shared 基础 store）；`frontend-agent/src/App.vue`（暗色主题切换）；`frontend-agent/src/Layout.vue`（暗色主题样式）；`frontend-agent/src/main.js`（暗色主题 CSS 变量）；`.dockerignore`、`backend/Dockerfile`、4 个前端 `Dockerfile` + `nginx.conf`、`docker-compose.yml`（Docker 化）；`.github/workflows/ci.yml`（CI/CD）；4 个前端 `vite.config.js` + `package.json`（Vitest 配置）；`frontend-client/src/utils/__tests__/status.test.js`（示例测试）。前后端均有改动。
- **提交**：`e4cd8cf`（DevOps 基础）、`33b044e`（组件抽取 + Redis + 暗色主题）
- **测试**：73/73 全部通过。

## [2026-07-24] P2 #11 前端公共层抽取：消除 250 行重复代码
- **变更**：新建 `shared/` 目录作为四端前端共享层，包含 4 个共享模块：`shared/utils/status.js`（statusType/statusText/priorityType/slaColor 等 7 个状态工具函数）、`shared/utils/format.js`（formatTime/formatShortTime/formatMsgTime 3 个时间格式化函数）、`shared/api/request.js`（createApiClient 工厂，统一封装 axios 拦截器与错误处理）、`shared/index.js`（统一导出入口）。四端 `vite.config.js` 新增 `@shared` 路径别名；四端 `api/index.js` 从各自重复的 axios 拦截器逻辑（共约 100 行）改为调用 `createApiClient`（各 4 行）；9 个 .vue 组件删除本地重复的状态/格式化函数（约 150 行），改用 shared 导入。共 21 个文件变更（+162 / -182），净减少约 20 行的同时消除 250 行重复代码。
- **原因**：四端前端存在大量重复的 API 拦截器、状态映射、时间格式化代码，维护时需同步修改四处，容易遗漏导致不一致。
- **影响**：`shared/api/request.js`、`shared/utils/status.js`、`shared/utils/format.js`、`shared/index.js`（新建）；四端 `vite.config.js`（@shared alias）；四端 `api/index.js`（改用 createApiClient）；`frontend-agent/src/views/AgentChat.vue`、`Dashboard.vue`、`TicketDetail.vue`、`TicketList.vue`；`frontend-client/src/views/Chat.vue`、`ChatRooms.vue`、`MyTickets.vue`；`frontend-ops/src/views/TicketHistory.vue`；`frontend/src/views/admin/AuditLogs.vue`（删除重复函数改用 shared）。纯前端重构，后端无变更。
- **提交**：`91a3ad9`
- **测试**：73/73 全部通过。

## [2026-07-24] P2 优化：聊天分页、Permission 缓存、审计日志前端页、移动端适配
- **变更**：四项 P2 优化打包交付。(1) 聊天消息分页：`chat.py` 的 `get_messages` 从一次性返回全部消息改为分页返回 `{total, page, page_size, items}`，四端聊天调用方（AgentChat / TicketDetail / Chat / ChatRooms）适配新返回格式。(2) Permission 内存缓存：`auth.py` 的 `require_permission` 增加 60 秒 TTL 内存缓存，避免每次请求都查库；`admin.py` 权限变更时自动清除对应用户缓存，保证一致性。(3) 审计日志前端页面：新建 `AuditLogs.vue`（筛选条件 + 分页表格 + 操作类型/目标类型标签展示），admin 前端 Layout 新增「操作日志」菜单项，路由同步注册。(4) 移动端适配：5 个关键页面通过 `@media` 断点（768px/480px）实现响应式——Login.vue 卡片宽度自适应、Dashboard.vue 四象限小屏单列、Layout.vue 侧边栏折叠+汉堡按钮+遮罩层、Overview.vue 统计卡片小屏 2 列/1 列。
- **原因**：聊天消息无分页导致长对话加载缓慢；权限校验每次查库增加数据库压力；审计日志虽有后端接口但缺少前端管理页面；移动端访问布局错乱无法正常使用。
- **影响**：`backend/app/api/chat.py`（消息分页返回）；`backend/app/utils/auth.py`（60s 权限缓存）；`backend/app/api/admin.py`（权限变更清缓存）；`frontend/src/views/admin/AuditLogs.vue`（新建审计日志页）；`frontend/src/views/admin/Layout.vue`（新增菜单项 + 移动端适配）；`frontend/src/router/index.js`（审计日志路由）；`frontend/src/api/index.js`（审计日志 API）；`frontend-agent/src/views/AgentChat.vue`（适配分页格式）；`frontend-agent/src/views/Dashboard.vue`（移动端适配）；`frontend-agent/src/views/Layout.vue`（移动端适配）；`frontend-agent/src/views/TicketDetail.vue`（适配分页格式）；`frontend-client/src/views/Chat.vue`（适配分页格式）；`frontend-client/src/views/ChatRooms.vue`（适配分页格式）；`frontend-client/src/views/Login.vue`（移动端适配）；`frontend-ops/src/views/Overview.vue`（移动端适配）。前后端均有改动，共 15 个文件。
- **提交**：`62ed2e2`
- **测试**：73/73 全部通过。

## [2026-07-23] P2 优化：错误边界、骨架屏、管理员审计、忘记密码修复、前端全面美化、Agent 架构重构
- **变更**：大量改动打包交付。(1) 全局错误边界：四端 main.js 注册 `app.config.errorHandler` 捕获未处理异常并 `console.error`。(2) 骨架屏：TicketList / Dashboard / MyTickets / Overview 四个列表页加载态从 spinner 改为 `el-skeleton`。(3) 管理员操作审计：新增 `AuditLog` 模型（audit_logs 表），admin.py 中 7 个关键操作（创建管理员、创建/更新/删除客服、审批权限、审批账号、修改权限）自动记录审计日志；新增 `GET /api/admin/audit-logs` 分页查询接口（支持 operator_id / action / date range 筛选）。(4) 忘记密码：新增 `POST /api/auth/reset-password`（account + name + new_password），四端 Login.vue 均增加忘记密码对话框；错误提示细分（验证码错误 400 / 账号姓名不匹配 400 / 新旧密码相同 400 / 账号锁定 423）。(5) 前端界面优化：22 个 Vue 文件全面美化（登录页渐变背景+居中卡片、Layout 侧边栏配色、表格/卡片圆角阴影、色彩间距统一）。(6) Agent 架构重构：新建 `front.md`（前端专家）、`backend.md`（后端专家）、`pm.md`（产品经理）三个 agent 定义；`coder.md` 改为调度中枢（不写代码，负责分派+审查+测试+提交）。(7) 后台管理增强：admin.py 新增 `POST /api/admin/admins`（super_admin 创建管理员）、`POST /api/admin/agents`（创建客服）、`PUT /api/admin/agents/{user_id}`（更新客服）、`DELETE /api/admin/agents/{user_id}`（删除客服）共 4 个新端点；用户列表搜索增强（支持 name / phone / login_id / feishu_user_id 四字段关键字搜索）；权限页改造为「账号管理」+ 客服 CRUD 入口。(8) 四端 api/index.js 新增 `resetPassword` 方法。
- **原因**：P2 优化清单中的高价值项集中交付：前端缺少全局错误兜底；列表页加载态体验差；管理员关键操作无审计追溯；用户忘记密码无自助重置途径；前端视觉风格不统一；Agent 定义职责混乱；后台管理缺少客服 CRUD 和管理员创建能力。
- **影响**：四端 `main.js`（错误边界）；`frontend-agent/src/views/TicketList.vue`、`frontend-agent/src/views/Dashboard.vue`、`frontend-client/src/views/MyTickets.vue`、`frontend-ops/src/views/Overview.vue`（骨架屏）；`backend/app/models/audit_log.py`（新建）、`backend/app/models/__init__.py`（导入）、`backend/app/api/admin.py`（审计记录 + admin/agents CRUD + 搜索增强）；`backend/app/api/auth.py`（reset-password 端点）；四端 `Login.vue`（忘记密码对话框 + 错误提示）；四端 `api/index.js`（resetPassword）；四端 22 个 Vue 文件（界面美化）；`.claude/agents/front.md`、`.claude/agents/backend.md`、`.claude/agents/pm.md`（新建）、`.claude/agents/coder.md`（重构）。前后端均有大量改动。
- **提交**：`df718f8`
- **测试**：73/73 全部通过。

## [2026-07-23] P2 优化三项：Home.vue 空 catch 修复、WebSocket 并行广播、模板持久化
- **变更**：三项 P2 优化。(1) Home.vue 文件发送失败的空 catch 块补 `ElMessage.error` 提示（P2 #12）。(2) `websocket.py` 全局广播和 `chat.py` 房间广播从顺序 `await` 改为 `asyncio.gather` 并行发送，减少多连接场景下的广播延迟（P2 #19）。(3) 快捷回复模板从内存 dict 存储改为数据库持久化：新增 `Template` 模型（templates 表，含 id/title/content/category/is_active/created_at/updated_at），`templates.py` 全部改用 DB CRUD，`seed_data.py` 增加 5 条模板种子数据，`alembic/env.py` 导入新模型（P2 #13）。
- **原因**：Home.vue 空 catch 静默吞异常用户无感知；WebSocket 广播顺序 await 在连接数多时累积延迟；模板内存存储重启即丢失，无法跨会话复用。
- **影响**：`frontend-client/src/views/Home.vue`（空 catch 修复）；`backend/app/utils/websocket.py`（并行广播）；`backend/app/api/chat.py`（并行广播）；`backend/app/api/templates.py`（DB CRUD 重写）；`backend/app/models/template.py`（新建）；`backend/app/models/__init__.py`（导入）；`backend/seed_data.py`（模板种子）；`backend/alembic/env.py`（模型导入）。前后端均有改动。
- **提交**：`c41ee60`
- **测试**：73/73 全部通过。

## [2026-07-23] 登录安全加固：验证码、账号锁定、注册即登录、限流收紧
- **变更**：六项后端安全加固。(1) User 模型扩展：新增 `login_fail_count`（密码错误计数）、`locked_until`（锁定截止时间）字段，新增 alembic 迁移 `b3c4d5e6f7a8`。(2) 验证码模块：新建 `captcha.py`，使用 Pillow 生成 4 位图形验证码（随机噪点+干扰线），内存存储 TTL 5 分钟；新增 `GET /api/auth/captcha` 获取验证码图片+key、`POST /api/auth/captcha/verify` 验证。(3) 注册改为即注册即登录：新用户注册后 status 直接为 ACTIVE（去掉 PENDING 审批），自动分配 login_id，登录后直接返回 token。(4) 登录安全加固：密码错误 5 次锁定 15 分钟（返回 423 + lock_remaining_seconds）；密码错误 3 次后需输入验证码（返回 400 + captcha_required=true）。(5) 限流收紧：登录从 10 次/分 改为 5 次/分，新增注册 3 次/小时、验证码获取 10 次/分。(6) 测试扩展至 73 个用例（新增账号锁定、验证码触发、注册即登录等），73/73 全部通过。
- **原因**：原登录无防暴力破解机制（无锁定、无验证码）；注册流程需要管理员审批过于繁琐，内部系统可简化为即注册即登录；原限流阈值偏宽松。
- **影响**：`backend/app/models/user.py`（login_fail_count/locked_until 字段）；`backend/app/api/auth.py`（登录锁定逻辑 + 注册即登录 + 错误提示细分）；`backend/app/api/captcha.py`（新建验证码模块）；`backend/app/main.py`（限流阈值调整 + 验证码限流）；`backend/app/utils/auth.py`（锁定状态检查）；`backend/alembic/versions/b3c4d5e6f7a8_add_login_security_fields.py`（迁移文件）；`backend/requirements.txt`（新增 Pillow 依赖）；`backend/tests/test_api.py`（测试扩展）。纯后端改动，前端无需适配。
- **提交**：`87a6bb8`
- **测试**：73/73 全部通过。

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
