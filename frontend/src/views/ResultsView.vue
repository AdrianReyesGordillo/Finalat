<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import type { InvestmentResponse } from '@/types'
import { useCourseStore } from '@/stores/course'
import AdBanner from '@/components/AdBanner.vue'

const router = useRouter()
const courseStore = useCourseStore()
const result = ref<InvestmentResponse | null>(null)

function resetAndGoHome() {
  sessionStorage.removeItem('chat_messages')
  sessionStorage.removeItem('chat_state')
  sessionStorage.removeItem('chat_step')
  sessionStorage.removeItem('investmentResult')
  router.push('/')
}

async function joinLearningPlan() {
  await courseStore.enroll()
  router.push('/curso')
}

onMounted(() => {
  const stored = sessionStorage.getItem('investmentResult')
  if (stored) {
    result.value = JSON.parse(stored)
  } else {
    router.push('/')
  }
})

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('es-MX', {
    style: 'currency',
    currency: 'MXN',
    minimumFractionDigits: 2,
  }).format(value)
}

function formatPercent(value: number): string {
  return `${value.toFixed(2)}%`
}

function getPercentage(allocated: number, total: number): string {
  return ((allocated / total) * 100).toFixed(1)
}
</script>

<template>
  <div v-if="result" class="max-w-5xl mx-auto px-4 py-8 md:py-12">
    <!-- Resumen -->
    <div class="bg-gradient-to-r from-primary-700 to-primary-900 rounded-2xl p-6 md:p-8 text-white mb-8 shadow-lg">
      <h1 class="text-2xl md:text-3xl font-bold mb-2">Tu plan de inversión óptimo</h1>
      <div class="grid sm:grid-cols-2 md:grid-cols-3 gap-4 md:gap-6 mt-6">
        <div>
          <p class="text-primary-200 text-sm">Monto total</p>
          <p class="text-xl md:text-2xl font-bold">{{ formatCurrency(result.total_amount) }}</p>
        </div>
        <div>
          <p class="text-primary-200 text-sm">Rendimiento estimado</p>
          <p class="text-xl md:text-2xl font-bold text-accent-400">
            +{{ formatCurrency(result.total_estimated_return) }}
          </p>
        </div>
        <div>
          <p class="text-primary-200 text-sm">Tasa efectiva anual</p>
          <p class="text-xl md:text-2xl font-bold">{{ formatPercent(result.effective_annual_rate) }}</p>
        </div>
      </div>
      <p class="text-primary-200 text-sm mt-4">
        Plazo: {{ result.term_days }} días
      </p>
    </div>

    <!-- Espacio AdSense -->
    <div class="mb-8">
      <AdBanner ad-format="auto" />
    </div>

    <!-- Distribución -->
    <h2 class="text-xl md:text-2xl font-bold text-primary-700 mb-6">Distribución recomendada</h2>

    <div class="space-y-4">
      <div
        v-for="(alloc, index) in result.allocations"
        :key="index"
        class="bg-white rounded-2xl shadow-sm border border-surface-200 p-4 md:p-6 hover:shadow-md transition-shadow"
      >
        <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div class="flex-1">
            <div class="flex items-center gap-3 mb-2">
              <div class="w-10 h-10 bg-primary-50 rounded-full flex items-center justify-center text-primary-700 font-bold text-sm">
                {{ index + 1 }}
              </div>
              <div>
                <h3 class="font-semibold text-primary-700 text-base md:text-lg">{{ alloc.instrument_name }}</h3>
                <p class="text-sm text-primary-300">{{ alloc.institution }}</p>
              </div>
            </div>

            <!-- Barra de progreso -->
            <div class="mt-3">
              <div class="flex justify-between text-sm mb-1">
                <span class="text-primary-400">
                  {{ formatCurrency(alloc.allocated_amount) }}
                  ({{ getPercentage(alloc.allocated_amount, result.total_amount) }}%)
                </span>
                <span class="text-accent-600 font-medium">
                  {{ formatPercent(alloc.annual_rate) }} anual
                </span>
              </div>
              <div class="w-full bg-surface-200 rounded-full h-2">
                <div
                  class="bg-accent-500 h-2 rounded-full transition-all"
                  :style="{ width: getPercentage(alloc.allocated_amount, result.total_amount) + '%' }"
                ></div>
              </div>
            </div>

            <p class="text-sm text-primary-300 mt-2">
              Rendimiento estimado: <span class="text-accent-600 font-medium">+{{ formatCurrency(alloc.estimated_return) }}</span>
              <span v-if="alloc.term_days"> · {{ alloc.term_days }} días</span>
            </p>

            <p v-if="alloc.conditions" class="text-xs text-primary-200 mt-1">
              {{ alloc.conditions }}
            </p>
          </div>

          <!-- Links de acción -->
          <div class="flex flex-col gap-2 md:min-w-[160px]">
            <a
              v-if="alloc.signup_link"
              :href="alloc.referral_link || alloc.signup_link"
              target="_blank"
              rel="noopener noreferrer"
              class="inline-flex items-center justify-center px-4 py-2.5 bg-accent-500 hover:bg-accent-600 text-primary-700 text-sm font-semibold rounded-full transition-colors"
            >
              Abrir cuenta →
            </a>
          </div>
        </div>
      </div>
    </div>

    <!-- Protección del dinero -->
    <div class="mt-8 bg-surface-50 border border-surface-200 rounded-2xl p-6">
      <h3 class="font-semibold text-primary-700 mb-3">¿Cómo está protegido tu dinero?</h3>
      <div class="space-y-2 text-sm text-primary-400">
        <p><strong class="text-primary-600">Bancos (IPAB):</strong> Protegidos hasta ~$3,536,000 MXN por el gobierno si el banco quiebra.</p>
        <p><strong class="text-primary-600">SOFIPOS (ProSofipo):</strong> Apps de ahorro/rendimiento protegidas hasta ~$221,000 MXN. El excedente queda en riesgo.</p>
        <p><strong class="text-primary-600">Fintechs (Ley Fintech):</strong> Sin seguro de depósito, pero la ley les obliga a mantener tu dinero en cuentas segregadas o bonos gubernamentales.</p>
        <p class="text-xs text-primary-300 mt-2">Verifica en qué categoría opera tu institución en el portal de la CNBV o CONDUSEF.</p>
      </div>
    </div>

    <!-- CTA: Plan de Aprendizaje -->
    <div v-if="!courseStore.enrolled" class="mt-8 bg-gradient-to-r from-accent-50 to-accent-100 border border-accent-200 rounded-2xl p-6 md:p-8">
      <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h3 class="text-lg font-bold text-primary-700 mb-1">¿Quieres aprender más sobre inversiones?</h3>
          <p class="text-sm text-primary-400">
            Únete al plan de aprendizaje: un curso paso a paso para entender finanzas e inversiones desde cero. Aprende a tu ritmo con lecciones cortas.
          </p>
        </div>
        <button
          @click="joinLearningPlan"
          class="flex-shrink-0 inline-flex items-center gap-2 px-6 py-3 bg-accent-500 hover:bg-accent-600 text-primary-800 font-semibold rounded-full transition-colors"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
          </svg>
          Unirme al curso
        </button>
      </div>
    </div>

    <!-- Botón volver -->
    <div class="mt-8 text-center">
      <button
        @click="resetAndGoHome"
        class="px-6 py-3 bg-primary-50 hover:bg-primary-100 text-primary-700 font-medium rounded-full transition-colors border border-primary-200"
      >
        ← Calcular de nuevo
      </button>
    </div>

    <!-- Espacio AdSense inferior -->
    <div class="mt-8">
      <AdBanner ad-format="auto" />
    </div>
  </div>
</template>
