<template>
  <div class="ops-analysis">
    <div class="page-header">
      <h2>工单分析</h2>
      <el-select v-model="days" style="width: 120px" @change="loadData">
        <el-option :value="7" label="最近7天" />
        <el-option :value="30" label="最近30天" />
        <el-option :value="90" label="最近90天" />
      </el-select>
    </div>

    <el-row :gutter="16">
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header><span class="chart-title">SLA达标率（按管理单元）</span></template>
          <el-table :data="slaData" stripe class="analysis-table" empty-text="暂无数据">
            <el-table-column prop="category" label="管理单元" />
            <el-table-column prop="total" label="总工单" width="80" align="center" />
            <el-table-column prop="met" label="达标" width="80" align="center" />
            <el-table-column prop="rate" label="达标率" width="120">
              <template #default="{ row }">
                <el-progress :percentage="row.rate" :color="row.rate >= 80 ? '#22c55e' : '#ef4444'" :stroke-width="8" />
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header><span class="chart-title">最近评价</span></template>
          <el-table :data="recentRatings" stripe class="analysis-table" empty-text="暂无评价数据">
            <el-table-column prop="ticket_no" label="工单号" width="140">
              <template #default="{ row }">
                <span class="ticket-no">{{ row.ticket_no }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="title" label="标题" show-overflow-tooltip />
            <el-table-column prop="rating" label="评分" width="110" align="center">
              <template #default="{ row }">
                <el-rate :model-value="row.rating" disabled size="small" />
              </template>
            </el-table-column>
            <el-table-column prop="comment" label="评价" show-overflow-tooltip />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { opsApi } from '@/api'

const days = ref(30)
const slaData = ref([])
const recentRatings = ref([])

onMounted(() => loadData())

async function loadData() {
  const [sla, rat] = await Promise.all([
    opsApi.getSlaCompliance(days.value),
    opsApi.getRatings(days.value),
  ])
  slaData.value = sla || []
  recentRatings.value = rat?.recent || []
}
</script>

<style scoped>
.ops-analysis { }

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
h2 { font-size: 18px; font-weight: 700; color: #1e293b; margin: 0; }

.chart-card {
  border-radius: 12px;
  border: none;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}
.chart-card :deep(.el-card__header) {
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
  background: #fafbfc;
  border-radius: 12px 12px 0 0;
}
.chart-title { font-weight: 600; font-size: 14px; color: #1e293b; }

.ticket-no { color: #0f766e; font-weight: 600; font-size: 13px; }

.analysis-table { border-radius: 8px; overflow: hidden; }
.analysis-table :deep(.el-table th.el-table__cell) {
  background: #f8fafc;
  font-weight: 600;
  color: #475569;
  font-size: 13px;
}
.analysis-table :deep(.el-table .el-table__row:hover > td) {
  background: #f0fdf4 !important;
}
</style>
