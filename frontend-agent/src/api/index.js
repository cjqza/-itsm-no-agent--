import { createApiClient } from '@shared/api/request'

const api = createApiClient()

export const authApi = {
  login: (data) => api.post('/auth/login', data),
  getMe: () => api.get('/auth/me'),
  resetPassword: (data) => api.post('/auth/reset-password', data),
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
