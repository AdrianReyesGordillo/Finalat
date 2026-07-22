import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { apiGet, apiPost } from '../composables/useApi'

// --- Types ---

export interface Course {
  id: string
  title: string
  description: string
  lesson_count: number
  sort_order: number
  created_at: string | null
  updated_at: string | null
}

export interface CourseProgress {
  course_id: string
  course_title: string
  total_lessons: number
  completed_lessons: number
  progress_percentage: number
}

export interface LessonSummary {
  id: string
  course_id: string
  title: string
  sort_order: number
  created_at: string | null
  updated_at: string | null
}

export interface LessonDetail {
  id: string
  course_id: string
  title: string
  content: string
  sort_order: number
  completed: boolean
  completed_at: string | null
  recommendation: string | null
  created_at: string | null
  updated_at: string | null
}

export interface CourseWithLessons {
  course: {
    id: string
    title: string
    description: string
  }
  lessons: LessonSummary[]
}

/**
 * Pinia store for the Learning System.
 * Manages courses, lessons, and user progress state.
 */
export const useLearningStore = defineStore('learning', () => {
  // --- State ---
  const courses = ref<Course[]>([])
  const progress = ref<CourseProgress[]>([])
  const currentCourse = ref<CourseWithLessons | null>(null)
  const currentLesson = ref<LessonDetail | null>(null)

  const coursesLoading = ref(false)
  const coursesError = ref<string | null>(null)
  const progressLoading = ref(false)
  const lessonsLoading = ref(false)
  const lessonsError = ref<string | null>(null)
  const lessonLoading = ref(false)
  const lessonError = ref<string | null>(null)
  const completingLesson = ref(false)

  // --- Computed ---

  /** Courses merged with progress data */
  const coursesWithProgress = computed(() => {
    return courses.value.map((course) => {
      const p = progress.value.find((pr) => pr.course_id === course.id)
      return {
        ...course,
        total_lessons: p?.total_lessons ?? course.lesson_count,
        completed_lessons: p?.completed_lessons ?? 0,
        progress_percentage: p?.progress_percentage ?? 0,
      }
    })
  })

  // --- Actions ---

  async function fetchCourses() {
    coursesLoading.value = true
    coursesError.value = null
    try {
      const data = await apiGet<Course[]>('/api/courses')
      courses.value = data
    } catch (e: unknown) {
      coursesError.value = e instanceof Error ? e.message : 'Error al cargar cursos.'
    } finally {
      coursesLoading.value = false
    }
  }

  async function fetchProgress() {
    progressLoading.value = true
    try {
      const data = await apiGet<CourseProgress[]>('/api/courses/progress')
      progress.value = data
    } catch {
      // Non-blocking — progress simply won't be shown
    } finally {
      progressLoading.value = false
    }
  }

  async function fetchCourseLessons(courseId: string) {
    lessonsLoading.value = true
    lessonsError.value = null
    try {
      const data = await apiGet<CourseWithLessons>(`/api/courses/${courseId}/lessons`)
      currentCourse.value = data
    } catch (e: unknown) {
      lessonsError.value = e instanceof Error ? e.message : 'Error al cargar las lecciones.'
    } finally {
      lessonsLoading.value = false
    }
  }

  async function fetchLesson(courseId: string, lessonId: string) {
    lessonLoading.value = true
    lessonError.value = null
    try {
      const data = await apiGet<LessonDetail>(`/api/courses/${courseId}/lessons/${lessonId}`)
      currentLesson.value = data
    } catch (e: unknown) {
      lessonError.value = e instanceof Error ? e.message : 'Error al cargar la leccion.'
    } finally {
      lessonLoading.value = false
    }
  }

  async function markLessonComplete(courseId: string, lessonId: string) {
    completingLesson.value = true
    try {
      await apiPost(`/api/courses/${courseId}/lessons/${lessonId}/complete`)
      // Update local state
      if (currentLesson.value && currentLesson.value.id === lessonId) {
        currentLesson.value.completed = true
        currentLesson.value.completed_at = new Date().toISOString()
      }
      // Refresh progress data
      await fetchProgress()
    } catch (e: unknown) {
      lessonError.value = e instanceof Error ? e.message : 'Error al completar la leccion.'
    } finally {
      completingLesson.value = false
    }
  }

  function clearCurrentCourse() {
    currentCourse.value = null
    currentLesson.value = null
  }

  return {
    // State
    courses,
    progress,
    currentCourse,
    currentLesson,
    coursesLoading,
    coursesError,
    progressLoading,
    lessonsLoading,
    lessonsError,
    lessonLoading,
    lessonError,
    completingLesson,
    // Computed
    coursesWithProgress,
    // Actions
    fetchCourses,
    fetchProgress,
    fetchCourseLessons,
    fetchLesson,
    markLessonComplete,
    clearCurrentCourse,
  }
})
