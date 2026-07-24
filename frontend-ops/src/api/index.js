import { createApiClient } from '@shared/api/request'

const api = createApiClient()

export const authApi = {
  login: (data) => api.post('/auth/login', data),
  getMe: () => api.get('/auth/me'),
  resetPassword: (data) => api.post('/auth/reset-password', data),
}

export const opsApi = {
  getOverview: (days = 30) => api.get('/ops/statistics/overview', { params: { days } }),
  getByCategory: (days = 30) => api.get('/ops/statistics/by-category', { params: { days } }),
  getByAgent: (days = 30) => api.get('/ops/statistics/by-agent', { params: { days } }),
  getRatings: (days = 30) => api.get('/ops/statistics/ratings', { params: { days } }),
  getSlaCompliance: (days = 30) => api.get('/ops/statistics/sla-compliance', { params: { days } }),
  getTrend: (days = 30) => api.get('/ops/statistics/trend', { params: { days } }),
  exportTickets: (params = {}) => api.get('/ops/export', { params: { days: 30, ...params }, responseType: 'blob' }),
}

export const ticketApi = {
  list: (params) => api.get('/itsm/tickets', { params }),
  get: (id) => api.get(`/itsm/tickets/${id}`),
  logs: (id) => api.get(`/itsm/tickets/${id}/logs`),
}

export const adminApi = {
  createPermissionRequest: (data) => api.post('/admin/permission-requests', null, { params: data }),
}

export default api
