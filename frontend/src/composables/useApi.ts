import axios from 'axios'
import { auth } from '@/firebase'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Interceptor to add Firebase auth token to all requests
api.interceptors.request.use(async (config) => {
  const user = auth.currentUser
  if (user) {
    try {
      const token = await user.getIdToken()
      config.headers.Authorization = `Bearer ${token}`
    } catch {
      // If token fetch fails, proceed without it
    }
  }
  return config
})

/**
 * Generic GET request with typed response.
 * Unwraps backend's {success, data} envelope if present.
 */
export async function apiGet<T>(url: string, params?: Record<string, unknown>): Promise<T> {
  const response = await api.get(url, { params })
  const d = response.data
  if (d && typeof d === 'object' && 'data' in d) return d.data as T
  return d as T
}

/**
 * Generic POST request with typed response.
 * Unwraps backend's {success, data} envelope if present.
 */
export async function apiPost<T>(url: string, body?: unknown): Promise<T> {
  const response = await api.post(url, body)
  const d = response.data
  if (d && typeof d === 'object' && 'data' in d) return d.data as T
  return d as T
}
