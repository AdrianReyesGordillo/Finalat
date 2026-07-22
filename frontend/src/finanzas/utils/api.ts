/**
 * Authenticated axios instance for the finanzas module.
 *
 * All requests automatically include the Firebase ID token in the
 * Authorization header, ensuring the backend can identify the user
 * and scope data to their account.
 */
import axios from 'axios'
import { auth } from '@/firebase'

const finApi = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Attach Firebase ID token to every request
finApi.interceptors.request.use(async (config) => {
  const user = auth.currentUser
  if (user) {
    try {
      const token = await user.getIdToken()
      config.headers.Authorization = `Bearer ${token}`
    } catch {
      // If token fetch fails, proceed without it (backend will return 401)
    }
  }
  return config
})

export default finApi
