<script setup lang="ts">
/**
 * ModuleUpdateTracker — Displays module update status with stale warnings.
 *
 * Shows each tracked financial module with:
 * - Green checkmark if up-to-date (updated within 7 days)
 * - Orange/yellow warning badge if stale (>7 days, <=30 days implied by backend stale flag)
 * - Red badge if never updated (last_updated_at is null)
 *
 * Per Requirements 17.2, 17.3, 17.4, 17.5:
 * - Display days since last update for each module
 * - Orange badge for stale modules (>30 days per requirements, but backend uses 7 days as stale)
 * - Red badge for never-updated modules
 * - "Sin actualizar" for modules with no records
 */
import { computed } from 'vue'
import type { ModuleUpdateStatus } from '../../types'

const props = defineProps<{
  modules: ModuleUpdateStatus[]
}>()

/** Module name display mapping (technical → Spanish) */
const MODULE_LABELS: Record<string, string> = {
  ahorro: 'Ahorro',
  creditos: 'Créditos',
  gastos_ingresos: 'Gastos/Ingresos',
  deudas: 'Deudas',
  aportaciones: 'Aportaciones',
  afore: 'Afore',
  gbm_portfolio: 'GBM',
}

/** Route paths for each module (matching Vue Router definitions) */
const MODULE_ROUTES: Record<string, string> = {
  ahorro: '/ahorro',
  creditos: '/creditos',
  gastos_ingresos: '/gastos-ingresos',
  deudas: '/deudas',
  aportaciones: '/aportaciones',
  afore: '/afore',
  gbm_portfolio: '/gbm-portfolio',
  gbm: '/gbm-portfolio',
}

interface ModuleDisplay {
  module_name: string
  label: string
  route: string
  last_updated_at: string | null
  stale: boolean
  daysSinceUpdate: number | null
  status: 'up-to-date' | 'stale' | 'never-updated'
}

const modulesDisplay = computed<ModuleDisplay[]>(() => {
  return props.modules.map((m) => {
    const label = MODULE_LABELS[m.module_name] || m.module_name
    const route = MODULE_ROUTES[m.module_name] || '/dashboard'

    let daysSinceUpdate: number | null = null
    let status: 'up-to-date' | 'stale' | 'never-updated' = 'never-updated'

    if (m.last_updated_at) {
      const lastUpdate = new Date(m.last_updated_at)
      const now = new Date()
      const diffMs = now.getTime() - lastUpdate.getTime()
      daysSinceUpdate = Math.floor(diffMs / (1000 * 60 * 60 * 24))

      if (m.stale) {
        status = 'stale'
      } else {
        status = 'up-to-date'
      }
    }

    return {
      module_name: m.module_name,
      label,
      route,
      last_updated_at: m.last_updated_at,
      stale: m.stale,
      daysSinceUpdate,
      status,
    }
  })
})

function formatLocalDate(isoString: string): string {
  const date = new Date(isoString)
  return date.toLocaleDateString('es-MX', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
}
</script>

<template>
  <section aria-labelledby="update-tracker-heading" class="space-y-3">
    <h2 id="update-tracker-heading" class="text-lg font-semibold text-gray-900 dark:text-gray-100">
      Estado de Módulos
    </h2>
    <p class="text-sm text-gray-600 dark:text-gray-400">
      Mantén tus módulos actualizados para un cálculo preciso de tu patrimonio.
    </p>

    <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      <router-link
        v-for="mod in modulesDisplay"
        :key="mod.module_name"
        :to="mod.route"
        class="group flex items-center gap-3 rounded-lg border p-3 transition-colors hover:shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        :class="{
          'border-green-200 bg-green-50/50 dark:border-green-800 dark:bg-green-900/20': mod.status === 'up-to-date',
          'border-yellow-200 bg-yellow-50/50 dark:border-yellow-800 dark:bg-yellow-900/20': mod.status === 'stale',
          'border-red-200 bg-red-50/50 dark:border-red-800 dark:bg-red-900/20': mod.status === 'never-updated',
        }"
        :aria-label="`${mod.label}: ${mod.status === 'never-updated' ? 'Sin actualizar' : mod.status === 'stale' ? 'Necesita actualización' : 'Actualizado'}`"
      >
        <!-- Status icon -->
        <div class="flex-shrink-0">
          <!-- Green checkmark (up-to-date) -->
          <svg
            v-if="mod.status === 'up-to-date'"
            xmlns="http://www.w3.org/2000/svg"
            class="h-6 w-6 text-green-600 dark:text-green-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            aria-hidden="true"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <!-- Orange warning (stale) -->
          <svg
            v-else-if="mod.status === 'stale'"
            xmlns="http://www.w3.org/2000/svg"
            class="h-6 w-6 text-yellow-600 dark:text-yellow-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            aria-hidden="true"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.068 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
          <!-- Red badge (never-updated) -->
          <svg
            v-else
            xmlns="http://www.w3.org/2000/svg"
            class="h-6 w-6 text-red-600 dark:text-red-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            aria-hidden="true"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>

        <!-- Module info -->
        <div class="flex-1 min-w-0">
          <p class="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
            {{ mod.label }}
          </p>

          <!-- Up-to-date message -->
          <p
            v-if="mod.status === 'up-to-date'"
            class="text-xs text-green-700 dark:text-green-300"
          >
            <template v-if="mod.daysSinceUpdate === 0">Actualizado hoy</template>
            <template v-else>Actualizado hace {{ mod.daysSinceUpdate }} {{ mod.daysSinceUpdate === 1 ? 'día' : 'días' }}</template>
          </p>

          <!-- Stale message -->
          <p
            v-else-if="mod.status === 'stale'"
            class="text-xs text-yellow-700 dark:text-yellow-300"
          >
            <span class="font-semibold">Actualiza este módulo</span>
            <span v-if="mod.daysSinceUpdate !== null"> — {{ mod.daysSinceUpdate }} días sin actualizar</span>
          </p>

          <!-- Never updated message -->
          <p
            v-else
            class="text-xs text-red-700 dark:text-red-300 font-semibold"
          >
            Sin actualizar
          </p>

          <!-- Last updated date -->
          <p
            v-if="mod.last_updated_at"
            class="text-xs text-gray-500 dark:text-gray-400 mt-0.5"
          >
            Última vez: {{ formatLocalDate(mod.last_updated_at) }}
          </p>
        </div>

        <!-- Navigate arrow -->
        <svg
          xmlns="http://www.w3.org/2000/svg"
          class="h-4 w-4 text-gray-400 group-hover:text-gray-600 dark:group-hover:text-gray-300 transition-colors flex-shrink-0"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          aria-hidden="true"
        >
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
        </svg>
      </router-link>
    </div>
  </section>
</template>
