<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  score: number
  total: number
  sectionName: string
}>()

const emit = defineEmits<{
  retry: []
  continue: []
}>()

const passed = computed(() => props.score >= 7)
const percentage = computed(() => Math.round((props.score / props.total) * 100))
</script>

<template>
  <div class="max-w-lg mx-auto text-center">
    <!-- Result icon -->
    <div class="mb-6">
      <div
        class="w-24 h-24 mx-auto rounded-full flex items-center justify-center"
        :class="passed ? 'bg-[#E8F8F7]' : 'bg-red-50'"
      >
        <!-- Pass -->
        <svg v-if="passed" class="w-12 h-12 text-[#2AAFAA]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>
        <!-- Fail -->
        <svg v-else class="w-12 h-12 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>
      </div>
    </div>

    <!-- Score -->
    <h2 class="text-3xl font-bold mb-2" :class="passed ? 'text-[#2AAFAA]' : 'text-red-500'">
      {{ score }}/{{ total }}
    </h2>
    <p class="text-sm text-gray-500 mb-2">{{ percentage }}% de respuestas correctas</p>

    <!-- Message -->
    <div class="bg-white rounded-2xl border border-gray-200 p-6 mb-8 mt-6">
      <h3 class="text-lg font-bold mb-2" :class="passed ? 'text-primary-700' : 'text-red-600'">
        {{ passed ? '¡Felicidades!' : 'No alcanzaste el puntaje mínimo' }}
      </h3>
      <p v-if="passed" class="text-gray-600 text-sm leading-relaxed">
        Aprobaste la evaluación de <strong>{{ sectionName }}</strong>. 
        Puedes continuar con la siguiente sección del curso.
      </p>
      <p v-else class="text-gray-600 text-sm leading-relaxed">
        Necesitas al menos <strong>7 de 10</strong> respuestas correctas para avanzar a la siguiente sección. 
        Te recomendamos repasar el material e intentarlo de nuevo.
      </p>
    </div>

    <!-- Actions -->
    <div class="flex flex-col sm:flex-row items-center justify-center gap-3">
      <button
        v-if="passed"
        @click="emit('continue')"
        class="flex items-center gap-2 px-6 py-3 text-sm font-semibold text-white bg-[#2AAFAA] hover:bg-[#239e99] rounded-xl transition-colors"
      >
        Continuar
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
        </svg>
      </button>

      <button
        v-if="!passed"
        @click="emit('retry')"
        class="flex items-center gap-2 px-6 py-3 text-sm font-semibold text-white bg-primary-700 hover:bg-primary-800 rounded-xl transition-colors"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
        </svg>
        Reintentar evaluación
      </button>
    </div>
  </div>
</template>
