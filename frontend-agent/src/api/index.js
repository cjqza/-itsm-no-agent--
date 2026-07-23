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
    console.error(`[API Error] ${status} ${error.config?.method?.toUpperCase()} ${error.config?.url}: ${msg}`)
    if (status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      localStorage.removeItem('permissions')
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

export const ticketApi = {
  dashboard: () => api.get('/itsm/dashboard'),
  list: (params) => api.get('/itsm/tickets', { params }),
  get: (id) => api.get(`/itsm/tickets/${id}`),
  accept: (id) => api.put(`/itsm/tickets/${id}/accept`),
  updateStatus: (id, data) => api.put(`/itsm/tickets/${id}/status`, data),
  resolve: (id) => api.put(`/itsm/tickets/${id}/resolve`),
  update: (id, data) => api.put(`/itsm/tickets/${id}`, data),
  remark: (id, data) => api.put(`/itsm/tickets/${id}/remark`, data),
  logs: (id) => api.get(`/itsm/tickets/${id}/logs`),
  search: (keyword) => api.get('/itsm/tickets/search', { params: { keyword } }),
  transfer: (id, data) => api.put(`/itsm/tickets/${id}/transfer`, data),
  cancel: (id) => api.put(`/itsm/tickets/${id}/cancel`),
  urge: (id, data) => api.put(`/itsm/tickets/${id}/urge`, data),
  getSlaWarnings: () => api.get('/itsm/tickets/sla-warnings'),
  pauseSla: (id, reason) => api.put(`/itsm/tickets/${id}/pause-sla`, null, { params: { reason } }),
  resumeSla: (id) => api.put(`/itsm/tickets/${id}/resume-sla`),
}

export const chatApi = {
  createRoom: (ticketId) => api.post(`/chat/rooms/${ticketId}`),
  getRoom: (ticketId) => api.get(`/chat/rooms/${ticketId}`),
  getMessages: (roomId) => api.get(`/chat/rooms/${roomId}/messages`),
  sendMessage: (roomId, data) => api.post(`/chat/rooms/${roomId}/messages`, data),
  closeRoom: (roomId) => api.put(`/chat/rooms/${roomId}/close`),
  markRead: (roomId) => api.post(`/chat/rooms/${roomId}/read`),
  getUnread: (roomId) => api.get(`/chat/rooms/${roomId}/unread`),
}

export const adminApi = {
  getCategories: () => api.get('/admin/categories/'),
  getAgents: () => api.get('/admin/agents'),
}

export const templateApi = {
  list: (category) => api.get('/templates', { params: category ? { category } : {} }),
  create: (data) => api.post('/templates', data),
  update: (id, data) => api.put(`/templates/${id}`, data),
  delete: (id) => api.delete(`/templates/${id}`),
}

export const uploadApi = {
  upload: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
  },
}

export default api
