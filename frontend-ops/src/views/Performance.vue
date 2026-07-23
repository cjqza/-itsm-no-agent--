<template>
  <div class="ops-performance">
    <h2>客服绩效</h2>
    <el-select v-model="days" style="width: 120px; margin-bottom: 20px" @change="loadData">
      <el-option :value="7" label="最近7天" />
      <el-option :value="30" label="最近30天" />
      <el-option :value="90" label="最近90天" />
    </el-select>

    <el-card>
      <el-table :data="agentData" stripe>
        <el-table-column prop="name" label="客服姓名" width="120" />
        <el-table-column prop="total" label="总工单" width="100" />
        <el-table-column prop="resolved" label="已解决" width="100" />
        <el-table-column label="解决率" width="120">
          <template #default="{ row }">
            {{ row.total > 0 ? Math.round(row.resolved / row.total * 100) : 0 }}%
          </template>
        </el-table-column>
        <el-table-column prop="avg_rating" label="平均评分" width="120">
          <template #default="{ row }">
            <el-rate :model-value="row.avg_rating" disabled size="small" />
            <span style="margin-left: 4px">{{ row.avg_rating }}</span>
          </template>
        </el-table-column>
        <el-table-column label="工单量">
          <template #default="{ row }">
            <el-progress :percentage="Math.min(100, (row.total / maxTotal) * 100)" :stroke-width="16" />
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
</script>

<style scoped>
h2 { margin-bottom: 16px; }
</style>
