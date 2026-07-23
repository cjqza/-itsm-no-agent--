<template>
  <el-container class="layout-container">
    <el-aside width="220px" class="sidebar">
      <div class="sidebar-header"><h2>⚙️ 后台管理</h2></div>
      <el-menu :default-active="activeMenu" router background-color="#304156" text-color="#bfcbd9" active-text-color="#409eff">
        <el-menu-item index="/admin"><el-icon><Key /></el-icon><span>权限管理</span></el-menu-item>
        <el-menu-item index="/admin/categories"><el-icon><Grid /></el-icon><span>分类配置</span></el-menu-item>
        <el-menu-item index="/admin/settings"><el-icon><Setting /></el-icon><span>系统设置</span></el-menu-item>
      </el-menu>
      <div class="sidebar-footer">
        <div class="user-info">
          <div class="avatar">{{ userStore.userName[0] }}</div>
          <span class="name">{{ userStore.userName }}</span>
        </div>
        <el-button text class="logout-btn" @click="handleLogout">退出</el-button>
      </div>
    </el-aside>
    <el-container>
      <el-header class="header">
        <div><el-breadcrumb><el-breadcrumb-item :to="{ path: '/admin' }">后台管理</el-breadcrumb-item></el-breadcrumb></div>
        <div><el-dropdown @command="handleCmd"><span class="user-info">{{ userStore.userName }} <el-icon><ArrowDown /></el-icon></span><template #dropdown><el-dropdown-menu><el-dropdown-item command="logout">退出登录</el-dropdown-item></el-dropdown-menu></template></el-dropdown></div>
      </el-header>
      <el-main class="main-content"><router-view /></el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const activeMenu = computed(() => route.path)
function handleLogout() { userStore.logout(); router.push('/login') }
function handleCmd(cmd) { if (cmd === 'logout') { userStore.logout(); router.push('/login') } }
</script>

<style scoped>
.layout-container { height: 100vh; }
.sidebar { background-color: #304156; display: flex; flex-direction: column; overflow: hidden; }
.sidebar-header { padding: 20px; text-align: center; color: white; }
.sidebar-header h2 { font-size: 18px; margin: 0; }
.sidebar .el-menu { flex: 1; border-right: none; margin-top: 8px; }
.sidebar .el-menu-item { height: 48px; line-height: 48px; margin: 4px 12px; border-radius: 8px; }
.sidebar .el-menu-item:hover, .sidebar .el-menu-item.is-active { background: rgba(255,255,255,0.1) !important; }
.sidebar-footer { padding: 16px 20px; border-top: 1px solid rgba(255,255,255,0.1); display: flex; align-items: center; justify-content: space-between; }
.user-info { display: flex; align-items: center; gap: 10px; }
.avatar { width: 32px; height: 32px; border-radius: 50%; background: #409eff; color: white; display: flex; align-items: center; justify-content: center; font-size: 14px; }
.name { color: white; font-size: 14px; }
.logout-btn { color: #bfcbd9 !important; font-size: 12px; }
.logout-btn:hover { color: white !important; }
.header { display: flex; justify-content: space-between; align-items: center; background: white; border-bottom: 1px solid #e6e6e6; padding: 0 20px; }
.main-content { background: #f5f7fa; padding: 20px; overflow-y: auto; }
</style>
