<template>
  <div class="account-requests">
    <el-card class="table-card">
      <template #header>
        <div class="card-header-bar">
          <span class="card-title">账号审批</span>
          <el-select v-model="statusFilter" clearable placeholder="状态筛选" style="width: 120px" size="small" @change="loadRequests">
            <el-option label="待审批" value="pending" />
            <el-option label="已激活" value="active" />
            <el-option label="已停用" value="inactive" />
          </el-select>
        </div>
      </template>
      <el-table :data="requests" stripe v-loading="loading" class="req-table" empty-text="暂无申请记录">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="name" label="姓名" width="120">
          <template #default="{ row }">
            <span class="user-name-cell">{{ row.name }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="phone" label="电话" width="150" />
        <el-table-column prop="login_id" label="专属ID" width="120">
          <template #default="{ row }">{{ row.login_id || '-' }}</template>
        </el-table-column>
        <el-table-column prop="role" label="角色" width="100">
          <template #default="{ row }">
            <el-tag size="small" effect="light">{{ row.role }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'pending' ? 'warning' : row.status === 'active' ? 'success' : 'info'" size="small" effect="light" round>
              {{ statusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="申请时间" width="180" />
        <el-table-column label="操作" width="160" v-if="statusFilter === 'pending' || !statusFilter">
          <template #default="{ row }">
            <template v-if="row.status === 'pending'">
              <el-button type="success" size="small" @click="handleApprove(row)" plain>批准</el-button>
              <el-button type="danger" size="small" @click="handleReject(row)" plain>拒绝</el-button>
            </template>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { adminApi } from '@/api'

const requests = ref([])
const loading = ref(false)
const statusFilter = ref('pending')

onMounted(() => { loadRequests() })

async function loadRequests() {
  loading.value = true
  try {
    requests.value = await adminApi.getAccountRequests(statusFilter.value || 'pending') || []
  } finally {
    loading.value = false
  }
}

async function handleApprove(row) {
  try {
    await ElMessageBox.confirm(`确定批准「${row.name}」的注册申请？`, '批准确认', { type: 'success', confirmButtonText: '批准' })
    const res = await adminApi.reviewAccountRequest(row.id, 'approve')
    ElMessage.success(`已批准，分配专属ID：${res.login_id}`)
    await loadRequests()
  } catch (e) { /* 用户取消 */ }
}

async function handleReject(row) {
  try {
    await ElMessageBox.confirm(`确定拒绝「${row.name}」的注册申请？`, '拒绝确认', { type: 'warning', confirmButtonText: '拒绝' })
    await adminApi.reviewAccountRequest(row.id, 'reject')
    ElMessage.success('已拒绝')
    await loadRequests()
  } catch (e) { /* 用户取消 */ }
}

function statusText(s) { return { pending: '待审批', active: '已激活', inactive: '已停用' }[s] || s }
</script>

<style scoped>
.table-card {
  border-radius: 12px;
  border: none;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}
.table-card :deep(.el-card__header) {
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
  background: #fafbfc;
  border-radius: 12px 12px 0 0;
}
.card-title { font-weight: 600; font-size: 14px; color: #1e293b; }
.card-header-bar { display: flex; justify-content: space-between; align-items: center; }

.user-name-cell { font-weight: 500; color: #1e293b; }

.req-table { border-radius: 8px; overflow: hidden; }
.req-table :deep(.el-table th.el-table__cell) {
  background: #f8fafc;
  font-weight: 600;
  color: #475569;
  font-size: 13px;
}
.req-table :deep(.el-table .el-table__row:hover > td) {
  background: #f8fafc !important;
}
</style>
