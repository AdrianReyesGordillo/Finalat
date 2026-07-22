<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

/**
 * ErrorAlert — Error notification component.
 * Listens to 'app:notification' custom events dispatched by useApi
 * and shows/hides messages with a timeout.
 * Supports dark mode via Tailwind dark: variants.
 */

interface Notification {
  id: number
  message: string
  severity: 'info' | 'warning' | 'error'
}

const notifications = ref<Notification[]>([])
let nextId = 0

function handleNotification(event: Event) {
  const { message, severity } = (event as CustomEvent).detail
  const id = nextId++
  notifications.value.push({ id, message, severity })

  // Auto-dismiss after 5 seconds
  setTimeout(() => {
    dismiss(id)
  }, 5000)
}

function dismiss(id: number) {
  notifications.value = notifications.value.filter((n) => n.id !== id)
}

function severityClasses(severity: string): string {
  switch (severity) {
    case 'error':
      return 'bg-red-50 border-red-400 text-red-800 dark:bg-red-900/30 dark:border-red-600 dark:text-red-300'
    case 'warning':
      return 'bg-yellow-50 border-yellow-400 text-yellow-800 dark:bg-yellow-900/30 dark:border-yellow-600 dark:text-yellow-300'
    case 'info':
      return 'bg-blue-50 border-blue-400 text-blue-800 dark:bg-blue-900/30 dark:border-blue-600 dark:text-blue-300'
    default:
      return 'bg-red-50 border-red-400 text-red-800 dark:bg-red-900/30 dark:border-red-600 dark:text-red-300'
  }
}

function severityIcon(severity: string): string {
  switch (severity) {
    case 'error':
      return '✕'
    case 'warning':
      return '⚠'
    case 'info':
      return 'ℹ'
    default:
      return '✕'
  }
}

onMounted(() => {
  window.addEventListener('app:notification', handleNotification)
})

onUnmounted(() => {
  window.removeEventListener('app:notification', handleNotification)
})
</script>

<template>
  <div
    class="fixed top-4 right-4 z-50 flex flex-col gap-2 max-w-sm"
    aria-live="polite"
    aria-atomic="false"
  >
    <TransitionGroup name="notification">
      <div
        v-for="notification in notifications"
        :key="notification.id"
        :class="[
          'flex items-start gap-2 rounded-lg border p-3 shadow-md',
          severityClasses(notification.severity),
        ]"
        role="alert"
      >
        <span class="shrink-0 text-lg" aria-hidden="true">
          {{ severityIcon(notification.severity) }}
        </span>
        <p class="flex-1 text-sm">{{ notification.message }}</p>
        <button
          class="shrink-0 rounded p-1 hover:bg-black/10 dark:hover:bg-white/10 focus:outline-2 focus:outline-offset-2 focus:outline-current"
          :aria-label="'Cerrar notificación'"
          @click="dismiss(notification.id)"
        >
          <span aria-hidden="true">&times;</span>
        </button>
      </div>
    </TransitionGroup>
  </div>
</template>

<style scoped>
.notification-enter-active,
.notification-leave-active {
  transition: all 0.3s ease;
}
.notification-enter-from {
  opacity: 0;
  transform: translateX(1rem);
}
.notification-leave-to {
  opacity: 0;
  transform: translateX(1rem);
}
</style>
