<template>
  <div v-if="isMobile && !sidebarCollapsed" class="sidebar-overlay" @click="sidebarCollapsed = true"></div>
  <el-container class="layout">
    <!-- 深色侧边栏 -->
    <el-aside :width="sidebarWidth" class="sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="sidebar-header">
        <div class="logo-wrapper">
          <div class="logo-icon">🖥️</div>
        </div>
        <div class="title">ITSM</div>
        <div class="subtitle">服务工单管理</div>
      </div>
      <el-menu
        :default-active="activeMenu"
        router
        background-color="transparent"
        text-color="rgba(255,255,255,0.65)"
        active-text-color="#ffffff"
      >
        <el-menu-item index="/">
          <el-icon><HomeFilled /></el-icon>
          <span>工作台</span>
        </el-menu-item>
        <el-menu-item index="/tickets">
          <el-icon><Tickets /></el-icon>
          <span>服务请求</span>
        </el-menu-item>
        <el-menu-item index="/chat">
          <el-icon><ChatDotRound /></el-icon>
          <span>消息</span>
        </el-menu-item>
      </el-menu>
      <div class="sidebar-footer">
        <div class="user-info">
          <div class="user-avatar">{{ store.userName?.[0] || 'U' }}</div>
          <div class="user-detail">
            <div class="user-name">{{ store.userName }}</div>
            <div class="user-role">客服人员</div>
          </div>
        </div>
        <el-button text class="logout-btn" @click="handleLogout">
          <el-icon><SwitchButton /></el-icon>
        </el-button>
      </div>
    </el-aside>

    <!-- 主内容区 -->
    <el-container>
      <el-header class="header">
        <div class="header-left">
          <el-button text class="menu-toggle" @click="sidebarCollapsed = !sidebarCollapsed">
            <el-icon :size="20"><Fold v-if="!sidebarCollapsed" /><Expand v-else /></el-icon>
          </el-button>
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/' }">工作台</el-breadcrumb-item>
            <el-breadcrumb-item v-if="route.name === 'TicketList'">服务请求</el-breadcrumb-item>
            <el-breadcrumb-item v-if="route.name === 'TicketDetail'">工单详情</el-breadcrumb-item>
            <el-breadcrumb-item v-if="route.name === 'AgentChat'">消息</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <el-badge :value="pendingCount" :hidden="pendingCount === 0" class="badge" type="danger">
            <el-button text size="small">
              <el-icon><Bell /></el-icon> 待处理
            </el-button>
          </el-badge>
          <el-button text size="small" @click="toggleTheme" :title="isDark ? '切换亮色' : '切换暗色'">
            <el-icon :size="18"><Sunny v-if="isDark" /><Moon v-else /></el-icon>
          </el-button>
        </div>
      </el-header>
      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
import { ticketApi } from '@/api'
import { ChatDotRound, HomeFilled, Tickets, SwitchButton, Bell, Fold, Expand, Sunny, Moon } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const store = useUserStore()
const pendingCount = ref(0)
const sidebarCollapsed = ref(false)
const isMobile = ref(false)
const isDark = ref(localStorage.getItem('theme') === 'dark')

function toggleTheme() {
  isDark.value = !isDark.value
  document.documentElement.classList.toggle('dark', isDark.value)
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
}
const sidebarWidth = computed(() => {
  if (isMobile.value) return sidebarCollapsed.value ? '0px' : '220px'
  return sidebarCollapsed.value ? '64px' : '220px'
})

function checkMobile() {
  isMobile.value = window.innerWidth <= 768
  if (isMobile.value) sidebarCollapsed.value = true
}
onUnmounted(() => { window.removeEventListener('resize', checkMobile) })

const activeMenu = computed(() => route.path)

onMounted(async () => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
  // 初始化暗色主题
  document.documentElement.classList.toggle('dark', isDark.value)
  try {
    const dash = await ticketApi.dashboard()
    pendingCount.value = dash.pending_count || 0
  } catch (e) { ElMessage.error('加载仪表盘数据失败') }
})

function handleLogout() { store.logout(); router.push('/login') }
</script>

<style scoped>
.layout { height: 100vh; }

.sidebar {
  background: linear-gradient(180deg, #0f172a 0%, #1e3a5f 100%);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border-right: none;
}

.sidebar-header {
  padding: 24px 20px 20px;
  text-align: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.logo-wrapper {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 52px;
  height: 52px;
  border-radius: 14px;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.3), rgba(37, 99, 235, 0.5));
  margin-bottom: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}
.logo-icon { font-size: 28px; }

.title { font-size: 20px; font-weight: 700; color: white; letter-spacing: 1px; }
.subtitle { font-size: 12px; color: rgba(255, 255, 255, 0.45); margin-top: 4px; }

.sidebar .el-menu {
  flex: 1;
  border-right: none;
  margin-top: 12px;
  padding: 0 8px;
}

.sidebar .el-menu-item {
  height: 44px;
  line-height: 44px;
  margin: 2px 0;
  border-radius: 10px;
  font-size: 14px;
  transition: all 0.2s;
}

.sidebar .el-menu-item:hover {
  background: rgba(255, 255, 255, 0.08) !important;
}

.sidebar .el-menu-item.is-active {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.4), rgba(37, 99, 235, 0.6)) !important;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.2);
}

.sidebar-footer {
  padding: 16px 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.user-info { display: flex; align-items: center; gap: 10px; }
.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
  font-weight: 600;
}
.user-detail { display: flex; flex-direction: column; }
.user-name { color: white; font-size: 14px; font-weight: 500; }
.user-role { color: rgba(255, 255, 255, 0.45); font-size: 11px; margin-top: 1px; }
.logout-btn { color: rgba(255, 255, 255, 0.45) !important; font-size: 14px; }
.logout-btn:hover { color: rgba(255, 255, 255, 0.9) !important; }

.header {
  background: white;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  border-bottom: 1px solid #f0f0f0;
  height: 56px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.03);
}

.main {
  background: #f0f2f5;
  padding: 20px;
  overflow-y: auto;
}

.menu-toggle { display: none; margin-right: 8px; }

.sidebar-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  z-index: 99;
}

@media (max-width: 768px) {
  .menu-toggle { display: inline-flex; }
  .sidebar {
    position: fixed;
    z-index: 100;
    height: 100vh;
    transition: width 0.3s;
  }
  .sidebar.collapsed { width: 0 !important; overflow: hidden; }
  .main { padding: 12px; }
}

@media (max-width: 480px) {
  .header { padding: 0 12px; }
  .main { padding: 8px; }
}

/* 暗色主题 */
:global(html.dark) .header {
  background: #1d1e1f;
  border-bottom-color: #363637;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.2);
}
:global(html.dark) .main {
  background: #0a0a0a;
}
:global(html.dark) .sidebar {
  background: linear-gradient(180deg, #0a0a0a 0%, #141414 100%);
}
</style>
