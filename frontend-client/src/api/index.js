import { createApiClient } from '@shared/api/request'

const api = createApiClient()

export const authApi = {
  login: (data) => api.post('/auth/login', data),
  getMe: () => api.get('/auth/me'),
  register: (data) => api.post('/auth/register', data),
  resetPassword: (data) => api.post('/auth/reset-password', data),
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

export const categoryApi = {
  getCategories: () => api.get('/itsm/categories'),
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
