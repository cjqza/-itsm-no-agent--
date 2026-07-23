<template>
  <div class="account-requests">
    <el-card>
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center">
          <span>账号审批</span>
          <el-select v-model="statusFilter" clearable placeholder="状态筛选" style="width: 120px" @change="loadRequests">
            <el-option label="待审批" value="pending" />
            <el-option label="已激活" value="active" />
            <el-option label="已停用" value="inactive" />
          </el-select>
        </div>
      </template>
      <el-table :data="requests" stripe v-loading="loading">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="name" label="姓名" width="120" />
        <el-table-column prop="phone" label="电话" width="150" />
        <el-table-column prop="login_id" label="专属ID" width="120">
          <template #default="{ row }">{{ row.login_id || '-' }}</template>
        </el-table-column>
        <el-table-column prop="role" label="角色" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ row.role }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'pending' ? 'warning' : row.status === 'active' ? 'success' : 'info'" size="small">
              {{ statusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="申请时间" width="180" />
        <el-table-column label="操作" width="160" v-if="statusFilter === 'pending' || !statusFilter">
          <template #default="{ row }">
            <template v-if="row.status === 'pending'">
              <el-button type="success" size="small" @click="handleApprove(row)">批准</el-button>
              <el-button type="danger" size="small" @click="handleReject(row)">拒绝</el-button>
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
