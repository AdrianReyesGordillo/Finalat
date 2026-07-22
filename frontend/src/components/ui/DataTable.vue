<script setup lang="ts">
import { ref, computed } from 'vue'
import LoadingSpinner from './LoadingSpinner.vue'
import EmptyState from './EmptyState.vue'

/**
 * DataTable — Generic sortable table with loading state.
 * Accepts columns (array of {field, header, sortable}), data, and loading as props.
 * Shows LoadingSpinner when loading. Supports pagination and dark mode.
 */

export interface TableColumn {
  field: string
  header: string
  sortable?: boolean
}

const props = defineProps<{
  /** Column definitions */
  columns: TableColumn[]
  /** Data rows — each row is a Record<string, unknown> */
  data: Record<string, unknown>[]
  /** Whether data is being loaded */
  loading?: boolean
  /** Items per page (default: 50) */
  pageSize?: number
  /** Optional empty state message */
  emptyMessage?: string
}>()

const emit = defineEmits<{
  (e: 'row-click', row: Record<string, unknown>): void
}>()

const currentPage = ref(1)
const sortField = ref<string | null>(null)
const sortOrder = ref<'asc' | 'desc'>('asc')

const effectivePageSize = computed(() => props.pageSize || 50)

const sortedData = computed(() => {
  if (!sortField.value) return props.data

  const field = sortField.value
  const order = sortOrder.value === 'asc' ? 1 : -1

  return [...props.data].sort((a, b) => {
    const aVal = a[field]
    const bVal = b[field]

    if (aVal == null && bVal == null) return 0
    if (aVal == null) return 1
    if (bVal == null) return -1

    if (typeof aVal === 'number' && typeof bVal === 'number') {
      return (aVal - bVal) * order
    }
    return String(aVal).localeCompare(String(bVal), 'es-MX') * order
  })
})

const totalPages = computed(() => Math.max(1, Math.ceil(sortedData.value.length / effectivePageSize.value)))

const paginatedData = computed(() => {
  const start = (currentPage.value - 1) * effectivePageSize.value
  return sortedData.value.slice(start, start + effectivePageSize.value)
})

function toggleSort(column: TableColumn) {
  if (!column.sortable) return

  if (sortField.value === column.field) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortField.value = column.field
    sortOrder.value = 'asc'
  }
  currentPage.value = 1
}

function goToPage(page: number) {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
  }
}

function getSortIndicator(column: TableColumn): string {
  if (!column.sortable) return ''
  if (sortField.value !== column.field) return ' ↕'
  return sortOrder.value === 'asc' ? ' ↑' : ' ↓'
}
</script>

<template>
  <div class="w-full overflow-hidden rounded-lg border border-gray-200 dark:border-gray-700">
    <!-- Loading state -->
    <div v-if="loading" class="flex items-center justify-center py-12">
      <LoadingSpinner size="lg" label="Cargando datos" />
    </div>

    <!-- Empty state -->
    <EmptyState
      v-else-if="!data.length"
      :message="emptyMessage || 'No hay datos disponibles'"
    />

    <!-- Table -->
    <div v-else class="overflow-x-auto">
      <table class="w-full text-left text-sm" role="grid">
        <thead class="border-b border-gray-200 bg-gray-50 text-xs uppercase text-gray-700 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300">
          <tr>
            <th
              v-for="column in columns"
              :key="column.field"
              class="px-4 py-3"
              :class="{ 'cursor-pointer select-none hover:bg-gray-100 dark:hover:bg-gray-700': column.sortable }"
              :aria-sort="sortField === column.field ? (sortOrder === 'asc' ? 'ascending' : 'descending') : undefined"
              scope="col"
              @click="toggleSort(column)"
              @keydown.enter="toggleSort(column)"
              @keydown.space.prevent="toggleSort(column)"
              :tabindex="column.sortable ? 0 : undefined"
            >
              {{ column.header }}
              <span v-if="column.sortable" aria-hidden="true" class="ml-1 text-gray-400">
                {{ getSortIndicator(column) }}
              </span>
            </th>
            <!-- Slot for action column header -->
            <th v-if="$slots.actions" class="px-4 py-3" scope="col">
              <span class="sr-only">Acciones</span>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(row, index) in paginatedData"
            :key="index"
            class="border-b border-gray-200 bg-white hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-900 dark:hover:bg-gray-800"
            @click="emit('row-click', row)"
          >
            <td
              v-for="column in columns"
              :key="column.field"
              class="px-4 py-3 text-gray-900 dark:text-gray-100"
            >
              <slot :name="`cell-${column.field}`" :row="row" :value="row[column.field]">
                {{ row[column.field] ?? '—' }}
              </slot>
            </td>
            <!-- Action column -->
            <td v-if="$slots.actions" class="px-4 py-3">
              <slot name="actions" :row="row" />
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Pagination -->
      <nav
        v-if="totalPages > 1"
        class="flex items-center justify-between border-t border-gray-200 bg-white px-4 py-3 dark:border-gray-700 dark:bg-gray-900"
        aria-label="Paginación de tabla"
      >
        <p class="text-sm text-gray-700 dark:text-gray-300">
          Mostrando {{ (currentPage - 1) * effectivePageSize + 1 }}–{{ Math.min(currentPage * effectivePageSize, sortedData.length) }}
          de {{ sortedData.length }} registros
        </p>
        <div class="flex gap-1">
          <button
            class="rounded px-3 py-1 text-sm font-medium text-gray-700 hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-50 dark:text-gray-300 dark:hover:bg-gray-800 focus:outline-2 focus:outline-offset-2 focus:outline-blue-500"
            :disabled="currentPage <= 1"
            aria-label="Página anterior"
            @click="goToPage(currentPage - 1)"
          >
            Anterior
          </button>
          <span class="flex items-center px-2 text-sm text-gray-600 dark:text-gray-400">
            {{ currentPage }} / {{ totalPages }}
          </span>
          <button
            class="rounded px-3 py-1 text-sm font-medium text-gray-700 hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-50 dark:text-gray-300 dark:hover:bg-gray-800 focus:outline-2 focus:outline-offset-2 focus:outline-blue-500"
            :disabled="currentPage >= totalPages"
            aria-label="Página siguiente"
            @click="goToPage(currentPage + 1)"
          >
            Siguiente
          </button>
        </div>
      </nav>
    </div>
  </div>
</template>
