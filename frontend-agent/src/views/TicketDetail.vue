<template>
  <div class="ticket-detail" v-loading="loading">
    <!-- 顶部操作栏 -->
    <el-card class="top-bar">
      <div class="top-actions">
        <el-button @click="router.back()">← 返回</el-button>
        <div class="ticket-title">
          <span class="no">{{ ticket.ticket_no }}</span>
          <span>{{ ticket.title }}</span>
        </div>
        <div class="actions">
          <el-button v-if="ticket.status === 'pending'" type="primary" @click="handleAccept">接单</el-button>
          <el-button v-if="ticket.status === 'accepted'" type="primary" @click="handleStatus('processing')">开始处理</el-button>
          <el-button v-if="ticket.status === 'processing'" type="success" @click="handleResolve">解决</el-button>
          <el-button @click="showRemark = true">修改标注</el-button>
          <el-button v-if="!ticket.is_sla_paused" @click="handlePauseSla">暂停计时</el-button>
          <el-button v-else @click="handleResumeSla">恢复计时</el-button>
        </div>
      </div>
    </el-card>

    <el-row :gutter="16" style="margin-top:16px">
      <!-- 左侧：工单信息 -->
      <el-col :span="14">
        <!-- 生命周期进度条 -->
        <el-card class="section">
          <div class="lifecycle">
            <div v-for="(step, i) in lifecycleSteps" :key="i" :class="['step', step.active ? 'active' : '', step.done ? 'done' : '']">
              <div class="step-icon">{{ step.done ? '✓' : i + 1 }}</div>
              <div class="step-label">{{ step.label }}</div>
            </div>
          </div>
        </el-card>

        <!-- 问题描述 -->
        <el-card class="section" style="margin-top:16px">
          <template #header><span>问题描述</span></template>
          <div class="description">{{ ticket.description || '无描述' }}</div>
          <div class="meta">
            <span>提交人：{{ ticket.creator_name }}</span>
            <span>优先级：<el-tag :type="priorityType(ticket.priority)" size="small">{{ ticket.priority }}</el-tag></span>
            <span>分类：{{ ticket.category_name || '未分类' }}</span>
          </div>
        </el-card>

        <!-- SLA计时 -->
        <el-card class="section" style="margin-top:16px">
          <template #header>
            <div class="sla-header">
              <span>SLA时效</span>
              <el-tag v-if="ticket.is_sla_paused" type="warning" size="small">已暂停</el-tag>
            </div>
          </template>
          <div class="sla-bar">
            <el-progress :percentage="slaPercent" :color="slaColor(ticket.sla_status)" :stroke-width="20" />
            <div class="sla-info">
              <span>已消耗：{{ slaPercent }}%</span>
              <span>剩余：{{ slaRemaining }}</span>
              <span>状态：<el-tag :type="slaTagType(ticket.sla_status)" size="small">{{ slaText(ticket.sla_status) }}</el-tag></span>
            </div>
          </div>
        </el-card>

        <!-- 分类信息 -->
        <el-card class="section" style="margin-top:16px">
          <template #header><span>工单分类</span></template>
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="负责人">{{ ticket.assignee_name || '未分配' }}</el-descriptions-item>
            <el-descriptions-item label="管理单元">{{ ticket.category_name || '未填写' }}</el-descriptions-item>
            <el-descriptions-item label="业务模块">{{ ticket.business_module_name || '未填写' }}</el-descriptions-item>
            <el-descriptions-item label="性质">{{ ticket.property_name || '未填写' }}</el-descriptions-item>
            <el-descriptions-item label="症状">{{ ticket.symptom_name || '未填写' }}</el-descriptions-item>
            <el-descriptions-item label="原因">{{ ticket.cause_name || '未填写' }}</el-descriptions-item>
            <el-descriptions-item label="解决方法" :span="2">{{ ticket.solution_name || '未填写' }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>

      <!-- 右侧：操作+历史+聊天 -->
      <el-col :span="10">
        <!-- 操作按钮 -->
        <el-card class="section">
          <template #header><span>操作</span></template>
          <div class="op-buttons">
            <el-button v-if="ticket.status === 'processing'" type="success" @click="handleResolve" style="width:100%">解决</el-button>
            <el-button type="warning" @click="showTransfer = true" style="width:100%">转派</el-button>
            <el-button type="info" disabled style="width:100%">派至现场 (开发中)</el-button>
            <el-button type="info" disabled style="width:100%">升级 (开发中)</el-button>
          </div>
        </el-card>

        <!-- 转派对话框 -->
        <el-dialog v-model="showTransfer" title="转派工单" width="400px">
          <el-form label-width="80px">
            <el-form-item label="目标客服">
              <el-select v-model="transferTarget" placeholder="选择客服" style="width: 100%">
                <el-option v-for="a in agents" :key="a.id" :label="a.name" :value="a.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="转派原因">
              <el-input v-model="transferReason" type="textarea" :rows="2" placeholder="请输入转派原因（可选）" />
            </el-form-item>
          </el-form>
          <template #footer>
            <el-button @click="showTransfer = false">取消</el-button>
            <el-button type="primary" @click="handleTransfer" :loading="operating">确认转派</el-button>
          </template>
        </el-dialog>

        <!-- 操作历史 -->
        <el-card class="section" style="margin-top:16px">
          <template #header><span>操作历史</span></template>
          <el-timeline>
            <el-timeline-item v-for="log in logs" :key="log.id" :timestamp="formatTime(log.created_at)" placement="top">
              <div class="log-item">
                <span class="log-user">{{ log.operator_name || '系统' }}</span>
                <span class="log-action">{{ log.content || log.action }}</span>
              </div>
            </el-timeline-item>
          </el-timeline>
        </el-card>

        <!-- 聊天区域 -->
        <el-card class="section chat-card" style="margin-top:16px" v-if="chatRoom">
          <template #header><span>对话</span></template>
          <div class="chat-messages" ref="chatRef">
            <div v-for="msg in chatMessages" :key="msg.id" :class="['chat-msg', msg.msg_type]">
              <template v-if="msg.msg_type === 'system'">
                <div class="sys-msg">{{ msg.content }}</div>
              </template>
              <template v-else>
                <div :class="['bubble', msg.sender_id === store.user.id ? 'mine' : 'other']">
                  <div class="sender">{{ msg.sender_name }}</div>
                  <div class="text">{{ msg.content }}</div>
                </div>
              </template>
            </div>
          </div>
          <div class="chat-input" v-if="chatRoom.status === 'active'">
            <el-input v-model="chatText" placeholder="输入消息..." @keyup.enter="sendChat" />
            <el-button type="primary" @click="sendChat" :disabled="!chatText.trim()">发送</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 备注对话框 -->
    <el-dialog v-model="showRemark" title="修改标注" width="400px">
      <el-input v-model="remarkText" type="textarea" :rows="3" placeholder="输入备注" />
      <template #footer>
        <el-button @click="showRemark = false">取消</el-button>
        <el-button type="primary" @click="handleRemark">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/store/user'
import { ticketApi, chatApi, adminApi } from '@/api'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'

const router = useRouter()
const route = useRoute()
const store = useUserStore()
const ticketId = route.params.id

const ticket = ref({})
const logs = ref([])
const agents = ref([])
const chatRoom = ref(null)
const chatMessages = ref([])
const chatText = ref('')
const chatRef = ref(null)
const loading = ref(false)
const operating = ref(false)
const showRemark = ref(false)
const remarkText = ref('')
const showTransfer = ref(false)
const transferTarget = ref(null)
const transferReason = ref('')
let chatWs = null

onMounted(async () => {
  await loadAll()
})

onUnmounted(() => {
  if (chatWs) { chatWs.close(); chatWs = null }
})

async function loadAll() {
  loading.value = true
  try {
    const [t, l, a] = await Promise.all([
      ticketApi.get(ticketId),
      ticketApi.logs(ticketId),
      adminApi.getAgents().catch(() => []),
    ])
    ticket.value = t
    logs.value = l
    agents.value = a || []
    remarkText.value = t.remark || ''

    // 加载聊天室
    try {
      chatRoom.value = await chatApi.getRoom(ticketId)
      const msgRes = await chatApi.getMessages(chatRoom.value.id)
      chatMessages.value = msgRes.items || msgRes
      scrollToBottom()
      connectChatWs()
    } catch (e) { chatRoom.value = null }
  } finally { loading.value = false }
}

function connectChatWs() {
  if (chatWs) chatWs.close()
  if (!chatRoom.value) return
  const token = localStorage.getItem('token')
  if (!token) return
  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
  const roomId = chatRoom.value.id
  chatWs = new WebSocket(`${protocol}//${location.host}/api/chat/ws/${roomId}?token=${token}`)

  chatWs.onmessage = (event) => {
    if (event.data === 'pong') return
    try {
      const data = JSON.parse(event.data)
      if (data.type === 'chat_message' && data.message) {
        // 避免重复：如果消息已存在则跳过
        const exists = chatMessages.value.some(m => m.id === data.message.id)
        if (!exists) {
          chatMessages.value.push(data.message)
          scrollToBottom()
        }
      }
    } catch (e) {}
  }

  chatWs.onclose = () => {
    // 自动重连（仅在组件还挂载时）
    if (chatRoom.value) {
      setTimeout(() => connectChatWs(), 3000)
    }
  }
}

const lifecycleSteps = computed(() => {
  const statusOrder = ['pending', 'accepted', 'processing', 'resolved_pending_review', 'resolved']
  const labels = ['提单', '接单', '处理', '解决', '评价']
  const currentIdx = statusOrder.indexOf(ticket.value.status)
  return labels.map((label, i) => ({
    label,
    done: i < currentIdx || (i === currentIdx && ticket.value.status === 'resolved'),
    active: i === currentIdx,
  }))
})

const slaPercent = computed(() => {
  if (!ticket.value.sla_deadline || !ticket.value.created_at) return 0
  const total = new Date(ticket.value.sla_deadline) - new Date(ticket.value.created_at)
  const elapsed = Date.now() - new Date(ticket.value.created_at)
  return Math.min(100, Math.round(elapsed / total * 100))
})

const slaRemaining = computed(() => {
  if (!ticket.value.sla_deadline) return '-'
  const remaining = new Date(ticket.value.sla_deadline) - Date.now()
  if (remaining <= 0) return '已超时'
  const hours = Math.floor(remaining / 3600000)
  const minutes = Math.floor((remaining % 3600000) / 60000)
  return `${hours}h ${minutes}m`
})

async function handleAccept() {
  try {
    await ticketApi.accept(ticketId)
    ElMessage.success('接单成功')
    await loadAll()
  } catch (e) { ElMessage.error('接单失败') }
}

async function handleStatus(status) {
  try {
    await ticketApi.updateStatus(ticketId, { status })
    ElMessage.success('状态更新成功')
    await loadAll()
  } catch (e) { ElMessage.error('状态更新失败') }
}

async function handleResolve() {
  try {
    await ticketApi.resolve(ticketId)
    ElMessage.success('已标记为待评价')
    await loadAll()
  } catch (e) { ElMessage.error('操作失败') }
}

async function handleTransfer() {
  if (!transferTarget.value) { ElMessage.warning('请选择目标客服'); return }
  operating.value = true
  try {
    await ticketApi.transfer(ticketId, { assignee_id: transferTarget.value, reason: transferReason.value })
    ElMessage.success('转派成功')
    showTransfer.value = false
    transferTarget.value = null
    transferReason.value = ''
    await loadAll()
  } catch (e) { ElMessage.error('转派失败') }
  finally { operating.value = false }
}

async function handleRemark() {
  try {
    await ticketApi.remark(ticketId, { remark: remarkText.value })
    showRemark.value = false
    ElMessage.success('标注已更新')
    await loadAll()
  } catch (e) { ElMessage.error('标注更新失败') }
}

async function handlePauseSla() {
  try {
    await ticketApi.remark(ticketId, { remark: '暂停计时', pause_ola: true })
    ElMessage.success('SLA已暂停')
    await loadAll()
  } catch (e) { ElMessage.error('SLA暂停失败') }
}

async function handleResumeSla() {
  try {
    await ticketApi.remark(ticketId, { remark: '恢复计时', pause_ola: false })
    ElMessage.success('SLA已恢复')
    await loadAll()
  } catch (e) { ElMessage.error('SLA恢复失败') }
}

async function sendChat() {
  const text = chatText.value.trim()
  if (!text || !chatRoom.value) return
  try {
    await chatApi.sendMessage(chatRoom.value.id, { content: text })
    chatText.value = ''
    // 消息会通过WebSocket实时返回，无需手动刷新
  } catch (e) { ElMessage.error('发送失败') }
}

function scrollToBottom() { nextTick(() => { if (chatRef.value) chatRef.value.scrollTop = chatRef.value.scrollHeight }) }

function priorityType(p) { return { P1: 'danger', P2: 'warning', P3: '', P4: 'info' }[p] || '' }
function slaColor(s) { return { green: '#67c23a', yellow: '#e6a23c', red: '#f56c6c', black: '#333' }[s] || '#999' }
function slaText(s) { return { green: '正常', yellow: '预警', red: '警告', black: '超时' }[s] || '' }
function slaTagType(s) { return { green: 'success', yellow: 'warning', red: 'danger', black: 'info' }[s] || 'info' }
function formatTime(t) { return t ? dayjs(t).format('YYYY-MM-DD HH:mm:ss') : '' }
</script>

<style scoped>
/* 卡片通用样式 */
.section {
  border-radius: 12px;
  border: none;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}
.section :deep(.el-card__header) {
  padding: 14px 20px;
  border-bottom: 1px solid #f0f0f0;
  background: #fafbfc;
  border-radius: 12px 12px 0 0;
  font-weight: 600;
  font-size: 14px;
  color: #1e293b;
}

.top-bar {
  border-radius: 12px;
  border: none;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}
.top-bar .top-actions { display: flex; align-items: center; gap: 16px; }
.ticket-title { flex: 1; display: flex; align-items: center; gap: 8px; }
.ticket-title .no { color: #2563eb; font-weight: 700; font-size: 15px; }
.ticket-title span:last-child { font-size: 14px; color: #334155; font-weight: 500; }
.actions { display: flex; gap: 8px; }

/* 生命周期进度条 */
.lifecycle { display: flex; justify-content: space-between; padding: 24px 16px; }
.step { display: flex; flex-direction: column; align-items: center; gap: 10px; position: relative; flex: 1; }
.step::after { content: ''; position: absolute; top: 18px; left: 50%; width: 100%; height: 2px; background: #e5e7eb; z-index: 0; }
.step:last-child::after { display: none; }
.step.done::after { background: #22c55e; }
.step-icon {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #f1f5f9;
  color: #94a3b8;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  z-index: 1;
  transition: all 0.2s;
}
.step.done .step-icon { background: #22c55e; color: white; box-shadow: 0 2px 8px rgba(34, 197, 94, 0.3); }
.step.active .step-icon { background: #3b82f6; color: white; box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3); }
.step-label { font-size: 12px; color: #94a3b8; font-weight: 500; }
.step.done .step-label, .step.active .step-label { color: #1e293b; font-weight: 600; }

/* 问题描述 */
.description {
  padding: 16px;
  background: #f8fafc;
  border-radius: 10px;
  font-size: 14px;
  line-height: 1.7;
  white-space: pre-wrap;
  color: #334155;
}
.meta { margin-top: 14px; display: flex; gap: 24px; font-size: 13px; color: #64748b; }

/* SLA */
.sla-header { display: flex; justify-content: space-between; align-items: center; }
.sla-info { display: flex; gap: 24px; margin-top: 10px; font-size: 13px; color: #64748b; }

/* 操作按钮 */
.op-buttons { display: flex; flex-direction: column; gap: 8px; }
.op-buttons .el-button { border-radius: 8px; }

/* 操作历史 */
.log-item { display: flex; gap: 8px; }
.log-user { font-weight: 600; color: #1e293b; font-size: 13px; }
.log-action { color: #64748b; font-size: 13px; }

/* 聊天区域 */
.chat-card :deep(.el-card__body) { padding: 0; }
.chat-messages { height: 300px; overflow-y: auto; padding: 16px; }
.chat-msg { margin-bottom: 12px; }
.sys-msg { text-align: center; color: #94a3b8; font-size: 12px; padding: 8px 0; }
.bubble { max-width: 80%; }
.bubble.mine { margin-left: auto; }
.sender { font-size: 11px; color: #94a3b8; margin-bottom: 4px; }
.bubble.mine .sender { text-align: right; }
.text {
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 13px;
  line-height: 1.5;
  word-break: break-word;
}
.bubble.mine .text { background: linear-gradient(135deg, #3b82f6, #2563eb); color: white; border-bottom-right-radius: 4px; }
.bubble.other .text { background: #f1f5f9; color: #334155; border-bottom-left-radius: 4px; }
.chat-input { display: flex; gap: 8px; padding: 14px; border-top: 1px solid #f0f0f0; background: #fafbfc; }
</style>
