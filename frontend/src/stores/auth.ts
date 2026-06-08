import { computed, shallowRef } from 'vue'
import { defineStore } from 'pinia'
import { http, tokenStorage } from '@/services/http'
import type { User } from '@/types'

interface TokenPair {
  access_token: string
  refresh_token: string
}

export const useAuthStore = defineStore('auth', () => {
  const user = shallowRef<User | null>(null)
  const loading = shallowRef(false)
  const isAuthenticated = computed(() => Boolean(tokenStorage.accessToken && user.value))
  const permissions = computed(
    () => new Set(user.value?.permission_codes ?? []),
  )

  async function login(username: string, password: string) {
    const body = new URLSearchParams({ username, password })
    const { data } = await http.post<TokenPair>('/auth/login', body, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    tokenStorage.set(data.access_token, data.refresh_token)
    await fetchCurrentUser()
  }

  async function fetchCurrentUser() {
    if (!tokenStorage.accessToken) return
    loading.value = true
    try {
      user.value = (await http.get<User>('/auth/me')).data
    } catch (error) {
      tokenStorage.clear()
      user.value = null
      throw error
    } finally {
      loading.value = false
    }
  }

  async function logout() {
    const refreshToken = tokenStorage.refreshToken
    if (refreshToken) {
      await http.post('/auth/logout', { refresh_token: refreshToken }).catch(() => undefined)
    }
    tokenStorage.clear()
    user.value = null
  }

  function hasPermission(code: string) {
    return Boolean(user.value?.is_superuser || permissions.value.has('*') || permissions.value.has(code))
  }

  return { user, loading, isAuthenticated, login, logout, fetchCurrentUser, hasPermission }
})
