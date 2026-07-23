<template>
  <div class="admin-settings">
    <h2>系统设置</h2>

    <el-card style="margin-bottom: 20px">
      <template #header><span>客服管理</span></template>
      <el-table :data="agents" stripe v-loading="loading">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="name" label="姓名" width="120" />
        <el-table-column prop="email" label="邮箱" />
        <el-table-column prop="is_online" label="在线状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_online ? 'success' : 'info'" size="small">
              {{ row.is_online ? '在线' : '离线' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="账号状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'danger'" size="small">
              {{ row.status === 'active' ? '正常' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card>
      <template #header><span>SLA配置说明</span></template>
      <el-descriptions :column="1" border>
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
h2 { margin-bottom: 16px; }
</style>
