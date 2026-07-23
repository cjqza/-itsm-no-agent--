<template>
  <div class="login-page">
    <div class="login-card">
      <div class="logo">🔧</div>
      <h1>公司桌面IT服务台</h1>
      <p>IT服务台 - 提交工单、在线咨询</p>
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
      <div style="margin-top: 16px">
        <el-link type="primary" @click="showRegister = true">没有账号？申请注册</el-link>
      </div>
    </div>

    <!-- 注册对话框 -->
    <el-dialog v-model="showRegister" title="申请注册" width="420px" :close-on-click-modal="false">
      <el-form :model="regForm" :rules="regRules" ref="regFormRef" label-width="80px">
        <el-form-item label="姓名" prop="name">
          <el-input v-model="regForm.name" placeholder="请输入姓名" maxlength="128" />
        </el-form-item>
        <el-form-item label="电话" prop="phone">
          <el-input v-model="regForm.phone" placeholder="请输入电话号码" maxlength="32" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="regForm.password" type="password" placeholder="至少6位" show-password maxlength="128" />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input v-model="regForm.confirmPassword" type="password" placeholder="再次输入密码" show-password maxlength="128" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRegister = false">取消</el-button>
        <el-button type="primary" :loading="regLoading" @click="handleRegister">提交申请</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
import { ElMessage } from 'element-plus'
import { authApi } from '@/api'

const router = useRouter()
const store = useUserStore()
const loading = ref(false)
const form = reactive({ account: '', password: '' })

// --- 注册 ---
const showRegister = ref(false)
const regLoading = ref(false)
const regFormRef = ref(null)
const regForm = reactive({ name: '', phone: '', password: '', confirmPassword: '' })

const validateConfirm = (rule, value, callback) => {
  if (value !== regForm.password) callback(new Error('两次密码不一致'))
  else callback()
}

const regRules = {
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  phone: [
    { required: true, message: '请输入电话', trigger: 'blur' },
    { pattern: /^[0-9+\-() ]{5,32}$/, message: '电话格式不正确', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateConfirm, trigger: 'blur' },
  ],
}

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

async function handleRegister() {
  if (!regFormRef.value) return
  await regFormRef.value.validate(async (valid) => {
    if (!valid) return
    regLoading.value = true
    try {
      await authApi.register({ name: regForm.name, phone: regForm.phone, password: regForm.password })
      ElMessage.success('申请已提交，等待管理员审批')
      showRegister.value = false
      // 重置表单
      regForm.name = ''; regForm.phone = ''; regForm.password = ''; regForm.confirmPassword = ''
    } catch (e) {
      ElMessage.error(e.response?.data?.detail || '注册失败')
    } finally { regLoading.value = false }
  })
}
</script>

<style scoped>
.login-page { height: 100vh; display: flex; justify-content: center; align-items: center; background: linear-gradient(135deg, #1a365d 0%, #2563eb 100%); }
.login-card { background: white; border-radius: 16px; padding: 48px; text-align: center; box-shadow: 0 20px 60px rgba(0,0,0,0.3); width: 420px; }
.logo { font-size: 64px; margin-bottom: 16px; }
h1 { color: #1a365d; margin-bottom: 8px; }
p { color: #666; margin-bottom: 24px; }
</style>
