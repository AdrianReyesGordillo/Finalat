<template>
  <div class="gastos-ingresos">
    <div class="page-header">
      <h1 class="page-title">Gastos / Ingresos</h1>
      <button class="btn-register" @click="openNewRegistro">
        <i class="pi pi-plus"></i> Registrar
      </button>
    </div>

    <!-- Modal Registro -->
    <div v-if="showRegistroModal" class="modal-overlay" @click.self="closeRegistroModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3><i class="pi pi-plus-circle"></i> {{ editingRecordId ? 'Editar Registro' : 'Nuevo Registro' }}</h3>
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
                <input type="number" step="0.01" min="0.01" class="field-input"
                  placeholder="0.00" v-model.number="registroForm.amount" />
              </div>
            </div>
          </div>

          <div v-if="registroError" class="modal-error">
            <i class="pi pi-exclamation-triangle"></i> {{ registroError }}
          </div>
          <div v-if="registroSuccess" class="modal-success">
            {{ registroSuccess }}
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn-cancel" @click="closeRegistroModal">Cerrar</button>
          <button
            class="btn-confirm"
            :disabled="registroSubmitting || !registroFormValid"
            @click="submitRegistro"
          >
            <i :class="registroSubmitting ? 'pi pi-spin pi-spinner' : 'pi pi-check'"></i>
            {{ registroSubmitting ? 'Registrando...' : 'Registrar' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Filtros -->
    <div class="filters-bar">
      <div class="filter-group">
        <label>Mes</label>
        <select v-model="filters.month" class="filter-input">
          <option value="">Todos</option>
          <option v-for="m in monthOptions" :key="m.value" :value="m.value">{{ m.label }}</option>
        </select>
      </div>
      <div class="filter-group">
        <label>Categoría</label>
        <select v-model="filters.category" class="filter-input">
          <option value="">Todas</option>
          <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
        </select>
      </div>
      <div class="filter-group">
        <label>Tipo</label>
        <select v-model="filters.type" class="filter-input">
          <option value="">Todos</option>
          <option value="ingreso">Ingreso</option>
          <option value="gasto">Gasto</option>
        </select>
      </div>
      <button class="btn-clear" @click="clearFilters">
        <i class="pi pi-filter-slash"></i> Limpiar
      </button>
    </div>

    <!-- Stats Cards -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon income-icon"><i class="pi pi-arrow-up"></i></div>
        <div class="stat-info">
          <span class="stat-label">Ingresos Totales</span>
          <span class="stat-value">+${{ formatMoney(totalIncome) }}</span>
          <span v-if="filters.month" class="stat-sub" :class="incomeVsPrev === null ? '' : incomeVsPrev >= 0 ? 'income' : 'expense'">
            {{ incomeVsPrev === null ? 'Sin datos mes anterior' : (incomeVsPrev >= 0 ? '+' : '') + incomeVsPrev + '% vs ' + prevMonthLabel }}
          </span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon expense-icon"><i class="pi pi-arrow-down"></i></div>
        <div class="stat-info">
          <span class="stat-label">Gastos Totales</span>
          <span class="stat-value">-${{ formatMoney(totalExpenses) }}</span>
          <span v-if="filters.month" class="stat-sub" :class="expensesVsPrev === null ? '' : expensesVsPrev > 0 ? 'expense' : 'income'">
            {{ expensesVsPrev === null ? 'Sin datos mes anterior' : (expensesVsPrev >= 0 ? '+' : '') + expensesVsPrev + '% vs ' + prevMonthLabel }}
          </span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon balance-icon"><i class="pi pi-wallet"></i></div>
        <div class="stat-info">
          <span class="stat-label">Balance</span>
          <span class="stat-value">
            {{ balance >= 0 ? '+' : '-' }}${{ formatMoney(Math.abs(balance)) }}
          </span>
          <span v-if="filters.month" class="stat-sub" :class="balanceVsPrev === null ? '' : balanceVsPrev >= 0 ? 'income' : 'expense'">
            {{ balanceVsPrev === null ? 'Sin datos mes anterior' : (balanceVsPrev >= 0 ? '+' : '') + balanceVsPrev + '% vs ' + prevMonthLabel }}
          </span>
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
            <tr v-for="item in filteredAndSorted" :key="item.id" class="clickable-row" @click="openDetailModal(item)">
              <td>{{ formatDate(item.date) }}</td>
              <td>{{ item.description }}</td>
              <td><span class="category-badge">{{ item.category }}</span></td>
              <td :class="item.amount > 0 ? 'income' : 'expense'">
                {{ item.amount > 0 ? '+' : '' }}${{ formatMoney(Math.abs(item.amount)) }}
              </td>
            </tr>
            <tr v-if="filteredAndSorted.length === 0">
              <td colspan="4" class="empty-row">No hay registros que coincidan con los filtros</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Modal Detalle / Acciones -->
    <div v-if="showDetailModal" class="modal-overlay" @click.self="showDetailModal = false">
      <div class="modal-content modal-sm">
        <div class="modal-header">
          <h3><i class="pi pi-info-circle"></i> Detalle del Registro</h3>
          <button class="btn-close" @click="showDetailModal = false"><i class="pi pi-times"></i></button>
        </div>

        <div class="modal-body">
          <div class="detail-summary">
            <div class="detail-summary-row">
              <span class="detail-label">Fecha</span>
              <span class="detail-value">{{ formatDate(selectedRecord.date) }}</span>
            </div>
            <div class="detail-summary-row">
              <span class="detail-label">Descripción</span>
              <span class="detail-value">{{ selectedRecord.description }}</span>
            </div>
            <div class="detail-summary-row">
              <span class="detail-label">Categoría</span>
              <span class="detail-value">{{ selectedRecord.category }}</span>
            </div>
            <div class="detail-summary-row">
              <span class="detail-label">Tipo</span>
              <span class="detail-value">{{ selectedRecord.amount > 0 ? 'Ingreso' : 'Gasto' }}</span>
            </div>
            <div class="detail-summary-row">
              <span class="detail-label">Monto</span>
              <span class="detail-value" :class="selectedRecord.amount > 0 ? 'income' : 'expense'">
                {{ selectedRecord.amount > 0 ? '+' : '-' }}${{ formatMoney(Math.abs(selectedRecord.amount)) }}
              </span>
            </div>
          </div>
        </div>

        <div class="modal-footer detail-actions">
          <button class="btn-edit" @click="editRecord">
            <i class="pi pi-pencil"></i> Editar
          </button>
          <button class="btn-delete" :disabled="deleting" @click="deleteRecord">
            <i :class="deleting ? 'pi pi-spin pi-spinner' : 'pi pi-trash'"></i>
            {{ deleting ? 'Eliminando...' : 'Eliminar' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Gráficas -->
    <div class="charts-row">
      <div class="chart-card">
        <h3>Ingresos vs Gastos</h3>
        <Line :data="lineChartData" :options="chartOptions" />
      </div>
      <div class="chart-card">
        <h3>Balance Mensual</h3>
        <Line :data="balanceChartData" :options="chartOptions" />
      </div>
    </div>

    <div class="charts-row">
      <div class="chart-card">
        <h3>Ingresos vs (Gastos + Créditos)</h3>
        <Line :data="lineChartWithPayments" :options="chartOptions" />
      </div>
      <div class="chart-card">
        <div class="chart-header">
          <h3>Gastos por Crédito vs Ingreso Fijo</h3>
          <button class="btn-edit-inline" @click="showIngresoFijoModal = true">
            <i class="pi pi-pencil"></i>
          </button>
        </div>
        <Line :data="gastosCreditoChartData" :options="chartOptions" />
      </div>
    </div>

    <div class="charts-row">
      <div class="chart-card">
        <h3>Patrimonio Neto</h3>
        <Line :data="patrimonioChartData" :options="chartOptions" />
      </div>
      <div class="chart-card">
        <h3>Ingresos por Categoría</h3>
        <Bar :data="ingresosCategoriaBarData" :options="barChartOptions" />
      </div>
    </div>

    <!-- Modal Ingreso Fijo -->
    <div v-if="showIngresoFijoModal" class="modal-overlay" @click.self="showIngresoFijoModal = false">
      <div class="modal-content modal-sm">
        <div class="modal-header">
          <h3><i class="pi pi-pencil"></i> Ingreso Fijo Mensual</h3>
          <button class="btn-close" @click="showIngresoFijoModal = false"><i class="pi pi-times"></i></button>
        </div>
        <div class="modal-body">
          <div class="modal-field">
            <label>Cantidad mensual ($)</label>
            <div class="field-input-wrap">
              <span class="field-prefix">$</span>
              <input type="number" step="1" min="0" class="field-input" v-model.number="ingresoFijoInput" placeholder="6000" />
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="showIngresoFijoModal = false">Cancelar</button>
          <button class="btn-confirm" @click="saveIngresoFijo">
            <i class="pi pi-check"></i> Guardar
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Line, Bar } from 'vue-chartjs'
import finApi from '../utils/api'
import { cachedGet } from '../utils/cache'
import { formatMoney } from '../utils/format.js'
import { usePreferencesStore } from '../stores/preferences'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, Title, Tooltip, Legend, Filler)

const prefsStore = usePreferencesStore()
if (!prefsStore.loaded) {
  prefsStore.load()
}

const transactions = ref([])
const creditCards = ref([])
const tableExpanded = ref(false)
// ===== MODAL REGISTRO =====
const showRegistroModal = ref(false)
const registroSubmitting = ref(false)
const registroError = ref('')
const registroSuccess = ref('')
const giCategories = ref([])

async function loadCategories() {
  try {
    const response = await cachedGet('/api/gi/categories')
    giCategories.value = response.data.map(c => c.name)
  } catch (error) {
    // Fallback to defaults if API fails
    giCategories.value = ['Freelance', 'Delivery', 'Sueldo', 'Creditos', 'Prestamos', 'Otros']
  }
}

// Helper to get today's date in local timezone (YYYY-MM-DD)
function getLocalDate() {
  const now = new Date()
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
}

const registroForm = ref({
  type: '',
  date: getLocalDate(),
  description: '',
  category: '',
  amount: null
})

const registroFormValid = computed(() =>
  registroForm.value.type &&
  registroForm.value.date &&
  registroForm.value.description &&
  registroForm.value.category &&
  registroForm.value.amount > 0
)

async function submitRegistro() {
  registroSubmitting.value = true
  registroError.value = ''
  registroSuccess.value = ''
  try {
    if (editingRecordId.value) {
      // Update existing record
      await finApi.put(`/api/gi/records/${editingRecordId.value}`, {
        date: registroForm.value.date,
        description: registroForm.value.description,
        category: registroForm.value.category,
        type: registroForm.value.type,
        amount: registroForm.value.amount
      })
      registroSuccess.value = '✅ Registro actualizado'
      editingRecordId.value = null
    } else {
      // Create new record
      await finApi.post('/api/gi/records', {
        date: registroForm.value.date,
        description: registroForm.value.description,
        category: registroForm.value.category,
        type: registroForm.value.type,
        amount: registroForm.value.amount
      })
      registroSuccess.value = `✅ ${registroForm.value.type === 'ingreso' ? 'Ingreso' : 'Gasto'} registrado: $${formatMoney(registroForm.value.amount)}`
    }
    registroForm.value = { type: '', date: getLocalDate(), description: '', category: '', amount: null }
    await loadRecords()
    setTimeout(() => { registroSuccess.value = '' }, 3000)
  } catch (error) {
    registroError.value = error.response?.data?.detail || error.message
    setTimeout(() => { registroError.value = '' }, 4000)
  } finally {
    registroSubmitting.value = false
  }
}

function openNewRegistro() {
  editingRecordId.value = null
  registroForm.value = { type: '', date: getLocalDate(), description: '', category: '', amount: null }
  registroError.value = ''
  registroSuccess.value = ''
  showRegistroModal.value = true
}

function closeRegistroModal() {
  showRegistroModal.value = false
  editingRecordId.value = null
  registroForm.value = { type: '', date: getLocalDate(), description: '', category: '', amount: null }
  registroError.value = ''
  registroSuccess.value = ''
}

// ===== MODAL DETALLE =====
const showDetailModal = ref(false)
const selectedRecord = ref({})
const deleting = ref(false)
const editingRecordId = ref(null)

function openDetailModal(item) {
  selectedRecord.value = item
  showDetailModal.value = true
}

function editRecord() {
  const record = selectedRecord.value
  editingRecordId.value = record.id
  registroForm.value = {
    type: record.amount > 0 ? 'ingreso' : 'gasto',
    date: record.date,
    description: record.description,
    category: record.category,
    amount: Math.abs(record.amount)
  }
  showDetailModal.value = false
  showRegistroModal.value = true
}

async function deleteRecord() {
  deleting.value = true
  try {
    await finApi.delete(`/api/gi/records/${selectedRecord.value.id}`)
    showDetailModal.value = false
    await loadRecords()
  } catch (error) {
    console.error('Error deleting record:', error)
  } finally {
    deleting.value = false
  }
}

async function loadRecords() {
  try {
    const response = await cachedGet('/api/gi/records', { forceRefresh: true })
    transactions.value = response.data.records
  } catch (error) {
    console.error('Error loading records:', error)
  }
}

async function loadCreditos() {
  try {
    const response = await cachedGet('/api/creditos')
    creditCards.value = response.data.cards || []
  } catch (error) {
    console.error('Error loading creditos:', error)
  }
}

// ===== PATRIMONIO NETO =====
const patrimonioHistory = ref([])

async function loadPatrimonio() {
  try {
    const response = await cachedGet('/api/patrimonio')
    patrimonioHistory.value = response.data.history || []
  } catch (error) {
    console.error('Error loading patrimonio:', error)
  }
}

const patrimonioChartData = computed(() => {
  const months = []
  const now = new Date()
  for (let i = 5; i >= 0; i--) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1)
    months.push({
      key: `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`,
      label: d.toLocaleDateString('es-AR', { month: 'short' })
    })
  }

  const data = months.map(m => {
    const entry = patrimonioHistory.value.find(h => h.month === m.key)
    return entry ? entry.value : 0
  })

  return {
    labels: months.map(m => m.label),
    datasets: [{
      label: 'Patrimonio Neto',
      data,
      borderColor: '#1da1f2',
      backgroundColor: 'rgba(29, 161, 242, 0.1)',
      fill: true,
      tension: 0.4
    }]
  }
})

const balanceChartData = computed(() => {
  const months = []
  const now = new Date()
  for (let i = 5; i >= 0; i--) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1)
    months.push({
      key: `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`,
      label: d.toLocaleDateString('es-AR', { month: 'short' })
    })
  }

  const data = months.map(m => {
    const income = transactions.value.filter(r => r.date && r.date.startsWith(m.key) && r.amount > 0).reduce((s, r) => s + r.amount, 0)
    const expense = transactions.value.filter(r => r.date && r.date.startsWith(m.key) && r.amount < 0).reduce((s, r) => s + Math.abs(r.amount), 0)
    return income - expense
  })

  return {
    labels: months.map(m => m.label),
    datasets: [{
      label: 'Balance',
      data,
      borderColor: '#8b5cf6',
      backgroundColor: 'rgba(139, 92, 246, 0.1)',
      fill: true,
      tension: 0.4
    }]
  }
})

const ingresoFijo = ref(0)
const showIngresoFijoModal = ref(false)
const ingresoFijoInput = ref(0)

function saveIngresoFijo() {
  if (ingresoFijoInput.value >= 0) {
    ingresoFijo.value = ingresoFijoInput.value
    prefsStore.save('ingreso_fijo', String(ingresoFijoInput.value))
  }
  showIngresoFijoModal.value = false
}

const gastosCreditoChartData = computed(() => {
  const months = []
  const now = new Date()
  // 4 meses atrás, mes actual, 1 mes adelante
  for (let i = 4; i >= -1; i--) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1)
    months.push({
      key: `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`,
      label: d.toLocaleDateString('es-AR', { month: 'short' })
    })
  }

  // Pagos mínimos de tarjetas agrupados por mes de vencimiento
  const cardPaymentsByMonth = {}
  creditCards.value.forEach(c => {
    if (c.paymentDate) {
      const monthKey = c.paymentDate.substring(0, 7)
      if (!cardPaymentsByMonth[monthKey]) cardPaymentsByMonth[monthKey] = 0
      cardPaymentsByMonth[monthKey] += (c.minimumPayment || 0)
    }
  })

  const creditData = months.map(m => {
    const gastos = transactions.value
      .filter(r => r.date && r.date.startsWith(m.key) && r.amount < 0 && r.category === 'Creditos')
      .reduce((s, r) => s + Math.abs(r.amount), 0)
    const cardPayments = cardPaymentsByMonth[m.key] || 0
    return gastos + cardPayments
  })

  const incomeData = months.map(() => ingresoFijo.value)

  return {
    labels: months.map(m => m.label),
    datasets: [
      {
        label: 'Ingreso Fijo',
        data: incomeData,
        borderColor: '#10b981',
        backgroundColor: 'rgba(16, 185, 129, 0.05)',
        fill: false,
        tension: 0,
        borderDash: [6, 4]
      },
      {
        label: 'Gastos por Crédito',
        data: creditData,
        borderColor: '#f59e0b',
        backgroundColor: 'rgba(245, 158, 11, 0.1)',
        fill: true,
        tension: 0.4
      }
    ]
  }
})

onMounted(() => {
  const saved = prefsStore.preferences['ingreso_fijo']
  if (saved) {
    ingresoFijo.value = Number(saved)
    ingresoFijoInput.value = Number(saved)
  }
  loadRecords()
  loadCreditos()
  loadPatrimonio()
  loadCategories()
})

const filters = ref({
  month: (() => {
    const now = new Date()
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
  })(),
  category: '',
  type: ''
})

const monthOptions = computed(() => {
  const options = []
  const now = new Date()
  for (let i = 0; i < 6; i++) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1)
    const value = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
    const label = d.toLocaleDateString('es-AR', { month: 'long', year: 'numeric' })
    options.push({ value, label: label.charAt(0).toUpperCase() + label.slice(1) })
  }
  return options
})

const categories = computed(() => {
  const cats = new Set(transactions.value.map(t => t.category))
  return [...cats].sort()
})

const filteredAndSorted = computed(() => {
  let result = [...transactions.value]

  // Filtro por mes
  if (filters.value.month) {
    result = result.filter(t => t.date && t.date.startsWith(filters.value.month))
  }

  // Filtro por categoría
  if (filters.value.category) {
    result = result.filter(t => t.category === filters.value.category)
  }

  // Filtro por tipo (ingreso/gasto)
  if (filters.value.type) {
    if (filters.value.type === 'ingreso') {
      result = result.filter(t => t.amount > 0)
    } else {
      result = result.filter(t => t.amount < 0)
    }
  }

  // Ordenamiento fijo: fecha más reciente primero
  result.sort((a, b) => {
    if (a.date < b.date) return 1
    if (a.date > b.date) return -1
    return 0
  })

  return result
})

const totalIncome = computed(() => {
  return filteredAndSorted.value
    .filter(t => t.amount > 0)
    .reduce((sum, t) => sum + t.amount, 0)
})

const totalExpenses = computed(() => {
  return filteredAndSorted.value
    .filter(t => t.amount < 0)
    .reduce((sum, t) => sum + Math.abs(t.amount), 0)
})

const balance = computed(() => {
  return totalIncome.value - totalExpenses.value
})

// Balance del mes anterior para comparación (reactivo al filtro)
const prevMonthBalance = computed(() => {
  const now = new Date()
  let refYear, refMonth

  if (filters.value.month) {
    const [y, m] = filters.value.month.split('-').map(Number)
    refYear = y
    refMonth = m
  } else {
    refYear = now.getFullYear()
    refMonth = now.getMonth() + 1
  }

  // Mes anterior al seleccionado
  const prevDate = new Date(refYear, refMonth - 2, 1)
  const prevKey = `${prevDate.getFullYear()}-${String(prevDate.getMonth() + 1).padStart(2, '0')}`
  const prevRecords = transactions.value.filter(r => r.date && r.date.startsWith(prevKey))
  const inc = prevRecords.filter(r => r.amount > 0).reduce((s, r) => s + r.amount, 0)
  const exp = prevRecords.filter(r => r.amount < 0).reduce((s, r) => s + Math.abs(r.amount), 0)
  return inc - exp
})

const balanceVsPrev = computed(() => {
  if (!prevMonthBalance.value) return null
  return Math.round(((balance.value - prevMonthBalance.value) / Math.abs(prevMonthBalance.value)) * 100)
})

const incomeVsPrev = computed(() => {
  if (!prevMonthIncome.value) return null
  return Math.round(((totalIncome.value - prevMonthIncome.value) / prevMonthIncome.value) * 100)
})

const expensesVsPrev = computed(() => {
  if (!prevMonthExpenses.value) return null
  return Math.round(((totalExpenses.value - prevMonthExpenses.value) / prevMonthExpenses.value) * 100)
})

const prevMonthIncome = computed(() => {
  const now = new Date()
  let refYear, refMonth
  if (filters.value.month) {
    const [y, m] = filters.value.month.split('-').map(Number)
    refYear = y
    refMonth = m
  } else {
    refYear = now.getFullYear()
    refMonth = now.getMonth() + 1
  }
  const prevDate = new Date(refYear, refMonth - 2, 1)
  const prevKey = `${prevDate.getFullYear()}-${String(prevDate.getMonth() + 1).padStart(2, '0')}`
  return transactions.value.filter(r => r.date && r.date.startsWith(prevKey) && r.amount > 0).reduce((s, r) => s + r.amount, 0)
})

const prevMonthExpenses = computed(() => {
  const now = new Date()
  let refYear, refMonth
  if (filters.value.month) {
    const [y, m] = filters.value.month.split('-').map(Number)
    refYear = y
    refMonth = m
  } else {
    refYear = now.getFullYear()
    refMonth = now.getMonth() + 1
  }
  const prevDate = new Date(refYear, refMonth - 2, 1)
  const prevKey = `${prevDate.getFullYear()}-${String(prevDate.getMonth() + 1).padStart(2, '0')}`
  return transactions.value.filter(r => r.date && r.date.startsWith(prevKey) && r.amount < 0).reduce((s, r) => s + Math.abs(r.amount), 0)
})

const prevMonthLabel = computed(() => {
  const now = new Date()
  let refYear, refMonth

  if (filters.value.month) {
    const [y, m] = filters.value.month.split('-').map(Number)
    refYear = y
    refMonth = m
  } else {
    refYear = now.getFullYear()
    refMonth = now.getMonth() + 1
  }

  const prevDate = new Date(refYear, refMonth - 2, 1)
  const label = prevDate.toLocaleDateString('es-AR', { month: 'long' })
  return label.charAt(0).toUpperCase() + label.slice(1)
})

function formatDate(dateStr) {
  const date = new Date(dateStr + 'T00:00:00')
  return date.toLocaleDateString('es-AR', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

function clearFilters() {
  filters.value = { month: '', category: '', type: '' }
}

// ===== GRÁFICAS =====
const chartOptions = {
  responsive: true,
  plugins: {
    legend: { position: 'bottom', labels: { color: '#8899a6' } }
  },
  scales: {
    x: { ticks: { color: '#8899a6' }, grid: { color: 'rgba(120,135,150,0.18)' } },
    y: { ticks: { color: '#8899a6' }, grid: { color: 'rgba(120,135,150,0.18)' } }
  }
}

const barColors = ['#f59e0b', '#8b5cf6', '#1da1f2', '#10b981', '#ef4444', '#ec4899', '#06b6d4', '#84cc16']

const barChartOptions = {
  indexAxis: 'y',
  responsive: true,
  plugins: {
    legend: { position: 'bottom', labels: { color: '#8899a6' } }
  },
  scales: {
    x: { stacked: true, ticks: { color: '#8899a6' }, grid: { color: 'rgba(120,135,150,0.18)' } },
    y: { stacked: true, ticks: { color: '#8899a6' }, grid: { color: 'rgba(120,135,150,0.18)' } }
  }
}

const ingresosCategoriaBarData = computed(() => {
  const months = []
  const now = new Date()
  for (let i = 5; i >= 0; i--) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1)
    months.push({
      key: `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`,
      label: d.toLocaleDateString('es-AR', { month: 'short' })
    })
  }

  // Only show categories that have at least one income record
  const incomeRecords = transactions.value.filter(r => r.amount > 0)
  const categoriesWithIncome = [...new Set(incomeRecords.map(r => r.category || 'Sin categoría'))]

  const datasets = categoriesWithIncome.map((cat, i) => ({
    label: cat,
    data: months.map(m =>
      transactions.value
        .filter(r => r.date && r.date.startsWith(m.key) && r.amount > 0 && (r.category || 'Sin categoría') === cat)
        .reduce((s, r) => s + r.amount, 0)
    ),
    backgroundColor: barColors[i % barColors.length]
  }))

  return {
    labels: months.map(m => m.label),
    datasets
  }
})

// Gráfica 1: Ingresos vs Gastos (6 meses)
const lineChartData = computed(() => {
  const months = []
  const now = new Date()
  for (let i = 5; i >= 0; i--) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1)
    months.push({
      key: `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`,
      label: d.toLocaleDateString('es-AR', { month: 'short' })
    })
  }

  const incomeData = months.map(m =>
    transactions.value.filter(r => r.date && r.date.startsWith(m.key) && r.amount > 0).reduce((s, r) => s + r.amount, 0)
  )
  const expenseData = months.map(m =>
    transactions.value.filter(r => r.date && r.date.startsWith(m.key) && r.amount < 0).reduce((s, r) => s + Math.abs(r.amount), 0)
  )

  return {
    labels: months.map(m => m.label),
    datasets: [
      {
        label: 'Ingresos',
        data: incomeData,
        borderColor: '#10b981',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        fill: true,
        tension: 0.4
      },
      {
        label: 'Gastos',
        data: expenseData,
        borderColor: '#ef4444',
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
        fill: true,
        tension: 0.4
      }
    ]
  }
})

// Gráfica 2: Ingresos vs Gastos + Pagos mínimos del mes actual
const lineChartWithPayments = computed(() => {
  const months = []
  const now = new Date()
  // 4 meses atrás, mes actual, 1 mes adelante
  for (let i = 4; i >= -1; i--) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1)
    months.push({
      key: `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`,
      label: d.toLocaleDateString('es-AR', { month: 'short' }),
      month: d.getMonth(),
      year: d.getFullYear()
    })
  }

  // Pagos mínimos de tarjetas agrupados por mes de vencimiento
  const paymentsByMonth = {}
  creditCards.value.forEach(c => {
    if (c.paymentDate) {
      const monthKey = c.paymentDate.substring(0, 7)
      if (!paymentsByMonth[monthKey]) paymentsByMonth[monthKey] = 0
      paymentsByMonth[monthKey] += (c.minimumPayment || 0)
    }
  })

  const incomeData = months.map(m =>
    transactions.value.filter(r => r.date && r.date.startsWith(m.key) && r.amount > 0).reduce((s, r) => s + r.amount, 0)
  )

  const expenseData = months.map(m => {
    const gastos = transactions.value.filter(r => r.date && r.date.startsWith(m.key) && r.amount < 0).reduce((s, r) => s + Math.abs(r.amount), 0)
    // Sumar pagos mínimos de tarjetas que vencen en ese mes
    const creditPayments = paymentsByMonth[m.key] || 0
    return gastos + creditPayments
  })

  return {
    labels: months.map(m => m.label),
    datasets: [
      {
        label: 'Ingresos',
        data: incomeData,
        borderColor: '#10b981',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        fill: true,
        tension: 0.4
      },
      {
        label: 'Gastos + Créditos',
        data: expenseData,
        borderColor: '#f59e0b',
        backgroundColor: 'rgba(245, 158, 11, 0.1)',
        fill: true,
        tension: 0.4
      }
    ]
  }
})
</script>

<style scoped>
.gastos-ingresos {
  max-width: 1200px;
}

.page-title {
  font-size: 1.8rem;
  font-weight: 700;
  margin-bottom: 0;
  color: var(--fin-text);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.btn-register {
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

.btn-register:hover {
  background-color: #1a91da;
}

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

.modal-field { display: flex; flex-direction: column; gap: 6px; }
.modal-field label { font-size: 0.75rem; text-transform: uppercase; color: var(--fin-text-muted); font-weight: 600; }
.modal-field-row { display: flex; gap: 12px; }
.modal-field-row .modal-field { flex: 1; }

.field-input-wrap {
  display: flex;
  align-items: center;
  background-color: var(--fin-surface-2);
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

.form-input {
  background-color: var(--fin-surface-2);
  border: 1px solid var(--fin-border);
  border-radius: 8px;
  padding: 10px 14px;
  color: var(--fin-text);
  font-size: 0.9rem;
}
.form-input:focus { outline: none; border-color: #1da1f2; }

.modal-error {
  padding: 10px 14px;
  border-radius: 8px;
  background-color: rgba(239, 68, 68, 0.15);
  color: #ef4444;
  border: 1px solid rgba(239, 68, 68, 0.3);
  font-size: 0.85rem;
}

.modal-success {
  padding: 10px 14px;
  border-radius: 8px;
  background-color: rgba(16, 185, 129, 0.15);
  color: #10b981;
  border: 1px solid rgba(16, 185, 129, 0.3);
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

/* Clickable rows */
.clickable-row { cursor: pointer; }
.clickable-row:hover td { background-color: var(--fin-hover); }

/* Detail modal */
.modal-sm { max-width: 420px; }

.detail-summary { display: flex; flex-direction: column; gap: 10px; }
.detail-summary-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid var(--fin-border);
}
.detail-summary-row:last-child { border-bottom: none; }
.detail-label { color: var(--fin-text-muted); font-size: 0.82rem; }
.detail-value { color: var(--fin-text); font-size: 0.9rem; font-weight: 600; }

.detail-actions {
  justify-content: space-between;
}

.btn-edit {
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
.btn-edit:hover { background-color: #1a91da; }

.btn-delete {
  background-color: rgba(239, 68, 68, 0.15);
  color: #ef4444;
  border: 1px solid rgba(239, 68, 68, 0.3);
  padding: 10px 18px;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
}
.btn-delete:hover { background-color: rgba(239, 68, 68, 0.25); }
.btn-delete:disabled { opacity: 0.6; cursor: not-allowed; }

/* Filtros */
.filters-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: flex-end;
  margin-bottom: 20px;
  padding: 16px;
  background-color: var(--fin-surface);
  border: 1px solid var(--fin-border);
  border-radius: 12px;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.filter-group label {
  font-size: 0.7rem;
  text-transform: uppercase;
  color: var(--fin-text-muted);
  font-weight: 600;
}

.filter-input {
  background-color: var(--fin-surface-2);
  border: 1px solid var(--fin-border);
  border-radius: 6px;
  padding: 8px 12px;
  color: var(--fin-text);
  font-size: 0.85rem;
  min-width: 140px;
}

.filter-input:focus {
  outline: none;
  border-color: #1da1f2;
}

.btn-clear {
  background-color: var(--fin-surface-2);
  border: 1px solid var(--fin-border);
  border-radius: 6px;
  padding: 8px 14px;
  color: var(--fin-text-muted);
  font-size: 0.85rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
}

.btn-clear:hover {
  color: var(--fin-text);
  border-color: #1da1f2;
}

/* Tabla */
.table-card {
  background-color: var(--fin-surface);
  border: 1px solid var(--fin-border);
  border-radius: 12px;
  overflow: hidden;
}

.table-accordion-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 20px;
  cursor: pointer;
  user-select: none;
  transition: background-color 0.2s;
}

.table-accordion-header:hover {
  background-color: var(--fin-surface-2);
}

.table-accordion-title {
  color: var(--fin-text);
  font-size: 0.95rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.table-accordion-header > i {
  color: var(--fin-text-muted);
  font-size: 0.85rem;
}

.table-accordion-body {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th {
  text-align: left;
  padding: 14px 20px;
  font-size: 0.8rem;
  text-transform: uppercase;
  color: var(--fin-text-muted);
  border-bottom: 1px solid var(--fin-border);
  background-color: var(--fin-surface-2);
  user-select: none;
}

.data-table th.sortable {
  cursor: pointer;
  transition: color 0.2s;
}

.data-table th.sortable:hover {
  color: #1da1f2;
}

.data-table th i {
  font-size: 0.7rem;
  margin-left: 6px;
}

.data-table td {
  padding: 14px 20px;
  border-bottom: 1px solid var(--fin-border);
  color: var(--fin-text);
  font-size: 0.9rem;
}

.data-table td.income {
  color: #10b981;
  font-weight: 600;
}

.data-table td.expense {
  color: #ef4444;
  font-weight: 600;
}

.data-table tr:last-child td {
  border-bottom: none;
}

.data-table tr:hover td {
  background-color: var(--fin-hover);
}

.empty-row {
  text-align: center;
  color: var(--fin-text-muted);
  padding: 40px 20px !important;
}

.category-badge {
  background-color: rgba(29, 161, 242, 0.15);
  color: #1da1f2;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 0.75rem;
}

.type-badge {
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
}

.type-badge.fijo {
  background-color: rgba(139, 92, 246, 0.15);
  color: #8b5cf6;
}

.type-badge.unico {
  background-color: rgba(245, 158, 11, 0.15);
  color: #f59e0b;
}

.income {
  color: #10b981;
  font-weight: 600;
}

.expense {
  color: #ef4444;
  font-weight: 600;
}

/* Stats Cards */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin: 16px 0 20px;
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
.stat-icon.income-icon { background-color: rgba(16, 185, 129, 0.15); color: #10b981; }
.stat-icon.expense-icon { background-color: rgba(239, 68, 68, 0.15); color: #ef4444; }
.stat-icon.balance-icon { background-color: rgba(29, 161, 242, 0.15); color: #1da1f2; }
.stat-icon.trend-icon { background-color: rgba(139, 92, 246, 0.15); color: #8b5cf6; }

.stat-info { display: flex; flex-direction: column; }
.stat-label { font-size: 0.8rem; color: var(--fin-text-muted); margin-bottom: 4px; }
.stat-value { font-size: 1.3rem; font-weight: 700; color: var(--fin-text); }
.stat-value.income { color: #10b981; }
.stat-value.expense { color: #ef4444; }
.stat-sub { font-size: 0.7rem; color: var(--fin-text-muted); margin-top: 2px; }
.stat-sub.income { color: #10b981; }
.stat-sub.expense { color: #ef4444; }

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .btn-register {
    width: 100%;
    justify-content: center;
  }

  .filters-bar {
    flex-direction: column;
    gap: 10px;
  }

  .filter-group {
    width: 100%;
  }

  .filter-input {
    width: 100%;
    min-width: unset;
  }

  .btn-clear {
    width: 100%;
    justify-content: center;
  }

  .data-table th,
  .data-table td {
    padding: 10px 12px;
    font-size: 0.8rem;
  }

  .stats-grid {
    grid-template-columns: 1fr;
    gap: 10px;
  }

  .stat-card {
    padding: 14px;
    gap: 10px;
  }

  .modal-content {
    width: 95%;
    max-width: 95vw;
  }

  .modal-field-row {
    flex-direction: column;
    gap: 14px;
  }

  .detail-actions {
    flex-direction: row;
  }
}

@media (max-width: 480px) {
  .page-title {
    font-size: 1.4rem;
  }

  .data-table th:nth-child(3),
  .data-table td:nth-child(3) {
    display: none;
  }

  .data-table th,
  .data-table td {
    padding: 8px 8px;
    font-size: 0.75rem;
  }
}

/* Charts */
.charts-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-top: 20px;
}

.chart-card {
  background-color: var(--fin-surface);
  border: 1px solid var(--fin-border);
  border-radius: 12px;
  padding: 20px;
}

.chart-full {
  margin-top: 20px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-header h3 {
  margin: 0;
}

.btn-edit-inline {
  background: rgba(29, 161, 242, 0.15);
  border: none;
  color: #1da1f2;
  width: 30px;
  height: 30px;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s;
}

.btn-edit-inline:hover {
  background: rgba(29, 161, 242, 0.3);
}

.chart-card h3 {
  color: var(--fin-text);
  font-size: 1rem;
  margin: 0 0 4px 0;
}

.chart-subtitle {
  color: var(--fin-text-muted);
  font-size: 0.75rem;
  margin: 0 0 12px 0;
}

@media (max-width: 768px) {
  .charts-row { grid-template-columns: 1fr; }
  .chart-card { padding: 14px; }
  .chart-card h3 { font-size: 0.9rem; }
}

/* Dark mode: native elements that don't inherit CSS variables well */
:global(.dark-mode) .form-input,
:global(.dark-mode) .filter-input {
  color-scheme: dark;
}

:global(.dark-mode) .form-input option,
:global(.dark-mode) .filter-input option {
  background-color: #192734;
  color: #e1e8ed;
}

:global(.dark-mode) input[type="date"].form-input {
  color-scheme: dark;
}
</style>
