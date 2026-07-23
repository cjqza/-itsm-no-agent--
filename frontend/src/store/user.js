import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api'

export const useUserStore = defineStore('user', () => {
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
  const permissions = ref(JSON.parse(localStorage.getItem('permissions') || '{}'))
  const ws = ref(null)
  const wsCallbacks = ref([])

  const isLoggedIn = computed(() => !!user.value)
  const userName = computed(() => user.value?.name || '')
  const userRole = computed(() => user.value?.role || '')

  const hasItsm = computed(() => permissions.value?.itsm || false)
  const hasOps = computed(() => permissions.value?.ops || false)
  const hasAdmin = computed(() => permissions.value?.admin || false)
  const isAdmin = computed(() => ['admin', 'super_admin'].includes(user.value?.role))

  async function login(loginData) {
    // loginData: { feishu_user_id } 或 { name } 或字符串
    const payload = typeof loginData === 'string'
      ? { feishu_user_id: loginData }
      : loginData
    const data = await authApi.login(payload)
    user.value = data.user
    permissions.value = data.permissions
    localStorage.setItem('token', data.token)
    localStorage.setItem('user', JSON.stringify(data.user))
    localStorage.setItem('permissions', JSON.stringify(data.permissions))

    // 登录后连接WebSocket
    connectWebSocket()

    return data
  }

  async function fetchMe() {
    try {
      const data = await authApi.getMe()
      user.value = { id: data.id, name: data.name, role: data.role }
      permissions.value = data.permissions
      localStorage.setItem('user', JSON.stringify(user.value))
      localStorage.setItem('permissions', JSON.stringify(data.permissions))
    } catch (e) {
      logout()
    }
  }

  function connectWebSocket() {
    const token = localStorage.getItem('token')
    if (!token) return

    try {
      const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
      const wsUrl = `${protocol}//${location.host}/ws?token=${token}`
      ws.value = new WebSocket(wsUrl)

      ws.value.onopen = () => {
        console.log('WebSocket已连接')
        // 心跳
        setInterval(() => {
          if (ws.value?.readyState === WebSocket.OPEN) {
            ws.value.send('ping')
          }
        }, 30000)
      }

      ws.value.onmessage = (event) => {
        if (event.data === 'pong') return
        try {
          const msg = JSON.parse(event.data)
          // 触发所有注册的回调
          wsCallbacks.value.forEach(cb => cb(msg))
        } catch (e) {}
      }

      ws.value.onclose = () => {
        console.log('WebSocket断开，5秒后重连...')
        setTimeout(connectWebSocket, 5000)
      }
    } catch (e) {}
  }

  function onWsMessage(callback) {
    wsCallbacks.value.push(callback)
    return () => {
      wsCallbacks.value = wsCallbacks.value.filter(cb => cb !== callback)
    }
  }

  function logout() {
    user.value = null
    permissions.value = {}
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    localStorage.removeItem('permissions')
    if (ws.value) {
      ws.value.close()
      ws.value = null
    }
  }

  return {
    user, permissions, isLoggedIn, userName, userRole,
    hasItsm, hasOps, hasAdmin, isAdmin,
    login, fetchMe, logout, connectWebSocket, onWsMessage,
  }
})
