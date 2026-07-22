<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useApi } from '../composables/useApi'
import { CurrencyDisplay, DataTable, FormModal, ConfirmDialog, LoadingSpinner } from '../components/ui'
import type { TableColumn } from '../components/ui/DataTable.vue'
import type { Ahorro } from '../types'

// --- State ---
const { get, post, put, delete: del } = useApi()

const items = ref<Ahorro[]>([])
const totalSavings = ref(0)
const failedCount = ref(0)
const loading = ref(false)
const error = ref<string | null>(null)
const saving = ref(false)
const deleting = ref(false)

// Form modal state
const showFormModal = ref(false)
const editingItem = ref<Ahorro | null>(null)
const formData = ref({ account_name: '', amount: 0 })

// Delete confirm state
const showDeleteDialog = ref(false)
const deletingItem = ref<Ahorro | null>(null)

// --- Table columns ---
const columns: TableColumn[] = [
  { field: 'account_name', header: 'Cuenta', sortable: true },
  { field: 'amount', header: 'Monto', sortable: true },
]

// --- Computed ---
const tableData = computed(() =>
  items.value.map((item) => ({
    ...item,
    id: item.id,
    account_name: item.account_name,
    amount: item.amount,
  }))
)

const modalTitle = computed(() =>
  editingItem.value ? 'Editar Ahorro' : 'Agregar Ahorro'
)

// --- API calls ---
interface AhorroListResponse {
  items: Ahorro[]
  total_savings: number
  failed_count: number
}

async function fetchData() {
  loading.value = true
  error.value = null
  try {
    const data = await get<AhorroListResponse>('/api/ahorro')
    items.value = data.items
    totalSavings.value = data.total_savings
    failedCount.value = data.failed_count
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Error al cargar los datos de ahorro.'
  } finally {
    loading.value = false
  }
}

async function handleSave() {
  saving.value = true
  error.value = null
  try {
    if (editingItem.value) {
      await put<Ahorro>(`/api/ahorro/${editingItem.value.id}`, {
        account_name: formData.value.account_name,
        amount: formData.value.amount,
      })
    } else {
      await post<Ahorro>('/api/ahorro', {
        account_name: formData.value.account_name,
        amount: formData.value.amount,
      })
    }
    showFormModal.value = false
    await fetchData()
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Error al guardar el registro.'
  } finally {
    saving.value = false
  }
}

async function handleDelete() {
  if (!deletingItem.value) return
  deleting.value = true
  error.value = null
  try {
    await del(`/api/ahorro/${deletingItem.value.id}`)
    showDeleteDialog.value = false
    deletingItem.value = null
    await fetchData()
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Error al eliminar el registro.'
  } finally {
    deleting.value = false
  }
}

// --- Actions ---
function openAddModal() {
  editingItem.value = null
  formData.value = { account_name: '', amount: 0 }
  showFormModal.value = true
}

function openEditModal(row: Record<string, unknown>) {
  const item = items.value.find((i) => i.id === row.id)
  if (!item) return
  editingItem.value = item
  formData.value = { account_name: item.account_name, amount: item.amount }
  showFormModal.value = true
}

function openDeleteDialog(row: Record<string, unknown>) {
  const item = items.value.find((i) => i.id === row.id)
  if (!item) return
  deletingItem.value = item
  showDeleteDialog.value = true
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
        <h1 class="text-2xl font-bold text-gray-900 dark:text-gray-100">Ahorro</h1>
        <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">
          Gestiona tus cuentas de ahorro
        </p>
      </div>
      <button
        type="button"
        class="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-2 focus:outline-offset-2 focus:outline-blue-500 dark:bg-blue-500 dark:hover:bg-blue-600"
        @click="openAddModal"
      >
        <span aria-hidden="true">+</span>
        Agregar Ahorro
      </button>
    </div>

    <!-- Total savings summary -->
    <div
      v-if="!loading && items.length > 0"
      class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800"
    >
      <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Total Ahorrado</p>
      <p class="mt-1 text-3xl font-bold text-gray-900 dark:text-gray-100">
        <CurrencyDisplay :amount="totalSavings" />
      </p>
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
      <LoadingSpinner size="lg" label="Cargando ahorros" />
    </div>

    <!-- Data table -->
    <DataTable
      v-else
      :columns="columns"
      :data="tableData"
      :loading="loading"
      empty-message="No tienes cuentas de ahorro registradas"
    >
      <!-- Custom cell for amount column -->
      <template #cell-amount="{ value }">
        <CurrencyDisplay :amount="value as number" />
      </template>

      <!-- Action buttons -->
      <template #actions="{ row }">
        <div class="flex items-center gap-2">
          <button
            type="button"
            class="rounded px-2 py-1 text-sm font-medium text-blue-600 hover:bg-blue-50 focus:outline-2 focus:outline-offset-2 focus:outline-blue-500 dark:text-blue-400 dark:hover:bg-blue-900/30"
            aria-label="Editar registro"
            @click.stop="openEditModal(row)"
          >
            Editar
          </button>
          <button
            type="button"
            class="rounded px-2 py-1 text-sm font-medium text-red-600 hover:bg-red-50 focus:outline-2 focus:outline-offset-2 focus:outline-red-500 dark:text-red-400 dark:hover:bg-red-900/30"
            aria-label="Eliminar registro"
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
        <!-- Account name field -->
        <div>
          <label
            for="ahorro-account-name"
            class="block text-sm font-medium text-gray-700 dark:text-gray-300"
          >
            Nombre de la cuenta
          </label>
          <input
            id="ahorro-account-name"
            v-model="formData.account_name"
            type="text"
            maxlength="100"
            required
            class="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100 dark:focus:border-blue-400"
            placeholder="Ej: Nu México, CETES, Ualá"
          />
        </div>

        <!-- Amount field -->
        <div>
          <label
            for="ahorro-amount"
            class="block text-sm font-medium text-gray-700 dark:text-gray-300"
          >
            Monto
          </label>
          <input
            id="ahorro-amount"
            v-model.number="formData.amount"
            type="number"
            min="0.01"
            max="999999999.99"
            step="0.01"
            required
            class="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100 dark:focus:border-blue-400"
            placeholder="0.00"
          />
        </div>

        <!-- Submit button in footer area -->
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
            :disabled="saving || !formData.account_name || formData.amount <= 0"
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
      title="Eliminar Ahorro"
      :message="`¿Estás seguro de que deseas eliminar la cuenta '${deletingItem?.account_name || ''}'? Esta acción no se puede deshacer.`"
      severity="danger"
      confirm-label="Eliminar"
      :loading="deleting"
      @confirm="handleDelete"
      @cancel="showDeleteDialog = false"
    />
  </div>
</template>
