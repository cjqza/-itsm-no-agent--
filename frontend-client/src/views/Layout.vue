<template>
  <div class="layout">
    <header class="header">
      <div class="logo" @click="router.push('/')">
        <span class="logo-icon">🔧</span>
        <span class="logo-text">公司桌面IT服务台</span>
      </div>
      <div class="nav">
        <router-link to="/" class="nav-item" exact-active-class="active">
          <el-icon><HomeFilled /></el-icon>
          <span>首页</span>
        </router-link>
        <router-link to="/chat-rooms" class="nav-item" active-class="active">
          <el-icon><ChatDotRound /></el-icon>
          <span>聊天</span>
        </router-link>
        <router-link to="/my-tickets" class="nav-item" active-class="active">
          <el-icon><Tickets /></el-icon>
          <span>我的工单</span>
        </router-link>
      </div>
      <div class="user">
        <div class="user-avatar">{{ store.userName?.[0] || 'U' }}</div>
        <span class="user-name">{{ store.userName }}</span>
        <el-divider direction="vertical" />
        <el-button text type="info" @click="handleLogout" size="small">
          <el-icon><SwitchButton /></el-icon> 退出
        </el-button>
      </div>
    </header>
    <main class="main">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
import { HomeFilled, ChatDotRound, Tickets, SwitchButton } from '@element-plus/icons-vue'
const router = useRouter()
const store = useUserStore()
function handleLogout() { store.logout(); router.push('/login') }
</script>

<style scoped>
.layout { min-height: 100vh; background: #f0f2f5; }

.header {
  background: white;
  height: 60px;
  display: flex;
  align-items: center;
  padding: 0 24px;
  box-shadow: 0 1px 8px rgba(0, 0, 0, 0.06);
  position: sticky;
  top: 0;
  z-index: 100;
  border-bottom: 1px solid #f0f0f0;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  flex-shrink: 0;
}
.logo-icon { font-size: 24px; }
.logo-text { font-size: 18px; font-weight: 700; color: #1e293b; letter-spacing: 0.3px; }

.nav { flex: 1; display: flex; gap: 4px; margin-left: 48px; }
.nav-item {
  display: flex;
  align-items: center;
  gap: 6px;
  text-decoration: none;
  color: #64748b;
  font-size: 14px;
  font-weight: 500;
  padding: 8px 16px;
  border-radius: 8px;
  transition: all 0.2s;
}
.nav-item:hover { color: #2563eb; background: #eff6ff; }
.nav-item.active { color: #2563eb; background: #dbeafe; font-weight: 600; }

.user {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}
.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #1e3a5f, #2563eb);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
}
.user-name { color: #334155; font-size: 14px; font-weight: 500; }

.main { max-width: 1200px; margin: 20px auto; padding: 0 24px; }
</style>
