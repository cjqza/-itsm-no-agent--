<template>
  <div class="login-page">
    <div class="login-card">
      <div class="logo">🖥️</div>
      <h1>ITSM服务工单管理</h1>
      <p>客服人员登录</p>
      <el-form :model="form" @submit.prevent="handleLogin" style="margin-top: 24px">
        <el-tabs v-model="loginMode">
          <el-tab-pane label="飞书ID登录" name="feishu">
            <el-input v-model="form.feishu_user_id" placeholder="请输入飞书用户ID" size="large" />
          </el-tab-pane>
          <el-tab-pane label="用户名登录" name="name">
            <el-input v-model="form.name" placeholder="请输入用户名" size="large" />
          </el-tab-pane>
        </el-tabs>
        <el-button type="primary" size="large" :loading="loading" @click="handleLogin" style="width: 100%; margin-top: 16px">
          登录
        </el-button>
      </el-form>
      <div class="demo-hints">
        <el-divider>测试账号</el-divider>
        <el-tag size="small" @click="quickLogin('agent_1')">张三</el-tag>
        <el-tag size="small" type="warning" @click="quickLogin('agent_2')">李四</el-tag>
        <el-tag size="small" type="info" @click="quickLogin('admin')">管理员</el-tag>
      </div>
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
const loginMode = ref('feishu')
const form = reactive({ feishu_user_id: '', name: '' })

async function handleLogin() {
  if (loginMode.value === 'feishu' && !form.feishu_user_id) { ElMessage.warning('请输入飞书用户ID'); return }
  if (loginMode.value === 'name' && !form.name) { ElMessage.warning('请输入用户名'); return }
  loading.value = true
  try {
    const data = loginMode.value === 'feishu' ? { feishu_user_id: form.feishu_user_id } : { name: form.name }
    await store.login(data)
    ElMessage.success('登录成功')
    router.push('/')
  } catch (e) { ElMessage.error('登录失败') }
  finally { loading.value = false }
}

function quickLogin(id) { form.feishu_user_id = id; loginMode.value = 'feishu'; handleLogin() }
</script>

<style scoped>
.login-page { height: 100vh; display: flex; justify-content: center; align-items: center; background: linear-gradient(135deg, #1a365d 0%, #1e40af 100%); }
.login-card { background: white; border-radius: 16px; padding: 48px; text-align: center; box-shadow: 0 20px 60px rgba(0,0,0,0.3); width: 420px; }
.logo { font-size: 64px; margin-bottom: 16px; }
h1 { color: #1a365d; margin-bottom: 8px; }
p { color: #666; margin-bottom: 24px; }
.demo-hints { margin-top: 16px; }
.demo-hints .el-tag { cursor: pointer; margin: 0 4px; }
</style>
