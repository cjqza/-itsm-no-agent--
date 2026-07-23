<template>
  <el-container class="layout">
    <el-aside width="220px" class="sidebar">
      <div class="sidebar-header">
        <div class="logo">📊</div>
        <div class="title">OPS</div>
        <div class="subtitle">运维统计分析</div>
      </div>
      <el-menu
        :default-active="activeMenu"
        router
        background-color="#0f766e"
        text-color="#99f6e4"
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
          <div class="avatar">{{ store.userName[0] }}</div>
          <span class="name">{{ store.userName }}</span>
        </div>
        <el-button text class="logout-btn" @click="handleLogout">退出</el-button>
      </div>
    </el-aside>
    <el-container>
      <el-header class="header">
        <el-breadcrumb>
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

const route = useRoute()
const router = useRouter()
const store = useUserStore()
const activeMenu = computed(() => route.path)

function handleLogout() { store.logout(); router.push('/login') }
</script>

<style scoped>
.layout { height: 100vh; }
.sidebar { background: #0f766e; display: flex; flex-direction: column; overflow: hidden; }
.sidebar-header { padding: 24px 20px 16px; text-align: center; border-bottom: 1px solid rgba(255,255,255,0.1); }
.logo { font-size: 32px; margin-bottom: 8px; }
.title { font-size: 20px; font-weight: bold; color: white; }
.subtitle { font-size: 12px; color: #99f6e4; margin-top: 4px; }
.sidebar .el-menu { flex: 1; border-right: none; margin-top: 8px; }
.sidebar .el-menu-item { height: 48px; line-height: 48px; margin: 4px 12px; border-radius: 8px; }
.sidebar .el-menu-item:hover, .sidebar .el-menu-item.is-active { background: rgba(255,255,255,0.15) !important; }
.sidebar-footer { padding: 16px 20px; border-top: 1px solid rgba(255,255,255,0.1); display: flex; align-items: center; justify-content: space-between; }
.user-info { display: flex; align-items: center; gap: 10px; }
.avatar { width: 32px; height: 32px; border-radius: 50%; background: #14b8a6; color: white; display: flex; align-items: center; justify-content: center; font-size: 14px; }
.name { color: white; font-size: 14px; }
.logout-btn { color: #99f6e4 !important; font-size: 12px; }
.logout-btn:hover { color: white !important; }
.header { background: white; display: flex; align-items: center; padding: 0 24px; border-bottom: 1px solid #e5e7eb; height: 56px; }
.main { background: #f5f7fa; padding: 20px; overflow-y: auto; }
</style>
