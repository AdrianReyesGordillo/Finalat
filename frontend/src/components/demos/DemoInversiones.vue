<script setup>
import { ref, computed } from 'vue'

const periods = [
  { key: '1m', label: '1M', months: 1 },
  { key: '3m', label: '3M', months: 3 },
  { key: '6m', label: '6M', months: 6 },
  { key: '1y', label: '1A', months: 12 },
  { key: '5y', label: '5A', months: 60 },
]

const savingsAccounts = ref([
  { name: 'Nu México', balance: 45000, annualRate: 13, color: '#820ad1', dailyGain: 16.03, selectedPeriod: '1y', description: 'Cajita Turbo' },
  { name: 'Mercado Pago', balance: 12500, annualRate: 12, color: '#00bcff', dailyGain: 4.11, selectedPeriod: '1y', description: 'Rendimiento diario' },
  { name: 'CETES 28 días', balance: 80000, annualRate: 6.18, color: '#10b981', dailyGain: 13.55, selectedPeriod: '1y', description: 'Gobierno Federal' },
])

const afore = ref({ balance: 125800, annualReturn: 8.5, provider: 'Profuturo', bimonthlyContribution: 2400, voluntaryContribution: 500 })

const showSingleAhorroModal = ref(false)
const singleAhorroAccount = ref(null)
const singleAhorroBalance = ref(null)
const singleAhorroSaving = ref(false)

const showAforeModal = ref(false)
const aforeFormData = ref({})
const aforeUpdating = ref(false)

const totalSavings = computed(() => savingsAccounts.value.reduce((s, a) => s + a.balance, 0))
const dailyTotal = computed(() => savingsAccounts.value.reduce((s, a) => s + a.dailyGain, 0))
const totalPortfolio = computed(() => totalSavings.value + afore.value.balance)

function formatMoney(n) { return (n || 0).toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }

function getProjection(account) {
  const p = periods.find(pp => pp.key === account.selectedPeriod)
  const months = p ? p.months : 12
  return account.balance * (1 + account.annualRate / 100 * months / 12)
}

function openSingleAhorroModal(account) {
  singleAhorroAccount.value = account
  singleAhorroBalance.value = null
  showSingleAhorroModal.value = true
}

function submitSingleAhorroBalance() {
  singleAhorroSaving.value = true
  setTimeout(() => {
    if (singleAhorroBalance.value && singleAhorroAccount.value) {
      singleAhorroAccount.value.balance = Number(singleAhorroBalance.value)
      singleAhorroAccount.value.dailyGain = Math.round(singleAhorroAccount.value.balance * (singleAhorroAccount.value.annualRate / 100) / 365 * 100) / 100
    }
    showSingleAhorroModal.value = false
    singleAhorroSaving.value = false
  }, 600)
}

function saveAfore() {
  aforeUpdating.value = true
  setTimeout(() => {
    if (aforeFormData.value.balance != null) afore.value.balance = Number(aforeFormData.value.balance)
    if (aforeFormData.value.annualReturn != null) afore.value.annualReturn = Number(aforeFormData.value.annualReturn)
    if (aforeFormData.value.bimonthlyContribution != null) afore.value.bimonthlyContribution = Number(aforeFormData.value.bimonthlyContribution)
    if (aforeFormData.value.voluntaryContribution != null) afore.value.voluntaryContribution = Number(aforeFormData.value.voluntaryContribution)
    showAforeModal.value = false
    aforeFormData.value = {}
    aforeUpdating.value = false
  }, 600)
}

const aforeProjection30 = computed(() => {
  const years = 30
  const monthly = afore.value.bimonthlyContribution / 2 + afore.value.voluntaryContribution * 4.33
  const rate = afore.value.annualReturn / 100 / 12
  let total = afore.value.balance
  for (let i = 0; i < years * 12; i++) { total = (total + monthly) * (1 + rate) }
  return Math.round(total)
})

function formatNumber(n) { return (n || 0).toLocaleString('es-MX') }
</script>

<template>
  <div class="demo-inv">
    <div class="demo-label"><span class="demo-badge">Demo interactiva</span> Edita saldos y observa cómo cambian las proyecciones.</div>

    <h2 class="page-title">Inversiones</h2>

    <!-- Stats -->
    <div class="stats-grid">
      <div class="stat-card"><div class="stat-icon portfolio"><i class="pi pi-briefcase"></i></div><div class="stat-info"><span class="stat-label">Portafolio Total</span><span class="stat-value">${{ formatMoney(totalPortfolio) }}</span></div></div>
      <div class="stat-card"><div class="stat-icon savings"><i class="pi pi-wallet"></i></div><div class="stat-info"><span class="stat-label">Liquidez</span><span class="stat-value">${{ formatMoney(totalSavings) }}</span></div></div>
      <div class="stat-card"><div class="stat-icon savings"><i class="pi pi-wallet"></i></div><div class="stat-info"><span class="stat-label">Ingreso Diario</span><span class="stat-value income">+${{ formatMoney(dailyTotal) }}</span></div></div>
    </div>

    <!-- Tabs -->
    <div class="section-tabs">
      <button class="tab-btn active"><i class="pi pi-wallet"></i> Ahorro</button>
      <button class="tab-btn" @click="showAforeModal = true"><i class="pi pi-shield"></i> Afore</button>
    </div>

    <!-- Savings Cards -->
    <div class="savings-cards">
      <div v-for="account in savingsAccounts" :key="account.name" class="savings-card" :style="{ borderTopColor: account.color }">
        <div class="savings-header">
          <div class="savings-brand" :style="{ backgroundColor: account.color + '20', color: account.color }"><i class="pi pi-wallet"></i></div>
          <div><h3>{{ account.name }}</h3><span class="savings-subtitle">{{ account.description }}</span></div>
          <button class="btn-edit-card" :style="{ color: account.color }" @click="openSingleAhorroModal(account)"><i class="pi pi-pencil"></i></button>
        </div>
        <div class="savings-balance"><span class="balance-label">Saldo Actual</span><span class="balance-value">${{ formatMoney(account.balance) }}</span></div>
        <div class="savings-rate">
          <span class="rate-badge" :style="{ backgroundColor: account.color + '20', color: account.color }">{{ account.annualRate }}% anual</span>
          <span class="daily-gain">+${{ formatMoney(account.dailyGain) }}/día</span>
        </div>
        <div class="period-selector">
          <button v-for="p in periods" :key="p.key" class="period-btn" :class="{ active: account.selectedPeriod === p.key }" @click="account.selectedPeriod = p.key">{{ p.label }}</button>
        </div>
        <div class="projection-summary">
          <div class="proj-item"><span class="proj-label">Proyección</span><span class="proj-value income">${{ formatMoney(getProjection(account)) }}</span></div>
          <div class="proj-item"><span class="proj-label">Ganancia</span><span class="proj-value income">+${{ formatMoney(getProjection(account) - account.balance) }}</span></div>
        </div>
      </div>
    </div>

    <!-- Afore section -->
    <div class="afore-section">
      <div class="afore-header"><div class="afore-brand"><i class="pi pi-shield"></i></div><div><h3>Afore</h3><span class="savings-subtitle">{{ afore.provider }}</span></div><button class="btn-edit-card" style="color:#1da1f2" @click="showAforeModal = true"><i class="pi pi-pencil"></i></button></div>
      <div class="afore-stats">
        <div class="afore-stat"><span class="afore-stat-label">Saldo Acumulado</span><span class="afore-stat-value">${{ formatMoney(afore.balance) }}</span></div>
        <div class="afore-stat"><span class="afore-stat-label">Rendimiento Anual</span><span class="afore-stat-value income">{{ afore.annualReturn }}%</span></div>
        <div class="afore-stat"><span class="afore-stat-label">Aportación Bimestral</span><span class="afore-stat-value">${{ formatMoney(afore.bimonthlyContribution) }}</span></div>
        <div class="afore-stat"><span class="afore-stat-label">Aportación Voluntaria</span><span class="afore-stat-value">${{ formatMoney(afore.voluntaryContribution) }}/semana</span></div>
      </div>
      <div class="afore-projection"><p>Proyección a 30 años: <strong class="income">${{ formatNumber(aforeProjection30) }}</strong></p></div>
    </div>

    <!-- Modal Ahorro -->
    <div v-if="showSingleAhorroModal" class="modal-overlay" @click.self="showSingleAhorroModal = false">
      <div class="upload-modal">
        <div class="upload-modal-header"><h3><i class="pi pi-wallet"></i> Editar {{ singleAhorroAccount?.name }}</h3><button class="btn-close" @click="showSingleAhorroModal = false"><i class="pi pi-times"></i></button></div>
        <div class="upload-modal-body">
          <p class="upload-hint">Ingresa el saldo actual de esta cuenta.</p>
          <div class="modal-field"><label><span class="balance-field-dot" :style="{ backgroundColor: singleAhorroAccount?.color }"></span> Saldo Actual</label><div class="balance-input-wrap"><span class="balance-input-prefix">$</span><input type="number" class="balance-input" :placeholder="formatMoney(singleAhorroAccount?.balance || 0)" v-model="singleAhorroBalance" /></div></div>
        </div>
        <div class="upload-modal-footer"><button class="btn-cancel" @click="showSingleAhorroModal = false">Cancelar</button><button class="btn-upload-confirm" :disabled="singleAhorroSaving || !singleAhorroBalance" @click="submitSingleAhorroBalance"><i :class="singleAhorroSaving ? 'pi pi-spin pi-spinner' : 'pi pi-check'"></i> {{ singleAhorroSaving ? 'Guardando...' : 'Guardar saldo' }}</button></div>
      </div>
    </div>

    <!-- Modal Afore -->
    <div v-if="showAforeModal" class="modal-overlay" @click.self="showAforeModal = false">
      <div class="upload-modal">
        <div class="upload-modal-header"><h3><i class="pi pi-shield"></i> Actualizar Datos Afore</h3><button class="btn-close" @click="showAforeModal = false"><i class="pi pi-times"></i></button></div>
        <div class="upload-modal-body">
          <div class="modal-field"><label>Saldo Acumulado</label><div class="balance-input-wrap"><span class="balance-input-prefix">$</span><input type="number" class="balance-input" :placeholder="formatMoney(afore.balance)" v-model.number="aforeFormData.balance" /></div></div>
          <div class="modal-field"><label>Rendimiento Anual (%)</label><div class="balance-input-wrap"><input type="number" step="0.1" class="balance-input" :placeholder="afore.annualReturn" v-model.number="aforeFormData.annualReturn" /></div></div>
          <div class="modal-field"><label>Aportación Bimestral</label><div class="balance-input-wrap"><span class="balance-input-prefix">$</span><input type="number" class="balance-input" :placeholder="formatMoney(afore.bimonthlyContribution)" v-model.number="aforeFormData.bimonthlyContribution" /></div></div>
          <div class="modal-field"><label>Aportación Voluntaria (semanal)</label><div class="balance-input-wrap"><span class="balance-input-prefix">$</span><input type="number" class="balance-input" :placeholder="formatMoney(afore.voluntaryContribution)" v-model.number="aforeFormData.voluntaryContribution" /></div></div>
        </div>
        <div class="upload-modal-footer"><button class="btn-cancel" @click="showAforeModal = false">Cancelar</button><button class="btn-upload-confirm" :disabled="aforeUpdating" @click="saveAfore"><i :class="aforeUpdating ? 'pi pi-spin pi-spinner' : 'pi pi-check'"></i> {{ aforeUpdating ? 'Guardando...' : 'Guardar datos' }}</button></div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.demo-inv {
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
.income { color: #10b981 !important; }

/* Stats */
.stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 20px; }
.stat-card { background-color: var(--fin-surface); border: 1px solid var(--fin-border); border-radius: 12px; padding: 16px; display: flex; align-items: center; gap: 12px; }
.stat-icon { width: 42px; height: 42px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 1.1rem; }
.stat-icon.portfolio { background-color: rgba(29,161,242,0.15); color: #1da1f2; }
.stat-icon.savings { background-color: rgba(16,185,129,0.15); color: #10b981; }
.stat-info { display: flex; flex-direction: column; }
.stat-label { font-size: 0.75rem; color: var(--fin-text-muted); margin-bottom: 2px; }
.stat-value { font-size: 1.1rem; font-weight: 700; color: var(--fin-text); }

/* Tabs */
.section-tabs { display: flex; gap: 8px; margin-bottom: 20px; }
.tab-btn { background: var(--fin-surface); border: 1px solid var(--fin-border); border-radius: 8px; padding: 10px 18px; color: var(--fin-text-muted); font-size: 0.85rem; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 6px; }
.tab-btn.active { border-color: #1da1f2; color: #1da1f2; background: rgba(29,161,242,0.08); }

/* Savings Cards */
.savings-cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; margin-bottom: 24px; }
.savings-card { background-color: var(--fin-surface); border: 1px solid var(--fin-border); border-top: 3px solid; border-radius: 12px; padding: 20px; }
.savings-header { display: flex; align-items: center; gap: 12px; margin-bottom: 14px; }
.savings-brand { width: 36px; height: 36px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 1rem; }
.savings-header h3 { color: var(--fin-text); font-size: 1rem; margin: 0; }
.savings-subtitle { color: var(--fin-text-muted); font-size: 0.75rem; }
.btn-edit-card { background: none; border: none; cursor: pointer; margin-left: auto; font-size: 1rem; }
.savings-balance { margin-bottom: 10px; }
.balance-label { display: block; font-size: 0.7rem; color: var(--fin-text-muted); margin-bottom: 2px; }
.balance-value { font-size: 1.4rem; font-weight: 700; color: var(--fin-text); }
.savings-rate { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
.rate-badge { font-size: 0.75rem; font-weight: 600; padding: 4px 10px; border-radius: 20px; }
.daily-gain { font-size: 0.8rem; color: #10b981; font-weight: 600; }
.period-selector { display: flex; gap: 4px; margin-bottom: 14px; }
.period-btn { background: var(--fin-surface-2); border: 1px solid var(--fin-border); border-radius: 6px; padding: 6px 10px; font-size: 0.75rem; color: var(--fin-text-muted); cursor: pointer; font-weight: 600; }
.period-btn.active { background: #1da1f2; color: white; border-color: #1da1f2; }
.projection-summary { display: flex; gap: 16px; }
.proj-item { display: flex; flex-direction: column; }
.proj-label { font-size: 0.7rem; color: var(--fin-text-muted); }
.proj-value { font-size: 1rem; font-weight: 700; }

/* Afore */
.afore-section { background-color: var(--fin-surface); border: 1px solid var(--fin-border); border-radius: 12px; padding: 20px; margin-top: 20px; }
.afore-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.afore-brand { width: 40px; height: 40px; border-radius: 10px; background: rgba(29,161,242,0.15); color: #1da1f2; display: flex; align-items: center; justify-content: center; font-size: 1.2rem; }
.afore-header h3 { color: var(--fin-text); font-size: 1.1rem; margin: 0; }
.afore-stats { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-bottom: 16px; }
.afore-stat { background: var(--fin-surface-2); border-radius: 8px; padding: 12px; }
.afore-stat-label { display: block; font-size: 0.7rem; color: var(--fin-text-muted); margin-bottom: 4px; }
.afore-stat-value { font-size: 1rem; font-weight: 700; color: var(--fin-text); }
.afore-projection { background: rgba(16,185,129,0.08); border: 1px solid rgba(16,185,129,0.2); border-radius: 8px; padding: 12px 16px; }
.afore-projection p { margin: 0; color: var(--fin-text-muted); font-size: 0.85rem; }
.afore-projection strong { font-size: 1.1rem; }

/* Modal */
.modal-overlay { position: fixed; inset: 0; background-color: rgba(0,0,0,0.6); display: flex; align-items: center; justify-content: center; z-index: 1000; backdrop-filter: blur(2px); }
.upload-modal { background-color: var(--fin-surface); border: 1px solid var(--fin-border); border-radius: 14px; width: 90%; max-width: 480px; max-height: 85vh; overflow-y: auto; }
.upload-modal-header { display: flex; justify-content: space-between; align-items: center; padding: 18px 20px; border-bottom: 1px solid var(--fin-border); }
.upload-modal-header h3 { color: var(--fin-text); margin: 0; display: flex; align-items: center; gap: 8px; font-size: 1rem; }
.btn-close { background: transparent; border: none; color: var(--fin-text-muted); font-size: 1.1rem; cursor: pointer; }
.upload-modal-body { padding: 20px; display: flex; flex-direction: column; gap: 14px; }
.upload-hint { color: var(--fin-text-muted); font-size: 0.85rem; margin: 0; }
.modal-field { display: flex; flex-direction: column; gap: 6px; }
.modal-field label { font-size: 0.75rem; text-transform: uppercase; color: var(--fin-text-muted); font-weight: 600; display: flex; align-items: center; gap: 6px; }
.balance-field-dot { width: 10px; height: 10px; border-radius: 50%; }
.balance-input-wrap { display: flex; align-items: center; background-color: var(--fin-surface-2); border: 1px solid var(--fin-border); border-radius: 8px; overflow: hidden; }
.balance-input-wrap:focus-within { border-color: #1da1f2; }
.balance-input-prefix { padding: 0 10px; color: var(--fin-text-muted); font-size: 0.9rem; border-right: 1px solid var(--fin-border); line-height: 38px; }
.balance-input { flex: 1; background: transparent; border: none; outline: none; color: var(--fin-text); font-size: 0.9rem; padding: 9px 12px; }
.upload-modal-footer { display: flex; justify-content: flex-end; gap: 10px; padding: 16px 20px; border-top: 1px solid var(--fin-border); }
.btn-cancel { background-color: var(--fin-surface-2); color: var(--fin-text-muted); border: 1px solid var(--fin-border); padding: 10px 18px; border-radius: 8px; font-size: 0.85rem; cursor: pointer; }
.btn-upload-confirm { background-color: #1da1f2; color: white; border: none; padding: 10px 18px; border-radius: 8px; font-size: 0.85rem; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 6px; }
.btn-upload-confirm:disabled { opacity: 0.6; cursor: not-allowed; }

@media (max-width: 640px) {
  .stats-grid { grid-template-columns: 1fr; }
  .savings-cards { grid-template-columns: 1fr; }
  .afore-stats { grid-template-columns: 1fr; }
}
</style>
