import { createApiClient } from '@shared/api/request'

const api = createApiClient()

// ============ 认证 ============
export const authApi = {
  login: (loginData) => api.post('/auth/login', loginData),
  getMe: () => api.get('/auth/me'),
  resetPassword: (data) => api.post('/auth/reset-password', data),
}

// ============ 后台管理 ============
export const adminApi = {
  // 用户
  getUsers: (params) => api.get('/admin/users', { params }),
  updateUser: (userId, data) => api.put(`/admin/users/${userId}`, data),
  updateUserStatus: (userId, data) => api.put(`/admin/users/${userId}/status`, data),
  unlockUser: (userId) => api.put(`/admin/users/${userId}/unlock`),

  // 权限
  getPermissions: (params) => api.get('/admin/permissions', { params }),
  updatePermission: (userId, data) => api.put(`/admin/permissions/${userId}`, null, { params: data }),
  getPermissionRequests: (status) => api.get('/admin/permission-requests', { params: { status } }),
  createPermissionRequest: (data) => api.post('/admin/permission-requests', null, { params: data }),
  reviewRequest: (id, action) => api.put(`/admin/permission-requests/${id}`, null, { params: { action } }),

  // 分类管理
  getCategories: () => api.get('/admin/categories/'),
  createCategory: (data) => api.post('/admin/categories/', data),
  updateCategory: (id, data) => api.put(`/admin/categories/${id}`, data),
  deleteCategory: (id) => api.delete(`/admin/categories/${id}`),

  getBusinessModules: () => api.get('/admin/business-modules/'),
  createBusinessModule: (data) => api.post('/admin/business-modules/', data),
  updateBusinessModule: (id, data) => api.put(`/admin/business-modules/${id}`, data),
  deleteBusinessModule: (id) => api.delete(`/admin/business-modules/${id}`),

  getProperties: () => api.get('/admin/properties/'),
  createProperty: (data) => api.post('/admin/properties/', data),
  updateProperty: (id, data) => api.put(`/admin/properties/${id}`, data),
  deleteProperty: (id) => api.delete(`/admin/properties/${id}`),

  getSymptoms: () => api.get('/admin/symptoms/'),
  createSymptom: (data) => api.post('/admin/symptoms/', data),
  updateSymptom: (id, data) => api.put(`/admin/symptoms/${id}`, data),
  deleteSymptom: (id) => api.delete(`/admin/symptoms/${id}`),

  getCauses: () => api.get('/admin/causes/'),
  createCause: (data) => api.post('/admin/causes/', data),
  updateCause: (id, data) => api.put(`/admin/causes/${id}`, data),
  deleteCause: (id) => api.delete(`/admin/causes/${id}`),

  getSolutions: () => api.get('/admin/solutions/'),
  createSolution: (data) => api.post('/admin/solutions/', data),
  updateSolution: (id, data) => api.put(`/admin/solutions/${id}`, data),
  deleteSolution: (id) => api.delete(`/admin/solutions/${id}`),

  // 管理员
  createAdmin: (data) => api.post('/admin/admins', data),

  getAgents: () => api.get('/admin/agents'),
  createAgent: (data) => api.post('/admin/agents', data),
  updateAgent: (userId, data) => api.put(`/admin/agents/${userId}`, data),
  deleteAgent: (userId) => api.delete(`/admin/agents/${userId}`),

  // 账号审批
  getAccountRequests: (status) => api.get('/admin/account-requests', { params: { status } }),
  reviewAccountRequest: (userId, action) => api.put(`/admin/account-requests/${userId}`, null, { params: { action } }),

  // 操作日志
  getAuditLogs: (params) => api.get('/admin/audit-logs', { params }),
}

export default api
