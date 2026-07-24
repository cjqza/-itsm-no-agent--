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
          <ChatMessage
            v-for="msg in messages"
            :key="msg.id"
            :msg="msg"
            :current-user-id="userId"
          />
        </div>
        <ChatInput
          v-if="selectedRoom.status !== 'closed'"
          ref="chatInputRef"
          placeholder="输入消息... (Enter发送)"
          :onSend="sendTextMessage"
          :onUpload="handleFileUpload"
        />
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
import { ref, onMounted, onUnmounted, nextTick, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { MoreFilled, Delete, CircleClose } from '@element-plus/icons-vue'
import { chatApi, uploadApi } from '@/api'
import { useUserStore } from '@/store/user'
import { statusType, statusText } from '@shared/utils/status'
import { useWebSocket } from '@shared/composables/useWebSocket'
import ChatMessage from '@shared/components/ChatMessage.vue'
import ChatInput from '@shared/components/ChatInput.vue'

const store = useUserStore()
const userId = computed(() => store.userId)

const rooms = ref([])
const selectedRoom = ref(null)
const messages = ref([])
const loading = ref(false)
const chatRef = ref(null)
const chatInputRef = ref(null)

const { connect, disconnect } = useWebSocket({
  onMessage: (data) => {
    if (data.type === 'chat_message' && data.room_id === selectedRoom.value?.id) {
      messages.value.push(data.message)
      scrollToBottom()
      chatApi.markRead(selectedRoom.value.id).catch(() => {})
    }
  },
})

onUnmounted(() => {
  disconnect()
})

async function loadRooms() {
  loading.value = true
  try {
    rooms.value = await chatApi.getMyRooms()
  } catch (e) {
    console.error('加载聊天室列表失败', e)
  }
  loading.value = false
}

async function selectRoom(room) {
  selectedRoom.value = room
  messages.value = []
  disconnect()
  try {
    const msgRes = await chatApi.getMessages(room.id)
    messages.value = msgRes.items || msgRes
    scrollToBottom()
    await chatApi.markRead(room.id)
    room.unread = 0
    connect(`/api/chat/ws/${room.id}`)
  } catch (e) {
    console.error('加载聊天记录失败', e)
  }
}

async function sendTextMessage(text) {
  if (!text || !selectedRoom.value) return
  try {
    await chatApi.sendMessage(selectedRoom.value.id, { content: text, msg_type: 'text' })
  } catch (e) {
    ElMessage.error('发送失败')
  }
}

async function handleFileUpload(file) {
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.warning('文件大小不能超过10MB')
    return
  }
  try {
    const result = await uploadApi.upload(file)
    const isImage = file.type.startsWith('image/')
    const content = isImage ? `[图片] ${result.url}` : `[文件] ${file.name}\n${result.url}`
    await chatApi.sendMessage(selectedRoom.value.id, {
      content,
      msg_type: isImage ? 'image' : 'file',
    })
    ElMessage.success('文件发送成功')
  } catch (e) {
    ElMessage.error('文件上传失败')
  }
}

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
        disconnect()
      }
      await loadRooms()
    } catch (e) {
      if (e !== 'cancel') ElMessage.error('删除失败')
    }
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (chatRef.value) chatRef.value.scrollTop = chatRef.value.scrollHeight
  })
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
