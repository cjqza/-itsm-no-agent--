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

export const ticketApi = {
  create: (data) => api.post('/itsm/tickets', data),
  list: (params) => api.get('/itsm/tickets', { params }),
  get: (id) => api.get(`/itsm/tickets/${id}`),
  rate: (id, data) => api.put(`/itsm/tickets/${id}/rate`, data),
  cancel: (id) => api.put(`/itsm/tickets/${id}/cancel`),
  urge: (id, data) => api.put(`/itsm/tickets/${id}/urge`, data),
}

export const uploadApi = {
  upload: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
  },
}

export const chatApi = {
  createRoom: (ticketId) => api.post(`/chat/rooms/${ticketId}`),
  getRoom: (ticketId) => api.get(`/chat/rooms/${ticketId}`),
  getMyRooms: () => api.get('/chat/my-rooms'),
  deleteRoom: (roomId) => api.delete(`/chat/rooms/${roomId}`),
  getMessages: (roomId) => api.get(`/chat/rooms/${roomId}/messages`),
  sendMessage: (roomId, data) => api.post(`/chat/rooms/${roomId}/messages`, data),
  markRead: (roomId) => api.post(`/chat/rooms/${roomId}/read`),
  getUnread: (roomId) => api.get(`/chat/rooms/${roomId}/unread`),
}

export default api
