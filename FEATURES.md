# 公司桌面IT服务台 — 功能清单

## 一、用户服务台（frontend-client :5173）

### 1.1 智能客服机器人
- [x] 首页输入框描述问题
- [x] 快捷分类卡片（操作系统、邮件、网络、硬件、账号权限、软件安装）
- [x] 关键词智能回复（蓝屏、无法开机、打印机、密码、邮件、网络）
- [x] 转人工关键词触发（转人工、人工服务、报障、报修、创建工单）
- [x] 触发后显示问题分类选择（桌面、网络、软件、其他）
- [x] 选择分类后自动创建工单（带 category_id）
- [x] 创建工单后自动创建聊天室
- [x] 显示工单号，可点击进入聊天室
- [x] 对话消息持久化（localStorage），刷新不丢失
- [x] 重置对话按钮

### 1.2 AI 智能客服
- [x] 首页 AI 聊天入口（与原有机器人并存）
- [x] SSE 流式输出（逐字显示 AI 回复）
- [x] RAG 检索增强生成（基于已解决工单 + FAQ 文档知识库）
- [x] 来源引用卡片（展示 AI 回答的参考来源）
- [x] 转人工按钮（AI 无法解答时无缝切换人工客服）
- [x] 原有关键词机器人作为 fallback（AI 不可用时自动降级）
- [x] Embedding 抽象层（支持 BGE 本地模型 / OpenAI API）
- [x] LLM 抽象层（支持 GGUF 本地模型 / DeepSeek API）
- [x] ChromaDB 向量存储
- [x] 知识库同步（已解决工单 + FAQ 文档自动入库）
- [x] 知识库状态查询
- [x] AI 专用限流（20 次/分钟/IP）
- [x] 重型依赖惰性导入（不安装 AI 包不影响现有功能）
- [x] RAG pipeline 初始化失败优雅降级（API 返回 503）
- [x] AI 思考过程显示（`<think>` 标签解析，可折叠区域，脉冲动画，流式自动展开/完成自动收起）
- [x] SSE 流式事件统一（sources/thinking/token/done/error 五种事件类型）

### 1.3 文件上传与消息
- [x] 发送图片消息（jpg/png/gif/webp/bmp）
- [x] 发送文件消息（pdf/doc/xls/ppt/txt/csv/zip/rar）
- [x] 图片消息内联预览，支持放大查看
- [x] 文件消息显示下载链接
- [x] 待发送文件预览，可取消
- [x] 文件大小限制 10MB

### 1.4 我的工单
- [x] 骨架屏加载态
- [x] 工单列表（分页、状态筛选）
- [x] 已评价工单详情对话框（工单号、创建时间、处理人、四维评分、反馈留言）
- [x] 操作按钮按状态智能分发（待评价→评价页，已评价→详情弹窗，其他→聊天室）
- [x] 行点击按状态智能分发（与按钮逻辑一致）

### 1.5 聊天室（/chat-rooms）
- [x] 左侧聊天室列表（含工单号、标题、最后消息、未读数）
- [x] 右侧聊天区域，支持文本/图片/文件消息
- [x] WebSocket 实时通信
- [x] 自动重连（指数退避 3s→30s）
- [x] 心跳 ping/pong（30s）
- [x] 消息已读标记
- [x] 删除聊天室（同时删除所有历史记录）
- [x] 工单状态标签显示
- [x] 待评价工单显示四维评分表单（服务态度/解决方法/解决时间/总体评价）
- [x] 已评价工单只读展示评价结果
- [x] 通过 query 参数 ticket_id 自动选中对应房间

### 1.6 工单聊天（/chat/:ticketId）
- [x] 实时 WebSocket 聊天
- [x] 历史消息加载
- [x] 图片/文件消息展示
- [x] 待接单工单可取消
- [x] 已接单/处理中工单可催单

### 1.7 登录
- [x] 账号密码登录（login_id 或手机号 + 密码）
- [x] 账号注册即登录（自动分配 login_id，无需审批）
- [x] 图形验证码（密码错误 3 次后触发）
- [x] 账号锁定保护（密码错误 5 次锁定 15 分钟）
- [x] 忘记密码（账号+姓名验证后重置密码）
- [x] 全局错误边界（app.config.errorHandler）

---

## 二、ITSM 客服端（frontend-agent :5174）

### 2.1 工作台（Dashboard）
- [x] 骨架屏加载态
- [x] 四象限看板布局
  - 左上：草稿箱工单（待接单 pending）
  - 右上：待处理工单池（已受理 accepted）
  - 左下：我的待办工单（处理中 processing）
  - 右下：已解决工单（待评价/已评价）
- [x] 每个面板显示工单数量标签
- [x] 待接单工单可直接接单
- [x] SLA 进度条显示
- [x] 待评价/已评价标签切换
- [x] WebSocket 实时通知：新工单/状态变更自动刷新（全局 /ws 端点）

### 2.2 服务请求（TicketList）
- [x] 骨架屏加载态
- [x] 工单列表（分页、搜索）
- [x] 状态筛选（待接单、已接单、处理中、待评价、已解决）
- [x] 点击进入工单详情
- [x] WebSocket 实时通知：新工单/状态变更自动刷新

### 2.3 工单详情（TicketDetail）
- [x] 生命周期进度条（提单→接单→处理→解决→评价）
- [x] 问题描述展示
- [x] SLA 时效进度条（百分比、剩余时间、状态标签）
- [x] 工单分类信息（负责人、管理单元、业务模块、性质、症状、原因、解决方法）
- [x] 操作按钮
  - [x] 接单（pending → accepted）
  - [x] 开始处理（accepted → processing）
  - [x] 解决（processing → resolved_pending_review）
  - [x] 修改标注
  - [x] 暂停/恢复 SLA 计时
- [x] 转派功能
  - [x] 选择目标客服（下拉列表）
  - [x] 转派原因（可选）
  - [x] 转派后自动更新负责人
- [x] 操作历史时间线
- [x] 聊天区域
  - [x] 实时 WebSocket 聊天
  - [x] 历史消息加载
  - [x] 系统消息展示

### 2.4 消息（AgentChat）
- [x] 聊天室列表
- [x] 未读消息数显示
- [x] 实时 WebSocket 聊天
- [x] 消息已读标记

### 2.5 登录
- [x] 账号密码登录（login_id 或手机号 + 密码）
- [x] 图形验证码（密码错误 3 次后触发）
- [x] 账号锁定保护（密码错误 5 次锁定 15 分钟）
- [x] 忘记密码（账号+姓名验证后重置密码）
- [x] 全局错误边界（app.config.errorHandler）

---

## 三、后台管理（frontend :5175）

### 3.1 权限管理
- [x] 用户列表（分页、四字段搜索：name/phone/login_id/feishu_user_id）
- [x] 权限申请审批
- [x] 账号注册申请审批（approve 分配 login_id）
- [x] 启用/禁用用户
- [x] 权限设置（itsm_access、ops_access、admin_access）
- [x] admin_access 仅 super_admin 可修改
- [x] 管理员创建（super_admin 可创建 admin/super_admin 账号）
- [x] 客服管理 CRUD（创建/更新/删除客服账号）
- [x] 审计日志查询（管理员关键操作追溯）
- [x] 审计日志前端页面（筛选+分页+操作类型/目标类型标签）

### 3.2 分类配置
- [x] 管理单元 CRUD
- [x] 业务模块 CRUD
- [x] 性质/症状/原因/解决方法 CRUD
- [x] SLA 时长配置

### 3.3 登录
- [x] 账号密码登录（login_id 或手机号 + 密码）
- [x] 管理员权限校验（路由守卫）
- [x] 账号申请审批界面
- [x] 图形验证码（密码错误 3 次后触发）
- [x] 账号锁定保护（密码错误 5 次锁定 15 分钟）
- [x] 忘记密码（账号+姓名验证后重置密码）
- [x] 全局错误边界（app.config.errorHandler）

---

## 四、OPS 统计系统（frontend-ops :5176）

### 4.1 数据概览（Overview）
- [x] 骨架屏加载态
- [x] 今日工单数、待处理数、处理中数、已解决数
- [x] 工单趋势图表（ECharts）
- [x] 分类分布饼图
- [x] 状态分布饼图（专用接口）
- [x] 管理单元柱状图（含平均处理时长 tooltip）
- [x] 评分分布柱状图
- [x] 时间筛选支持「全部」选项（days 参数可选）
- [x] SLA 达标率

### 4.2 数据分析（Analysis）
- [x] 按时间范围筛选
- [x] 按分类筛选
- [x] 按客服筛选

### 4.3 客服绩效（Performance）
- [x] 客服工单处理量排名
- [x] 平均处理时长
- [x] SLA 达标率

### 4.4 工单历史（TicketHistory）
- [x] 历史工单查询（分页、搜索、筛选）
- [x] 工单详情查看
- [x] 导出功能（按当前筛选条件导出，含成功/失败提示）

### 4.5 登录
- [x] 账号密码登录（login_id 或手机号 + 密码）
- [x] 图形验证码（密码错误 3 次后触发）
- [x] 账号锁定保护（密码错误 5 次锁定 15 分钟）
- [x] 忘记密码（账号+姓名验证后重置密码）
- [x] 全局错误边界（app.config.errorHandler）

---

## 五、后端 API（75 个端点）

### 5.1 认证（auth.py + captcha.py — 5 个）
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/auth/login | 登录（account: login_id/手机号 + password，3 次错误需验证码，5 次锁定 15 分钟） |
| POST | /api/auth/register | 账号注册即登录（自动分配 login_id，返回 token） |
| POST | /api/auth/reset-password | 忘记密码（account + name + new_password 验证后重置） |
| GET | /api/auth/me | 获取当前用户信息 |
| GET | /api/auth/captcha | 获取图形验证码（图片 base64 + captcha_id，内部 verify 函数由登录/注册自动调用） |

### 5.2 工单管理（itsm.py — 18 个）
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/itsm/dashboard | 看板统计数据 |
| GET | /api/itsm/tickets | 工单列表（分页、筛选） |
| POST | /api/itsm/tickets | 创建工单 |
| GET | /api/itsm/tickets/{id} | 工单详情 |
| PUT | /api/itsm/tickets/{id} | 更新工单 |
| PUT | /api/itsm/tickets/{id}/status | 更新工单状态 |
| PUT | /api/itsm/tickets/{id}/accept | 接单 |
| PUT | /api/itsm/tickets/{id}/resolve | 解决 |
| PUT | /api/itsm/tickets/{id}/transfer | 转派（原因可选） |
| PUT | /api/itsm/tickets/{id}/cancel | 取消（仅创建者、仅 pending） |
| PUT | /api/itsm/tickets/{id}/urge | 催单 |
| PUT | /api/itsm/tickets/{id}/remark | 修改标注 |
| PUT | /api/itsm/tickets/{id}/pause-sla | 暂停 SLA |
| PUT | /api/itsm/tickets/{id}/resume-sla | 恢复 SLA |
| GET | /api/itsm/tickets/{id}/logs | 操作日志 |
| GET | /api/itsm/tickets/search | 搜索工单 |
| GET | /api/itsm/tickets/sla-warnings | SLA 预警列表 |
| GET | /api/itsm/categories | 分类列表 |

### 5.3 聊天（chat.py — 10 个）
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/chat/rooms/{ticket_id} | 创建聊天室（已存在则返回） |
| GET | /api/chat/rooms/{ticket_id} | 获取工单聊天室 |
| GET | /api/chat/my-rooms | 我的聊天室列表 |
| DELETE | /api/chat/rooms/{room_id} | 删除聊天室及消息 |
| GET | /api/chat/rooms/{room_id}/messages | 获取聊天记录（分页，返回 {total, page, page_size, items}） |
| POST | /api/chat/rooms/{room_id}/messages | 发送消息 |
| PUT | /api/chat/rooms/{room_id}/close | 关闭聊天室 |
| POST | /api/chat/rooms/{room_id}/read | 标记已读 |
| GET | /api/chat/rooms/{room_id}/unread | 未读数 |
| WS | /api/chat/ws/{room_id} | WebSocket 实时聊天 |

### 5.4 后台管理（admin.py — 22 个）
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/admin/users | 用户列表（四字段搜索） |
| PUT | /api/admin/users/{id} | 更新用户 |
| PUT | /api/admin/users/{id}/status | 启用/禁用 |
| POST | /api/admin/admins | 创建管理员（仅 super_admin） |
| GET | /api/admin/permissions | 权限列表 |
| PUT | /api/admin/permissions/{user_id} | 修改权限 |
| POST | /api/admin/permission-requests | 提交权限申请 |
| GET | /api/admin/permission-requests | 权限申请列表 |
| PUT | /api/admin/permission-requests/{id} | 审批权限申请 |
| GET | /api/admin/account-requests | 账号注册申请列表 |
| PUT | /api/admin/account-requests/{user_id} | 审批账号申请（approve 分配 login_id） |
| GET | /api/admin/audit-logs | 审计日志查询（分页，支持 operator_id/action/date 筛选） |
| GET | /api/admin/agents | 客服列表（itsm_access） |
| POST | /api/admin/agents | 创建客服 |
| PUT | /api/admin/agents/{user_id} | 更新客服 |
| DELETE | /api/admin/agents/{user_id} | 删除客服 |
| CRUD | /api/admin/categories/ | 管理单元 |
| CRUD | /api/admin/business-modules/ | 业务模块 |
| CRUD | /api/admin/properties/ | 性质 |
| CRUD | /api/admin/symptoms/ | 症状 |
| CRUD | /api/admin/causes/ | 原因 |
| CRUD | /api/admin/solutions/ | 解决方法 |

### 5.5 OPS 统计（ops.py — 11 个）
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/ops/statistics/overview | 总览统计（days 可选） |
| GET | /api/ops/statistics/by-category | 按管理单元统计（days 可选） |
| GET | /api/ops/statistics/by-agent | 按客服统计（days 可选） |
| GET | /api/ops/statistics/ratings | 评分统计（days 可选） |
| GET | /api/ops/statistics/sla-compliance | SLA 达标率（days 可选） |
| GET | /api/ops/statistics/trend | 趋势分析（days 可选） |
| GET | /api/ops/tickets | OPS 工单列表（days 可选） |
| GET | /api/ops/status-distribution | 状态分布（days 可选） |
| GET | /api/ops/category-stats | 管理单元统计（含平均处理时长，days 可选） |
| GET | /api/ops/rating-distribution | 评分分布（days 可选） |
| GET | /api/ops/export | 导出报表 |

### 5.6 文件上传（upload.py — 1 个）
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/upload | 上传文件（10MB 限制） |

### 5.7 快捷回复模板（templates.py — 4 个）
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/templates | 模板列表 |
| POST | /api/templates | 创建模板 |
| PUT | /api/templates/{id} | 更新模板 |
| DELETE | /api/templates/{id} | 删除模板 |

### 5.8 全局通知（main.py — 1 个）
| 方法 | 路径 | 说明 |
|------|------|------|
| WS | /ws | 全局通知 WebSocket（JWT 认证，工单创建/状态变更广播） |

### 5.9 AI 智能客服（ai_chat.py — 3 个）
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/ai/chat | AI 聊天（支持 SSE 流式输出，RAG 检索增强生成） |
| POST | /api/ai/knowledge/sync | 知识库同步（已解决工单 + FAQ 文档入库，需 admin_access） |
| GET | /api/ai/knowledge/status | 知识库状态查询（需 admin_access） |

---

## 六、通用功能

### 6.1 认证与权限
- [x] JWT Token 认证
- [x] 账号密码登录（login_id/手机号 + bcrypt 密码）
- [x] 账号注册即登录（自动分配 login_id，返回 token）
- [x] 图形验证码（Pillow 生成，4 位随机字符，内存存储 TTL 5 分钟）
- [x] 账号锁定保护（密码错误 5 次锁定 15 分钟，3 次后需验证码）
- [x] 忘记密码重置（account + name 验证后设置新密码）
- [x] 三级权限体系（itsm_access、ops_access、admin_access）
- [x] admin_access 仅 super_admin 可修改（非 super_admin 返回 403）
- [x] 管理员/超级管理员自动拥有所有权限
- [x] 权限申请 → 管理员审批流程
- [x] 用户状态校验（PENDING/禁用用户无法登录）
- [x] 登录限流（5 次/分钟，注册 3 次/小时，验证码 10 次/分钟）
- [x] 权限校验内存缓存（require_permission 60s TTL，权限变更自动清除）

### 6.2 实时通信
- [x] WebSocket 聊天（per-room）
- [x] WebSocket 工单通知（全局）
- [x] 心跳 ping/pong（30s）
- [x] 断线自动重连（指数退避）
- [x] 消息已读状态追踪

### 6.3 SLA 管理
- [x] 根据分类自动设置 SLA 时长
- [x] SLA 颜色状态（绿→黄→红→黑）
- [x] 暂停/恢复 SLA 计时
- [x] 后台定时检查（每分钟）
- [x] SLA 预警列表

### 6.4 前端共享层（shared/）
- [x] shared/utils/status.js（7 个状态/优先级/SLA 工具函数）
- [x] shared/utils/format.js（3 个时间格式化函数）
- [x] shared/api/request.js（createApiClient 工厂，统一封装 axios 拦截器）
- [x] shared/index.js（统一导出入口）
- [x] 四端 vite.config.js 注册 @shared 路径别名
- [x] 四端 api/index.js 改用 createApiClient（消除 100 行重复拦截器）
- [x] 9 个组件删除本地重复函数改用 shared 导入（消除 150 行重复）
- [x] shared/components/BaseLogin.vue（四端登录页统一组件，300 行→65 行）
- [x] shared/components/ChatMessage.vue（三端聊天页消息渲染统一组件）
- [x] shared/components/ChatInput.vue（三端聊天页输入框统一组件）
- [x] shared/composables/useWebSocket.js（三端 WS 连接统一为 composable，含重连+心跳）
- [x] shared/stores/user.js（四端 store 基础提取：token/user/permissions/login/logout/fetchMe）

### 6.5 AI / RAG
- [x] RAG 检索增强生成管道（检索 → 构建消息 → 生成）
- [x] Embedding 抽象层（BGE 本地模型 / OpenAI API 可切换）
- [x] LLM 抽象层（GGUF 本地模型 / DeepSeek API 可切换）
- [x] ChromaDB 向量存储
- [x] 知识库自动构建（已解决工单 + FAQ 文档同步）
- [x] 提示词模板（系统角色、RAG 上下文、兜底提示）
- [x] SSE 流式输出（Server-Sent Events）
- [x] AI 限流（20 次/分钟/IP，独立分组）
- [x] 重型依赖惰性导入（不安装 AI 包不影响现有功能）
- [x] RAG pipeline 初始化失败优雅降级（返回 503）
- [x] AI 思考过程提取（`_parse_thinking` 解析 `<think>` 标签，`_stream_with_thinking` 流式分离 thinking/answer）
- [x] 所有 LLM 子类统一返回 `{answer, thinking}` 结构
- [x] RAG query/stream_query 返回 thinking 字段
- [x] SSE 五种事件类型：sources / thinking / token / done / error
- [x] generate_next_login_id 性能优化（SELECT MAX 替代全表扫描）

### 6.6 其他
- [x] API 限流（登录 5/min，注册 3/hour，验证码 10/min，其他 120/min，AI 20/min/IP）
- [x] 文件上传（图片/文档/文本/压缩包，10MB，已移除 text/html/js/css 危险类型）
- [x] 快捷回复模板（数据库持久化，支持 CRUD + 分类筛选 + 种子数据）
- [x] 工单操作日志
- [x] 管理员操作审计日志（AuditLog 模型，7 个关键操作自动记录，分页查询接口）
- [x] 全局错误边界（四端 app.config.errorHandler）
- [x] 骨架屏加载态（TicketList / Dashboard / MyTickets / Overview）
- [x] 404 兜底路由
- [x] 全局异常日志落盘（RotatingFileHandler，10MB 轮转 5 份）
- [x] 数据库性能索引（tickets/ticket_logs/chat_messages/chat_message_reads 高频查询字段）
- [x] 聊天室列表批量查询优化（get_my_rooms 从 1+3N → 4 次批量查询）
- [x] Dashboard 统计合并查询（5 次独立 SELECT → 1 条 CASE SQL）
- [x] WebSocket 并行广播（asyncio.gather 替代顺序 await）
- [x] 前端空 catch 块统一补错误提示（12 处）
- [x] Pydantic 输入校验（rating 1-5、title 200 字、description 5000 字、模板 title/content 长度限制）
- [x] 聊天消息分页加载（get_messages 返回 {total, page, page_size, items}）
- [x] 移动端响应式适配（Login/Dashboard/Layout/Overview，@media 768px/480px 断点）
- [x] Redis 缓存替换（限流 sorted set / Permission hash 60s TTL / 验证码 string GETDEL，均 fallback 内存）
- [x] Docker 化（backend Dockerfile + 4 前端 Dockerfile + nginx.conf + docker-compose.yml）
- [x] CI/CD 流水线（.github/workflows/ci.yml，backend 测试 + 4 前端构建矩阵）
- [x] 前端单元测试（4 端 Vitest 配置 + 示例测试 status.test.js）
- [x] ITSM 暗色主题切换（Sun/Moon 按钮 + localStorage 持久化）

---

## 七、测试账号

| 角色 | login_id | 密码 | 名称 |
|------|----------|------|------|
| 管理员 | admin | admin123 | 系统管理员 |
| 客服 | U00001 | 123456 | 张三 |
| 客服 | U00002 | 123456 | 李四 |
| 客服 | U00003 | 123456 | 王五 |
| 客服 | U00004 | 123456 | 赵六 |
| 客服 | U00005 | 123456 | 钱七 |
| 用户 | U00006 | 123456 | 刘一 |
| 用户 | U00007 | 123456 | 陈二 |
