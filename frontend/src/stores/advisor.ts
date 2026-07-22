import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { apiPost, apiGet } from '../composables/useApi'

// --- Types ---

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp?: string
}

export interface Allocation {
  instrument_name: string
  allocated_amount: number
  effective_rate: number
  projected_annual_return: number
}

interface ChatApiResponse {
  message: string
  state: string
  done: boolean
  allocations: Allocation[] | null
  ai_limited: boolean
}

interface SessionApiResponse {
  session_id: string
  state: string
  interaction_count: number
  collected_params: Record<string, unknown> | null
  messages: ChatMessage[]
}

export const useAdvisorStore = defineStore('advisor', () => {
  // --- State ---
  const messages = ref<ChatMessage[]>([])
  const state = ref<string>('welcome')
  const loading = ref(false)
  const sessionLoading = ref(false)
  const error = ref<string | null>(null)
  const aiLimited = ref(false)
  const done = ref(false)
  const allocations = ref<Allocation[] | null>(null)
  const sessionId = ref<string | null>(null)
  const interactionCount = ref(0)

  // --- Computed ---
  const hasMessages = computed(() => messages.value.length > 0)
  const isTerminated = computed(() => state.value === 'terminated')

  // --- Actions ---

  /** Load existing session from the backend */
  async function loadSession() {
    sessionLoading.value = true
    error.value = null
    try {
      const data = await apiGet<SessionApiResponse>('/api/advisor/session')
      sessionId.value = data.session_id
      state.value = data.state
      interactionCount.value = data.interaction_count
      messages.value = data.messages || []
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Error al cargar la sesión del asesor.'
    } finally {
      sessionLoading.value = false
    }
  }

  /** Send a chat message to the advisor */
  async function sendMessage(text: string) {
    if (!text.trim() || loading.value) return

    // Add user message to local state immediately
    const userMsg: ChatMessage = { role: 'user', content: text.trim() }
    messages.value.push(userMsg)

    loading.value = true
    error.value = null
    aiLimited.value = false

    try {
      const data = await apiPost<ChatApiResponse>('/api/advisor/chat', { message: text.trim() })

      // Add assistant response
      const assistantMsg: ChatMessage = { role: 'assistant', content: data.message }
      messages.value.push(assistantMsg)

      // Update state
      state.value = data.state
      done.value = data.done
      aiLimited.value = data.ai_limited
      allocations.value = data.allocations || null
      interactionCount.value += 1
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Error al enviar el mensaje.'
      // Remove the user message if the request failed
      messages.value.pop()
    } finally {
      loading.value = false
    }
  }

  /** Reset the conversation session */
  async function resetSession() {
    loading.value = true
    error.value = null
    try {
      const data = await apiPost<SessionApiResponse>('/api/advisor/reset')
      sessionId.value = data.session_id
      state.value = data.state
      interactionCount.value = data.interaction_count
      messages.value = data.messages || []
      allocations.value = null
      aiLimited.value = false
      done.value = false
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Error al reiniciar la sesión.'
    } finally {
      loading.value = false
    }
  }

  /** Clear local error */
  function clearError() {
    error.value = null
  }

  return {
    // State
    messages,
    state,
    loading,
    sessionLoading,
    error,
    aiLimited,
    done,
    allocations,
    sessionId,
    interactionCount,

    // Computed
    hasMessages,
    isTerminated,

    // Actions
    loadSession,
    sendMessage,
    resetSession,
    clearError,
  }
})
