<template>
  <div :class="['chat-msg', msg.msg_type]">
    <!-- 系统消息 -->
    <template v-if="msg.msg_type === 'system'">
      <div class="sys-msg">{{ msg.content }}</div>
    </template>
    <!-- 普通消息 -->
    <template v-else>
      <div :class="['bubble', isMine ? 'mine' : 'other']">
        <div class="sender">{{ msg.sender_name }}</div>
        <!-- 图片消息 -->
        <div v-if="isImageMessage" class="image-content">
          <el-image :src="imageUrl" :preview-src-list="[imageUrl]" fit="contain" style="max-width: 280px; max-height: 280px; border-radius: 8px;" />
        </div>
        <!-- 文件消息 -->
        <div v-else-if="isFileMessage" class="file-content">
          <el-icon :size="20"><Document /></el-icon>
          <div class="file-info">
            <span class="file-name">{{ fileName }}</span>
            <a :href="fileUrl" target="_blank" download class="download-link">下载文件</a>
          </div>
        </div>
        <!-- 文本消息 -->
        <div v-else class="text">{{ msg.content }}</div>
        <div class="time">{{ formatMsgTime(msg.created_at) }}</div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Document } from '@element-plus/icons-vue'
import { formatMsgTime } from '@shared/utils/format'

const props = defineProps({
  msg: { type: Object, required: true },
  currentUserId: { type: [Number, String], required: true },
})

const isMine = computed(() => props.msg.sender_id === props.currentUserId)

const isImageMessage = computed(() => {
  return props.msg.msg_type === 'image' || (props.msg.content && props.msg.content.startsWith('[图片]'))
})

const isFileMessage = computed(() => {
  return props.msg.msg_type === 'file' || (props.msg.content && props.msg.content.startsWith('[文件]'))
})

const imageUrl = computed(() => {
  if (!props.msg.content) return ''
  const match = props.msg.content.match(/\[图片\]\s*(.+)/)
  return match ? match[1].trim() : props.msg.content
})

const fileUrl = computed(() => {
  if (!props.msg.content) return ''
  const lines = props.msg.content.split('\n')
  for (const line of lines) {
    if (line.startsWith('/uploads/') || line.includes('/uploads/')) {
      return line.trim()
    }
  }
  return ''
})

const fileName = computed(() => {
  if (!props.msg.content) return '文件'
  const match = props.msg.content.match(/\[文件\]\s*(.+)/)
  if (match) return match[1].split('\n')[0].trim()
  return '文件'
})
</script>

<style scoped>
.chat-msg { margin-bottom: 12px; }

.sys-msg {
  text-align: center;
  color: #94a3b8;
  font-size: 12px;
  padding: 8px;
}

.bubble { max-width: 70%; }
.bubble.mine { margin-left: auto; }
.bubble.other { margin-right: auto; }

.sender {
  font-size: 12px;
  color: #94a3b8;
  margin-bottom: 4px;
}
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

.time {
  font-size: 11px;
  color: #cbd5e1;
  margin-top: 4px;
}
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
</style>
