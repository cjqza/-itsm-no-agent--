<template>
  <div class="ticket-history">
    <h2>历史工单查询</h2>

    <el-card>
      <template #header>
        <div class="toolbar">
          <div class="filters">
            <el-input v-model="keyword" placeholder="搜索工单号/标题" style="width: 200px" @keyup.enter="loadTickets" clearable>
              <template #append><el-button @click="loadTickets"><el-icon><Search /></el-icon></el-button></template>
            </el-input>
            <el-select v-model="filters.status" clearable placeholder="状态" style="width: 120px" @change="loadTickets">
              <el-option label="待接单" value="pending" />
              <el-option label="已接单" value="accepted" />
              <el-option label="处理中" value="processing" />
              <el-option label="待评价" value="resolved_pending_review" />
              <el-option label="已解决" value="resolved" />
            </el-select>
            <el-select v-model="filters.category_id" clearable placeholder="管理单元" style="width: 140px" @change="loadTickets">
              <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
            </el-select>
          </div>
          <el-button @click="handleExport">导出报表</el-button>
        </div>
      </template>

      <el-table :data="tickets" stripe v-loading="loading" @row-click="goToDetail">
        <el-table-column prop="ticket_no" label="工单号" width="140" />
        <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">{{ statusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="priority" label="优先级" width="70">
          <template #default="{ row }">
            <el-tag :type="priorityType(row.priority)" size="small">{{ row.priority }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="category_name" label="管理单元" width="120">
          <template #default="{ row }">{{ row.category_name || '-' }}</template>
        </el-table-column>
        <el-table-column prop="creator_name" label="提单人" width="80" />
        <el-table-column prop="assignee_name" label="负责人" width="80">
          <template #default="{ row }">{{ row.assignee_name || '-' }}</template>
        </el-table-column>
        <el-table-column prop="rating" label="评分" width="100">
          <template #default="{ row }">
            <el-rate v-if="row.rating" :model-value="row.rating" disabled size="small" />
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="sla_status" label="SLA" width="70">
          <template #default="{ row }">
            <el-tag :color="slaColor(row.sla_status)" style="color: white; border: none" size="small">
              {{ row.sla_status?.toUpperCase() }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        style="margin-top: 16px; justify-content: flex-end"
        @current-change="loadTickets"
      />
    </el-card>

    <!-- 工单详情对话框 -->
    <el-dialog v-model="showDetail" title="工单详情" width="700px">
      <el-descriptions :column="2" border v-if="currentTicket">
        <el-descriptions-item label="工单号">{{ currentTicket.ticket_no }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="statusType(currentTicket.status)">{{ statusText(currentTicket.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="标题" :span="2">{{ currentTicket.title }}</el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">{{ currentTicket.description || '无' }}</el-descriptions-item>
        <el-descriptions-item label="提单人">{{ currentTicket.creator_name }}</el-descriptions-item>
        <el-descriptions-item label="负责人">{{ currentTicket.assignee_name || '未分配' }}</el-descriptions-item>
        <el-descriptions-item label="管理单元">{{ currentTicket.category_name || '未分类' }}</el-descriptions-item>
        <el-descriptions-item label="优先级">{{ currentTicket.priority }}</el-descriptions-item>
        <el-descriptions-item label="评分" :span="2">
          <el-rate v-if="currentTicket.rating" :model-value="currentTicket.rating" disabled />
          <span v-else>未评价</span>
          <span v-if="currentTicket.rating_comment" style="margin-left: 8px; color: #999">{{ currentTicket.rating_comment }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatTime(currentTicket.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="解决时间">{{ formatTime(currentTicket.resolved_at) }}</el-descriptions-item>
      </el-descriptions>

      <el-divider />
      <h4>操作日志</h4>
      <el-timeline style="margin-top: 12px">
        <el-timeline-item v-for="log in logs" :key="log.id" :timestamp="formatTime(log.created_at)" placement="top">
          <span style="font-weight: bold">{{ log.operator_name || '系统' }}</span>
          <span style="color: #999; margin-left: 8px">{{ log.content || log.action }}</span>
        </el-timeline-item>
      </el-timeline>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ticketApi, opsApi } from '@/api'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'

const tickets = ref([])
const categories = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const keyword = ref('')
const filters = reactive({ status: '', category_id: '' })

const showDetail = ref(false)
const currentTicket = ref(null)
const logs = ref([])

onMounted(() => { loadTickets(); loadCategories() })

async function loadTickets() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (filters.status) params.status = filters.status
    if (filters.category_id) params.category_id = filters.category_id
    if (keyword.value) params.keyword = keyword.value
    const data = await ticketApi.list(params)
    tickets.value = data.items || []
    total.value = data.total || 0
  } finally { loading.value = false }
}

async function loadCategories() {
  try {
    const data = await import('@/api').then(m => m.default.get('/admin/categories/'))
    categories.value = data || []
  } catch (e) {}
}

async function goToDetail(row) {
  currentTicket.value = row
  showDetail.value = true
  try { logs.value = await ticketApi.logs(row.id) || [] } catch (e) { logs.value = [] }
}

async function handleExport() {
  try {
    const params = {}
    if (filters.status) params.status = filters.status
    if (filters.category_id) params.category_id = filters.category_id
    if (keyword.value) params.keyword = keyword.value
    const blob = await opsApi.exportTickets(params)
    const url = window.URL.createObjectURL(new Blob([blob]))
    const a = document.createElement('a')
    a.href = url
    a.download = 'tickets_report.xlsx'
    a.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (e) {
    ElMessage.error('导出失败：' + (e.response?.data?.detail || e.message || '未知错误'))
  }
}

function formatTime(t) { return t ? dayjs(t).format('YYYY-MM-DD HH:mm') : '' }
function statusType(s) { return { pending: 'info', accepted: '', processing: 'warning', resolved_pending_review: 'success', resolved: 'success' }[s] || 'info' }
function statusText(s) { return { pending: '待接单', accepted: '已接单', processing: '处理中', resolved_pending_review: '待评价', resolved: '已解决' }[s] || s }
function priorityType(p) { return { P1: 'danger', P2: 'warning', P3: '', P4: 'info' }[p] || '' }
function slaColor(s) { return { green: '#67c23a', yellow: '#e6a23c', red: '#f56c6c', black: '#333' }[s] || '#999' }
</script>

<style scoped>
h2 { margin-bottom: 16px; }
.toolbar { display: flex; justify-content: space-between; align-items: center; }
.filters { display: flex; gap: 8px; }
</style>
