<template>
  <div class="ticket-list-page">
    <el-card>
      <template #header>
        <div class="toolbar">
          <div class="left">
            <el-button type="primary" @click="loadTickets">刷新</el-button>
          </div>
          <div class="right">
            <el-input v-model="keyword" placeholder="搜索工单号/标题" style="width:200px" @keyup.enter="loadTickets" clearable>
              <template #append><el-button @click="loadTickets"><el-icon><Search /></el-icon></el-button></template>
            </el-input>
            <el-select v-model="filters.status" clearable placeholder="状态" style="width:120px" @change="loadTickets">
              <el-option label="待接单" value="pending" />
              <el-option label="已接单" value="accepted" />
              <el-option label="处理中" value="processing" />
              <el-option label="待评价" value="resolved_pending_review" />
              <el-option label="已解决" value="resolved" />
            </el-select>
          </div>
        </div>
      </template>

      <el-table :data="tickets" stripe v-loading="loading" @row-click="goToDetail">
        <el-table-column width="50">
          <template #default="{ row }">
            <div class="sla-indicator" :style="{ background: slaColor(row.sla_status) }"></div>
          </template>
        </el-table-column>
        <el-table-column prop="ticket_no" label="工单号" width="130">
          <template #default="{ row }">
            <span class="ticket-no">{{ row.ticket_no }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
        <el-table-column prop="category_name" label="业务系统" width="100">
          <template #default="{ row }">{{ row.category_name || '-' }}</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" size="small">{{ statusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="creator_name" label="提交人" width="80" />
        <el-table-column prop="assignee_name" label="处理人" width="80">
          <template #default="{ row }">{{ row.assignee_name || '-' }}</template>
        </el-table-column>
        <el-table-column label="闭环" width="60">
          <template #default="{ row }">
            <el-tag :type="row.status === 'resolved' ? 'success' : 'danger'" size="small" effect="dark">
              {{ row.status === 'resolved' ? '已闭环' : '待处理' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="提交时间" width="140">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        style="margin-top:16px; justify-content:flex-end"
        @current-change="loadTickets"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ticketApi } from '@/api'
import dayjs from 'dayjs'

const router = useRouter()
const tickets = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const keyword = ref('')
const filters = reactive({ status: '' })

onMounted(() => loadTickets())

async function loadTickets() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (filters.status) params.status = filters.status
    if (keyword.value) params.keyword = keyword.value
    const data = await ticketApi.list(params)
    tickets.value = data.items || []
    total.value = data.total || 0
  } finally { loading.value = false }
}

function goToDetail(row) { router.push(`/tickets/${row.id}`) }

function slaColor(s) { return { green: '#67c23a', yellow: '#e6a23c', red: '#f56c6c', black: '#333' }[s] || '#999' }
function statusTagType(s) { return { pending: 'info', accepted: '', processing: 'warning', resolved_pending_review: 'success', resolved: 'success' }[s] || 'info' }
function statusText(s) { return { pending: '待接单', accepted: '已接单', processing: '处理中', resolved_pending_review: '待评价', resolved: '已解决' }[s] || s }
function formatTime(t) { return t ? dayjs(t).format('YYYY-MM-DD HH:mm') : '' }
</script>

<style scoped>
.toolbar { display: flex; justify-content: space-between; align-items: center; }
.right { display: flex; gap: 8px; }
.sla-indicator { width: 4px; height: 24px; border-radius: 2px; }
.ticket-no { color: #2563eb; font-weight: bold; }
</style>
