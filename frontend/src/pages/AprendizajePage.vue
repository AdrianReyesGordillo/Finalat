<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useLearningStore } from '../stores/learning'

const router = useRouter()
const store = useLearningStore()

function navigateToCourse(courseId: string) {
  router.push({ name: 'aprendizaje-curso', params: { courseId } })
}

onMounted(async () => {
  await Promise.all([store.fetchCourses(), store.fetchProgress()])
})
</script>

<template>
  <div class="p-6 space-y-6">
    <!-- Page header -->
    <div>
      <h1 class="text-2xl font-bold text-gray-900 dark:text-gray-100">Aprendizaje</h1>
      <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">
        Cursos de educacion financiera para mejorar tu manejo del dinero.
      </p>
    </div>

    <!-- Error state -->
    <div
      v-if="store.coursesError"
      class="rounded-lg border border-red-300 bg-red-50 p-4 dark:border-red-600 dark:bg-red-900/30"
      role="alert"
    >
      <p class="text-sm text-red-800 dark:text-red-200">{{ store.coursesError }}</p>
    </div>

    <!-- Loading state -->
    <div
      v-if="store.coursesLoading"
      class="flex items-center justify-center py-12"
    >
      <div
        class="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent"
        role="status"
        aria-label="Cargando cursos"
      />
    </div>

    <!-- Empty state -->
    <div
      v-else-if="store.coursesWithProgress.length === 0 && !store.coursesError"
      class="flex flex-col items-center justify-center py-16 text-center"
    >
      <svg
        class="h-16 w-16 text-gray-300 dark:text-gray-600"
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
      <p class="mt-4 text-lg font-medium text-gray-600 dark:text-gray-400">
        No hay cursos disponibles
      </p>
      <p class="mt-1 text-sm text-gray-500 dark:text-gray-500">
        Los cursos se agregaran proximamente.
      </p>
    </div>

    <!-- Course grid -->
    <div
      v-else
      class="grid gap-6 sm:grid-cols-2 lg:grid-cols-3"
    >
      <article
        v-for="course in store.coursesWithProgress"
        :key="course.id"
        class="group cursor-pointer rounded-xl border border-gray-200 bg-white p-5 shadow-sm transition-shadow hover:shadow-md focus-within:ring-2 focus-within:ring-blue-500 dark:border-gray-700 dark:bg-gray-800"
        role="button"
        tabindex="0"
        :aria-label="`Curso: ${course.title}`"
        @click="navigateToCourse(course.id)"
        @keydown.enter="navigateToCourse(course.id)"
        @keydown.space.prevent="navigateToCourse(course.id)"
      >
        <!-- Course title -->
        <h2
          class="text-lg font-semibold text-gray-900 group-hover:text-blue-600 dark:text-gray-100 dark:group-hover:text-blue-400"
        >
          {{ course.title }}
        </h2>

        <!-- Course description -->
        <p class="mt-2 text-sm text-gray-600 dark:text-gray-400 line-clamp-3">
          {{ course.description }}
        </p>

        <!-- Lesson count -->
        <div class="mt-4 flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
          <svg
            class="h-4 w-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <span>{{ course.lesson_count }} {{ course.lesson_count === 1 ? 'leccion' : 'lecciones' }}</span>
        </div>

        <!-- Progress bar -->
        <div class="mt-4">
          <div class="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
            <span>Progreso</span>
            <span>{{ course.progress_percentage }}%</span>
          </div>
          <div
            class="mt-1 h-2 w-full overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700"
            role="progressbar"
            :aria-valuenow="course.progress_percentage"
            aria-valuemin="0"
            aria-valuemax="100"
            :aria-label="`Progreso del curso: ${course.progress_percentage}%`"
          >
            <div
              class="h-full rounded-full transition-all duration-300"
              :class="[
                course.progress_percentage === 100
                  ? 'bg-green-500 dark:bg-green-400'
                  : 'bg-blue-500 dark:bg-blue-400'
              ]"
              :style="{ width: `${course.progress_percentage}%` }"
            />
          </div>
          <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
            {{ course.completed_lessons }} de {{ course.total_lessons }} completadas
          </p>
        </div>
      </article>
    </div>
  </div>
</template>
