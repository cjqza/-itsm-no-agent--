<template>
  <div class="login-page" :style="{ background: backgroundGradient }">
    <!-- 装饰背景元素 -->
    <div class="bg-decoration">
      <div class="bg-circle bg-circle-1" :style="{ background: accentColor }"></div>
      <div class="bg-circle bg-circle-2" :style="{ background: accentColor }"></div>
      <div class="bg-circle bg-circle-3" :style="{ background: accentColor }"></div>
    </div>

    <div class="login-card">
      <div class="login-header">
        <slot name="logo">
          <div class="logo-wrapper" :style="{ background: logoGradient }">
            <div class="logo-icon">🔑</div>
          </div>
        </slot>
        <h1>{{ title }}</h1>
        <p class="subtitle">{{ subtitle }}</p>
      </div>

      <el-form :model="form" @submit.prevent="handleLogin" class="login-form" ref="loginFormRef">
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
          :loading="loginLoading"
          @click="handleLogin"
          class="login-btn"
          :style="{ background: logoGradient, border: 'none' }"
        >
          <span v-if="!loginLoading">登 录</span>
          <span v-else>登录中...</span>
        </el-button>
      </el-form>

      <div class="login-footer">
        <el-link v-if="showRegister" type="primary" @click="openRegisterDialog" class="register-link">
          没有账号？申请注册
        </el-link>
        <span v-if="showRegister && showForgotPassword" class="divider">|</span>
        <el-link v-if="showForgotPassword" type="primary" @click="openResetDialog" class="reset-link">忘记密码？</el-link>
      </div>

      <slot name="extra"></slot>

      <div v-if="copyrightText" class="copyright">
        <span>{{ copyrightText }}</span>
        <span class="divider">|</span>
        <span>&copy; 2024 IT Support</span>
      </div>
    </div>

    <!-- 注册对话框 -->
    <el-dialog v-model="showRegisterDialog" title="申请注册" width="420px" :close-on-click-modal="false" class="register-dialog">
      <el-form :model="regForm" :rules="regRules" ref="regFormRef" label-width="80px">
        <el-form-item label="姓名" prop="name">
          <el-input v-model="regForm.name" placeholder="请输入姓名" maxlength="128" prefix-icon="User" />
        </el-form-item>
        <el-form-item label="电话" prop="phone">
          <el-input v-model="regForm.phone" placeholder="请输入电话号码" maxlength="32" prefix-icon="Phone" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="regForm.password" type="password" placeholder="至少6位" show-password maxlength="128" prefix-icon="Lock" />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input v-model="regForm.confirmPassword" type="password" placeholder="再次输入密码" show-password maxlength="128" prefix-icon="Lock" />
        </el-form-item>
        <el-form-item label="验证码" prop="captcha_text">
          <div style="display: flex; gap: 8px; width: 100%">
            <el-input v-model="regForm.captcha_text" placeholder="请输入验证码" style="flex: 1" />
            <img v-if="regCaptchaImg" :src="regCaptchaImg" @click="fetchRegCaptcha" style="height: 36px; cursor: pointer; border-radius: 4px; border: 1px solid #e2e8f0" alt="验证码" />
            <span v-else @click="fetchRegCaptcha" style="cursor: pointer; color: #64748b; white-space: nowrap; line-height: 36px">获取验证码</span>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRegisterDialog = false">取消</el-button>
        <el-button type="primary" :loading="regLoading" @click="handleRegister">提交申请</el-button>
      </template>
    </el-dialog>

    <!-- 忘记密码对话框 -->
    <el-dialog v-model="showResetDialog" title="重置密码" width="420px" :close-on-click-modal="false" class="reset-dialog">
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
        <el-button @click="showResetDialog = false">返回登录</el-button>
        <el-button type="primary" :loading="resetLoading" @click="handleResetPassword">重置密码</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  title: { type: String, default: '系统登录' },
  subtitle: { type: String, default: '' },
  backgroundGradient: { type: String, default: 'linear-gradient(135deg, #0f172a 0%, #1e3a5f 40%, #2563eb 100%)' },
  logoGradient: { type: String, default: 'linear-gradient(135deg, #1e3a5f, #2563eb)' },
  accentColor: { type: String, default: '#3b82f6' },
  showRegister: { type: Boolean, default: false },
  showForgotPassword: { type: Boolean, default: true },
  copyrightText: { type: String, default: '' },
  loginHandler: { type: Function, required: true },
  registerHandler: { type: Function, default: null },
  captchaApi: { type: Function, required: true },
  resetPasswordApi: { type: Function, required: true },
})

const emit = defineEmits(['login-success', 'register-success', 'reset-success'])

// --- 登录 ---
const loginLoading = ref(false)
const loginFormRef = ref(null)
const form = reactive({ account: '', password: '' })

async function handleLogin() {
  if (!form.account) { ElMessage.warning('请输入账号'); return }
  if (!form.password) { ElMessage.warning('请输入密码'); return }
  loginLoading.value = true
  try {
    await props.loginHandler({ account: form.account, password: form.password })
    ElMessage.success('登录成功')
    emit('login-success')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '登录失败')
  } finally {
    loginLoading.value = false
  }
}

// --- 注册 ---
const showRegisterDialog = ref(false)
const regLoading = ref(false)
const regFormRef = ref(null)
const regForm = reactive({ name: '', phone: '', password: '', confirmPassword: '', captcha_text: '' })

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
  captcha_text: [{ required: true, message: '请输入验证码', trigger: 'blur' }],
}

// 注册验证码
const regCaptchaImg = ref('')
const regCaptchaId = ref('')

async function fetchRegCaptcha() {
  try {
    const res = await props.captchaApi()
    regCaptchaImg.value = res.image
    regCaptchaId.value = res.captcha_id
  } catch (e) { console.error('获取验证码失败', e) }
}

function openRegisterDialog() {
  regForm.name = ''
  regForm.phone = ''
  regForm.password = ''
  regForm.confirmPassword = ''
  regForm.captcha_text = ''
  showRegisterDialog.value = true
  fetchRegCaptcha()
}

async function handleRegister() {
  if (!regFormRef.value) return
  await regFormRef.value.validate(async (valid) => {
    if (!valid) return
    if (!props.registerHandler) { ElMessage.error('注册功能未配置'); return }
    regLoading.value = true
    try {
      await props.registerHandler({
        name: regForm.name,
        phone: regForm.phone,
        password: regForm.password,
        captcha_id: regCaptchaId.value,
        captcha_text: regForm.captcha_text,
      })
      ElMessage.success('申请已提交，等待管理员审批')
      showRegisterDialog.value = false
      emit('register-success')
    } catch (e) {
      fetchRegCaptcha()
      regForm.captcha_text = ''
      ElMessage.error(e.response?.data?.detail || '注册失败')
    } finally {
      regLoading.value = false
    }
  })
}

// --- 忘记密码 ---
const showResetDialog = ref(false)
const resetLoading = ref(false)
const resetFormRef = ref(null)
const captchaImg = ref('')
const captchaId = ref('')
const resetForm = reactive({ name: '', phone: '', captcha_text: '', new_password: '', confirm_password: '' })

const validateResetConfirm = (rule, value, callback) => {
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
    { validator: validateResetConfirm, trigger: 'blur' },
  ],
}

async function fetchCaptcha() {
  try {
    const res = await props.captchaApi()
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
  showResetDialog.value = true
  fetchCaptcha()
}

async function handleResetPassword() {
  if (!resetFormRef.value) return
  try { await resetFormRef.value.validate() } catch { return }
  resetLoading.value = true
  try {
    await props.resetPasswordApi({
      name: resetForm.name,
      phone: resetForm.phone,
      captcha_id: captchaId.value,
      captcha_text: resetForm.captcha_text,
      new_password: resetForm.new_password,
    })
    ElMessage.success('密码重置成功，请重新登录')
    showResetDialog.value = false
    emit('reset-success')
  } catch (e) {
    fetchCaptcha()
    resetForm.captcha_text = ''
    ElMessage.error(e.response?.data?.detail || '重置失败')
  } finally {
    resetLoading.value = false
  }
}
</script>

<style scoped>
.login-page {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
  overflow: hidden;
}

/* 装饰背景圆 */
.bg-decoration { position: absolute; inset: 0; pointer-events: none; overflow: hidden; }
.bg-circle { position: absolute; border-radius: 50%; opacity: 0.08; }
.bg-circle-1 { width: 600px; height: 600px; top: -200px; right: -100px; }
.bg-circle-2 { width: 400px; height: 400px; bottom: -150px; left: -100px; }
.bg-circle-3 { width: 200px; height: 200px; top: 40%; left: 10%; }

.login-card {
  background: rgba(255, 255, 255, 0.98);
  border-radius: 20px;
  padding: 48px 40px 32px;
  text-align: center;
  box-shadow: 0 25px 80px rgba(0, 0, 0, 0.35), 0 0 0 1px rgba(255, 255, 255, 0.1);
  max-width: 420px;
  width: 90%;
  position: relative;
  z-index: 1;
}

.login-header { margin-bottom: 32px; }

:deep(.logo-wrapper) {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 80px;
  height: 80px;
  border-radius: 20px;
  margin-bottom: 20px;
  box-shadow: 0 8px 24px rgba(37, 99, 235, 0.3);
}
:deep(.logo-icon) { font-size: 40px; line-height: 1; }

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
.login-form :deep(.el-input__wrapper:hover) { box-shadow: 0 0 0 1px #93c5fd inset; }
.login-form :deep(.el-input__wrapper.is-focus) { box-shadow: 0 0 0 2px #3b82f6 inset; }

.login-btn {
  width: 100%;
  height: 44px;
  border-radius: 10px;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 2px;
  margin-top: 4px;
  transition: all 0.3s;
}
.login-btn:hover { transform: translateY(-1px); box-shadow: 0 6px 20px rgba(37, 99, 235, 0.4); }

.login-footer { margin-top: 20px; display: flex; align-items: center; justify-content: center; gap: 12px; }
.register-link { font-size: 14px; }
.reset-link { font-size: 13px; }
.login-footer .divider { color: #cbd5e1; }

.copyright {
  margin-top: 28px;
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

@media (max-width: 480px) {
  .login-card { padding: 32px 20px 24px; border-radius: 16px; }
  h1 { font-size: 20px; }
  .login-footer { flex-direction: column; gap: 8px; }
  .login-footer .divider { display: none; }
}
</style>
