import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

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
    const message = error.response?.data?.detail || '请求失败'
    if (status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      router.push('/login')
      ElMessage.error('登录已过期，请重新登录')
    } else if (status === 403) {
      ElMessage.error('没有权限访问')
    } else {
      ElMessage.error(message)
    }
    return Promise.reject(error)
  }
)

// ============ 认证 ============
export const authApi = {
  login: (loginData) => {
    if (typeof loginData === 'string') {
      return api.post('/auth/login', { feishu_user_id: loginData })
    }
    return api.post('/auth/login', loginData)
  },
  getMe: () => api.get('/auth/me'),
}

// ============ 后台管理 ============
export const adminApi = {
  // 权限
  getPermissions: () => api.get('/admin/permissions'),
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

  getAgents: () => api.get('/admin/agents'),
}

export default api
