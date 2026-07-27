<script setup>
import { ref, computed } from 'vue'

const cards = ref([
  { name: 'Nu', color: '#820ad1', debt: 3500, creditLimit: 25000, minPayment: 850, fullPayment: 3500, cutoffDate: '2026-07-25', paymentDate: '2026-08-05' },
  { name: 'BBVA Azul', color: '#0075eb', debt: 12800, creditLimit: 40000, minPayment: 2100, fullPayment: 12800, cutoffDate: '2026-07-20', paymentDate: '2026-08-01' },
])

const showModal = ref(false)
const activeCard = ref(null)
const editFields = ref({})
const modalSaving = ref(false)

const totalCredit = computed(() => cards.value.reduce((s, c) => s + c.creditLimit, 0))
const totalDebt = computed(() => cards.value.reduce((s, c) => s + c.debt, 0))
const totalAvailable = computed(() => totalCredit.value - totalDebt.value)
const usagePercent = computed(() => totalCredit.value ? Math.round(totalDebt.value / totalCredit.value * 100) : 0)
const totalPayment = computed(() => cards.value.reduce((s, c) => s + c.minPayment, 0))

const currentCardData = computed(() => cards.value.find(c => c.name === activeCard.value) || {})
const hasEdits = computed(() => Object.values(editFields.value).some(v => v !== null && v !== undefined && v !== ''))

function formatMoney(n) { return (n || 0).toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }
function formatDate(d) { if (!d) return '—'; const [y,m,dd] = d.split('-'); return `${dd}/${m}/${y}` }
function daysUntil(d) { if (!d) return 0; const diff = Math.ceil((new Date(d+'T00:00:00') - new Date()) / 86400000); return diff > 0 ? diff : 0 }

function openModal(card) {
  editFields.value = {}
  activeCard.value = card ? card.name : cards.value[0]?.name
  showModal.value = true
}

function selectCard(card) { activeCard.value = card.name; editFields.value = {} }

function saveCard() {
  modalSaving.value = true
  setTimeout(() => {
    const card = cards.value.find(c => c.name === activeCard.value)
    if (card) {
      if (editFields.value.debt != null && editFields.value.debt !== '') card.debt = Number(editFields.value.debt)
      if (editFields.value.creditLimit != null && editFields.value.creditLimit !== '') card.creditLimit = Number(editFields.value.creditLimit)
      if (editFields.value.minimumPayment != null && editFields.value.minimumPayment !== '') card.minPayment = Number(editFields.value.minimumPayment)
      if (editFields.value.fullPayment != null && editFields.value.fullPayment !== '') card.fullPayment = Number(editFields.value.fullPayment)
      if (editFields.value.cutoffDate) card.cutoffDate = editFields.value.cutoffDate
      if (editFields.value.paymentDate) card.paymentDate = editFields.value.paymentDate
    }
    showModal.value = false
    editFields.value = {}
    modalSaving.value = false
  }, 600)
}
</script>

<template>
  <div class="demo-cr">
    <div class="demo-label"><span class="demo-badge">Demo interactiva</span> Edita los datos de una tarjeta y observa cómo se actualizan los totales.</div>

    <h2 class="page-title">Créditos</h2>

    <!-- Stats -->
    <div class="stats-grid">
      <div class="stat-card"><div class="stat-icon credit"><i class="pi pi-credit-card"></i></div><div class="stat-info"><span class="stat-label">Crédito Total</span><span class="stat-value">${{ formatMoney(totalCredit) }}</span></div></div>
      <div class="stat-card"><div class="stat-icon debt"><i class="pi pi-exclamation-triangle"></i></div><div class="stat-info"><span class="stat-label">Deuda Total</span><span class="stat-value">${{ formatMoney(totalDebt) }}</span></div></div>
      <div class="stat-card"><div class="stat-icon available"><i class="pi pi-check-circle"></i></div><div class="stat-info"><span class="stat-label">Disponible Total</span><span class="stat-value">${{ formatMoney(totalAvailable) }}</span></div></div>
      <div class="stat-card"><div class="stat-icon usage"><i class="pi pi-percentage"></i></div><div class="stat-info"><span class="stat-label">Uso Total</span><span class="stat-value">{{ usagePercent }}%</span></div></div>
    </div>

    <!-- Cards -->
    <div class="cards-grid">
      <div v-for="card in cards" :key="card.name" class="credit-card-item" :style="{ borderTopColor: card.color }">
        <div class="card-header">
          <div class="card-brand" :style="{ backgroundColor: card.color + '20', color: card.color }"><i class="pi pi-credit-card"></i></div>
          <div class="card-name-section"><h3>{{ card.name }}</h3><span class="card-subtitle">Tarjeta de Crédito</span></div>
          <button class="btn-edit-card" :style="{ color: card.color }" @click="openModal(card)"><i class="pi pi-pencil"></i></button>
        </div>

        <div class="card-usage-bar">
          <div class="usage-bar-bg"><div class="usage-bar-fill" :style="{ width: (card.debt / card.creditLimit * 100) + '%', backgroundColor: card.color }"></div></div>
          <span class="usage-text">{{ Math.round(card.debt / card.creditLimit * 100) }}% utilizado</span>
        </div>

        <div class="card-details">
          <div class="detail-row"><span class="detail-label">Crédito Total</span><span class="detail-value">${{ formatMoney(card.creditLimit) }}</span></div>
          <div class="detail-row"><span class="detail-label">Saldo a Deber</span><span class="detail-value debt-color">${{ formatMoney(card.debt) }}</span></div>
          <div class="detail-row"><span class="detail-label">Disponible</span><span class="detail-value available-color">${{ formatMoney(card.creditLimit - card.debt) }}</span></div>
          <div class="detail-row separator"><span class="detail-label">Fecha de Corte</span><span class="detail-value">{{ formatDate(card.cutoffDate) }}</span></div>
          <div class="detail-row"><span class="detail-label">Fecha de Pago</span><span class="detail-value highlight">{{ formatDate(card.paymentDate) }}</span></div>
          <div class="detail-row"><span class="detail-label">Pago Mínimo</span><span class="detail-value">${{ formatMoney(card.minPayment) }}</span></div>
          <div class="detail-row"><span class="detail-label">Pago para No Generar Intereses</span><span class="detail-value highlight">${{ formatMoney(card.fullPayment) }}</span></div>
        </div>

        <div class="payment-countdown" v-if="daysUntil(card.paymentDate) > 0">
          <i class="pi pi-clock"></i> {{ daysUntil(card.paymentDate) }} días para tu fecha de pago
        </div>
      </div>
    </div>

    <!-- Modal -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="upload-modal">
        <div class="upload-modal-header">
          <h3><i class="pi pi-credit-card"></i> Actualizar Tarjetas de Crédito</h3>
          <button class="btn-close" @click="showModal = false"><i class="pi pi-times"></i></button>
        </div>
        <div class="upload-modal-body">
          <p class="upload-hint">Selecciona una tarjeta y actualiza sus datos. Los campos vacíos no se modificarán.</p>
          <div class="card-selector">
            <button v-for="card in cards" :key="card.name" class="card-tab" :class="{ active: activeCard === card.name }" :style="activeCard === card.name ? { borderColor: card.color, color: card.color } : {}" @click="selectCard(card)">
              <span class="card-tab-dot" :style="{ backgroundColor: card.color }"></span> {{ card.name }}
            </button>
          </div>
          <div v-if="activeCard" class="card-fields">
            <div class="modal-field"><label>Saldo a Deber</label><div class="balance-input-wrap"><span class="balance-input-prefix">$</span><input type="number" step="0.01" min="0" class="balance-input" :placeholder="formatMoney(currentCardData.debt)" v-model.number="editFields.debt" /></div></div>
            <div class="modal-field"><label>Crédito Total</label><div class="balance-input-wrap"><span class="balance-input-prefix">$</span><input type="number" step="0.01" min="0" class="balance-input" :placeholder="formatMoney(currentCardData.creditLimit)" v-model.number="editFields.creditLimit" /></div></div>
            <div class="modal-field"><label>Pago Mínimo</label><div class="balance-input-wrap"><span class="balance-input-prefix">$</span><input type="number" step="0.01" min="0" class="balance-input" :placeholder="formatMoney(currentCardData.minPayment)" v-model.number="editFields.minimumPayment" /></div></div>
            <div class="modal-field"><label>Pago para No Generar Intereses</label><div class="balance-input-wrap"><span class="balance-input-prefix">$</span><input type="number" step="0.01" min="0" class="balance-input" :placeholder="formatMoney(currentCardData.fullPayment)" v-model.number="editFields.fullPayment" /></div></div>
            <div class="modal-field"><label>Fecha de Corte</label><div class="balance-input-wrap"><input type="date" class="balance-input" v-model="editFields.cutoffDate" /></div></div>
            <div class="modal-field"><label>Fecha de Pago</label><div class="balance-input-wrap"><input type="date" class="balance-input" v-model="editFields.paymentDate" /></div></div>
          </div>
        </div>
        <div class="upload-modal-footer">
          <button class="btn-cancel" @click="showModal = false">Cancelar</button>
          <button class="btn-upload-confirm" :disabled="modalSaving || !hasEdits" @click="saveCard">
            <i :class="modalSaving ? 'pi pi-spin pi-spinner' : 'pi pi-check'"></i>
            {{ modalSaving ? 'Guardando...' : 'Guardar cambios' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.demo-cr {
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

/* Stats */
.stats-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-bottom: 20px; }
.stat-card { background-color: var(--fin-surface); border: 1px solid var(--fin-border); border-radius: 12px; padding: 16px; display: flex; align-items: center; gap: 12px; }
.stat-icon { width: 42px; height: 42px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 1.1rem; }
.stat-icon.credit { background-color: rgba(29,161,242,0.15); color: #1da1f2; }
.stat-icon.debt { background-color: rgba(239,68,68,0.15); color: #ef4444; }
.stat-icon.available { background-color: rgba(16,185,129,0.15); color: #10b981; }
.stat-icon.usage { background-color: rgba(245,158,11,0.15); color: #f59e0b; }
.stat-info { display: flex; flex-direction: column; }
.stat-label { font-size: 0.75rem; color: var(--fin-text-muted); margin-bottom: 2px; }
.stat-value { font-size: 1.1rem; font-weight: 700; color: var(--fin-text); }

/* Cards */
.cards-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px; margin-bottom: 20px; }
.credit-card-item { background-color: var(--fin-surface); border: 1px solid var(--fin-border); border-top: 3px solid; border-radius: 12px; padding: 20px; }
.card-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.card-brand { width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 1.1rem; }
.card-name-section h3 { color: var(--fin-text); font-size: 1.1rem; margin: 0; }
.card-subtitle { color: var(--fin-text-muted); font-size: 0.75rem; }
.btn-edit-card { background: none; border: none; cursor: pointer; margin-left: auto; font-size: 1rem; }
.card-usage-bar { margin-bottom: 16px; }
.usage-bar-bg { height: 6px; background-color: var(--fin-border); border-radius: 3px; overflow: hidden; margin-bottom: 4px; }
.usage-bar-fill { height: 100%; border-radius: 3px; transition: width 0.3s; }
.usage-text { font-size: 0.7rem; color: var(--fin-text-muted); }
.card-details { display: flex; flex-direction: column; gap: 8px; margin-bottom: 16px; }
.detail-row { display: flex; justify-content: space-between; align-items: center; padding: 6px 0; }
.detail-row.separator { border-top: 1px solid var(--fin-border); margin-top: 4px; padding-top: 12px; }
.detail-label { color: var(--fin-text-muted); font-size: 0.82rem; }
.detail-value { color: var(--fin-text); font-size: 0.9rem; font-weight: 600; }
.debt-color { color: #ef4444; }
.available-color { color: #10b981; }
.highlight { color: #f59e0b; }
.payment-countdown { background: rgba(245,158,11,0.1); border: 1px solid rgba(245,158,11,0.25); border-radius: 8px; padding: 10px 14px; font-size: 0.82rem; color: #f59e0b; display: flex; align-items: center; gap: 8px; }

/* Modal */
.modal-overlay { position: fixed; inset: 0; background-color: rgba(0,0,0,0.6); display: flex; align-items: center; justify-content: center; z-index: 1000; backdrop-filter: blur(2px); }
.upload-modal { background-color: var(--fin-surface); border: 1px solid var(--fin-border); border-radius: 14px; width: 90%; max-width: 520px; max-height: 85vh; overflow-y: auto; }
.upload-modal-header { display: flex; justify-content: space-between; align-items: center; padding: 18px 20px; border-bottom: 1px solid var(--fin-border); }
.upload-modal-header h3 { color: var(--fin-text); margin: 0; display: flex; align-items: center; gap: 8px; font-size: 1rem; }
.btn-close { background: transparent; border: none; color: var(--fin-text-muted); font-size: 1.1rem; cursor: pointer; }
.upload-modal-body { padding: 20px; }
.upload-hint { color: var(--fin-text-muted); font-size: 0.85rem; margin: 0 0 16px; }
.card-selector { display: flex; gap: 8px; margin-bottom: 16px; }
.card-tab { background: var(--fin-surface-2); border: 2px solid var(--fin-border); border-radius: 8px; padding: 8px 14px; color: var(--fin-text-muted); font-size: 0.85rem; cursor: pointer; display: flex; align-items: center; gap: 6px; font-weight: 600; }
.card-tab.active { border-color: currentColor; }
.card-tab-dot { width: 8px; height: 8px; border-radius: 50%; }
.card-fields { display: flex; flex-direction: column; gap: 12px; }
.modal-field { display: flex; flex-direction: column; gap: 6px; }
.modal-field label { font-size: 0.75rem; text-transform: uppercase; color: var(--fin-text-muted); font-weight: 600; }
.balance-input-wrap { display: flex; align-items: center; background-color: var(--fin-surface-2); border: 1px solid var(--fin-border); border-radius: 8px; overflow: hidden; }
.balance-input-wrap:focus-within { border-color: #1da1f2; }
.balance-input-prefix { padding: 0 10px; color: var(--fin-text-muted); font-size: 0.9rem; border-right: 1px solid var(--fin-border); line-height: 38px; }
.balance-input { flex: 1; background: transparent; border: none; outline: none; color: var(--fin-text); font-size: 0.9rem; padding: 9px 12px; }
.upload-modal-footer { display: flex; justify-content: flex-end; gap: 10px; padding: 16px 20px; border-top: 1px solid var(--fin-border); }
.btn-cancel { background-color: var(--fin-surface-2); color: var(--fin-text-muted); border: 1px solid var(--fin-border); padding: 10px 18px; border-radius: 8px; font-size: 0.85rem; cursor: pointer; }
.btn-upload-confirm { background-color: #1da1f2; color: white; border: none; padding: 10px 18px; border-radius: 8px; font-size: 0.85rem; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 6px; }
.btn-upload-confirm:disabled { opacity: 0.6; cursor: not-allowed; }

@media (max-width: 640px) {
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
  .cards-grid { grid-template-columns: 1fr; }
  .card-selector { flex-wrap: wrap; }
}
</style>
