<template>
  <div class="my-tickets">
    <h2>我的工单</h2>
    <el-table :data="tickets" stripe v-loading="loading" @row-click="goToChat">
      <el-table-column prop="ticket_no" label="工单号" width="140" />
      <el-table-column prop="title" label="问题描述" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ statusText(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="assignee_name" label="处理人" width="100">
        <template #default="{ row }">{{ row.assignee_name || '待分配' }}</template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="160">
        <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="100">
        <template #default="{ row }">
          <el-button type="primary" link @click.stop="goToChat(row)">
            {{ row.status === 'resolved_pending_review' ? '去评价' : '查看' }}
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
import { ticketApi } from '@/api'
import dayjs from 'dayjs'

const router = useRouter()
const store = useUserStore()
const tickets = ref([])
const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    const data = await ticketApi.list({ creator_id: store.user.id })
    tickets.value = data.items || []
  } finally { loading.value = false }
})

function goToChat(row) { router.push(`/chat/${row.id}`) }
function statusType(s) {
  return { pending: 'info', accepted: '', processing: 'warning', resolved_pending_review: 'success', resolved: 'success' }[s] || 'info'
}
function statusText(s) {
  return { pending: '待接单', accepted: '已接单', processing: '处理中', resolved_pending_review: '待评价', resolved: '已解决' }[s] || s
}
function formatTime(t) { return t ? dayjs(t).format('YYYY-MM-DD HH:mm') : '' }
</script>

<style scoped>
.my-tickets { background: white; border-radius: 12px; padding: 24px; }
h2 { margin-bottom: 20px; color: #1a365d; }
</style>
