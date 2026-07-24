<template>
  <div class="chat-input-area">
    <div class="input-row">
      <el-upload
        :show-file-list="false"
        :before-upload="handleFileSelect"
        accept="image/*,.pdf,.doc,.docx,.xls,.xlsx,.txt,.zip,.rar"
      >
        <el-button :icon="Paperclip" circle />
      </el-upload>
      <el-input
        v-model="inputText"
        :placeholder="placeholder"
        @keyup.enter="handleSend"
        :disabled="disabled"
      />
      <el-button
        type="primary"
        @click="handleSend"
        :loading="sending"
        :disabled="!inputText.trim()"
      >
        发送
      </el-button>
    </div>
    <div v-if="pendingFile" class="pending-file">
      <el-tag closable @close="pendingFile = null" size="small">
        <el-icon><Document /></el-icon> {{ pendingFile.name }}
      </el-tag>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Paperclip, Document } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

defineProps({
  placeholder: { type: String, default: '输入消息...' },
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['send', 'upload'])

const inputText = ref('')
const sending = ref(false)
const pendingFile = ref(null)

function handleFileSelect(file) {
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.warning('文件大小不能超过10MB')
    return false
  }
  pendingFile.value = file
  return false
}

async function handleSend() {
  const text = inputText.value.trim()
  if (!text && !pendingFile.value) return

  sending.value = true
  try {
    if (pendingFile.value) {
      emit('upload', pendingFile.value)
      pendingFile.value = null
    }
    if (text) {
      emit('send', text)
      inputText.value = ''
    }
  } finally {
    sending.value = false
  }
}

function clear() {
  inputText.value = ''
  pendingFile.value = null
}

defineExpose({ clear, sending })
</script>

<style scoped>
.chat-input-area {
  padding: 14px 20px;
  border-top: 1px solid #f0f0f0;
  background: #fafbfc;
}
.input-row {
  display: flex;
  gap: 8px;
  align-items: center;
}
.pending-file { margin-top: 8px; }
</style>
