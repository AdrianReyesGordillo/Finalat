<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  getCourseLessons,
  getLessonDetail,
  markLessonComplete,
  type CourseWithLessons,
  type LessonDetail,
  type LessonSummary,
} from '@/services/api'

const router = useRouter()
const route = useRoute()
const sidebarOpen = ref(false)

// State
const courseData = ref<CourseWithLessons | null>(null)
const currentLesson = ref<LessonDetail | null>(null)
const currentLessonIndex = ref(0)
const completedLessonIds = ref<Set<string>>(new Set())

const loading = ref(true)
const lessonLoading = ref(false)
const error = ref<string | null>(null)
const completing = ref(false)

// Computed
const courseId = computed(() => route.params.courseId as string)
const lessons = computed<LessonSummary[]>(() => courseData.value?.lessons || [])
const courseTitle = computed(() => courseData.value?.course.title || '')
const courseColor = computed(() => {
  const colors: Record<string, string> = {
    'finanzas-personales': '#2AAFAA',
    'renta-fija-variable': '#6366f1',
    'fundamentos-trading': '#f59e0b',
  }
  return colors[courseId.value] || '#2AAFAA'
})

const isFirstLesson = computed(() => currentLessonIndex.value === 0)
const isLastLesson = computed(() => currentLessonIndex.value === lessons.value.length - 1)
const progressPercent = computed(() => {
  if (lessons.value.length === 0) return 0
  return Math.round((completedLessonIds.value.size / lessons.value.length) * 100)
})

// Load course data
async function loadCourse() {
  loading.value = true
  error.value = null
  try {
    courseData.value = await getCourseLessons(courseId.value)
    if (lessons.value.length > 0) {
      await loadLesson(0)
    }
  } catch (e: any) {
    error.value = e.message || 'Error al cargar el curso.'
  } finally {
    loading.value = false
  }
}

// Load a specific lesson by index
async function loadLesson(index: number) {
  if (index < 0 || index >= lessons.value.length) return
  lessonLoading.value = true
  currentLessonIndex.value = index
  try {
    const lesson = lessons.value[index]
    const detail = await getLessonDetail(courseId.value, lesson.id)
    currentLesson.value = detail
    if (detail.completed) {
      completedLessonIds.value.add(detail.id)
    }
  } catch (e: any) {
    error.value = e.message || 'Error al cargar la lección.'
  } finally {
    lessonLoading.value = false
  }
}

// Navigation
async function handleNext() {
  if (!currentLesson.value) return

  // Mark current lesson as complete
  completing.value = true
  try {
    await markLessonComplete(courseId.value, currentLesson.value.id)
    completedLessonIds.value.add(currentLesson.value.id)
  } catch {
    // Non-blocking: progress is best-effort
  } finally {
    completing.value = false
  }

  if (!isLastLesson.value) {
    await loadLesson(currentLessonIndex.value + 1)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  } else {
    // Course completed — go back to catalog
    router.push('/aprende')
  }
}

function handlePrevious() {
  if (!isFirstLesson.value) {
    loadLesson(currentLessonIndex.value - 1)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }
}

async function navigateToLesson(index: number) {
  await loadLesson(index)
  sidebarOpen.value = false
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function goBack() {
  router.push('/aprende')
}

onMounted(loadCourse)

// Reload if route changes
watch(() => route.params.courseId, () => {
  if (route.params.courseId) {
    loadCourse()
  }
})
</script>

<template>
  <div v-if="!loading && courseData" class="course-learn-page">
    <!-- Mobile backdrop -->
    <div
      v-if="sidebarOpen"
      @click="sidebarOpen = false"
      class="sidebar-backdrop"
    ></div>

    <!-- Sidebar -->
    <aside class="course-sidebar" :class="{ open: sidebarOpen }">
      <button class="btn-back" @click="goBack">
        <i class="pi pi-arrow-left"></i>
        <span>Cursos</span>
      </button>

      <div class="sidebar-course-title">
        <h2>{{ courseTitle }}</h2>
      </div>

      <!-- Progress bar -->
      <div class="sidebar-progress">
        <div class="progress-header">
          <span class="progress-label">Tu progreso</span>
          <span class="progress-value">{{ progressPercent }}%</span>
        </div>
        <div class="progress-track">
          <div class="progress-fill" :style="{ width: progressPercent + '%', backgroundColor: courseColor }"></div>
        </div>
      </div>

      <!-- Lessons list -->
      <nav class="sidebar-nav">
        <div v-for="(lesson, index) in lessons" :key="lesson.id" class="nav-lesson">
          <button
            class="nav-lesson-btn"
            :class="{
              active: index === currentLessonIndex,
              completed: completedLessonIds.has(lesson.id),
            }"
            @click="navigateToLesson(index)"
          >
            <div class="lesson-status-icon">
              <i v-if="completedLessonIds.has(lesson.id)" class="pi pi-check-circle"></i>
              <div v-else-if="index === currentLessonIndex" class="dot-active"></div>
              <div v-else class="dot-unlocked"></div>
            </div>
            <span class="lesson-title-text">{{ lesson.title }}</span>
          </button>
        </div>
      </nav>
    </aside>

    <!-- Mobile toggle -->
    <button
      v-if="!sidebarOpen"
      @click="sidebarOpen = true"
      class="btn-mobile-sidebar"
    >
      <i class="pi pi-bars"></i>
      Progreso
    </button>

    <!-- Main content -->
    <main class="course-main">
      <div v-if="lessonLoading" class="lesson-loading">
        <div class="spinner"></div>
      </div>

      <div v-else-if="currentLesson">
        <!-- Lesson header -->
        <div class="lesson-header">
          <p class="lesson-counter">
            Lección {{ currentLessonIndex + 1 }} de {{ lessons.length }}
          </p>
          <h1 class="lesson-title">{{ currentLesson.title }}</h1>
        </div>

        <!-- Lesson content from API (HTML) -->
        <div class="lesson-content" v-html="currentLesson.content"></div>

        <!-- Navigation buttons -->
        <div class="lesson-nav">
          <button
            v-if="!isFirstLesson"
            @click="handlePrevious"
            class="btn-nav btn-prev"
          >
            <i class="pi pi-arrow-left"></i>
            Anterior
          </button>
          <div v-else></div>

          <button
            @click="handleNext"
            class="btn-nav btn-next"
            :style="{ backgroundColor: courseColor }"
            :disabled="completing"
          >
            {{ isLastLesson ? 'Finalizar curso' : 'Siguiente' }}
            <i :class="isLastLesson ? 'pi pi-check' : 'pi pi-arrow-right'"></i>
          </button>
        </div>
      </div>
    </main>
  </div>

  <!-- Loading -->
  <div v-else-if="loading" class="course-loading">
    <div class="spinner"></div>
  </div>

  <!-- Error -->
  <div v-else-if="error" class="course-error">
    <p>{{ error }}</p>
    <button @click="goBack" class="btn-nav btn-prev">Volver a cursos</button>
  </div>
</template>

<style scoped>
.course-learn-page {
  display: flex;
  min-height: calc(100dvh - 4rem);
}

/* Sidebar */
.course-sidebar {
  position: fixed;
  top: 4rem;
  left: 0;
  width: 16rem;
  height: calc(100dvh - 4rem);
  background: #fff;
  border-right: 1px solid #e5e7eb;
  padding: 1.25rem 0.75rem;
  overflow-y: auto;
  z-index: 20;
  transition: transform 0.2s ease;
}

@media (max-width: 768px) {
  .course-sidebar { transform: translateX(-100%); width: 17rem; }
  .course-sidebar.open { transform: translateX(0); }
}

.sidebar-backdrop { display: none; }
@media (max-width: 768px) {
  .sidebar-backdrop { display: block; position: fixed; inset: 0; top: 4rem; background: rgba(0, 0, 0, 0.4); z-index: 15; }
}

.btn-back {
  display: flex; align-items: center; gap: 0.5rem; font-size: 0.8rem; font-weight: 500;
  color: #6b7280; background: none; border: none; cursor: pointer;
  padding: 0.25rem 0.5rem; border-radius: 0.375rem; margin-bottom: 0.75rem; transition: color 0.15s;
}
.btn-back:hover { color: #374151; }

.sidebar-course-title h2 {
  font-size: 0.95rem; font-weight: 700; color: var(--color-primary-700, #2D2B6B);
  margin-bottom: 1rem; line-height: 1.3;
}

.sidebar-progress { margin-bottom: 1.25rem; }
.progress-header { display: flex; justify-content: space-between; margin-bottom: 0.375rem; }
.progress-label { font-size: 0.7rem; font-weight: 600; color: #6b7280; }
.progress-value { font-size: 0.7rem; font-weight: 700; color: var(--color-primary-700, #2D2B6B); }
.progress-track { height: 0.375rem; background: #f3f4f6; border-radius: 9999px; overflow: hidden; }
.progress-fill { height: 100%; border-radius: 9999px; transition: width 0.5s ease; }

/* Sidebar navigation */
.nav-lesson { margin-bottom: 0.125rem; }
.nav-lesson-btn {
  width: 100%; display: flex; align-items: center; gap: 0.5rem;
  padding: 0.5rem 0.5rem; border-radius: 0.5rem; border: none; background: none;
  cursor: pointer; font-size: 0.8rem; color: #4b5563; text-align: left; transition: all 0.15s;
}
.nav-lesson-btn:hover { background: #f9fafb; }
.nav-lesson-btn.active { background: rgba(42, 175, 170, 0.08); color: var(--color-primary-700, #2D2B6B); font-weight: 600; }
.nav-lesson-btn.completed { color: #9ca3af; }

.lesson-status-icon {
  width: 1.25rem; height: 1.25rem; display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.lesson-status-icon .pi-check-circle { color: #2AAFAA; font-size: 1rem; }
.dot-active {
  width: 0.625rem; height: 0.625rem; border-radius: 50%; background: var(--color-primary-700, #2D2B6B);
  box-shadow: 0 0 0 3px rgba(45, 43, 107, 0.15);
}
.dot-unlocked { width: 0.5rem; height: 0.5rem; border-radius: 50%; border: 2px solid #d1d5db; }
.lesson-title-text { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* Mobile sidebar toggle */
.btn-mobile-sidebar {
  display: none; position: fixed; top: 5rem; left: 0.5rem; z-index: 30;
  align-items: center; gap: 0.5rem; font-size: 0.8rem; font-weight: 600;
  color: var(--color-primary-700, #2D2B6B); background: #fff; border: 1px solid #e5e7eb;
  border-radius: 0.5rem; padding: 0.5rem 0.75rem; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08); cursor: pointer;
}
@media (max-width: 768px) { .btn-mobile-sidebar { display: flex; } }

/* Main content */
.course-main {
  margin-left: 16rem; flex: 1; min-width: 0; max-width: 48rem;
  margin-right: auto; padding: 2rem 1.5rem;
}
@media (max-width: 768px) { .course-main { margin-left: 0; padding: 4rem 1rem 2rem; } }

.lesson-header { margin-bottom: 2rem; }
.lesson-counter { font-size: 0.8rem; font-weight: 500; color: #2AAFAA; margin-bottom: 0.25rem; }
.lesson-title { font-size: 1.5rem; font-weight: 700; color: var(--color-primary-700, #2D2B6B); }

/* Navigation buttons */
.lesson-nav {
  display: flex; align-items: center; justify-content: space-between;
  margin-top: 2.5rem; padding-top: 1.5rem; border-top: 1px solid #e5e7eb;
}
.btn-nav {
  display: flex; align-items: center; gap: 0.5rem; padding: 0.625rem 1.25rem;
  border-radius: 9999px; font-size: 0.875rem; font-weight: 600; border: none; cursor: pointer; transition: all 0.15s;
}
.btn-prev { background: #f9fafb; color: var(--color-primary-700, #2D2B6B); border: 1px solid #e5e7eb; }
.btn-prev:hover { background: #f3f4f6; }
.btn-next { color: #fff; }
.btn-next:hover { opacity: 0.9; }
.btn-next:disabled { opacity: 0.6; cursor: not-allowed; }

/* Loading & error */
.course-loading, .lesson-loading {
  display: flex; align-items: center; justify-content: center; min-height: calc(100dvh - 4rem);
}
.lesson-loading { min-height: 200px; }
.course-error { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: calc(100dvh - 4rem); gap: 1rem; color: #dc2626; }
.spinner {
  width: 2rem; height: 2rem; border: 3px solid #e5e7eb; border-top-color: var(--color-primary-700, #2D2B6B);
  border-radius: 50%; animation: spin 0.6s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ─── Lesson content styles (v-html) ─────────────────────────────────── */
.lesson-content :deep(h1) {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-primary-700, #2D2B6B);
  margin-bottom: 0.5rem;
}

.lesson-content :deep(h2) {
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--color-primary-700, #2D2B6B);
  margin-top: 2rem;
  margin-bottom: 0.75rem;
}

.lesson-content :deep(h3) {
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-primary-700, #2D2B6B);
  margin-bottom: 0.5rem;
}

.lesson-content :deep(p) {
  color: #374151;
  line-height: 1.7;
  margin-bottom: 1rem;
}

.lesson-content :deep(.subtitle) {
  color: #6b7280;
  margin-bottom: 1.5rem;
}

.lesson-content :deep(section) {
  margin-bottom: 2rem;
}

.lesson-content :deep(ul),
.lesson-content :deep(ol) {
  padding-left: 1.5rem;
  margin-bottom: 1rem;
  color: #374151;
}

.lesson-content :deep(ul) {
  list-style-type: disc;
}

.lesson-content :deep(ol) {
  list-style-type: decimal;
}

.lesson-content :deep(li) {
  margin-bottom: 0.5rem;
  line-height: 1.6;
}

.lesson-content :deep(strong) {
  font-weight: 600;
  color: #1f2937;
}

.lesson-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
  margin-bottom: 1.5rem;
  border: 1px solid #e5e7eb;
  border-radius: 0.75rem;
  overflow: hidden;
}

.lesson-content :deep(thead) {
  background: #f0f0fa;
}

.lesson-content :deep(th) {
  text-align: left;
  padding: 0.75rem;
  font-weight: 600;
  color: var(--color-primary-700, #2D2B6B);
}

.lesson-content :deep(td) {
  padding: 0.75rem;
  border-top: 1px solid #e5e7eb;
  color: #374151;
}

.lesson-content :deep(tr:nth-child(even)) {
  background: #fafafe;
}

/* Cards grid */
.lesson-content :deep(.card-grid) {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(14rem, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.lesson-content :deep(.card) {
  background: #fff;
  border: 1px solid #e0e0f0;
  border-radius: 0.75rem;
  padding: 1rem;
}

.lesson-content :deep(.card h3) {
  font-size: 0.9rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.lesson-content :deep(.card p) {
  font-size: 0.85rem;
  color: #4b5563;
  margin-bottom: 0.5rem;
}

.lesson-content :deep(.card ul) {
  font-size: 0.85rem;
  padding-left: 1.25rem;
}

.lesson-content :deep(.card-green) {
  background: #f0fdf4;
  border-color: #bbf7d0;
}
.lesson-content :deep(.card-green h3) { color: #166534; }
.lesson-content :deep(.card-green li),
.lesson-content :deep(.card-green p) { color: #15803d; }

.lesson-content :deep(.card-red) {
  background: #fef2f2;
  border-color: #fecaca;
}
.lesson-content :deep(.card-red h3) { color: #991b1b; }
.lesson-content :deep(.card-red li),
.lesson-content :deep(.card-red p) { color: #b91c1c; }

.lesson-content :deep(.card-orange) {
  background: #fffbeb;
  border-color: #fed7aa;
}
.lesson-content :deep(.card-orange h3) { color: #92400e; }
.lesson-content :deep(.card-orange li),
.lesson-content :deep(.card-orange p) { color: #b45309; }

/* Tip / info box */
.lesson-content :deep(.tip) {
  background: #f0f0fa;
  border: 1px solid #e0e0f0;
  border-radius: 0.75rem;
  padding: 1rem;
  font-size: 0.875rem;
  color: var(--color-primary-700, #2D2B6B);
  font-weight: 500;
  margin: 1rem 0;
}

/* Warning box */
.lesson-content :deep(.warning) {
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 0.75rem;
  padding: 1rem;
  margin: 1rem 0;
}
.lesson-content :deep(.warning h3) { color: #991b1b; margin-bottom: 0.5rem; }
.lesson-content :deep(.warning p) { font-size: 0.875rem; color: #b91c1c; }

/* Placeholder for in-development content */
.lesson-content :deep(.placeholder) {
  background: #fafafe;
  border: 1px solid #e0e0f0;
  border-radius: 0.75rem;
  padding: 1.5rem;
  text-align: center;
  color: #9ca3af;
}
</style>

<style>
/* Unscoped styles for dark mode (ensures correct specificity without scoped attribute conflicts) */
html.dark .course-learn-page { background: #0f1419; }
html.dark .course-sidebar { background: #15202b !important; border-right-color: #2d3741 !important; }
html.dark .course-main { background: #0f1419; }
html.dark .btn-back { color: #98a5b3; }
html.dark .btn-back:hover { color: #e1e8ed; }
html.dark .sidebar-course-title h2 { color: #e1e8ed; }
html.dark .progress-label { color: #7d8b99; }
html.dark .progress-value { color: #cdccea; }
html.dark .progress-track { background: #1c2b3a; }
html.dark .nav-lesson-btn { color: #c3ccd5; }
html.dark .nav-lesson-btn:hover { background: #1c2b3a; }
html.dark .nav-lesson-btn.active { background: rgba(42, 175, 170, 0.1); color: #e1e8ed; }
html.dark .nav-lesson-btn.completed { color: #7d8b99; }
html.dark .dot-unlocked { border-color: #3d4f5f; }
html.dark .dot-active { background: #2AAFAA; box-shadow: 0 0 0 3px rgba(42, 175, 170, 0.2); }
html.dark .btn-mobile-sidebar { background: #15202b; color: #e1e8ed; border-color: #2d3741; }
html.dark .lesson-counter { color: #2AAFAA; }
html.dark .lesson-title { color: #e1e8ed; }
html.dark .lesson-nav { border-top-color: #2d3741; }
html.dark .btn-prev { background: #1c2b3a; color: #e1e8ed; border-color: #2d3741; }
html.dark .btn-prev:hover { background: #2d3741; }
html.dark .course-loading .spinner,
html.dark .lesson-loading .spinner { border-color: #2d3741; border-top-color: #cdccea; }

/* Lesson content (v-html) dark mode */
html.dark .lesson-content h1,
html.dark .lesson-content h2,
html.dark .lesson-content h3 { color: #e1e8ed; }
html.dark .lesson-content p { color: #c3ccd5; }
html.dark .lesson-content .subtitle { color: #7d8b99; }
html.dark .lesson-content li { color: #c3ccd5; }
html.dark .lesson-content strong { color: #e1e8ed; }
html.dark .lesson-content td { color: #c3ccd5; border-top-color: #2d3741; }
html.dark .lesson-content th { color: #e1e8ed; }
html.dark .lesson-content thead { background: #1c2b3a; }
html.dark .lesson-content table { border-color: #2d3741; }
html.dark .lesson-content tr:nth-child(even) { background: #1c2b3a; }
html.dark .lesson-content .card { background: #1c2b3a; border-color: #2d3741; }
html.dark .lesson-content .card p { color: #98a5b3; }
html.dark .lesson-content .card-green { background: rgba(16, 185, 129, 0.08); border-color: rgba(16, 185, 129, 0.2); }
html.dark .lesson-content .card-green h3 { color: #34d399; }
html.dark .lesson-content .card-green li,
html.dark .lesson-content .card-green p { color: #6ee7b7; }
html.dark .lesson-content .card-red { background: rgba(239, 68, 68, 0.08); border-color: rgba(239, 68, 68, 0.2); }
html.dark .lesson-content .card-red h3 { color: #f87171; }
html.dark .lesson-content .card-red li,
html.dark .lesson-content .card-red p { color: #fca5a5; }
html.dark .lesson-content .card-orange { background: rgba(245, 158, 11, 0.08); border-color: rgba(245, 158, 11, 0.2); }
html.dark .lesson-content .card-orange h3 { color: #fbbf24; }
html.dark .lesson-content .card-orange li,
html.dark .lesson-content .card-orange p { color: #fcd34d; }
html.dark .lesson-content .tip { background: #1c2b3a; border-color: #2d3741; color: #cdccea; }
html.dark .lesson-content .warning { background: rgba(239, 68, 68, 0.06); border-color: rgba(239, 68, 68, 0.2); }
html.dark .lesson-content .warning h3 { color: #f87171; }
html.dark .lesson-content .warning p { color: #fca5a5; }
html.dark .lesson-content .placeholder { background: #1c2b3a; border-color: #2d3741; color: #7d8b99; }
</style>
