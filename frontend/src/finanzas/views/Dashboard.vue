<template>
  <div class="dashboard">
    <h1 class="page-title">Dashboard Financiero</h1>

    <!-- Resumen Principal -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon patrimony"><i class="pi pi-building"></i></div>
        <div class="stat-info">
          <span class="stat-label">Patrimonio Neto</span>
          <span class="stat-value">${{ formatMoney(patrimony) }}</span>
          <span class="stat-sub" :class="patrimonyVsPrev === null ? '' : patrimonyVsPrev >= 0 ? 'income' : 'expense'">
            {{ patrimonyVsPrev === null ? 'Sin datos mes anterior' : (patrimonyVsPrev >= 0 ? '+' : '') + patrimonyVsPrev + '% vs mes anterior' }}
          </span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon income-icon"><i class="pi pi-arrow-up"></i></div>
        <div class="stat-info">
          <span class="stat-label">Ingresos (mes)</span>
          <span class="stat-value">${{ formatMoney(monthlyIncome) }}</span>
          <span class="stat-sub" :class="incomeVsPrev === null ? '' : incomeVsPrev >= 0 ? 'income' : 'expense'">
            {{ incomeVsPrev === null ? 'Sin datos mes anterior' : (incomeVsPrev >= 0 ? '+' : '') + incomeVsPrev + '% vs mes anterior' }}
          </span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon expense-icon"><i class="pi pi-arrow-down"></i></div>
        <div class="stat-info">
          <span class="stat-label">Gastos (mes)</span>
          <span class="stat-value">${{ formatMoney(monthlyExpenses) }}</span>
          <span class="stat-sub" :class="expensesVsPrev === null ? '' : expensesVsPrev > 0 ? 'expense' : 'income'">
            {{ expensesVsPrev === null ? 'Sin datos mes anterior' : (expensesVsPrev >= 0 ? '+' : '') + expensesVsPrev + '% vs mes anterior' }}
          </span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon savings-icon"><i class="pi pi-percentage"></i></div>
        <div class="stat-info">
          <span class="stat-label">Tasa de Ahorro</span>
          <span class="stat-value">{{ savingsRate }}%</span>
          <span class="stat-sub">Meta: 30%</span>
        </div>
      </div>
    </div>

    <!-- Fila 2: Créditos + Inversiones resumen -->
    <div class="row-2">
      <div class="card credit-summary">
        <div class="card-header">
          <h3>Tarjetas de Crédito</h3>
          <router-link to="/finanzas/creditos" class="card-link">Ver detalle →</router-link>
        </div>
        <div class="credit-bars">
          <div v-for="card in creditCards" :key="card.name" class="credit-bar-item">
            <div class="credit-bar-info">
              <span class="credit-bar-name" :style="{ color: card.color }">{{ card.name }}</span>
              <span class="credit-bar-amount">${{ formatMoney(card.debt) }} / ${{ formatMoney(card.limit) }}</span>
            </div>
            <div class="credit-bar-bg">
              <div class="credit-bar-fill" :style="{ width: card.usage + '%', backgroundColor: card.color }"></div>
            </div>
          </div>
        </div>
        <div class="credit-totals">
          <div class="credit-total-item">
            <span class="ct-label">Deuda Total</span>
            <span class="ct-value expense">${{ formatMoney(totalCreditDebt) }}</span>
          </div>
          <div class="credit-total-item">
            <span class="ct-label">Disponible</span>
            <span class="ct-value income">${{ formatMoney(totalCreditAvailable) }}</span>
          </div>
        </div>

        <div class="payments-section">
          <h4>Próximos Pagos</h4>
          <div class="payments-list">
            <div v-for="payment in upcomingPayments" :key="payment.name" class="payment-item">
              <div class="payment-icon" :style="{ backgroundColor: payment.color + '20', color: payment.color }">
                <i class="pi pi-credit-card"></i>
              </div>
              <div class="payment-info">
                <span class="payment-name">{{ payment.name }}</span>
                <span class="payment-date">{{ payment.date }}</span>
              </div>
              <div class="payment-right">
                <span class="payment-amount" :style="{ color: paymentColor(payment.daysLeft) }">${{ formatMoney(payment.amount) }}</span>
                <span class="payment-days" :style="{ color: paymentColor(payment.daysLeft) }">{{ payment.daysLeft }} días</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="card investments-summary">
        <div class="card-header">
          <h3>Inversiones</h3>
          <router-link to="/finanzas/inversiones" class="card-link">Ver detalle →</router-link>
        </div>
        <div class="inv-breakdown">
          <div class="inv-item" v-if="prefsStore.isPanelEnabled('ahorro')">
            <div class="inv-icon" style="background-color: rgba(0, 117, 235, 0.15); color: #0075eb;">
              <i class="pi pi-wallet"></i>
            </div>
            <div class="inv-info">
              <span class="inv-name">Liquidez</span>
              <span class="inv-amount">${{ formatMoney(liquidez) }}</span>
            </div>
            <span class="inv-rate income">{{ formatPct(liquidezRate, 1) }}% anual</span>
          </div>
          <div class="inv-item" v-if="prefsStore.panelPrestamos && totalLoans > 0">
            <div class="inv-icon" style="background-color: rgba(16, 185, 129, 0.15); color: #10b981;">
              <i class="pi pi-money-bill"></i>
            </div>
            <div class="inv-info">
              <span class="inv-name">Préstamos</span>
              <span class="inv-amount">${{ formatMoney(totalLoans) }}</span>
            </div>
            <span class="inv-rate income">Activos</span>
          </div>
          <div class="inv-item" v-if="prefsStore.panelAcciones">
            <div class="inv-icon" style="background-color: rgba(139, 92, 246, 0.15); color: #8b5cf6;">
              <i class="pi pi-chart-line"></i>
            </div>
            <div class="inv-info">
              <span class="inv-name">Acciones + ETFs</span>
              <span class="inv-amount">${{ formatMoney(gbmTotal) }}</span>
            </div>
            <span class="inv-rate" :class="gbmReturnPct >= 0 ? 'income' : 'expense'">{{ gbmReturnPct >= 0 ? '+' : '' }}{{ formatPct(gbmReturnPct, 1) }}%</span>
          </div>
          <div class="inv-item" v-if="prefsStore.isPanelEnabled('afore')">
            <div class="inv-icon" style="background-color: rgba(29, 161, 242, 0.15); color: #1da1f2;">
              <i class="pi pi-shield"></i>
            </div>
            <div class="inv-info">
              <span class="inv-name">Afore</span>
              <span class="inv-amount">${{ formatMoney(afore) }}</span>
            </div>
            <span class="inv-rate" :class="aforeRate > 0 ? 'income' : ''">{{ formatPct(aforeRate, 1) }}% anual</span>
          </div>
        </div>
        <div class="inv-total">
          <span>Portafolio Total</span>
          <strong>${{ formatMoney(totalPortfolio) }}</strong>
        </div>

        <div v-if="prefsStore.isPanelEnabled('ahorro')" class="daily-earnings">
          <h4>Ganancias Diarias por Intereses</h4>
          <div class="earnings-row" v-for="acc in savingsAccounts" :key="acc.name">
            <span>{{ acc.name }}</span><span class="income">+${{ formatMoney(acc.dailyGain) }}</span>
          </div>
          <div class="earnings-row total">
            <span>Total diario</span><span class="income">+${{ formatMoney(dailyEarnings) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Fila 3: Gráfica + Deudas -->
    <div class="row-3">
      <div class="card">
        <div class="card-header">
          <h3>Ingresos vs Gastos</h3>
          <router-link to="/finanzas/gastos-ingresos" class="card-link">Ver detalle →</router-link>
        </div>
        <Line :data="lineChartData" :options="chartOptions" />
      </div>
      <div v-if="prefsStore.panelDeudas" class="card debts-summary">
        <div class="card-header">
          <h3>Deudas</h3>
          <router-link to="/finanzas/deudas" class="card-link">Ver detalle →</router-link>
        </div>

        <div v-if="deudas.length === 0" class="debts-empty">
          <i class="pi pi-check-circle"></i>
          <span>Sin deudas registradas</span>
        </div>

        <div v-else>
          <div class="debts-total-row">
            <span class="debts-total-label">Deuda Total</span>
            <span class="debts-total-value expense">${{ formatMoney(totalDeudas) }}</span>
          </div>

          <div class="debts-list">
            <div v-for="deuda in deudas" :key="deuda.id" class="debt-item">
              <div class="debt-item-left">
                <div class="debt-icon"><i class="pi pi-money-bill"></i></div>
                <div class="debt-info">
                  <span class="debt-name">{{ deuda.name }}</span>
                  <span class="debt-meta">{{ deuda.frequencyLabel }} · {{ deuda.paymentsRemaining }} pagos restantes</span>
                </div>
              </div>
              <div class="debt-item-right">
                <span class="debt-amount">${{ formatMoney(deuda.paymentAmount) }}</span>
                <span class="debt-days" :style="{ color: debtDaysColor(deuda.daysUntilPayment) }">
                  en {{ deuda.daysUntilPayment }} días
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Fila 4: Últimos movimientos -->
    <div class="row-4">
      <div class="card full-width">
        <div class="card-header">
          <h3>Últimos Movimientos</h3>
          <router-link to="/finanzas/gastos-ingresos" class="card-link">Ver todos →</router-link>
        </div>
        <div class="movements-list">
          <div v-for="tx in recentTransactions" :key="tx.id" class="movement-item">
            <div class="movement-icon" :class="tx.amount > 0 ? 'mov-income' : 'mov-expense'">
              <i :class="tx.amount > 0 ? 'pi pi-arrow-up' : 'pi pi-arrow-down'"></i>
            </div>
            <div class="movement-info">
              <span class="movement-desc">{{ tx.description }}</span>
              <span class="movement-meta">{{ tx.category }} · {{ tx.date }}</span>
            </div>
            <span class="movement-amount" :class="tx.amount > 0 ? 'income' : 'expense'">
              {{ tx.amount > 0 ? '+' : '' }}${{ formatMoney(Math.abs(tx.amount)) }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Line } from 'vue-chartjs'
import finApi from '../utils/api'
import { cachedGet } from '../utils/cache'
import { formatMoney, formatNumber, formatPct } from '../utils/format.js'
import { usePreferencesStore } from '../stores/preferences'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler)

const prefsStore = usePreferencesStore()

// Reactive data from APIs
const creditCards = ref([])
const totalCreditDebt = ref(0)
const totalCreditAvailable = ref(0)
const upcomingPayments = ref([])

const totalSavings = ref(0)
const totalLoans = ref(0)
const gbmTotal = ref(0)
const gbmReturnPct = ref(0)
const afore = ref(0)
const aforeRate = ref(0)
const dailyEarnings = ref(0)
const savingsAccounts = ref([])

const recentTransactions = ref([])
const monthlyIncome = ref(0)
const monthlyExpenses = ref(0)
const prevMonthIncome = ref(0)
const prevMonthExpenses = ref(0)
const deudas = ref([])
const totalDeudas = ref(0)
const prevMonthPatrimony = ref(null)

const totalPortfolio = computed(() => totalSavings.value + totalLoans.value + gbmTotal.value + afore.value)
const patrimony = computed(() => totalPortfolio.value - totalCreditDebt.value)
const savingsRate = computed(() => monthlyIncome.value > 0 ? Math.round(((monthlyIncome.value - monthlyExpenses.value) / monthlyIncome.value) * 100) : 0)

// Variación patrimonio vs mes anterior (%)
const patrimonyVsPrev = computed(() => {
  if (prevMonthPatrimony.value === null || prevMonthPatrimony.value === 0) return null
  return Math.round(((patrimony.value - prevMonthPatrimony.value) / Math.abs(prevMonthPatrimony.value)) * 100)
})

// Variación vs mes anterior (%)
const incomeVsPrev = computed(() => {
  if (!prevMonthIncome.value) return null
  return Math.round(((monthlyIncome.value - prevMonthIncome.value) / prevMonthIncome.value) * 100)
})
const expensesVsPrev = computed(() => {
  if (!prevMonthExpenses.value) return null
  return Math.round(((monthlyExpenses.value - prevMonthExpenses.value) / prevMonthExpenses.value) * 100)
})

// Cuentas de ahorro (liquidez = suma de todas las cuentas)
const liquidez = computed(() => savingsAccounts.value.reduce((s, a) => s + a.balance, 0))
const liquidezRate = computed(() => {
  if (!savingsAccounts.value.length) return 0
  // Promedio ponderado por balance
  const totalBalance = savingsAccounts.value.reduce((s, a) => s + a.balance, 0)
  if (totalBalance === 0) return 0
  return savingsAccounts.value.reduce((s, a) => s + a.annualRate * (a.balance / totalBalance), 0)
})

// Chart data
const lineChartData = ref({ labels: [], datasets: [] })

onMounted(async () => {
  try {
    const res = await cachedGet('/api/dashboard')
    const { gbm: gbmRes, creditos: creditRes, inversiones: invRes, gi: giRes, deudas: deudasRes } = res.data

    // GBM
    gbmTotal.value = gbmRes.summary.totalValueMXN
    gbmReturnPct.value = gbmRes.summary.totalReturnPct

    // Créditos
    const cards = creditRes.cards
    creditCards.value = cards.map(c => ({
      name: c.name,
      color: c.color,
      debt: c.debt,
      limit: c.creditLimit,
      usage: c.usagePercent
    }))
    totalCreditDebt.value = creditRes.summary.totalDebt
    totalCreditAvailable.value = creditRes.summary.totalAvailable

    upcomingPayments.value = cards
      .filter(c => c.paymentDate)
      .sort((a, b) => a.daysUntilPayment - b.daysUntilPayment)
      .map(c => ({
        name: c.name,
        color: c.color,
        date: formatPaymentDate(c.paymentDate),
        amount: c.fullPayment,
        daysLeft: c.daysUntilPayment
      }))

    // Inversiones
    const inv = invRes
    totalSavings.value = inv.summary.totalSavings
    totalLoans.value = inv.summary.totalLoans
    afore.value = inv.afore.balance || 0
    aforeRate.value = inv.afore.annualReturn || 0
    savingsAccounts.value = inv.ahorro

    // Daily earnings = sum of all savings accounts daily gains
    dailyEarnings.value = inv.ahorro.reduce((s, a) => s + (a.dailyGain || 0), 0)

    // GI Records
    const records = giRes.records || []

    // Recent transactions (last 5)
    recentTransactions.value = records.slice(0, 5).map(r => ({
      id: r.id,
      description: r.description,
      category: r.category,
      date: formatShortDate(r.date),
      amount: r.amount
    }))

    // Mes actual y mes anterior
    const now = new Date()
    const currentMonth = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
    const prevDate = new Date(now.getFullYear(), now.getMonth() - 1, 1)
    const prevMonth = `${prevDate.getFullYear()}-${String(prevDate.getMonth() + 1).padStart(2, '0')}`

    const thisMonthRecords = records.filter(r => r.date && r.date.startsWith(currentMonth))
    const prevMonthRecords = records.filter(r => r.date && r.date.startsWith(prevMonth))

    monthlyIncome.value = thisMonthRecords.filter(r => r.amount > 0).reduce((s, r) => s + r.amount, 0)
    monthlyExpenses.value = thisMonthRecords.filter(r => r.amount < 0).reduce((s, r) => s + Math.abs(r.amount), 0)
    prevMonthIncome.value = prevMonthRecords.filter(r => r.amount > 0).reduce((s, r) => s + r.amount, 0)
    prevMonthExpenses.value = prevMonthRecords.filter(r => r.amount < 0).reduce((s, r) => s + Math.abs(r.amount), 0)

    // Build line chart: last 6 months income vs expenses
    buildLineChart(records)

    // Deudas
    deudas.value = deudasRes.deudas.sort((a, b) => a.daysUntilPayment - b.daysUntilPayment)
    totalDeudas.value = deudasRes.totalDebt

    // Patrimonio: load previous month for comparison
    try {
      const patrimonioRes = await finApi.get('/api/patrimonio')
      const history = patrimonioRes.data.history || []
      const now2 = new Date()
      const prevDate2 = new Date(now2.getFullYear(), now2.getMonth() - 1, 1)
      const prevMonthKey = `${prevDate2.getFullYear()}-${String(prevDate2.getMonth() + 1).padStart(2, '0')}`
      const prevEntry = history.find(h => h.month === prevMonthKey)
      if (prevEntry) {
        prevMonthPatrimony.value = prevEntry.value
      }
    } catch (e) {
      console.error('Error loading patrimonio history:', e)
    }

  } catch (error) {
    console.error('Error loading dashboard data:', error)
  }
})

function buildLineChart(records) {
  const months = []
  const now = new Date()
  for (let i = 5; i >= 0; i--) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1)
    months.push({
      key: `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`,
      label: d.toLocaleDateString('es-AR', { month: 'short' })
    })
  }

  const incomeData = months.map(m => {
    return records.filter(r => r.date && r.date.startsWith(m.key) && r.amount > 0).reduce((s, r) => s + r.amount, 0)
  })

  const expenseData = months.map(m => {
    return records.filter(r => r.date && r.date.startsWith(m.key) && r.amount < 0).reduce((s, r) => s + Math.abs(r.amount), 0)
  })

  lineChartData.value = {
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
}

function paymentColor(days) {
  if (days <= 5) return '#ef4444'
  if (days < 15) return '#f59e0b'
  return '#10b981'
}

function debtDaysColor(days) {
  if (days <= 5) return '#ef4444'
  if (days <= 10) return '#f59e0b'
  return '#8899a6'
}

function formatPaymentDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr + 'T00:00:00')
  return date.toLocaleDateString('es-AR', { day: '2-digit', month: 'short', year: 'numeric' })
}

function formatShortDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr + 'T00:00:00')
  return date.toLocaleDateString('es-AR', { day: '2-digit', month: 'short' })
}

const chartOptions = {
  responsive: true,
  plugins: {
    legend: { labels: { color: '#8899a6' } }
  },
  scales: {
    x: { ticks: { color: '#8899a6' }, grid: { color: 'rgba(120,135,150,0.18)' } },
    y: { ticks: { color: '#8899a6' }, grid: { color: 'rgba(120,135,150,0.18)' } }
  }
}
</script>

<style scoped>
.dashboard {
  max-width: 1200px;
}

.page-title {
  font-size: 1.8rem;
  font-weight: 700;
  margin-bottom: 24px;
  color: var(--fin-text);
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
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
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
}

.stat-icon.patrimony { background-color: rgba(29, 161, 242, 0.15); color: #1da1f2; }
.stat-icon.income-icon { background-color: rgba(16, 185, 129, 0.15); color: #10b981; }
.stat-icon.expense-icon { background-color: rgba(239, 68, 68, 0.15); color: #ef4444; }
.stat-icon.savings-icon { background-color: rgba(139, 92, 246, 0.15); color: #8b5cf6; }

.stat-info { display: flex; flex-direction: column; }
.stat-label { font-size: 0.8rem; color: var(--fin-text-muted); margin-bottom: 4px; }
.stat-value { font-size: 1.3rem; font-weight: 700; color: var(--fin-text); }
.stat-sub { font-size: 0.7rem; color: var(--fin-text-muted); margin-top: 2px; }
.stat-sub.income { color: #10b981; }
.stat-sub.expense { color: #ef4444; }

/* Cards */
.card {
  background-color: var(--fin-surface);
  border: 1px solid var(--fin-border);
  border-radius: 12px;
  padding: 20px;
}

.card h3 {
  color: var(--fin-text);
  font-size: 1rem;
  margin-bottom: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.card-header h3 { margin-bottom: 0; }

.card-link {
  color: #1da1f2;
  font-size: 0.8rem;
  text-decoration: none;
  font-weight: 600;
}

.card-link:hover { text-decoration: underline; }

/* Row 2 */
.row-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 24px;
}

/* Credit Summary */
.credit-bars { margin-bottom: 16px; }

.credit-bar-item { margin-bottom: 12px; }

.credit-bar-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
}

.credit-bar-name { font-size: 0.85rem; font-weight: 600; }
.credit-bar-amount { font-size: 0.75rem; color: var(--fin-text-muted); }

.credit-bar-bg {
  height: 6px;
  background-color: var(--fin-border);
  border-radius: 3px;
  overflow: hidden;
}

.credit-bar-fill {
  height: 100%;
  border-radius: 3px;
}

.credit-totals {
  display: flex;
  gap: 20px;
  padding-top: 12px;
  border-top: 1px solid var(--fin-border);
}

.credit-total-item { display: flex; flex-direction: column; gap: 2px; }
.ct-label { font-size: 0.7rem; color: var(--fin-text-muted); }
.ct-value { font-size: 0.9rem; font-weight: 700; color: var(--fin-text); }
.ct-value.expense { color: #ef4444; }
.ct-value.income { color: #10b981; }
.ct-value.highlight { color: #f59e0b; }

/* Investments Summary */
.inv-breakdown { display: flex; flex-direction: column; gap: 10px; margin-bottom: 12px; }

.inv-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px;
  border-radius: 8px;
  background-color: var(--fin-surface-2);
}

.inv-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.9rem;
}

.inv-info { flex: 1; display: flex; flex-direction: column; }
.inv-name { font-size: 0.8rem; color: var(--fin-text-muted); }
.inv-amount { font-size: 0.9rem; font-weight: 600; color: var(--fin-text); }
.inv-rate { font-size: 0.75rem; font-weight: 600; }

.inv-total {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  background-color: var(--fin-surface-2);
  border-radius: 8px;
  color: var(--fin-text-muted);
  font-size: 0.85rem;
}

.inv-total strong { color: var(--fin-text); font-size: 1.1rem; }

/* Row 3 */
.row-3 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 24px;
}

/* Row 4 */
.row-4 {
  margin-top: 0;
}

.full-width {
  width: 100%;
}

/* Movements */
.movements-list { display: flex; flex-direction: column; gap: 8px; }

.movement-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px;
  border-radius: 8px;
  background-color: var(--fin-surface-2);
}

.movement-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
}

.mov-income { background-color: rgba(16, 185, 129, 0.15); color: #10b981; }
.mov-expense { background-color: rgba(239, 68, 68, 0.15); color: #ef4444; }

.movement-info { flex: 1; display: flex; flex-direction: column; }
.movement-desc { font-size: 0.85rem; color: var(--fin-text); }
.movement-meta { font-size: 0.7rem; color: var(--fin-text-muted); }
.movement-amount { font-size: 0.9rem; font-weight: 700; }

/* Payments section inside credit card */
.payments-section {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid var(--fin-border);
}

.payments-section h4 {
  color: var(--fin-text-muted);
  font-size: 0.8rem;
  text-transform: uppercase;
  margin-bottom: 10px;
}

/* Payments */
.payments-list { display: flex; flex-direction: column; gap: 8px; }

.payment-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px;
  border-radius: 8px;
  background-color: var(--fin-surface-2);
}

.payment-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.85rem;
}

.payment-info { flex: 1; display: flex; flex-direction: column; }
.payment-name { font-size: 0.85rem; color: var(--fin-text); font-weight: 600; }
.payment-date { font-size: 0.7rem; color: var(--fin-text-muted); }

.payment-right { display: flex; flex-direction: column; align-items: flex-end; }
.payment-amount { font-size: 0.9rem; font-weight: 700; }
.payment-days { font-size: 0.7rem; }

/* Daily Earnings */
.daily-earnings {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--fin-border);
}

.daily-earnings h4 {
  color: var(--fin-text-muted);
  font-size: 0.8rem;
  text-transform: uppercase;
  margin-bottom: 8px;
}

.earnings-row {
  display: flex;
  justify-content: space-between;
  padding: 4px 0;
  font-size: 0.82rem;
  color: var(--fin-text-muted);
}

.earnings-row.total {
  border-top: 1px solid var(--fin-border);
  margin-top: 4px;
  padding-top: 8px;
  color: var(--fin-text);
  font-weight: 600;
}

.income { color: #10b981; font-weight: 600; }
.expense { color: #ef4444; font-weight: 600; }
.highlight { color: #f59e0b; }

/* Debts Summary */
.debts-total-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  background-color: var(--fin-surface-2);
  border-radius: 8px;
  margin-bottom: 12px;
}

.debts-total-label { font-size: 0.82rem; color: var(--fin-text-muted); }
.debts-total-value { font-size: 1.1rem; font-weight: 700; }

.debts-list { display: flex; flex-direction: column; gap: 8px; }

.debt-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  background-color: var(--fin-surface-2);
  border-radius: 8px;
  gap: 10px;
}

.debt-item-left { display: flex; align-items: center; gap: 10px; flex: 1; min-width: 0; }

.debt-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background-color: rgba(239, 68, 68, 0.15);
  color: #ef4444;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.85rem;
  flex-shrink: 0;
}

.debt-info { display: flex; flex-direction: column; min-width: 0; }
.debt-name { font-size: 0.85rem; color: var(--fin-text); font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.debt-meta { font-size: 0.7rem; color: var(--fin-text-muted); }

.debt-item-right { display: flex; flex-direction: column; align-items: flex-end; flex-shrink: 0; }
.debt-amount { font-size: 0.9rem; font-weight: 700; color: var(--fin-text); }
.debt-days { font-size: 0.7rem; }

.debts-empty {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #10b981;
  font-size: 0.85rem;
  padding: 12px 0;
}

@media (max-width: 768px) {
  .row-2, .row-3, .row-4 {
    grid-template-columns: 1fr;
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
  }

  .card {
    padding: 16px;
  }
}

@media (max-width: 480px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }

  .page-title {
    font-size: 1.2rem;
  }
}
</style>
