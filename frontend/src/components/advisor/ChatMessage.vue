<script setup lang="ts">
/**
 * ChatMessage — Renders a single chat bubble.
 * User messages are aligned right with blue styling.
 * Assistant messages are aligned left with gray styling.
 */
defineProps<{
  role: 'user' | 'assistant'
  content: string
}>()
</script>

<template>
  <div
    class="flex w-full"
    :class="role === 'user' ? 'justify-end' : 'justify-start'"
  >
    <div
      class="max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap break-words"
      :class="
        role === 'user'
          ? 'bg-blue-600 text-white rounded-br-md dark:bg-blue-500'
          : 'bg-gray-100 text-gray-900 rounded-bl-md dark:bg-gray-700 dark:text-gray-100'
      "
      :aria-label="role === 'user' ? 'Tu mensaje' : 'Respuesta de Fina'"
    >
      {{ content }}
    </div>
  </div>
</template>
