import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api'

export const useUserStore = defineStore('user', () => {
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
  const isLoggedIn = computed(() => !!user.value)
  const userName = computed(() => user.value?.name || '')
  const userId = computed(() => user.value?.id || null)

  async function login(loginData) {
    const data = await authApi.login(loginData)
    user.value = data.user
    localStorage.setItem('token', data.token)
    localStorage.setItem('user', JSON.stringify(data.user))
    return data
  }

  function logout() {
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  return { user, isLoggedIn, userName, userId, login, logout }
})
