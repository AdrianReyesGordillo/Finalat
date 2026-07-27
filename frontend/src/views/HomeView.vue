<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { getChatGreeting, sendChatMessage, type ChatState, type ChatResponse } from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import AdBanner from '@/components/AdBanner.vue'

const authStore = useAuthStore()
const firstName = computed(() => {
  const full = authStore.displayName
  return full ? full.split(' ')[0] : ''
})

interface DisplayMessage {
  role: 'user' | 'assistant'
  content: string
}

const messages = ref<DisplayMessage[]>([])
const chatState = ref<ChatState>({})
const stepIndex = ref(0)
const userInput = ref('')
const loading = ref(false)
const calculating = ref(false)
const chatContainer = ref<HTMLElement | null>(null)
const inputRef = ref<HTMLTextAreaElement | null>(null)

// ─── Persistencia en sessionStorage ──────────────────────────────────────────

function saveState() {
  sessionStorage.setItem('chat_messages', JSON.stringify(messages.value))
  sessionStorage.setItem('chat_state', JSON.stringify(chatState.value))
  sessionStorage.setItem('chat_step', String(stepIndex.value))
}

function loadState(): boolean {
  const saved = sessionStorage.getItem('chat_messages')
  const savedState = sessionStorage.getItem('chat_state')
  const savedStep = sessionStorage.getItem('chat_step')
  if (saved && savedState) {
    messages.value = JSON.parse(saved)
    chatState.value = JSON.parse(savedState)
    stepIndex.value = savedStep ? parseInt(savedStep) : 0
    return true
  }
  return false
}

onMounted(async () => {
  const restored = loadState()
  if (!restored) {
    try {
      const greeting = await getChatGreeting()
      const personalizedGreeting = firstName.value
        ? greeting.replace(/^Hola, soy/, `Hola **${firstName.value}**, soy`)
        : greeting
      messages.value.push({ role: 'assistant', content: personalizedGreeting })
    } catch {
      const name = firstName.value || ''
      messages.value.push({
        role: 'assistant',
        content: name
          ? `Hola **${name}**, soy **Fina**, tu asesora financiera. Puedo ayudarte a encontrar las mejores cuentas de ahorro para hacer crecer tu dinero en México. ¿En qué te puedo ayudar hoy?`
          : 'Hola, soy **Fina**, tu asesora financiera. Puedo ayudarte a encontrar las mejores cuentas de ahorro para hacer crecer tu dinero en México. ¿En qué te puedo ayudar hoy?',
      })
    }
    saveState()
  }
  await scrollToBottom()
})

onBeforeUnmount(() => {
  saveState()
})

async function handleSend() {
  const text = userInput.value.trim()
  if (!text || loading.value) return

  messages.value.push({ role: 'user', content: text })
  userInput.value = ''
  loading.value = true
  saveState()
  await scrollToBottom()

  try {
    const response: ChatResponse = await sendChatMessage(text, { ...chatState.value, user_name: firstName.value }, stepIndex.value)

    // Actualizar estado
    chatState.value = response.state
    stepIndex.value = response.current_step_index

    // Simular "pensando" para que se sienta más natural
    const thinkDelay = response.investment_result ? 0 : 800 + Math.random() * 700
    if (thinkDelay > 0) {
      await new Promise(resolve => setTimeout(resolve, thinkDelay))
    }

    if (response.investment_result) {
      loading.value = false
      calculating.value = true
      await scrollToBottom()

      await new Promise(resolve => setTimeout(resolve, 1500))
      calculating.value = false

      // Show the assistant's message with investment results inline in chat
      messages.value.push({
        role: 'assistant',
        content: response.assistant_message,
      })
      saveState()
    } else {
      messages.value.push({
        role: 'assistant',
        content: response.assistant_message,
      })
      saveState()
    }
  } catch (err) {
    messages.value.push({
      role: 'assistant',
      content: 'Tuve un problema al procesar tu mensaje. ¿Puedes intentar de nuevo?',
    })
    saveState()
  } finally {
    loading.value = false
    await scrollToBottom()
  }
}



function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}

// --- Slider plazo ---
const sliderMonths = ref(12)
const sliderActive = ref(false)

function sliderLabel(months: number): string {
  if (months <= 6) return '6 meses o menos'
  if (months >= 36) return '3 años o más'
  const years = Math.floor(months / 12)
  const rem = months % 12
  if (years === 0) return `${months} meses`
  if (rem === 0) return years === 1 ? '1 año' : `${years} años`
  return years === 1 ? `1 año ${rem} meses` : `${years} años ${rem} meses`
}

function sendSliderValue() {
  const label = sliderLabel(sliderMonths.value)
  sliderActive.value = false
  userInput.value = label
  handleSend()
}

async function scrollToBottom() {
  await nextTick()
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
  if (inputRef.value && !loading.value && !calculating.value) {
    inputRef.value.focus()
  }
}

function formatMarkdown(text: string): string {
  // Remove slider marker from rendered text (slider is handled separately)
  const cleaned = text.replace(/\[\[SLIDER_PLAZO\]\]/g, '')
  return cleaned
    .replace(/\[([^\]]+)\]\((https?:\/\/[^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener" class="text-[#F0A500] underline hover:text-[#d49200]">$1</a>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>')
}

function hasSlider(content: string): boolean {
  return content.includes('[[SLIDER_PLAZO]]')
}
</script>

<template>
  <div class="flex flex-col h-[calc(100dvh-64px)] overflow-hidden">
    <!-- Ad top banner (mobile/tablet) - visible en < lg -->
    <div class="lg:hidden px-3 pt-3">
      <AdBanner ad-format="horizontal" ins-style="display:block; height:60px" />
    </div>

    <!-- Main layout -->
    <div class="flex flex-1 min-h-0 px-2 md:px-4 py-3 gap-3">
      <!-- Ad left column (desktop lg+) -->
      <div class="hidden lg:flex w-[160px] flex-shrink-0 items-start">
        <div class="sticky top-3 w-full">
          <AdBanner ad-format="vertical" ins-style="display:block; width:160px; height:600px" />
        </div>
      </div>

      <!-- Chat column -->
      <div class="flex flex-col flex-1 min-w-0 max-w-2xl mx-auto">
        <!-- Chat container -->
        <div
          ref="chatContainer"
          class="flex-1 overflow-y-auto space-y-5 pb-4 px-1 md:px-3 chat-scroll"
        >
          <!-- Messages -->
          <div
            v-for="(msg, i) in messages"
            :key="i"
            class="flex flex-col"
          >
            <!-- Message row -->
            <div
              :class="[
                'flex',
                msg.role === 'user' ? 'justify-end' : 'justify-start',
              ]"
            >
              <!-- Assistant avatar -->
              <div
                v-if="msg.role === 'assistant'"
                class="w-11 h-11 rounded-full mr-3 flex-shrink-0 mt-1 bg-white dark:bg-[#15202b] border border-[#2D2B6B]/30 dark:border-[#2d3741] overflow-hidden flex items-center justify-center"
              >
                <img src="/logo-icon.jpg" alt="Fina" class="w-9 h-9 object-contain rounded-full" />
              </div>

              <!-- Bubble -->
              <div
                :class="[
                  'max-w-[85%] sm:max-w-[80%] px-4 sm:px-5 py-3.5 text-[15px] leading-relaxed',
                  msg.role === 'user'
                    ? 'bg-[#2D2B6B] text-white rounded-2xl rounded-br-sm chat-bubble-user'
                    : 'bg-white dark:bg-[#15202b] text-[#2D2B6B] dark:text-[#e1e8ed] rounded-2xl rounded-bl-sm border border-[#E0E0F0] dark:border-[#2d3741] shadow-sm chat-bubble-bot',
                ]"
              >
                <div v-html="formatMarkdown(msg.content)"></div>
              </div>
            </div>

            <!-- Slider de plazo (aparece debajo del bubble que lo solicita) -->
            <div v-if="msg.role === 'assistant' && hasSlider(msg.content) && i === messages.length - 1" class="w-full mt-3 px-14">
              <div class="bg-white dark:bg-[#15202b] border border-[#E0E0F0] dark:border-[#2d3741] rounded-2xl px-5 py-4 shadow-sm">
                <div class="flex justify-between items-center mb-2">
                  <span class="text-xs text-gray-500 dark:text-[#8899a6]">6 meses</span>
                  <span class="text-sm font-semibold text-[#2D2B6B] dark:text-white">{{ sliderLabel(sliderMonths) }}</span>
                  <span class="text-xs text-gray-500 dark:text-[#8899a6]">3+ años</span>
                </div>
                <input
                  type="range"
                  min="6"
                  max="36"
                  step="3"
                  v-model.number="sliderMonths"
                  class="w-full h-2 bg-gray-200 dark:bg-[#2d3741] rounded-lg appearance-none cursor-pointer accent-[#F0A500]"
                />
                <button
                  @click="sendSliderValue"
                  class="mt-3 w-full py-2 bg-[#F0A500]/40 hover:bg-[#F0A500] text-[#2D2B6B] font-semibold rounded-xl transition-colors"
                >
                  Seleccionar {{ sliderLabel(sliderMonths) }}
                </button>
              </div>
            </div>

          </div>

          <!-- Typing indicator -->
          <div v-if="loading" class="flex justify-start">
            <div class="w-11 h-11 rounded-full mr-3 flex-shrink-0 bg-white dark:bg-[#15202b] border border-[#2D2B6B]/30 dark:border-[#2d3741] overflow-hidden flex items-center justify-center">
              <img src="/logo-icon.jpg" alt="Fina" class="w-9 h-9 object-contain rounded-full" />
            </div>
            <div class="bg-white dark:bg-[#15202b] border border-[#E0E0F0] dark:border-[#2d3741] rounded-2xl rounded-bl-sm px-5 py-4 shadow-sm chat-bubble-bot">
              <div class="flex space-x-1.5">
                <div class="w-2.5 h-2.5 bg-primary-300 rounded-full animate-bounce" style="animation-delay: 0ms"></div>
                <div class="w-2.5 h-2.5 bg-primary-300 rounded-full animate-bounce" style="animation-delay: 150ms"></div>
                <div class="w-2.5 h-2.5 bg-primary-300 rounded-full animate-bounce" style="animation-delay: 300ms"></div>
              </div>
            </div>
          </div>

          <!-- Calculating animation -->
          <div v-if="calculating" class="flex justify-start">
            <div class="w-11 h-11 rounded-full mr-3 flex-shrink-0 bg-white dark:bg-[#15202b] border border-[#2D2B6B]/30 dark:border-[#2d3741] overflow-hidden flex items-center justify-center">
              <img src="/logo-icon.jpg" alt="Fina" class="w-9 h-9 object-contain rounded-full" />
            </div>
            <div class="bg-white border border-accent-200 rounded-2xl rounded-bl-sm px-5 py-4 shadow-sm">
              <div class="flex items-center gap-3">
                <div class="w-5 h-5 border-2 border-accent-500 border-t-transparent rounded-full animate-spin"></div>
                <span class="text-[15px] text-primary-700 font-medium">Calculando tu plan de inversión óptimo...</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Input area -->
        <div class="bg-transparent px-3 md:px-4 py-3">
          <div class="flex gap-2 items-center">
            <textarea
              ref="inputRef"
              v-model="userInput"
              @keydown="handleKeydown"
              :disabled="loading || calculating"
              rows="1"
              class="flex-1 resize-none px-4 py-3 bg-transparent border border-[#E0E0F0] dark:border-[#3a3a5c] rounded-3xl focus:ring-2 focus:ring-[#F0A500] focus:border-[#F0A500] text-[15px] text-[#2D2B6B] dark:text-white placeholder-[#9b99c8] disabled:opacity-50 outline-none transition-all chat-input"
              placeholder="Escribe tu respuesta..."
            ></textarea>
            <button
              @click="handleSend"
              :disabled="loading || calculating || !userInput.trim()"
              class="w-11 h-11 flex-shrink-0 bg-[#F0A500] hover:bg-[#d49200] text-[#2D2B6B] rounded-full flex items-center justify-center transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <line x1="22" y1="2" x2="11" y2="13"/>
                <polygon points="22 2 15 22 11 13 2 9 22 2"/>
              </svg>
            </button>
          </div>
          <p class="text-xs text-gray-400 mt-2 text-center">
            Finalat usa IA para asesorarte. Las tasas son referenciales.
          </p>
        </div>
      </div>

      <!-- Ad right column (desktop lg+) -->
      <div class="hidden lg:flex w-[160px] flex-shrink-0 items-start">
        <div class="sticky top-3 w-full">
          <AdBanner ad-format="vertical" ins-style="display:block; width:160px; height:600px" />
        </div>
      </div>
    </div>

    <!-- Ad bottom banner (mobile/tablet) - visible en < lg -->
    <div class="lg:hidden px-3 pb-3">
      <AdBanner ad-format="horizontal" ins-style="display:block; height:60px" />
    </div>
  </div>
</template>
