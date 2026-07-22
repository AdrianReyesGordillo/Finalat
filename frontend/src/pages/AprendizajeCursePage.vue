<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useLearningStore } from '../stores/learning'
import type { LessonSummary } from '../stores/learning'

const route = useRoute()
const router = useRouter()
const store = useLearningStore()

const courseId = computed(() => route.params.courseId as string)
const selectedLessonId = ref<string | null>(null)

// --- Computed ---

const lessonList = computed<LessonSummary[]>(() => {
  return store.currentCourse?.lessons ?? []
})

const courseTitle = computed(() => store.currentCourse?.course?.title ?? 'Curso')

const currentLessonIndex = computed(() => {
  if (!selectedLessonId.value) return -1
  return lessonList.value.findIndex((l) => l.id === selectedLessonId.value)
})

const hasPreviousLesson = computed(() => currentLessonIndex.value > 0)

const hasNextLesson = computed(() =>
  currentLessonIndex.value >= 0 && currentLessonIndex.value < lessonList.value.length - 1
)

// --- Actions ---

async function selectLesson(lessonId: string) {
  selectedLessonId.value = lessonId
  await store.fetchLesson(courseId.value, lessonId)
}

async function markComplete() {
  if (!selectedLessonId.value) return
  await store.markLessonComplete(courseId.value, selectedLessonId.value)
  // Refresh lessons to update completed status in sidebar
  await store.fetchCourseLessons(courseId.value)
}

function goToPreviousLesson() {
  if (!hasPreviousLesson.value) return
  const prevLesson = lessonList.value[currentLessonIndex.value - 1]
  selectLesson(prevLesson.id)
}

function goToNextLesson() {
  if (!hasNextLesson.value) return
  const nextLesson = lessonList.value[currentLessonIndex.value + 1]
  selectLesson(nextLesson.id)
}

function goBack() {
  router.push({ name: 'aprendizaje' })
}

// --- Lifecycle ---

onMounted(async () => {
  await store.fetchCourseLessons(courseId.value)
  await store.fetchProgress()

  // Auto-select first lesson if available
  if (lessonList.value.length > 0) {
    await selectLesson(lessonList.value[0].id)
  }
})

// Watch route params if user navigates between courses
watch(courseId, async (newId) => {
  if (newId) {
    store.clearCurrentCourse()
    selectedLessonId.value = null
    await store.fetchCourseLessons(newId)
    if (lessonList.value.length > 0) {
      await selectLesson(lessonList.value[0].id)
    }
  }
})
</script>

<template>
  <div class="flex h-full flex-col">
    <!-- Top bar with back button and course title -->
    <header
      class="flex items-center gap-3 border-b border-gray-200 bg-white px-4 py-3 dark:border-gray-700 dark:bg-gray-800"
    >
      <button
        type="button"
        class="inline-flex items-center gap-1 rounded-lg px-3 py-1.5 text-sm font-medium text-gray-600 hover:bg-gray-100 focus:outline-2 focus:outline-offset-2 focus:outline-blue-500 dark:text-gray-300 dark:hover:bg-gray-700"
        aria-label="Volver a cursos"
        @click="goBack"
      >
        <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
        Volver
      </button>
      <h1 class="text-lg font-semibold text-gray-900 dark:text-gray-100 truncate">
        {{ courseTitle }}
      </h1>
    </header>

    <!-- Loading state for lessons list -->
    <div
      v-if="store.lessonsLoading"
      class="flex items-center justify-center py-12"
    >
      <div
        class="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent"
        role="status"
        aria-label="Cargando lecciones"
      />
    </div>

    <!-- Error state -->
    <div
      v-else-if="store.lessonsError"
      class="p-6"
    >
      <div
        class="rounded-lg border border-red-300 bg-red-50 p-4 dark:border-red-600 dark:bg-red-900/30"
        role="alert"
      >
        <p class="text-sm text-red-800 dark:text-red-200">{{ store.lessonsError }}</p>
      </div>
    </div>

    <!-- Main content: sidebar + lesson viewer -->
    <div v-else class="flex flex-1 overflow-hidden">
      <!-- Lesson sidebar -->
      <aside
        class="w-64 flex-shrink-0 overflow-y-auto border-r border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-900"
        aria-label="Lista de lecciones"
      >
        <nav class="p-3 space-y-1">
          <button
            v-for="(lesson, index) in lessonList"
            :key="lesson.id"
            type="button"
            class="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm transition-colors focus:outline-2 focus:outline-offset-2 focus:outline-blue-500"
            :class="[
              selectedLessonId === lesson.id
                ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-200'
                : 'text-gray-700 hover:bg-gray-200 dark:text-gray-300 dark:hover:bg-gray-800'
            ]"
            :aria-current="selectedLessonId === lesson.id ? 'true' : undefined"
            @click="selectLesson(lesson.id)"
          >
            <!-- Lesson number / completion indicator -->
            <span
              class="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full text-xs font-medium"
              :class="[
                store.currentLesson?.id === lesson.id && store.currentLesson?.completed
                  ? 'bg-green-500 text-white'
                  : 'bg-gray-300 text-gray-700 dark:bg-gray-600 dark:text-gray-200'
              ]"
              :aria-label="
                store.currentLesson?.id === lesson.id && store.currentLesson?.completed
                  ? 'Leccion completada'
                  : `Leccion ${index + 1}`
              "
            >
              <template v-if="store.currentLesson?.id === lesson.id && store.currentLesson?.completed">
                <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
                </svg>
              </template>
              <template v-else>
                {{ index + 1 }}
              </template>
            </span>
            <span class="truncate">{{ lesson.title }}</span>
          </button>
        </nav>
      </aside>

      <!-- Lesson content viewer -->
      <main class="flex-1 overflow-y-auto p-6" aria-label="Contenido de la leccion">
        <!-- Loading lesson content -->
        <div
          v-if="store.lessonLoading"
          class="flex items-center justify-center py-12"
        >
          <div
            class="h-6 w-6 animate-spin rounded-full border-4 border-blue-500 border-t-transparent"
            role="status"
            aria-label="Cargando contenido"
          />
        </div>

        <!-- Lesson error -->
        <div
          v-else-if="store.lessonError"
          class="rounded-lg border border-red-300 bg-red-50 p-4 dark:border-red-600 dark:bg-red-900/30"
          role="alert"
        >
          <p class="text-sm text-red-800 dark:text-red-200">{{ store.lessonError }}</p>
        </div>

        <!-- Lesson content -->
        <article v-else-if="store.currentLesson" class="max-w-3xl space-y-6">
          <!-- Recommendation warning -->
          <div
            v-if="store.currentLesson.recommendation"
            class="rounded-lg border border-yellow-300 bg-yellow-50 p-4 dark:border-yellow-600 dark:bg-yellow-900/30"
            role="alert"
          >
            <div class="flex items-center gap-2">
              <svg class="h-5 w-5 text-yellow-600 dark:text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
              <p class="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                {{ store.currentLesson.recommendation }}
              </p>
            </div>
          </div>

          <!-- Lesson title -->
          <h2 class="text-2xl font-bold text-gray-900 dark:text-gray-100">
            {{ store.currentLesson.title }}
          </h2>

          <!-- Lesson content body -->
          <div
            class="prose prose-gray max-w-none dark:prose-invert prose-headings:text-gray-900 dark:prose-headings:text-gray-100 prose-p:text-gray-700 dark:prose-p:text-gray-300"
            v-html="store.currentLesson.content"
          />

          <!-- Actions bar -->
          <div class="flex flex-col gap-4 border-t border-gray-200 pt-6 dark:border-gray-700 sm:flex-row sm:items-center sm:justify-between">
            <!-- Mark as complete button -->
            <div>
              <button
                v-if="!store.currentLesson.completed"
                type="button"
                :disabled="store.completingLesson"
                class="inline-flex items-center gap-2 rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 focus:outline-2 focus:outline-offset-2 focus:outline-green-500 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-green-500 dark:hover:bg-green-600"
                @click="markComplete"
              >
                <span
                  v-if="store.completingLesson"
                  class="inline-block h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"
                  aria-hidden="true"
                />
                <svg v-else class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                </svg>
                Marcar como completada
              </button>
              <span
                v-else
                class="inline-flex items-center gap-2 text-sm font-medium text-green-600 dark:text-green-400"
              >
                <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Leccion completada
              </span>
            </div>

            <!-- Navigation buttons -->
            <div class="flex items-center gap-2">
              <button
                type="button"
                :disabled="!hasPreviousLesson"
                class="inline-flex items-center gap-1 rounded-lg border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-2 focus:outline-offset-2 focus:outline-blue-500 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
                aria-label="Leccion anterior"
                @click="goToPreviousLesson"
              >
                <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
                </svg>
                Anterior
              </button>
              <button
                type="button"
                :disabled="!hasNextLesson"
                class="inline-flex items-center gap-1 rounded-lg border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-2 focus:outline-offset-2 focus:outline-blue-500 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
                aria-label="Siguiente leccion"
                @click="goToNextLesson"
              >
                Siguiente
                <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                </svg>
              </button>
            </div>
          </div>
        </article>

        <!-- No lesson selected placeholder -->
        <div v-else class="flex flex-col items-center justify-center py-16 text-center">
          <svg
            class="h-12 w-12 text-gray-300 dark:text-gray-600"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="1.5"
              d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.331 0 4.472.89 6.042 2.348M12 6.042A8.967 8.967 0 0118 3.75c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18c-2.331 0-4.472.89-6.042 2.348M12 6.042V20.348"
            />
          </svg>
          <p class="mt-4 text-sm text-gray-500 dark:text-gray-400">
            Selecciona una leccion del menu lateral para comenzar.
          </p>
        </div>
      </main>
    </div>
  </div>
</template>
