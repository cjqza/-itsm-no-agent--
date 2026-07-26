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
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span class="chart-title">最近评价</span>
              <el-select v-model="ratingFilter" size="small" style="width: 100px" @change="loadData" clearable placeholder="全部评分">
                <el-option :value="5" label="5星" />
                <el-option :value="4" label="4星" />
                <el-option :value="3" label="3星" />
                <el-option :value="2" label="2星" />
                <el-option :value="1" label="1星" />
              </el-select>
            </div>
          </template>
          <el-table :data="recentRatings" stripe class="analysis-table" empty-text="暂无评价数据">
            <el-table-column prop="ticket_no" label="工单号" width="130">
              <template #default="{ row }">
                <span class="ticket-no">{{ row.ticket_no }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="title" label="标题" min-width="100" show-overflow-tooltip />
            <el-table-column label="总体" width="60" align="center">
              <template #default="{ row }">
                <el-tag :type="row.rating_overall >= 4 ? 'success' : row.rating_overall >= 3 ? 'warning' : 'danger'" size="small" effect="light" round>
                  {{ row.rating_overall || '-' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="详情" width="180">
              <template #default="{ row }">
                <div style="font-size: 12px; color: #666; line-height: 1.5;">
                  态度:{{ row.rating_attitude || '-' }} 方法:{{ row.rating_solution || '-' }} 时间:{{ row.rating_time || '-' }}
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="comment" label="反馈" min-width="80" show-overflow-tooltip />
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
const ratingFilter = ref(null)  // 评分筛选
const slaData = ref([])
const recentRatings = ref([])

onMounted(() => loadData())

async function loadData() {
  const params = { days: days.value || undefined }
  if (ratingFilter.value) {
    params.min_rating = ratingFilter.value
    params.max_rating = ratingFilter.value
  }
  const [sla, rat] = await Promise.all([
    opsApi.getSlaCompliance(days.value),
    opsApi.getRatings(params),
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
