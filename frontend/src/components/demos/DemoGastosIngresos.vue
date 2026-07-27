<script setup>
import { ref, computed } from 'vue'

const giCategories = ['Comida', 'Transporte', 'Entretenimiento', 'Salario', 'Freelance', 'Servicios']
const transactions = ref([
  { id: '1', type: 'gasto', date: '2026-07-21', description: 'Uber Eats', category: 'Comida', amount: -189 },
  { id: '2', type: 'ingreso', date: '2026-07-20', description: 'Nómina quincenal', category: 'Salario', amount: 18500 },
  { id: '3', type: 'gasto', date: '2026-07-19', description: 'Gasolina', category: 'Transporte', amount: -850 },
])

const showRegistroModal = ref(false)
const registroForm = ref({ type: '', date: '2026-07-24', description: '', category: '', amount: null })
const registroSuccess = ref('')
const registroError = ref('')
const registroSubmitting = ref(false)
const tableExpanded = ref(true)

const registroFormValid = computed(() =>
  registroForm.value.type && registroForm.value.date && registroForm.value.description &&
  registroForm.value.category && registroForm.value.amount > 0
)

const totalIncome = computed(() => transactions.value.filter(r => r.amount > 0).reduce((s, r) => s + r.amount, 0))
const totalExpenses = computed(() => transactions.value.filter(r => r.amount < 0).reduce((s, r) => s + Math.abs(r.amount), 0))
const balance = computed(() => totalIncome.value - totalExpenses.value)

function formatMoney(n) { return (n || 0).toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }
function formatDate(d) { if (!d) return ''; const [y,m,dd] = d.split('-'); return `${dd}/${m}/${y}` }

function openNewRegistro() {
  registroForm.value = { type: '', date: '2026-07-24', description: '', category: '', amount: null }
  registroError.value = ''
  registroSuccess.value = ''
  showRegistroModal.value = true
}

function submitRegistro() {
  if (!registroFormValid.value) return
  registroSubmitting.value = true
  setTimeout(() => {
    const signed = registroForm.value.type === 'ingreso' ? registroForm.value.amount : -registroForm.value.amount
    transactions.value.unshift({
      id: String(Date.now()),
      type: registroForm.value.type,
      date: registroForm.value.date,
      description: registroForm.value.description,
      category: registroForm.value.category,
      amount: signed,
    })
    registroSuccess.value = `✅ ${registroForm.value.type === 'ingreso' ? 'Ingreso' : 'Gasto'} registrado: $${formatMoney(registroForm.value.amount)}`
    registroForm.value = { type: '', date: '2026-07-24', description: '', category: '', amount: null }
    registroSubmitting.value = false
    setTimeout(() => { registroSuccess.value = '' }, 3000)
  }, 600)
}

function closeRegistroModal() { showRegistroModal.value = false }
</script>

<template>
  <div class="demo-gi">
    <div class="demo-label"><span class="demo-badge">Demo interactiva</span> Prueba registrar un gasto o ingreso y observa cómo se actualiza el resumen.</div>

    <!-- Header -->
    <div class="page-header">
      <h2 class="page-title">Gastos / Ingresos</h2>
      <button class="btn-register" @click="openNewRegistro">
        <i class="pi pi-plus"></i> Registrar
      </button>
    </div>

    <!-- Modal Registro -->
    <div v-if="showRegistroModal" class="modal-overlay" @click.self="closeRegistroModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3><i class="pi pi-plus-circle"></i> Nuevo Registro</h3>
          <button class="btn-close" @click="closeRegistroModal"><i class="pi pi-times"></i></button>
        </div>
        <div class="modal-body">
          <div class="modal-field-row">
            <div class="modal-field">
              <label>Tipo</label>
              <select v-model="registroForm.type" class="form-input">
                <option value="">Seleccionar...</option>
                <option value="ingreso">Ingreso</option>
                <option value="gasto">Gasto</option>
              </select>
            </div>
            <div class="modal-field">
              <label>Fecha</label>
              <input type="date" v-model="registroForm.date" class="form-input" />
            </div>
          </div>
          <div class="modal-field">
            <label>Descripción</label>
            <input type="text" v-model="registroForm.description" class="form-input" placeholder="Ej: Salario mensual" />
          </div>
          <div class="modal-field-row">
            <div class="modal-field">
              <label>Categoría</label>
              <select v-model="registroForm.category" class="form-input">
                <option value="">Seleccionar...</option>
                <option v-for="cat in giCategories" :key="cat" :value="cat">{{ cat }}</option>
              </select>
            </div>
            <div class="modal-field">
              <label>Monto ($)</label>
              <div class="field-input-wrap">
                <span class="field-prefix">$</span>
                <input type="number" step="0.01" min="0.01" class="field-input" placeholder="0.00" v-model.number="registroForm.amount" />
              </div>
            </div>
          </div>
          <div v-if="registroError" class="modal-error"><i class="pi pi-exclamation-triangle"></i> {{ registroError }}</div>
          <div v-if="registroSuccess" class="modal-success">{{ registroSuccess }}</div>
        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="closeRegistroModal">Cerrar</button>
          <button class="btn-confirm" :disabled="registroSubmitting || !registroFormValid" @click="submitRegistro">
            <i :class="registroSubmitting ? 'pi pi-spin pi-spinner' : 'pi pi-check'"></i>
            {{ registroSubmitting ? 'Registrando...' : 'Registrar' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Stats Cards -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon income-icon"><i class="pi pi-arrow-up"></i></div>
        <div class="stat-info">
          <span class="stat-label">Ingresos Totales</span>
          <span class="stat-value income">+${{ formatMoney(totalIncome) }}</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon expense-icon"><i class="pi pi-arrow-down"></i></div>
        <div class="stat-info">
          <span class="stat-label">Gastos Totales</span>
          <span class="stat-value expense">-${{ formatMoney(totalExpenses) }}</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon balance-icon"><i class="pi pi-wallet"></i></div>
        <div class="stat-info">
          <span class="stat-label">Balance</span>
          <span class="stat-value" :class="balance >= 0 ? 'income' : 'expense'">{{ balance >= 0 ? '+' : '-' }}${{ formatMoney(Math.abs(balance)) }}</span>
        </div>
      </div>
    </div>

    <!-- Tabla -->
    <div class="table-card">
      <div class="table-accordion-header" @click="tableExpanded = !tableExpanded">
        <span class="table-accordion-title"><i class="pi pi-list"></i> Registros</span>
        <i :class="tableExpanded ? 'pi pi-chevron-up' : 'pi pi-chevron-down'"></i>
      </div>
      <div v-show="tableExpanded" class="table-accordion-body">
        <table class="data-table">
          <thead>
            <tr>
              <th>Fecha</th>
              <th>Descripción</th>
              <th>Categoría</th>
              <th>Monto</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in transactions" :key="item.id">
              <td>{{ formatDate(item.date) }}</td>
              <td>{{ item.description }}</td>
              <td><span class="category-badge">{{ item.category }}</span></td>
              <td :class="item.amount > 0 ? 'income' : 'expense'">
                {{ item.amount > 0 ? '+' : '' }}${{ formatMoney(Math.abs(item.amount)) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<style scoped>
.demo-gi {
  --fin-bg: #0f1419;
  --fin-surface: #15202b;
  --fin-surface-2: #1c2b3a;
  --fin-border: #2d3741;
  --fin-text: #e1e8ed;
  --fin-text-muted: #8899a6;
  --fin-hover: #1c2b3a;

  background: var(--fin-bg);
  border: 1px solid var(--fin-border);
  border-radius: 14px;
  padding: 1.5rem;
  margin: 1.5rem 0;
}

.demo-label { margin-bottom: 1.25rem; color: var(--fin-text-muted); font-size: 0.85rem; }
.demo-badge { background: #F0A500; color: #2D2B6B; font-size: 0.7rem; font-weight: 700; padding: 2px 8px; border-radius: 4px; text-transform: uppercase; margin-right: 8px; }

.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-title { font-size: 1.4rem; font-weight: 700; color: var(--fin-text); margin: 0; }

.btn-register { background-color: #1da1f2; color: white; border: none; padding: 10px 20px; border-radius: 8px; font-size: 0.9rem; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 8px; }
.btn-register:hover { background-color: #1a91da; }

/* Modal */
.modal-overlay { position: fixed; inset: 0; background-color: rgba(0,0,0,0.6); display: flex; align-items: center; justify-content: center; z-index: 1000; backdrop-filter: blur(2px); }
.modal-content { background-color: var(--fin-surface); border: 1px solid var(--fin-border); border-radius: 14px; width: 90%; max-width: 520px; max-height: 85vh; overflow-y: auto; }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 18px 20px; border-bottom: 1px solid var(--fin-border); }
.modal-header h3 { color: var(--fin-text); margin: 0; display: flex; align-items: center; gap: 8px; font-size: 1rem; }
.btn-close { background: transparent; border: none; color: var(--fin-text-muted); font-size: 1.1rem; cursor: pointer; }
.modal-body { padding: 20px; display: flex; flex-direction: column; gap: 14px; }
.modal-field { display: flex; flex-direction: column; gap: 6px; }
.modal-field label { font-size: 0.75rem; text-transform: uppercase; color: var(--fin-text-muted); font-weight: 600; }
.modal-field-row { display: flex; gap: 12px; }
.modal-field-row .modal-field { flex: 1; }
.form-input { background-color: var(--fin-surface-2); border: 1px solid var(--fin-border); border-radius: 8px; padding: 10px 14px; color: var(--fin-text); font-size: 0.9rem; }
.form-input:focus { outline: none; border-color: #1da1f2; }
.field-input-wrap { display: flex; align-items: center; background-color: var(--fin-surface-2); border: 1px solid var(--fin-border); border-radius: 8px; overflow: hidden; }
.field-input-wrap:focus-within { border-color: #1da1f2; }
.field-prefix { padding: 0 10px; color: var(--fin-text-muted); font-size: 0.9rem; border-right: 1px solid var(--fin-border); line-height: 38px; }
.field-input { flex: 1; background: transparent; border: none; outline: none; color: var(--fin-text); font-size: 0.9rem; padding: 9px 12px; }
.modal-error { padding: 10px 14px; border-radius: 8px; background-color: rgba(239,68,68,0.15); color: #ef4444; border: 1px solid rgba(239,68,68,0.3); font-size: 0.85rem; }
.modal-success { padding: 10px 14px; border-radius: 8px; background-color: rgba(16,185,129,0.15); color: #10b981; border: 1px solid rgba(16,185,129,0.3); font-size: 0.85rem; }
.modal-footer { display: flex; justify-content: flex-end; gap: 10px; padding: 16px 20px; border-top: 1px solid var(--fin-border); }
.btn-cancel { background-color: var(--fin-surface-2); color: var(--fin-text-muted); border: 1px solid var(--fin-border); padding: 10px 18px; border-radius: 8px; font-size: 0.85rem; cursor: pointer; }
.btn-cancel:hover { color: var(--fin-text); border-color: #1da1f2; }
.btn-confirm { background-color: #1da1f2; color: white; border: none; padding: 10px 18px; border-radius: 8px; font-size: 0.85rem; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 6px; }
.btn-confirm:hover { background-color: #1a91da; }
.btn-confirm:disabled { opacity: 0.6; cursor: not-allowed; }

/* Stats */
.stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 20px; }
.stat-card { background-color: var(--fin-surface); border: 1px solid var(--fin-border); border-radius: 12px; padding: 16px; display: flex; align-items: center; gap: 12px; }
.stat-icon { width: 42px; height: 42px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 1.1rem; }
.stat-icon.income-icon { background-color: rgba(16,185,129,0.15); color: #10b981; }
.stat-icon.expense-icon { background-color: rgba(239,68,68,0.15); color: #ef4444; }
.stat-icon.balance-icon { background-color: rgba(29,161,242,0.15); color: #1da1f2; }
.stat-info { display: flex; flex-direction: column; }
.stat-label { font-size: 0.75rem; color: var(--fin-text-muted); margin-bottom: 2px; }
.stat-value { font-size: 1.1rem; font-weight: 700; color: var(--fin-text); }
.income { color: #10b981 !important; }
.expense { color: #ef4444 !important; }

/* Table */
.table-card { background-color: var(--fin-surface); border: 1px solid var(--fin-border); border-radius: 12px; overflow: hidden; }
.table-accordion-header { display: flex; justify-content: space-between; align-items: center; padding: 14px 20px; cursor: pointer; }
.table-accordion-header:hover { background-color: var(--fin-surface-2); }
.table-accordion-title { color: var(--fin-text); font-size: 0.95rem; font-weight: 600; display: flex; align-items: center; gap: 8px; }
.table-accordion-header > i { color: var(--fin-text-muted); }
.table-accordion-body { overflow-x: auto; }
.data-table { width: 100%; border-collapse: collapse; }
.data-table th { text-align: left; padding: 12px 20px; font-size: 0.75rem; text-transform: uppercase; color: var(--fin-text-muted); border-bottom: 1px solid var(--fin-border); background-color: var(--fin-surface-2); }
.data-table td { padding: 12px 20px; font-size: 0.85rem; color: var(--fin-text); border-bottom: 1px solid var(--fin-border); }
.category-badge { background-color: var(--fin-surface-2); padding: 3px 10px; border-radius: 12px; font-size: 0.75rem; color: var(--fin-text-muted); }

@media (max-width: 640px) {
  .stats-grid { grid-template-columns: 1fr; }
  .modal-field-row { flex-direction: column; gap: 14px; }
}
</style>
