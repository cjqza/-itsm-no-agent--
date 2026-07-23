<template>
  <el-container class="layout">
    <!-- 深色侧边栏 -->
    <el-aside width="220px" class="sidebar">
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
import { ChatDotRound, HomeFilled, Tickets, SwitchButton, Bell } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const store = useUserStore()
const pendingCount = ref(0)

const activeMenu = computed(() => route.path)

onMounted(async () => {
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
</style>
