<script setup lang="ts">
import { computed } from 'vue'

/**
 * CurrencyDisplay — Formatted monetary amount display (es-MX locale).
 * Formats numbers as MXN currency using Intl.NumberFormat.
 * Supports dark mode via Tailwind dark: variants.
 */
const props = defineProps<{
  /** Numeric amount to display */
  amount: number | null | undefined
  /** Show as positive/negative color indicator */
  colored?: boolean
  /** Override currency code (default: MXN) */
  currency?: string
}>()

const formatter = new Intl.NumberFormat('es-MX', {
  style: 'currency',
  currency: props.currency || 'MXN',
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
})

const formattedAmount = computed(() => {
  if (props.amount == null || isNaN(props.amount)) {
    return '—'
  }
  return formatter.format(props.amount)
})

const colorClass = computed(() => {
  if (!props.colored || props.amount == null) return ''
  if (props.amount > 0) return 'text-green-600 dark:text-green-400'
  if (props.amount < 0) return 'text-red-600 dark:text-red-400'
  return ''
})
</script>

<template>
  <span :class="['font-mono tabular-nums', colorClass]">
    {{ formattedAmount }}
  </span>
</template>
