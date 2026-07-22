<script setup lang="ts">
import Dialog from 'primevue/dialog'

/**
 * ConfirmDialog — Delete/action confirmation dialog.
 * Accepts message, onConfirm callback, and severity (warn/danger).
 * Supports dark mode via Tailwind dark: variants.
 */

defineProps<{
  /** Whether the dialog is visible (v-model) */
  visible: boolean
  /** Confirmation message to display */
  message: string
  /** Dialog title (default: "Confirmar acción") */
  title?: string
  /** Visual severity: 'warn' or 'danger' */
  severity?: 'warn' | 'danger'
  /** Confirm button text (default: "Confirmar") */
  confirmLabel?: string
  /** Cancel button text (default: "Cancelar") */
  cancelLabel?: string
  /** Whether confirm action is loading */
  loading?: boolean
}>()

const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void
  (e: 'confirm'): void
  (e: 'cancel'): void
}>()

function handleConfirm() {
  emit('confirm')
}

function handleCancel() {
  emit('cancel')
  emit('update:visible', false)
}

const severityStyles = {
  warn: {
    icon: '⚠',
    iconBg: 'bg-yellow-100 dark:bg-yellow-900/40',
    iconColor: 'text-yellow-600 dark:text-yellow-400',
    button: 'bg-yellow-600 hover:bg-yellow-700 focus:ring-yellow-500 dark:bg-yellow-500 dark:hover:bg-yellow-600',
  },
  danger: {
    icon: '✕',
    iconBg: 'bg-red-100 dark:bg-red-900/40',
    iconColor: 'text-red-600 dark:text-red-400',
    button: 'bg-red-600 hover:bg-red-700 focus:ring-red-500 dark:bg-red-500 dark:hover:bg-red-600',
  },
}
</script>

<template>
  <Dialog
    :visible="visible"
    :header="title || 'Confirmar acción'"
    modal
    :dismissable-mask="true"
    :close-on-escape="true"
    class="w-full max-w-md"
    @update:visible="emit('update:visible', $event)"
  >
    <div class="flex items-start gap-4 p-2">
      <!-- Icon -->
      <div
        :class="[
          'flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-xl',
          severityStyles[severity || 'danger'].iconBg,
          severityStyles[severity || 'danger'].iconColor,
        ]"
        aria-hidden="true"
      >
        {{ severityStyles[severity || 'danger'].icon }}
      </div>

      <!-- Message -->
      <p class="text-sm text-gray-700 dark:text-gray-300">
        {{ message }}
      </p>
    </div>

    <template #footer>
      <div class="flex justify-end gap-2">
        <button
          type="button"
          class="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-2 focus:outline-offset-2 focus:outline-blue-500 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
          @click="handleCancel"
        >
          {{ cancelLabel || 'Cancelar' }}
        </button>
        <button
          type="button"
          :class="[
            'rounded-lg px-4 py-2 text-sm font-medium text-white focus:outline-2 focus:outline-offset-2 disabled:opacity-50 disabled:cursor-not-allowed',
            severityStyles[severity || 'danger'].button,
          ]"
          :disabled="loading"
          @click="handleConfirm"
        >
          <span v-if="loading" class="mr-2 inline-block h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
          {{ confirmLabel || 'Confirmar' }}
        </button>
      </div>
    </template>
  </Dialog>
</template>
