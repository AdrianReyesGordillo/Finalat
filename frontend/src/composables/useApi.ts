import axios, { type AxiosInstance, type AxiosError, type InternalAxiosRequestConfig } from 'axios'
import { useAuthStore } from '../stores/auth'
import type { APIResponse } from '../types'
import router from '../router'

/**
 * Creates and configures an Axios instance with:
 * - Base URL from environment variable
 * - Request interceptor: attaches JWT Bearer token from auth store
 * - Response interceptor: unwraps APIResponse envelope, handles errors (401, 429, generic)
 */
function createApiInstance(): AxiosInstance {
  const instance = axios.create({
    baseURL: import.meta.env.VITE_API_URL,
    headers: {
      'Content-Type': 'application/json',
    },
    timeout: 15000,
  })

  // --- Request Interceptor ---
  instance.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
      const authStore = useAuthStore()
      const token = authStore.token

      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }

      return config
    },
    (error) => Promise.reject(error)
  )

  // --- Response Interceptor ---
  instance.interceptors.response.use(
    (response) => {
      // Unwrap the APIResponse envelope: return response.data.data
      const body = response.data as APIResponse<unknown>
      if (body && typeof body === 'object' && 'success' in body) {
        if (body.success) {
          // Replace response.data with the unwrapped data
          response.data = body.data
        } else {
          // API returned success: false — treat as an error
          const message = body.error?.message || 'Error desconocido'
          return Promise.reject(new Error(message))
        }
      }
      return response
    },
    async (error: AxiosError<APIResponse<unknown>>) => {
      const authStore = useAuthStore()
      const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

      // Handle 401 Unauthorized: attempt token refresh, retry once
      if (error.response?.status === 401 && !originalRequest._retry) {
        originalRequest._retry = true

        try {
          const newToken = await authStore.refreshToken()
          if (newToken) {
            authStore.setToken(newToken)
            originalRequest.headers.Authorization = `Bearer ${newToken}`
            return instance(originalRequest)
          }
        } catch {
          // Refresh failed — fall through to clear auth
        }

        // Token refresh failed or no new token — redirect to login
        authStore.clearAuth()
        router.push('/login')
        return Promise.reject(new Error('Sesion expirada. Inicia sesion nuevamente.'))
      }

      // Handle 429 Rate Limited
      if (error.response?.status === 429) {
        const message = 'Has excedido el limite de solicitudes. Intenta de nuevo en un momento.'
        showNotification(message, 'warning')
        return Promise.reject(new Error(message))
      }

      // Generic error handler: extract message from API envelope or use fallback
      const apiError = error.response?.data?.error
      const message = apiError?.message || error.message || 'Error de conexion con el servidor.'
      return Promise.reject(new Error(message))
    }
  )

  return instance
}

/**
 * Simple notification utility.
 * Dispatches a custom event that UI components (e.g., ErrorAlert, Toast) can listen to.
 * This avoids coupling the composable to a specific UI library.
 */
function showNotification(message: string, severity: 'info' | 'warning' | 'error' = 'error') {
  if (typeof window !== 'undefined') {
    window.dispatchEvent(
      new CustomEvent('app:notification', {
        detail: { message, severity },
      })
    )
  }
}

// Singleton instance — created lazily
let apiInstance: AxiosInstance | null = null

function getApiInstance(): AxiosInstance {
  if (!apiInstance) {
    apiInstance = createApiInstance()
  }
  return apiInstance
}

/**
 * Composable that provides the configured Axios instance and typed convenience methods.
 */
export function useApi() {
  const api = getApiInstance()

  return {
    /** The raw Axios instance with interceptors pre-configured */
    api,

    /** Typed GET request — returns unwrapped data of type T */
    get: <T>(url: string, params?: Record<string, unknown>) =>
      api.get<T>(url, { params }).then((res) => res.data),

    /** Typed POST request — returns unwrapped data of type T */
    post: <T>(url: string, data?: unknown) =>
      api.post<T>(url, data).then((res) => res.data),

    /** Typed PUT request — returns unwrapped data of type T */
    put: <T>(url: string, data?: unknown) =>
      api.put<T>(url, data).then((res) => res.data),

    /** Typed DELETE request — returns unwrapped data of type T */
    delete: <T>(url: string) =>
      api.delete<T>(url).then((res) => res.data),
  }
}

// --- Standalone typed API methods for convenience imports ---

/** Typed GET request — returns unwrapped data of type T */
export function apiGet<T>(url: string, params?: Record<string, unknown>): Promise<T> {
  return getApiInstance()
    .get<T>(url, { params })
    .then((res) => res.data)
}

/** Typed POST request — returns unwrapped data of type T */
export function apiPost<T>(url: string, data?: unknown): Promise<T> {
  return getApiInstance()
    .post<T>(url, data)
    .then((res) => res.data)
}

/** Typed PUT request — returns unwrapped data of type T */
export function apiPut<T>(url: string, data?: unknown): Promise<T> {
  return getApiInstance()
    .put<T>(url, data)
    .then((res) => res.data)
}

/** Typed DELETE request — returns unwrapped data of type T */
export function apiDelete<T>(url: string): Promise<T> {
  return getApiInstance()
    .delete<T>(url)
    .then((res) => res.data)
}

export default useApi
