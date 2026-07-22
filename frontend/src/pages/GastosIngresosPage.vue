<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useApi } from '../composables/useApi'
import { DataTable, ConfirmDialog, FormModal, CurrencyDisplay, LoadingSpinner } from '../components/ui'
import type { TableColumn } from '../components/ui/DataTable.vue'
import type { GastosIngresos, Category } from '../types'

// --- API ---
const { get, post, put, delete: apiDelete } = useApi()

// --- State ---
const entries = ref<GastosIngresos[]>([])
const categories = ref<Category[]>([])
const totalIncome = ref<number>(0)
const totalExpense = ref<number>(0)
const failedCount = ref<number>(0)
const loading = ref(false)
const error = ref<string | null>(null)

// --- Modal state ---
const showFormModal = ref(false)
const formLoading = ref(false)
const editingEntry = ref<GastosIngresos | null>(null)

// --- Delete confirmation ---
const showDeleteDialog = ref(false)
const deletingEntry = ref<GastosIngresos | null>(null)
const deleteLoading = ref(false)

// --- Form data ---
const form = ref({
  type: 'expense' as 'income' | 'expense',
  amount: '',
  description: '',
  category_id: '',
  entry_date: '',
})

const formErrors = ref<Record<string, string>>({})

// --- Computed ---
const tableColumns: TableColumn[] = [
  { field: 'type', header: 'Tipo' },
  { field: 'description', header: 'Descripción', sortable: true },
  { field: 'amount', header: 'Monto', sortable: true },
  { field: 'category_name', header: 'Categoría', sortable: true },
  { field: 'entry_date', header: 'Fecha', sortable: true },
]

const tableData = computed(() =>
  entries.value.map((entry) => ({
    ...entry,
    amount: Number(entry.amount),
  }))
)

const modalTitle = computed(() =>
  editingEntry.value ? 'Editar Registro' : 'Nuevo Registro'
)

// --- Methods ---
async function fetchEntries() {
  loading.value = true
  error.value = null
  try {
    const data = await get<{
      items: GastosIngresos[]
      total_income: string
      total_expense: string
      failed_count: number
    }>('/api/gastos-ingresos')
    entries.value = data.items
    totalIncome.value = parseFloat(data.total_income)
    totalExpense.value = parseFloat(data.total_expense)
    failedCount.value = data.failed_count
  } catch (err: unknown) {
    error.value = err instanceof Error ? err.message : 'Error al cargar los datos'
  } finally {
    loading.value = false
  }
}

async function fetchCategories() {
  try {
    const data = await get<Category[]>('/api/categories')
    categories.value = data
  } catch {
    // Categories fetch failure is non-blocking
  }
}

function openCreateModal() {
  editingEntry.value = null
  form.value = {
    type: 'expense',
    amount: '',
    description: '',
    category_id: '',
    entry_date: new Date().toISOString().slice(0, 10),
  }
  formErrors.value = {}
  showFormModal.value = true
}

function openEditModal(row: Record<string, unknown>) {
  const entry = row as unknown as GastosIngresos
  editingEntry.value = entry
  form.value = {
    type: entry.type,
    amount: String(entry.amount),
    description: entry.description,
    category_id: entry.category_id,
    entry_date: entry.entry_date,
  }
  formErrors.value = {}
  showFormModal.value = true
}

function validateForm(): boolean {
  const errors: Record<string, string> = {}

  if (!form.value.type) {
    errors.type = 'Selecciona un tipo'
  }

  const amount = parseFloat(form.value.amount)
  if (!form.value.amount || isNaN(amount) || amount < 0.01 || amount > 999999999.99) {
    errors.amount = 'Ingresa un monto válido (0.01 - 999,999,999.99)'
  }

  if (!form.value.description.trim()) {
    errors.description = 'La descripción es requerida'
  } else if (form.value.description.length > 500) {
    errors.description = 'Máximo 500 caracteres'
  }

  if (!form.value.category_id) {
    errors.category_id = 'Selecciona una categoría'
  }

  if (!form.value.entry_date) {
    errors.entry_date = 'Selecciona una fecha'
  }

  formErrors.value = errors
  return Object.keys(errors).length === 0
}

async function submitForm() {
  if (!validateForm()) return

  formLoading.value = true
  try {
    const payload = {
      type: form.value.type,
      amount: parseFloat(form.value.amount),
      description: form.value.description.trim(),
      category_id: form.value.category_id,
      entry_date: form.value.entry_date,
    }

    if (editingEntry.value) {
      await put(`/api/gastos-ingresos/${editingEntry.value.id}`, payload)
    } else {
      await post('/api/gastos-ingresos', payload)
    }

    showFormModal.value = false
    await fetchEntries()
  } catch (err: unknown) {
    formErrors.value.general = err instanceof Error ? err.message : 'Error al guardar'
  } finally {
    formLoading.value = false
  }
}

function confirmDelete(row: Record<string, unknown>) {
  deletingEntry.value = row as unknown as GastosIngresos
  showDeleteDialog.value = true
}

async function executeDelete() {
  if (!deletingEntry.value) return

  deleteLoading.value = true
  try {
    await apiDelete(`/api/gastos-ingresos/${deletingEntry.value.id}`)
    showDeleteDialog.value = false
    deletingEntry.value = null
    await fetchEntries()
  } catch (err: unknown) {
    error.value = err instanceof Error ? err.message : 'Error al eliminar'
  } finally {
    deleteLoading.value = false
  }
}

function formatDate(dateStr: string): string {
  if (!dateStr) return '—'
  const [year, month, day] = dateStr.split('-')
  return `${day}/${month}/${year}`
}

// --- Lifecycle ---
onMounted(() => {
  fetchEntries()
  fetchCategories()
})
</script>

<template>
  <div class="p-6 space-y-6">
    <!-- Header -->
    <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-gray-100">
        Gastos e Ingresos
      </h1>
      <button
        type="button"
        class="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-2 focus:outline-offset-2 focus:outline-blue-500 dark:bg-blue-500 dark:hover:bg-blue-600"
        @click="openCreateModal"
      >
        <span aria-hidden="true">+</span>
        Nuevo Registro
      </button>
    </div>

    <!-- Summary cards -->
    <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <!-- Total Income -->
      <div class="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
        <p class="text-sm font-medium text-gray-500 dark:text-gray-400">Total Ingresos</p>
        <p class="mt-1 text-2xl font-bold text-green-600 dark:text-green-400">
          <CurrencyDisplay :amount="totalIncome" />
        </p>
      </div>
      <!-- Total Expenses -->
      <div class="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
        <p class="text-sm font-medium text-gray-500 dark:text-gray-400">Total Gastos</p>
        <p class="mt-1 text-2xl font-bold text-red-600 dark:text-red-400">
          <CurrencyDisplay :amount="totalExpense" />
        </p>
      </div>
      <!-- Balance -->
      <div class="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
        <p class="text-sm font-medium text-gray-500 dark:text-gray-400">Balance</p>
        <p class="mt-1 text-2xl font-bold">
          <CurrencyDisplay :amount="totalIncome - totalExpense" :colored="true" />
        </p>
      </div>
    </div>

    <!-- Warning for failed decryptions -->
    <div
      v-if="failedCount > 0"
      class="rounded-lg border border-yellow-300 bg-yellow-50 p-3 text-sm text-yellow-800 dark:border-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300"
      role="alert"
    >
      {{ failedCount }} registro(s) no pudieron ser mostrados debido a un error de procesamiento.
    </div>

    <!-- Error state -->
    <div
      v-if="error"
      class="rounded-lg border border-red-300 bg-red-50 p-3 text-sm text-red-800 dark:border-red-700 dark:bg-red-900/30 dark:text-red-300"
      role="alert"
    >
      {{ error }}
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="flex justify-center py-12">
      <LoadingSpinner size="lg" label="Cargando gastos e ingresos" />
    </div>

    <!-- Data Table -->
    <DataTable
      v-else
      :columns="tableColumns"
      :data="(tableData as unknown as Record<string, unknown>[])"
      :loading="loading"
      empty-message="No hay registros de gastos o ingresos"
      @row-click="openEditModal"
    >
      <!-- Type badge -->
      <template #cell-type="{ value }">
        <span
          :class="[
            'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
            value === 'income'
              ? 'bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300'
              : 'bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300',
          ]"
        >
          {{ value === 'income' ? 'Ingreso' : 'Gasto' }}
        </span>
      </template>

      <!-- Amount display -->
      <template #cell-amount="{ value }">
        <CurrencyDisplay :amount="value as number" />
      </template>

      <!-- Date formatted -->
      <template #cell-entry_date="{ value }">
        {{ formatDate(value as string) }}
      </template>

      <!-- Actions column -->
      <template #actions="{ row }">
        <div class="flex items-center gap-2">
          <button
            type="button"
            class="rounded p-1 text-gray-500 hover:bg-gray-100 hover:text-blue-600 focus:outline-2 focus:outline-offset-2 focus:outline-blue-500 dark:text-gray-400 dark:hover:bg-gray-700 dark:hover:text-blue-400"
            aria-label="Editar registro"
            @click.stop="openEditModal(row)"
          >
            <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
          </button>
          <button
            type="button"
            class="rounded p-1 text-gray-500 hover:bg-gray-100 hover:text-red-600 focus:outline-2 focus:outline-offset-2 focus:outline-red-500 dark:text-gray-400 dark:hover:bg-gray-700 dark:hover:text-red-400"
            aria-label="Eliminar registro"
            @click.stop="confirmDelete(row)"
          >
            <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </template>
    </DataTable>

    <!-- Create/Edit Form Modal -->
    <FormModal
      v-model:visible="showFormModal"
      :title="modalTitle"
    >
      <form @submit.prevent="submitForm" class="space-y-4">
        <!-- General error -->
        <div
          v-if="formErrors.general"
          class="rounded-lg border border-red-300 bg-red-50 p-3 text-sm text-red-800 dark:border-red-700 dark:bg-red-900/30 dark:text-red-300"
          role="alert"
        >
          {{ formErrors.general }}
        </div>

        <!-- Type select -->
        <div>
          <label for="entry-type" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Tipo
          </label>
          <select
            id="entry-type"
            v-model="form.type"
            class="mt-1 block w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
            :class="{ 'border-red-500': formErrors.type }"
          >
            <option value="expense">Gasto</option>
            <option value="income">Ingreso</option>
          </select>
          <p v-if="formErrors.type" class="mt-1 text-xs text-red-600 dark:text-red-400">
            {{ formErrors.type }}
          </p>
        </div>

        <!-- Amount -->
        <div>
          <label for="entry-amount" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Monto
          </label>
          <input
            id="entry-amount"
            v-model="form.amount"
            type="number"
            step="0.01"
            min="0.01"
            max="999999999.99"
            placeholder="0.00"
            class="mt-1 block w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
            :class="{ 'border-red-500': formErrors.amount }"
          />
          <p v-if="formErrors.amount" class="mt-1 text-xs text-red-600 dark:text-red-400">
            {{ formErrors.amount }}
          </p>
        </div>

        <!-- Description -->
        <div>
          <label for="entry-description" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Descripción
          </label>
          <input
            id="entry-description"
            v-model="form.description"
            type="text"
            maxlength="500"
            placeholder="Descripción del movimiento"
            class="mt-1 block w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
            :class="{ 'border-red-500': formErrors.description }"
          />
          <p v-if="formErrors.description" class="mt-1 text-xs text-red-600 dark:text-red-400">
            {{ formErrors.description }}
          </p>
        </div>

        <!-- Category select -->
        <div>
          <label for="entry-category" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Categoría
          </label>
          <select
            id="entry-category"
            v-model="form.category_id"
            class="mt-1 block w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
            :class="{ 'border-red-500': formErrors.category_id }"
          >
            <option value="" disabled>Selecciona una categoría</option>
            <option
              v-for="cat in categories"
              :key="cat.id"
              :value="cat.id"
            >
              {{ cat.name }}
            </option>
          </select>
          <p v-if="formErrors.category_id" class="mt-1 text-xs text-red-600 dark:text-red-400">
            {{ formErrors.category_id }}
          </p>
        </div>

        <!-- Entry date -->
        <div>
          <label for="entry-date" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Fecha
          </label>
          <input
            id="entry-date"
            v-model="form.entry_date"
            type="date"
            class="mt-1 block w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
            :class="{ 'border-red-500': formErrors.entry_date }"
          />
          <p v-if="formErrors.entry_date" class="mt-1 text-xs text-red-600 dark:text-red-400">
            {{ formErrors.entry_date }}
          </p>
        </div>
      </form>

      <!-- Footer -->
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
          class="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-2 focus:outline-offset-2 focus:outline-blue-500 disabled:opacity-50 disabled:cursor-not-allowed dark:bg-blue-500 dark:hover:bg-blue-600"
          :disabled="formLoading"
          @click="submitForm"
        >
          <span v-if="formLoading" class="mr-2 inline-block h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
          {{ editingEntry ? 'Guardar Cambios' : 'Crear Registro' }}
        </button>
      </template>
    </FormModal>

    <!-- Delete Confirmation Dialog -->
    <ConfirmDialog
      v-model:visible="showDeleteDialog"
      title="Eliminar Registro"
      :message="`¿Estás seguro de que deseas eliminar este registro? Esta acción no se puede deshacer.`"
      severity="danger"
      confirm-label="Eliminar"
      :loading="deleteLoading"
      @confirm="executeDelete"
    />
  </div>
</template>
