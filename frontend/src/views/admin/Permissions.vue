<template>
  <div class="permissions">
    <el-tabs v-model="activeTab">
      <!-- 权限列表 -->
      <el-tab-pane label="用户权限" name="list">
        <el-card>
          <template #header><span>用户权限管理</span></template>
          <el-table :data="permissions" stripe v-loading="loading">
            <el-table-column prop="user_id" label="用户ID" width="80" />
            <el-table-column prop="user_name" label="用户名" width="120" />
            <el-table-column prop="user_role" label="角色" width="100">
              <template #default="{ row }">
                <el-tag :type="row.user_role === 'admin' ? 'danger' : row.user_role === 'agent' ? 'warning' : 'info'" size="small">
                  {{ roleText(row.user_role) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="ITSM权限" width="100">
              <template #default="{ row }">
                <el-switch v-model="row.itsm_access" :disabled="isAdminRole(row.user_role)" @change="updatePerm(row)" />
              </template>
            </el-table-column>
            <el-table-column label="OPS权限" width="100">
              <template #default="{ row }">
                <el-switch v-model="row.ops_access" :disabled="isAdminRole(row.user_role)" @change="updatePerm(row)" />
              </template>
            </el-table-column>
            <el-table-column label="后台管理权限" width="140">
              <template #default="{ row }">
                <el-tooltip
                  :disabled="!adminSwitchDisabled(row.user_role)"
                  content="后台权限只能由 admin 修改"
                  placement="top"
                >
                  <el-switch v-model="row.admin_access" :disabled="adminSwitchDisabled(row.user_role)" @change="updatePerm(row)" />
                </el-tooltip>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <!-- 权限申请 -->
      <el-tab-pane label="权限申请" name="requests">
        <el-card>
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center">
              <span>权限申请列表</span>
              <el-select v-model="reqStatusFilter" clearable placeholder="状态筛选" style="width: 120px" @change="loadRequests">
                <el-option label="待审批" value="pending" />
                <el-option label="已批准" value="approved" />
                <el-option label="已拒绝" value="rejected" />
              </el-select>
            </div>
          </template>
          <el-table :data="requests" stripe v-loading="loadingReq">
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="user_name" label="申请人" width="100" />
            <el-table-column prop="request_type" label="申请权限" width="120">
              <template #default="{ row }">
                <el-tag size="small">{{ typeText(row.request_type) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="reason" label="申请理由" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === 'pending' ? 'warning' : row.status === 'approved' ? 'success' : 'danger'" size="small">
                  {{ statusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="申请时间" width="160" />
            <el-table-column label="操作" width="160" v-if="reqStatusFilter !== 'approved' && reqStatusFilter !== 'rejected'">
              <template #default="{ row }">
                <template v-if="row.status === 'pending'">
                  <el-button type="success" size="small" @click="reviewReq(row.id, 'approved')">批准</el-button>
                  <el-button type="danger" size="small" @click="reviewReq(row.id, 'rejected')">拒绝</el-button>
                </template>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { adminApi } from '@/api'
import { useUserStore } from '@/store/user'

const userStore = useUserStore()

const activeTab = ref('list')
const permissions = ref([])
const requests = ref([])
const loading = ref(false)
const loadingReq = ref(false)
const reqStatusFilter = ref('pending')

onMounted(async () => {
  await Promise.all([loadPermissions(), loadRequests()])
})

async function loadPermissions() {
  loading.value = true
  try { permissions.value = await adminApi.getPermissions() || [] } finally { loading.value = false }
}

async function loadRequests() {
  loadingReq.value = true
  try { requests.value = await adminApi.getPermissionRequests(reqStatusFilter.value) || [] } finally { loadingReq.value = false }
}

async function updatePerm(row) {
  try {
    await adminApi.updatePermission(row.user_id, {
      itsm_access: row.itsm_access,
      ops_access: row.ops_access,
      admin_access: row.admin_access,
    })
    ElMessage.success('权限更新成功')
  } catch (e) { await loadPermissions() }
}

async function reviewReq(id, action) {
  try {
    await adminApi.reviewRequest(id, action)
    ElMessage.success(action === 'approved' ? '已批准' : '已拒绝')
    await loadRequests()
  } catch (e) { ElMessage.error('审批操作失败') }
}

function isAdminRole(role) { return role === 'admin' || role === 'super_admin' }
function adminSwitchDisabled(role) { return isAdminRole(role) || userStore.userRole !== 'super_admin' }
function roleText(r) { return { user: '普通用户', agent: '客服', admin: '管理员', super_admin: '超级管理员' }[r] || r }
function typeText(t) { return { itsm: 'ITSM系统', ops: 'OPS系统', admin: '后台管理' }[t] || t }
function statusText(s) { return { pending: '待审批', approved: '已批准', rejected: '已拒绝' }[s] || s }
</script>
