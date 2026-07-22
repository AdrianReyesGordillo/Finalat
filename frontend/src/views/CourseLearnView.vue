<script setup lang="ts">
import { ref, computed, onMounted, defineAsyncComponent, type Component } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useMultiCourseStore } from '@/stores/multiCourse'
import { COURSES, getSectionId, type CourseDefinition } from '@/data/courses'
import { getCourseQuizBySection } from '@/data/courseQuizzes'
import SectionTest from '@/components/SectionTest.vue'
import SectionTestResult from '@/components/SectionTestResult.vue'

const router = useRouter()
const route = useRoute()
const store = useMultiCourseStore()
const sidebarOpen = ref(false)

// Map lesson IDs to their Vue components
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

// Get current course from route
const courseId = computed(() => route.params.courseId as string)
const course = computed<CourseDefinition | undefined>(() => COURSES.find(c => c.id === courseId.value))
const progress = computed(() => store.getProgress(courseId.value))

const currentLesson = computed(() => {
  if (!course.value) return null
  return course.value.lessons[progress.value.currentLessonIndex]
})

const lessonComponent = computed(() => {
  if (!currentLesson.value) return null
  return lessonComponents[currentLesson.value.id] || null
})

const isFirstLesson = computed(() => progress.value.currentLessonIndex === 0)
const isLastLesson = computed(() => {
  if (!course.value) return false
  return progress.value.currentLessonIndex === course.value.lessons.length - 1
})

const progressPercent = computed(() => store.courseProgressPercent(courseId.value))

// Group lessons by section for sidebar
interface SectionGroup {
  name: string
  sectionId: string
  lessons: { index: number; id: string; title: string }[]
}

const groupedLessons = computed<SectionGroup[]>(() => {
  if (!course.value) return []
  const groups: SectionGroup[] = []
  let currentSection = ''

  course.value.lessons.forEach((lesson, index) => {
    if (lesson.section !== currentSection) {
      currentSection = lesson.section
      groups.push({
        name: currentSection,
        sectionId: getSectionId(currentSection),
        lessons: [],
      })
    }
    groups[groups.length - 1].lessons.push({ index, id: lesson.id, title: lesson.title })
  })

  return groups
})

// Quiz for current test
const currentQuiz = computed(() => {
  if (!store.currentTestSection || !store.activeTestCourseId) return null
  return getCourseQuizBySection(store.activeTestCourseId, store.currentTestSection)
})

onMounted(async () => {
  if (store.loading) {
    await store.loadProgress()
  }
  // If course not started, start it
  if (course.value && !store.isCourseStarted(courseId.value)) {
    await store.startCourse(courseId.value)
  }
})

async function handleNext() {
  const newIndex = await store.completeAndNext(courseId.value)
  if (newIndex >= 0) {
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }
}

async function handlePrevious() {
  await store.goToPrevious(courseId.value)
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

async function navigateToLesson(index: number) {
  if (store.isLessonUnlocked(courseId.value, index)) {
    await store.goToLesson(courseId.value, index)
    sidebarOpen.value = false
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }
}

function handleTestComplete(score: number) {
  store.onTestComplete(score)
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

async function handleTestContinue() {
  await store.onTestPass()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function handleTestRetry() {
  store.onTestRetry()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function goBack() {
  router.push('/aprende')
}
</script>

<template>
  <div v-if="course" class="course-learn-page">
    <!-- Mobile backdrop -->
    <div
      v-if="sidebarOpen"
      @click="sidebarOpen = false"
      class="sidebar-backdrop"
    ></div>

    <!-- Sidebar -->
    <aside class="course-sidebar" :class="{ open: sidebarOpen }">
      <!-- Back button -->
      <button class="btn-back" @click="goBack">
        <i class="pi pi-arrow-left"></i>
        <span>Cursos</span>
      </button>

      <!-- Course title -->
      <div class="sidebar-course-title">
        <h2>{{ course.title }}</h2>
      </div>

      <!-- Progress bar -->
      <div class="sidebar-progress">
        <div class="progress-header">
          <span class="progress-label">Tu progreso</span>
          <span class="progress-value">{{ progressPercent }}%</span>
        </div>
        <div class="progress-track">
          <div class="progress-fill" :style="{ width: progressPercent + '%', backgroundColor: course.color }"></div>
        </div>
      </div>

      <!-- Sections -->
      <nav class="sidebar-nav">
        <div v-for="group in groupedLessons" :key="group.name" class="nav-section">
          <h3 class="nav-section-title">
            {{ group.name }}
            <i v-if="store.isSectionPassed(courseId, group.sectionId)" class="pi pi-check-circle section-passed-icon"></i>
          </h3>

          <div v-for="{ index, id, title } in group.lessons" :key="id" class="nav-lesson">
            <button
              class="nav-lesson-btn"
              :class="{
                active: index === progress.currentLessonIndex && !store.showingTest && !store.showingResult,
                completed: store.isLessonCompleted(courseId, id),
                locked: !store.isLessonUnlocked(courseId, index),
              }"
              :disabled="!store.isLessonUnlocked(courseId, index)"
              @click="navigateToLesson(index)"
            >
              <!-- Status icon -->
              <div class="lesson-status-icon">
                <i v-if="store.isLessonCompleted(courseId, id)" class="pi pi-check-circle"></i>
                <div v-else-if="index === progress.currentLessonIndex && !store.showingTest && !store.showingResult" class="dot-active"></div>
                <div v-else-if="store.isLessonUnlocked(courseId, index)" class="dot-unlocked"></div>
                <i v-else class="pi pi-lock"></i>
              </div>
              <span class="lesson-title-text">{{ title }}</span>
            </button>
          </div>
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
      <!-- Test view -->
      <div v-if="store.showingTest && currentQuiz">
        <SectionTest
          :section-name="currentQuiz.sectionName"
          :questions="currentQuiz.questions"
          @complete="handleTestComplete"
        />
      </div>

      <!-- Result view -->
      <div v-else-if="store.showingResult">
        <SectionTestResult
          :score="store.lastTestScore"
          :total="10"
          :section-name="currentQuiz?.sectionName || ''"
          @continue="handleTestContinue"
          @retry="handleTestRetry"
        />
      </div>

      <!-- Normal lesson content -->
      <div v-else>
        <!-- Lesson header -->
        <div class="lesson-header">
          <p class="lesson-counter">
            Lección {{ progress.currentLessonIndex + 1 }} de {{ course.lessons.length }}
          </p>
          <h1 class="lesson-title">{{ currentLesson?.title }}</h1>
        </div>

        <!-- Dynamic lesson content -->
        <div class="prose prose-sm md:prose-base max-w-none">
          <component v-if="lessonComponent" :is="lessonComponent" />
        </div>

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
            :style="{ backgroundColor: course.color }"
          >
            {{ isLastLesson ? 'Finalizar curso' : 'Siguiente' }}
            <i :class="isLastLesson ? 'pi pi-check' : 'pi pi-arrow-right'"></i>
          </button>
        </div>
      </div>
    </main>
  </div>

  <!-- Loading -->
  <div v-else class="course-loading">
    <div class="spinner"></div>
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
  .course-sidebar {
    transform: translateX(-100%);
    width: 17rem;
  }
  .course-sidebar.open {
    transform: translateX(0);
  }
}

.sidebar-backdrop {
  display: none;
}
@media (max-width: 768px) {
  .sidebar-backdrop {
    display: block;
    position: fixed;
    inset: 0;
    top: 4rem;
    background: rgba(0, 0, 0, 0.4);
    z-index: 15;
  }
}

.btn-back {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8rem;
  font-weight: 500;
  color: #6b7280;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.25rem 0.5rem;
  border-radius: 0.375rem;
  margin-bottom: 0.75rem;
  transition: color 0.15s;
}
.btn-back:hover { color: #374151; }

.sidebar-course-title h2 {
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--color-primary-700, #2D2B6B);
  margin-bottom: 1rem;
  line-height: 1.3;
}

.sidebar-progress {
  margin-bottom: 1.25rem;
}
.progress-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.375rem;
}
.progress-label {
  font-size: 0.7rem;
  font-weight: 600;
  color: #6b7280;
}
.progress-value {
  font-size: 0.7rem;
  font-weight: 700;
  color: var(--color-primary-700, #2D2B6B);
}
.progress-track {
  height: 0.375rem;
  background: #f3f4f6;
  border-radius: 9999px;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  border-radius: 9999px;
  transition: width 0.5s ease;
}

/* Sidebar navigation */
.nav-section {
  margin-bottom: 1rem;
}
.nav-section-title {
  font-size: 0.65rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #9ca3af;
  margin-bottom: 0.375rem;
  padding-left: 0.25rem;
  display: flex;
  align-items: center;
  gap: 0.375rem;
}
.section-passed-icon {
  font-size: 0.75rem;
  color: #2AAFAA;
}

.nav-lesson-btn {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.5rem;
  border-radius: 0.5rem;
  border: none;
  background: none;
  cursor: pointer;
  font-size: 0.8rem;
  color: #4b5563;
  text-align: left;
  transition: all 0.15s;
}
.nav-lesson-btn:hover:not(:disabled) { background: #f9fafb; }
.nav-lesson-btn.active {
  background: rgba(42, 175, 170, 0.08);
  color: var(--color-primary-700, #2D2B6B);
  font-weight: 600;
}
.nav-lesson-btn.completed { color: #9ca3af; }
.nav-lesson-btn.locked {
  color: #d1d5db;
  cursor: not-allowed;
}

.lesson-status-icon {
  width: 1.25rem;
  height: 1.25rem;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.lesson-status-icon .pi-check-circle { color: #2AAFAA; font-size: 1rem; }
.lesson-status-icon .pi-lock { color: #d1d5db; font-size: 0.75rem; }
.dot-active {
  width: 0.625rem;
  height: 0.625rem;
  border-radius: 50%;
  background: var(--color-primary-700, #2D2B6B);
  box-shadow: 0 0 0 3px rgba(45, 43, 107, 0.15);
}
.dot-unlocked {
  width: 0.5rem;
  height: 0.5rem;
  border-radius: 50%;
  border: 2px solid #d1d5db;
}
.lesson-title-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Mobile sidebar toggle */
.btn-mobile-sidebar {
  display: none;
  position: fixed;
  top: 5rem;
  left: 0.5rem;
  z-index: 30;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--color-primary-700, #2D2B6B);
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  padding: 0.5rem 0.75rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  cursor: pointer;
}
@media (max-width: 768px) {
  .btn-mobile-sidebar { display: flex; }
}

/* Main content */
.course-main {
  margin-left: 16rem;
  flex: 1;
  min-width: 0;
  max-width: 48rem;
  margin-right: auto;
  padding: 2rem 1.5rem;
}
@media (max-width: 768px) {
  .course-main {
    margin-left: 0;
    padding: 4rem 1rem 2rem;
  }
}

.lesson-header {
  margin-bottom: 2rem;
}
.lesson-counter {
  font-size: 0.8rem;
  font-weight: 500;
  color: #2AAFAA;
  margin-bottom: 0.25rem;
}
.lesson-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-primary-700, #2D2B6B);
}

/* Navigation buttons */
.lesson-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 2.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e5e7eb;
}
.btn-nav {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.625rem 1.25rem;
  border-radius: 9999px;
  font-size: 0.875rem;
  font-weight: 600;
  border: none;
  cursor: pointer;
  transition: all 0.15s;
}
.btn-prev {
  background: #f9fafb;
  color: var(--color-primary-700, #2D2B6B);
  border: 1px solid #e5e7eb;
}
.btn-prev:hover { background: #f3f4f6; }
.btn-next {
  color: #fff;
}
.btn-next:hover { opacity: 0.9; }

/* Loading */
.course-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: calc(100dvh - 4rem);
}
.spinner {
  width: 2rem;
  height: 2rem;
  border: 3px solid #e5e7eb;
  border-top-color: var(--color-primary-700, #2D2B6B);
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ── Dark mode ───────────────────────────────────────────────────────────── */
:global(html.dark) .course-sidebar {
  background: #15202b;
  border-right-color: #2d3741;
}

:global(html.dark) .sidebar-backdrop {
  background: rgba(0, 0, 0, 0.6);
}

:global(html.dark) .btn-back {
  color: #98a5b3;
}
:global(html.dark) .btn-back:hover {
  color: #e1e8ed;
}

:global(html.dark) .sidebar-course-title h2 {
  color: #e1e8ed;
}

:global(html.dark) .progress-label {
  color: #7d8b99;
}
:global(html.dark) .progress-value {
  color: #cdccea;
}
:global(html.dark) .progress-track {
  background: #1c2b3a;
}

:global(html.dark) .nav-section-title {
  color: #7d8b99;
}

:global(html.dark) .nav-lesson-btn {
  color: #c3ccd5;
}
:global(html.dark) .nav-lesson-btn:hover:not(:disabled) {
  background: #1c2b3a;
}
:global(html.dark) .nav-lesson-btn.active {
  background: rgba(42, 175, 170, 0.1);
  color: #e1e8ed;
}
:global(html.dark) .nav-lesson-btn.completed {
  color: #7d8b99;
}
:global(html.dark) .nav-lesson-btn.locked {
  color: #3d4f5f;
}

:global(html.dark) .lesson-status-icon .pi-lock {
  color: #3d4f5f;
}
:global(html.dark) .dot-unlocked {
  border-color: #3d4f5f;
}
:global(html.dark) .dot-active {
  background: #2AAFAA;
  box-shadow: 0 0 0 3px rgba(42, 175, 170, 0.2);
}

:global(html.dark) .btn-mobile-sidebar {
  background: #15202b;
  color: #e1e8ed;
  border-color: #2d3741;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}

:global(html.dark) .lesson-title {
  color: #e1e8ed;
}

:global(html.dark) .lesson-nav {
  border-top-color: #2d3741;
}
:global(html.dark) .btn-prev {
  background: #1c2b3a;
  color: #e1e8ed;
  border-color: #2d3741;
}
:global(html.dark) .btn-prev:hover {
  background: #2d3741;
}

:global(html.dark) .course-loading .spinner {
  border-color: #2d3741;
  border-top-color: #cdccea;
}
</style>
