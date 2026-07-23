import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/Login.vue'),
  },
  {
    path: '/no-permission',
    name: 'NoPermission',
    component: () => import('@/views/auth/NoPermission.vue'),
  },
  {
    path: '/',
    redirect: '/admin',
  },
  // 后台管理路由
  {
    path: '/admin',
    component: () => import('@/views/admin/Layout.vue'),
    meta: { requiresAdmin: true },
    children: [
      {
        path: '',
        name: 'AdminPermissions',
        component: () => import('@/views/admin/Permissions.vue'),
      },
      {
        path: 'categories',
        name: 'AdminCategories',
        component: () => import('@/views/admin/Categories.vue'),
      },
      {
        path: 'settings',
        name: 'AdminSettings',
        component: () => import('@/views/admin/Settings.vue'),
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/auth/NotFound.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')

  if (to.path === '/login') {
    next()
    return
  }

  if (!token) {
    next('/login')
    return
  }

  // 检查admin权限
  if (to.matched.some(record => record.meta.requiresAdmin)) {
    const permissions = JSON.parse(localStorage.getItem('permissions') || '{}')
    if (!permissions.admin) {
      next('/no-permission')
      return
    }
  }

  next()
})

export default router
