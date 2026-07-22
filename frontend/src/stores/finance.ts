import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { apiGet } from '../composables/useApi'
import type { Ahorro, Creditos, Deudas, Afore, GbmPosition, PatrimonioNeto } from '../types'

/**
 * Per-module loading/error state tracker.
 */
interface ModuleState {
  loading: boolean
  error: string | null
  lastFetched: Date | null
}

function createModuleState(): ModuleState {
  return { loading: false, error: null, lastFetched: null }
}

/**
 * Centralized Pinia store for financial data.
 * Aggregates data from multiple backend API modules and provides
 * reactive summaries (total_savings, total_debt, etc.) for use across the app.
 */
export const useFinanceStore = defineStore('finance', () => {
  // --- Raw data ---
  const savings = ref<Ahorro[]>([])
  const credits = ref<Creditos[]>([])
  const debts = ref<Deudas[]>([])
  const afore = ref<Afore[]>([])
  const gbmPositions = ref<GbmPosition[]>([])
  const patrimonio = ref<PatrimonioNeto | null>(null)

  // --- Per-module loading/error state ---
  const savingsState = ref<ModuleState>(createModuleState())
  const creditsState = ref<ModuleState>(createModuleState())
  const debtsState = ref<ModuleState>(createModuleState())
  const aforeState = ref<ModuleState>(createModuleState())
  const gbmState = ref<ModuleState>(createModuleState())
  const patrimonioState = ref<ModuleState>(createModuleState())

  // --- Aggregate computed summaries ---
  const totalSavings = computed(() =>
    savings.value.reduce((sum, entry) => sum + entry.amount, 0)
  )

  const totalCredit = computed(() =>
    credits.value.reduce((sum, entry) => sum + entry.balance, 0)
  )

  const totalDebt = computed(() =>
    debts.value.reduce((sum, entry) => sum + entry.total_amount, 0)
  )

  const totalMonthlyPayment = computed(() =>
    debts.value.reduce((sum, entry) => sum + entry.monthly_payment, 0)
  )

  const totalAfore = computed(() =>
    afore.value.reduce((sum, entry) => sum + entry.balance, 0)
  )

  const totalGbm = computed(() =>
    gbmPositions.value.reduce((sum, pos) => sum + pos.market_value, 0)
  )

  const netWorth = computed(() => {
    if (patrimonio.value) {
      return patrimonio.value.total
    }
    // Fallback calculation from local data
    const assets = totalSavings.value + totalAfore.value + totalGbm.value
    const liabilities = totalDebt.value + totalCredit.value
    return assets - liabilities
  })

  // --- Global loading computed ---
  const loading = computed(() =>
    savingsState.value.loading ||
    creditsState.value.loading ||
    debtsState.value.loading ||
    aforeState.value.loading ||
    gbmState.value.loading ||
    patrimonioState.value.loading
  )

  // --- Individual fetch actions ---

  async function fetchSavings(): Promise<void> {
    savingsState.value.loading = true
    savingsState.value.error = null
    try {
      const data = await apiGet<Ahorro[]>('/api/ahorro')
      savings.value = data ?? []
      savingsState.value.lastFetched = new Date()
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Error al cargar ahorros'
      savingsState.value.error = message
    } finally {
      savingsState.value.loading = false
    }
  }

  async function fetchCredits(): Promise<void> {
    creditsState.value.loading = true
    creditsState.value.error = null
    try {
      const data = await apiGet<Creditos[]>('/api/creditos')
      credits.value = data ?? []
      creditsState.value.lastFetched = new Date()
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Error al cargar créditos'
      creditsState.value.error = message
    } finally {
      creditsState.value.loading = false
    }
  }

  async function fetchDebts(): Promise<void> {
    debtsState.value.loading = true
    debtsState.value.error = null
    try {
      const data = await apiGet<Deudas[]>('/api/deudas')
      debts.value = data ?? []
      debtsState.value.lastFetched = new Date()
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Error al cargar deudas'
      debtsState.value.error = message
    } finally {
      debtsState.value.loading = false
    }
  }

  async function fetchAfore(): Promise<void> {
    aforeState.value.loading = true
    aforeState.value.error = null
    try {
      const data = await apiGet<Afore[]>('/api/afore')
      afore.value = data ?? []
      aforeState.value.lastFetched = new Date()
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Error al cargar afore'
      aforeState.value.error = message
    } finally {
      aforeState.value.loading = false
    }
  }

  async function fetchGbm(): Promise<void> {
    gbmState.value.loading = true
    gbmState.value.error = null
    try {
      const data = await apiGet<GbmPosition[]>('/api/gbm')
      gbmPositions.value = data ?? []
      gbmState.value.lastFetched = new Date()
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Error al cargar portafolio GBM'
      gbmState.value.error = message
    } finally {
      gbmState.value.loading = false
    }
  }

  async function fetchPatrimonio(): Promise<void> {
    patrimonioState.value.loading = true
    patrimonioState.value.error = null
    try {
      const data = await apiGet<PatrimonioNeto>('/api/patrimonio')
      patrimonio.value = data ?? null
      patrimonioState.value.lastFetched = new Date()
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Error al cargar patrimonio'
      patrimonioState.value.error = message
    } finally {
      patrimonioState.value.loading = false
    }
  }

  // --- Aggregate fetch actions ---

  /**
   * Fetches all financial data in parallel.
   * Each module fetches independently — a failure in one does not block others.
   */
  async function fetchAll(): Promise<void> {
    await Promise.allSettled([
      fetchSavings(),
      fetchCredits(),
      fetchDebts(),
      fetchAfore(),
      fetchGbm(),
      fetchPatrimonio(),
    ])
  }

  /**
   * Alias for fetchAll — refreshes all financial modules.
   */
  async function refreshAll(): Promise<void> {
    await fetchAll()
  }

  // --- Invalidation / refresh helpers ---

  /**
   * Invalidates cached data for a specific module and re-fetches it.
   * Call this after a mutation (create/update/delete) on that module.
   */
  async function invalidateModule(module: 'savings' | 'credits' | 'debts' | 'afore' | 'gbm' | 'patrimonio'): Promise<void> {
    switch (module) {
      case 'savings':
        savings.value = []
        await fetchSavings()
        break
      case 'credits':
        credits.value = []
        await fetchCredits()
        break
      case 'debts':
        debts.value = []
        await fetchDebts()
        break
      case 'afore':
        afore.value = []
        await fetchAfore()
        break
      case 'gbm':
        gbmPositions.value = []
        await fetchGbm()
        break
      case 'patrimonio':
        patrimonio.value = null
        await fetchPatrimonio()
        break
    }
  }

  /**
   * Resets all data to initial empty state.
   * Useful on logout or when switching users.
   */
  function $reset(): void {
    savings.value = []
    credits.value = []
    debts.value = []
    afore.value = []
    gbmPositions.value = []
    patrimonio.value = null

    savingsState.value = createModuleState()
    creditsState.value = createModuleState()
    debtsState.value = createModuleState()
    aforeState.value = createModuleState()
    gbmState.value = createModuleState()
    patrimonioState.value = createModuleState()
  }

  return {
    // Raw data
    savings,
    credits,
    debts,
    afore,
    gbmPositions,
    patrimonio,

    // Per-module state
    savingsState,
    creditsState,
    debtsState,
    aforeState,
    gbmState,
    patrimonioState,

    // Aggregate summaries
    totalSavings,
    totalCredit,
    totalDebt,
    totalMonthlyPayment,
    totalAfore,
    totalGbm,
    netWorth,

    // Global loading
    loading,

    // Individual fetch actions
    fetchSavings,
    fetchCredits,
    fetchDebts,
    fetchAfore,
    fetchGbm,
    fetchPatrimonio,

    // Aggregate actions
    fetchAll,
    refreshAll,

    // Invalidation
    invalidateModule,

    // Reset
    $reset,
  }
})
