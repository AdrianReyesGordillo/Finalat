<script setup>
import { ref, computed } from 'vue'

const categories = ref([
  {
    category: 'Afore', person: '', amount: 500, color: '#10b981', frequency: 'semanal',
    weeks: [
      { id: '1', weekStart: '2026-07-07', weekEnd: '2026-07-13', status: 'realizada' },
      { id: '2', weekStart: '2026-07-14', weekEnd: '2026-07-20', status: 'realizada' },
      { id: '3', weekStart: '2026-07-21', weekEnd: '2026-07-27', status: 'pendiente' },
      { id: '4', weekStart: '2026-07-28', weekEnd: '2026-08-03', status: 'pendiente' },
    ]
  },
  {
    category: 'GBM', person: '', amount: 1000, color: '#1da1f2', frequency: 'quincenal',
    weeks: [
      { id: '5', weekStart: '2026-07-01', weekEnd: '2026-07-15', status: 'realizada' },
      { id: '6', weekStart: '2026-07-16', weekEnd: '2026-07-31', status: 'pendiente' },
    ]
  },
])

const showModal = ref(false)
const editingWeek = ref({})
const selectedStatus = ref('pendiente')
const saving = ref(false)

const statusOptions = [
  { value: 'realizada', label: 'Realizada', icon: 'pi pi-check-circle' },
  { value: 'pendiente', label: 'Pendiente', icon: 'pi pi-clock' },
]

function frequencyShort(freq) {
  const labels = { semanal: 'sem', quincenal: 'qna', mensual: 'mes' }
  return labels[freq] || 'periodo'
}

function statusLabel(status) {
  const labels = { realizada: 'Realizada', pendiente: 'Pendiente', atrasada: 'Atrasada' }
  return labels[status] || status
}

function formatPeriodRange(start, end) {
  const s = new Date(start + 'T00:00:00')
  const e = new Date(end + 'T00:00:00')
  const opts = { day: '2-digit', month: 'short' }
  return `${s.toLocaleDateString('es-MX', opts)} - ${e.toLocaleDateString('es-MX', opts)}`
}

function openModal(week) {
  editingWeek.value = week
  selectedStatus.value = week.status
  showModal.value = true
}

function saveStatus() {
  saving.value = true
  setTimeout(() => {
    editingWeek.value.status = selectedStatus.value
    showModal.value = false
    saving.value = false
  }, 400)
}
</script>

<template>
  <div class="demo-ap">
    <div class="demo-label"><span class="demo-badge">Demo interactiva</span> Marca tus aportaciones como realizadas y observa tu progreso.</div>

    <h2 class="page-title">Aportaciones</h2>

    <!-- Month nav -->
    <div class="month-nav">
      <button class="btn-nav"><i class="pi pi-chevron-left"></i></button>
      <span class="month-label">Julio 2026</span>
      <button class="btn-nav"><i class="pi pi-chevron-right"></i></button>
    </div>

    <!-- Categories -->
    <div class="categories-grid">
      <div v-for="cat in categories" :key="cat.category" class="category-card">
        <div class="category-header">
          <div class="category-title">
            <span class="category-dot" :style="{ backgroundColor: cat.color }"></span>
            <span>{{ cat.category }}</span>
            <span v-if="cat.person" class="category-person">— {{ cat.person }}</span>
          </div>
          <span class="category-amount">${{ cat.amount }}/{{ frequencyShort(cat.frequency) }}</span>
        </div>

        <div class="weeks-table">
          <div class="week-row week-header">
            <span class="week-cell week-label-cell">Periodo</span>
            <span class="week-cell">Estado</span>
            <span class="week-cell week-action-cell"></span>
          </div>
          <div v-for="week in cat.weeks" :key="week.id" class="week-row">
            <span class="week-cell week-label-cell">{{ formatPeriodRange(week.weekStart, week.weekEnd) }}</span>
            <span class="week-cell"><span class="status-badge" :class="week.status">{{ statusLabel(week.status) }}</span></span>
            <span class="week-cell week-action-cell"><button class="btn-edit" @click="openModal(week)"><i class="pi pi-pencil"></i></button></span>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="upload-modal modal-sm">
        <div class="upload-modal-header">
          <h3><i class="pi pi-pencil"></i> Actualizar Estado</h3>
          <button class="btn-close" @click="showModal = false"><i class="pi pi-times"></i></button>
        </div>
        <div class="upload-modal-body">
          <p class="upload-hint">Semana: <strong>{{ formatPeriodRange(editingWeek.weekStart, editingWeek.weekEnd) }}</strong></p>
          <div class="status-options">
            <button v-for="opt in statusOptions" :key="opt.value" class="status-option" :class="{ active: selectedStatus === opt.value, [opt.value]: true }" @click="selectedStatus = opt.value">
              <i :class="opt.icon"></i> {{ opt.label }}
            </button>
          </div>
        </div>
        <div class="upload-modal-footer">
          <button class="btn-cancel" @click="showModal = false">Cancelar</button>
          <button class="btn-upload-confirm" :disabled="saving" @click="saveStatus">
            <i :class="saving ? 'pi pi-spin pi-spinner' : 'pi pi-check'"></i>
            {{ saving ? 'Guardando...' : 'Guardar' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.demo-ap {
  --fin-bg: #0f1419;
  --fin-surface: #15202b;
  --fin-surface-2: #1c2b3a;
  --fin-border: #2d3741;
  --fin-text: #e1e8ed;
  --fin-text-muted: #8899a6;
  background: var(--fin-bg); border: 1px solid var(--fin-border); border-radius: 14px; padding: 1.5rem; margin: 1.5rem 0;
}
.demo-label { margin-bottom: 1.25rem; color: var(--fin-text-muted); font-size: 0.85rem; }
.demo-badge { background: #F0A500; color: #2D2B6B; font-size: 0.7rem; font-weight: 700; padding: 2px 8px; border-radius: 4px; text-transform: uppercase; margin-right: 8px; }
.page-title { font-size: 1.4rem; font-weight: 700; color: var(--fin-text); margin: 0 0 20px; }

/* Month nav */
.month-nav { display: flex; align-items: center; justify-content: center; gap: 16px; margin-bottom: 24px; }
.btn-nav { background-color: var(--fin-surface-2); border: 1px solid var(--fin-border); border-radius: 8px; padding: 8px 12px; color: var(--fin-text); cursor: pointer; }
.btn-nav:hover { border-color: #1da1f2; color: #1da1f2; }
.month-label { font-size: 1.1rem; font-weight: 600; color: var(--fin-text); min-width: 160px; text-align: center; }

/* Categories */
.categories-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; }
.category-card { background-color: var(--fin-surface); border: 1px solid var(--fin-border); border-radius: 12px; padding: 20px; }
.category-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.category-title { display: flex; align-items: center; gap: 8px; font-size: 1rem; font-weight: 600; color: var(--fin-text); }
.category-dot { width: 10px; height: 10px; border-radius: 50%; }
.category-person { font-weight: 400; color: var(--fin-text-muted); font-size: 0.9rem; }
.category-amount { font-size: 0.85rem; color: var(--fin-text-muted); background-color: var(--fin-surface-2); padding: 4px 10px; border-radius: 20px; }

/* Weeks table */
.weeks-table { display: flex; flex-direction: column; }
.week-row { display: grid; grid-template-columns: 1fr auto 50px; align-items: center; padding: 10px 12px; border-bottom: 1px solid var(--fin-border); gap: 12px; }
.week-row:last-child { border-bottom: none; }
.week-row.week-header { background-color: var(--fin-surface-2); border-radius: 8px 8px 0 0; font-size: 0.75rem; text-transform: uppercase; color: var(--fin-text-muted); font-weight: 600; }
.week-cell { font-size: 0.85rem; color: var(--fin-text); }
.week-label-cell { white-space: nowrap; }
.week-action-cell { text-align: center; }

/* Status badges */
.status-badge { padding: 4px 10px; border-radius: 20px; font-size: 0.72rem; font-weight: 600; text-transform: uppercase; }
.status-badge.realizada { background-color: rgba(16,185,129,0.15); color: #10b981; }
.status-badge.pendiente { background-color: rgba(245,158,11,0.15); color: #f59e0b; }

/* Edit button */
.btn-edit { background: none; border: none; color: var(--fin-text-muted); cursor: pointer; padding: 6px; border-radius: 6px; }
.btn-edit:hover { color: #1da1f2; background-color: rgba(29,161,242,0.1); }

/* Modal */
.modal-overlay { position: fixed; inset: 0; background-color: rgba(0,0,0,0.6); display: flex; align-items: center; justify-content: center; z-index: 1000; backdrop-filter: blur(2px); }
.upload-modal { background-color: var(--fin-surface); border: 1px solid var(--fin-border); border-radius: 14px; width: 90%; max-width: 400px; }
.upload-modal-header { display: flex; justify-content: space-between; align-items: center; padding: 18px 20px; border-bottom: 1px solid var(--fin-border); }
.upload-modal-header h3 { color: var(--fin-text); margin: 0; display: flex; align-items: center; gap: 8px; font-size: 1rem; }
.btn-close { background: transparent; border: none; color: var(--fin-text-muted); font-size: 1.1rem; cursor: pointer; }
.upload-modal-body { padding: 20px; }
.upload-hint { color: var(--fin-text-muted); font-size: 0.85rem; margin: 0 0 16px; }
.upload-hint strong { color: var(--fin-text); }

/* Status options */
.status-options { display: flex; gap: 10px; }
.status-option { flex: 1; padding: 14px; border-radius: 10px; border: 2px solid var(--fin-border); background: var(--fin-surface-2); color: var(--fin-text-muted); font-size: 0.85rem; font-weight: 600; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px; transition: all 0.15s; }
.status-option.active.realizada { border-color: #10b981; color: #10b981; background: rgba(16,185,129,0.1); }
.status-option.active.pendiente { border-color: #f59e0b; color: #f59e0b; background: rgba(245,158,11,0.1); }
.status-option:hover { border-color: #1da1f2; }

.upload-modal-footer { display: flex; justify-content: flex-end; gap: 10px; padding: 16px 20px; border-top: 1px solid var(--fin-border); }
.btn-cancel { background-color: var(--fin-surface-2); color: var(--fin-text-muted); border: 1px solid var(--fin-border); padding: 10px 18px; border-radius: 8px; font-size: 0.85rem; cursor: pointer; }
.btn-upload-confirm { background-color: #1da1f2; color: white; border: none; padding: 10px 18px; border-radius: 8px; font-size: 0.85rem; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 6px; }
.btn-upload-confirm:disabled { opacity: 0.6; cursor: not-allowed; }

@media (max-width: 640px) {
  .categories-grid { grid-template-columns: 1fr; }
}
</style>
