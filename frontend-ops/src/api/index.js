import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

const api = axios.create({ baseURL: '/api', timeout: 30000 })

api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  response => response.data,
  error => {
    const status = error.response?.status
    const msg = error.response?.data?.detail || '请求失败'
    if (status === 401) {
      localStorage.removeItem('token')
      router.push('/login')
      ElMessage.error('登录已过期')
    } else {
      ElMessage.error(msg)
    }
    return Promise.reject(error)
  }
)

export const authApi = {
  login: (data) => api.post('/auth/login', data),
  getMe: () => api.get('/auth/me'),
}

export const opsApi = {
  getOverview: (days = 30) => api.get('/ops/statistics/overview', { params: { days } }),
  getByCategory: (days = 30) => api.get('/ops/statistics/by-category', { params: { days } }),
  getByAgent: (days = 30) => api.get('/ops/statistics/by-agent', { params: { days } }),
  getRatings: (days = 30) => api.get('/ops/statistics/ratings', { params: { days } }),
  getSlaCompliance: (days = 30) => api.get('/ops/statistics/sla-compliance', { params: { days } }),
  getTrend: (days = 30) => api.get('/ops/statistics/trend', { params: { days } }),
  exportTickets: (days = 30) => api.get('/ops/export', { params: { days }, responseType: 'blob' }),
}

export const ticketApi = {
  list: (params) => api.get('/itsm/tickets', { params }),
  get: (id) => api.get(`/itsm/tickets/${id}`),
  logs: (id) => api.get(`/itsm/tickets/${id}/logs`),
}

export default api
