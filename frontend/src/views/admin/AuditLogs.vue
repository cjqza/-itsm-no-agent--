<template>
  <div class="audit-logs">
    <el-card class="table-card">
      <template #header>
        <div class="card-header-bar">
          <span class="card-title">操作日志</span>
          <div class="search-bar">
            <el-select
              v-model="actionFilter"
              placeholder="操作类型"
              clearable
              style="width: 140px"
              size="small"
              @change="handleFilter"
            >
              <el-option label="创建" value="create" />
              <el-option label="更新" value="update" />
              <el-option label="删除" value="delete" />
              <el-option label="审批通过" value="approve" />
              <el-option label="审批拒绝" value="reject" />
            </el-select>
            <el-select
              v-model="targetTypeFilter"
              placeholder="目标类型"
              clearable
              style="width: 140px"
              size="small"
              @change="handleFilter"
            >
              <el-option label="用户" value="user" />
              <el-option label="权限" value="permission" />
              <el-option label="客服" value="agent" />
              <el-option label="管理员" value="admin" />
              <el-option label="分类" value="category" />
              <el-option label="模板" value="template" />
            </el-select>
            <el-button size="small" @click="handleReset">重置</el-button>
          </div>
        </div>
      </template>
      <el-table :data="logs" stripe v-loading="loading" class="logs-table" empty-text="暂无操作日志">
        <el-table-column prop="operator_name" label="操作人" width="120" />
        <el-table-column prop="action" label="操作类型" width="110">
          <template #default="{ row }">
            <el-tag :type="actionTagType(row.action)" size="small" effect="light" round>
              {{ actionText(row.action) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="target_type" label="目标类型" width="100">
          <template #default="{ row }">
            <span>{{ targetTypeText(row.target_type) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="target_id" label="目标ID" width="80" />
        <el-table-column prop="detail" label="详情" min-width="200" show-overflow-tooltip />
        <el-table-column prop="created_at" label="时间" width="170">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-bar">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadLogs"
          @current-change="loadLogs"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { adminApi } from '@/api'
import { ElMessage } from 'element-plus'
import { formatTime } from '@shared/utils/format'

const logs = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const actionFilter = ref('')
const targetTypeFilter = ref('')

onMounted(() => { loadLogs() })

async function loadLogs() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (actionFilter.value) params.action = actionFilter.value
    if (targetTypeFilter.value) params.target_type = targetTypeFilter.value
    const res = await adminApi.getAuditLogs(params)
    logs.value = res.items || []
    total.value = res.total || 0
  } catch (e) {
    ElMessage.error('加载操作日志失败')
  } finally {
    loading.value = false
  }
}

function handleFilter() {
  page.value = 1
  loadLogs()
}

function handleReset() {
  actionFilter.value = ''
  targetTypeFilter.value = ''
  page.value = 1
  loadLogs()
}

function actionTagType(action) {
  return { create: 'success', update: '', delete: 'danger', approve: 'success', reject: 'warning' }[action] || 'info'
}

function actionText(action) {
  return { create: '创建', update: '更新', delete: '删除', approve: '审批通过', reject: '审批拒绝' }[action] || action
}

function targetTypeText(type) {
  return { user: '用户', permission: '权限', agent: '客服', admin: '管理员', category: '分类', template: '模板' }[type] || type
}

</script>

<style scoped>
.audit-logs { }

.table-card {
  border-radius: 12px;
  border: none;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.card-header-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
}

.search-bar {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.pagination-bar {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
  padding: 8px 0;
}
</style>
