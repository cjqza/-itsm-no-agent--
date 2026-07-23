<template>
  <div class="login-page">
    <!-- 装饰背景元素 -->
    <div class="bg-decoration">
      <div class="bg-circle bg-circle-1"></div>
      <div class="bg-circle bg-circle-2"></div>
      <div class="bg-circle bg-circle-3"></div>
    </div>

    <div class="login-card">
      <div class="login-header">
        <div class="logo-wrapper">
          <div class="logo-icon">📊</div>
        </div>
        <h1>OPS 运维统计</h1>
        <p class="subtitle">工单数据查询与统计分析</p>
      </div>

      <el-form :model="form" @submit.prevent="handleLogin" class="login-form">
        <el-form-item>
          <el-input
            v-model="form.account"
            placeholder="专属ID 或 手机号"
            size="large"
            prefix-icon="User"
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            size="large"
            prefix-icon="Lock"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        <el-button
          type="primary"
          size="large"
          :loading="loading"
          @click="handleLogin"
          class="login-btn"
        >
          <span v-if="!loading">登 录</span>
          <span v-else>登录中...</span>
        </el-button>
      </el-form>

      <div class="login-footer">
        <el-link type="primary" @click="openResetDialog" class="reset-link">忘记密码？</el-link>
      </div>

      <div class="copyright">
        <span>OPS 运维统计平台 v1.0</span>
        <span class="divider">|</span>
        <span>&copy; 2024 IT Support</span>
      </div>
    </div>

    <!-- 忘记密码对话框 -->
    <el-dialog v-model="showReset" title="重置密码" width="420px" :close-on-click-modal="false" class="reset-dialog">
      <el-form :model="resetForm" :rules="resetRules" ref="resetFormRef" label-width="80px">
        <el-form-item label="姓名" prop="name">
          <el-input v-model="resetForm.name" placeholder="请输入注册时的姓名" maxlength="128" />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="resetForm.phone" placeholder="请输入注册时的手机号" maxlength="32" />
        </el-form-item>
        <el-form-item label="验证码" prop="captcha_text">
          <div style="display: flex; gap: 8px; width: 100%">
            <el-input v-model="resetForm.captcha_text" placeholder="请输入验证码" style="flex: 1" />
            <img v-if="captchaImg" :src="captchaImg" @click="fetchCaptcha" style="height: 36px; cursor: pointer; border-radius: 4px; border: 1px solid #e2e8f0" alt="验证码" />
            <span v-else @click="fetchCaptcha" style="cursor: pointer; color: #64748b; white-space: nowrap; line-height: 36px">获取验证码</span>
          </div>
        </el-form-item>
        <el-form-item label="新密码" prop="new_password">
          <el-input v-model="resetForm.new_password" type="password" placeholder="至少6位" show-password maxlength="128" />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirm_password">
          <el-input v-model="resetForm.confirm_password" type="password" placeholder="再次输入新密码" show-password maxlength="128" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showReset = false">返回登录</el-button>
        <el-button type="primary" :loading="resetLoading" @click="handleResetPassword">重置密码</el-button>
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
import api from '@/api'

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

// --- 忘记密码 ---
const showReset = ref(false)
const resetLoading = ref(false)
const resetFormRef = ref(null)
const captchaImg = ref('')
const captchaId = ref('')
const resetForm = reactive({ name: '', phone: '', captcha_text: '', new_password: '', confirm_password: '' })

const validateConfirm = (rule, value, callback) => {
  if (value !== resetForm.new_password) callback(new Error('两次密码不一致'))
  else callback()
}

const resetRules = {
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  phone: [{ required: true, message: '请输入手机号', trigger: 'blur' }],
  captcha_text: [{ required: true, message: '请输入验证码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' },
  ],
  confirm_password: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateConfirm, trigger: 'blur' },
  ],
}

async function fetchCaptcha() {
  try {
    const res = await api.get('/auth/captcha')
    captchaImg.value = res.image
    captchaId.value = res.captcha_id
  } catch { /* ignore */ }
}

function openResetDialog() {
  resetForm.name = ''
  resetForm.phone = ''
  resetForm.captcha_text = ''
  resetForm.new_password = ''
  resetForm.confirm_password = ''
  showReset.value = true
  fetchCaptcha()
}

async function handleResetPassword() {
  if (!resetFormRef.value) return
  try { await resetFormRef.value.validate() } catch { return }
  resetLoading.value = true
  try {
    await authApi.resetPassword({
      name: resetForm.name,
      phone: resetForm.phone,
      captcha_id: captchaId.value,
      captcha_text: resetForm.captcha_text,
      new_password: resetForm.new_password,
    })
    ElMessage.success('密码重置成功，请重新登录')
    showReset.value = false
  } catch (e) {
    fetchCaptcha()
    resetForm.captcha_text = ''
    ElMessage.error(e.response?.data?.detail || '重置失败')
  } finally { resetLoading.value = false }
}
</script>

<style scoped>
.login-page {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #0f172a 0%, #064e3b 40%, #0f766e 100%);
  position: relative;
  overflow: hidden;
}

/* 装饰背景圆 */
.bg-decoration { position: absolute; inset: 0; pointer-events: none; overflow: hidden; }
.bg-circle { position: absolute; border-radius: 50%; opacity: 0.08; }
.bg-circle-1 { width: 600px; height: 600px; background: #14b8a6; top: -200px; right: -100px; }
.bg-circle-2 { width: 400px; height: 400px; background: #2dd4bf; bottom: -150px; left: -100px; }
.bg-circle-3 { width: 200px; height: 200px; background: #5eead4; top: 40%; left: 10%; }

.login-card {
  background: rgba(255, 255, 255, 0.98);
  border-radius: 20px;
  padding: 48px 40px 32px;
  text-align: center;
  box-shadow: 0 25px 80px rgba(0, 0, 0, 0.35);
  width: 420px;
  position: relative;
  z-index: 1;
}

.login-header { margin-bottom: 32px; }

.logo-wrapper {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 80px;
  height: 80px;
  border-radius: 20px;
  background: linear-gradient(135deg, #064e3b, #0f766e);
  margin-bottom: 20px;
  box-shadow: 0 8px 24px rgba(15, 118, 110, 0.3);
}
.logo-icon { font-size: 40px; line-height: 1; }

h1 {
  color: #1e293b;
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 8px;
  letter-spacing: 0.5px;
}
.subtitle { color: #64748b; font-size: 14px; }

.login-form { margin-top: 8px; }
.login-form :deep(.el-form-item) { margin-bottom: 20px; }
.login-form :deep(.el-input__wrapper) {
  border-radius: 10px;
  box-shadow: 0 0 0 1px #e2e8f0 inset;
  transition: box-shadow 0.2s;
}
.login-form :deep(.el-input__wrapper:hover) { box-shadow: 0 0 0 1px #99f6e4 inset; }
.login-form :deep(.el-input__wrapper.is-focus) { box-shadow: 0 0 0 2px #14b8a6 inset; }

.login-btn {
  width: 100%;
  height: 44px;
  border-radius: 10px;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 2px;
  margin-top: 4px;
  background: linear-gradient(135deg, #064e3b, #0f766e);
  border: none;
  transition: all 0.3s;
}
.login-btn:hover { transform: translateY(-1px); box-shadow: 0 6px 20px rgba(15, 118, 110, 0.4); }

.login-footer { margin-top: 16px; }
.reset-link { font-size: 13px; }

.copyright {
  margin-top: 32px;
  padding-top: 20px;
  border-top: 1px solid #f1f5f9;
  font-size: 12px;
  color: #94a3b8;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}
.copyright .divider { color: #cbd5e1; }
</style>
