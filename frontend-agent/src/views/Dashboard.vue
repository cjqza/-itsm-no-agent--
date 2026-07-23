<template>
  <div class="dashboard">
    <el-skeleton :loading="loading" animated :rows="4">
      <template #template>
        <el-row :gutter="16">
          <el-col :span="12" v-for="i in 4" :key="i">
            <div style="padding: 20px; background: white; border-radius: 12px; margin-bottom: 16px;">
              <el-skeleton-item variant="h3" style="width: 50%; height: 24px; margin-bottom: 16px;" />
              <el-skeleton-item variant="text" style="width: 100%; height: 16px; margin-bottom: 12px;" v-for="j in 3" :key="j" />
            </div>
          </el-col>
        </el-row>
      </template>
      <template #default>
        <el-row :gutter="16">
          <!-- 左上：草稿箱工单（未接单） -->
          <el-col :span="12">
            <el-card class="panel">
              <template #header>
                <div class="panel-header">
                  <span>📋 草稿箱工单 <el-tag type="info" size="small">{{ draftTickets.length }}</el-tag></span>
                  <el-button type="primary" size="small" @click="router.push('/tickets')">查看全部</el-button>
                </div>
              </template>
              <div class="ticket-list">
                <div v-for="t in draftTickets" :key="t.id" class="ticket-item" @click="goToDetail(t)">
                  <div class="ticket-left">
                    <div class="sla-bar" :style="{ background: slaColor(t.sla_status) }"></div>
                  </div>
                  <div class="ticket-body">
                    <div class="ticket-title">{{ t.ticket_no }} - {{ t.title }}</div>
                    <div class="ticket-meta">
                      <span>{{ t.creator_name }}</span>
                      <span>{{ formatTime(t.created_at) }}</span>
                    </div>
                  </div>
                  <el-button type="primary" size="small" @click.stop="handleAccept(t)">接单</el-button>
                </div>
                <el-empty v-if="draftTickets.length === 0" description="暂无待接工单" />
              </div>
            </el-card>
          </el-col>

          <!-- 右上：待处理工单池（已受理未处理） -->
          <el-col :span="12">
            <el-card class="panel">
              <template #header>
                <div class="panel-header">
                  <span>📥 待处理工单池 <el-tag type="warning" size="small">{{ acceptedTickets.length }}</el-tag></span>
                </div>
              </template>
              <div class="ticket-list">
                <div v-for="t in acceptedTickets" :key="t.id" class="ticket-item" @click="goToDetail(t)">
                  <div class="ticket-left">
                    <div class="sla-bar" :style="{ background: slaColor(t.sla_status) }"></div>
                  </div>
                  <div class="ticket-body">
                    <div class="ticket-title">{{ t.ticket_no }} - {{ t.title }}</div>
                    <div class="ticket-meta">
                      <span>负责人: {{ t.assignee_name || '未分配' }}</span>
                      <span>{{ formatTime(t.created_at) }}</span>
                    </div>
                  </div>
                  <el-tag :type="statusTagType(t.status)" size="small">{{ statusText(t.status) }}</el-tag>
                </div>
                <el-empty v-if="acceptedTickets.length === 0" description="暂无待处理工单" />
              </div>
            </el-card>
          </el-col>
        </el-row>

        <el-row :gutter="16" style="margin-top:16px">
          <!-- 左下：我的待办工单（我处理中的） -->
          <el-col :span="12">
            <el-card class="panel">
              <template #header>
                <div class="panel-header">
                  <span>🔧 我的待办工单 <el-tag type="warning" size="small">{{ myProcessingTickets.length }}</el-tag></span>
                </div>
              </template>
              <div class="ticket-list">
                <div v-for="t in myProcessingTickets" :key="t.id" class="ticket-item" @click="goToDetail(t)">
                  <div class="ticket-left">
                    <div class="sla-bar" :style="{ background: slaColor(t.sla_status) }"></div>
                  </div>
                  <div class="ticket-body">
                    <div class="ticket-title">{{ t.ticket_no }} - {{ t.title }}</div>
                    <div class="sla-progress">
                      <el-progress :percentage="getSlaPercent(t)" :color="slaColor(t.sla_status)" :stroke-width="6" />
                    </div>
                  </div>
                  <el-tag :type="statusTagType(t.status)" size="small">{{ statusText(t.status) }}</el-tag>
                </div>
                <el-empty v-if="myProcessingTickets.length === 0" description="暂无待办工单" />
              </div>
            </el-card>
          </el-col>

          <!-- 右下：已解决待评价 / 未解决 -->
          <el-col :span="12">
            <el-card class="panel">
              <template #header>
                <div class="panel-header">
                  <span>✅ 已解决工单 <el-tag type="success" size="small">{{ resolvedTickets.length }}</el-tag></span>
                  <el-tabs v-model="resolvedTab" class="mini-tabs">
                    <el-tab-pane label="待评价" name="pending_review" />
                    <el-tab-pane label="已评价" name="resolved" />
                  </el-tabs>
                </div>
              </template>
              <div class="ticket-list">
                <div v-for="t in filteredResolved" :key="t.id" class="ticket-item" @click="goToDetail(t)">
                  <div class="ticket-body">
                    <div class="ticket-title">{{ t.ticket_no }} - {{ t.title }}</div>
                    <div class="ticket-meta">
                      <span>{{ t.creator_name }}</span>
                      <el-tag :type="statusTagType(t.status)" size="small">{{ statusText(t.status) }}</el-tag>
                    </div>
                  </div>
                </div>
                <el-empty v-if="filteredResolved.length === 0" description="暂无工单" />
              </div>
            </el-card>
          </el-col>
        </el-row>
      </template>
    </el-skeleton>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
import { ticketApi } from '@/api'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'

const router = useRouter()
const store = useUserStore()
const allTickets = ref([])
const resolvedTab = ref('pending_review')
const loading = ref(false)

onMounted(async () => {
  await loadData()
})

async function loadData() {
  loading.value = true
  try {
    const result = await ticketApi.list({ page_size: 100 })
    allTickets.value = result.items || []
  } catch (e) { ElMessage.error('加载工单列表失败') } finally { loading.value = false }
}

// 草稿箱：待接单（pending）
const draftTickets = computed(() => allTickets.value.filter(t => t.status === 'pending'))

// 待处理工单池：已受理（accepted）
const acceptedTickets = computed(() => allTickets.value.filter(t => t.status === 'accepted'))

// 我的待办：我处理中（processing，指派给我）
const myProcessingTickets = computed(() =>
  allTickets.value.filter(t => t.status === 'processing' && t.assignee_id === store.user.id)
)

// 已解决工单：待评价 + 已评价
const resolvedTickets = computed(() =>
  allTickets.value.filter(t => t.status === 'resolved_pending_review' || t.status === 'resolved')
)

const filteredResolved = computed(() => {
  if (resolvedTab.value === 'pending_review') return resolvedTickets.value.filter(t => t.status === 'resolved_pending_review')
  return resolvedTickets.value.filter(t => t.status === 'resolved')
})

async function handleAccept(ticket) {
  try {
    await ticketApi.accept(ticket.id)
    ElMessage.success('接单成功')
    await loadData()
  } catch (e) { ElMessage.error('接单失败') }
}

function goToDetail(t) { router.push(`/tickets/${t.id}`) }

function getSlaPercent(t) {
  if (!t.sla_deadline || !t.created_at) return 0
  const total = new Date(t.sla_deadline) - new Date(t.created_at)
  const elapsed = Date.now() - new Date(t.created_at)
  return Math.min(100, Math.round(elapsed / total * 100))
}

function slaColor(s) { return { green: '#67c23a', yellow: '#e6a23c', red: '#f56c6c', black: '#333' }[s] || '#999' }
function statusTagType(s) { return { pending: 'info', accepted: '', processing: 'warning', resolved_pending_review: 'success', resolved: 'success' }[s] || 'info' }
function statusText(s) { return { pending: '待接单', accepted: '已接单', processing: '处理中', resolved_pending_review: '待评价', resolved: '已解决' }[s] || s }
function formatTime(t) { return t ? dayjs(t).format('MM-DD HH:mm') : '' }
</script>

<style scoped>
.dashboard { }

.panel {
  height: 380px;
  border-radius: 12px;
  border: none;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.06);
  transition: box-shadow 0.2s;
}
.panel:hover { box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08); }

.panel :deep(.el-card__header) {
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
  background: #fafbfc;
  border-radius: 12px 12px 0 0;
}

.panel-header { display: flex; justify-content: space-between; align-items: center; font-weight: 600; font-size: 14px; }
.mini-tabs { margin-top: -8px; }
.mini-tabs :deep(.el-tabs__header) { margin: 0; }
.mini-tabs :deep(.el-tabs__item) { height: 32px; line-height: 32px; font-size: 12px; }

.ticket-list { max-height: 300px; overflow-y: auto; padding: 4px 0; }
.ticket-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  margin: 4px 8px;
  border-radius: 8px;
  border-bottom: none;
  cursor: pointer;
  transition: all 0.15s;
}
.ticket-item:hover {
  background: #f0f7ff;
  transform: translateX(2px);
}
.ticket-left { width: 4px; }
.sla-bar { width: 4px; height: 36px; border-radius: 2px; }
.ticket-body { flex: 1; min-width: 0; }
.ticket-title { font-size: 13px; color: #1e293b; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.ticket-meta { font-size: 12px; color: #94a3b8; display: flex; gap: 12px; margin-top: 4px; }
.sla-progress { width: 120px; margin-top: 4px; }
</style>
