<template>
  <div class="creditos">
    <h1 class="page-title">Créditos</h1>

    <!-- Empty state -->
    <div v-if="!cards.length && !loading" class="empty-state">
      <i class="pi pi-credit-card empty-icon"></i>
      <h2>Sin créditos registrados</h2>
      <p>Aún no tienes créditos registrados. Ve a <router-link to="/configuracion?tab=creditos">Configuración</router-link> para agregar tus tarjetas de crédito.</p>
    </div>

    <template v-if="cards.length">
    <!-- Resumen Total -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon credit"><i class="pi pi-credit-card"></i></div>
        <div class="stat-info">
          <span class="stat-label">Crédito Total</span>
          <span class="stat-value">${{ formatMoney(totalCredit) }}</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon debt"><i class="pi pi-exclamation-triangle"></i></div>
        <div class="stat-info">
          <span class="stat-label">Deuda Total</span>
          <span class="stat-value">${{ formatMoney(totalDebt) }}</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon available"><i class="pi pi-check-circle"></i></div>
        <div class="stat-info">
          <span class="stat-label">Disponible Total</span>
          <span class="stat-value">${{ formatMoney(totalAvailable) }}</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon usage"><i class="pi pi-percentage"></i></div>
        <div class="stat-info">
          <span class="stat-label">Uso Total</span>
          <span class="stat-value">{{ usagePercent }}%</span>
        </div>
      </div>
    </div>

    <!-- Banner de actualización (solo lunes sin actualizar) -->
    <div v-if="updateStatus.needsUpdate" class="update-banner">
      <div class="update-banner-info">
        <i class="pi pi-refresh"></i>
        <div>
          <span class="update-banner-title">Datos de tarjetas pendientes de actualizar</span>
          <span class="update-banner-sub">
            Es lunes — actualiza los saldos y fechas de tus tarjetas.
            <span v-if="updateStatus.lastUpdate">
              Última actualización: {{ formatDate(updateStatus.lastUpdate) }}
              (hace {{ updateStatus.daysSinceUpdate }} días)
            </span>
            <span v-else>Nunca actualizado.</span>
          </span>
        </div>
      </div>
      <button class="btn-update" @click="openModal(null)">
        <i class="pi pi-pencil"></i> Actualizar tarjetas
      </button>
    </div>

    <!-- Indicador de última actualización (cuando ya está al día) -->
    <div v-else-if="updateStatus.lastUpdate" class="update-ok">
      <i class="pi pi-check-circle"></i>
      <span>Datos actualizados el {{ formatDate(updateStatus.lastUpdate) }}</span>
    </div>

    <!-- Modal de actualización -->
    <div v-if="showModal" class="upload-overlay" @click.self="showModal = false">
      <div class="upload-modal">
        <div class="upload-modal-header">
          <h3><i class="pi pi-credit-card"></i> Actualizar Tarjetas de Crédito</h3>
          <button class="btn-close" @click="showModal = false"><i class="pi pi-times"></i></button>
        </div>

        <div class="upload-modal-body">
          <p class="upload-hint">Selecciona una tarjeta y actualiza sus datos. Los campos vacíos no se modificarán.</p>

          <!-- Selector de tarjeta -->
          <div class="card-selector">
            <button
              v-for="card in cards"
              :key="card.name"
              class="card-tab"
              :class="{ active: activeCard === card.name }"
              :style="activeCard === card.name ? { borderColor: card.color, color: card.color } : {}"
              @click="selectCard(card)"
            >
              <span class="card-tab-dot" :style="{ backgroundColor: card.color }"></span>
              {{ card.name }}
            </button>
          </div>

          <!-- Campos de la tarjeta seleccionada -->
          <div v-if="activeCard" class="card-fields">
            <div class="modal-field">
              <label>Saldo a Deber</label>
              <div class="balance-input-wrap">
                <span class="balance-input-prefix">$</span>
                <input type="number" step="0.01" min="0" class="balance-input"
                  :placeholder="formatMoney(currentCardData.debt)"
                  v-model.number="editFields.debt" />
              </div>
            </div>
            <div class="modal-field">
              <label>Crédito Total</label>
              <div class="balance-input-wrap">
                <span class="balance-input-prefix">$</span>
                <input type="number" step="0.01" min="0" class="balance-input"
                  :placeholder="formatMoney(currentCardData.creditLimit)"
                  v-model.number="editFields.creditLimit" />
              </div>
            </div>
            <div class="modal-field">
              <label>Pago Mínimo</label>
              <div class="balance-input-wrap">
                <span class="balance-input-prefix">$</span>
                <input type="number" step="0.01" min="0" class="balance-input"
                  :placeholder="formatMoney(currentCardData.minimumPayment)"
                  v-model.number="editFields.minimumPayment" />
              </div>
            </div>
            <div class="modal-field">
              <label>Pago para No Generar Intereses</label>
              <div class="balance-input-wrap">
                <span class="balance-input-prefix">$</span>
                <input type="number" step="0.01" min="0" class="balance-input"
                  :placeholder="formatMoney(currentCardData.fullPayment)"
                  v-model.number="editFields.fullPayment" />
              </div>
            </div>
            <div class="modal-field">
              <label>Fecha de Corte</label>
              <div class="balance-input-wrap">
                <input type="date" class="balance-input date-input"
                  :placeholder="currentCardData.cutoffDate"
                  v-model="editFields.cutoffDate" />
              </div>
            </div>
            <div class="modal-field">
              <label>Fecha de Pago</label>
              <div class="balance-input-wrap">
                <input type="date" class="balance-input date-input"
                  :placeholder="currentCardData.paymentDate"
                  v-model="editFields.paymentDate" />
              </div>
            </div>
          </div>

          <div v-if="modalError" class="upload-error">
            <i class="pi pi-exclamation-triangle"></i> {{ modalError }}
          </div>
        </div>

        <div class="upload-modal-footer">
          <button class="btn-cancel" @click="showModal = false">Cancelar</button>
          <button
            class="btn-upload-confirm"
            :disabled="modalSaving || !activeCard || !hasEdits"
            @click="saveCard"
          >
            <i :class="modalSaving ? 'pi pi-spin pi-spinner' : 'pi pi-check'"></i>
            {{ modalSaving ? 'Guardando...' : 'Guardar cambios' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Tarjetas individuales -->
    <div class="cards-grid">
      <div v-for="card in cards" :key="card.name" class="credit-card-item" :style="{ borderTopColor: card.color }">
        <div class="card-header">
          <div class="card-brand" :style="{ backgroundColor: card.color + '20', color: card.color }">
            <i class="pi pi-credit-card"></i>
          </div>
          <div class="card-name-section">
            <h3>{{ card.name }}</h3>
            <span class="card-subtitle">Tarjeta de Crédito</span>
          </div>
          <button class="btn-edit-card" :style="{ color: card.color }" @click="openModal(card)">
            <i class="pi pi-pencil"></i>
          </button>
        </div>

        <div class="card-usage-bar">
          <div class="usage-bar-bg">
            <div class="usage-bar-fill" :style="{ width: card.usagePercent + '%', backgroundColor: card.color }"></div>
          </div>
          <span class="usage-text">{{ card.usagePercent }}% utilizado</span>
        </div>

        <div class="card-details">
          <div class="detail-row">
            <span class="detail-label">Crédito Total</span>
            <span class="detail-value">${{ formatMoney(card.creditLimit) }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Saldo a Deber</span>
            <span class="detail-value debt-color">${{ formatMoney(card.debt) }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Disponible</span>
            <span class="detail-value available-color">${{ formatMoney(card.available) }}</span>
          </div>
          <div class="detail-row separator">
            <span class="detail-label">Fecha de Corte</span>
            <span class="detail-value">{{ formatDate(card.cutoffDate) }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Fecha de Pago</span>
            <span class="detail-value highlight">{{ formatDate(card.paymentDate) }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Pago Mínimo</span>
            <span class="detail-value">${{ formatMoney(card.minimumPayment) }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Pago para No Generar Intereses</span>
            <span class="detail-value highlight">${{ formatMoney(card.fullPayment) }}</span>
          </div>
        </div>

        <PaymentCountdown :days="daysUntilPayment(card.paymentDate)" />
      </div>
    </div>

    <!-- Tabla resumen -->
    <div class="table-card">
      <h3>Resumen de Tarjetas</h3>
      <table class="data-table">
        <thead>
          <tr>
            <th>Tarjeta</th>
            <th>Crédito</th>
            <th>Deuda</th>
            <th>Disponible</th>
            <th>Uso %</th>
            <th>Fecha Corte</th>
            <th>Fecha Pago</th>
            <th>Pago Requerido</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="card in cards" :key="card.name">
            <td>
              <span class="table-card-name" :style="{ color: card.color }">
                <i class="pi pi-credit-card"></i> {{ card.name }}
              </span>
            </td>
            <td>${{ formatMoney(card.creditLimit) }}</td>
            <td class="debt-color">${{ formatMoney(card.debt) }}</td>
            <td class="available-color">${{ formatMoney(card.available) }}</td>
            <td>
              <span class="usage-badge" :class="getUsageClass(card.usagePercent)">
                {{ card.usagePercent }}%
              </span>
            </td>
            <td>{{ formatDate(card.cutoffDate) }}</td>
            <td>{{ formatDate(card.paymentDate) }}</td>
            <td class="highlight">${{ formatMoney(card.fullPayment) }}</td>
          </tr>
          <tr class="totals-row">
            <td><strong>TOTAL</strong></td>
            <td><strong>${{ formatMoney(totalCredit) }}</strong></td>
            <td class="debt-color"><strong>${{ formatMoney(totalDebt) }}</strong></td>
            <td class="available-color"><strong>${{ formatMoney(totalAvailable) }}</strong></td>
            <td><strong>{{ usagePercent }}%</strong></td>
            <td>—</td>
            <td>—</td>
            <td class="highlight"><strong>${{ formatMoney(totalPayment) }}</strong></td>
          </tr>
        </tbody>
      </table>
    </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import finApi from '../utils/api'
import { cachedGet } from '../utils/cache'
import PaymentCountdown from '../components/PaymentCountdown.vue'
import { formatMoney } from '../utils/format.js'

const cards = ref([])
const loading = ref(true)
const totalCredit = ref(0)
const totalDebt = ref(0)
const totalAvailable = ref(0)
const totalPayment = ref(0)
const usagePercent = ref(0)

async function loadCreditos() {
  loading.value = true
  try {
    const response = await cachedGet('/api/creditos')
    const data = response.data?.data || response.data || {}
    cards.value = data.cards || data.items || []
    const summary = data.summary || {}
    totalCredit.value = summary.totalCredit || data.total_balance || 0
    totalDebt.value = summary.totalDebt || 0
    totalAvailable.value = summary.totalAvailable || 0
    totalPayment.value = summary.totalPayment || 0
    usagePercent.value = summary.usagePercent || 0
  } catch (error) {
    console.error('Error loading credit data:', error)
    cards.value = []
  } finally {
    loading.value = false
  }
}

// ===== ESTADO DE ACTUALIZACIÓN =====
const updateStatus = ref({ needsUpdate: false, lastUpdate: null, isMonday: false, daysSinceUpdate: null })

async function loadUpdateStatus() {
  try {
    const res = await cachedGet('/api/creditos/update-status')
    updateStatus.value = res.data
  } catch { /* silencioso */ }
}

// ===== MODAL =====
const showModal = ref(false)
const activeCard = ref(null)
const editFields = ref({})
const modalSaving = ref(false)
const modalError = ref('')

const currentCardData = computed(() =>
  cards.value.find(c => c.name === activeCard.value) || {}
)

const hasEdits = computed(() =>
  Object.values(editFields.value).some(v => v !== null && v !== undefined && v !== '')
)

function openModal(card) {
  editFields.value = {}
  modalError.value = ''
  activeCard.value = card ? card.name : (cards.value[0]?.name || null)
  showModal.value = true
}

function selectCard(card) {
  activeCard.value = card.name
  editFields.value = {}
  modalError.value = ''
}

async function saveCard() {
  modalSaving.value = true
  modalError.value = ''
  try {
    const payload = { name: activeCard.value }
    for (const [k, v] of Object.entries(editFields.value)) {
      if (v !== null && v !== undefined && v !== '') payload[k] = v
    }
    await finApi.post('/api/creditos/update-card', payload)
    await loadCreditos()
    await loadUpdateStatus()
    showModal.value = false
    editFields.value = {}
  } catch (e) {
    modalError.value = e.response?.data?.detail || 'Error al guardar los cambios.'
  } finally {
    modalSaving.value = false
  }
}

onMounted(() => {
  loadCreditos()
  loadUpdateStatus()
})

function formatDate(dateStr) {
  if (!dateStr) return ''
  const clean = dateStr.split(' ')[0]
  const [y, m, d] = clean.split('-')
  return `${d}-${m}-${y}`
}

function daysUntilPayment(dateStr) {
  if (!dateStr) return 0
  const today = new Date()
  const payment = new Date(dateStr + 'T00:00:00')
  const diff = Math.ceil((payment - today) / (1000 * 60 * 60 * 24))
  return diff > 0 ? diff : 0
}

function getUsageClass(percent) {
  if (percent >= 70) return 'high'
  if (percent >= 40) return 'medium'
  return 'low'
}
</script>

<style scoped>
.creditos {
  max-width: 1200px;
  width: 100%;
  overflow-x: hidden;
  overflow-wrap: break-word;
  word-break: break-word;
}

.empty-state {
  text-align: center;
  padding: 80px 20px;
  color: var(--fin-text-muted);
}

.empty-icon {
  font-size: 3rem;
  opacity: 0.4;
  margin-bottom: 16px;
}

.empty-state h2 {
  color: var(--fin-text);
  font-size: 1.2rem;
  margin-bottom: 8px;
}

.empty-state p {
  font-size: 0.9rem;
}

.empty-state a {
  color: #1da1f2;
  text-decoration: none;
}

.empty-state a:hover {
  text-decoration: underline;
}

.page-title {
  font-size: 1.8rem;
  font-weight: 700;
  margin-bottom: 24px;
  color: var(--fin-text);
}

/* Stats */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(220px, 100%), 1fr));
  gap: 16px;
  margin-bottom: 24px;
  max-width: 100%;
}

.stat-card {
  background-color: var(--fin-surface);
  border: 1px solid var(--fin-border);
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
}

.stat-icon.credit {
  background-color: rgba(29, 161, 242, 0.15);
  color: #1da1f2;
}

.stat-icon.debt {
  background-color: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}

.stat-icon.available {
  background-color: rgba(16, 185, 129, 0.15);
  color: #10b981;
}

.stat-icon.usage {
  background-color: rgba(245, 158, 11, 0.15);
  color: #f59e0b;
}

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-label {
  font-size: 0.8rem;
  color: var(--fin-text-muted);
  margin-bottom: 4px;
}

.stat-value {
  font-size: 1.3rem;
  font-weight: 700;
  color: var(--fin-text);
}

/* Cards Grid */
.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(320px, 100%), 1fr));
  gap: 16px;
  margin-bottom: 24px;
  max-width: 100%;
}

.credit-card-item {
  background-color: var(--fin-surface);
  border: 1px solid var(--fin-border);
  border-top: 3px solid;
  border-radius: 12px;
  padding: 20px;
  min-width: 0;
  overflow: hidden;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.card-brand {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
}

.card-name-section h3 {
  color: var(--fin-text);
  font-size: 1.1rem;
  margin: 0;
}

.card-subtitle {
  color: var(--fin-text-muted);
  font-size: 0.75rem;
}

.card-usage-bar {
  margin-bottom: 16px;
}

.usage-bar-bg {
  height: 6px;
  background-color: var(--fin-border);
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 4px;
}

.usage-bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.3s ease;
}

.usage-text {
  font-size: 0.7rem;
  color: var(--fin-text-muted);
}

.card-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
}

.detail-row.separator {
  border-top: 1px solid var(--fin-border);
  margin-top: 4px;
  padding-top: 12px;
}

.detail-label {
  color: var(--fin-text-muted);
  font-size: 0.82rem;
}

.detail-value {
  color: var(--fin-text);
  font-size: 0.9rem;
  font-weight: 600;
}

.debt-color {
  color: #ef4444;
}

.available-color {
  color: #10b981;
}

.highlight {
  color: #f59e0b;
}

/* countdown handled by PaymentCountdown component */

/* Tabla */
.table-card {
  background-color: var(--fin-surface);
  border: 1px solid var(--fin-border);
  border-radius: 12px;
  padding: 24px;
  overflow-x: auto;
  max-width: 100%;
}

.table-card h3 {
  color: var(--fin-text);
  margin-bottom: 16px;
  font-size: 1rem;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 600px;
}

.data-table th {
  text-align: left;
  padding: 12px 16px;
  font-size: 0.75rem;
  text-transform: uppercase;
  color: var(--fin-text-muted);
  border-bottom: 1px solid var(--fin-border);
  background-color: var(--fin-surface-2);
}

.data-table td {
  padding: 12px 16px;
  border-bottom: 1px solid var(--fin-border);
  color: var(--fin-text);
  font-size: 0.85rem;
}

.data-table tr:hover td {
  background-color: var(--fin-hover);
}

.totals-row td {
  background-color: var(--fin-surface-2);
  border-top: 2px solid var(--fin-border);
}

.table-card-name {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
}

.usage-badge {
  padding: 3px 8px;
  border-radius: 12px;
  font-size: 0.7rem;
  font-weight: 600;
}

.usage-badge.low {
  background-color: rgba(16, 185, 129, 0.15);
  color: #10b981;
}

.usage-badge.medium {
  background-color: rgba(245, 158, 11, 0.15);
  color: #f59e0b;
}

.usage-badge.high {
  background-color: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}

@media (max-width: 768px) {
  .charts-grid {
    grid-template-columns: 1fr;
  }

  .cards-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .credit-card-item {
    padding: 16px;
  }

  .card-header {
    gap: 10px;
    margin-bottom: 12px;
  }

  .card-brand {
    width: 34px;
    height: 34px;
    font-size: 0.95rem;
  }

  .card-name-section h3 {
    font-size: 0.95rem;
  }

  .detail-row {
    padding: 4px 0;
  }

  .detail-label {
    font-size: 0.75rem;
  }

  .detail-value {
    font-size: 0.82rem;
  }

  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
  }

  .stat-card {
    padding: 14px;
    gap: 10px;
  }

  .stat-icon {
    width: 38px;
    height: 38px;
    font-size: 1rem;
  }

  .stat-value {
    font-size: 1.1rem;
  }

  .page-title {
    font-size: 1.4rem;
    margin-bottom: 16px;
  }

  .table-card {
    padding: 12px;
    border-radius: 10px;
  }

  .data-table th,
  .data-table td {
    padding: 8px 10px;
    font-size: 0.75rem;
  }

  /* Hide less important columns on mobile */
  .data-table th:nth-child(6),
  .data-table td:nth-child(6),
  .data-table th:nth-child(7),
  .data-table td:nth-child(7) {
    display: none;
  }

  .update-banner {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .btn-update {
    width: 100%;
    justify-content: center;
  }

  /* Modal responsive */
  .upload-modal {
    max-width: 100%;
    max-height: calc(100vh - 32px);
    border-radius: 12px;
  }

  .upload-modal-body {
    padding: 14px;
    gap: 12px;
  }

  .upload-modal-header {
    padding: 12px 14px;
  }

  .upload-modal-header h3 {
    font-size: 0.9rem;
  }

  .upload-modal-footer {
    padding: 12px 14px;
  }

  .card-tab {
    padding: 5px 10px;
    font-size: 0.75rem;
  }

  .card-selector {
    flex-wrap: wrap;
  }
}

@media (max-width: 480px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }

  .credit-card-item {
    padding: 14px;
  }

  .card-details {
    gap: 4px;
  }

  .data-table th:nth-child(2),
  .data-table td:nth-child(2) {
    display: none;
  }
}

/* ── Banner de actualización ─────────────────────────────────────────── */
.update-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 18px;
  margin-bottom: 20px;
  background-color: rgba(245, 158, 11, 0.08);
  border: 1px solid rgba(245, 158, 11, 0.3);
  border-radius: 10px;
  max-width: 100%;
  overflow: hidden;
}

.update-banner-info {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  color: #f59e0b;
  font-size: 0.85rem;
}

.update-banner-info > .pi { margin-top: 2px; font-size: 1rem; }

.update-banner-info > div {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.update-banner-title {
  font-weight: 700;
  color: #f59e0b;
}

.update-banner-sub {
  color: var(--fin-text-muted);
  font-size: 0.78rem;
}

.btn-update {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background-color: #f59e0b;
  color: var(--fin-bg-2);
  border: none;
  border-radius: 8px;
  font-size: 0.82rem;
  font-weight: 700;
  cursor: pointer;
  white-space: nowrap;
  transition: background-color 0.2s;
}
.btn-update:hover { background-color: #d97706; }

.update-ok {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  margin-bottom: 20px;
  background-color: rgba(16, 185, 129, 0.08);
  border: 1px solid rgba(16, 185, 129, 0.25);
  border-radius: 10px;
  color: #10b981;
  font-size: 0.82rem;
}

.btn-update-sm {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  margin-left: auto;
  padding: 5px 12px;
  background: transparent;
  border: 1px solid rgba(16, 185, 129, 0.4);
  color: #10b981;
  border-radius: 6px;
  font-size: 0.78rem;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-update-sm:hover { background: rgba(16, 185, 129, 0.1); }

/* ── Botón editar en cada tarjeta ────────────────────────────────────── */
.btn-edit-card {
  margin-left: auto;
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 0.85rem;
  opacity: 0.5;
  transition: opacity 0.2s;
  padding: 4px;
}
.btn-edit-card:hover { opacity: 1; }

/* ── Modal ───────────────────────────────────────────────────────────── */
.upload-overlay {
  position: fixed;
  inset: 0;
  background-color: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 16px;
  overflow: hidden;
}

.upload-modal {
  background-color: var(--fin-surface);
  border: 1px solid var(--fin-border);
  border-radius: 14px;
  width: 100%;
  max-width: 440px;
  max-height: calc(100vh - 32px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0,0,0,0.5);
}

.upload-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 20px;
  border-bottom: 1px solid var(--fin-border);
  flex-shrink: 0;
}

.upload-modal-header h3 {
  color: var(--fin-text);
  font-size: 1rem;
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
}

.btn-close {
  background: transparent;
  border: none;
  color: var(--fin-text-muted);
  cursor: pointer;
  font-size: 1rem;
  padding: 4px;
  transition: color 0.2s;
}
.btn-close:hover { color: var(--fin-text); }

.upload-modal-body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-x: hidden;
  overflow-y: auto;
  flex: 1;
  min-height: 0;
}

.upload-hint {
  color: var(--fin-text-muted);
  font-size: 0.82rem;
  margin: 0;
}

/* Selector de tarjeta */
.card-selector {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.card-tab {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  background: transparent;
  border: 1px solid var(--fin-border);
  border-radius: 20px;
  color: var(--fin-text-muted);
  font-size: 0.82rem;
  cursor: pointer;
  transition: all 0.2s;
}
.card-tab:hover { border-color: var(--fin-text-muted); color: var(--fin-text); }
.card-tab.active { font-weight: 700; background: rgba(255,255,255,0.04); }

.card-tab-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

/* Campos */
.card-fields { display: flex; flex-direction: column; gap: 14px; }

.modal-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.modal-field label {
  font-size: 0.8rem;
  color: var(--fin-text);
  font-weight: 600;
}

.field-hint {
  font-size: 0.72rem;
  color: var(--fin-text-muted);
  font-weight: 400;
}

.balance-input-wrap {
  display: flex;
  align-items: center;
  background-color: var(--fin-bg-2);
  border: 1px solid var(--fin-border);
  border-radius: 8px;
  overflow: hidden;
  transition: border-color 0.2s;
  min-width: 0;
  width: 100%;
  max-width: 100%;
}
.balance-input-wrap:focus-within { border-color: #1da1f2; }

.balance-input-prefix {
  padding: 0 10px;
  color: var(--fin-text-muted);
  font-size: 0.9rem;
  border-right: 1px solid var(--fin-border);
  line-height: 38px;
  flex-shrink: 0;
}

.balance-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  color: var(--fin-text);
  font-size: 0.88rem;
  padding: 9px 12px;
  min-width: 0;
  width: 100%;
}
.balance-input::placeholder { color: #4a5568; }
.balance-input::-webkit-inner-spin-button,
.balance-input::-webkit-outer-spin-button { opacity: 0.4; }

.date-input { color-scheme: dark; }

.upload-error {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background-color: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 8px;
  color: #ef4444;
  font-size: 0.82rem;
}

.upload-modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 16px 20px;
  border-top: 1px solid var(--fin-border);
  flex-shrink: 0;
}

.btn-cancel {
  background: transparent;
  border: 1px solid var(--fin-border);
  color: var(--fin-text-muted);
  padding: 9px 18px;
  border-radius: 8px;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-cancel:hover { color: var(--fin-text); border-color: var(--fin-text-muted); }

.btn-upload-confirm {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 20px;
  background-color: #1da1f2;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 700;
  cursor: pointer;
  transition: background-color 0.2s;
}
.btn-upload-confirm:hover:not(:disabled) { background-color: #1a91da; }
.btn-upload-confirm:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
