<template>
  <div class="my-tickets">
    <div class="page-header">
      <h2>我的工单</h2>
      <el-button type="primary" :icon="Refresh" @click="loadTickets" :loading="loading" size="small">刷新</el-button>
    </div>
    <el-skeleton :loading="loading" animated :rows="5">
      <template #template>
        <div style="padding: 12px 0;">
          <el-skeleton-item variant="text" style="width: 100%; height: 40px; margin-bottom: 8px;" v-for="i in 5" :key="i" />
        </div>
      </template>
      <template #default>
        <el-table :data="tickets" stripe @row-click="goToChat" class="tickets-table" empty-text="暂无工单，去首页提交一个吧">
          <el-table-column prop="ticket_no" label="工单号" width="140">
            <template #default="{ row }">
              <span class="ticket-no">{{ row.ticket_no }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="title" label="问题描述" min-width="200" show-overflow-tooltip />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="statusType(row.status)" size="small" effect="light" round>{{ statusText(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="assignee_name" label="处理人" width="100">
            <template #default="{ row }">
              <span :class="{'text-muted': !row.assignee_name}">{{ row.assignee_name || '待分配' }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="160">
            <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="100" fixed="right">
            <template #default="{ row }">
              <el-button
                :type="row.status === 'resolved_pending_review' ? 'warning' : 'primary'"
                link
                @click.stop="goToChat(row)"
              >
                {{ row.status === 'resolved_pending_review' ? '去评价' : '查看' }}
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </template>
    </el-skeleton>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
import { ticketApi } from '@/api'
import { Refresh } from '@element-plus/icons-vue'
import { statusType, statusText } from '@shared/utils/status'
import { formatTime } from '@shared/utils/format'

const router = useRouter()
const store = useUserStore()
const tickets = ref([])
const loading = ref(false)

onMounted(() => loadTickets())

async function loadTickets() {
  loading.value = true
  try {
    const data = await ticketApi.list({ creator_id: store.user.id })
    tickets.value = data.items || []
  } finally { loading.value = false }
}

function goToChat(row) { router.push({ path: '/chat-rooms', query: { ticket_id: row.id } }) }
</script>

<style scoped>
.my-tickets {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
h2 { color: #1e293b; font-size: 18px; font-weight: 700; margin: 0; }

.ticket-no { color: #2563eb; font-weight: 600; font-size: 13px; }
.text-muted { color: #94a3b8; }

/* 表格样式 */
.tickets-table { border-radius: 8px; overflow: hidden; }
.tickets-table :deep(.el-table th.el-table__cell) {
  background: #f8fafc;
  font-weight: 600;
  color: #475569;
  font-size: 13px;
}
.tickets-table :deep(.el-table .el-table__row) {
  cursor: pointer;
  transition: background 0.15s;
}
.tickets-table :deep(.el-table .el-table__row:hover > td) {
  background: #f0f7ff !important;
}
</style>
