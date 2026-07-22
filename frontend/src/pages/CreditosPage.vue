<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useApi } from '../composables/useApi'
import { DataTable, CurrencyDisplay, FormModal, ConfirmDialog } from '../components/ui'
import type { TableColumn } from '../components/ui/DataTable.vue'
import type { Creditos } from '../types'
import LoadingSpinner from '../components/ui/LoadingSpinner.vue'

/**
 * CreditosPage — Credit Cards CRUD page.
 * Displays credit cards in a DataTable with utilization color coding.
 * Supports create, edit, and delete operations.
 * Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 22.1
 */

// --- State ---
const { get, post, put, delete: apiDelete } = useApi()

const items = ref<Creditos[]>([])
const totalBalance = ref(0)
const failedCount = ref(0)
const loading = ref(false)
const error = ref<string | null>(null)

// Form modal state
const showFormModal = ref(false)
const formLoading = ref(false)
const isEditing = ref(false)
const editingId = ref<string | null>(null)
const formErrors = ref<Record<string, string>>({})

// Form fields
const form = ref({
  card_name: '',
  balance: 0,
  limit: 0,
  minimum_payment: 0,
})

// Delete confirmation state
const showDeleteDialog = ref(false)
const deleteLoading = ref(false)
const deletingItem = ref<Creditos | null>(null)

// --- Table Columns ---
const columns: TableColumn[] = [
  { field: 'card_name', header: 'Tarjeta', sortable: true },
  { field: 'balance', header: 'Saldo', sortable: true },
  { field: 'limit', header: 'Límite', sortable: true },
  { field: 'minimum_payment', header: 'Pago Mínimo', sortable: true },
  { field: 'utilization', header: 'Utilización', sortable: true },
]

// --- Computed ---
const tableData = computed(() =>
  items.value.map((item) => ({
    ...item,
    _raw: item,
  }))
)

// --- API Methods ---
async function fetchCreditos() {
  loading.value = true
  error.value = null
  try {
    const response = await get<{
      items: Creditos[]
      total_balance: number
      failed_count: number
    }>('/api/creditos')
    items.value = response.items
    totalBalance.value = response.total_balance
    failedCount.value = response.failed_count
  } catch (err: unknown) {
    error.value = err instanceof Error ? err.message : 'Error al cargar las tarjetas de crédito.'
  } finally {
    loading.value = false
  }
}

async function handleSubmit() {
  formErrors.value = {}

  // Client-side validation
  if (!form.value.card_name.trim()) {
    formErrors.value.card_name = 'El nombre de la tarjeta es obligatorio.'
    return
  }
  if (form.value.card_name.length > 100) {
    formErrors.value.card_name = 'El nombre no puede exceder 100 caracteres.'
    return
  }
  if (form.value.balance < 0 || form.value.balance > 999999999.99) {
    formErrors.value.balance = 'El saldo debe estar entre $0.00 y $999,999,999.99.'
    return
  }
  if (form.value.limit < 0 || form.value.limit > 999999999.99) {
    formErrors.value.limit = 'El límite debe estar entre $0.00 y $999,999,999.99.'
    return
  }
  if (form.value.minimum_payment < 0 || form.value.minimum_payment > 999999999.99) {
    formErrors.value.minimum_payment = 'El pago mínimo debe estar entre $0.00 y $999,999,999.99.'
    return
  }

  formLoading.value = true
  try {
    const payload = {
      card_name: form.value.card_name.trim(),
      balance: form.value.balance,
      limit: form.value.limit,
      minimum_payment: form.value.minimum_payment,
    }

    if (isEditing.value && editingId.value) {
      await put(`/api/creditos/${editingId.value}`, payload)
    } else {
      await post('/api/creditos', payload)
    }

    showFormModal.value = false
    resetForm()
    await fetchCreditos()
  } catch (err: unknown) {
    formErrors.value.general = err instanceof Error ? err.message : 'Error al guardar la tarjeta.'
  } finally {
    formLoading.value = false
  }
}

async function handleDelete() {
  if (!deletingItem.value) return

  deleteLoading.value = true
  try {
    await apiDelete(`/api/creditos/${deletingItem.value.id}`)
    showDeleteDialog.value = false
    deletingItem.value = null
    await fetchCreditos()
  } catch (err: unknown) {
    error.value = err instanceof Error ? err.message : 'Error al eliminar la tarjeta.'
    showDeleteDialog.value = false
  } finally {
    deleteLoading.value = false
  }
}

// --- UI Helpers ---
function openCreateModal() {
  resetForm()
  isEditing.value = false
  editingId.value = null
  showFormModal.value = true
}

function openEditModal(row: Record<string, unknown>) {
  const item = row as unknown as Creditos
  isEditing.value = true
  editingId.value = item.id
  form.value = {
    card_name: item.card_name,
    balance: item.balance,
    limit: item.limit,
    minimum_payment: item.minimum_payment,
  }
  formErrors.value = {}
  showFormModal.value = true
}

function confirmDelete(row: Record<string, unknown>) {
  deletingItem.value = row as unknown as Creditos
  showDeleteDialog.value = true
}

function resetForm() {
  form.value = {
    card_name: '',
    balance: 0,
    limit: 0,
    minimum_payment: 0,
  }
  formErrors.value = {}
}

function getUtilizationClass(utilization: number | string): string {
  if (typeof utilization === 'string') return 'text-gray-500 dark:text-gray-400'
  if (utilization < 30) return 'text-green-600 dark:text-green-400'
  if (utilization <= 50) return 'text-yellow-600 dark:text-yellow-400'
  return 'text-red-600 dark:text-red-400'
}

function formatUtilization(utilization: number | string): string {
  if (typeof utilization === 'string') return utilization
  return `${utilization.toFixed(2)}%`
}

// --- Lifecycle ---
onMounted(() => {
  fetchCreditos()
})
</script>

<template>
  <div class="p-6 space-y-6">
    <!-- Page Header -->
    <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-gray-100">
          Tarjetas de Crédito
        </h1>
        <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">
          Gestiona tus tarjetas de crédito y monitorea tu utilización.
        </p>
      </div>
      <button
        type="button"
        class="inline-flex items-center rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-2 focus:outline-offset-2 focus:outline-blue-500 dark:bg-blue-500 dark:hover:bg-blue-600"
        @click="openCreateModal"
      >
        <span aria-hidden="true" class="mr-2">+</span>
        Agregar Tarjeta
      </button>
    </div>

    <!-- Total Balance Summary -->
    <div
      class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800"
    >
      <div class="flex items-center justify-between">
        <div>
          <p class="text-sm font-medium text-gray-600 dark:text-gray-400">
            Saldo Total de Tarjetas
          </p>
          <div v-if="loading" class="mt-1">
            <LoadingSpinner size="sm" label="Cargando saldo" />
          </div>
          <p v-else class="mt-1 text-2xl font-bold text-gray-900 dark:text-gray-100">
            <CurrencyDisplay :amount="totalBalance" />
          </p>
        </div>
        <div
          v-if="failedCount > 0"
          class="rounded-md bg-yellow-50 px-3 py-1 text-xs text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300"
          role="alert"
        >
          {{ failedCount }} registro(s) no pudieron ser mostrados
        </div>
      </div>
    </div>

    <!-- Error Alert -->
    <div
      v-if="error"
      class="rounded-lg border border-red-300 bg-red-50 p-4 text-sm text-red-700 dark:border-red-600 dark:bg-red-900/30 dark:text-red-300"
      role="alert"
    >
      <div class="flex items-center gap-2">
        <span aria-hidden="true">✕</span>
        <p>{{ error }}</p>
        <button
          type="button"
          class="ml-auto text-red-500 hover:text-red-700 dark:text-red-400 dark:hover:text-red-200"
          aria-label="Cerrar error"
          @click="error = null"
        >
          &times;
        </button>
      </div>
    </div>

    <!-- Data Table -->
    <DataTable
      :columns="columns"
      :data="tableData"
      :loading="loading"
      empty-message="No tienes tarjetas de crédito registradas. Agrega una para comenzar."
    >
      <!-- Balance cell -->
      <template #cell-balance="{ value }">
        <CurrencyDisplay :amount="value as number" />
      </template>

      <!-- Limit cell -->
      <template #cell-limit="{ value }">
        <CurrencyDisplay :amount="value as number" />
      </template>

      <!-- Minimum Payment cell -->
      <template #cell-minimum_payment="{ value }">
        <CurrencyDisplay :amount="value as number" />
      </template>

      <!-- Utilization cell with color coding -->
      <template #cell-utilization="{ value }">
        <span
          :class="['font-semibold', getUtilizationClass(value as number | string)]"
        >
          {{ formatUtilization(value as number | string) }}
        </span>
      </template>

      <!-- Actions column -->
      <template #actions="{ row }">
        <div class="flex items-center gap-2">
          <button
            type="button"
            class="rounded p-1.5 text-gray-500 hover:bg-gray-100 hover:text-blue-600 focus:outline-2 focus:outline-offset-2 focus:outline-blue-500 dark:text-gray-400 dark:hover:bg-gray-700 dark:hover:text-blue-400"
            aria-label="Editar tarjeta"
            @click.stop="openEditModal(row)"
          >
            <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
          </button>
          <button
            type="button"
            class="rounded p-1.5 text-gray-500 hover:bg-gray-100 hover:text-red-600 focus:outline-2 focus:outline-offset-2 focus:outline-red-500 dark:text-gray-400 dark:hover:bg-gray-700 dark:hover:text-red-400"
            aria-label="Eliminar tarjeta"
            @click.stop="confirmDelete(row)"
          >
            <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </template>
    </DataTable>

    <!-- Form Modal (Create/Edit) -->
    <FormModal
      v-model:visible="showFormModal"
      :title="isEditing ? 'Editar Tarjeta de Crédito' : 'Agregar Tarjeta de Crédito'"
    >
      <form @submit.prevent="handleSubmit" class="space-y-4">
        <!-- General error -->
        <div
          v-if="formErrors.general"
          class="rounded-md bg-red-50 p-3 text-sm text-red-700 dark:bg-red-900/30 dark:text-red-300"
          role="alert"
        >
          {{ formErrors.general }}
        </div>

        <!-- Card Name -->
        <div>
          <label
            for="credito-card-name"
            class="block text-sm font-medium text-gray-700 dark:text-gray-300"
          >
            Nombre de la Tarjeta
          </label>
          <input
            id="credito-card-name"
            v-model="form.card_name"
            type="text"
            maxlength="100"
            required
            class="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100 dark:focus:border-blue-400"
            placeholder="Ej: BBVA Platino"
          />
          <p v-if="formErrors.card_name" class="mt-1 text-xs text-red-600 dark:text-red-400">
            {{ formErrors.card_name }}
          </p>
        </div>

        <!-- Balance -->
        <div>
          <label
            for="credito-balance"
            class="block text-sm font-medium text-gray-700 dark:text-gray-300"
          >
            Saldo Actual
          </label>
          <div class="relative mt-1">
            <span class="absolute inset-y-0 left-0 flex items-center pl-3 text-gray-500 dark:text-gray-400">$</span>
            <input
              id="credito-balance"
              v-model.number="form.balance"
              type="number"
              step="0.01"
              min="0"
              max="999999999.99"
              required
              class="block w-full rounded-lg border border-gray-300 pl-7 pr-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100 dark:focus:border-blue-400"
              placeholder="0.00"
            />
          </div>
          <p v-if="formErrors.balance" class="mt-1 text-xs text-red-600 dark:text-red-400">
            {{ formErrors.balance }}
          </p>
        </div>

        <!-- Limit -->
        <div>
          <label
            for="credito-limit"
            class="block text-sm font-medium text-gray-700 dark:text-gray-300"
          >
            Límite de Crédito
          </label>
          <div class="relative mt-1">
            <span class="absolute inset-y-0 left-0 flex items-center pl-3 text-gray-500 dark:text-gray-400">$</span>
            <input
              id="credito-limit"
              v-model.number="form.limit"
              type="number"
              step="0.01"
              min="0"
              max="999999999.99"
              required
              class="block w-full rounded-lg border border-gray-300 pl-7 pr-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100 dark:focus:border-blue-400"
              placeholder="0.00"
            />
          </div>
          <p v-if="formErrors.limit" class="mt-1 text-xs text-red-600 dark:text-red-400">
            {{ formErrors.limit }}
          </p>
        </div>

        <!-- Minimum Payment -->
        <div>
          <label
            for="credito-min-payment"
            class="block text-sm font-medium text-gray-700 dark:text-gray-300"
          >
            Pago Mínimo
          </label>
          <div class="relative mt-1">
            <span class="absolute inset-y-0 left-0 flex items-center pl-3 text-gray-500 dark:text-gray-400">$</span>
            <input
              id="credito-min-payment"
              v-model.number="form.minimum_payment"
              type="number"
              step="0.01"
              min="0"
              max="999999999.99"
              required
              class="block w-full rounded-lg border border-gray-300 pl-7 pr-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100 dark:focus:border-blue-400"
              placeholder="0.00"
            />
          </div>
          <p v-if="formErrors.minimum_payment" class="mt-1 text-xs text-red-600 dark:text-red-400">
            {{ formErrors.minimum_payment }}
          </p>
        </div>

        <!-- Submit button (hidden, form submits via footer) -->
        <input type="submit" class="hidden" />
      </form>

      <template #footer="{ close }">
        <div class="flex justify-end gap-2">
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
            @click="handleSubmit"
          >
            <span
              v-if="formLoading"
              class="mr-2 inline-block h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"
            />
            {{ isEditing ? 'Guardar Cambios' : 'Agregar Tarjeta' }}
          </button>
        </div>
      </template>
    </FormModal>

    <!-- Delete Confirmation Dialog -->
    <ConfirmDialog
      v-model:visible="showDeleteDialog"
      title="Eliminar Tarjeta"
      :message="`¿Estás seguro de que deseas eliminar la tarjeta '${deletingItem?.card_name ?? ''}'? Esta acción no se puede deshacer.`"
      severity="danger"
      confirm-label="Eliminar"
      :loading="deleteLoading"
      @confirm="handleDelete"
      @cancel="deletingItem = null"
    />
  </div>
</template>
