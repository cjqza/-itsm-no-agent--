import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/login', name: 'Login', component: () => import('@/views/Login.vue') },
  { path: '/', component: () => import('@/views/Layout.vue'),
    children: [
      { path: '', name: 'Dashboard', component: () => import('@/views/Dashboard.vue') },
      { path: 'tickets', name: 'TicketList', component: () => import('@/views/TicketList.vue') },
      { path: 'tickets/:id', name: 'TicketDetail', component: () => import('@/views/TicketDetail.vue') },
      { path: 'chat', name: 'AgentChat', component: () => import('@/views/AgentChat.vue') },
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
