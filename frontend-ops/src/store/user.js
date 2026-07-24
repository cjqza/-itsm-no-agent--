import { defineStore } from 'pinia'
import { authApi } from '@/api'
import { createBaseStore } from '@shared/stores/user'

export const useUserStore = defineStore('user', () => {
  return { ...createBaseStore(authApi) }
})
