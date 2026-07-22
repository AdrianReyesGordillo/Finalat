<script setup lang="ts">
import { ref, nextTick, watch, onMounted } from 'vue'
import { useAdvisorStore } from '../../stores/advisor'
import ChatMessage from './ChatMessage.vue'
import type { Allocation } from '../../stores/advisor'

const store = useAdvisorStore()

const inputText = ref('')
const messagesContainer = ref<HTMLElement | null>(null)

// Scroll to bottom when messages change
watch(
  () => store.messages.length,
  async () => {
    await nextTick()
    scrollToBottom()
  }
)

// Also scroll when loading state changes (typing indicator appears/disappears)
watch(
  () => store.loading,
  async () => {
    await nextTick()
    scrollToBottom()
  }
)

function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

async function handleSend() {
  const text = inputText.value.trim()
  if (!text || store.loading || store.isTerminated) return
  inputText.value = ''
  await store.sendMessage(text)
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    handleSend()
  }
}

async function handleReset() {
  await store.resetSession()
}

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('es-MX', {
    style: 'currency',
    currency: 'MXN',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount)
}

function formatAllocation(alloc: Allocation): string {
  return `${alloc.instrument_name} — ${formatCurrency(alloc.allocated_amount)} (${alloc.effective_rate.toFixed(2)}% anual, rendimiento: ${formatCurrency(alloc.projected_annual_return)})`
}

// Load session on mount
onMounted(() => {
  store.loadSession()
})
</script>

<template>
  <div class="flex h-full flex-col">
    <!-- AI Limited banner -->
    <div
      v-if="store.aiLimited"
      class="flex items-center gap-2 border-b border-yellow-300 bg-yellow-50 px-4 py-2 dark:border-yellow-600 dark:bg-yellow-900/30"
      role="alert"
    >
      <span class="text-sm text-yellow-800 dark:text-yellow-200">
        El servicio de IA esta limitado. Las respuestas pueden ser menos detalladas.
      </span>
    </div>

    <!-- Messages area -->
    <div
      ref="messagesContainer"
      class="flex-1 overflow-y-auto px-4 py-4 space-y-3"
      aria-label="Historial de conversacion"
      role="log"
      aria-live="polite"
    >
      <!-- Session loading -->
      <div v-if="store.sessionLoading" class="flex items-center justify-center py-12">
        <div class="flex flex-col items-center gap-3">
          <div
            class="h-8 w-8 animate-spin rounded-full border-3 border-blue-600 border-t-transparent dark:border-blue-400 dark:border-t-transparent"
          />
          <span class="text-sm text-gray-500 dark:text-gray-400">Cargando conversacion...</span>
        </div>
      </div>

      <!-- Empty state (no messages yet) -->
      <div
        v-else-if="!store.hasMessages && !store.loading"
        class="flex flex-col items-center justify-center py-12 text-center"
      >
        <div class="mb-4 text-4xl" aria-hidden="true">🤖</div>
        <h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100">
          Hola, soy Fina
        </h2>
        <p class="mt-2 max-w-sm text-sm text-gray-600 dark:text-gray-400">
          Tu asesora financiera inteligente. Escribeme un mensaje para comenzar
          a encontrar la mejor forma de invertir tu capital.
        </p>
      </div>

      <!-- Message list -->
      <template v-else>
        <ChatMessage
          v-for="(msg, idx) in store.messages"
          :key="idx"
          :role="msg.role"
          :content="msg.content"
        />
      </template>

      <!-- Allocations display -->
      <div
        v-if="store.allocations && store.allocations.length > 0"
        class="rounded-lg border border-green-200 bg-green-50 p-4 dark:border-green-700 dark:bg-green-900/30"
      >
        <h3 class="mb-2 text-sm font-semibold text-green-800 dark:text-green-200">
          Asignacion recomendada
        </h3>
        <ul class="space-y-1">
          <li
            v-for="(alloc, idx) in store.allocations"
            :key="idx"
            class="text-sm text-green-700 dark:text-green-300"
          >
            {{ idx + 1 }}. {{ formatAllocation(alloc) }}
          </li>
        </ul>
      </div>

      <!-- Typing indicator -->
      <div
        v-if="store.loading"
        class="flex justify-start"
        aria-label="Fina esta pensando"
      >
        <div class="flex items-center gap-2 rounded-2xl rounded-bl-md bg-gray-100 px-4 py-3 dark:bg-gray-700">
          <div class="flex gap-1">
            <span class="h-2 w-2 animate-bounce rounded-full bg-gray-400 dark:bg-gray-500" style="animation-delay: 0ms" />
            <span class="h-2 w-2 animate-bounce rounded-full bg-gray-400 dark:bg-gray-500" style="animation-delay: 150ms" />
            <span class="h-2 w-2 animate-bounce rounded-full bg-gray-400 dark:bg-gray-500" style="animation-delay: 300ms" />
          </div>
          <span class="text-sm text-gray-500 dark:text-gray-400">Fina esta pensando...</span>
        </div>
      </div>
    </div>

    <!-- Error display -->
    <div
      v-if="store.error"
      class="border-t border-red-200 bg-red-50 px-4 py-2 dark:border-red-700 dark:bg-red-900/30"
      role="alert"
    >
      <div class="flex items-center justify-between">
        <span class="text-sm text-red-700 dark:text-red-300">{{ store.error }}</span>
        <button
          type="button"
          class="text-sm font-medium text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
          aria-label="Cerrar error"
          @click="store.clearError()"
        >
          Cerrar
        </button>
      </div>
    </div>

    <!-- Terminated state -->
    <div
      v-if="store.isTerminated"
      class="border-t border-gray-200 bg-gray-50 px-4 py-3 text-center dark:border-gray-700 dark:bg-gray-800"
    >
      <p class="text-sm text-gray-600 dark:text-gray-400">
        La sesion ha terminado. Puedes iniciar una nueva conversacion.
      </p>
    </div>

    <!-- Input area -->
    <div class="border-t border-gray-200 bg-white px-4 py-3 dark:border-gray-700 dark:bg-gray-900">
      <div class="flex items-end gap-2">
        <label for="advisor-input" class="sr-only">Escribe tu mensaje</label>
        <textarea
          id="advisor-input"
          v-model="inputText"
          :disabled="store.loading || store.isTerminated"
          rows="1"
          class="flex-1 resize-none rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900 placeholder-gray-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100 dark:placeholder-gray-400 dark:focus:border-blue-400"
          placeholder="Escribe tu mensaje..."
          aria-label="Escribe tu mensaje para Fina"
          @keydown="handleKeydown"
        />
        <button
          type="button"
          :disabled="!inputText.trim() || store.loading || store.isTerminated"
          class="inline-flex items-center justify-center rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-2 focus:outline-offset-2 focus:outline-blue-500 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-blue-500 dark:hover:bg-blue-600"
          aria-label="Enviar mensaje"
          @click="handleSend"
        >
          Enviar
        </button>
        <button
          type="button"
          :disabled="store.loading"
          class="inline-flex items-center justify-center rounded-lg border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-2 focus:outline-offset-2 focus:outline-blue-500 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
          aria-label="Reiniciar conversacion"
          title="Reiniciar conversacion"
          @click="handleReset"
        >
          Reiniciar
        </button>
      </div>
    </div>
  </div>
</template>
