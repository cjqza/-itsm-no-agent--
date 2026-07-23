<template>
  <div class="chat-page">
    <div class="chat-header">
      <el-button text @click="router.back()">← 返回</el-button>
      <div class="ticket-info">
        <span class="ticket-no">{{ ticket?.ticket_no }}</span>
        <span class="ticket-title">{{ ticket?.title }}</span>
      </div>
      <el-tag :type="statusType(ticket?.status)">{{ statusText(ticket?.status) }}</el-tag>
    </div>

    <div class="chat-body">
      <div class="messages" ref="chatRef">
        <div v-for="msg in messages" :key="msg.id" :class="['msg', msg.msg_type]">
          <template v-if="msg.msg_type === 'system'">
            <div class="sys-msg">{{ msg.content }}</div>
          </template>
          <template v-else>
            <div :class="['bubble', msg.sender_id === store.user.id ? 'mine' : 'other']">
              <div class="sender">{{ msg.sender_name }}</div>
              <!-- 图片消息 -->
              <div v-if="isImageMessage(msg)" class="image-content">
                <el-image :src="getImageUrl(msg.content)" :preview-src-list="[getImageUrl(msg.content)]" fit="contain" style="max-width: 280px; max-height: 280px; border-radius: 8px;" />
              </div>
              <!-- 文件消息 -->
              <div v-else-if="isFileMessage(msg)" class="file-content">
                <el-icon :size="20"><Document /></el-icon>
                <div class="file-info">
                  <span class="file-name">{{ getFileName(msg.content) }}</span>
                  <a :href="getFileUrl(msg.content)" target="_blank" download class="download-link">下载文件</a>
                </div>
              </div>
              <!-- 文本消息 -->
              <div v-else class="text">{{ msg.content }}</div>
              <div class="time">{{ formatTime(msg.created_at) }}</div>
            </div>
          </template>
        </div>
      </div>

      <div class="input-area" v-if="ticket?.status !== 'resolved'">
        <el-upload
          :show-file-list="false"
          :before-upload="handleUpload"
          accept="image/*,.pdf,.doc,.docx,.xls,.xlsx,.txt,.zip,.rar"
        >
          <el-button :icon="Paperclip" circle />
        </el-upload>
        <el-input v-model="inputText" placeholder="输入消息..." @keyup.enter="sendMessage" />
        <el-button type="primary" @click="sendMessage" :disabled="!inputText.trim()">发送</el-button>
      </div>

      <!-- 催办/取消按钮 -->
      <div class="action-buttons" v-if="ticket?.status === 'pending'">
        <el-button type="danger" @click="handleCancel">取消工单</el-button>
      </div>
      <div class="action-buttons" v-else-if="ticket?.status === 'accepted' || ticket?.status === 'processing'">
        <el-button type="warning" @click="handleUrge">催办</el-button>
      </div>

      <!-- 评价卡片 -->
      <div v-if="ticket?.status === 'resolved_pending_review'" class="rating-section">
        <el-card>
          <h3>请对本次服务进行评价</h3>
          <el-rate v-model="rating" size="large" />
          <el-input v-model="ratingComment" type="textarea" :rows="2" placeholder="评价内容（可选）" style="margin: 12px 0" />
          <el-button type="primary" @click="submitRating">提交评价</el-button>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/store/user'
import { ticketApi, chatApi, uploadApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Paperclip, Document } from '@element-plus/icons-vue'
import dayjs from 'dayjs'

const router = useRouter()
const route = useRoute()
const store = useUserStore()
const ticketId = route.params.ticketId

const ticket = ref(null)
const messages = ref([])
const inputText = ref('')
const chatRef = ref(null)
const rating = ref(5)
const ratingComment = ref('')
const currentRoomId = ref(null)
let ws = null
let heartbeatTimer = null
let reconnectAttempts = 0
const MAX_RECONNECT = 10

onMounted(async () => {
  await loadTicket()
  await loadMessages()
})

onUnmounted(() => {
  if (heartbeatTimer) { clearInterval(heartbeatTimer); heartbeatTimer = null }
  if (ws) { ws.close(); ws = null }
})

async function loadTicket() {
  ticket.value = await ticketApi.get(ticketId)
}

async function loadMessages() {
  try {
    const room = await chatApi.getRoom(ticketId)
    currentRoomId.value = room.id
    messages.value = await chatApi.getMessages(room.id)
    scrollToBottom()
    connectWebSocket()
  } catch (e) {
    console.log('聊天室暂未创建，等待客服接单')
  }
}

function connectWebSocket() {
  if (ws) ws.close()
  if (heartbeatTimer) { clearInterval(heartbeatTimer); heartbeatTimer = null }
  const token = localStorage.getItem('token')
  if (!token || !currentRoomId.value) return

  try {
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
    const roomId = currentRoomId.value
    ws = new WebSocket(`${protocol}//${location.host}/api/chat/ws/${roomId}?token=${token}`)

    ws.onopen = () => {
      reconnectAttempts = 0
      heartbeatTimer = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send('ping')
        }
      }, 30000)
    }

    ws.onmessage = (event) => {
      if (event.data === 'pong') return
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'chat_message' && data.message) {
          const exists = messages.value.some(m => m.id === data.message.id)
          if (!exists) {
            messages.value.push(data.message)
            scrollToBottom()
          }
        }
      } catch (e) { console.warn('解析消息失败', e) }
    }

    ws.onclose = () => {
      if (heartbeatTimer) { clearInterval(heartbeatTimer); heartbeatTimer = null }
      if (reconnectAttempts < MAX_RECONNECT) {
        const delay = Math.min(3000 * Math.pow(2, reconnectAttempts), 30000)
        reconnectAttempts++
        setTimeout(connectWebSocket, delay)
      }
    }
  } catch (e) { console.error('WebSocket连接失败', e) }
}

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || !currentRoomId.value) return

  try {
    await chatApi.sendMessage(currentRoomId.value, { content: text })
    inputText.value = ''
  } catch (e) {
    ElMessage.error('发送失败')
  }
}

async function handleUpload(file) {
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.warning('文件大小不能超过10MB')
    return false
  }

  try {
    const result = await uploadApi.upload(file)
    if (currentRoomId.value) {
      const isImage = file.type.startsWith('image/')
      const content = isImage ? `[图片] ${result.url}` : `[文件] ${file.name}\n${result.url}`
      await chatApi.sendMessage(currentRoomId.value, {
        content: content,
        msg_type: isImage ? 'image' : 'file',
      })
      ElMessage.success('文件发送成功')
    }
  } catch (e) { ElMessage.error('文件上传失败') }
  return false
}

function isImageMessage(msg) {
  return msg.msg_type === 'image' || (msg.content && msg.content.startsWith('[图片]'))
}

function isFileMessage(msg) {
  return msg.msg_type === 'file' || (msg.content && msg.content.startsWith('[文件]'))
}

function getImageUrl(content) {
  if (!content) return ''
  // 从 "[图片] /uploads/..." 格式中提取URL
  const match = content.match(/\[图片\]\s*(.+)/)
  return match ? match[1].trim() : content
}

function getFileUrl(content) {
  if (!content) return ''
  // 从 "[文件] filename\n/uploads/..." 格式中提取URL
  const lines = content.split('\n')
  for (const line of lines) {
    if (line.startsWith('/uploads/') || line.includes('/uploads/')) {
      return line.trim()
    }
  }
  return ''
}

function getFileName(content) {
  if (!content) return '文件'
  const match = content.match(/\[文件\]\s*(.+)/)
  if (match) {
    const fileName = match[1].split('\n')[0].trim()
    return fileName
  }
  return '文件'
}

async function submitRating() {
  try {
    await ticketApi.rate(ticketId, { rating: rating.value, rating_comment: ratingComment.value })
    ElMessage.success('评价成功')
    await loadTicket()
  } catch (e) { ElMessage.error('评价失败') }
}

async function handleCancel() {
  try {
    await ElMessageBox.confirm('确定要取消此工单吗？取消后将自动关闭。', '确认取消', { type: 'warning' })
    await ticketApi.cancel(ticketId)
    ElMessage.success('工单已取消')
    await loadTicket()
  } catch (e) { if (e !== 'cancel') ElMessage.error('取消失败') }
}

async function handleUrge() {
  try {
    await ticketApi.urge(ticketId, { message: '请尽快处理' })
    ElMessage.success('催办已发送')
  } catch (e) { ElMessage.error('催办失败') }
}

function scrollToBottom() {
  nextTick(() => { if (chatRef.value) chatRef.value.scrollTop = chatRef.value.scrollHeight })
}

function formatTime(t) { return t ? dayjs(t).format('HH:mm') : '' }
function statusType(s) {
  return { pending: 'info', accepted: '', processing: 'warning', resolved_pending_review: 'success', resolved: 'success' }[s] || 'info'
}
function statusText(s) {
  return { pending: '待接单', accepted: '已接单', processing: '处理中', resolved_pending_review: '待评价', resolved: '已解决' }[s] || s
}
</script>

<style scoped>
.chat-page {
  height: calc(100vh - 108px);
  display: flex;
  flex-direction: column;
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.chat-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 20px;
  border-bottom: 1px solid #f0f0f0;
  background: #fafbfc;
}

.ticket-info { flex: 1; }
.ticket-no { font-weight: 700; color: #2563eb; margin-right: 8px; font-size: 14px; }
.ticket-title { color: #334155; font-size: 14px; }

.chat-body { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
.messages { flex: 1; overflow-y: auto; padding: 20px; }
.msg { margin-bottom: 12px; }
.sys-msg { text-align: center; color: #94a3b8; font-size: 12px; padding: 8px; }
.bubble { max-width: 70%; }
.bubble.mine { margin-left: auto; }
.bubble.other { margin-right: auto; }
.sender { font-size: 12px; color: #94a3b8; margin-bottom: 4px; }
.bubble.mine .sender { text-align: right; }
.text {
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.6;
  word-break: break-word;
}
.bubble.mine .text {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: white;
  border-bottom-right-radius: 4px;
}
.bubble.other .text {
  background: #f1f5f9;
  color: #334155;
  border-bottom-left-radius: 4px;
}
.time { font-size: 11px; color: #cbd5e1; margin-top: 4px; }
.bubble.mine .time { text-align: right; }

/* 图片消息 */
.image-content { margin-bottom: 4px; }
.bubble.mine .image-content { text-align: right; }

/* 文件消息 */
.file-content {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: #f1f5f9;
  border-radius: 12px;
}
.bubble.mine .file-content { background: #1d4ed8; }
.file-info { display: flex; flex-direction: column; gap: 4px; }
.file-name { font-size: 13px; font-weight: 500; color: #334155; }
.bubble.mine .file-name { color: white; }
.download-link { font-size: 12px; color: #2563eb; text-decoration: none; }
.bubble.mine .download-link { color: #93c5fd; }

.input-area {
  display: flex;
  gap: 8px;
  padding: 14px 20px;
  border-top: 1px solid #f0f0f0;
  align-items: center;
  background: #fafbfc;
}

.rating-section { padding: 20px; border-top: 1px solid #f0f0f0; }
.rating-section h3 { margin-bottom: 12px; color: #1e293b; }

.action-buttons {
  display: flex;
  gap: 8px;
  padding: 8px 20px;
  border-top: 1px solid #f0f0f0;
}
</style>
