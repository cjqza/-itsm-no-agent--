<template>
  <BaseLogin
    title="ITSM 服务工单管理"
    subtitle="客服人员工作台"
    background-gradient="linear-gradient(135deg, #0f172a 0%, #1e3a5f 40%, #1e40af 100%)"
    logo-gradient="linear-gradient(135deg, #1e3a5f, #1e40af)"
    accent-color="#3b82f6"
    copyright-text="ITSM 工单管理系统 v1.0"
    :login-handler="handleLogin"
    :captcha-api="fetchCaptcha"
    :reset-password-api="handleResetPassword"
    @login-success="onLoginSuccess"
  >
    <template #logo>
      <div class="logo-wrapper" style="background: linear-gradient(135deg, #1e3a5f, #1e40af); box-shadow: 0 8px 24px rgba(30, 64, 175, 0.3);">
        <div class="logo-icon">🖥️</div>
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
const store = useUserStore()

async function handleLogin(payload) {
  await store.login(payload)
}

function onLoginSuccess() {
  router.push('/')
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
