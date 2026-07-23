<template>
  <div class="ops-overview">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px">
      <h2>OPS总览</h2>
      <div>
        <el-select v-model="days" style="width: 120px; margin-right: 10px" @change="loadData">
          <el-option :value="7" label="最近7天" />
          <el-option :value="30" label="最近30天" />
          <el-option :value="90" label="最近90天" />
        </el-select>
        <el-button @click="handleExport">导出报表</el-button>
      </div>
    </div>

    <el-row :gutter="20" class="stat-cards">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value">{{ overview.total || 0 }}</div>
          <div class="stat-label">总工单数</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card pending">
          <div class="stat-value">{{ overview.status_counts?.pending || 0 }}</div>
          <div class="stat-label">待处理</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card rating">
          <div class="stat-value">{{ overview.avg_rating || 0 }}</div>
          <div class="stat-label">平均评分</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card sla">
          <div class="stat-value">{{ overview.sla_compliance_rate || 0 }}%</div>
          <div class="stat-label">SLA达标率</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="12">
        <el-card>
          <template #header><span>工单趋势</span></template>
          <div ref="trendChart" style="height: 300px"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header><span>状态分布</span></template>
          <div ref="statusChart" style="height: 300px"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="12">
        <el-card>
          <template #header><span>按管理单元统计</span></template>
          <div ref="categoryChart" style="height: 300px"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header><span>评分分布</span></template>
          <div ref="ratingChart" style="height: 300px"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { opsApi } from '@/api'

const days = ref(30)
const overview = ref({})
const trendChart = ref(null)
const statusChart = ref(null)
const categoryChart = ref(null)
const ratingChart = ref(null)

// 存储图表实例以便销毁
let trendInstance = null
let statusInstance = null
let categoryInstance = null
let ratingInstance = null

onMounted(async () => { await loadData() })

onUnmounted(() => {
  // 组件销毁时释放图表资源
  trendInstance?.dispose()
  statusInstance?.dispose()
  categoryInstance?.dispose()
  ratingInstance?.dispose()
})

async function loadData() {
  const [ov, trend, cat, rat] = await Promise.all([
    opsApi.getOverview(days.value),
    opsApi.getTrend(days.value),
    opsApi.getByCategory(days.value),
    opsApi.getRatings(days.value),
  ])
  overview.value = ov
  await nextTick()
  renderTrendChart(trend)
  renderStatusChart(ov.status_counts || {})
  renderCategoryChart(cat)
  renderRatingChart(rat.distribution || [])
}

function renderTrendChart(data) {
  if (!trendChart.value) return
  if (!trendInstance) trendInstance = echarts.init(trendChart.value)
  trendInstance.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: data.map(d => d.date) },
    yAxis: { type: 'value' },
    series: [{ data: data.map(d => d.count), type: 'line', smooth: true, areaStyle: { opacity: 0.3 } }],
  })
}

function renderStatusChart(data) {
  if (!statusChart.value) return
  const names = { pending: '待派发', assigned: '已派发', accepted: '已接单', analyzing: '分析中', processing: '处理中', resolved_pending_review: '待评价', resolved: '已解决' }
  if (!statusInstance) statusInstance = echarts.init(statusChart.value)
  statusInstance.setOption({
    tooltip: { trigger: 'item' },
    series: [{ type: 'pie', radius: '60%', data: Object.entries(data).map(([k, v]) => ({ name: names[k] || k, value: v })) }],
  })
}

function renderCategoryChart(data) {
  if (!categoryChart.value) return
  if (!categoryInstance) categoryInstance = echarts.init(categoryChart.value)
  categoryInstance.setOption({
    tooltip: {},
    xAxis: { type: 'category', data: data.map(d => d.name), axisLabel: { rotate: 30 } },
    yAxis: { type: 'value' },
    series: [{ data: data.map(d => d.count), type: 'bar' }],
  })
}

function renderRatingChart(data) {
  if (!ratingChart.value) return
  if (!ratingInstance) ratingInstance = echarts.init(ratingChart.value)
  ratingInstance.setOption({
    tooltip: {},
    xAxis: { type: 'category', data: data.map(d => `${d.rating}星`) },
    yAxis: { type: 'value' },
    series: [{ data: data.map(d => d.count), type: 'bar' }],
  })
}

async function handleExport() {
  try {
    const blob = await opsApi.exportTickets(days.value)
    const url = window.URL.createObjectURL(new Blob([blob]))
    const a = document.createElement('a')
    a.href = url
    a.download = `tickets_report_${days.value}days.xlsx`
    a.click()
  } catch (e) {}
}
</script>

<style scoped>
.stat-cards .stat-card { text-align: center; padding: 20px; }
.stat-value { font-size: 36px; font-weight: bold; color: #0f766e; }
.stat-card.pending .stat-value { color: #e6a23c; }
.stat-card.rating .stat-value { color: #67c23a; }
.stat-card.sla .stat-value { color: #f56c6c; }
.stat-label { font-size: 14px; color: #999; margin-top: 8px; }
</style>
