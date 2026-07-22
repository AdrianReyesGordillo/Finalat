<script setup lang="ts">
import { onMounted, computed, defineAsyncComponent, type Component } from 'vue'
import { useRouter } from 'vue-router'
import { useCourseStore, COURSE_LESSONS } from '@/stores/course'
import AdBanner from '@/components/AdBanner.vue'

const router = useRouter()
const courseStore = useCourseStore()

// Map lesson IDs to their Vue components (reusing existing learn content)
const lessonComponents: Record<string, Component> = {
  'introduccion': defineAsyncComponent(() => import('./learn/ComoEmpiezo.vue')),
  'renta-fija': defineAsyncComponent(() => import('./learn/RentaFija.vue')),
  'renta-variable': defineAsyncComponent(() => import('./learn/RentaVariable.vue')),
  'conceptos': defineAsyncComponent(() => import('./learn/Conceptos.vue')),
  'fondo-emergencia': defineAsyncComponent(() => import('./learn/FondoEmergencia.vue')),
  'diversificacion': defineAsyncComponent(() => import('./learn/Diversificacion.vue')),
  'tarjeta-credito': defineAsyncComponent(() => import('./learn/TarjetaCredito.vue')),
  'cetes': defineAsyncComponent(() => import('./learn/Cetes.vue')),
  'cuentas-ahorro': defineAsyncComponent(() => import('./learn/CuentasAhorro.vue')),
  'acciones': defineAsyncComponent(() => import('./learn/Acciones.vue')),
  'trading': defineAsyncComponent(() => import('./learn/Trading.vue')),
  'tendencias': defineAsyncComponent(() => import('./learn/trading/Tendencias.vue')),
  'velas': defineAsyncComponent(() => import('./learn/trading/Velas.vue')),
  'patrones': defineAsyncComponent(() => import('./learn/trading/Patrones.vue')),
  'indicadores': defineAsyncComponent(() => import('./learn/trading/Indicadores.vue')),
  'gestion-riesgo': defineAsyncComponent(() => import('./learn/trading/GestionRiesgo.vue')),
}

onMounted(async () => {
  if (courseStore.loading) {
    await courseStore.loadProgress()
  }
  if (!courseStore.enrolled) {
    router.push('/')
  }
})

const currentLesson = computed(() => COURSE_LESSONS[courseStore.currentLessonIndex])
const lessonComponent = computed(() => {
  const lessonId = currentLesson.value?.id
  return lessonId ? lessonComponents[lessonId] : null
})

async function handleNext() {
  await courseStore.completeCurrentAndNext()
}

async function handlePrevious() {
  await courseStore.goToPrevious()
}

function isLessonCompleted(lessonId: string): boolean {
  return courseStore.completedLessons.includes(lessonId)
}

function isLessonCurrent(index: number): boolean {
  return index === courseStore.currentLessonIndex
}

function canAccessLesson(index: number): boolean {
  if (index === courseStore.currentLessonIndex) return true
  if (index < courseStore.currentLessonIndex) return true
  const lesson = COURSE_LESSONS[index]
  return courseStore.completedLessons.includes(lesson.id)
}

async function navigateToLesson(index: number) {
  if (canAccessLesson(index)) {
    await courseStore.goToLesson(index)
  }
}
</script>

<template>
  <div v-if="!courseStore.loading" class="flex flex-col lg:flex-row min-h-[calc(100dvh-56px)]">
    <!-- Sidebar: Progreso del curso -->
    <aside class="lg:w-72 lg:min-h-full bg-white border-b lg:border-b-0 lg:border-r border-surface-200 p-4 lg:p-6 lg:sticky lg:top-14 lg:h-[calc(100dvh-56px)] lg:overflow-y-auto flex-shrink-0">
      <!-- Progress header -->
      <div class="mb-6">
        <h2 class="text-lg font-bold text-primary-700 mb-2">Plan de Aprendizaje</h2>
        <div class="flex items-center gap-3">
          <div class="flex-1 bg-surface-200 rounded-full h-2.5">
            <div
              class="bg-accent-500 h-2.5 rounded-full transition-all duration-500"
              :style="{ width: courseStore.progressPercent + '%' }"
            ></div>
          </div>
          <span class="text-sm font-medium text-primary-400">{{ courseStore.progressPercent }}%</span>
        </div>
        <p class="text-xs text-primary-300 mt-1">
          {{ courseStore.completedLessons.length }} de {{ courseStore.totalLessons }} lecciones
        </p>
      </div>

      <!-- Lesson list -->
      <nav class="space-y-1 hidden lg:block">
        <button
          v-for="(lesson, index) in COURSE_LESSONS"
          :key="lesson.id"
          @click="navigateToLesson(index)"
          :disabled="!canAccessLesson(index)"
          :class="[
            'w-full text-left px-3 py-2.5 rounded-xl text-sm font-medium transition-all flex items-center gap-3',
            isLessonCurrent(index)
              ? 'bg-primary-700 text-white shadow-sm'
              : isLessonCompleted(lesson.id)
                ? 'bg-surface-100 text-primary-600 hover:bg-surface-200'
                : canAccessLesson(index)
                  ? 'text-primary-400 hover:bg-surface-100'
                  : 'text-primary-200 cursor-not-allowed opacity-60',
          ]"
        >
          <!-- Status icon -->
          <div
            :class="[
              'w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 text-xs font-bold',
              isLessonCurrent(index)
                ? 'bg-white/20 text-white'
                : isLessonCompleted(lesson.id)
                  ? 'bg-green-100 text-green-600'
                  : 'bg-surface-200 text-primary-300',
            ]"
          >
            <svg v-if="isLessonCompleted(lesson.id) && !isLessonCurrent(index)" class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"/>
            </svg>
            <span v-else>{{ index + 1 }}</span>
          </div>
          <span class="truncate">{{ lesson.title }}</span>
        </button>
      </nav>
    </aside>

    <!-- Main content area -->
    <main class="flex-1 min-w-0">
      <div class="max-w-3xl mx-auto px-4 sm:px-6 py-8 md:py-12">
        <!-- Lesson header -->
        <div class="mb-8">
          <p class="text-sm font-medium text-accent-500 mb-1">
            Lección {{ courseStore.currentLessonIndex + 1 }} de {{ courseStore.totalLessons }}
          </p>
          <h1 class="text-2xl md:text-3xl font-bold text-primary-700">
            {{ currentLesson?.title }}
          </h1>
        </div>

        <!-- Ad banner -->
        <div class="mb-6">
          <AdBanner ad-format="auto" />
        </div>

        <!-- Dynamic lesson content -->
        <div class="prose prose-sm md:prose-base max-w-none">
          <component v-if="lessonComponent" :is="lessonComponent" />
        </div>

        <!-- Navigation buttons -->
        <div class="mt-12 flex items-center justify-between border-t border-surface-200 pt-6">
          <button
            v-if="!courseStore.isFirstLesson"
            @click="handlePrevious"
            class="flex items-center gap-2 px-5 py-3 bg-surface-100 hover:bg-surface-200 text-primary-700 font-medium rounded-full transition-colors border border-surface-200"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
            </svg>
            Anterior
          </button>
          <div v-else></div>

          <button
            v-if="!courseStore.isLastLesson"
            @click="handleNext"
            class="flex items-center gap-2 px-5 py-3 bg-accent-500 hover:bg-accent-600 text-primary-800 font-semibold rounded-full transition-colors"
          >
            Siguiente
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
            </svg>
          </button>
          <div v-else class="flex items-center gap-2 px-5 py-3 bg-green-100 text-green-700 font-semibold rounded-full">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
            </svg>
            ¡Curso completado!
          </div>
        </div>

        <!-- Bottom ad -->
        <div class="mt-8">
          <AdBanner ad-format="auto" />
        </div>
      </div>
    </main>
  </div>

  <!-- Loading state -->
  <div v-else class="flex items-center justify-center min-h-[calc(100dvh-56px)]">
    <div class="w-8 h-8 border-4 border-surface-200 border-t-primary-700 rounded-full animate-spin"></div>
  </div>
</template>
