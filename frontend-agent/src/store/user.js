import { defineStore } from 'pinia'
import { computed } from 'vue'
import { authApi } from '@/api'
import { createBaseStore } from '@shared/stores/user'

export const useUserStore = defineStore('user', () => {
  const base = createBaseStore(authApi)
  const hasItsm = computed(() => base.permissions.value?.itsm || false)

  return { ...base, hasItsm }
})
