<template>
  <div class="chat-rooms-page">
    <!-- 左侧：聊天室列表 -->
    <div class="rooms-sidebar">
      <div class="rooms-header">
        <h3>💬 我的聊天</h3>
      </div>
      <div class="rooms-list" v-loading="loading">
        <div v-if="rooms.length === 0" class="empty-rooms">
          <p>暂无聊天记录</p>
          <p class="empty-hint">提交工单后将自动创建聊天室</p>
        </div>
        <div
          v-for="room in rooms"
          :key="room.id"
          :class="['room-item', { active: selectedRoom?.id === room.id }]"
          @click="selectRoom(room)"
        >
          <div class="room-info">
            <div class="room-title">
              <span class="ticket-no">{{ room.ticket_no }}</span>
              <el-tag v-if="room.unread > 0" type="danger" size="small" class="unread-badge">{{ room.unread }}</el-tag>
            </div>
            <div class="room-subtitle">{{ room.ticket_title }}</div>
            <div class="room-last-msg" v-if="room.last_message">
              {{ room.last_message.content?.substring(0, 30) }}{{ room.last_message.content?.length > 30 ? '...' : '' }}
            </div>
          </div>
          <div class="room-meta">
            <el-tag :type="statusType(room.ticket_status)" size="small">{{ statusText(room.ticket_status) }}</el-tag>
            <el-dropdown trigger="click" @command="handleRoomAction($event, room)" @click.stop>
              <el-icon class="room-menu"><MoreFilled /></el-icon>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="delete" style="color: #f56c6c;">
                    <el-icon><Delete /></el-icon> 删除聊天
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧：聊天区域 -->
    <div class="chat-area">
      <template v-if="selectedRoom">
        <div class="chat-header">
          <span class="chat-title">{{ selectedRoom.ticket_no }} - {{ selectedRoom.ticket_title }}</span>
          <el-tag :type="statusType(selectedRoom.ticket_status)" size="small">{{ statusText(selectedRoom.ticket_status) }}</el-tag>
        </div>
        <div class="chat-messages" ref="chatRef">
          <div v-for="msg in messages" :key="msg.id" :class="['msg', msg.sender_id === userId ? 'self' : 'other']">
            <div class="msg-sender">{{ msg.sender_name }}</div>
            <div class="msg-content">
              <!-- 图片消息 -->
              <div v-if="msg.msg_type === 'image'" class="msg-image">
                <el-image :src="msg.content" :preview-src-list="[msg.content]" fit="contain" style="max-width: 260px; max-height: 260px; border-radius: 8px;" />
              </div>
              <!-- 文件消息 -->
              <div v-else-if="msg.msg_type === 'file'" class="msg-file">
                <el-icon :size="20"><Document /></el-icon>
                <a :href="getFileUrl(msg.content)" target="_blank" download class="file-link">{{ getFileName(msg.content) }}</a>
              </div>
              <!-- 系统消息 -->
              <div v-else-if="msg.msg_type === 'system'" class="msg-system">{{ msg.content }}</div>
              <!-- 文本消息 -->
              <div v-else class="msg-text">{{ msg.content }}</div>
            </div>
            <div class="msg-time">{{ formatTime(msg.created_at) }}</div>
          </div>
        </div>
        <div class="chat-input-area" v-if="selectedRoom.status !== 'closed'">
          <div class="input-row">
            <el-upload :show-file-list="false" :before-upload="handleFileSelect" accept="image/*,.pdf,.doc,.docx,.xls,.xlsx,.txt,.zip,.rar">
              <el-button :icon="Paperclip" circle />
            </el-upload>
            <el-input
              v-model="inputText"
              placeholder="输入消息... (Enter发送)"
              @keyup.enter="sendTextMessage"
              :disabled="sending"
            />
            <el-button type="primary" @click="sendTextMessage" :loading="sending" :disabled="!inputText.trim() && !pendingFile">
              发送
            </el-button>
          </div>
          <div v-if="pendingFile" class="pending-file">
            <el-tag closable @close="pendingFile = null" size="small">
              <el-icon><Document /></el-icon> {{ pendingFile.name }}
            </el-tag>
          </div>
        </div>
        <div v-else class="chat-closed-hint">
          <el-icon><CircleClose /></el-icon> 聊天室已关闭
        </div>
      </template>
      <div v-else class="no-chat-selected">
        <div class="no-chat-icon">💬</div>
        <p>选择一个聊天开始对话</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Paperclip, Document, MoreFilled, Delete, CircleClose } from '@element-plus/icons-vue'
import { chatApi, uploadApi } from '@/api'
import { useUserStore } from '@/store/user'

const store = useUserStore()
const userId = computed(() => store.userId)

const rooms = ref([])
const selectedRoom = ref(null)
const messages = ref([])
const inputText = ref('')
const pendingFile = ref(null)
const sending = ref(false)
const loading = ref(false)
const chatRef = ref(null)
const ws = ref(null)
const reconnectAttempts = ref(0)

// 加载聊天室列表
async function loadRooms() {
  loading.value = true
  try {
    rooms.value = await chatApi.getMyRooms()
  } catch (e) {
    console.error('加载聊天室列表失败', e)
  }
  loading.value = false
}

// 选择聊天室
async function selectRoom(room) {
  selectedRoom.value = room
  messages.value = []
  try {
    const msgRes = await chatApi.getMessages(room.id)
    messages.value = msgRes.items || msgRes
    scrollToBottom()
    // 标记已读
    await chatApi.markRead(room.id)
    room.unread = 0
    // 连接WebSocket
    connectWS(room.id)
  } catch (e) {
    console.error('加载聊天记录失败', e)
  }
}

// WebSocket连接
function connectWS(roomId) {
  if (ws.value) {
    ws.value.close()
    ws.value = null
  }
  const token = localStorage.getItem('token')
  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${protocol}//${location.host}/api/chat/ws/${roomId}?token=${token}`
  const socket = new WebSocket(wsUrl)

  socket.onopen = () => {
    reconnectAttempts.value = 0
    // 启动心跳
    socket._heartbeat = setInterval(() => {
      if (socket.readyState === WebSocket.OPEN) socket.send('ping')
    }, 30000)
  }

  socket.onmessage = (event) => {
    if (event.data === 'pong') return
    try {
      const data = JSON.parse(event.data)
      if (data.type === 'chat_message' && data.room_id === roomId) {
        messages.value.push(data.message)
        scrollToBottom()
        // 标记已读
        chatApi.markRead(roomId).catch(() => {})
      }
    } catch (e) {}
  }

  socket.onclose = () => {
    if (socket._heartbeat) clearInterval(socket._heartbeat)
    // 重连
    if (selectedRoom.value?.id === roomId && reconnectAttempts.value < 10) {
      reconnectAttempts.value++
      const delay = Math.min(3000 * reconnectAttempts.value, 30000)
      setTimeout(() => {
        if (selectedRoom.value?.id === roomId) connectWS(roomId)
      }, delay)
    }
  }

  ws.value = socket
}

// 发送文本消息
async function sendTextMessage() {
  const text = inputText.value.trim()
  if (!text) return

  // 如果有文件，先上传
  if (pendingFile.value) {
    sending.value = true
    const uploadResult = await uploadFile(pendingFile.value)
    sending.value = false
    if (uploadResult) {
      const isImage = pendingFile.value.type.startsWith('image/')
      const content = isImage ? `[图片] ${uploadResult.url}` : `[文件] ${pendingFile.value.name}\n${uploadResult.url}`
      await chatApi.sendMessage(selectedRoom.value.id, {
        content,
        msg_type: isImage ? 'image' : 'text',
      })
    }
    pendingFile.value = null
  }

  if (!text) return
  inputText.value = ''
  sending.value = true
  try {
    await chatApi.sendMessage(selectedRoom.value.id, { content: text, msg_type: 'text' })
  } catch (e) {
    ElMessage.error('发送失败')
  }
  sending.value = false
}

// 文件上传
function handleFileSelect(file) {
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.warning('文件大小不能超过10MB')
    return false
  }
  pendingFile.value = file
  return false
}

async function uploadFile(file) {
  try {
    return await uploadApi.upload(file)
  } catch (e) {
    ElMessage.error('文件上传失败')
    return null
  }
}

// 删除聊天室
async function handleRoomAction(command, room) {
  if (command === 'delete') {
    try {
      await ElMessageBox.confirm('删除后聊天记录将无法恢复，确定要删除吗？', '删除聊天', {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
      })
      await chatApi.deleteRoom(room.id)
      ElMessage.success('已删除')
      if (selectedRoom.value?.id === room.id) {
        selectedRoom.value = null
        messages.value = []
        if (ws.value) { ws.value.close(); ws.value = null }
      }
      await loadRooms()
    } catch (e) {
      if (e !== 'cancel') ElMessage.error('删除失败')
    }
  }
}

// 辅助函数
function scrollToBottom() {
  nextTick(() => {
    if (chatRef.value) chatRef.value.scrollTop = chatRef.value.scrollHeight
  })
}

function statusType(status) {
  const map = { pending: 'info', accepted: '', processing: 'warning', resolved_pending_review: 'success', resolved: 'success', closed: 'info' }
  return map[status] || 'info'
}

function statusText(status) {
  const map = { pending: '待接单', accepted: '已接单', processing: '处理中', resolved_pending_review: '待评价', resolved: '已解决', closed: '已关闭' }
  return map[status] || status
}

function formatTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  const now = new Date()
  const diff = now - d
  if (diff < 86400000 && d.getDate() === now.getDate()) {
    return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  }
  return d.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' }) + ' ' + d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

function getFileUrl(content) {
  if (!content) return ''
  const lines = content.split('\n')
  return lines[lines.length - 1] || ''
}

function getFileName(content) {
  if (!content) return '文件'
  const match = content.match(/\[文件\]\s*(.+)/)
  return match ? match[1] : '文件'
}

onMounted(loadRooms)
</script>

<style scoped>
.chat-rooms-page {
  display: flex;
  height: calc(100vh - 120px);
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}

/* 左侧栏 */
.rooms-sidebar { width: 300px; border-right: 1px solid #f0f0f0; display: flex; flex-direction: column; }
.rooms-header { padding: 16px 20px; border-bottom: 1px solid #f0f0f0; background: #fafbfc; }
.rooms-header h3 { margin: 0; font-size: 16px; color: #1e293b; font-weight: 600; }
.rooms-list { flex: 1; overflow-y: auto; }
.empty-rooms { padding: 48px 20px; text-align: center; color: #94a3b8; }
.empty-hint { font-size: 12px; color: #cbd5e1; margin-top: 8px; }

.room-item {
  display: flex;
  align-items: center;
  padding: 14px 20px;
  cursor: pointer;
  border-bottom: 1px solid #f8fafc;
  transition: all 0.15s;
  gap: 12px;
}
.room-item:hover { background: #f0f7ff; }
.room-item.active {
  background: #eff6ff;
  border-left: 3px solid #3b82f6;
}

.room-info { flex: 1; min-width: 0; }
.room-title { display: flex; align-items: center; gap: 8px; }
.ticket-no { font-weight: 600; font-size: 13px; color: #1e293b; }
.unread-badge { margin-left: auto; }
.room-subtitle { font-size: 12px; color: #64748b; margin-top: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.room-last-msg { font-size: 11px; color: #94a3b8; margin-top: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.room-meta { display: flex; flex-direction: column; align-items: flex-end; gap: 8px; }
.room-menu { cursor: pointer; color: #94a3b8; padding: 4px; border-radius: 6px; transition: all 0.15s; }
.room-menu:hover { background: #e2e8f0; color: #64748b; }

/* 右侧聊天区 */
.chat-area { flex: 1; display: flex; flex-direction: column; }
.chat-header {
  padding: 14px 20px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
  gap: 12px;
  background: #fafbfc;
}
.chat-title { font-weight: 600; font-size: 14px; color: #1e293b; }

.chat-messages { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 12px; }
.msg { max-width: 70%; }
.msg.self { align-self: flex-end; }
.msg.other { align-self: flex-start; }
.msg-sender { font-size: 12px; color: #94a3b8; margin-bottom: 4px; }
.msg.self .msg-sender { text-align: right; }
.msg-content {
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.6;
  word-break: break-word;
}
.msg.self .msg-content {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: white;
  border-bottom-right-radius: 4px;
}
.msg.other .msg-content {
  background: #f1f5f9;
  color: #334155;
  border-bottom-left-radius: 4px;
}
.msg-system { background: transparent !important; color: #94a3b8 !important; text-align: center; font-size: 12px; padding: 4px 0 !important; }
.msg-time { font-size: 11px; color: #cbd5e1; margin-top: 4px; }
.msg.self .msg-time { text-align: right; }
.msg-image { margin: 4px 0; }
.msg-file { display: flex; align-items: center; gap: 8px; }
.file-link { color: inherit; text-decoration: underline; }

/* 输入区 */
.chat-input-area { padding: 12px 20px; border-top: 1px solid #f0f0f0; background: #fafbfc; }
.input-row { display: flex; gap: 8px; align-items: center; }
.pending-file { margin-top: 8px; }
.chat-closed-hint {
  padding: 16px;
  text-align: center;
  color: #94a3b8;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.no-chat-selected { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #cbd5e1; }
.no-chat-icon { font-size: 64px; margin-bottom: 16px; }
.no-chat-selected p { font-size: 16px; }
</style>
