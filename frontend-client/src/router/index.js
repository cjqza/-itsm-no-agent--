import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/login', name: 'Login', component: () => import('@/views/Login.vue') },
  { path: '/', component: () => import('@/views/Layout.vue'),
    children: [
      { path: '', name: 'Home', component: () => import('@/views/Home.vue') },
      { path: 'chat-rooms', name: 'ChatRooms', component: () => import('@/views/ChatRooms.vue') },
      { path: 'chat/:ticketId', name: 'Chat', component: () => import('@/views/Chat.vue') },
      { path: 'my-tickets', name: 'MyTickets', component: () => import('@/views/MyTickets.vue') },
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
