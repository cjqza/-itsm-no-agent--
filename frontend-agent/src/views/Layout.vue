<template>
  <el-container class="layout">
    <!-- 深色侧边栏 -->
    <el-aside width="220px" class="sidebar">
      <div class="sidebar-header">
        <div class="logo">🖥️</div>
        <div class="title">ITSM</div>
        <div class="subtitle">服务工单管理</div>
      </div>
      <el-menu
        :default-active="activeMenu"
        router
        background-color="#1a365d"
        text-color="#94a3b8"
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
          <div class="user-avatar">{{ store.userName[0] }}</div>
          <div class="user-name">{{ store.userName }}</div>
        </div>
        <el-button text class="logout-btn" @click="handleLogout">退出</el-button>
      </div>
    </el-aside>

    <!-- 主内容区 -->
    <el-container>
      <el-header class="header">
        <div class="header-left">
          <el-breadcrumb>
            <el-breadcrumb-item :to="{ path: '/' }">工作台</el-breadcrumb-item>
            <el-breadcrumb-item v-if="route.name === 'TicketList'">服务请求</el-breadcrumb-item>
            <el-breadcrumb-item v-if="route.name === 'TicketDetail'">工单详情</el-breadcrumb-item>
            <el-breadcrumb-item v-if="route.name === 'AgentChat'">消息</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <el-badge :value="pendingCount" :hidden="pendingCount === 0" class="badge">
            <el-button text>待处理</el-button>
          </el-badge>
        </div>
      </el-header>
      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
import { ticketApi } from '@/api'
import { ChatDotRound } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const store = useUserStore()
const pendingCount = ref(0)

const activeMenu = computed(() => route.path)

onMounted(async () => {
  try {
    const dash = await ticketApi.dashboard()
    pendingCount.value = dash.pending_count || 0
  } catch (e) {}
})

function handleLogout() { store.logout(); router.push('/login') }
</script>

<style scoped>
.layout { height: 100vh; }

.sidebar {
  background: #1a365d;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar-header {
  padding: 24px 20px 16px;
  text-align: center;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}

.logo { font-size: 32px; margin-bottom: 8px; }
.title { font-size: 20px; font-weight: bold; color: white; }
.subtitle { font-size: 12px; color: #94a3b8; margin-top: 4px; }

.sidebar .el-menu {
  flex: 1;
  border-right: none;
  margin-top: 8px;
}

.sidebar .el-menu-item {
  height: 48px;
  line-height: 48px;
  margin: 4px 12px;
  border-radius: 8px;
}

.sidebar .el-menu-item:hover,
.sidebar .el-menu-item.is-active {
  background: rgba(255,255,255,0.1) !important;
}

.sidebar-footer {
  padding: 16px 20px;
  border-top: 1px solid rgba(255,255,255,0.1);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.user-info { display: flex; align-items: center; gap: 10px; }
.user-avatar { width: 32px; height: 32px; border-radius: 50%; background: #3b82f6; color: white; display: flex; align-items: center; justify-content: center; font-size: 14px; }
.user-name { color: white; font-size: 14px; }
.logout-btn { color: #94a3b8 !important; font-size: 12px; }
.logout-btn:hover { color: white !important; }

.header {
  background: white;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  border-bottom: 1px solid #e5e7eb;
  height: 56px;
}

.main {
  background: #f5f7fa;
  padding: 20px;
  overflow-y: auto;
}
</style>
