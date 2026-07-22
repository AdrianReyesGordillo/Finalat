<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useApi } from '../composables/useApi'
import { CurrencyDisplay, LoadingSpinner } from '../components/ui'
import type { PatrimonioNeto } from '../types'

// --- State ---
const { get } = useApi()

const patrimonio = ref<PatrimonioNeto | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

// --- Computed ---
const netWorthColorClass = computed(() => {
  if (!patrimonio.value) return ''
  if (patrimonio.value.total > 0) return 'text-green-600 dark:text-green-400'
  if (patrimonio.value.total < 0) return 'text-red-600 dark:text-red-400'
  return 'text-gray-900 dark:text-gray-100'
})

const hasPartialData = computed(() => {
  return patrimonio.value?.meta?.failed_count && patrimonio.value.meta.failed_count > 0
})

/** Calculate progress percentage for a value relative to a total (capped at 100%) */
function progressPercent(value: number, total: number): number {
  if (total <= 0) return 0
  return Math.min(Math.round((value / total) * 100), 100)
}

// --- API call ---
async function fetchPatrimonio() {
  loading.value = true
  error.value = null
  try {
    const data = await get<PatrimonioNeto>('/api/patrimonio')
    patrimonio.value = data
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Error al cargar el patrimonio neto.'
  } finally {
    loading.value = false
  }
}

// --- Lifecycle ---
onMounted(() => {
  fetchPatrimonio()
})
</script>

<template>
  <div class="p-6 space-y-6">
    <!-- Page header -->
    <div>
      <h1 class="text-2xl font-bold text-gray-900 dark:text-gray-100">Patrimonio Neto</h1>
      <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">
        Tu salud financiera en un vistazo
      </p>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="flex items-center justify-center py-12">
      <LoadingSpinner size="lg" label="Cargando patrimonio neto" />
    </div>

    <!-- Error state -->
    <div
      v-else-if="error"
      class="rounded-lg border border-red-300 bg-red-50 p-4 dark:border-red-600 dark:bg-red-900/30"
      role="alert"
    >
      <p class="text-sm text-red-800 dark:text-red-200">{{ error }}</p>
      <button
        type="button"
        class="mt-2 rounded-lg bg-red-100 px-3 py-1.5 text-sm font-medium text-red-800 hover:bg-red-200 focus:outline-2 focus:outline-offset-2 focus:outline-red-500 dark:bg-red-800 dark:text-red-200 dark:hover:bg-red-700"
        @click="fetchPatrimonio"
      >
        Reintentar
      </button>
    </div>

    <!-- Content -->
    <template v-else-if="patrimonio">
      <!-- Partial data warning -->
      <div
        v-if="hasPartialData"
        class="rounded-lg border border-yellow-300 bg-yellow-50 p-4 dark:border-yellow-600 dark:bg-yellow-900/30"
        role="alert"
      >
        <p class="text-sm text-yellow-800 dark:text-yellow-200">
          {{ patrimonio.meta?.failed_count }} registro(s) no pudieron ser incluidos en el calculo por errores de lectura.
        </p>
      </div>

      <!-- Net Worth Hero Card -->
      <div
        class="rounded-xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800"
      >
        <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Patrimonio Neto Total</p>
        <p :class="['mt-2 text-4xl font-bold font-mono tabular-nums', netWorthColorClass]">
          <CurrencyDisplay :amount="patrimonio.total" :colored="true" />
        </p>
        <div class="mt-4 flex flex-wrap gap-6 text-sm text-gray-600 dark:text-gray-400">
          <div class="flex items-center gap-2">
            <span class="inline-block h-3 w-3 rounded-full bg-green-500" aria-hidden="true" />
            <span>Activos: </span>
            <CurrencyDisplay :amount="patrimonio.assets.total" />
          </div>
          <div class="flex items-center gap-2">
            <span class="inline-block h-3 w-3 rounded-full bg-red-500" aria-hidden="true" />
            <span>Pasivos: </span>
            <CurrencyDisplay :amount="patrimonio.liabilities.total" />
          </div>
        </div>
      </div>

      <!-- Assets and Liabilities Grid -->
      <div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <!-- Assets Section -->
        <section aria-labelledby="assets-heading">
          <div class="rounded-xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800">
            <div class="flex items-center justify-between">
              <h2
                id="assets-heading"
                class="text-lg font-semibold text-gray-900 dark:text-gray-100"
              >
                Activos
              </h2>
              <span class="text-lg font-bold text-green-600 dark:text-green-400">
                <CurrencyDisplay :amount="patrimonio.assets.total" />
              </span>
            </div>

            <div class="mt-4 space-y-4">
              <!-- Ahorro card -->
              <div class="rounded-lg border border-gray-100 bg-gray-50 p-4 dark:border-gray-700 dark:bg-gray-900/50">
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-3">
                    <div
                      class="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-100 text-blue-600 dark:bg-blue-900/50 dark:text-blue-400"
                      aria-hidden="true"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                        <path d="M4 4a2 2 0 00-2 2v1h16V6a2 2 0 00-2-2H4z" />
                        <path fill-rule="evenodd" d="M18 9H2v5a2 2 0 002 2h12a2 2 0 002-2V9zM4 13a1 1 0 011-1h1a1 1 0 110 2H5a1 1 0 01-1-1zm5-1a1 1 0 100 2h1a1 1 0 100-2H9z" clip-rule="evenodd" />
                      </svg>
                    </div>
                    <div>
                      <p class="text-sm font-medium text-gray-900 dark:text-gray-100">Ahorro</p>
                      <p class="text-xs text-gray-500 dark:text-gray-400">Cuentas de ahorro</p>
                    </div>
                  </div>
                  <span class="text-sm font-semibold text-gray-900 dark:text-gray-100">
                    <CurrencyDisplay :amount="patrimonio.assets.ahorro" />
                  </span>
                </div>
                <!-- Progress bar -->
                <div
                  v-if="patrimonio.assets.total > 0"
                  class="mt-3 h-2 w-full overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700"
                  role="progressbar"
                  :aria-valuenow="progressPercent(patrimonio.assets.ahorro, patrimonio.assets.total)"
                  aria-valuemin="0"
                  aria-valuemax="100"
                  :aria-label="`Ahorro: ${progressPercent(patrimonio.assets.ahorro, patrimonio.assets.total)}% de los activos`"
                >
                  <div
                    class="h-full rounded-full bg-blue-500 transition-all duration-300"
                    :style="{ width: `${progressPercent(patrimonio.assets.ahorro, patrimonio.assets.total)}%` }"
                  />
                </div>
              </div>

              <!-- Afore card -->
              <div class="rounded-lg border border-gray-100 bg-gray-50 p-4 dark:border-gray-700 dark:bg-gray-900/50">
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-3">
                    <div
                      class="flex h-10 w-10 items-center justify-center rounded-lg bg-purple-100 text-purple-600 dark:bg-purple-900/50 dark:text-purple-400"
                      aria-hidden="true"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clip-rule="evenodd" />
                      </svg>
                    </div>
                    <div>
                      <p class="text-sm font-medium text-gray-900 dark:text-gray-100">Afore</p>
                      <p class="text-xs text-gray-500 dark:text-gray-400">Fondo de retiro</p>
                    </div>
                  </div>
                  <span class="text-sm font-semibold text-gray-900 dark:text-gray-100">
                    <CurrencyDisplay :amount="patrimonio.assets.afore" />
                  </span>
                </div>
                <!-- Progress bar -->
                <div
                  v-if="patrimonio.assets.total > 0"
                  class="mt-3 h-2 w-full overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700"
                  role="progressbar"
                  :aria-valuenow="progressPercent(patrimonio.assets.afore, patrimonio.assets.total)"
                  aria-valuemin="0"
                  aria-valuemax="100"
                  :aria-label="`Afore: ${progressPercent(patrimonio.assets.afore, patrimonio.assets.total)}% de los activos`"
                >
                  <div
                    class="h-full rounded-full bg-purple-500 transition-all duration-300"
                    :style="{ width: `${progressPercent(patrimonio.assets.afore, patrimonio.assets.total)}%` }"
                  />
                </div>
              </div>

              <!-- GBM card -->
              <div class="rounded-lg border border-gray-100 bg-gray-50 p-4 dark:border-gray-700 dark:bg-gray-900/50">
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-3">
                    <div
                      class="flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-100 text-emerald-600 dark:bg-emerald-900/50 dark:text-emerald-400"
                      aria-hidden="true"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M12 7a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0V8.414l-4.293 4.293a1 1 0 01-1.414 0L8 10.414l-4.293 4.293a1 1 0 01-1.414-1.414l5-5a1 1 0 011.414 0L11 10.586 14.586 7H12z" clip-rule="evenodd" />
                      </svg>
                    </div>
                    <div>
                      <p class="text-sm font-medium text-gray-900 dark:text-gray-100">GBM</p>
                      <p class="text-xs text-gray-500 dark:text-gray-400">Portafolio de inversiones</p>
                    </div>
                  </div>
                  <span class="text-sm font-semibold text-gray-900 dark:text-gray-100">
                    <CurrencyDisplay :amount="patrimonio.assets.gbm" />
                  </span>
                </div>
                <!-- Progress bar -->
                <div
                  v-if="patrimonio.assets.total > 0"
                  class="mt-3 h-2 w-full overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700"
                  role="progressbar"
                  :aria-valuenow="progressPercent(patrimonio.assets.gbm, patrimonio.assets.total)"
                  aria-valuemin="0"
                  aria-valuemax="100"
                  :aria-label="`GBM: ${progressPercent(patrimonio.assets.gbm, patrimonio.assets.total)}% de los activos`"
                >
                  <div
                    class="h-full rounded-full bg-emerald-500 transition-all duration-300"
                    :style="{ width: `${progressPercent(patrimonio.assets.gbm, patrimonio.assets.total)}%` }"
                  />
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- Liabilities Section -->
        <section aria-labelledby="liabilities-heading">
          <div class="rounded-xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800">
            <div class="flex items-center justify-between">
              <h2
                id="liabilities-heading"
                class="text-lg font-semibold text-gray-900 dark:text-gray-100"
              >
                Pasivos
              </h2>
              <span class="text-lg font-bold text-red-600 dark:text-red-400">
                <CurrencyDisplay :amount="patrimonio.liabilities.total" />
              </span>
            </div>

            <div class="mt-4 space-y-4">
              <!-- Deudas card -->
              <div class="rounded-lg border border-gray-100 bg-gray-50 p-4 dark:border-gray-700 dark:bg-gray-900/50">
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-3">
                    <div
                      class="flex h-10 w-10 items-center justify-center rounded-lg bg-red-100 text-red-600 dark:bg-red-900/50 dark:text-red-400"
                      aria-hidden="true"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clip-rule="evenodd" />
                      </svg>
                    </div>
                    <div>
                      <p class="text-sm font-medium text-gray-900 dark:text-gray-100">Deudas</p>
                      <p class="text-xs text-gray-500 dark:text-gray-400">Deudas personales</p>
                    </div>
                  </div>
                  <span class="text-sm font-semibold text-gray-900 dark:text-gray-100">
                    <CurrencyDisplay :amount="patrimonio.liabilities.deudas" />
                  </span>
                </div>
                <!-- Progress bar -->
                <div
                  v-if="patrimonio.liabilities.total > 0"
                  class="mt-3 h-2 w-full overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700"
                  role="progressbar"
                  :aria-valuenow="progressPercent(patrimonio.liabilities.deudas, patrimonio.liabilities.total)"
                  aria-valuemin="0"
                  aria-valuemax="100"
                  :aria-label="`Deudas: ${progressPercent(patrimonio.liabilities.deudas, patrimonio.liabilities.total)}% de los pasivos`"
                >
                  <div
                    class="h-full rounded-full bg-red-500 transition-all duration-300"
                    :style="{ width: `${progressPercent(patrimonio.liabilities.deudas, patrimonio.liabilities.total)}%` }"
                  />
                </div>
              </div>

              <!-- Creditos card -->
              <div class="rounded-lg border border-gray-100 bg-gray-50 p-4 dark:border-gray-700 dark:bg-gray-900/50">
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-3">
                    <div
                      class="flex h-10 w-10 items-center justify-center rounded-lg bg-orange-100 text-orange-600 dark:bg-orange-900/50 dark:text-orange-400"
                      aria-hidden="true"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                        <path d="M4 4a2 2 0 00-2 2v1h16V6a2 2 0 00-2-2H4z" />
                        <path fill-rule="evenodd" d="M18 9H2v5a2 2 0 002 2h12a2 2 0 002-2V9zM4 13a1 1 0 011-1h1a1 1 0 110 2H5a1 1 0 01-1-1zm5-1a1 1 0 100 2h1a1 1 0 100-2H9z" clip-rule="evenodd" />
                      </svg>
                    </div>
                    <div>
                      <p class="text-sm font-medium text-gray-900 dark:text-gray-100">Creditos</p>
                      <p class="text-xs text-gray-500 dark:text-gray-400">Tarjetas de credito</p>
                    </div>
                  </div>
                  <span class="text-sm font-semibold text-gray-900 dark:text-gray-100">
                    <CurrencyDisplay :amount="patrimonio.liabilities.creditos" />
                  </span>
                </div>
                <!-- Progress bar -->
                <div
                  v-if="patrimonio.liabilities.total > 0"
                  class="mt-3 h-2 w-full overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700"
                  role="progressbar"
                  :aria-valuenow="progressPercent(patrimonio.liabilities.creditos, patrimonio.liabilities.total)"
                  aria-valuemin="0"
                  aria-valuemax="100"
                  :aria-label="`Creditos: ${progressPercent(patrimonio.liabilities.creditos, patrimonio.liabilities.total)}% de los pasivos`"
                >
                  <div
                    class="h-full rounded-full bg-orange-500 transition-all duration-300"
                    :style="{ width: `${progressPercent(patrimonio.liabilities.creditos, patrimonio.liabilities.total)}%` }"
                  />
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>

      <!-- Empty state when everything is zero -->
      <div
        v-if="patrimonio.total === 0 && patrimonio.assets.total === 0 && patrimonio.liabilities.total === 0"
        class="rounded-xl border border-gray-200 bg-white p-8 text-center shadow-sm dark:border-gray-700 dark:bg-gray-800"
      >
        <p class="text-gray-600 dark:text-gray-400">
          No tienes datos financieros registrados aun. Comienza agregando registros en los modulos de Ahorro, Afore, GBM, Deudas o Creditos.
        </p>
      </div>
    </template>
  </div>
</template>
