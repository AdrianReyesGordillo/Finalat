<script setup lang="ts">
/**
 * FormModal — Generic modal for create/edit forms.
 * Uses PrimeVue Dialog for the modal shell.
 * Accepts title, v-model:visible, and provides slots for form content and footer.
 * Supports dark mode via Tailwind dark: variants.
 */

import Dialog from 'primevue/dialog'

defineProps<{
  /** Modal title */
  title: string
  /** Whether the modal is visible (v-model) */
  visible: boolean
  /** Optional max width class (default: max-w-lg) */
  maxWidth?: string
}>()

const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void
}>()

function closeModal() {
  emit('update:visible', false)
}
</script>

<template>
  <Dialog
    :visible="visible"
    :header="title"
    modal
    :dismissable-mask="true"
    :close-on-escape="true"
    :class="['w-full', maxWidth || 'max-w-lg']"
    @update:visible="emit('update:visible', $event)"
  >
    <!-- Form content slot -->
    <div class="space-y-4 p-2">
      <slot :close="closeModal" />
    </div>

    <!-- Footer slot -->
    <template #footer>
      <div class="flex justify-end gap-2">
        <slot name="footer" :close="closeModal">
          <button
            type="button"
            class="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-2 focus:outline-offset-2 focus:outline-blue-500 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
            @click="closeModal"
          >
            Cancelar
          </button>
        </slot>
      </div>
    </template>
  </Dialog>
</template>
