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
      if (status === 401) {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        localStorage.removeItem('permissions')
        window.location.href = loginPath
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
