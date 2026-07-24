<template>
  <BaseLogin
    title="后台管理系统"
    subtitle="权限管理、分类配置、系统设置"
    background-gradient="linear-gradient(135deg, #0f172a 0%, #312e81 40%, #6d28d9 100%)"
    logo-gradient="linear-gradient(135deg, #4c1d95, #7c3aed)"
    accent-color="#8b5cf6"
    copyright-text="后台管理系统 v1.0"
    :login-handler="handleLogin"
    :captcha-api="fetchCaptcha"
    :reset-password-api="handleResetPassword"
    @login-success="onLoginSuccess"
  >
    <template #logo>
      <div class="logo-wrapper" style="background: linear-gradient(135deg, #4c1d95, #7c3aed); box-shadow: 0 8px 24px rgba(124, 58, 237, 0.3);">
        <div class="logo-icon">⚙️</div>
      </div>
    </template>
  </BaseLogin>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
import { authApi } from '@/api'
import api from '@/api'
import BaseLogin from '@shared/components/BaseLogin.vue'

const router = useRouter()
const userStore = useUserStore()

async function handleLogin(payload) {
  await userStore.login(payload)
}

function onLoginSuccess() {
  if (userStore.hasAdmin) {
    router.push('/admin')
  } else {
    router.push('/no-permission')
  }
}

async function fetchCaptcha() {
  return await api.get('/auth/captcha')
}

async function handleResetPassword(data) {
  await authApi.resetPassword(data)
}
</script>

<style scoped>
:deep(.logo-wrapper) {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 80px;
  height: 80px;
  border-radius: 20px;
  margin-bottom: 20px;
}
:deep(.logo-icon) { font-size: 40px; line-height: 1; }
</style>
