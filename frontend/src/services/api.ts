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
    const response = await api.post('/banxico/sync-tasas')
    return { synced: true, message: response.data.message }
  } catch (err: any) {
    const detail = err.response?.data?.detail
    const message = detail?.message || 'No se pudieron sincronizar las tasas de Banxico'
    console.warn('Sync Banxico:', message)
    return { synced: false, message }
  }
}

export async function getInstruments(type?: string): Promise<Instrument[]> {
  const params = type ? { instrument_type: type } : {}
  const response = await api.get<Instrument[]>('/instruments/', { params })
  return response.data
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
    const response = await api.post('/nu/sync-tasas')
    return { synced: true, message: response.data.message, vigencia: response.data.vigencia }
  } catch (err: any) {
    const detail = err.response?.data?.detail
    const message = typeof detail === 'string' ? detail : 'No se pudieron sincronizar las tasas de Nu'
    console.warn('Sync Nu:', message)
    return { synced: false, message }
  }
}

/**
 * Sincroniza las tasas de Stori con datos del scraping.
 */
export async function syncTasasStori(): Promise<{ synced: boolean; message: string }> {
  try {
    const response = await api.post('/stori/sync-tasas')
    return { synced: true, message: response.data.message }
  } catch (err: any) {
    const detail = err.response?.data?.detail
    const message = typeof detail === 'string' ? detail : 'No se pudieron sincronizar las tasas de Stori'
    console.warn('Sync Stori:', message)
    return { synced: false, message }
  }
}

/**
 * Sincroniza todas las fuentes adicionales (Ualá, Mercado Pago, Klar, Finsus, Didi).
 */
export async function syncAllScrapers(): Promise<{ synced: boolean; message: string }> {
  try {
    const response = await api.post('/scrapers/sync-all')
    return { synced: true, message: response.data.message }
  } catch (err: any) {
    console.warn('Sync scrapers:', err.message)
    return { synced: false, message: 'No se pudieron sincronizar algunas fuentes' }
  }
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
