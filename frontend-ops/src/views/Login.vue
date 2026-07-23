<template>
  <div class="login-page">
    <div class="login-card">
      <div class="logo">📊</div>
      <h1>OPS运维统计</h1>
      <p>工单数据查询与统计分析</p>
      <el-form :model="form" @submit.prevent="handleLogin" style="margin-top: 24px">
        <el-form-item>
          <el-input v-model="form.account" placeholder="专属ID 或 手机号" size="large" prefix-icon="User" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="form.password" type="password" placeholder="请输入密码" size="large" prefix-icon="Lock" show-password />
        </el-form-item>
        <el-button type="primary" size="large" :loading="loading" @click="handleLogin" style="width: 100%; margin-top: 8px">
          登录
        </el-button>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
import { ElMessage } from 'element-plus'

const router = useRouter()
const store = useUserStore()
const loading = ref(false)
const form = reactive({ account: '', password: '' })

async function handleLogin() {
  if (!form.account) { ElMessage.warning('请输入账号'); return }
  if (!form.password) { ElMessage.warning('请输入密码'); return }
  loading.value = true
  try {
    await store.login({ account: form.account, password: form.password })
    ElMessage.success('登录成功')
    router.push('/')
  } catch (e) { ElMessage.error(e.response?.data?.detail || '登录失败') }
  finally { loading.value = false }
}
</script>

<style scoped>
.login-page { height: 100vh; display: flex; justify-content: center; align-items: center; background: linear-gradient(135deg, #0f766e 0%, #0d9488 100%); }
.login-card { background: white; border-radius: 16px; padding: 48px; text-align: center; box-shadow: 0 20px 60px rgba(0,0,0,0.3); width: 420px; }
.logo { font-size: 64px; margin-bottom: 16px; }
h1 { color: #0f766e; margin-bottom: 8px; }
p { color: #666; margin-bottom: 24px; }
</style>
