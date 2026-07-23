import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api'

export const useUserStore = defineStore('user', () => {
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
  const permissions = ref(JSON.parse(localStorage.getItem('permissions') || '{}'))
  const ws = ref(null)
  const wsCallbacks = ref([])
  // WebSocket 心跳/重连管理
  let heartbeatTimer = null
  let reconnectTimer = null
  let reconnectAttempts = 0
  let manualClose = false
  const MAX_RECONNECT = 10

  function clearWsTimers() {
    if (heartbeatTimer) { clearInterval(heartbeatTimer); heartbeatTimer = null }
    if (reconnectTimer) { clearTimeout(reconnectTimer); reconnectTimer = null }
  }

  const isLoggedIn = computed(() => !!user.value)
  const userName = computed(() => user.value?.name || '')
  const userRole = computed(() => user.value?.role || '')

  const hasItsm = computed(() => permissions.value?.itsm || false)
  const hasOps = computed(() => permissions.value?.ops || false)
  const hasAdmin = computed(() => permissions.value?.admin || false)
  const isAdmin = computed(() => ['admin', 'super_admin'].includes(user.value?.role))

  async function login(loginData) {
    // loginData: { account, password }
    const data = await authApi.login(loginData)
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
      user.value = { id: data.id, name: data.name, role: data.role, login_id: data.login_id, phone: data.phone }
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

    // 新建连接前清理旧连接与定时器，避免僵尸心跳/重复重连累积
    manualClose = false
    clearWsTimers()
    if (ws.value) {
      try { ws.value.onclose = null; ws.value.close() } catch (e) {}
      ws.value = null
    }

    try {
      const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
      const wsUrl = `${protocol}//${location.host}/ws?token=${token}`
      ws.value = new WebSocket(wsUrl)

      ws.value.onopen = () => {
        console.log('WebSocket已连接')
        reconnectAttempts = 0
        // 心跳（句柄存入 heartbeatTimer 以便清理）
        if (heartbeatTimer) clearInterval(heartbeatTimer)
        heartbeatTimer = setInterval(() => {
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
        if (heartbeatTimer) { clearInterval(heartbeatTimer); heartbeatTimer = null }
        // 主动 logout 触发的关闭不再重连
        if (manualClose) return
        if (reconnectAttempts < MAX_RECONNECT) {
          const delay = Math.min(3000 * Math.pow(2, reconnectAttempts), 30000)
          reconnectAttempts++
          console.log(`WebSocket断开，${delay / 1000}秒后重连(${reconnectAttempts}/${MAX_RECONNECT})...`)
          if (reconnectTimer) clearTimeout(reconnectTimer)
          reconnectTimer = setTimeout(connectWebSocket, delay)
        } else {
          console.log('WebSocket重连已达上限，停止重连')
        }
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
    // 主动关闭：清理定时器并阻止 onclose 触发重连
    manualClose = true
    reconnectAttempts = 0
    clearWsTimers()
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
