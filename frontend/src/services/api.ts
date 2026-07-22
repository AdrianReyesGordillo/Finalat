import axios from 'axios'
import type { Instrument, InvestmentRequest, InvestmentResponse } from '@/types'
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
 * Sincroniza las tasas de CETES con la API de Banxico.
 * Actualiza la BD con las tasas más recientes.
 * Si falla (rate limit, red), no bloquea el flujo.
 */
export async function syncTasasBanxico(): Promise<{ synced: boolean; message: string }> {
  try {
    const response = await api.post('/scrapers/sync-banxico')
    return { synced: true, message: response.data.message || 'Synced' }
  } catch (err: any) {
    return { synced: false, message: 'No se pudieron sincronizar las tasas de Banxico' }
  }
}

export async function getInstruments(type?: string): Promise<Instrument[]> {
  const params = type ? { instrument_type: type } : {}
  const response = await api.get('/instruments/', { params })
  // Backend wraps response in {success, data: {items: [...]}}
  const data = response.data
  if (data?.data?.items) return data.data.items
  if (Array.isArray(data)) return data
  return []
}

export async function calculateOptimalDistribution(
  request: InvestmentRequest
): Promise<InvestmentResponse> {
  const response = await api.post<InvestmentResponse>('/calculator/optimize', request)
  return response.data
}

export async function getTasasCetes() {
  const response = await api.get('/banxico/tasas-cetes')
  return response.data
}

export async function getTasaObjetivo() {
  const response = await api.get('/banxico/tasa-objetivo')
  return response.data
}

/**
 * Sincroniza las tasas de Nu México con datos del scraping.
 * Actualiza la BD con las tasas más recientes.
 */
export async function syncTasasNu(): Promise<{ synced: boolean; message: string; vigencia?: string }> {
  try {
    const response = await api.post('/scrapers/sync-all')
    return { synced: true, message: 'Synced' }
  } catch (err: any) {
    return { synced: false, message: 'No se pudieron sincronizar las tasas de Nu' }
  }
}

/**
 * Sincroniza las tasas de Stori con datos del scraping.
 */
export async function syncTasasStori(): Promise<{ synced: boolean; message: string }> {
  // Stori sync is handled by sync-all
  return { synced: true, message: 'Handled by sync-all' }
}

/**
 * Sincroniza todas las fuentes adicionales (Ualá, Mercado Pago, Klar, Finsus, Didi).
 */
export async function syncAllScrapers(): Promise<{ synced: boolean; message: string }> {
  // Already handled by syncTasasNu which calls sync-all
  return { synced: true, message: 'Already synced' }
}

/**
 * Obtiene las tasas actuales de Nu con info de vigencia.
 */
export async function getTasasNu() {
  const response = await api.get('/nu/tasas')
  return response.data
}

// ─── Chat ────────────────────────────────────────────────────────────────────

export interface ChatState {
  [key: string]: any
}

export interface ChatResponse {
  assistant_message: string
  investment_result: any | null
  state: ChatState
  current_step_index: number
  completed: boolean
  redirect_to: string | null
}

export async function getChatGreeting(): Promise<string> {
  const response = await api.get('/chat/greeting')
  return response.data.message
}

export async function sendChatMessage(
  userMessage: string,
  state: ChatState,
  currentStepIndex: number
): Promise<ChatResponse> {
  const response = await api.post<ChatResponse>('/chat/message', {
    user_message: userMessage,
    state,
    current_step_index: currentStepIndex,
  })
  return response.data
}


// ─── Courses (Learning System) ──────────────────────────────────────────────

export interface CourseItem {
  id: string
  title: string
  description: string
  lesson_count: number
  sort_order: number
  created_at: string | null
  updated_at: string | null
}

export interface LessonSummary {
  id: string
  course_id: string
  title: string
  sort_order: number
  created_at: string | null
  updated_at: string | null
}

export interface CourseWithLessons {
  course: { id: string; title: string; description: string }
  lessons: LessonSummary[]
}

export interface LessonDetail {
  id: string
  course_id: string
  title: string
  content: string
  sort_order: number
  completed: boolean
  completed_at: string | null
  recommendation: string | null
  created_at: string | null
  updated_at: string | null
}

export interface CourseProgress {
  course_id: string
  course_title: string
  total_lessons: number
  completed_lessons: number
  progress_percentage: number
}

/** Unwrap the backend's {success, data} envelope */
function unwrap<T>(response: any): T {
  const d = response.data
  if (d && 'data' in d) return d.data as T
  return d as T
}

export async function getCourses(): Promise<CourseItem[]> {
  const response = await api.get('/courses')
  return unwrap<CourseItem[]>(response)
}

export async function getCourseLessons(courseId: string): Promise<CourseWithLessons> {
  const response = await api.get(`/courses/${courseId}/lessons`)
  return unwrap<CourseWithLessons>(response)
}

export async function getLessonDetail(courseId: string, lessonId: string): Promise<LessonDetail> {
  const response = await api.get(`/courses/${courseId}/lessons/${lessonId}`)
  return unwrap<LessonDetail>(response)
}

export async function markLessonComplete(courseId: string, lessonId: string): Promise<void> {
  await api.post(`/courses/${courseId}/lessons/${lessonId}/complete`)
}

export async function getCoursesProgress(): Promise<CourseProgress[]> {
  const response = await api.get('/courses/progress')
  return unwrap<CourseProgress[]>(response)
}
