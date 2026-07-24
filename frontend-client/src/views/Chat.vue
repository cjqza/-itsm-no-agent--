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
        <ChatMessage
          v-for="msg in messages"
          :key="msg.id"
          :msg="msg"
          :current-user-id="store.user?.id || 0"
        />
      </div>

      <ChatInput
        v-if="ticket?.status !== 'resolved'"
        ref="chatInputRef"
        placeholder="输入消息..."
        :onSend="sendMessage"
        :onUpload="handleUpload"
      />

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
import { statusType, statusText } from '@shared/utils/status'
import { useWebSocket } from '@shared/composables/useWebSocket'
import ChatMessage from '@shared/components/ChatMessage.vue'
import ChatInput from '@shared/components/ChatInput.vue'

const router = useRouter()
const route = useRoute()
const store = useUserStore()
const ticketId = route.params.ticketId

const ticket = ref(null)
const messages = ref([])
const chatRef = ref(null)
const chatInputRef = ref(null)
const rating = ref(5)
const ratingComment = ref('')
const currentRoomId = ref(null)

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
  await loadTicket()
  await loadMessages()
})

onUnmounted(() => {
  disconnect()
})

async function loadTicket() {
  ticket.value = await ticketApi.get(ticketId)
}

async function loadMessages() {
  try {
    const room = await chatApi.getRoom(ticketId)
    currentRoomId.value = room.id
    const msgRes = await chatApi.getMessages(room.id)
    messages.value = msgRes.items || msgRes
    scrollToBottom()
    connect(`/api/chat/ws/${room.id}`)
  } catch (e) {
    console.log('聊天室暂未创建，等待客服接单')
  }
}

async function sendMessage(text) {
  if (!text || !currentRoomId.value) return
  try {
    await chatApi.sendMessage(currentRoomId.value, { content: text })
  } catch (e) {
    ElMessage.error('发送失败')
  }
}

async function handleUpload(file) {
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.warning('文件大小不能超过10MB')
    return
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

.rating-section { padding: 20px; border-top: 1px solid #f0f0f0; }
.rating-section h3 { margin-bottom: 12px; color: #1e293b; }

.action-buttons {
  display: flex;
  gap: 8px;
  padding: 8px 20px;
  border-top: 1px solid #f0f0f0;
}
</style>
