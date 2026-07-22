<template>
  <div class="deudas">
    <div class="page-header">
      <h1 class="page-title">Deudas</h1>
      <button class="btn-primary" @click="showNuevaDeudaModal = true">
        <i class="pi pi-plus"></i> Nuevo Préstamo
      </button>
    </div>

    <!-- Modal Nueva Deuda -->
    <div v-if="showNuevaDeudaModal" class="modal-overlay" @click.self="showNuevaDeudaModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3><i class="pi pi-plus-circle"></i> Nuevo Préstamo</h3>
          <button class="btn-close" @click="showNuevaDeudaModal = false"><i class="pi pi-times"></i></button>
        </div>

        <div class="modal-body">
          <p class="modal-hint">Registra una nueva deuda. Completa todos los campos.</p>

          <div class="modal-field">
            <label>Nombre del Préstamo</label>
            <input type="text" v-model="deudaForm.name" class="form-input" placeholder="Ej: Préstamo Banco X" />
          </div>

          <div class="modal-field-row">
            <div class="modal-field">
              <label>Deuda Total</label>
              <div class="field-input-wrap">
                <span class="field-prefix">$</span>
                <input type="number" step="0.01" min="0.01" class="field-input"
                  placeholder="0.00" v-model.number="deudaForm.totalDebt" />
              </div>
            </div>
            <div class="modal-field">
              <label>Temporalidad</label>
              <select v-model="deudaForm.frequency" class="form-input">
                <option value="">Seleccionar...</option>
                <option value="mensual">Mensual</option>
                <option value="quincenal">Quincenal</option>
              </select>
            </div>
          </div>

          <div class="modal-field-row">
            <div class="modal-field">
              <label>Cantidad a Pagar (por periodo)</label>
              <div class="field-input-wrap">
                <span class="field-prefix">$</span>
                <input type="number" step="0.01" min="0.01" class="field-input"
                  placeholder="0.00" v-model.number="deudaForm.paymentAmount" />
              </div>
            </div>
            <div class="modal-field">
              <label>{{ deudaForm.frequency === 'quincenal' ? 'Primera fecha de pago' : 'Fecha de pago' }}</label>
              <input type="date" v-model="deudaForm.payDate1" class="form-input" />
            </div>
          </div>

          <div v-if="deudaForm.frequency === 'quincenal'" class="modal-field">
            <label>Segunda fecha de pago</label>
            <input type="date" v-model="deudaForm.payDate2" class="form-input" />
          </div>

          <div v-if="deudaFormError" class="modal-error">
            <i class="pi pi-exclamation-triangle"></i> {{ deudaFormError }}
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn-cancel" @click="showNuevaDeudaModal = false">Cancelar</button>
          <button
            class="btn-confirm"
            :disabled="deudaFormSubmitting || !deudaFormValid"
            @click="submitNuevaDeuda"
          >
            <i :class="deudaFormSubmitting ? 'pi pi-spin pi-spinner' : 'pi pi-check'"></i>
            {{ deudaFormSubmitting ? 'Registrando...' : 'Registrar' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Mensaje -->
    <div v-if="message" class="alert-message" :class="messageType">
      {{ message }}
    </div>

    <!-- Resumen -->
    <div class="stats-grid" v-if="deudas.length > 0">
      <div class="stat-card">
        <div class="stat-icon debt"><i class="pi pi-exclamation-triangle"></i></div>
        <div class="stat-info">
          <span class="stat-label">Deuda Total</span>
          <span class="stat-value">${{ formatMoney(totalDebt) }}</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon count"><i class="pi pi-list"></i></div>
        <div class="stat-info">
          <span class="stat-label">Préstamos Activos</span>
          <span class="stat-value">{{ deudas.length }}</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon next"><i class="pi pi-clock"></i></div>
        <div class="stat-info">
          <span class="stat-label">Próximo Pago</span>
          <span class="stat-value">{{ nextPaymentInfo }}</span>
        </div>
      </div>
    </div>

    <!-- Cards de deudas -->
    <div class="deudas-grid">
      <div v-for="deuda in deudas" :key="deuda.id" class="deuda-card">
        <div class="deuda-header">
          <div class="deuda-name">
            <i class="pi pi-money-bill"></i>
            <h3>{{ deuda.name }}</h3>
          </div>
          <span class="frequency-badge" :class="deuda.frequency">
            {{ deuda.frequencyLabel }}
          </span>
        </div>

        <div class="deuda-details">
          <div class="detail-row">
            <span class="detail-label">Deuda Total</span>
            <span class="detail-value debt-color">${{ formatMoney(deuda.totalDebt) }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Cantidad a Pagar</span>
            <span class="detail-value highlight">${{ formatMoney(deuda.paymentAmount) }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Pagos Restantes</span>
            <span class="detail-value">{{ deuda.paymentsRemaining }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Próxima Fecha de Pago</span>
            <span class="detail-value highlight">{{ formatDate(deuda.nextPaymentDate) }}</span>
          </div>
        </div>

        <PaymentCountdown :days="deuda.daysUntilPayment" />
      </div>
    </div>

    <!-- Empty state -->
    <div v-if="deudas.length === 0" class="empty-state">
      <i class="pi pi-check-circle"></i>
      <p>No tienes deudas registradas</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import finApi from '../utils/api'
import { cachedGet } from '../utils/cache'
import PaymentCountdown from '../components/PaymentCountdown.vue'
import { formatMoney } from '../utils/format.js'

const deudas = ref([])
const totalDebt = ref(0)
const message = ref('')
const messageType = ref('')

// ===== MODAL NUEVA DEUDA =====
const showNuevaDeudaModal = ref(false)
const deudaFormSubmitting = ref(false)
const deudaFormError = ref('')
const deudaForm = ref({
  name: '',
  totalDebt: null,
  paymentAmount: null,
  frequency: '',
  payDate1: '',
  payDate2: ''
})

const deudaFormValid = computed(() =>
  deudaForm.value.name &&
  deudaForm.value.totalDebt > 0 &&
  deudaForm.value.paymentAmount > 0 &&
  deudaForm.value.frequency &&
  deudaForm.value.payDate1
)

async function submitNuevaDeuda() {
  deudaFormSubmitting.value = true
  deudaFormError.value = ''
  try {
    const payDay1 = deudaForm.value.payDate1 ? new Date(deudaForm.value.payDate1 + 'T00:00:00').getDate() : 1
    const payDay2 = deudaForm.value.frequency === 'quincenal' && deudaForm.value.payDate2
      ? new Date(deudaForm.value.payDate2 + 'T00:00:00').getDate() : 0

    await finApi.post('/api/deudas', {
      name: deudaForm.value.name,
      totalDebt: deudaForm.value.totalDebt,
      paymentAmount: deudaForm.value.paymentAmount,
      frequency: deudaForm.value.frequency,
      payDay1,
      payDay2,
      startDate1: deudaForm.value.payDate1,
      startDate2: deudaForm.value.frequency === 'quincenal' ? deudaForm.value.payDate2 : ''
    })

    showNuevaDeudaModal.value = false
    deudaForm.value = { name: '', totalDebt: null, paymentAmount: null, frequency: '', payDate1: '', payDate2: '' }
    message.value = '✅ Préstamo registrado correctamente'
    messageType.value = 'success'
    setTimeout(() => { message.value = '' }, 3000)
    await loadDeudas()
  } catch (error) {
    deudaFormError.value = error.response?.data?.detail || error.message
  } finally {
    deudaFormSubmitting.value = false
  }
}

const nextPaymentInfo = computed(() => {
  if (deudas.value.length === 0) return 'N/A'
  const sorted = [...deudas.value].sort((a, b) => a.daysUntilPayment - b.daysUntilPayment)
  const next = sorted[0]
  return `${next.daysUntilPayment}d - $${formatMoney(next.paymentAmount)}`
})

onMounted(async () => {
  await loadDeudas()
})

async function loadDeudas() {
  try {
    const response = await cachedGet('/api/deudas')
    deudas.value = response.data.deudas
    totalDebt.value = response.data.totalDebt
  } catch (error) {
    console.error('Error loading deudas:', error)
  }
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr + 'T00:00:00')
  return date.toLocaleDateString('es-AR', { day: '2-digit', month: 'short', year: 'numeric' })
}
</script>

<style scoped>
.deudas { max-width: 1000px; }

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-title { font-size: 1.8rem; font-weight: 700; color: var(--fin-text); }

.btn-primary {
  background-color: #1da1f2;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: background-color 0.2s;
}
.btn-primary:hover { background-color: #1a91da; }

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background-color: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(2px);
}

.modal-content {
  background-color: var(--fin-surface);
  border: 1px solid var(--fin-border);
  border-radius: 14px;
  width: 90%;
  max-width: 520px;
  max-height: 85vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 20px;
  border-bottom: 1px solid var(--fin-border);
}
.modal-header h3 { color: var(--fin-text); margin: 0; display: flex; align-items: center; gap: 8px; font-size: 1rem; }

.btn-close {
  background: transparent;
  border: none;
  color: var(--fin-text-muted);
  font-size: 1.1rem;
  cursor: pointer;
  padding: 4px;
}
.btn-close:hover { color: var(--fin-text); }

.modal-body { padding: 20px; display: flex; flex-direction: column; gap: 14px; }
.modal-hint { color: var(--fin-text-muted); font-size: 0.85rem; margin: 0; }

.modal-field { display: flex; flex-direction: column; gap: 6px; }
.modal-field label { font-size: 0.75rem; text-transform: uppercase; color: var(--fin-text-muted); font-weight: 600; }
.modal-field-row { display: flex; gap: 12px; }
.modal-field-row .modal-field { flex: 1; }

.field-input-wrap {
  display: flex;
  align-items: center;
  background-color: var(--fin-bg-2);
  border: 1px solid var(--fin-border);
  border-radius: 8px;
  overflow: hidden;
  transition: border-color 0.2s;
}
.field-input-wrap:focus-within { border-color: #1da1f2; }
.field-prefix {
  padding: 0 10px;
  color: var(--fin-text-muted);
  font-size: 0.9rem;
  border-right: 1px solid var(--fin-border);
  line-height: 38px;
}
.field-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  color: var(--fin-text);
  font-size: 0.9rem;
  padding: 9px 12px;
}

.modal-error {
  padding: 10px 14px;
  border-radius: 8px;
  background-color: rgba(239, 68, 68, 0.15);
  color: #ef4444;
  border: 1px solid rgba(239, 68, 68, 0.3);
  font-size: 0.85rem;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 16px 20px;
  border-top: 1px solid var(--fin-border);
}

.btn-cancel {
  background-color: var(--fin-surface-2);
  color: var(--fin-text-muted);
  border: 1px solid var(--fin-border);
  padding: 10px 18px;
  border-radius: 8px;
  font-size: 0.85rem;
  cursor: pointer;
}
.btn-cancel:hover { color: var(--fin-text); border-color: #1da1f2; }

.btn-confirm {
  background-color: #1da1f2;
  color: white;
  border: none;
  padding: 10px 18px;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
}
.btn-confirm:hover { background-color: #1a91da; }
.btn-confirm:disabled { opacity: 0.6; cursor: not-allowed; }

/* Form */
.form-card {
  background-color: var(--fin-surface);
  border: 1px solid var(--fin-border);
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 20px;
}
.form-card h3 { color: var(--fin-text); margin-bottom: 16px; }

.deuda-form { display: flex; flex-direction: column; gap: 14px; }
.form-row { display: flex; gap: 12px; }
.form-group { display: flex; flex-direction: column; gap: 6px; flex: 1; }
.form-group.flex-2 { flex: 2; }
.form-group label { font-size: 0.75rem; text-transform: uppercase; color: var(--fin-text-muted); font-weight: 600; }

.form-input {
  background-color: var(--fin-surface-2);
  border: 1px solid var(--fin-border);
  border-radius: 8px;
  padding: 10px 14px;
  color: var(--fin-text);
  font-size: 0.9rem;
}
.form-input:focus { outline: none; border-color: #1da1f2; }

.form-actions { margin-top: 8px; }

/* Message */
.alert-message {
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 20px;
  font-size: 0.9rem;
}
.alert-message.success { background-color: rgba(16, 185, 129, 0.15); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.3); }
.alert-message.error { background-color: rgba(239, 68, 68, 0.15); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.3); }

/* Stats */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
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
  width: 48px; height: 48px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center; font-size: 1.2rem;
}
.stat-icon.debt { background-color: rgba(239, 68, 68, 0.15); color: #ef4444; }
.stat-icon.count { background-color: rgba(29, 161, 242, 0.15); color: #1da1f2; }
.stat-icon.next { background-color: rgba(245, 158, 11, 0.15); color: #f59e0b; }

.stat-info { display: flex; flex-direction: column; }
.stat-label { font-size: 0.8rem; color: var(--fin-text-muted); margin-bottom: 4px; }
.stat-value { font-size: 1.3rem; font-weight: 700; color: var(--fin-text); }

/* Deudas Grid */
.deudas-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.deuda-card {
  background-color: var(--fin-surface);
  border: 1px solid var(--fin-border);
  border-top: 3px solid #ef4444;
  border-radius: 12px;
  padding: 20px;
}

.deuda-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.deuda-name { display: flex; align-items: center; gap: 10px; }
.deuda-name i { color: #ef4444; font-size: 1.1rem; }
.deuda-name h3 { color: var(--fin-text); font-size: 1rem; margin: 0; }

.frequency-badge {
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 0.7rem;
  font-weight: 600;
}
.frequency-badge.mensual { background-color: rgba(29, 161, 242, 0.15); color: #1da1f2; }
.frequency-badge.quincenal { background-color: rgba(139, 92, 246, 0.15); color: #8b5cf6; }

.deuda-details { display: flex; flex-direction: column; gap: 10px; margin-bottom: 16px; }

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
}
.detail-label { color: var(--fin-text-muted); font-size: 0.82rem; }
.detail-value { color: var(--fin-text); font-size: 0.9rem; font-weight: 600; }
.debt-color { color: #ef4444; }
.highlight { color: #f59e0b; }

/* countdown handled by PaymentCountdown component */

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--fin-text-muted);
}
.empty-state i { font-size: 3rem; margin-bottom: 12px; color: #10b981; display: block; }
.empty-state p { font-size: 1rem; }

@media (max-width: 768px) {
  .deudas-grid { grid-template-columns: 1fr; }

  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .btn-primary {
    width: 100%;
    justify-content: center;
  }

  .stats-grid {
    grid-template-columns: 1fr;
    gap: 10px;
  }

  .stat-card {
    padding: 14px;
    gap: 10px;
  }

  .page-title {
    font-size: 1.4rem;
  }

  .modal-content {
    width: 95%;
    max-width: 95vw;
  }

  .modal-field-row {
    flex-direction: column;
    gap: 14px;
  }
}

@media (max-width: 480px) {
  .deuda-card {
    padding: 14px;
  }

  .detail-label, .detail-value {
    font-size: 0.8rem;
  }
}
</style>
