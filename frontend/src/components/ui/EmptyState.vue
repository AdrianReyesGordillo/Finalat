<script setup lang="ts">
/**
 * EmptyState — Empty state placeholder component.
 * Displays a message and optional action when no data is available.
 * Supports dark mode via Tailwind dark: variants.
 */

defineProps<{
  /** Main message to display */
  message?: string
  /** Optional description below the message */
  description?: string
  /** Optional action button label */
  actionLabel?: string
}>()

const emit = defineEmits<{
  (e: 'action'): void
}>()
</script>

<template>
  <div class="flex flex-col items-center justify-center px-6 py-12 text-center">
    <!-- Icon/Illustration -->
    <div
      class="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-gray-100 dark:bg-gray-800"
      aria-hidden="true"
    >
      <svg
        class="h-8 w-8 text-gray-400 dark:text-gray-500"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="1.5"
          d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
        />
      </svg>
    </div>

    <!-- Message -->
    <p class="text-base font-medium text-gray-900 dark:text-gray-100">
      {{ message || 'Sin datos' }}
    </p>

    <!-- Description -->
    <p
      v-if="description"
      class="mt-1 text-sm text-gray-500 dark:text-gray-400"
    >
      {{ description }}
    </p>

    <!-- Slot for custom content -->
    <slot />

    <!-- Action button -->
    <button
      v-if="actionLabel"
      type="button"
      class="mt-4 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-2 focus:outline-offset-2 focus:outline-blue-500 dark:bg-blue-500 dark:hover:bg-blue-600"
      @click="emit('action')"
    >
      {{ actionLabel }}
    </button>
  </div>
</template>
