<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useApi } from '../composables/useApi'
import { CurrencyDisplay, DataTable, ConfirmDialog, FormModal, LoadingSpinner } from '../components/ui'
import type { TableColumn } from '../components/ui/DataTable.vue'
import type { Afore } from '../types'

/**
 * AforePage — Afore (Pension Fund) management page.
 * Displays Afore entries in a DataTable with CRUD operations.
 * Shows aggregate total_balance at top.
 * Validates: Requirements 8.1, 8.2, 8.3, 22.1
 */

const { get, post, put, delete: apiDelete } = useApi()

// --- State ---
const items = ref<Afore[]>([])
const totalBalance = ref(0)
const failedCount = ref(0)
const loading = ref(false)
const error = ref<string | null>(null)

// Modal state
const showFormModal = ref(false)
const formLoading = ref(false)
const editingItem = ref<Afore | null>(null)

// Delete dialog state
const showDeleteDialog = ref(false)
const deleteLoading = ref(false)
const deletingItem = ref<Afore | null>(null)

// Form data
const form = ref({
  provider_name: '',
  balance: null as number | null,
  last_update_date: '',
})

const formErrors = ref<Record<string, string>>({})

// --- Table columns ---
const columns: TableColumn[] = [
  { field: 'provider_name', header: 'Proveedor', sortable: true },
  { field: 'balance', header: 'Saldo', sortable: true },
  { field: 'last_update_date', header: 'Última actualización', sortable: true },
]

// --- Computed ---
const isEditing = computed(() => editingItem.value !== null)
const modalTitle = computed(() => isEditing.value ? 'Editar Afore' : 'Nuevo Afore')

const tableData = computed(() =>
  items.value.map((item) => ({
    ...item,
  })) as unknown as Record<string, unknown>[]
)

// --- API Functions ---
interface AforeListResponse {
  items: Afore[]
  total_balance: number
  failed_count: number
}

async function fetchAfore() {
  loading.value = true
  error.value = null
  try {
    const response = await get<AforeListResponse>('/api/afore')
    items.value = response.items
    totalBalance.value = response.total_balance
    failedCount.value = response.failed_count
  } catch (err: unknown) {
    error.value = err instanceof Error ? err.message : 'Error al cargar los datos de Afore.'
  } finally {
    loading.value = false
  }
}

async function saveAfore() {
  formErrors.value = {}

  // Client-side validation
  if (!form.value.provider_name.trim()) {
    formErrors.value.provider_name = 'El nombre del proveedor es obligatorio'
  } else if (form.value.provider_name.length > 100) {
    formErrors.value.provider_name = 'Máximo 100 caracteres'
  }

  if (form.value.balance == null || form.value.balance < 0.01 || form.value.balance > 999999999.99) {
    formErrors.value.balance = 'El saldo debe estar entre $0.01 y $999,999,999.99'
  }

  if (!form.value.last_update_date) {
    formErrors.value.last_update_date = 'La fecha de última actualización es obligatoria'
  }

  if (Object.keys(formErrors.value).length > 0) return

  formLoading.value = true
  try {
    const payload = {
      provider_name: form.value.provider_name.trim(),
      balance: form.value.balance,
      last_update_date: form.value.last_update_date,
    }

    if (isEditing.value && editingItem.value) {
      await put(`/api/afore/${editingItem.value.id}`, payload)
    } else {
      await post('/api/afore', payload)
    }

    showFormModal.value = false
    await fetchAfore()
  } catch (err: unknown) {
    error.value = err instanceof Error ? err.message : 'Error al guardar el registro de Afore.'
  } finally {
    formLoading.value = false
  }
}

async function confirmDelete() {
  if (!deletingItem.value) return

  deleteLoading.value = true
  try {
    await apiDelete(`/api/afore/${deletingItem.value.id}`)
    showDeleteDialog.value = false
    deletingItem.value = null
    await fetchAfore()
  } catch (err: unknown) {
    error.value = err instanceof Error ? err.message : 'Error al eliminar el registro de Afore.'
  } finally {
    deleteLoading.value = false
  }
}

// --- UI Handlers ---
function openCreateModal() {
  editingItem.value = null
  form.value = {
    provider_name: '',
    balance: null,
    last_update_date: '',
  }
  formErrors.value = {}
  showFormModal.value = true
}

function openEditModal(row: Record<string, unknown>) {
  const item = row as unknown as Afore
  editingItem.value = item
  form.value = {
    provider_name: item.provider_name,
    balance: item.balance,
    last_update_date: item.last_update_date,
  }
  formErrors.value = {}
  showFormModal.value = true
}

function openDeleteDialog(row: Record<string, unknown>) {
  deletingItem.value = row as unknown as Afore
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
  fetchAfore()
})
</script>

<template>
  <div class="p-6 space-y-6">
    <!-- Page header -->
    <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-gray-100">Afore</h1>
        <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">
          Gestiona tus fondos de pensión (Afore)
        </p>
      </div>
      <button
        type="button"
        class="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-2 focus:outline-offset-2 focus:outline-blue-500 dark:bg-blue-500 dark:hover:bg-blue-600"
        @click="openCreateModal"
      >
        <span aria-hidden="true">+</span>
        Nuevo Afore
      </button>
    </div>

    <!-- Aggregate summary card -->
    <div
      v-if="!loading && items.length > 0"
      class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-900"
    >
      <div class="flex items-center justify-between">
        <div>
          <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Saldo Total Afore</p>
          <p class="mt-1 text-2xl font-bold text-gray-900 dark:text-gray-100">
            <CurrencyDisplay :amount="totalBalance" />
          </p>
        </div>
        <div
          class="flex h-12 w-12 items-center justify-center rounded-full bg-purple-100 dark:bg-purple-900/40"
          aria-hidden="true"
        >
          <svg class="h-6 w-6 text-purple-600 dark:text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
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

    <!-- Loading state -->
    <div v-if="loading" class="flex items-center justify-center py-12">
      <LoadingSpinner size="lg" label="Cargando datos de Afore" />
    </div>

    <!-- Data table -->
    <DataTable
      v-else
      :columns="columns"
      :data="tableData"
      :loading="loading"
      empty-message="No tienes registros de Afore"
    >
      <template #cell-balance="{ row }">
        <CurrencyDisplay :amount="(row as Record<string, unknown>).balance as number" />
      </template>

      <template #cell-last_update_date="{ row }">
        {{ formatDate((row as Record<string, unknown>).last_update_date as string) }}
      </template>

      <template #actions="{ row }">
        <div class="flex items-center gap-2">
          <button
            type="button"
            class="rounded p-1 text-gray-500 hover:bg-gray-100 hover:text-blue-600 focus:outline-2 focus:outline-offset-2 focus:outline-blue-500 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-blue-400"
            aria-label="Editar registro de Afore"
            @click.stop="openEditModal(row)"
          >
            <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
          </button>
          <button
            type="button"
            class="rounded p-1 text-gray-500 hover:bg-gray-100 hover:text-red-600 focus:outline-2 focus:outline-offset-2 focus:outline-red-500 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-red-400"
            aria-label="Eliminar registro de Afore"
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
      <form @submit.prevent="saveAfore" class="space-y-4">
        <!-- Provider Name -->
        <div>
          <label for="afore-provider-name" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Nombre del proveedor
          </label>
          <input
            id="afore-provider-name"
            v-model="form.provider_name"
            type="text"
            maxlength="100"
            placeholder="Ej: Profuturo, SURA, Coppel, XXI Banorte"
            class="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100 dark:placeholder-gray-500"
            :class="{ 'border-red-500 dark:border-red-500': formErrors.provider_name }"
          />
          <p v-if="formErrors.provider_name" class="mt-1 text-xs text-red-600 dark:text-red-400">
            {{ formErrors.provider_name }}
          </p>
        </div>

        <!-- Balance -->
        <div>
          <label for="afore-balance" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Saldo
          </label>
          <input
            id="afore-balance"
            v-model.number="form.balance"
            type="number"
            step="0.01"
            min="0.01"
            max="999999999.99"
            placeholder="0.00"
            class="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100 dark:placeholder-gray-500"
            :class="{ 'border-red-500 dark:border-red-500': formErrors.balance }"
          />
          <p v-if="formErrors.balance" class="mt-1 text-xs text-red-600 dark:text-red-400">
            {{ formErrors.balance }}
          </p>
        </div>

        <!-- Last Update Date -->
        <div>
          <label for="afore-last-update-date" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Fecha de última actualización
          </label>
          <input
            id="afore-last-update-date"
            v-model="form.last_update_date"
            type="date"
            class="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
            :class="{ 'border-red-500 dark:border-red-500': formErrors.last_update_date }"
          />
          <p v-if="formErrors.last_update_date" class="mt-1 text-xs text-red-600 dark:text-red-400">
            {{ formErrors.last_update_date }}
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
          @click="saveAfore"
        >
          <span v-if="formLoading" class="mr-2 inline-block h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
          {{ isEditing ? 'Guardar cambios' : 'Crear registro' }}
        </button>
      </template>
    </FormModal>

    <!-- Delete Confirmation Dialog -->
    <ConfirmDialog
      v-model:visible="showDeleteDialog"
      title="Eliminar registro de Afore"
      :message="`¿Estás seguro de eliminar el registro de '${deletingItem?.provider_name}'? Esta acción no se puede deshacer.`"
      severity="danger"
      confirm-label="Eliminar"
      :loading="deleteLoading"
      @confirm="confirmDelete"
    />
  </div>
</template>
