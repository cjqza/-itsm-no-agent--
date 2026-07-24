/**
 * Base user store factory.
 * Each frontend calls this with its own authApi instance,
 * then extends the returned refs/methods as needed.
 *
 * Usage:
 *   import { createBaseStore } from '@shared/stores/user'
 *   import { authApi } from '@/api'
 *
 *   export const useUserStore = defineStore('user', () => {
 *     const base = createBaseStore(authApi)
 *     // add frontend-specific computeds/methods here
 *     return { ...base }
 *   })
 */
import { ref, computed } from 'vue'

export function createBaseStore(authApi) {
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
  const permissions = ref(JSON.parse(localStorage.getItem('permissions') || '{}'))

  const isLoggedIn = computed(() => !!user.value)
  const userName = computed(() => user.value?.name || '')

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

  return { user, permissions, isLoggedIn, userName, login, logout, fetchMe }
}
