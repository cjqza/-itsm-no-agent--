import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/login', name: 'Login', component: () => import('@/views/Login.vue') },
  { path: '/', component: () => import('@/views/Layout.vue'),
    children: [
      { path: '', name: 'Overview', component: () => import('@/views/Overview.vue') },
      { path: 'analysis', name: 'Analysis', component: () => import('@/views/Analysis.vue') },
      { path: 'performance', name: 'Performance', component: () => import('@/views/Performance.vue') },
      { path: 'tickets', name: 'TicketHistory', component: () => import('@/views/TicketHistory.vue') },
    ],
  },
  { path: '/:pathMatch(.*)*', name: 'NotFound', component: () => import('@/views/NotFound.vue') },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.path === '/login') { next(); return }
  if (!token) { next('/login'); return }
  next()
})

export default router
