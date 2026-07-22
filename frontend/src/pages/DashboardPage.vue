<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useApi } from '../composables/useApi'
import { useFinanceStore } from '../stores/finance'
import { ModuleUpdateTracker, LoadingSpinner } from '../components/ui'
import type { ModuleUpdateStatus } from '../types'

const { get } = useApi()
const financeStore = useFinanceStore()

const modules = ref<ModuleUpdateStatus[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

// Finance summary from the store
const totalSavings = computed(() => financeStore.totalSavings)
const totalCredit = computed(() => financeStore.totalCredit)
const totalDebt = computed(() => financeStore.totalDebt)
const totalAfore = computed(() => financeStore.totalAfore)
const totalGbm = computed(() => financeStore.totalGbm)
const netWorth = computed(() => financeStore.netWorth)
const financeLoading = computed(() => financeStore.loading)

function formatCurrency(value: number): string {
  return value.toLocaleString('es-MX', {
    style: 'currency',
    currency: 'MXN',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

async function fetchUpdateTracker() {
  loading.value = true
  error.value = null
  try {
    const data = await get<ModuleUpdateStatus[]>('/api/update-tracker')
    modules.value = data
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Error al cargar el estado de los módulos.'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchUpdateTracker()
  financeStore.fetchAll()
})
</script>

<template>
  <div class="p-6 space-y-6">
    <!-- Page header -->
    <div>
      <h1 class="text-2xl font-bold text-gray-900 dark:text-gray-100">Dashboard</h1>
      <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">
        Resumen general de tus finanzas personales
      </p>
    </div>

    <!-- Error state -->
    <div
      v-if="error"
      class="rounded-lg border border-red-300 bg-red-50 p-4 dark:border-red-600 dark:bg-red-900/30"
      role="alert"
    >
      <p class="text-sm text-red-800 dark:text-red-200">{{ error }}</p>
    </div>

    <!-- Finance Summary Cards -->
    <section aria-labelledby="finance-summary-heading">
      <h2 id="finance-summary-heading" class="sr-only">Resumen financiero</h2>

      <div v-if="financeLoading" class="flex items-center justify-center py-8">
        <LoadingSpinner size="md" label="Cargando resumen financiero" />
      </div>

      <div v-else class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <!-- Net Worth -->
        <div class="rounded-lg border border-indigo-200 bg-indigo-50 p-4 dark:border-indigo-700 dark:bg-indigo-900/20">
          <p class="text-xs font-medium uppercase tracking-wide text-indigo-600 dark:text-indigo-400">
            Patrimonio Neto
          </p>
          <p class="mt-1 text-xl font-bold text-indigo-900 dark:text-indigo-100">
            {{ formatCurrency(netWorth) }}
          </p>
        </div>

        <!-- Total Savings -->
        <div class="rounded-lg border border-green-200 bg-green-50 p-4 dark:border-green-700 dark:bg-green-900/20">
          <p class="text-xs font-medium uppercase tracking-wide text-green-600 dark:text-green-400">
            Ahorro Total
          </p>
          <p class="mt-1 text-xl font-bold text-green-900 dark:text-green-100">
            {{ formatCurrency(totalSavings) }}
          </p>
        </div>

        <!-- Total Afore -->
        <div class="rounded-lg border border-blue-200 bg-blue-50 p-4 dark:border-blue-700 dark:bg-blue-900/20">
          <p class="text-xs font-medium uppercase tracking-wide text-blue-600 dark:text-blue-400">
            Afore
          </p>
          <p class="mt-1 text-xl font-bold text-blue-900 dark:text-blue-100">
            {{ formatCurrency(totalAfore) }}
          </p>
        </div>

        <!-- GBM Portfolio -->
        <div class="rounded-lg border border-purple-200 bg-purple-50 p-4 dark:border-purple-700 dark:bg-purple-900/20">
          <p class="text-xs font-medium uppercase tracking-wide text-purple-600 dark:text-purple-400">
            Portafolio GBM
          </p>
          <p class="mt-1 text-xl font-bold text-purple-900 dark:text-purple-100">
            {{ formatCurrency(totalGbm) }}
          </p>
        </div>

        <!-- Total Debt -->
        <div class="rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-700 dark:bg-red-900/20">
          <p class="text-xs font-medium uppercase tracking-wide text-red-600 dark:text-red-400">
            Deuda Total
          </p>
          <p class="mt-1 text-xl font-bold text-red-900 dark:text-red-100">
            {{ formatCurrency(totalDebt) }}
          </p>
        </div>

        <!-- Total Credit -->
        <div class="rounded-lg border border-orange-200 bg-orange-50 p-4 dark:border-orange-700 dark:bg-orange-900/20">
          <p class="text-xs font-medium uppercase tracking-wide text-orange-600 dark:text-orange-400">
            Créditos
          </p>
          <p class="mt-1 text-xl font-bold text-orange-900 dark:text-orange-100">
            {{ formatCurrency(totalCredit) }}
          </p>
        </div>
      </div>
    </section>

    <!-- Loading state for update tracker -->
    <div v-if="loading" class="flex items-center justify-center py-12">
      <LoadingSpinner size="lg" label="Cargando estado de módulos" />
    </div>

    <!-- Update tracker section -->
    <ModuleUpdateTracker
      v-else-if="modules.length > 0"
      :modules="modules"
    />
  </div>
</template>
