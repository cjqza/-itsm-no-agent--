# 变更日志（CHANGELOG）

> 本文件由 initializer（记录管家 agent）维护，记录项目的开发进展与变更。最新条目在最上方。

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
