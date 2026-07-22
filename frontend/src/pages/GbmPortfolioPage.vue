<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useApi } from '../composables/useApi'
import { CurrencyDisplay, DataTable, FormModal, ConfirmDialog, LoadingSpinner } from '../components/ui'
import type { TableColumn } from '../components/ui/DataTable.vue'
import type { GbmPosition } from '../types'

// --- State ---
const { get, post, put, delete: del } = useApi()

const items = ref<GbmPosition[]>([])
const totalMarketValue = ref(0)
const totalGainLossPct = ref(0)
const failedCount = ref(0)
const loading = ref(false)
const error = ref<string | null>(null)
const saving = ref(false)
const deleting = ref(false)

// Form modal state
const showFormModal = ref(false)
const editingItem = ref<GbmPosition | null>(null)
const formData = ref({
  ticker: '',
  shares: 0,
  avg_cost: 0,
  market_value: 0,
})

// Delete confirm state
const showDeleteDialog = ref(false)
const deletingItem = ref<GbmPosition | null>(null)

// --- Table columns ---
const columns: TableColumn[] = [
  { field: 'ticker', header: 'Ticker', sortable: true },
  { field: 'shares', header: 'Acciones', sortable: true },
  { field: 'avg_cost', header: 'Costo Promedio', sortable: true },
  { field: 'market_value', header: 'Valor de Mercado', sortable: true },
  { field: 'gain_loss_pct', header: 'Ganancia/Pérdida %', sortable: true },
]

// --- Computed ---
const tableData = computed(() =>
  items.value.map((item) => ({
    ...item,
    id: item.id,
    ticker: item.ticker,
    shares: item.shares,
    avg_cost: item.avg_cost,
    market_value: item.market_value,
    gain_loss_pct: item.gain_loss_pct,
  }))
)

const modalTitle = computed(() =>
  editingItem.value ? 'Editar Posición' : 'Agregar Posición'
)

const totalGainLossColorClass = computed(() => {
  if (totalGainLossPct.value > 0) return 'text-green-600 dark:text-green-400'
  if (totalGainLossPct.value < 0) return 'text-red-600 dark:text-red-400'
  return 'text-gray-900 dark:text-gray-100'
})

// --- API calls ---
interface GbmListResponse {
  items: GbmPosition[]
  total_market_value: number
  total_gain_loss_pct: number
  failed_count: number
}

async function fetchData() {
  loading.value = true
  error.value = null
  try {
    const data = await get<GbmListResponse>('/api/gbm-portfolio')
    items.value = data.items
    totalMarketValue.value = data.total_market_value
    totalGainLossPct.value = data.total_gain_loss_pct
    failedCount.value = data.failed_count
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Error al cargar el portafolio GBM.'
  } finally {
    loading.value = false
  }
}

async function handleSave() {
  saving.value = true
  error.value = null
  try {
    if (editingItem.value) {
      await put<GbmPosition>(`/api/gbm-portfolio/${editingItem.value.id}`, {
        ticker: formData.value.ticker,
        shares: formData.value.shares,
        avg_cost: formData.value.avg_cost,
        market_value: formData.value.market_value,
      })
    } else {
      await post<GbmPosition>('/api/gbm-portfolio', {
        ticker: formData.value.ticker,
        shares: formData.value.shares,
        avg_cost: formData.value.avg_cost,
        market_value: formData.value.market_value,
      })
    }
    showFormModal.value = false
    await fetchData()
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Error al guardar la posición.'
  } finally {
    saving.value = false
  }
}

async function handleDelete() {
  if (!deletingItem.value) return
  deleting.value = true
  error.value = null
  try {
    await del(`/api/gbm-portfolio/${deletingItem.value.id}`)
    showDeleteDialog.value = false
    deletingItem.value = null
    await fetchData()
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Error al eliminar la posición.'
  } finally {
    deleting.value = false
  }
}

// --- Actions ---
function openAddModal() {
  editingItem.value = null
  formData.value = { ticker: '', shares: 0, avg_cost: 0, market_value: 0 }
  showFormModal.value = true
}

function openEditModal(row: Record<string, unknown>) {
  const item = items.value.find((i) => i.id === row.id)
  if (!item) return
  editingItem.value = item
  formData.value = {
    ticker: item.ticker,
    shares: item.shares,
    avg_cost: item.avg_cost,
    market_value: item.market_value,
  }
  showFormModal.value = true
}

function openDeleteDialog(row: Record<string, unknown>) {
  const item = items.value.find((i) => i.id === row.id)
  if (!item) return
  deletingItem.value = item
  showDeleteDialog.value = true
}

function getGainLossColorClass(value: number): string {
  if (value > 0) return 'text-green-600 dark:text-green-400 font-semibold'
  if (value < 0) return 'text-red-600 dark:text-red-400 font-semibold'
  return 'text-gray-900 dark:text-gray-100'
}

function formatPercent(value: number): string {
  const sign = value > 0 ? '+' : ''
  return `${sign}${value.toFixed(2)}%`
}

// --- Lifecycle ---
onMounted(() => {
  fetchData()
})
</script>

<template>
  <div class="p-6 space-y-6">
    <!-- Page header -->
    <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-gray-100">Portafolio GBM</h1>
        <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">
          Gestiona tus posiciones de inversión en GBM
        </p>
      </div>
      <button
        type="button"
        class="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-2 focus:outline-offset-2 focus:outline-blue-500 dark:bg-blue-500 dark:hover:bg-blue-600"
        @click="openAddModal"
      >
        <span aria-hidden="true">+</span>
        Agregar Posición
      </button>
    </div>

    <!-- Aggregate summary cards -->
    <div
      v-if="!loading && items.length > 0"
      class="grid grid-cols-1 gap-4 sm:grid-cols-2"
    >
      <!-- Total Market Value -->
      <div class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
        <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Valor Total de Mercado</p>
        <p class="mt-1 text-3xl font-bold text-gray-900 dark:text-gray-100">
          <CurrencyDisplay :amount="totalMarketValue" />
        </p>
      </div>

      <!-- Total Gain/Loss Percentage -->
      <div class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
        <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Ganancia/Pérdida Total</p>
        <p class="mt-1 text-3xl font-bold" :class="totalGainLossColorClass">
          {{ formatPercent(totalGainLossPct) }}
        </p>
      </div>
    </div>

    <!-- Warning for failed decryptions -->
    <div
      v-if="failedCount > 0"
      class="rounded-lg border border-yellow-300 bg-yellow-50 p-4 dark:border-yellow-600 dark:bg-yellow-900/30"
      role="alert"
    >
      <p class="text-sm text-yellow-800 dark:text-yellow-200">
        ⚠ {{ failedCount }} registro(s) no pudieron ser mostrados por un error de lectura.
      </p>
    </div>

    <!-- Error message -->
    <div
      v-if="error"
      class="rounded-lg border border-red-300 bg-red-50 p-4 dark:border-red-600 dark:bg-red-900/30"
      role="alert"
    >
      <p class="text-sm text-red-800 dark:text-red-200">{{ error }}</p>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="flex items-center justify-center py-12">
      <LoadingSpinner size="lg" label="Cargando portafolio" />
    </div>

    <!-- Data table -->
    <DataTable
      v-else
      :columns="columns"
      :data="tableData"
      :loading="loading"
      empty-message="No tienes posiciones registradas en tu portafolio GBM"
    >
      <!-- Custom cell for avg_cost column -->
      <template #cell-avg_cost="{ value }">
        <CurrencyDisplay :amount="value as number" />
      </template>

      <!-- Custom cell for market_value column -->
      <template #cell-market_value="{ value }">
        <CurrencyDisplay :amount="value as number" />
      </template>

      <!-- Custom cell for gain_loss_pct — color coded -->
      <template #cell-gain_loss_pct="{ value }">
        <span :class="getGainLossColorClass(value as number)">
          {{ formatPercent(value as number) }}
        </span>
      </template>

      <!-- Action buttons -->
      <template #actions="{ row }">
        <div class="flex items-center gap-2">
          <button
            type="button"
            class="rounded px-2 py-1 text-sm font-medium text-blue-600 hover:bg-blue-50 focus:outline-2 focus:outline-offset-2 focus:outline-blue-500 dark:text-blue-400 dark:hover:bg-blue-900/30"
            aria-label="Editar posición"
            @click.stop="openEditModal(row)"
          >
            Editar
          </button>
          <button
            type="button"
            class="rounded px-2 py-1 text-sm font-medium text-red-600 hover:bg-red-50 focus:outline-2 focus:outline-offset-2 focus:outline-red-500 dark:text-red-400 dark:hover:bg-red-900/30"
            aria-label="Eliminar posición"
            @click.stop="openDeleteDialog(row)"
          >
            Eliminar
          </button>
        </div>
      </template>
    </DataTable>

    <!-- Form modal (Add/Edit) -->
    <FormModal
      v-model:visible="showFormModal"
      :title="modalTitle"
    >
      <form @submit.prevent="handleSave" class="space-y-4">
        <!-- Ticker field -->
        <div>
          <label
            for="gbm-ticker"
            class="block text-sm font-medium text-gray-700 dark:text-gray-300"
          >
            Ticker
          </label>
          <input
            id="gbm-ticker"
            v-model="formData.ticker"
            type="text"
            maxlength="20"
            required
            class="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900 uppercase shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100 dark:focus:border-blue-400"
            placeholder="Ej: AMZN, AAPL, VOO"
          />
        </div>

        <!-- Shares field -->
        <div>
          <label
            for="gbm-shares"
            class="block text-sm font-medium text-gray-700 dark:text-gray-300"
          >
            Acciones
          </label>
          <input
            id="gbm-shares"
            v-model.number="formData.shares"
            type="number"
            min="0.000001"
            step="0.000001"
            required
            class="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100 dark:focus:border-blue-400"
            placeholder="0"
          />
        </div>

        <!-- Average cost field -->
        <div>
          <label
            for="gbm-avg-cost"
            class="block text-sm font-medium text-gray-700 dark:text-gray-300"
          >
            Costo Promedio
          </label>
          <input
            id="gbm-avg-cost"
            v-model.number="formData.avg_cost"
            type="number"
            min="0.01"
            max="999999999.99"
            step="0.01"
            required
            class="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100 dark:focus:border-blue-400"
            placeholder="0.00"
          />
        </div>

        <!-- Market value field -->
        <div>
          <label
            for="gbm-market-value"
            class="block text-sm font-medium text-gray-700 dark:text-gray-300"
          >
            Valor de Mercado
          </label>
          <input
            id="gbm-market-value"
            v-model.number="formData.market_value"
            type="number"
            min="0.01"
            max="999999999.99"
            step="0.01"
            required
            class="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100 dark:focus:border-blue-400"
            placeholder="0.00"
          />
        </div>

        <!-- Submit button -->
        <div class="flex justify-end gap-2 pt-2">
          <button
            type="button"
            class="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-2 focus:outline-offset-2 focus:outline-blue-500 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
            @click="showFormModal = false"
          >
            Cancelar
          </button>
          <button
            type="submit"
            :disabled="saving || !formData.ticker || formData.shares <= 0 || formData.avg_cost <= 0 || formData.market_value <= 0"
            class="inline-flex items-center rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-2 focus:outline-offset-2 focus:outline-blue-500 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-blue-500 dark:hover:bg-blue-600"
          >
            <span
              v-if="saving"
              class="mr-2 inline-block h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"
            />
            {{ editingItem ? 'Guardar Cambios' : 'Agregar' }}
          </button>
        </div>
      </form>

      <!-- Override default footer since we handle it inside the form -->
      <template #footer>
        <span />
      </template>
    </FormModal>

    <!-- Delete confirmation dialog -->
    <ConfirmDialog
      v-model:visible="showDeleteDialog"
      title="Eliminar Posición"
      :message="`¿Estás seguro de que deseas eliminar la posición '${deletingItem?.ticker || ''}'? Esta acción no se puede deshacer.`"
      severity="danger"
      confirm-label="Eliminar"
      :loading="deleting"
      @confirm="handleDelete"
      @cancel="showDeleteDialog = false"
    />
  </div>
</template>
