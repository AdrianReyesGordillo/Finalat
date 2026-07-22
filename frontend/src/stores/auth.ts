import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User } from 'firebase/auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(null)
  const loading = ref<boolean>(true)
  const error = ref<string | null>(null)

  const isAuthenticated = computed(() => !!user.value)
  const userId = computed(() => user.value?.uid ?? null)

  function setUser(newUser: User | null) {
    user.value = newUser
  }

  function setToken(newToken: string | null) {
    token.value = newToken
  }

  function setLoading(isLoading: boolean) {
    loading.value = isLoading
  }

  function setError(errorMessage: string | null) {
    error.value = errorMessage
  }

  function clearAuth() {
    user.value = null
    token.value = null
    error.value = null
  }

  /**
   * Attempts to refresh the Firebase ID token silently.
   * Returns the new token or null if refresh is not possible.
   */
  async function refreshToken(): Promise<string | null> {
    const currentUser = user.value
    if (!currentUser) return null

    try {
      const newToken = await currentUser.getIdToken(true)
      token.value = newToken
      return newToken
    } catch {
      return null
    }
  }

  return {
    user,
    token,
    loading,
    error,
    isAuthenticated,
    userId,
    setUser,
    setToken,
    setLoading,
    setError,
    clearAuth,
    refreshToken,
  }
})
