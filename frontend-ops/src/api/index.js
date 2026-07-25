import { createApiClient } from '@shared/api/request'

const api = createApiClient()

export const authApi = {
  login: (data) => api.post('/auth/login', data),
  getMe: () => api.get('/auth/me'),
  resetPassword: (data) => api.post('/auth/reset-password', data),
}

export const opsApi = {
  getOverview: (days = null) => api.get('/ops/statistics/overview', { params: days ? { days } : {} }),
  getByCategory: (days = null) => api.get('/ops/statistics/by-category', { params: days ? { days } : {} }),
  getByAgent: (days = null) => api.get('/ops/statistics/by-agent', { params: days ? { days } : {} }),
  getRatings: (days = null) => api.get('/ops/statistics/ratings', { params: days ? { days } : {} }),
  getSlaCompliance: (days = null) => api.get('/ops/statistics/sla-compliance', { params: days ? { days } : {} }),
  getTrend: (days = null) => api.get('/ops/statistics/trend', { params: days ? { days } : {} }),
  getStatusDistribution: (days = null) => api.get('/ops/status-distribution', { params: days ? { days } : {} }),
  getCategoryStats: (days = null) => api.get('/ops/category-stats', { params: days ? { days } : {} }),
  getRatingDistribution: (days = null) => api.get('/ops/rating-distribution', { params: days ? { days } : {} }),
  listTickets: (params = {}) => api.get('/ops/tickets', { params }),
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
