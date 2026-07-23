<template>
  <div class="ops-overview">
    <div class="page-header">
      <h2>OPS 总览</h2>
      <div class="header-actions">
        <el-select v-model="days" style="width: 120px" @change="loadData" size="default">
          <el-option :value="7" label="最近7天" />
          <el-option :value="30" label="最近30天" />
          <el-option :value="90" label="最近90天" />
        </el-select>
        <el-button type="primary" plain @click="handleExport">
          <el-icon><Download /></el-icon> 导出报表
        </el-button>
      </div>
    </div>

    <el-skeleton :loading="loading" animated :rows="4">
      <template #template>
        <el-row :gutter="16" class="stat-cards">
          <el-col :span="6" v-for="i in 4" :key="i">
            <div class="stat-card" style="padding: 24px 20px;">
              <el-skeleton-item variant="circle" style="width: 36px; height: 36px; flex-shrink: 0;" />
              <div style="flex: 1;">
                <el-skeleton-item variant="h3" style="width: 60%; height: 32px; margin-bottom: 6px;" />
                <el-skeleton-item variant="text" style="width: 40%; height: 13px;" />
              </div>
            </div>
          </el-col>
        </el-row>
        <el-row :gutter="16" style="margin-top: 16px;">
          <el-col :span="12" v-for="i in 2" :key="i">
            <div style="background: white; border-radius: 12px; padding: 16px 20px;">
              <el-skeleton-item variant="text" style="width: 30%; height: 20px; margin-bottom: 16px;" />
              <el-skeleton-item variant="rect" style="width: 100%; height: 300px; border-radius: 8px;" />
            </div>
          </el-col>
        </el-row>
        <el-row :gutter="16" style="margin-top: 16px;">
          <el-col :span="12" v-for="i in 2" :key="i">
            <div style="background: white; border-radius: 12px; padding: 16px 20px;">
              <el-skeleton-item variant="text" style="width: 30%; height: 20px; margin-bottom: 16px;" />
              <el-skeleton-item variant="rect" style="width: 100%; height: 300px; border-radius: 8px;" />
            </div>
          </el-col>
        </el-row>
      </template>
      <template #default>
        <el-row :gutter="16" class="stat-cards">
          <el-col :span="6">
            <div class="stat-card stat-total">
              <div class="stat-icon">📋</div>
              <div class="stat-content">
                <div class="stat-value">{{ overview.total || 0 }}</div>
                <div class="stat-label">总工单数</div>
              </div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-card stat-pending">
              <div class="stat-icon">⏳</div>
              <div class="stat-content">
                <div class="stat-value">{{ overview.status_counts?.pending || 0 }}</div>
                <div class="stat-label">待处理</div>
              </div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-card stat-rating">
              <div class="stat-icon">⭐</div>
              <div class="stat-content">
                <div class="stat-value">{{ overview.avg_rating || 0 }}</div>
                <div class="stat-label">平均评分</div>
              </div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-card stat-sla">
              <div class="stat-icon">🎯</div>
              <div class="stat-content">
                <div class="stat-value">{{ overview.sla_compliance_rate || 0 }}<span class="stat-unit">%</span></div>
                <div class="stat-label">SLA达标率</div>
              </div>
            </div>
          </el-col>
        </el-row>

        <el-row :gutter="16" style="margin-top: 16px">
          <el-col :span="12">
            <el-card class="chart-card">
              <template #header><span class="chart-title">工单趋势</span></template>
              <div ref="trendChart" style="height: 300px"></div>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card class="chart-card">
              <template #header><span class="chart-title">状态分布</span></template>
              <div ref="statusChart" style="height: 300px"></div>
            </el-card>
          </el-col>
        </el-row>

        <el-row :gutter="16" style="margin-top: 16px">
          <el-col :span="12">
            <el-card class="chart-card">
              <template #header><span class="chart-title">按管理单元统计</span></template>
              <div ref="categoryChart" style="height: 300px"></div>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card class="chart-card">
              <template #header><span class="chart-title">评分分布</span></template>
              <div ref="ratingChart" style="height: 300px"></div>
            </el-card>
          </el-col>
        </el-row>
      </template>
    </el-skeleton>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { opsApi } from '@/api'
import { ElMessage } from 'element-plus'
import { Download } from '@element-plus/icons-vue'

const days = ref(30)
const overview = ref({})
const loading = ref(false)
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
  loading.value = true
  try {
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
  } catch (e) {
    ElMessage.error('加载统计数据失败')
  } finally { loading.value = false }
}

function renderTrendChart(data) {
  if (!trendChart.value) return
  if (!trendInstance) trendInstance = echarts.init(trendChart.value)
  trendInstance.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: data.map(d => d.date), axisLine: { lineStyle: { color: '#e5e7eb' } }, axisLabel: { color: '#6b7280' } },
    yAxis: { type: 'value', axisLine: { show: false }, splitLine: { lineStyle: { color: '#f3f4f6' } }, axisLabel: { color: '#6b7280' } },
    series: [{
      data: data.map(d => d.count),
      type: 'line',
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      lineStyle: { width: 3, color: '#14b8a6' },
      itemStyle: { color: '#14b8a6' },
      areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(20, 184, 166, 0.25)' }, { offset: 1, color: 'rgba(20, 184, 166, 0.02)' }]) },
    }],
  })
}

function renderStatusChart(data) {
  if (!statusChart.value) return
  const names = { pending: '待派发', assigned: '已派发', accepted: '已接单', analyzing: '分析中', processing: '处理中', resolved_pending_review: '待评价', resolved: '已解决' }
  const colors = ['#f59e0b', '#8b5cf6', '#3b82f6', '#06b6d4', '#14b8a6', '#22c55e', '#10b981']
  if (!statusInstance) statusInstance = echarts.init(statusChart.value)
  statusInstance.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { orient: 'vertical', right: '5%', top: 'center', textStyle: { color: '#6b7280' } },
    color: colors,
    series: [{
      type: 'pie',
      radius: ['45%', '70%'],
      center: ['40%', '50%'],
      avoidLabelOverlap: false,
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
      label: { show: false },
      emphasis: { label: { show: true, fontSize: 14, fontWeight: 'bold' } },
      data: Object.entries(data).map(([k, v]) => ({ name: names[k] || k, value: v })),
    }],
  })
}

function renderCategoryChart(data) {
  if (!categoryChart.value) return
  if (!categoryInstance) categoryInstance = echarts.init(categoryChart.value)
  categoryInstance.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: '3%', right: '4%', bottom: '10%', containLabel: true },
    xAxis: { type: 'category', data: data.map(d => d.name), axisLabel: { rotate: 30, color: '#6b7280' }, axisLine: { lineStyle: { color: '#e5e7eb' } } },
    yAxis: { type: 'value', axisLine: { show: false }, splitLine: { lineStyle: { color: '#f3f4f6' } }, axisLabel: { color: '#6b7280' } },
    series: [{
      data: data.map(d => d.count),
      type: 'bar',
      barWidth: '50%',
      itemStyle: {
        borderRadius: [4, 4, 0, 0],
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: '#14b8a6' }, { offset: 1, color: '#0d9488' }]),
      },
    }],
  })
}

function renderRatingChart(data) {
  if (!ratingChart.value) return
  if (!ratingInstance) ratingInstance = echarts.init(ratingChart.value)
  const starColors = ['#ef4444', '#f97316', '#eab308', '#84cc16', '#22c55e']
  ratingInstance.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: data.map(d => `${d.rating} 星`), axisLabel: { color: '#6b7280' }, axisLine: { lineStyle: { color: '#e5e7eb' } } },
    yAxis: { type: 'value', axisLine: { show: false }, splitLine: { lineStyle: { color: '#f3f4f6' } }, axisLabel: { color: '#6b7280' } },
    series: [{
      data: data.map((d, i) => ({ value: d.count, itemStyle: { color: starColors[i] || '#6b7280', borderRadius: [4, 4, 0, 0] } })),
      type: 'bar',
      barWidth: '50%',
    }],
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
    ElMessage.success('导出成功')
  } catch (e) {
    ElMessage.error('导出失败：' + (e.response?.data?.detail || e.message || '未知错误'))
  }
}
</script>

<style scoped>
.ops-overview { }

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.page-header h2 {
  font-size: 20px;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
}
.header-actions { display: flex; gap: 10px; align-items: center; }

/* 统计卡片 */
.stat-cards { }
.stat-cards .stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 24px 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  transition: all 0.2s;
  border-left: 4px solid transparent;
}
.stat-cards .stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.stat-icon { font-size: 36px; flex-shrink: 0; }
.stat-content { flex: 1; }
.stat-value {
  font-size: 32px;
  font-weight: 800;
  line-height: 1;
  letter-spacing: -0.5px;
}
.stat-unit { font-size: 20px; font-weight: 600; margin-left: 2px; }
.stat-label { font-size: 13px; color: #64748b; margin-top: 6px; }

/* 各卡片主题色 */
.stat-total { border-left-color: #3b82f6; }
.stat-total .stat-value { color: #1e40af; }

.stat-pending { border-left-color: #f59e0b; }
.stat-pending .stat-value { color: #d97706; }

.stat-rating { border-left-color: #22c55e; }
.stat-rating .stat-value { color: #16a34a; }

.stat-sla { border-left-color: #14b8a6; }
.stat-sla .stat-value { color: #0f766e; }

/* 图表卡片 */
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
</style>
