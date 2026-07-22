<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { getInstruments, syncTasasBanxico, syncTasasNu, syncTasasStori, syncAllScrapers } from '@/services/api'
import type { Instrument } from '@/types'
import AdBanner from '@/components/AdBanner.vue'

const instruments = ref<Instrument[]>([])
const loading = ref(true)
const syncing = ref(true)
const filter = ref<string>('all')

onMounted(async () => {
  try {
    loading.value = true
    instruments.value = await getInstruments()
    loading.value = false

    syncing.value = true
    await Promise.all([
      syncTasasBanxico(),
      syncTasasNu(),
      syncTasasStori(),
      syncAllScrapers(),
    ])
    syncing.value = false

    instruments.value = await getInstruments()
  } catch (err) {
    console.error('Error cargando instrumentos:', err)
    loading.value = false
    syncing.value = false
  }
})

const filteredInstruments = computed(() => {
  if (filter.value === 'all') return instruments.value
  return instruments.value.filter((i) => i.instrument_type === filter.value)
})

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('es-MX', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}

function getTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    cuenta_ahorro: 'Cuenta de Ahorro',
    cetes: 'CETES',
    fondo: 'Fondo',
    p2p: 'P2P',
  }
  return labels[type] || type
}

function getTypeBadgeClass(type: string): string {
  const classes: Record<string, string> = {
    cuenta_ahorro: 'bg-blue-100 text-blue-700',
    cetes: 'bg-green-100 text-green-700',
    fondo: 'bg-purple-100 text-purple-700',
    p2p: 'bg-orange-100 text-orange-700',
  }
  return classes[type] || 'bg-gray-100 text-gray-700'
}
</script>

<template>
  <div class="max-w-7xl mx-auto px-2 md:px-4 py-6 md:py-8">
    <div class="text-center mb-6">
      <h1 class="text-2xl md:text-3xl font-bold text-[#2D2B6B] mb-1">Tabla de Tasas Actuales</h1>
      <p class="text-gray-400 text-sm">
        Comparativa actualizada de rendimientos en México
      </p>
    </div>

    <!-- Filtros -->
    <div class="flex flex-wrap justify-center gap-2 mb-5">
      <button
        v-for="opt in [
          { value: 'all', label: 'Todos' },
          { value: 'cuenta_ahorro', label: 'Cuentas de Ahorro' },
          { value: 'cetes', label: 'CETES' },
          { value: 'fondo', label: 'Fondos' },
          { value: 'p2p', label: 'P2P' },
        ]"
        :key="opt.value"
        @click="filter = opt.value"
        :class="[
          'px-4 py-2 rounded-full text-sm font-medium transition-all border-[1.5px]',
          filter === opt.value
            ? 'bg-[#2D2B6B] border-[#2D2B6B] text-white'
            : 'bg-transparent border-[#2D2B6B]/20 text-[#2D2B6B]/60 hover:border-[#2D2B6B]/50 hover:text-[#2D2B6B]',
        ]"
      >
        {{ opt.label }}
      </button>
    </div>

    <!-- Espacio AdSense -->
    <div class="mb-4">
      <AdBanner ad-format="auto" />
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center py-12">
      <div class="inline-block w-8 h-8 border-4 border-[#E0E0F0] border-t-[#2D2B6B] rounded-full animate-spin"></div>
      <p class="mt-4 text-gray-400">
        {{ syncing ? 'Sincronizando tasas...' : 'Cargando tasas...' }}
      </p>
    </div>

    <!-- Tabla -->
    <div v-else class="overflow-x-auto">
      <table class="w-full bg-white rounded-2xl shadow-sm border border-[#E0E0F0] overflow-hidden">
        <thead class="bg-[#2D2B6B]">
          <tr>
            <th class="px-4 md:px-5 py-3.5 text-left text-xs font-semibold text-white/80 uppercase tracking-wider">
              Instrumento
            </th>
            <th class="px-4 md:px-5 py-3.5 text-left text-xs font-semibold text-white/80 uppercase tracking-wider min-w-[140px]">
              Tipo
            </th>
            <th class="px-4 md:px-5 py-3.5 text-center text-xs font-semibold text-white/80 uppercase tracking-wider">
              Tasa Anual
            </th>
            <th class="hidden md:table-cell px-5 py-3.5 text-center text-xs font-semibold text-white/80 uppercase tracking-wider">
              Límite
            </th>
            <th class="hidden md:table-cell px-5 py-3.5 text-center text-xs font-semibold text-white/80 uppercase tracking-wider">
              Plazo
            </th>
            <th class="hidden lg:table-cell px-5 py-3.5 text-left text-xs font-semibold text-white/80 uppercase tracking-wider">
              Condiciones
            </th>
            <th class="hidden lg:table-cell px-5 py-3.5 text-center text-xs font-semibold text-white/80 uppercase tracking-wider">
              Actualizado
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-[#E0E0F0]">
          <tr
            v-for="inst in filteredInstruments"
            :key="inst.id"
            class="hover:bg-[#FAFAFE] transition-colors"
          >
            <td class="px-4 md:px-5 py-3.5">
              <a
                v-if="inst.signup_link"
                :href="inst.referral_link || inst.signup_link"
                target="_blank"
                rel="noopener noreferrer"
                class="font-medium text-[#2D2B6B] hover:text-[#F0A500] underline underline-offset-2 transition-colors"
              >
                {{ inst.name }}
              </a>
              <div v-else class="font-medium text-[#2D2B6B]">{{ inst.name }}</div>
              <div class="text-xs text-gray-400">{{ inst.institution }}</div>
            </td>
            <td class="px-4 md:px-5 py-3.5 min-w-[140px]">
              <span
                :class="['px-3 py-1 rounded-full text-xs font-medium whitespace-nowrap', getTypeBadgeClass(inst.instrument_type)]"
              >
                {{ getTypeLabel(inst.instrument_type) }}
              </span>
            </td>
            <td class="px-4 md:px-5 py-3.5 text-center">
              <span class="text-lg font-bold text-[#F0A500]">{{ inst.annual_rate }}%</span>
              <span v-if="inst.secondary_rate !== null" class="block text-xs text-gray-400">
                {{ inst.secondary_rate }}% excedente
              </span>
            </td>
            <td class="hidden md:table-cell px-5 py-3.5 text-center text-sm text-gray-500">
              <span v-if="inst.max_amount_for_rate">
                ${{ inst.max_amount_for_rate.toLocaleString('es-MX') }}
              </span>
              <span v-else class="text-gray-300">Sin límite</span>
            </td>
            <td class="hidden md:table-cell px-5 py-3.5 text-center text-sm text-gray-500">
              <span v-if="inst.term_days && inst.term_days > 0">{{ inst.term_days }} días</span>
              <span v-else-if="inst.term_days && inst.term_days === -1" class="text-[#F0A500] font-medium">Congelado</span>
              <span v-else class="text-gray-300">Líquido</span>
            </td>
            <td class="hidden lg:table-cell px-5 py-3.5 text-xs text-gray-400 max-w-xs">
              {{ inst.conditions || '—' }}
            </td>
            <td class="hidden lg:table-cell px-5 py-3.5 text-center text-xs text-gray-400">
              {{ formatDate(inst.last_updated) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <p class="text-center text-xs text-gray-400 mt-4">
      Las tasas son referenciales y se actualizan periódicamente. Verifica siempre en la fuente oficial.
    </p>

    <!-- Ad bottom -->
    <div class="mt-5">
      <AdBanner ad-format="auto" />
    </div>
  </div>
</template>
