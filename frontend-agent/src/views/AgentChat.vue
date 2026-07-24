<template>
  <div class="agent-chat">
    <!-- 左侧: 工单列表 -->
    <div class="sidebar">
      <div class="sidebar-header">
        <span class="title">消息</span>
        <el-badge :value="ticketList.length" :max="99" class="badge" />
      </div>
      <div class="ticket-list">
        <div
          v-for="t in ticketList"
          :key="t.id"
          :class="['ticket-item', { active: selectedTicket?.id === t.id }]"
          @click="selectTicket(t)"
        >
          <div class="item-left">
            <el-badge :value="unreadCounts[t.id] || 0" :hidden="!unreadCounts[t.id]" :max="99" class="unread-badge">
              <div class="status-dot" :style="{ background: statusColor(t.status) }"></div>
            </el-badge>
          </div>
          <div class="item-body">
            <div class="item-top">
              <span class="ticket-no">{{ t.ticket_no }}</span>
              <span class="time">{{ formatTime(t.updated_at || t.created_at) }}</span>
            </div>
            <div class="item-title">{{ t.title }}</div>
            <div class="item-preview">
              <el-tag :type="statusTagType(t.status)" size="small">{{ statusText(t.status) }}</el-tag>
              <span class="creator">{{ t.creator_name }}</span>
            </div>
          </div>
        </div>
        <el-empty v-if="ticketList.length === 0" description="暂无进行中的工单" />
      </div>
    </div>

    <!-- 右侧: 聊天区域 -->
    <div class="chat-area">
      <template v-if="selectedTicket">
        <!-- 头部 -->
        <div class="chat-header">
          <div class="header-info">
            <span class="no">{{ selectedTicket.ticket_no }}</span>
            <span class="title">{{ selectedTicket.title }}</span>
            <el-tag :type="statusTagType(selectedTicket.status)" size="small" style="margin-left: 8px">
              {{ statusText(selectedTicket.status) }}
            </el-tag>
          </div>
          <div class="header-actions">
            <el-button size="small" @click="goToDetail">查看详情</el-button>
            <el-button v-if="selectedTicket.status === 'processing'" type="success" size="small" @click="handleResolve">
              标记解决
            </el-button>
          </div>
        </div>

        <!-- 消息列表 -->
        <div class="messages" ref="messagesRef">
          <ChatMessage
            v-for="msg in messages"
            :key="msg.id"
            :msg="msg"
            :current-user-id="store.user.id"
          />
          <div v-if="messages.length === 0" class="no-messages">暂无消息</div>
        </div>

        <!-- 输入区域 -->
        <ChatInput
          v-if="chatRoom && chatRoom.status === 'active'"
          placeholder="输入消息... (Enter发送)"
          @send="sendMessage"
        />
        <div class="input-area disabled" v-else-if="chatRoom && chatRoom.status === 'closed'">
          <span class="closed-hint">聊天室已关闭</span>
        </div>
      </template>

      <!-- 未选择工单 -->
      <div v-else class="empty-chat">
        <el-icon :size="64" color="#ddd"><ChatDotRound /></el-icon>
        <p>选择一个工单开始对话</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
import { ticketApi, chatApi } from '@/api'
import { ElMessage } from 'element-plus'
import { ChatDotRound } from '@element-plus/icons-vue'
import { statusTagType, statusText } from '@shared/utils/status'
import { useWebSocket } from '@shared/composables/useWebSocket'
import ChatMessage from '@shared/components/ChatMessage.vue'
import ChatInput from '@shared/components/ChatInput.vue'
import dayjs from 'dayjs'

const router = useRouter()
const store = useUserStore()

const ticketList = ref([])
const selectedTicket = ref(null)
const chatRoom = ref(null)
const messages = ref([])
const messagesRef = ref(null)
const unreadCounts = ref({})

const { connect, disconnect } = useWebSocket({
  onMessage: (data) => {
    if (data.type === 'chat_message' && data.message) {
      const exists = messages.value.some(m => m.id === data.message.id)
      if (!exists) {
        messages.value.push(data.message)
        scrollToBottom()
      }
    }
  },
})

onMounted(async () => {
  await loadTickets()
})

onUnmounted(() => {
  disconnect()
})

async function loadTickets() {
  try {
    const res = await ticketApi.list({
      assignee_id: store.user.id,
      page_size: 100,
    })
    ticketList.value = (res.items || []).filter(t =>
      ['accepted', 'processing', 'resolved_pending_review'].includes(t.status)
    )
    await loadUnreadCounts()
  } catch (e) {
    console.error('加载工单失败', e)
  }
}

async function loadUnreadCounts() {
  const counts = {}
  for (const t of ticketList.value) {
    try {
      const room = await chatApi.getRoom(t.id)
      const unread = await chatApi.getUnread(room.id)
      if (unread.unread > 0) {
        counts[t.id] = unread.unread
      }
    } catch (e) { /* 聊天室可能不存在 */ }
  }
  unreadCounts.value = counts
}

async function selectTicket(ticket) {
  selectedTicket.value = ticket
  messages.value = []
  chatRoom.value = null
  disconnect()

  try {
    const room = await chatApi.getRoom(ticket.id)
    chatRoom.value = room

    const msgRes = await chatApi.getMessages(room.id)
    messages.value = msgRes.items || msgRes
    scrollToBottom()

    await chatApi.markRead(room.id)
    unreadCounts.value[ticket.id] = 0

    connect(`/api/chat/ws/${room.id}`)
  } catch (e) {
    chatRoom.value = null
  }
}

async function sendMessage(text) {
  if (!text || !chatRoom.value) return
  try {
    await chatApi.sendMessage(chatRoom.value.id, { content: text })
  } catch (e) {
    ElMessage.error('发送失败')
  }
}

async function handleResolve() {
  if (!selectedTicket.value) return
  try {
    await ticketApi.resolve(selectedTicket.value.id)
    ElMessage.success('已标记为待评价')
    await loadTickets()
    selectedTicket.value = null
    messages.value = []
    chatRoom.value = null
    disconnect()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

function goToDetail() {
  if (selectedTicket.value) {
    router.push(`/tickets/${selectedTicket.value.id}`)
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

function formatTime(t) {
  if (!t) return ''
  const d = dayjs(t)
  const now = dayjs()
  if (d.isSame(now, 'day')) return d.format('HH:mm')
  if (d.isSame(now.subtract(1, 'day'), 'day')) return '昨天'
  return d.format('MM-DD')
}

function statusColor(s) {
  return { accepted: '#409eff', processing: '#e6a23c', resolved_pending_review: '#67c23a' }[s] || '#999'
}
</script>

<style scoped>
.agent-chat {
  display: flex;
  height: calc(100vh - 60px);
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

/* 左侧边栏 */
.sidebar {
  width: 320px;
  border-right: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.sidebar-header {
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  gap: 8px;
  background: #fafafa;
}

.sidebar-header .title {
  font-size: 16px;
  font-weight: 600;
  color: #1a365d;
}

.ticket-list {
  flex: 1;
  overflow-y: auto;
}

.ticket-item {
  display: flex;
  gap: 12px;
  padding: 14px 20px;
  cursor: pointer;
  border-bottom: 1px solid #f3f4f6;
  transition: background 0.15s;
}

.ticket-item:hover {
  background: #f0f7ff;
}

.ticket-item.active {
  background: #e8f0fe;
  border-left: 3px solid #2563eb;
}

.item-left {
  padding-top: 4px;
}

.unread-badge :deep(.el-badge__content) {
  font-size: 10px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.item-body {
  flex: 1;
  min-width: 0;
}

.item-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.ticket-no {
  font-size: 13px;
  font-weight: 600;
  color: #2563eb;
}

.time {
  font-size: 11px;
  color: #999;
}

.item-title {
  font-size: 14px;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 6px;
}

.item-preview {
  display: flex;
  align-items: center;
  gap: 8px;
}

.creator {
  font-size: 12px;
  color: #999;
}

/* 右侧聊天区 */
.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.chat-header {
  padding: 12px 20px;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fafafa;
}

.header-info {
  display: flex;
  align-items: center;
  min-width: 0;
}

.header-info .no {
  font-weight: 600;
  color: #2563eb;
  margin-right: 8px;
  flex-shrink: 0;
}

.header-info .title {
  font-size: 15px;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.header-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.no-messages {
  text-align: center;
  color: #ccc;
  padding: 40px 0;
  font-size: 14px;
}

.input-area {
  display: flex;
  gap: 8px;
  padding: 16px 20px;
  border-top: 1px solid #e5e7eb;
  background: #fafafa;
}

.input-area.disabled {
  justify-content: center;
}

.closed-hint {
  color: #999;
  font-size: 14px;
}

.empty-chat {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  color: #ccc;
}

.empty-chat p {
  margin-top: 12px;
  font-size: 14px;
}
</style>
