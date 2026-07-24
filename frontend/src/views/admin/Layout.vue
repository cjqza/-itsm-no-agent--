<template>
  <div v-if="isMobile && !sidebarCollapsed" class="sidebar-overlay" @click="sidebarCollapsed = true"></div>
  <el-container class="layout-container">
    <el-aside :width="sidebarWidth" class="sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="sidebar-header">
        <div class="logo-wrapper">
          <div class="logo-icon">⚙️</div>
        </div>
        <div class="title">后台管理</div>
        <div class="subtitle">系统配置与管理</div>
      </div>
      <el-menu
        :default-active="activeMenu"
        router
        background-color="transparent"
        text-color="rgba(255,255,255,0.65)"
        active-text-color="#ffffff"
      >
        <el-menu-item index="/admin"><el-icon><Key /></el-icon><span>权限管理</span></el-menu-item>
        <el-menu-item index="/admin/categories"><el-icon><Grid /></el-icon><span>分类配置</span></el-menu-item>
        <el-menu-item index="/admin/settings"><el-icon><Setting /></el-icon><span>系统设置</span></el-menu-item>
        <el-menu-item index="/admin/audit-logs"><el-icon><Document /></el-icon><span>操作日志</span></el-menu-item>
      </el-menu>
      <div class="sidebar-footer">
        <div class="user-info">
          <div class="avatar">{{ userStore.userName?.[0] || 'A' }}</div>
          <div class="user-detail">
            <div class="name">{{ userStore.userName }}</div>
            <div class="role">管理员</div>
          </div>
        </div>
        <el-button text class="logout-btn" @click="handleLogout">
          <el-icon><SwitchButton /></el-icon>
        </el-button>
      </div>
    </el-aside>
    <el-container>
      <el-header class="header">
        <div class="header-left">
          <el-button text class="menu-toggle" @click="sidebarCollapsed = !sidebarCollapsed">
            <el-icon :size="20"><Fold v-if="!sidebarCollapsed" /><Expand v-else /></el-icon>
          </el-button>
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/admin' }">后台管理</el-breadcrumb-item>
            <el-breadcrumb-item v-if="route.name === 'Categories'">分类配置</el-breadcrumb-item>
            <el-breadcrumb-item v-if="route.name === 'Settings'">系统设置</el-breadcrumb-item>
            <el-breadcrumb-item v-if="route.name === 'AdminAuditLogs'">操作日志</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <el-dropdown @command="handleCmd">
            <span class="header-user">
              <div class="header-avatar">{{ userStore.userName?.[0] || 'A' }}</div>
              <span>{{ userStore.userName }}</span>
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout">
                  <el-icon><SwitchButton /></el-icon> 退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      <el-main class="main-content"><router-view /></el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
import { Key, UserFilled, Grid, Setting, ArrowDown, SwitchButton, Document, Fold, Expand } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const activeMenu = computed(() => route.path)
const sidebarCollapsed = ref(false)
const isMobile = ref(false)
const sidebarWidth = computed(() => {
  if (isMobile.value) return sidebarCollapsed.value ? '0px' : '220px'
  return sidebarCollapsed.value ? '64px' : '220px'
})

function checkMobile() {
  isMobile.value = window.innerWidth <= 768
  if (isMobile.value) sidebarCollapsed.value = true
}
onMounted(() => { checkMobile(); window.addEventListener('resize', checkMobile) })
onUnmounted(() => { window.removeEventListener('resize', checkMobile) })
function handleLogout() { userStore.logout(); router.push('/login') }
function handleCmd(cmd) { if (cmd === 'logout') { userStore.logout(); router.push('/login') } }
</script>

<style scoped>
.layout-container { height: 100vh; }

.sidebar {
  background: linear-gradient(180deg, #1e1b4b 0%, #312e81 100%);
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
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.3), rgba(124, 58, 237, 0.5));
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
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.4), rgba(124, 58, 237, 0.6)) !important;
  box-shadow: 0 2px 8px rgba(124, 58, 237, 0.2);
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
  background: linear-gradient(135deg, #8b5cf6, #7c3aed);
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
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  border-bottom: 1px solid #f0f0f0;
  padding: 0 24px;
  height: 56px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.03);
}

.header-right { display: flex; align-items: center; }
.header-user {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 14px;
  color: #334155;
}
.header-avatar {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  background: linear-gradient(135deg, #8b5cf6, #7c3aed);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
}

.main-content { background: #f0f2f5; padding: 20px; overflow-y: auto; }

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
  .main-content { padding: 12px; }
}

@media (max-width: 480px) {
  .header { padding: 0 12px; }
  .main-content { padding: 8px; }
}
</style>
