<script setup lang="ts">
/**
 * LoadingSpinner — A loading indicator component.
 * Displays a spinning animation centered within its container.
 * Supports dark mode via Tailwind dark: variants.
 */
defineProps<{
  /** Size of the spinner: 'sm' | 'md' | 'lg' */
  size?: 'sm' | 'md' | 'lg'
  /** Optional label for accessibility */
  label?: string
}>()

const sizeClasses: Record<string, string> = {
  sm: 'h-5 w-5 border-2',
  md: 'h-8 w-8 border-3',
  lg: 'h-12 w-12 border-4',
}
</script>

<template>
  <div
    class="flex items-center justify-center"
    role="status"
    :aria-label="label || 'Cargando'"
  >
    <div
      :class="[
        'animate-spin rounded-full border-solid border-blue-600 border-t-transparent dark:border-blue-400 dark:border-t-transparent',
        sizeClasses[size || 'md'],
      ]"
    />
    <span class="sr-only">{{ label || 'Cargando...' }}</span>
  </div>
</template>
