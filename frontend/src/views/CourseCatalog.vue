<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useMultiCourseStore } from '@/stores/multiCourse'
import { COURSES } from '@/data/courses'

const router = useRouter()
const store = useMultiCourseStore()

onMounted(async () => {
  if (store.loading) {
    await store.loadProgress()
  }
  // Migrate old progress if needed
  const migrated = localStorage.getItem('learn_progress_migrated')
  if (!migrated && localStorage.getItem('learn_progress')) {
    await store.migrateOldProgress()
  }
})

function openCourse(courseId: string) {
  if (!store.isCourseStarted(courseId)) {
    store.startCourse(courseId)
  }
  router.push(`/aprende/${courseId}`)
}

function getCourseStatus(courseId: string): string {
  if (store.isCourseCompleted(courseId)) return 'Completado'
  if (store.isCourseStarted(courseId)) return 'En progreso'
  return 'Comenzar'
}

function getCourseStatusClass(courseId: string): string {
  if (store.isCourseCompleted(courseId)) return 'status-completed'
  if (store.isCourseStarted(courseId)) return 'status-progress'
  return 'status-new'
}
</script>

<template>
  <div class="catalog-page">
    <div class="catalog-header">
      <h1 class="catalog-title">Aprendizaje</h1>
      <p class="catalog-subtitle">
        Cursos diseñados para que domines tus finanzas personales a tu propio ritmo. Puedes tomar varios cursos a la vez.
      </p>
    </div>

    <div v-if="store.loading" class="catalog-loading">
      <div class="spinner"></div>
    </div>

    <div v-else class="courses-grid">
      <div
        v-for="course in COURSES"
        :key="course.id"
        class="course-card"
        @click="openCourse(course.id)"
      >
        <!-- Progress bar -->
        <div class="course-progress-bar">
          <div
            class="course-progress-fill"
            :style="{ width: store.courseProgressPercent(course.id) + '%', backgroundColor: course.color }"
          ></div>
        </div>

        <div class="course-card-body">
          <!-- Icon -->
          <div class="course-icon" :style="{ backgroundColor: course.color + '18' }">
            <i :class="'pi ' + course.icon" :style="{ color: course.color }"></i>
          </div>

          <!-- Content -->
          <div class="course-info">
            <h3 class="course-title">{{ course.title }}</h3>
            <p class="course-description">{{ course.description }}</p>

            <div class="course-meta">
              <span class="course-lessons-count">
                <i class="pi pi-book"></i>
                {{ course.lessons.length }} lecciones
              </span>
              <span class="course-tests-count">
                <i class="pi pi-check-circle"></i>
                {{ course.testSections.length }} evaluaciones
              </span>
            </div>
          </div>

          <!-- Status / CTA -->
          <div class="course-footer">
            <div class="course-progress-text" v-if="store.isCourseStarted(course.id) && !store.isCourseCompleted(course.id)">
              {{ store.courseProgressPercent(course.id) }}% completado
            </div>

            <button class="course-btn" :class="getCourseStatusClass(course.id)">
              <i v-if="store.isCourseCompleted(course.id)" class="pi pi-check"></i>
              <i v-else-if="store.isCourseStarted(course.id)" class="pi pi-play"></i>
              <i v-else class="pi pi-arrow-right"></i>
              {{ getCourseStatus(course.id) }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.catalog-page {
  max-width: 900px;
  margin: 0 auto;
  padding: 2rem 1rem;
}

.catalog-header {
  margin-bottom: 2rem;
}

.catalog-title {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--color-primary-700, #2D2B6B);
  margin-bottom: 0.5rem;
}

.catalog-subtitle {
  color: #6b7280;
  font-size: 0.95rem;
  line-height: 1.5;
}

.catalog-loading {
  display: flex;
  justify-content: center;
  padding: 4rem 0;
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

.courses-grid {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.course-card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 1rem;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.course-card:hover {
  border-color: #d1d5db;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}

.course-progress-bar {
  height: 4px;
  background: #f3f4f6;
}

.course-progress-fill {
  height: 100%;
  border-radius: 0 2px 2px 0;
  transition: width 0.5s ease;
}

.course-card-body {
  padding: 1.5rem;
}

.course-icon {
  width: 3rem;
  height: 3rem;
  border-radius: 0.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1rem;
}

.course-icon i {
  font-size: 1.25rem;
}

.course-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--color-primary-700, #2D2B6B);
  margin-bottom: 0.5rem;
}

.course-description {
  color: #6b7280;
  font-size: 0.875rem;
  line-height: 1.5;
  margin-bottom: 1rem;
}

.course-meta {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
}

.course-lessons-count,
.course-tests-count {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.8rem;
  color: #9ca3af;
}

.course-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 0.75rem;
  border-top: 1px solid #f3f4f6;
}

.course-progress-text {
  font-size: 0.8rem;
  color: #6b7280;
  font-weight: 500;
}

.course-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  font-size: 0.85rem;
  font-weight: 600;
  border: none;
  cursor: pointer;
  transition: all 0.15s ease;
}

.course-btn.status-new {
  background: var(--color-primary-700, #2D2B6B);
  color: #fff;
}

.course-btn.status-new:hover {
  opacity: 0.9;
}

.course-btn.status-progress {
  background: #f0fdf4;
  color: #16a34a;
  border: 1px solid #bbf7d0;
}

.course-btn.status-completed {
  background: #f0fdf4;
  color: #16a34a;
  border: 1px solid #bbf7d0;
}

/* Responsive */
@media (max-width: 640px) {
  .catalog-page {
    padding: 1.5rem 0.75rem;
  }

  .catalog-title {
    font-size: 1.5rem;
  }

  .course-card-body {
    padding: 1.25rem;
  }

  .course-meta {
    flex-wrap: wrap;
    gap: 0.75rem;
  }
}

/* ── Dark mode ───────────────────────────────────────────────────────────── */
:global(html.dark) .catalog-title {
  color: #e1e8ed;
}

:global(html.dark) .catalog-subtitle {
  color: #98a5b3;
}

:global(html.dark) .spinner {
  border-color: #2d3741;
  border-top-color: #cdccea;
}

:global(html.dark) .course-card {
  background: #15202b;
  border-color: #2d3741;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}

:global(html.dark) .course-card:hover {
  border-color: #3d4f5f;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
}

:global(html.dark) .course-progress-bar {
  background: #1c2b3a;
}

:global(html.dark) .course-title {
  color: #e1e8ed;
}

:global(html.dark) .course-description {
  color: #98a5b3;
}

:global(html.dark) .course-lessons-count,
:global(html.dark) .course-tests-count {
  color: #7d8b99;
}

:global(html.dark) .course-footer {
  border-top-color: #2d3741;
}

:global(html.dark) .course-progress-text {
  color: #98a5b3;
}

:global(html.dark) .course-btn.status-new {
  background: #4f4cc4;
  color: #fff;
}

:global(html.dark) .course-btn.status-progress {
  background: rgba(16, 185, 129, 0.1);
  color: #34d399;
  border-color: rgba(16, 185, 129, 0.25);
}

:global(html.dark) .course-btn.status-completed {
  background: rgba(16, 185, 129, 0.1);
  color: #34d399;
  border-color: rgba(16, 185, 129, 0.25);
}
</style>
