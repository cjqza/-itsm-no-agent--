/**
 * Parameterised Axios client factory shared across all frontends.
 *
 * Usage:
 *   import { createApiClient } from '@shared/api/request'
 *   const api = createApiClient()            // defaults: baseURL='/api', loginPath='/login'
 *   const api = createApiClient({ loginPath: '/auth/login' })
 */
import axios from 'axios'
import { ElMessage } from 'element-plus'

export function createApiClient({ baseURL = '/api', loginPath = '/login', timeout = 30000 } = {}) {
  const api = axios.create({ baseURL, timeout })

  api.interceptors.request.use(
    (config) => {
      const token = localStorage.getItem('token')
      if (token) config.headers.Authorization = `Bearer ${token}`
      return config
    },
    (error) => Promise.reject(error)
  )

  api.interceptors.response.use(
    (response) => response.data,
    (error) => {
      const status = error.response?.status
      const msg = error.response?.data?.detail || '请求失败'
      const isLoginRequest = error.config?.url?.includes('/auth/login')
      const requireCaptcha = error.response?.headers?.['x-require-captcha'] === 'true'

      if (status === 401 && !isLoginRequest) {
        // 非登录接口的 401：token 过期，清除并跳转登录页
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        localStorage.removeItem('permissions')
        window.location.href = loginPath
      } else if (isLoginRequest && requireCaptcha) {
        // 登录接口需要验证码：不显示错误，由调用方弹出验证码对话框
      } else if (status === 401 && isLoginRequest) {
        // 登录接口的 401：账号或密码错误，不跳转，只返回错误
        // 不显示 ElMessage，由调用方处理
      } else if (status === 403) {
        ElMessage.warning(msg)
      } else {
        ElMessage.error(msg)
      }
      return Promise.reject(error)
    }
  )

  return api
}
