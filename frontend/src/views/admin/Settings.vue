<template>
  <div class="admin-settings">
    <h2>系统设置</h2>

    <el-card class="settings-card" style="margin-bottom: 16px">
      <template #header><span class="card-title">客服管理</span></template>
      <el-table :data="agents" stripe v-loading="loading" class="settings-table" empty-text="暂无客服数据">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="name" label="姓名" width="120">
          <template #default="{ row }">
            <span class="user-name-cell">{{ row.name }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="email" label="邮箱" />
        <el-table-column prop="is_online" label="在线状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_online ? 'success' : 'info'" size="small" effect="light" round>
              {{ row.is_online ? '在线' : '离线' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="账号状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'danger'" size="small" effect="light" round>
              {{ row.status === 'active' ? '正常' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card class="settings-card">
      <template #header><span class="card-title">SLA 配置说明</span></template>
      <el-descriptions :column="1" border class="sla-desc">
        <el-descriptions-item label="接单超时">5分钟未接单，工单颜色变为黑色</el-descriptions-item>
        <el-descriptions-item label="SLA预警">超过SLA时间50%变红色警告</el-descriptions-item>
        <el-descriptions-item label="OLA暂停">用户未回复时可暂停OLA计时</el-descriptions-item>
        <el-descriptions-item label="默认SLA">4小时（可在管理单元中自定义）</el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { adminApi } from '@/api'

const agents = ref([])
const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try { agents.value = await adminApi.getAgents() || [] } finally { loading.value = false }
})
</script>

<style scoped>
h2 { margin-bottom: 16px; font-size: 18px; font-weight: 700; color: #1e293b; }

.settings-card {
  border-radius: 12px;
  border: none;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}
.settings-card :deep(.el-card__header) {
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
  background: #fafbfc;
  border-radius: 12px 12px 0 0;
}
.card-title { font-weight: 600; font-size: 14px; color: #1e293b; }

.user-name-cell { font-weight: 500; color: #1e293b; }

.settings-table { border-radius: 8px; overflow: hidden; }
.settings-table :deep(.el-table th.el-table__cell) {
  background: #f8fafc;
  font-weight: 600;
  color: #475569;
  font-size: 13px;
}
.settings-table :deep(.el-table .el-table__row:hover > td) {
  background: #f8fafc !important;
}

.sla-desc :deep(.el-descriptions__label) {
  font-weight: 600;
  color: #475569;
}
</style>
