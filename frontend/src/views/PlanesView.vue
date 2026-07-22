<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useSubscriptionStore, type Tier } from '@/stores/subscription'
import finApi from '@/finanzas/utils/api'

const router = useRouter()
const route = useRoute()
const subStore = useSubscriptionStore()
const selectedPlan = ref<string | null>(null)
const subscribing = ref(false)
const errorMsg = ref('')
const successMsg = ref('')

onMounted(async () => {
  if (!subStore.loaded) {
    await subStore.load()
  }
  selectedPlan.value = subStore.tier

  // Handle return from Stripe Checkout
  if (route.query.success === 'true') {
    successMsg.value = '¡Suscripción activada exitosamente!'
    // Reload subscription to get updated tier
    await subStore.load()
    selectedPlan.value = subStore.tier
  }
  if (route.query.cancelled === 'true') {
    errorMsg.value = 'El proceso de pago fue cancelado.'
  }
})

interface Plan {
  id: Tier
  name: string
  price: number
  period: string
  description: string
  features: string[]
  highlight?: boolean
  badge?: string
  members?: number
}

const plans: Plan[] = [
  {
    id: 'free',
    name: 'Free',
    price: 0,
    period: '',
    description: 'Lo esencial para comenzar a organizar tus finanzas.',
    features: [
      'Dashboard financiero básico',
      'Registro de gastos e ingresos',
      'Cursos de aprendizaje gratuitos',
      'Agente financiero limitado',
    ],
  },
  {
    id: 'student',
    name: 'Estudiantil',
    price: 4,
    period: '/mes',
    description: 'Herramientas avanzadas para crecer financieramente.',
    badge: 'Popular',
    highlight: true,
    features: [
      'Todo lo del plan Free',
      'Agente financiero ilimitado',
      'Acceso completo a inversiones',
      'Análisis avanzado de gastos',
      'Proyecciones y simulaciones',
      'Soporte prioritario',
    ],
  },
  {
    id: 'family',
    name: 'Familiar',
    price: 12,
    period: '/mes',
    description: 'Finanzas en equipo: gestiona hasta 4 personas.',
    members: 4,
    features: [
      'Todo lo del plan Estudiantil',
      'Hasta 4 miembros en la cuenta',
      'Dashboard familiar compartido',
      'Metas de ahorro en grupo',
      'Reportes consolidados',
      'Administración de permisos',
    ],
  },
]

function isCurrentPlan(planId: string): boolean {
  return subStore.tier === planId
}

function getButtonText(planId: string): string {
  if (isCurrentPlan(planId)) return 'Plan actual'
  if (planId === 'free') return 'Cambiar a Free'
  return 'Suscribirme'
}

async function selectPlan(planId: Tier) {
  if (isCurrentPlan(planId)) return

  // Free tier: just downgrade directly
  if (planId === 'free') {
    subscribing.value = true
    errorMsg.value = ''
    try {
      await subStore.updateTier('free')
      selectedPlan.value = 'free'
    } catch (err: any) {
      errorMsg.value = err.message || 'Error al cambiar de plan.'
    } finally {
      subscribing.value = false
    }
    return
  }

  // Paid tiers: redirect to Stripe Checkout
  subscribing.value = true
  errorMsg.value = ''
  try {
    const { data } = await finApi.post('/api/stripe/create-checkout', { tier: planId })
    if (data.url) {
      window.location.href = data.url
    }
  } catch (err: any) {
    errorMsg.value = err.response?.data?.detail || 'Error al iniciar el proceso de pago.'
    subscribing.value = false
  }
}

function goBack() {
  router.push('/')
}

async function openBillingPortal() {
  try {
    const { data } = await finApi.post('/api/stripe/create-portal')
    if (data.url) {
      window.location.href = data.url
    }
  } catch (err: any) {
    errorMsg.value = err.response?.data?.detail || 'Error al abrir el portal de facturación.'
  }
}
</script>

<template>
  <div class="planes-page">
    <!-- Header -->
    <div class="planes-header">
      <button class="btn-back" @click="goBack">
        <i class="pi pi-arrow-left"></i>
        <span>Volver</span>
      </button>
      <h1 class="planes-title">Elige tu plan</h1>
      <p class="planes-subtitle">
        Selecciona el plan que mejor se adapte a tus necesidades. Puedes cambiar o cancelar en cualquier momento.
      </p>
    </div>

    <!-- Plans grid -->
    <div class="plans-grid">
      <div
        v-for="plan in plans"
        :key="plan.id"
        class="plan-card"
        :class="{ highlighted: plan.highlight, selected: isCurrentPlan(plan.id) }"
      >
        <!-- Badge -->
        <div v-if="plan.badge" class="plan-badge">{{ plan.badge }}</div>

        <!-- Current plan indicator -->
        <div v-if="isCurrentPlan(plan.id)" class="plan-current-badge">Tu plan</div>

        <!-- Plan header -->
        <div class="plan-header">
          <h2 class="plan-name">{{ plan.name }}</h2>
          <p class="plan-description">{{ plan.description }}</p>
        </div>

        <!-- Price -->
        <div class="plan-price">
          <span v-if="plan.price === 0" class="price-amount">Gratis</span>
          <template v-else>
            <span class="price-currency">$</span>
            <span class="price-amount">{{ plan.price }}</span>
            <span class="price-usd">USD</span>
            <span class="price-period">{{ plan.period }}</span>
          </template>
        </div>

        <!-- Members badge -->
        <div v-if="plan.members" class="plan-members">
          <i class="pi pi-users"></i>
          <span>Hasta {{ plan.members }} personas</span>
        </div>

        <!-- Features -->
        <ul class="plan-features">
          <li v-for="feature in plan.features" :key="feature">
            <i class="pi pi-check"></i>
            <span>{{ feature }}</span>
          </li>
        </ul>

        <!-- CTA -->
        <button
          class="plan-btn"
          :class="{
            'btn-highlight': plan.highlight && !isCurrentPlan(plan.id),
            'btn-default': !plan.highlight || isCurrentPlan(plan.id),
            'btn-current': isCurrentPlan(plan.id),
          }"
          :disabled="isCurrentPlan(plan.id) || subscribing"
          @click="selectPlan(plan.id)"
        >
          <i v-if="subscribing && selectedPlan === plan.id" class="pi pi-spin pi-spinner"></i>
          {{ getButtonText(plan.id) }}
        </button>
      </div>
    </div>

    <!-- Success message -->
    <div v-if="successMsg" class="planes-success">
      <i class="pi pi-check-circle"></i>
      <span>{{ successMsg }}</span>
    </div>

    <!-- Error message -->
    <div v-if="errorMsg" class="planes-error">
      <i class="pi pi-exclamation-triangle"></i>
      <span>{{ errorMsg }}</span>
    </div>

    <!-- Manage billing (for existing paid subscribers) -->
    <div v-if="subStore.isPremium" class="planes-billing">
      <button class="btn-billing" @click="openBillingPortal">
        <i class="pi pi-credit-card"></i>
        Administrar método de pago
      </button>
    </div>

    <!-- FAQ / note -->
    <div class="planes-note">
      <i class="pi pi-info-circle"></i>
      <p>Todos los pagos se procesan de forma segura. Puedes cancelar tu suscripción en cualquier momento desde la configuración de tu cuenta.</p>
    </div>
  </div>
</template>

<style scoped>
.planes-page {
  max-width: 1000px;
  margin: 0 auto;
  padding: 2rem 1rem;
}

.planes-header {
  text-align: center;
  margin-bottom: 2.5rem;
}

.btn-back {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
  font-weight: 500;
  color: #6b7280;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.375rem 0.75rem;
  border-radius: 0.5rem;
  margin-bottom: 1.5rem;
  transition: color 0.15s;
}
.btn-back:hover { color: #374151; }

.planes-title {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--color-primary-700, #2D2B6B);
  margin-bottom: 0.5rem;
}

.planes-subtitle {
  color: #6b7280;
  font-size: 0.95rem;
  line-height: 1.5;
  max-width: 500px;
  margin: 0 auto;
}

/* Plans grid */
.plans-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.plan-card {
  position: relative;
  background: #fff;
  border: 2px solid #e5e7eb;
  border-radius: 1.25rem;
  padding: 1.75rem 1.5rem;
  display: flex;
  flex-direction: column;
  transition: all 0.2s ease;
}

.plan-card.highlighted {
  border-color: #2AAFAA;
  box-shadow: 0 4px 20px rgba(42, 175, 170, 0.12);
}

.plan-card.selected {
  border-color: var(--color-primary-700, #2D2B6B);
  box-shadow: 0 4px 20px rgba(45, 43, 107, 0.15);
}

.plan-badge {
  position: absolute;
  top: -0.75rem;
  left: 50%;
  transform: translateX(-50%);
  background: #2AAFAA;
  color: #fff;
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
}

.plan-current-badge {
  position: absolute;
  top: -0.75rem;
  right: 1rem;
  background: var(--color-primary-700, #2D2B6B);
  color: #fff;
  font-size: 0.65rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 0.2rem 0.6rem;
  border-radius: 9999px;
}

.plan-header {
  margin-bottom: 1.25rem;
}

.plan-name {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-primary-700, #2D2B6B);
  margin-bottom: 0.375rem;
}

.plan-description {
  font-size: 0.825rem;
  color: #6b7280;
  line-height: 1.4;
}

/* Price */
.plan-price {
  display: flex;
  align-items: baseline;
  gap: 0.25rem;
  margin-bottom: 1.25rem;
  padding-bottom: 1.25rem;
  border-bottom: 1px solid #f3f4f6;
}

.price-currency {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--color-primary-700, #2D2B6B);
}

.price-amount {
  font-size: 2rem;
  font-weight: 800;
  color: var(--color-primary-700, #2D2B6B);
  line-height: 1;
}

.price-usd {
  font-size: 0.8rem;
  font-weight: 600;
  color: #6b7280;
  margin-left: 0.25rem;
}

.price-period {
  font-size: 0.85rem;
  color: #9ca3af;
  font-weight: 500;
}

/* Members */
.plan-members {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: rgba(42, 175, 170, 0.08);
  color: #0f766e;
  font-size: 0.8rem;
  font-weight: 600;
  padding: 0.5rem 0.75rem;
  border-radius: 0.5rem;
  margin-bottom: 1.25rem;
}

/* Features */
.plan-features {
  list-style: none;
  padding: 0;
  margin: 0 0 1.5rem;
  flex: 1;
}

.plan-features li {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  font-size: 0.825rem;
  color: #4b5563;
  padding: 0.375rem 0;
}

.plan-features li i {
  color: #2AAFAA;
  font-size: 0.75rem;
  margin-top: 0.2rem;
  flex-shrink: 0;
}

/* CTA button */
.plan-btn {
  width: 100%;
  padding: 0.75rem 1rem;
  border-radius: 0.75rem;
  font-size: 0.875rem;
  font-weight: 600;
  border: none;
  cursor: pointer;
  transition: all 0.15s ease;
}

.plan-btn.btn-highlight {
  background: #2AAFAA;
  color: #fff;
}
.plan-btn.btn-highlight:hover {
  background: #239e99;
}

.plan-btn.btn-default {
  background: #f9fafb;
  color: var(--color-primary-700, #2D2B6B);
  border: 1px solid #e5e7eb;
}
.plan-btn.btn-default:hover:not(:disabled) {
  background: #f3f4f6;
}

.plan-btn.btn-current {
  background: #f0fdf4;
  color: #16a34a;
  border: 1px solid #bbf7d0;
  cursor: default;
}

.plan-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

/* Error */
.planes-error {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 0.75rem;
  color: #dc2626;
  font-size: 0.8rem;
  margin-bottom: 1rem;
}

/* Success */
.planes-success {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 0.75rem;
  color: #16a34a;
  font-size: 0.8rem;
  margin-bottom: 1rem;
}

/* Billing portal */
.planes-billing {
  display: flex;
  justify-content: center;
  margin-bottom: 1.5rem;
}

.btn-billing {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.625rem 1.25rem;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 0.75rem;
  color: var(--color-primary-700, #2D2B6B);
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}
.btn-billing:hover {
  background: #f3f4f6;
  border-color: #d1d5db;
}

/* Note */
.planes-note {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: #f9fafb;
  border-radius: 0.75rem;
  color: #6b7280;
  font-size: 0.8rem;
  line-height: 1.5;
}
.planes-note i {
  margin-top: 2px;
  flex-shrink: 0;
  color: #9ca3af;
}

/* Responsive */
@media (max-width: 768px) {
  .plans-grid {
    grid-template-columns: 1fr;
    gap: 1.25rem;
  }

  .plan-card.highlighted {
    order: -1;
  }

  .planes-title {
    font-size: 1.5rem;
  }
}

@media (min-width: 769px) and (max-width: 1023px) {
  .plans-grid {
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
  }

  .plan-card {
    padding: 1.5rem 1.25rem;
  }
}

/* ── Dark mode ───────────────────────────────────────────────────────────── */
:global(html.dark) .planes-title {
  color: #e1e8ed;
}

:global(html.dark) .planes-subtitle {
  color: #98a5b3;
}

:global(html.dark) .btn-back {
  color: #98a5b3;
}
:global(html.dark) .btn-back:hover {
  color: #e1e8ed;
}

:global(html.dark) .plan-card {
  background: #15202b;
  border-color: #2d3741;
}

:global(html.dark) .plan-card.highlighted {
  border-color: #2AAFAA;
  box-shadow: 0 4px 20px rgba(42, 175, 170, 0.08);
}

:global(html.dark) .plan-card.selected {
  border-color: #6366f1;
  box-shadow: 0 4px 20px rgba(99, 102, 241, 0.1);
}

:global(html.dark) .plan-name {
  color: #e1e8ed;
}

:global(html.dark) .plan-description {
  color: #98a5b3;
}

:global(html.dark) .price-currency,
:global(html.dark) .price-amount {
  color: #e1e8ed;
}

:global(html.dark) .price-usd {
  color: #7d8b99;
}

:global(html.dark) .price-period {
  color: #7d8b99;
}

:global(html.dark) .plan-price {
  border-bottom-color: #2d3741;
}

:global(html.dark) .plan-members {
  background: rgba(42, 175, 170, 0.1);
  color: #34d399;
}

:global(html.dark) .plan-features li {
  color: #c3ccd5;
}

:global(html.dark) .plan-btn.btn-default {
  background: #1c2b3a;
  color: #e1e8ed;
  border-color: #2d3741;
}
:global(html.dark) .plan-btn.btn-default:hover:not(:disabled) {
  background: #2d3741;
}

:global(html.dark) .plan-btn.btn-current {
  background: rgba(16, 185, 129, 0.1);
  color: #34d399;
  border-color: rgba(16, 185, 129, 0.25);
}

:global(html.dark) .planes-note {
  background: #1c2b3a;
  color: #98a5b3;
}
:global(html.dark) .planes-note i {
  color: #7d8b99;
}

:global(html.dark) .planes-error {
  background: rgba(220, 38, 38, 0.1);
  border-color: rgba(220, 38, 38, 0.25);
  color: #f87171;
}

:global(html.dark) .planes-success {
  background: rgba(16, 185, 129, 0.1);
  border-color: rgba(16, 185, 129, 0.25);
  color: #34d399;
}

:global(html.dark) .btn-billing {
  background: #1c2b3a;
  border-color: #2d3741;
  color: #e1e8ed;
}
:global(html.dark) .btn-billing:hover {
  background: #2d3741;
}

:global(html.dark) .plan-current-badge {
  background: #4f4cc4;
}
</style>
