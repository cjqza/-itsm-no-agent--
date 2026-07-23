<template>
  <div class="ops-performance">
    <div class="page-header">
      <h2>客服绩效</h2>
      <el-select v-model="days" style="width: 120px" @change="loadData">
        <el-option :value="7" label="最近7天" />
        <el-option :value="30" label="最近30天" />
        <el-option :value="90" label="最近90天" />
      </el-select>
    </div>

    <el-card class="perf-card">
      <el-table :data="agentData" stripe class="perf-table" empty-text="暂无绩效数据">
        <el-table-column prop="name" label="客服姓名" width="120">
          <template #default="{ row }">
            <div class="agent-name">
              <div class="agent-avatar">{{ row.name?.[0] || 'A' }}</div>
              <span>{{ row.name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="total" label="总工单" width="100" align="center" />
        <el-table-column prop="resolved" label="已解决" width="100" align="center" />
        <el-table-column label="解决率" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="row.total > 0 && (row.resolved / row.total) >= 0.8 ? 'success' : 'warning'" size="small" effect="light" round>
              {{ row.total > 0 ? Math.round(row.resolved / row.total * 100) : 0 }}%
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="avg_rating" label="平均评分" width="150">
          <template #default="{ row }">
            <div class="rating-cell">
              <el-rate :model-value="row.avg_rating" disabled size="small" />
              <span class="rating-num">{{ row.avg_rating }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="工单量分布" min-width="200">
          <template #default="{ row }">
            <el-progress
              :percentage="Math.min(100, Math.round((row.total / maxTotal) * 100))"
              :stroke-width="14"
              :color="getProgressColor(row.total / maxTotal)"
            />
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { opsApi } from '@/api'

const days = ref(30)
const agentData = ref([])
const maxTotal = computed(() => Math.max(...agentData.value.map(a => a.total), 1))

onMounted(() => loadData())

async function loadData() {
  agentData.value = await opsApi.getByAgent(days.value) || []
}

function getProgressColor(ratio) {
  if (ratio >= 0.8) return '#22c55e'
  if (ratio >= 0.5) return '#14b8a6'
  return '#3b82f6'
}
</script>

<style scoped>
.ops-performance { }

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
h2 { font-size: 18px; font-weight: 700; color: #1e293b; margin: 0; }

.perf-card {
  border-radius: 12px;
  border: none;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.agent-name {
  display: flex;
  align-items: center;
  gap: 8px;
}
.agent-avatar {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  background: linear-gradient(135deg, #14b8a6, #0f766e);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
}

.rating-cell {
  display: flex;
  align-items: center;
  gap: 6px;
}
.rating-num {
  font-size: 13px;
  font-weight: 600;
  color: #1e293b;
}

.perf-table { border-radius: 8px; overflow: hidden; }
.perf-table :deep(.el-table th.el-table__cell) {
  background: #f8fafc;
  font-weight: 600;
  color: #475569;
  font-size: 13px;
}
.perf-table :deep(.el-table .el-table__row:hover > td) {
  background: #f0fdf4 !important;
}
</style>
