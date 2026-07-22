<template>
  <div class="payment-countdown" :class="{ urgent: days === 0 }">
    <i class="pi pi-clock" :style="{ color: clockColor }"></i>
    <span v-if="days === 0" class="urgent-text">HOY ES LA FECHA LÍMITE DE PAGO</span>
    <span v-else>{{ days }} días para el pago</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  days: { type: Number, required: true }
})

const clockColor = computed(() => {
  if (props.days === 0) return '#ef4444'
  if (props.days <= 5) return '#ef4444'
  if (props.days < 15) return '#f59e0b'
  return '#10b981'
})
</script>

<style scoped>
.payment-countdown {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background-color: var(--fin-surface-2);
  border-radius: 8px;
  color: var(--fin-text-muted);
  font-size: 0.8rem;
}

.payment-countdown.urgent {
  background-color: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
}

.urgent-text {
  color: #ef4444;
  font-weight: 700;
  letter-spacing: 0.5px;
}

.payment-countdown i {
  font-size: 0.9rem;
  transition: color 0.2s;
}
</style>
