<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <div class="logo-icon">🖥️</div>
        <h1>后台管理系统</h1>
        <p>权限管理、分类配置、系统设置</p>
      </div>
      <el-form :model="form" @submit.prevent="handleLogin" class="login-form">
        <el-tabs v-model="loginMode">
          <el-tab-pane label="飞书ID登录" name="feishu">
            <el-form-item>
              <el-input
                v-model="form.feishu_user_id"
                placeholder="请输入飞书用户ID"
                prefix-icon="User"
                size="large"
              />
            </el-form-item>
          </el-tab-pane>
          <el-tab-pane label="用户名登录" name="name">
            <el-form-item>
              <el-input
                v-model="form.name"
                placeholder="请输入用户名"
                prefix-icon="User"
                size="large"
              />
            </el-form-item>
          </el-tab-pane>
        </el-tabs>
        <el-form-item>
          <el-button type="primary" size="large" :loading="loading" @click="handleLogin" style="width: 100%">
            登录
          </el-button>
        </el-form-item>
        <div class="demo-hints">
          <el-divider>测试账号</el-divider>
          <p>管理员: <el-tag size="small" @click="quickLogin('admin')">系统管理员</el-tag></p>
          <p>客服: <el-tag size="small" type="warning" @click="quickLogin('agent_1')">张三</el-tag></p>
          <p>用户: <el-tag size="small" type="info" @click="quickLogin('user1')">刘一</el-tag></p>
        </div>
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
const userStore = useUserStore()
const loading = ref(false)
const loginMode = ref('feishu')
const form = reactive({
  feishu_user_id: '',
  name: '',
})

async function handleLogin() {
  if (loginMode.value === 'feishu' && !form.feishu_user_id) {
    ElMessage.warning('请输入飞书用户ID')
    return
  }
  if (loginMode.value === 'name' && !form.name) {
    ElMessage.warning('请输入用户名')
    return
  }

  loading.value = true
  try {
    const loginData = loginMode.value === 'feishu'
      ? { feishu_user_id: form.feishu_user_id }
      : { name: form.name }

    await userStore.login(loginData)
    ElMessage.success('登录成功')

    if (userStore.hasAdmin) {
      router.push('/admin')
    } else {
      router.push('/no-permission')
    }
  } catch (e) {
    ElMessage.error('登录失败')
  } finally {
    loading.value = false
  }
}

function quickLogin(feishuId) {
  form.feishu_user_id = feishuId
  loginMode.value = 'feishu'
  handleLogin()
}
</script>

<style scoped>
.login-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  width: 420px;
  padding: 40px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.logo-icon {
  font-size: 48px;
  margin-bottom: 10px;
}

.login-header h1 {
  font-size: 24px;
  color: #333;
  margin-bottom: 8px;
}

.login-header p {
  color: #999;
  font-size: 14px;
}

.demo-hints {
  margin-top: 10px;
  text-align: center;
}

.demo-hints p {
  margin: 6px 0;
  font-size: 13px;
  color: #666;
}

.demo-hints .el-tag {
  cursor: pointer;
}
</style>
