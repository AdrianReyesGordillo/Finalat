<script setup lang="ts">
import { ref, computed } from 'vue'
import type { QuizQuestion } from '@/data/learnQuestions'

const props = defineProps<{
  sectionName: string
  questions: QuizQuestion[]
}>()

const emit = defineEmits<{
  complete: [score: number]
}>()

const currentQuestionIndex = ref(0)
const answers = ref<(number | null)[]>(new Array(props.questions.length).fill(null))
const submitted = ref(false)

const currentQuestion = computed(() => props.questions[currentQuestionIndex.value])
const totalQuestions = computed(() => props.questions.length)
const allAnswered = computed(() => answers.value.every(a => a !== null))

function selectOption(optionIndex: number) {
  if (submitted.value) return
  answers.value[currentQuestionIndex.value] = optionIndex
}

function goToQuestion(index: number) {
  if (index >= 0 && index < totalQuestions.value) {
    currentQuestionIndex.value = index
  }
}

function nextQuestion() {
  if (currentQuestionIndex.value < totalQuestions.value - 1) {
    currentQuestionIndex.value++
  }
}

function prevQuestion() {
  if (currentQuestionIndex.value > 0) {
    currentQuestionIndex.value--
  }
}

function submitTest() {
  if (!allAnswered.value) return
  submitted.value = true
  const score = answers.value.reduce((acc: number, answer, i) => {
    return acc + (answer === props.questions[i].correctIndex ? 1 : 0)
  }, 0)
  emit('complete', score)
}
</script>

<template>
  <div class="max-w-2xl mx-auto">
    <!-- Header -->
    <div class="mb-8">
      <div class="flex items-center gap-3 mb-3">
        <div class="w-10 h-10 rounded-xl bg-[#E8F8F7] flex items-center justify-center">
          <svg class="w-5 h-5 text-[#2AAFAA]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
        </div>
        <div>
          <h2 class="text-xl font-bold text-primary-700">Evaluación: {{ sectionName }}</h2>
          <p class="text-sm text-gray-500">Necesitas al menos 7/10 para avanzar</p>
        </div>
      </div>

      <!-- Question indicators -->
      <div class="flex flex-wrap gap-2 mt-4">
        <button
          v-for="(_, i) in questions"
          :key="i"
          @click="goToQuestion(i)"
          class="w-8 h-8 rounded-lg text-xs font-bold flex items-center justify-center transition-all"
          :class="[
            i === currentQuestionIndex
              ? 'bg-primary-700 text-white'
              : answers[i] !== null
                ? 'bg-[#2AAFAA] text-white'
                : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
          ]"
        >
          {{ i + 1 }}
        </button>
      </div>
    </div>

    <!-- Question -->
    <div class="bg-white rounded-2xl border border-gray-200 p-6 md:p-8 mb-6">
      <p class="text-xs font-semibold text-gray-400 mb-2">
        Pregunta {{ currentQuestionIndex + 1 }} de {{ totalQuestions }}
      </p>
      <h3 class="text-lg font-semibold text-primary-700 mb-6">
        {{ currentQuestion.question }}
      </h3>

      <!-- Options -->
      <div class="space-y-3">
        <button
          v-for="(option, i) in currentQuestion.options"
          :key="i"
          @click="selectOption(i)"
          class="w-full text-left px-5 py-4 rounded-xl border-2 transition-all text-sm font-medium"
          :class="[
            answers[currentQuestionIndex] === i
              ? 'border-[#2AAFAA] bg-[#E8F8F7] text-primary-700'
              : 'border-gray-200 hover:border-gray-300 text-gray-700 hover:bg-gray-50'
          ]"
        >
          <div class="flex items-center gap-3">
            <div
              class="w-6 h-6 rounded-full border-2 flex items-center justify-center flex-shrink-0"
              :class="answers[currentQuestionIndex] === i ? 'border-[#2AAFAA] bg-[#2AAFAA]' : 'border-gray-300'"
            >
              <div v-if="answers[currentQuestionIndex] === i" class="w-2 h-2 rounded-full bg-white"></div>
            </div>
            <span>{{ option }}</span>
          </div>
        </button>
      </div>
    </div>

    <!-- Navigation -->
    <div class="flex items-center justify-between">
      <button
        v-if="currentQuestionIndex > 0"
        @click="prevQuestion"
        class="flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-primary-700 bg-white border border-gray-200 rounded-xl hover:bg-gray-50 transition-colors"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
        </svg>
        Anterior
      </button>
      <div v-else></div>

      <button
        v-if="currentQuestionIndex < totalQuestions - 1"
        @click="nextQuestion"
        :disabled="answers[currentQuestionIndex] === null"
        class="flex items-center gap-2 px-4 py-2.5 text-sm font-semibold text-white bg-primary-700 hover:bg-primary-800 rounded-xl transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
      >
        Siguiente
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
        </svg>
      </button>

      <!-- Submit button (last question) -->
      <button
        v-else
        @click="submitTest"
        :disabled="!allAnswered"
        class="flex items-center gap-2 px-5 py-2.5 text-sm font-semibold text-white bg-[#2AAFAA] hover:bg-[#239e99] rounded-xl transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
      >
        Enviar respuestas
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
        </svg>
      </button>
    </div>
  </div>
</template>
