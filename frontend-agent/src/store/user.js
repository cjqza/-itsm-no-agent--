import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api'

export const useUserStore = defineStore('user', () => {
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
  const permissions = ref(JSON.parse(localStorage.getItem('permissions') || '{}'))
  const isLoggedIn = computed(() => !!user.value)
  const userName = computed(() => user.value?.name || '')
  const hasItsm = computed(() => permissions.value?.itsm || false)

  async function login(loginData) {
    const data = await authApi.login(loginData)
    user.value = data.user
    permissions.value = data.permissions
    localStorage.setItem('token', data.token)
    localStorage.setItem('user', JSON.stringify(data.user))
    localStorage.setItem('permissions', JSON.stringify(data.permissions))
    return data
  }

  function logout() {
    user.value = null
    permissions.value = {}
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    localStorage.removeItem('permissions')
  }

  return { user, permissions, isLoggedIn, userName, hasItsm, login, logout }
})
