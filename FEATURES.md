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

### 1.2 文件上传与消息
- [x] 发送图片消息（jpg/png/gif/webp/bmp）
- [x] 发送文件消息（pdf/doc/xls/ppt/txt/csv/zip/rar）
- [x] 图片消息内联预览，支持放大查看
- [x] 文件消息显示下载链接
- [x] 待发送文件预览，可取消
- [x] 文件大小限制 10MB

### 1.3 我的工单
- [x] 工单列表（分页、状态筛选）
- [x] 工单详情查看
- [x] 点击工单进入聊天室

### 1.4 聊天室（/chat-rooms）
- [x] 左侧聊天室列表（含工单号、标题、最后消息、未读数）
- [x] 右侧聊天区域，支持文本/图片/文件消息
- [x] WebSocket 实时通信
- [x] 自动重连（指数退避 3s→30s）
- [x] 心跳 ping/pong（30s）
- [x] 消息已读标记
- [x] 删除聊天室（同时删除所有历史记录）
- [x] 工单状态标签显示

### 1.5 工单聊天（/chat/:ticketId）
- [x] 实时 WebSocket 聊天
- [x] 历史消息加载
- [x] 图片/文件消息展示
- [x] 待评价工单显示评分表单
- [x] 待接单工单可取消
- [x] 已接单/处理中工单可催单

### 1.6 登录
- [x] 飞书用户ID登录
- [x] 用户名登录

---

## 二、ITSM 客服端（frontend-agent :5174）

### 2.1 工作台（Dashboard）
- [x] 四象限看板布局
  - 左上：草稿箱工单（待接单 pending）
  - 右上：待处理工单池（已受理 accepted）
  - 左下：我的待办工单（处理中 processing）
  - 右下：已解决工单（待评价/已评价）
- [x] 每个面板显示工单数量标签
- [x] 待接单工单可直接接单
- [x] SLA 进度条显示
- [x] 待评价/已评价标签切换

### 2.2 服务请求（TicketList）
- [x] 工单列表（分页、搜索）
- [x] 状态筛选（待接单、已接单、处理中、待评价、已解决）
- [x] 点击进入工单详情

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
- [x] 飞书用户ID登录
- [x] 用户名登录
- [x] 快捷登录（张三、李四、管理员）

---

## 三、后台管理（frontend :5175）

### 3.1 权限管理
- [x] 用户列表（分页、搜索）
- [x] 权限申请审批
- [x] 启用/禁用用户
- [x] 权限设置（itsm_access、ops_access、admin_access）

### 3.2 分类配置
- [x] 管理单元 CRUD
- [x] 业务模块 CRUD
- [x] 性质/症状/原因/解决方法 CRUD
- [x] SLA 时长配置

### 3.3 登录
- [x] 飞书用户ID登录
- [x] 用户名登录
- [x] 管理员权限校验（路由守卫）

---

## 四、OPS 统计系统（frontend-ops :5176）

### 4.1 数据概览（Overview）
- [x] 今日工单数、待处理数、处理中数、已解决数
- [x] 工单趋势图表（ECharts）
- [x] 分类分布饼图
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
- [x] 导出功能

### 4.5 登录
- [x] 飞书用户ID登录
- [x] 用户名登录

---

## 五、后端 API（52 个端点）

### 5.1 认证（auth.py — 3 个）
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/auth/login | 登录（支持 feishu_user_id 或 name） |
| GET | /api/auth/me | 获取当前用户信息 |
| GET | /api/auth/permissions | 获取当前用户权限 |

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
| GET | /api/chat/rooms/{room_id}/messages | 获取聊天记录 |
| POST | /api/chat/rooms/{room_id}/messages | 发送消息 |
| PUT | /api/chat/rooms/{room_id}/close | 关闭聊天室 |
| POST | /api/chat/rooms/{room_id}/read | 标记已读 |
| GET | /api/chat/rooms/{room_id}/unread | 未读数 |
| WS | /api/chat/ws/{room_id} | WebSocket 实时聊天 |

### 5.4 后台管理（admin.py — 15 个）
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/admin/users | 用户列表 |
| PUT | /api/admin/users/{id} | 更新用户 |
| PUT | /api/admin/users/{id}/status | 启用/禁用 |
| GET | /api/admin/permissions | 权限列表 |
| GET | /api/admin/permission-requests | 权限申请列表 |
| POST | /api/admin/permission-requests | 提交权限申请 |
| PUT | /api/admin/permission-requests/{id} | 审批权限申请 |
| GET | /api/admin/agents | 客服列表（itsm_access） |
| CRUD | /api/admin/categories/ | 管理单元 |
| CRUD | /api/admin/business-modules/ | 业务模块 |
| CRUD | /api/admin/properties/ | 性质 |
| CRUD | /api/admin/symptoms/ | 症状 |
| CRUD | /api/admin/causes/ | 原因 |
| CRUD | /api/admin/solutions/ | 解决方法 |

### 5.5 OPS 统计（ops.py — 7 个）
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/ops/statistics | 综合统计 |
| GET | /api/ops/export | 导出报表 |
| GET | /api/ops/trend | 趋势分析 |
| GET | /api/ops/category-distribution | 分类分布 |
| GET | /api/ops/agent-performance | 客服绩效 |
| GET | /api/ops/sla-stats | SLA 统计 |
| GET | /api/ops/ticket-history | 历史工单查询 |

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

---

## 六、通用功能

### 6.1 认证与权限
- [x] JWT Token 认证
- [x] 三级权限体系（itsm_access、ops_access、admin_access）
- [x] 管理员/超级管理员自动拥有所有权限
- [x] 权限申请 → 管理员审批流程
- [x] 登录限流（10 次/分钟）

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

### 6.4 其他
- [x] API 限流（登录 10/min，其他 120/min）
- [x] 文件上传（图片/文档/文本/压缩包，10MB）
- [x] 快捷回复模板
- [x] 工单操作日志
- [x] 404 兜底路由

---

## 七、测试账号

| 角色 | feishu_user_id | 名称 |
|------|----------------|------|
| 管理员 | admin | 系统管理员 |
| 客服 | agent_1 | 张三 |
| 客服 | agent_2 | 李四 |
| 客服 | agent_3 | 王五 |
| 客服 | agent_4 | 赵六 |
| 客服 | agent_5 | 钱七 |
| 用户 | user1 | 刘一 |
| 用户 | user2 | 陈二 |
