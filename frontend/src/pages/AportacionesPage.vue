<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useApi } from '../composables/useApi'
import { CurrencyDisplay, DataTable, ConfirmDialog, FormModal } from '../components/ui'
import type { TableColumn } from '../components/ui/DataTable.vue'
import type { Aportaciones } from '../types'

/**
 * AportacionesPage — Contributions (Aportaciones) management page.
 * Displays recurring contribution schedules in a DataTable with CRUD operations.
 * Shows aggregate total_annual_projection at top.
 * Validates: Requirements 7.1, 7.2, 7.3, 22.1
 */

const { get, post, put, delete: apiDelete } = useApi()

// --- State ---
const items = ref<Aportaciones[]>([])
const totalAnnualProjection = ref(0)
const failedCount = ref(0)
const loading = ref(false)
const error = ref<string | null>(null)

// Modal state
const showFormModal = ref(false)
const formLoading = ref(false)
const editingItem = ref<Aportaciones | null>(null)

// Delete dialog state
const showDeleteDialog = ref(false)
const deleteLoading = ref(false)
const deletingItem = ref<Aportaciones | null>(null)

// Form data
const form = ref({
  target_name: '',
  amount: null as number | null,
  frequency: 'monthly' as 'weekly' | 'biweekly' | 'monthly',
  start_date: '',
})

const formErrors = ref<Record<string, string>>({})

// --- Frequency labels ---
const frequencyLabels: Record<string, string> = {
  weekly: 'Semanal',
  biweekly: 'Quincenal',
  monthly: 'Mensual',
}

// --- Table columns ---
const columns: TableColumn[] = [
  { field: 'target_name', header: 'Destino', sortable: true },
  { field: 'amount', header: 'Monto', sortable: true },
  { field: 'frequency', header: 'Frecuencia', sortable: true },
  { field: 'start_date', header: 'Fecha inicio', sortable: true },
  { field: 'annual_projection', header: 'Proyección anual', sortable: true },
]

// --- Computed ---
const isEditing = computed(() => editingItem.value !== null)
const modalTitle = computed(() => isEditing.value ? 'Editar Aportación' : 'Nueva Aportación')

// Table data as Record[] for DataTable
const tableData = computed(() =>
  items.value.map((item) => ({
    ...item,
    frequency_label: frequencyLabels[item.frequency] || item.frequency,
  })) as unknown as Record<string, unknown>[]
)

// --- API Functions ---
async function fetchAportaciones() {
  loading.value = true
  error.value = null
  try {
    const response = await get<{
      items: Aportaciones[]
      total_annual_projection: number
      failed_count: number
    }>('/api/aportaciones')
    items.value = response.items
    totalAnnualProjection.value = response.total_annual_projection
    failedCount.value = response.failed_count
  } catch (err: unknown) {
    error.value = err instanceof Error ? err.message : 'Error al cargar las aportaciones'
  } finally {
    loading.value = false
  }
}

async function saveAportacion() {
  formErrors.value = {}

  // Client-side validation
  if (!form.value.target_name.trim()) {
    formErrors.value.target_name = 'El destino es obligatorio'
  } else if (form.value.target_name.length > 100) {
    formErrors.value.target_name = 'Máximo 100 caracteres'
  }

  if (form.value.amount == null || form.value.amount < 0.01 || form.value.amount > 999999999.99) {
    formErrors.value.amount = 'El monto debe estar entre $0.01 y $999,999,999.99'
  }

  if (!['weekly', 'biweekly', 'monthly'].includes(form.value.frequency)) {
    formErrors.value.frequency = 'Selecciona una frecuencia válida'
  }

  if (!form.value.start_date) {
    formErrors.value.start_date = 'La fecha de inicio es obligatoria'
  }

  if (Object.keys(formErrors.value).length > 0) return

  formLoading.value = true
  try {
    const payload = {
      target_name: form.value.target_name.trim(),
      amount: form.value.amount,
      frequency: form.value.frequency,
      start_date: form.value.start_date,
    }

    if (isEditing.value && editingItem.value) {
      await put(`/api/aportaciones/${editingItem.value.id}`, payload)
    } else {
      await post('/api/aportaciones', payload)
    }

    showFormModal.value = false
    await fetchAportaciones()
  } catch (err: unknown) {
    error.value = err instanceof Error ? err.message : 'Error al guardar la aportación'
  } finally {
    formLoading.value = false
  }
}

async function confirmDelete() {
  if (!deletingItem.value) return

  deleteLoading.value = true
  try {
    await apiDelete(`/api/aportaciones/${deletingItem.value.id}`)
    showDeleteDialog.value = false
    deletingItem.value = null
    await fetchAportaciones()
  } catch (err: unknown) {
    error.value = err instanceof Error ? err.message : 'Error al eliminar la aportación'
  } finally {
    deleteLoading.value = false
  }
}

// --- UI Handlers ---
function openCreateModal() {
  editingItem.value = null
  form.value = {
    target_name: '',
    amount: null,
    frequency: 'monthly',
    start_date: '',
  }
  formErrors.value = {}
  showFormModal.value = true
}

function openEditModal(row: Record<string, unknown>) {
  const item = row as unknown as Aportaciones
  editingItem.value = item
  form.value = {
    target_name: item.target_name,
    amount: item.amount,
    frequency: item.frequency,
    start_date: item.start_date,
  }
  formErrors.value = {}
  showFormModal.value = true
}

function openDeleteDialog(row: Record<string, unknown>) {
  deletingItem.value = row as unknown as Aportaciones
  showDeleteDialog.value = true
}

function formatDate(dateStr: string): string {
  if (!dateStr) return '—'
  const date = new Date(dateStr + 'T00:00:00')
  return date.toLocaleDateString('es-MX', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
}

// --- Lifecycle ---
onMounted(() => {
  fetchAportaciones()
})
</script>

<template>
  <div class="p-6 space-y-6">
    <!-- Page header -->
    <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-gray-100">Aportaciones</h1>
        <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">
          Gestiona tus contribuciones recurrentes
        </p>
      </div>
      <button
        type="button"
        class="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-2 focus:outline-offset-2 focus:outline-blue-500 dark:bg-blue-500 dark:hover:bg-blue-600"
        @click="openCreateModal"
      >
        <span aria-hidden="true">+</span>
        Nueva Aportación
      </button>
    </div>

    <!-- Aggregate summary card -->
    <div class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-900">
      <div class="flex items-center justify-between">
        <div>
          <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Proyección Anual Total</p>
          <p class="mt-1 text-2xl font-bold text-gray-900 dark:text-gray-100">
            <CurrencyDisplay :amount="totalAnnualProjection" />
          </p>
        </div>
        <div
          class="flex h-12 w-12 items-center justify-center rounded-full bg-green-100 dark:bg-green-900/40"
          aria-hidden="true"
        >
          <svg class="h-6 w-6 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
          </svg>
        </div>
      </div>
    </div>

    <!-- Error message -->
    <div
      v-if="error"
      class="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/30 dark:text-red-400"
      role="alert"
    >
      {{ error }}
      <button
        type="button"
        class="ml-2 font-medium underline hover:no-underline"
        @click="error = null"
      >
        Cerrar
      </button>
    </div>

    <!-- Failed count warning -->
    <div
      v-if="failedCount > 0"
      class="rounded-lg border border-yellow-200 bg-yellow-50 p-4 text-sm text-yellow-700 dark:border-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400"
      role="alert"
    >
      {{ failedCount }} registro(s) no pudieron ser mostrados debido a errores de descifrado.
    </div>

    <!-- Data table -->
    <DataTable
      :columns="columns"
      :data="tableData"
      :loading="loading"
      empty-message="No tienes aportaciones registradas"
    >
      <template #cell-amount="{ row }">
        <CurrencyDisplay :amount="(row as Record<string, unknown>).amount as number" />
      </template>

      <template #cell-frequency="{ row }">
        {{ (row as Record<string, unknown>).frequency_label }}
      </template>

      <template #cell-start_date="{ row }">
        {{ formatDate((row as Record<string, unknown>).start_date as string) }}
      </template>

      <template #cell-annual_projection="{ row }">
        <CurrencyDisplay :amount="(row as Record<string, unknown>).annual_projection as number" />
      </template>

      <template #actions="{ row }">
        <div class="flex items-center gap-2">
          <button
            type="button"
            class="rounded p-1 text-gray-500 hover:bg-gray-100 hover:text-blue-600 focus:outline-2 focus:outline-offset-2 focus:outline-blue-500 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-blue-400"
            aria-label="Editar aportación"
            @click.stop="openEditModal(row)"
          >
            <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
          </button>
          <button
            type="button"
            class="rounded p-1 text-gray-500 hover:bg-gray-100 hover:text-red-600 focus:outline-2 focus:outline-offset-2 focus:outline-red-500 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-red-400"
            aria-label="Eliminar aportación"
            @click.stop="openDeleteDialog(row)"
          >
            <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </template>
    </DataTable>

    <!-- Add/Edit Form Modal -->
    <FormModal
      v-model:visible="showFormModal"
      :title="modalTitle"
    >
      <form @submit.prevent="saveAportacion" class="space-y-4">
        <!-- Target Name -->
        <div>
          <label for="aportacion-target" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Destino
          </label>
          <input
            id="aportacion-target"
            v-model="form.target_name"
            type="text"
            maxlength="100"
            placeholder="Ej: CETES, Nu México, Fondo de emergencia"
            class="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100 dark:placeholder-gray-500"
            :class="{ 'border-red-500 dark:border-red-500': formErrors.target_name }"
          />
          <p v-if="formErrors.target_name" class="mt-1 text-xs text-red-600 dark:text-red-400">
            {{ formErrors.target_name }}
          </p>
        </div>

        <!-- Amount -->
        <div>
          <label for="aportacion-amount" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Monto
          </label>
          <input
            id="aportacion-amount"
            v-model.number="form.amount"
            type="number"
            step="0.01"
            min="0.01"
            max="999999999.99"
            placeholder="0.00"
            class="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100 dark:placeholder-gray-500"
            :class="{ 'border-red-500 dark:border-red-500': formErrors.amount }"
          />
          <p v-if="formErrors.amount" class="mt-1 text-xs text-red-600 dark:text-red-400">
            {{ formErrors.amount }}
          </p>
        </div>

        <!-- Frequency -->
        <div>
          <label for="aportacion-frequency" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Frecuencia
          </label>
          <select
            id="aportacion-frequency"
            v-model="form.frequency"
            class="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
            :class="{ 'border-red-500 dark:border-red-500': formErrors.frequency }"
          >
            <option value="weekly">Semanal</option>
            <option value="biweekly">Quincenal</option>
            <option value="monthly">Mensual</option>
          </select>
          <p v-if="formErrors.frequency" class="mt-1 text-xs text-red-600 dark:text-red-400">
            {{ formErrors.frequency }}
          </p>
        </div>

        <!-- Start Date -->
        <div>
          <label for="aportacion-start-date" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Fecha de inicio
          </label>
          <input
            id="aportacion-start-date"
            v-model="form.start_date"
            type="date"
            class="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
            :class="{ 'border-red-500 dark:border-red-500': formErrors.start_date }"
          />
          <p v-if="formErrors.start_date" class="mt-1 text-xs text-red-600 dark:text-red-400">
            {{ formErrors.start_date }}
          </p>
        </div>
      </form>

      <template #footer="{ close }">
        <button
          type="button"
          class="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-2 focus:outline-offset-2 focus:outline-blue-500 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
          @click="close"
        >
          Cancelar
        </button>
        <button
          type="button"
          class="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-2 focus:outline-offset-2 focus:outline-blue-500 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-blue-500 dark:hover:bg-blue-600"
          :disabled="formLoading"
          @click="saveAportacion"
        >
          <span v-if="formLoading" class="mr-2 inline-block h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
          {{ isEditing ? 'Guardar cambios' : 'Crear aportación' }}
        </button>
      </template>
    </FormModal>

    <!-- Delete Confirmation Dialog -->
    <ConfirmDialog
      v-model:visible="showDeleteDialog"
      title="Eliminar aportación"
      :message="`¿Estás seguro de eliminar la aportación a '${deletingItem?.target_name}'? Esta acción no se puede deshacer.`"
      severity="danger"
      confirm-label="Eliminar"
      :loading="deleteLoading"
      @confirm="confirmDelete"
    />
  </div>
</template>
