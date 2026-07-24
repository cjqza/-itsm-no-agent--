<template>
  <BaseLogin
    title="公司桌面IT服务台"
    subtitle="提交工单、在线咨询、快速解决IT问题"
    background-gradient="linear-gradient(135deg, #0f172a 0%, #1e3a5f 40%, #1d4ed8 100%)"
    logo-gradient="linear-gradient(135deg, #1e3a5f, #2563eb)"
    accent-color="#3b82f6"
    :show-register="true"
    copyright-text="公司桌面IT服务台 v1.0"
    :login-handler="handleLogin"
    :register-handler="handleRegister"
    :captcha-api="fetchCaptcha"
    :reset-password-api="handleResetPassword"
    @login-success="onLoginSuccess"
  >
    <template #logo>
      <div class="logo-wrapper" style="background: linear-gradient(135deg, #1e3a5f, #2563eb); box-shadow: 0 8px 24px rgba(37, 99, 235, 0.3);">
        <div class="logo-icon">🔧</div>
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

async function handleRegister(data) {
  await authApi.register(data)
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
:deep(.logo-icon) { font-size: 40px; line-height: 1; filter: brightness(0) invert(1); }
</style>
