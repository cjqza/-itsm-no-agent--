<template>
  <div class="layout">
    <header class="header">
      <div class="logo" @click="router.push('/')">🔧 公司桌面IT服务台</div>
      <div class="nav">
        <router-link to="/" class="nav-item">首页</router-link>
        <router-link to="/chat-rooms" class="nav-item">💬 聊天</router-link>
        <router-link to="/my-tickets" class="nav-item">我的工单</router-link>
      </div>
      <div class="user">
        <span>{{ store.userName }}</span>
        <el-button text @click="handleLogout">退出</el-button>
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
const router = useRouter()
const store = useUserStore()
function handleLogout() { store.logout(); router.push('/login') }
</script>

<style scoped>
.layout { min-height: 100vh; background: #f5f7fa; }
.header { background: white; height: 60px; display: flex; align-items: center; padding: 0 24px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); position: sticky; top: 0; z-index: 100; }
.logo { font-size: 18px; font-weight: bold; color: #1a365d; cursor: pointer; }
.nav { flex: 1; display: flex; gap: 24px; margin-left: 48px; }
.nav-item { text-decoration: none; color: #666; font-size: 14px; padding: 8px 0; border-bottom: 2px solid transparent; }
.nav-item:hover, .nav-item.router-link-active { color: #2563eb; border-bottom-color: #2563eb; }
.user { display: flex; align-items: center; gap: 12px; color: #333; font-size: 14px; }
.main { max-width: 1200px; margin: 24px auto; padding: 0 24px; }
</style>
