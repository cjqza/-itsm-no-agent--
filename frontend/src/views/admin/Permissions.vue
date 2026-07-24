<template>
  <div class="permissions">
    <el-tabs v-model="activeTab" class="perm-tabs">
      <!-- 账号管理 -->
      <el-tab-pane label="账号管理" name="list">
        <el-card class="table-card">
          <template #header>
            <div class="card-header-bar">
              <span class="card-title">账号管理</span>
              <div class="search-bar">
                <el-select
                  v-model="roleFilter"
                  placeholder="角色筛选"
                  clearable
                  style="width: 140px"
                  size="small"
                  @change="handleRoleFilter"
                >
                  <el-option label="超级管理员" value="super_admin" />
                  <el-option label="管理员" value="admin" />
                  <el-option label="客服" value="agent" />
                  <el-option label="普通用户" value="user" />
                  <el-option label="已锁定" value="locked" />
                </el-select>
                <el-input
                  v-model="searchKeyword"
                  placeholder="搜索姓名、账号、手机号、邮箱"
                  clearable
                  style="width: 260px"
                  size="small"
                  @keyup.enter="handleSearch"
                  @clear="handleSearchClear"
                >
                  <template #prefix><el-icon><Search /></el-icon></template>
                </el-input>
                <el-button type="primary" size="small" @click="handleSearch">搜索</el-button>
                <el-button size="small" @click="handleReset">重置</el-button>
                <el-button type="success" size="small" @click="openAddDialog">新增客服</el-button>
                <el-button v-if="userStore.isSuperAdmin" type="warning" size="small" @click="openAdminDialog">新增管理员</el-button>
              </div>
            </div>
          </template>
          <el-table :data="users" stripe v-loading="loading" class="perm-table" empty-text="暂无用户数据">
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="login_id" label="账号" width="100" />
            <el-table-column prop="name" label="姓名" width="100">
              <template #default="{ row }">
                <span class="user-name-cell">{{ row.name }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="role" label="角色" width="110">
              <template #default="{ row }">
                <el-tag :type="row.role === 'admin' || row.role === 'super_admin' ? 'danger' : row.role === 'agent' ? 'warning' : 'info'" size="small" effect="light" round>
                  {{ roleText(row.role) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="phone" label="手机号" width="130" />
            <el-table-column prop="email" label="邮箱" min-width="150" show-overflow-tooltip />
            <el-table-column prop="department" label="部门" width="120" show-overflow-tooltip />
            <el-table-column prop="status" label="状态" width="100" align="center">
              <template #default="{ row }">
                <div>
                  <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small" effect="light" round>
                    {{ row.status === 'active' ? '正常' : '已禁用' }}
                  </el-tag>
                  <el-tag v-if="row.locked_until" type="warning" size="small" effect="light" round style="margin-top: 4px;">
                    已锁定
                  </el-tag>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200" align="center">
              <template #default="{ row }">
                <template v-if="row.role === 'agent'">
                  <el-button type="primary" size="small" link @click="openDetailDialog(row)">详情</el-button>
                  <el-button
                    :type="row.status === 'active' ? 'danger' : 'success'"
                    size="small"
                    link
                    @click="handleToggleStatus(row)"
                  >
                    {{ row.status === 'active' ? '禁用' : '启用' }}
                  </el-button>
                </template>
                <template v-else-if="row.role === 'admin' || row.role === 'super_admin'">
                  <el-button
                    v-if="userStore.isSuperAdmin"
                    type="primary"
                    size="small"
                    link
                    @click="openEditAdminDialog(row)"
                  >编辑</el-button>
                  <el-button
                    v-if="userStore.isSuperAdmin && row.role === 'admin' && row.id !== userStore.user.id"
                    :type="row.status === 'active' ? 'danger' : 'success'"
                    size="small"
                    link
                    @click="handleToggleAdminStatus(row)"
                  >
                    {{ row.status === 'active' ? '禁用' : '启用' }}
                  </el-button>
                  <span v-if="!userStore.isSuperAdmin" class="no-action">-</span>
                </template>
                <template v-else>
                  <span class="no-action">-</span>
                </template>
                <!-- 解锁按钮：所有角色的锁定用户都显示 -->
                <el-button
                  v-if="row.locked_until"
                  type="warning"
                  size="small"
                  link
                  @click="handleUnlock(row)"
                >解锁</el-button>
              </template>
            </el-table-column>
          </el-table>
          <!-- 分页 -->
          <div class="pagination-bar" v-if="total > pageSize">
            <el-pagination
              v-model:current-page="currentPage"
              :page-size="pageSize"
              :total="total"
              layout="total, prev, pager, next"
              small
              @current-change="handlePageChange"
            />
          </div>
        </el-card>
      </el-tab-pane>

      <!-- 权限申请（保留原样） -->
      <el-tab-pane label="权限申请" name="requests">
        <el-card class="table-card">
          <template #header>
            <div class="card-header-bar">
              <span class="card-title">权限申请列表</span>
              <el-select v-model="reqStatusFilter" clearable placeholder="状态筛选" style="width: 120px" size="small" @change="loadRequests">
                <el-option label="待审批" value="pending" />
                <el-option label="已批准" value="approved" />
                <el-option label="已拒绝" value="rejected" />
              </el-select>
            </div>
          </template>
          <el-table :data="requests" stripe v-loading="loadingReq" class="perm-table" empty-text="暂无申请记录">
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="user_name" label="申请人" width="100">
              <template #default="{ row }">
                <span class="user-name-cell">{{ row.user_name }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="request_type" label="申请权限" width="120">
              <template #default="{ row }">
                <el-tag size="small" effect="light">{{ typeText(row.request_type) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="reason" label="申请理由" min-width="150" show-overflow-tooltip />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === 'pending' ? 'warning' : row.status === 'approved' ? 'success' : 'danger'" size="small" effect="light" round>
                  {{ statusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="申请时间" width="160" />
            <el-table-column label="操作" width="160" v-if="reqStatusFilter !== 'approved' && reqStatusFilter !== 'rejected'">
              <template #default="{ row }">
                <template v-if="row.status === 'pending'">
                  <el-button type="success" size="small" @click="reviewReq(row.id, 'approved')" plain>批准</el-button>
                  <el-button type="danger" size="small" @click="reviewReq(row.id, 'rejected')" plain>拒绝</el-button>
                </template>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <!-- 客服详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="客服详情"
      width="480px"
      :close-on-click-modal="false"
    >
      <template v-if="detailUser">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="账号">{{ detailUser.login_id }}</el-descriptions-item>
          <el-descriptions-item label="姓名">{{ detailUser.name }}</el-descriptions-item>
          <el-descriptions-item label="手机号">{{ detailUser.phone }}</el-descriptions-item>
          <el-descriptions-item label="邮箱">{{ detailUser.email || '-' }}</el-descriptions-item>
          <el-descriptions-item label="部门">{{ detailUser.department || '-' }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="detailUser.status === 'active' ? 'success' : 'info'" size="small">
              {{ detailUser.status === 'active' ? '正常' : '已禁用' }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <div style="margin-top: 20px; padding-top: 16px; border-top: 1px solid #eee;">
          <div style="font-weight: bold; margin-bottom: 12px; color: #333;">权限管理</div>
          <div style="display: flex; flex-wrap: wrap; gap: 8px;">
            <el-button
              type="danger"
              size="small"
              @click="handleDowngrade(detailUser)"
            >取消客服</el-button>
            <el-button
              v-if="detailUser.itsm_access"
              type="warning"
              size="small"
              @click="handleRevokePermission(detailUser, 'itsm')"
            >取消 ITSM 权限</el-button>
            <el-button
              v-if="detailUser.ops_access"
              type="warning"
              size="small"
              @click="handleRevokePermission(detailUser, 'ops')"
            >取消 OPS 权限</el-button>
          </div>
        </div>
      </template>
      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 升级为客服对话框 -->
    <el-dialog
      v-model="dialogVisible"
      title="升级为客服"
      width="520px"
      :close-on-click-modal="false"
      @closed="resetForm"
    >
      <div style="margin-bottom: 16px;">
        <el-input
          v-model="upgradeSearch"
          placeholder="搜索用户姓名、账号、手机号"
          clearable
          @input="searchUsersForUpgrade"
        >
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
      </div>
      <el-table
        :data="upgradeUsers"
        max-height="300"
        highlight-current-row
        @current-change="handleUpgradeUserSelect"
        style="width: 100%"
        v-loading="upgradeLoading"
      >
        <el-table-column prop="login_id" label="账号" width="100" />
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column prop="phone" label="手机号" width="130" />
        <el-table-column prop="role" label="角色" width="80">
          <template #default="{ row }">
            <el-tag size="small">{{ roleText(row.role) }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
      <div v-if="selectedUpgradeUser" style="margin-top: 12px; padding: 8px; background: #f0f9ff; border-radius: 4px;">
        已选择：<strong>{{ selectedUpgradeUser.name }}</strong>（{{ selectedUpgradeUser.login_id }}）
      </div>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="submitting"
          :disabled="!selectedUpgradeUser"
          @click="handleUpgrade"
        >升级为客服</el-button>
      </template>
    </el-dialog>

    <!-- 新增管理员对话框 -->
    <el-dialog
      v-model="adminDialogVisible"
      title="新增管理员"
      width="480px"
      :close-on-click-modal="false"
      @closed="resetAdminForm"
    >
      <el-form
        ref="adminFormRef"
        :model="adminForm"
        :rules="adminFormRules"
        label-width="80px"
        label-position="right"
      >
        <el-form-item label="姓名" prop="name">
          <el-input v-model="adminForm.name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="adminForm.phone" placeholder="请输入手机号" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="adminForm.password" type="password" show-password placeholder="请输入密码" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="adminForm.email" placeholder="请输入邮箱（可选）" />
        </el-form-item>
        <el-form-item label="部门">
          <el-input v-model="adminForm.department" placeholder="请输入部门（可选）" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="adminForm.role" placeholder="请选择角色" style="width: 100%">
            <el-option label="管理员" value="admin" />
            <el-option label="超级管理员" value="super_admin" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="adminDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleAdminSubmit">创建</el-button>
      </template>
    </el-dialog>

    <!-- 编辑管理员对话框 -->
    <el-dialog
      v-model="editAdminDialogVisible"
      title="编辑管理员"
      width="480px"
      :close-on-click-modal="false"
      @closed="resetEditAdminForm"
    >
      <el-form
        ref="editAdminFormRef"
        :model="editAdminForm"
        :rules="editAdminFormRules"
        label-width="80px"
        label-position="right"
      >
        <el-form-item label="姓名" prop="name">
          <el-input v-model="editAdminForm.name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="editAdminForm.phone" placeholder="请输入手机号" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="editAdminForm.email" placeholder="请输入邮箱（可选）" />
        </el-form-item>
        <el-form-item label="部门">
          <el-input v-model="editAdminForm.department" placeholder="请输入部门（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editAdminDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleEditAdminSubmit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { adminApi } from '@/api'
import { useUserStore } from '@/store/user'

const userStore = useUserStore()
const isSuperAdmin = userStore.isSuperAdmin

// ===== 账号管理 =====
const activeTab = ref('list')
const users = ref([])
const loading = ref(false)
const searchKeyword = ref('')
const roleFilter = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

// ===== 权限申请 =====
const requests = ref([])
const loadingReq = ref(false)
const reqStatusFilter = ref('pending')

// ===== 对话框 =====
const dialogVisible = ref(false)
const detailDialogVisible = ref(false)
const detailUser = ref(null)
const submitting = ref(false)
const formRef = ref(null)
const editingUserId = ref(null)

const agentForm = reactive({
  name: '',
  phone: '',
  password: '',
  email: '',
  department: '',
})

const formRules = {
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  phone: [{ required: true, message: '请输入手机号', trigger: 'blur' }],
}

// ===== 升级为客服 =====
const upgradeUsers = ref([])
const upgradeLoading = ref(false)
const upgradeSearch = ref('')
const selectedUpgradeUser = ref(null)

async function searchUsersForUpgrade() {
  upgradeLoading.value = true
  try {
    const params = { role: 'user', page_size: 50 }
    if (upgradeSearch.value.trim()) {
      params.keyword = upgradeSearch.value.trim()
    }
    const res = await adminApi.getUsers(params)
    upgradeUsers.value = res?.items || []
  } finally {
    upgradeLoading.value = false
  }
}

function handleUpgradeUserSelect(row) {
  selectedUpgradeUser.value = row
}

async function handleUpgrade() {
  if (!selectedUpgradeUser.value) {
    ElMessage.warning('请选择要升级的用户')
    return
  }
  submitting.value = true
  try {
    await adminApi.upgradeToAgent(selectedUpgradeUser.value.id)
    ElMessage.success(`已将 ${selectedUpgradeUser.value.name} 升级为客服`)
    dialogVisible.value = false
    await loadUsers()
  } catch (e) {
    // error handled by interceptor
  } finally {
    submitting.value = false
  }
}

async function handleDowngrade(row) {
  try {
    await ElMessageBox.confirm(
      `确定要取消「${row.name}」的客服权限吗？取消后将变为普通用户。`,
      '操作确认',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    await adminApi.downgradeToUser(row.id)
    ElMessage.success(`已取消 ${row.name} 的客服权限`)
    detailDialogVisible.value = false
    await loadUsers()
  } catch (e) {
    if (e !== 'cancel') {
      // error handled by interceptor
    }
  }
}

// ===== 新增管理员 =====
const adminDialogVisible = ref(false)
const adminFormRef = ref(null)
const adminForm = reactive({
  name: '',
  phone: '',
  password: '',
  email: '',
  department: '',
  role: 'admin',
})
const adminFormRules = {
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  phone: [{ required: true, message: '请输入手机号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
}

// ===== 编辑管理员 =====
const editAdminDialogVisible = ref(false)
const editAdminFormRef = ref(null)
const editingAdminId = ref(null)
const editAdminForm = reactive({
  name: '',
  phone: '',
  email: '',
  department: '',
})
const editAdminFormRules = {
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  phone: [{ required: true, message: '请输入手机号', trigger: 'blur' }],
}

onMounted(async () => {
  await Promise.all([loadUsers(), loadRequests()])
})

// ===== 账号管理方法 =====

async function loadUsers() {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value,
    }
    if (searchKeyword.value.trim()) {
      params.keyword = searchKeyword.value.trim()
    }
    if (roleFilter.value === 'locked') {
      params.locked = true
    } else if (roleFilter.value) {
      params.role = roleFilter.value
    }
    const res = await adminApi.getUsers(params)
    users.value = res?.items || []
    total.value = res?.total || 0
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  // 搜索时清除角色筛选，以便搜索到所有匹配用户（包括普通用户）
  roleFilter.value = ''
  currentPage.value = 1
  loadUsers()
}

function handleSearchClear() {
  searchKeyword.value = ''
  currentPage.value = 1
  loadUsers()
}

function handleRoleFilter() {
  searchKeyword.value = ''
  currentPage.value = 1
  loadUsers()
}

function handleReset() {
  searchKeyword.value = ''
  roleFilter.value = ''
  currentPage.value = 1
  loadUsers()
}

function handlePageChange(page) {
  currentPage.value = page
  loadUsers()
}

function openAddDialog() {
  isEditMode.value = false
  editingUserId.value = null
  resetFormData()
  upgradeSearch.value = ''
  selectedUpgradeUser.value = null
  upgradeUsers.value = []
  dialogVisible.value = true
  searchUsersForUpgrade()
}

function openDetailDialog(row) {
  detailUser.value = row
  detailDialogVisible.value = true
}

async function handleRevokePermission(row, permType) {
  const permName = permType === 'itsm' ? 'ITSM' : 'OPS'
  try {
    await ElMessageBox.confirm(
      `确定要取消「${row.name}」的 ${permName} 权限吗？`,
      '操作确认',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    const params = {}
    params[`${permType}_access`] = false
    await adminApi.updatePermission(row.id, params)
    ElMessage.success(`已取消 ${row.name} 的 ${permName} 权限`)
    await loadUsers()
    // 更新详情用户数据
    const updated = users.value.find(u => u.id === row.id)
    if (updated) detailUser.value = updated
  } catch (e) {
    if (e !== 'cancel') {
      // error handled by interceptor
    }
  }
}

function resetFormData() {
  agentForm.name = ''
  agentForm.phone = ''
  agentForm.password = ''
  agentForm.email = ''
  agentForm.department = ''
}

function resetForm() {
  formRef.value?.resetFields()
  resetFormData()
  editingUserId.value = null
}

async function handleSubmit() {
  if (formRef.value) {
    try {
      await formRef.value.validate()
    } catch {
      return
    }
  }

  submitting.value = true
  try {
    if (isEditMode.value) {
      const payload = {
        name: agentForm.name,
        phone: agentForm.phone,
        email: agentForm.email || null,
        department: agentForm.department || null,
      }
      await adminApi.updateAgent(editingUserId.value, payload)
      ElMessage.success('客服信息更新成功')
    } else {
      await adminApi.createAgent({
        name: agentForm.name,
        phone: agentForm.phone,
        password: agentForm.password,
        email: agentForm.email || null,
        department: agentForm.department || null,
      })
      ElMessage.success('客服创建成功')
    }
    dialogVisible.value = false
    await loadUsers()
  } catch (e) {
    // error already handled by interceptor
  } finally {
    submitting.value = false
  }
}

async function handleToggleStatus(row) {
  const isActive = row.status === 'active'
  const action = isActive ? '禁用' : '启用'
  try {
    await ElMessageBox.confirm(
      `确定要${action}客服「${row.name}」吗？`,
      '操作确认',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    if (isActive) {
      await adminApi.deleteAgent(row.id)
    } else {
      // 重新启用：通过 updateAgent 将 status 改回 active
      // 但后端 updateAgent 不处理 status，所以直接用已有的 status 接口
      await adminApi.updateUserStatus(row.id, { status: 'active' })
    }
    ElMessage.success(`已${action}`)
    await loadUsers()
  } catch (e) {
    if (e !== 'cancel') {
      // error already handled by interceptor
    }
  }
}

async function handleUnlock(row) {
  try {
    await ElMessageBox.confirm(
      `确定要解锁账号「${row.name}」吗？`,
      '操作确认',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    await adminApi.unlockUser(row.id)
    ElMessage.success('账号已解锁')
    await loadUsers()
  } catch (e) {
    if (e !== 'cancel') {
      // error already handled by interceptor
    }
  }
}

// ===== 管理员操作方法 =====

function openAdminDialog() {
  adminForm.name = ''
  adminForm.phone = ''
  adminForm.password = ''
  adminForm.email = ''
  adminForm.department = ''
  adminForm.role = 'admin'
  adminDialogVisible.value = true
}

function resetAdminForm() {
  adminFormRef.value?.resetFields()
  adminForm.name = ''
  adminForm.phone = ''
  adminForm.password = ''
  adminForm.email = ''
  adminForm.department = ''
  adminForm.role = 'admin'
}

async function handleAdminSubmit() {
  if (adminFormRef.value) {
    try {
      await adminFormRef.value.validate()
    } catch {
      return
    }
  }
  submitting.value = true
  try {
    await adminApi.createAdmin({
      name: adminForm.name,
      phone: adminForm.phone,
      password: adminForm.password,
      email: adminForm.email || null,
      department: adminForm.department || null,
      role: adminForm.role,
    })
    ElMessage.success('管理员创建成功')
    adminDialogVisible.value = false
    await loadUsers()
  } catch (e) {
    // error already handled by interceptor
  } finally {
    submitting.value = false
  }
}

function openEditAdminDialog(row) {
  editingAdminId.value = row.id
  editAdminForm.name = row.name || ''
  editAdminForm.phone = row.phone || ''
  editAdminForm.email = row.email || ''
  editAdminForm.department = row.department || ''
  editAdminDialogVisible.value = true
}

function resetEditAdminForm() {
  editAdminFormRef.value?.resetFields()
  editAdminForm.name = ''
  editAdminForm.phone = ''
  editAdminForm.email = ''
  editAdminForm.department = ''
  editingAdminId.value = null
}

async function handleEditAdminSubmit() {
  if (editAdminFormRef.value) {
    try {
      await editAdminFormRef.value.validate()
    } catch {
      return
    }
  }
  submitting.value = true
  try {
    const payload = {
      name: editAdminForm.name,
      phone: editAdminForm.phone,
      email: editAdminForm.email || null,
      department: editAdminForm.department || null,
    }
    await adminApi.updateUser(editingAdminId.value, payload)
    ElMessage.success('管理员信息更新成功')
    editAdminDialogVisible.value = false
    await loadUsers()
  } catch (e) {
    // error already handled by interceptor
  } finally {
    submitting.value = false
  }
}

async function handleToggleAdminStatus(row) {
  const isActive = row.status === 'active'
  const action = isActive ? '禁用' : '启用'
  try {
    await ElMessageBox.confirm(
      `确定要${action}管理员「${row.name}」吗？`,
      '操作确认',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    await adminApi.updateUserStatus(row.id, { status: isActive ? 'inactive' : 'active' })
    ElMessage.success(`已${action}`)
    await loadUsers()
  } catch (e) {
    if (e !== 'cancel') {
      // error already handled by interceptor
    }
  }
}

// ===== 权限申请方法（保留原样） =====

async function loadRequests() {
  loadingReq.value = true
  try { requests.value = await adminApi.getPermissionRequests(reqStatusFilter.value) || [] } finally { loadingReq.value = false }
}

async function reviewReq(id, action) {
  try {
    await adminApi.reviewRequest(id, action)
    ElMessage.success(action === 'approved' ? '已批准' : '已拒绝')
    await loadRequests()
  } catch (e) { ElMessage.error('审批操作失败') }
}

// ===== 工具函数 =====

function roleText(r) { return { user: '普通用户', agent: '客服', admin: '管理员', super_admin: '超级管理员' }[r] || r }
function typeText(t) { return { itsm: 'ITSM系统', ops: 'OPS系统', admin: '后台管理' }[t] || t }
function statusText(s) { return { pending: '待审批', approved: '已批准', rejected: '已拒绝' }[s] || s }
</script>

<style scoped>
.permissions { }

.perm-tabs :deep(.el-tabs__item) {
  font-size: 14px;
  font-weight: 500;
}

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
.card-header-bar { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; }
.search-bar { display: flex; align-items: center; gap: 8px; }

.user-name-cell { font-weight: 500; color: #1e293b; }
.no-action { color: #c0c4cc; }

/* 表格样式 */
.perm-table { border-radius: 8px; overflow: hidden; }
.perm-table :deep(.el-table th.el-table__cell) {
  background: #f8fafc;
  font-weight: 600;
  color: #475569;
  font-size: 13px;
}
.perm-table :deep(.el-table .el-table__row:hover > td) {
  background: #f8fafc !important;
}

.pagination-bar {
  display: flex;
  justify-content: flex-end;
  padding: 16px 0 4px;
}
</style>
