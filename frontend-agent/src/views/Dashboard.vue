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

          <!-- 右上：待处理工单池（分 Tab） -->
          <el-col :span="12">
            <el-card class="panel">
              <template #header>
                <div class="panel-header">
                  <span>📥 待处理工单池</span>
                  <el-tabs v-model="acceptedTab" class="mini-tabs">
                    <el-tab-pane :label="`我的 (${myAcceptedTickets.length})`" name="mine" />
                    <el-tab-pane :label="`全部 (${otherAcceptedTickets.length})`" name="all" />
                  </el-tabs>
                </div>
              </template>
              <div class="ticket-list">
                <template v-if="acceptedTab === 'mine'">
                  <div v-for="t in myAcceptedTickets" :key="t.id" class="ticket-item" @click="goToDetail(t)">
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
                    <el-tag :type="statusTagType(t.status)" size="small">{{ statusText(t.status) }}</el-tag>
                  </div>
                  <el-empty v-if="myAcceptedTickets.length === 0" description="暂无我的待处理工单" />
                </template>
                <template v-else>
                  <div v-for="t in otherAcceptedTickets" :key="t.id" class="ticket-item" @click="goToDetail(t)">
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
                  <el-empty v-if="otherAcceptedTickets.length === 0" description="暂无其他人的待处理工单" />
                </template>
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
                    <div class="sla-bar" :style="{ background: slaColorByPercent(getSlaPercent(t)) }"></div>
                  </div>
                  <div class="ticket-body">
                    <div class="ticket-title">{{ t.ticket_no }} - {{ t.title }}</div>
                    <div class="sla-progress">
                      <el-progress :percentage="Math.min(100, getSlaPercent(t))" :color="slaColorByPercent(getSlaPercent(t))" :stroke-width="6" />
                      <span class="sla-text" :style="{ color: slaColorByPercent(getSlaPercent(t)) }">
                        {{ getSlaStatusText(getSlaPercent(t)) }}
                      </span>
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
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
import { ticketApi } from '@/api'
import { ElMessage } from 'element-plus'
import { slaColor, statusTagType, statusText, slaColorByPercent } from '@shared/utils/status'
import { formatShortTime as formatTime } from '@shared/utils/format'

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
const acceptedTab = ref('mine')
const myAcceptedTickets = computed(() =>
  allTickets.value.filter(t => t.status === 'accepted' && t.assignee_id === store.user?.id)
)
const otherAcceptedTickets = computed(() =>
  allTickets.value.filter(t => t.status === 'accepted' && t.assignee_id !== store.user?.id)
)

// 我的待办：我处理中（processing，指派给我）
const myProcessingTickets = computed(() =>
  allTickets.value.filter(t => t.status === 'processing' && t.assignee_id === store.user?.id)
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

// 实时时间戳（每分钟刷新）
const now = ref(Date.now())
let nowTimer = null

onMounted(() => {
  nowTimer = setInterval(() => { now.value = Date.now() }, 60000)
})
onUnmounted(() => { if (nowTimer) clearInterval(nowTimer) })

// 监听全局WebSocket通知，自动刷新数据
let unsubWs = null
onMounted(() => {
  unsubWs = store.onWsMessage((msg) => {
    if (msg.type === 'new_ticket' || msg.type === 'ticket_update') {
      loadData()
    }
  })
})
onUnmounted(() => { if (unsubWs) unsubWs() })

// 将后端UTC时间戳转为Date对象（无时区后缀视为UTC）
function utcDate(t) {
  if (!t) return new Date()
  return new Date(typeof t === 'string' && !t.endsWith('Z') && !/[+-]\d{2}:\d{2}$/.test(t) ? t + 'Z' : t)
}

function getSlaPercent(t) {
  if (!t.sla_deadline || !t.created_at) return 0
  // SLA暂停时，用暂停前的进度
  if (t.is_sla_paused && t.sla_paused_at) {
    const total = utcDate(t.sla_deadline) - utcDate(t.created_at)
    const pausedElapsed = utcDate(t.sla_paused_at) - utcDate(t.created_at)
    const pausedSeconds = t.sla_paused_seconds || 0
    return Math.min(100, Math.round((pausedElapsed - pausedSeconds * 1000) / total * 100))
  }
  const total = utcDate(t.sla_deadline) - utcDate(t.created_at)
  const elapsed = now.value - utcDate(t.created_at)
  const pausedSeconds = t.sla_paused_seconds || 0
  return Math.min(200, Math.round((elapsed - pausedSeconds * 1000) / total * 100))
}


function getSlaStatusText(percent) {
  if (percent >= 100) return '已超时'
  if (percent >= 80) return '即将超时'
  if (percent >= 50) return '注意'
  return '正常'
}

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
.sla-progress { width: 120px; margin-top: 4px; display: flex; flex-direction: column; gap: 2px; }
.sla-text { font-size: 11px; font-weight: 500; }

@media (max-width: 768px) {
  .dashboard :deep(.el-col-12) {
    flex: 0 0 100%;
    max-width: 100%;
  }
  .panel { height: auto; max-height: 400px; }
}

@media (max-width: 480px) {
  .panel-header { flex-direction: column; align-items: flex-start; gap: 8px; }
  .ticket-item { padding: 10px 12px; }
  .sla-progress { width: 80px; }
}
</style>
