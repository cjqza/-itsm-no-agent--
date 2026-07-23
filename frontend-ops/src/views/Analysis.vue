<template>
  <div class="ops-analysis">
    <h2>工单分析</h2>
    <el-select v-model="days" style="width: 120px; margin-bottom: 20px" @change="loadData">
      <el-option :value="7" label="最近7天" />
      <el-option :value="30" label="最近30天" />
      <el-option :value="90" label="最近90天" />
    </el-select>

    <el-row :gutter="20">
      <el-col :span="12">
        <el-card>
          <template #header><span>SLA达标率（按管理单元）</span></template>
          <el-table :data="slaData" stripe>
            <el-table-column prop="category" label="管理单元" />
            <el-table-column prop="total" label="总工单" width="80" />
            <el-table-column prop="met" label="达标" width="80" />
            <el-table-column prop="rate" label="达标率" width="100">
              <template #default="{ row }">
                <el-progress :percentage="row.rate" :color="row.rate >= 80 ? '#67c23a' : '#f56c6c'" />
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header><span>最近评价</span></template>
          <el-table :data="recentRatings" stripe>
            <el-table-column prop="ticket_no" label="工单号" width="140" />
            <el-table-column prop="title" label="标题" show-overflow-tooltip />
            <el-table-column prop="rating" label="评分" width="100">
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
h2 { margin-bottom: 16px; }
</style>
