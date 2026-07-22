<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useApi } from '../composables/useApi'
import { DataTable, CurrencyDisplay, ConfirmDialog, FormModal } from '../components/ui'
import type { TableColumn } from '../components/ui/DataTable.vue'
import type { Deudas } from '../types'
import LoadingSpinner from '../components/ui/LoadingSpinner.vue'

/**
 * DeudasPage — Full CRUD page for managing debts (deudas).
 * Displays debts in a DataTable with aggregate totals,
 * add/edit form modal, and delete confirmation dialog.
 * All text in Spanish (es-MX locale).
 *
 * Requirements: 6.1, 6.2, 6.3, 6.4, 22.1
 */

// --- API composable ---
const { get, post, put, delete: apiDelete } = useApi()

// --- State ---
const loading = ref(true)
const error = ref<string | null>(null)
const items = ref<Deudas[]>([])
const totalDebt = ref(0)
const totalMonthlyPayment = ref(0)
const failedCount = ref(0)

// --- Modal state ---
const showFormModal = ref(false)
const formLoading = ref(false)
const formError = ref<string | null>(null)
const isEditing = ref(false)
const editingId = ref<string | null>(null)

// --- Form fields ---
const formData = ref({
  creditor_name: '',
  total_amount: null as number | null,
  monthly_payment: null as number | null,
  interest_rate: null as number | null,
  start_date: '',
})

// --- Delete state ---
const showDeleteDialog = ref(false)
const deleteLoading = ref(false)
const deletingId = ref<string | null>(null)
const deletingName = ref('')

// --- Table columns ---
const columns: TableColumn[] = [
  { field: 'creditor_name', header: 'Acreedor', sortable: true },
  { field: 'total_amount', header: 'Monto Total', sortable: true },
  { field: 'monthly_payment', header: 'Pago Mensual', sortable: true },
  { field: 'interest_rate', header: 'Tasa de Interés', sortable: true },
  { field: 'remaining_balance', header: 'Saldo Restante', sortable: true },
  { field: 'estimated_payoff_date', header: 'Fecha Est. Liquidación', sortable: true },
]

// --- API Interface ---
interface DeudaListApiResponse {
  items: Deudas[]
  total_debt: number
  total_monthly_payment: number
  failed_count: number
}

// --- Data fetching ---
async function fetchDeudas() {
  loading.value = true
  error.value = null
  try {
    const data = await get<DeudaListApiResponse>('/api/deudas')
    items.value = data.items
    totalDebt.value = data.total_debt
    totalMonthlyPayment.value = data.total_monthly_payment
    failedCount.value = data.failed_count
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Error al cargar las deudas.'
  } finally {
    loading.value = false
  }
}

// --- Table data (mapped for DataTable) ---
const tableData = computed(() =>
  items.value.map((item) => ({
    ...item,
    id: item.id,
    creditor_name: item.creditor_name,
    total_amount: item.total_amount,
    monthly_payment: item.monthly_payment,
    interest_rate: item.interest_rate,
    remaining_balance: item.remaining_balance,
    estimated_payoff_date: item.estimated_payoff_date,
  })) as Record<string, unknown>[]
)

// --- Format helpers ---
function formatPayoffDate(value: string): string {
  if (value === 'indefinite') return 'Indefinido'
  if (value === 'paid') return 'Pagado'
  // ISO date string -> localized date
  try {
    const d = new Date(value)
    if (isNaN(d.getTime())) return value
    return d.toLocaleDateString('es-MX', { year: 'numeric', month: 'long', day: 'numeric' })
  } catch {
    return value
  }
}

function formatInterestRate(rate: number): string {
  return `${rate.toFixed(2)}%`
}

// --- Form actions ---
function openAddModal() {
  isEditing.value = false
  editingId.value = null
  formError.value = null
  formData.value = {
    creditor_name: '',
    total_amount: null,
    monthly_payment: null,
    interest_rate: null,
    start_date: '',
  }
  showFormModal.value = true
}

function openEditModal(row: Record<string, unknown>) {
  const deuda = row as unknown as Deudas
  isEditing.value = true
  editingId.value = deuda.id
  formError.value = null
  formData.value = {
    creditor_name: deuda.creditor_name,
    total_amount: deuda.total_amount,
    monthly_payment: deuda.monthly_payment,
    interest_rate: deuda.interest_rate,
    start_date: deuda.start_date,
  }
  showFormModal.value = true
}

async function submitForm() {
  formError.value = null

  // Basic validation
  if (!formData.value.creditor_name.trim()) {
    formError.value = 'El nombre del acreedor es obligatorio.'
    return
  }
  if (!formData.value.total_amount || formData.value.total_amount < 0.01) {
    formError.value = 'El monto total debe ser al menos $0.01.'
    return
  }
  if (!formData.value.monthly_payment || formData.value.monthly_payment < 0.01) {
    formError.value = 'El pago mensual debe ser al menos $0.01.'
    return
  }
  if (formData.value.interest_rate === null || formData.value.interest_rate < 0 || formData.value.interest_rate > 100) {
    formError.value = 'La tasa de interés debe estar entre 0% y 100%.'
    return
  }
  if (!formData.value.start_date) {
    formError.value = 'La fecha de inicio es obligatoria.'
    return
  }

  formLoading.value = true
  try {
    const payload = {
      creditor_name: formData.value.creditor_name.trim(),
      total_amount: formData.value.total_amount,
      monthly_payment: formData.value.monthly_payment,
      interest_rate: formData.value.interest_rate,
      start_date: formData.value.start_date,
    }

    if (isEditing.value && editingId.value) {
      await put(`/api/deudas/${editingId.value}`, payload)
    } else {
      await post('/api/deudas', payload)
    }

    showFormModal.value = false
    await fetchDeudas()
  } catch (e: unknown) {
    formError.value = e instanceof Error ? e.message : 'Error al guardar la deuda.'
  } finally {
    formLoading.value = false
  }
}

// --- Delete actions ---
function openDeleteDialog(row: Record<string, unknown>) {
  const deuda = row as unknown as Deudas
  deletingId.value = deuda.id
  deletingName.value = deuda.creditor_name
  showDeleteDialog.value = true
}

async function confirmDelete() {
  if (!deletingId.value) return
  deleteLoading.value = true
  try {
    await apiDelete(`/api/deudas/${deletingId.value}`)
    showDeleteDialog.value = false
    await fetchDeudas()
  } catch (e: unknown) {
    // Notification handled by interceptor
  } finally {
    deleteLoading.value = false
  }
}

// --- Lifecycle ---
onMounted(() => {
  fetchDeudas()
})
</script>

<template>
  <div class="p-6 space-y-6">
    <!-- Page header -->
    <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-gray-100">Deudas</h1>
        <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">
          Gestiona y monitorea tus deudas personales.
        </p>
      </div>
      <button
        type="button"
        class="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-2 focus:outline-offset-2 focus:outline-blue-500 dark:bg-blue-500 dark:hover:bg-blue-600"
        @click="openAddModal"
      >
        <span aria-hidden="true">+</span>
        Agregar Deuda
      </button>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="flex items-center justify-center py-12">
      <LoadingSpinner size="lg" label="Cargando deudas" />
    </div>

    <!-- Error state -->
    <div
      v-else-if="error"
      class="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800 dark:border-red-700 dark:bg-red-900/30 dark:text-red-300"
      role="alert"
    >
      <p>{{ error }}</p>
      <button
        type="button"
        class="mt-2 text-sm font-medium text-red-600 underline hover:no-underline dark:text-red-400"
        @click="fetchDeudas"
      >
        Reintentar
      </button>
    </div>

    <!-- Content -->
    <template v-else>
      <!-- Aggregate summary cards -->
      <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
          <p class="text-sm font-medium text-gray-500 dark:text-gray-400">Deuda Total</p>
          <p class="mt-1 text-2xl font-bold text-red-600 dark:text-red-400">
            <CurrencyDisplay :amount="totalDebt" />
          </p>
        </div>
        <div class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
          <p class="text-sm font-medium text-gray-500 dark:text-gray-400">Pago Mensual Total</p>
          <p class="mt-1 text-2xl font-bold text-gray-900 dark:text-gray-100">
            <CurrencyDisplay :amount="totalMonthlyPayment" />
          </p>
        </div>
      </div>

      <!-- Failed count warning -->
      <div
        v-if="failedCount > 0"
        class="rounded-lg border border-yellow-200 bg-yellow-50 p-3 text-sm text-yellow-800 dark:border-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300"
        role="alert"
      >
        {{ failedCount }} registro(s) no pudieron ser mostrados debido a un error de descifrado.
      </div>

      <!-- Data table -->
      <DataTable
        :columns="columns"
        :data="tableData"
        :loading="false"
        empty-message="No tienes deudas registradas"
      >
        <!-- Custom cell: total_amount -->
        <template #cell-total_amount="{ value }">
          <CurrencyDisplay :amount="value as number" />
        </template>

        <!-- Custom cell: monthly_payment -->
        <template #cell-monthly_payment="{ value }">
          <CurrencyDisplay :amount="value as number" />
        </template>

        <!-- Custom cell: interest_rate -->
        <template #cell-interest_rate="{ value }">
          <span class="font-mono">{{ formatInterestRate(value as number) }}</span>
        </template>

        <!-- Custom cell: remaining_balance -->
        <template #cell-remaining_balance="{ value }">
          <CurrencyDisplay :amount="value as number" />
        </template>

        <!-- Custom cell: estimated_payoff_date -->
        <template #cell-estimated_payoff_date="{ value }">
          <span
            :class="{
              'font-medium text-red-600 dark:text-red-400': value === 'indefinite',
              'font-medium text-green-600 dark:text-green-400': value === 'paid',
            }"
          >
            {{ formatPayoffDate(value as string) }}
          </span>
        </template>

        <!-- Actions column -->
        <template #actions="{ row }">
          <div class="flex items-center gap-2">
            <button
              type="button"
              class="rounded p-1 text-blue-600 hover:bg-blue-50 focus:outline-2 focus:outline-offset-2 focus:outline-blue-500 dark:text-blue-400 dark:hover:bg-blue-900/30"
              aria-label="Editar deuda"
              title="Editar"
              @click.stop="openEditModal(row)"
            >
              <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
            </button>
            <button
              type="button"
              class="rounded p-1 text-red-600 hover:bg-red-50 focus:outline-2 focus:outline-offset-2 focus:outline-red-500 dark:text-red-400 dark:hover:bg-red-900/30"
              aria-label="Eliminar deuda"
              title="Eliminar"
              @click.stop="openDeleteDialog(row)"
            >
              <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        </template>
      </DataTable>
    </template>

    <!-- Add/Edit Form Modal -->
    <FormModal
      :visible="showFormModal"
      :title="isEditing ? 'Editar Deuda' : 'Agregar Deuda'"
      @update:visible="showFormModal = $event"
    >
      <form @submit.prevent="submitForm" class="space-y-4">
        <!-- Form error -->
        <div
          v-if="formError"
          class="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800 dark:border-red-700 dark:bg-red-900/30 dark:text-red-300"
          role="alert"
        >
          {{ formError }}
        </div>

        <!-- Creditor name -->
        <div>
          <label for="creditor_name" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Nombre del Acreedor
          </label>
          <input
            id="creditor_name"
            v-model="formData.creditor_name"
            type="text"
            maxlength="100"
            required
            class="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100 dark:placeholder-gray-400"
            placeholder="Ej: Banco X, Tarjeta Y"
          />
        </div>

        <!-- Total amount -->
        <div>
          <label for="total_amount" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Monto Total de la Deuda
          </label>
          <input
            id="total_amount"
            v-model.number="formData.total_amount"
            type="number"
            min="0.01"
            max="999999999.99"
            step="0.01"
            required
            class="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100 dark:placeholder-gray-400"
            placeholder="0.00"
          />
        </div>

        <!-- Monthly payment -->
        <div>
          <label for="monthly_payment" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Pago Mensual
          </label>
          <input
            id="monthly_payment"
            v-model.number="formData.monthly_payment"
            type="number"
            min="0.01"
            max="999999999.99"
            step="0.01"
            required
            class="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100 dark:placeholder-gray-400"
            placeholder="0.00"
          />
        </div>

        <!-- Interest rate -->
        <div>
          <label for="interest_rate" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Tasa de Interés Anual (%)
          </label>
          <input
            id="interest_rate"
            v-model.number="formData.interest_rate"
            type="number"
            min="0"
            max="100"
            step="0.01"
            required
            class="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100 dark:placeholder-gray-400"
            placeholder="0.00"
          />
        </div>

        <!-- Start date -->
        <div>
          <label for="start_date" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Fecha de Inicio
          </label>
          <input
            id="start_date"
            v-model="formData.start_date"
            type="date"
            required
            class="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100 dark:placeholder-gray-400"
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
            :disabled="formLoading"
            class="inline-flex items-center rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-2 focus:outline-offset-2 focus:outline-blue-500 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-blue-500 dark:hover:bg-blue-600"
          >
            <span
              v-if="formLoading"
              class="mr-2 inline-block h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"
            />
            {{ isEditing ? 'Guardar Cambios' : 'Agregar' }}
          </button>
        </div>
      </form>

      <!-- Override footer slot to remove default cancel button -->
      <template #footer>
        <span></span>
      </template>
    </FormModal>

    <!-- Delete Confirmation Dialog -->
    <ConfirmDialog
      v-model:visible="showDeleteDialog"
      :message="`¿Estás seguro de que deseas eliminar la deuda con '${deletingName}'? Esta acción no se puede deshacer.`"
      title="Eliminar Deuda"
      severity="danger"
      confirm-label="Eliminar"
      :loading="deleteLoading"
      @confirm="confirmDelete"
      @cancel="showDeleteDialog = false"
    />
  </div>
</template>
