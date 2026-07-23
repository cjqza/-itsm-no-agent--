<template>
  <el-container class="layout">
    <el-aside width="220px" class="sidebar">
      <div class="sidebar-header">
        <div class="logo-wrapper">
          <div class="logo-icon">📊</div>
        </div>
        <div class="title">OPS</div>
        <div class="subtitle">运维统计分析</div>
      </div>
      <el-menu
        :default-active="activeMenu"
        router
        background-color="transparent"
        text-color="rgba(255,255,255,0.65)"
        active-text-color="#ffffff"
      >
        <el-menu-item index="/">
          <el-icon><DataAnalysis /></el-icon>
          <span>总览</span>
        </el-menu-item>
        <el-menu-item index="/analysis">
          <el-icon><PieChart /></el-icon>
          <span>工单分析</span>
        </el-menu-item>
        <el-menu-item index="/performance">
          <el-icon><User /></el-icon>
          <span>客服绩效</span>
        </el-menu-item>
        <el-menu-item index="/tickets">
          <el-icon><Tickets /></el-icon>
          <span>历史工单</span>
        </el-menu-item>
      </el-menu>
      <div class="sidebar-footer">
        <div class="user-info">
          <div class="avatar">{{ store.userName?.[0] || 'U' }}</div>
          <div class="user-detail">
            <div class="name">{{ store.userName }}</div>
            <div class="role">运维人员</div>
          </div>
        </div>
        <el-button text class="logout-btn" @click="handleLogout">
          <el-icon><SwitchButton /></el-icon>
        </el-button>
      </div>
    </el-aside>
    <el-container>
      <el-header class="header">
        <el-breadcrumb separator="/">
          <el-breadcrumb-item :to="{ path: '/' }">OPS</el-breadcrumb-item>
          <el-breadcrumb-item v-if="route.name === 'Analysis'">工单分析</el-breadcrumb-item>
          <el-breadcrumb-item v-if="route.name === 'Performance'">客服绩效</el-breadcrumb-item>
          <el-breadcrumb-item v-if="route.name === 'TicketHistory'">历史工单</el-breadcrumb-item>
        </el-breadcrumb>
      </el-header>
      <el-main class="main"><router-view /></el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
import { DataAnalysis, PieChart, User, Tickets, SwitchButton } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const store = useUserStore()
const activeMenu = computed(() => route.path)

function handleLogout() { store.logout(); router.push('/login') }
</script>

<style scoped>
.layout { height: 100vh; }

.sidebar {
  background: linear-gradient(180deg, #042f2e 0%, #0f766e 100%);
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
  background: linear-gradient(135deg, rgba(20, 184, 166, 0.3), rgba(15, 118, 110, 0.5));
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
  background: linear-gradient(135deg, rgba(20, 184, 166, 0.4), rgba(15, 118, 110, 0.6)) !important;
  box-shadow: 0 2px 8px rgba(15, 118, 110, 0.2);
}

.sidebar-footer {
  padding: 16px 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.user-info { display: flex; align-items: center; gap: 10px; }
.user-detail { display: flex; flex-direction: column; }
.avatar {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: linear-gradient(135deg, #14b8a6, #0f766e);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
  font-weight: 600;
}
.name { color: white; font-size: 14px; font-weight: 500; }
.role { color: rgba(255, 255, 255, 0.45); font-size: 11px; margin-top: 1px; }
.logout-btn { color: rgba(255, 255, 255, 0.45) !important; font-size: 14px; }
.logout-btn:hover { color: rgba(255, 255, 255, 0.9) !important; }

.header {
  background: white;
  display: flex;
  align-items: center;
  padding: 0 24px;
  border-bottom: 1px solid #f0f0f0;
  height: 56px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.03);
}

.main { background: #f0f2f5; padding: 20px; overflow-y: auto; }
</style>
