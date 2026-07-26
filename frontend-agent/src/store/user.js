import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api'
import { createBaseStore } from '@shared/stores/user'
import { useWebSocket } from '@shared/composables/useWebSocket'

export const useUserStore = defineStore('user', () => {
  const wsCallbacks = ref([])

  const { connect: wsConnect, disconnect: wsDisconnect } = useWebSocket({
    onMessage: (msg) => {
      wsCallbacks.value.forEach(cb => cb(msg))
    },
    maxReconnect: 10,
  })

  const base = createBaseStore(authApi)
  const hasItsm = computed(() => base.permissions.value?.itsm || false)

  // Wrap login to also connect global WS
  async function login(loginData) {
    const data = await base.login(loginData)
    connectWebSocket()
    return data
  }

  // Wrap fetchMe to also connect global WS (页面刷新/恢复登录态时)
  async function fetchMe() {
    await base.fetchMe()
    if (base.isLoggedIn.value) {
      connectWebSocket()
    }
  }

  // Wrap logout to also disconnect global WS
  function logout() {
    wsDisconnect()
    base.logout()
  }

  function connectWebSocket() {
    wsConnect('/ws')
  }

  function onWsMessage(callback) {
    wsCallbacks.value.push(callback)
    return () => {
      wsCallbacks.value = wsCallbacks.value.filter(cb => cb !== callback)
    }
  }

  return {
    ...base,
    login,
    logout,
    fetchMe,
    hasItsm,
    connectWebSocket,
    onWsMessage,
  }
})
