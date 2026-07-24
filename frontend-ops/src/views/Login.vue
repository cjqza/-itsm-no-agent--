<template>
  <BaseLogin
    title="OPS 运维统计"
    subtitle="工单数据查询与统计分析"
    background-gradient="linear-gradient(135deg, #0f172a 0%, #064e3b 40%, #0f766e 100%)"
    logo-gradient="linear-gradient(135deg, #064e3b, #0f766e)"
    accent-color="#14b8a6"
    copyright-text="OPS 运维统计平台 v1.0"
    :login-handler="handleLogin"
    :captcha-api="fetchCaptcha"
    :reset-password-api="handleResetPassword"
    @login-success="onLoginSuccess"
  >
    <template #logo>
      <div class="logo-wrapper" style="background: linear-gradient(135deg, #064e3b, #0f766e); box-shadow: 0 8px 24px rgba(15, 118, 110, 0.3);">
        <div class="logo-icon">📊</div>
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
