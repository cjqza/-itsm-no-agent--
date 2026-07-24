import { defineStore } from 'pinia'
import { computed } from 'vue'
import { authApi } from '@/api'
import { createBaseStore } from '@shared/stores/user'

export const useUserStore = defineStore('user', () => {
  const base = createBaseStore(authApi)
  const userId = computed(() => base.user.value?.id || null)

  return { ...base, userId }
})
