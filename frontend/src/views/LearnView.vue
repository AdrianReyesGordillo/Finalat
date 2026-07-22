<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useLearnStore, LEARN_LESSONS } from '@/stores/learn'
import { getQuizBySection } from '@/data/learnQuestions'
import SectionTest from '@/components/SectionTest.vue'
import SectionTestResult from '@/components/SectionTestResult.vue'

const router = useRouter()
const route = useRoute()
const learnStore = useLearnStore()
const sidebarOpen = ref(false)
const initialized = ref(false)

onMounted(async () => {
  if (learnStore.loading) {
    await learnStore.loadProgress()
  }
  // Clear any stale test state from previous navigation
  if (learnStore.showingTest || learnStore.showingResult) {
    learnStore.showingTest = false
    learnStore.showingResult = false
    learnStore.currentTestSection = ''
  }
  // Always navigate to the user's current lesson on initial load
  await navigateToCurrentLesson(true)
  initialized.value = true
})

// Watch route changes to sync lesson index (only after initialization)
watch(() => route.path, (newPath) => {
  if (!initialized.value) return
  if (learnStore.showingTest || learnStore.showingResult) return
  
  const index = learnStore.getLessonIndexByRoute(newPath)
  if (index >= 0 && index !== learnStore.currentLessonIndex) {
    if (learnStore.isUnlocked(index)) {
      learnStore.currentLessonIndex = index
    } else {
      navigateToCurrentLesson(true)
    }
  }
})

async function navigateToCurrentLesson(replace = false) {
  const lesson = learnStore.currentLesson
  if (lesson) {
    const target = lesson.route
    console.log('[Learn] navigateToCurrentLesson -', replace ? 'replace' : 'push', 'to:', target, 'from:', route.path)
    if (replace) {
      await router.replace(target)
    } else {
      await router.push(target)
    }
  } else {
    console.warn('[Learn] navigateToCurrentLesson - no current lesson!')
  }
}

async function handleNext() {
  console.log('[Learn] handleNext called, current index:', learnStore.currentLessonIndex, 'current route:', route.path)
  const newIndex = await learnStore.completeAndNext()
  console.log('[Learn] completeAndNext returned:', newIndex, 'showingTest:', learnStore.showingTest)
  
  if (newIndex >= 0) {
    console.log('[Learn] Navigating to:', learnStore.currentLesson?.route)
    await navigateToCurrentLesson()
  }
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

async function handlePrevious() {
  await learnStore.goToPrevious()
  await navigateToCurrentLesson()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

// Test handlers
const currentQuiz = computed(() => {
  if (!learnStore.currentTestSection) return null
  return getQuizBySection(learnStore.currentTestSection)
})

function handleTestComplete(score: number) {
  learnStore.onTestComplete(score)
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

async function handleTestContinue() {
  await learnStore.onTestPass()
  navigateToCurrentLesson()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function handleTestRetry() {
  learnStore.onTestRetry()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

// Group lessons by section for the sidebar
interface SectionGroup {
  name: string
  lessons: { index: number; lesson: typeof LEARN_LESSONS[0] }[]
}

const groupedLessons = computed<SectionGroup[]>(() => {
  const groups: SectionGroup[] = []
  let currentSection = ''

  LEARN_LESSONS.forEach((lesson, index) => {
    if (lesson.section !== currentSection) {
      currentSection = lesson.section
      groups.push({ name: currentSection, lessons: [] })
    }
    groups[groups.length - 1].lessons.push({ index, lesson })
  })

  return groups
})
</script>

<template>
  <div class="flex">
    <!-- Backdrop móvil -->
    <div
      v-if="sidebarOpen"
      @click="sidebarOpen = false"
      class="md:hidden fixed inset-0 top-16 bg-black/40 z-10"
    ></div>

    <!-- Sidebar -->
    <aside
      class="fixed top-16 left-0 h-[calc(100dvh-4rem)] w-64 md:w-56 border-r border-gray-200 bg-white z-20 pt-5 px-3 overflow-y-auto transition-transform duration-200"
      :class="sidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'"
    >
      <!-- Progress bar -->
      <div class="mb-4 px-1">
        <div class="flex items-center justify-between mb-1.5">
          <span class="text-xs font-semibold text-primary-600">Tu progreso</span>
          <span class="text-xs font-bold text-primary-700">{{ learnStore.progressPercent }}%</span>
        </div>
        <div class="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
          <div
            class="h-full bg-[#2AAFAA] rounded-full transition-all duration-500"
            :style="{ width: learnStore.progressPercent + '%' }"
          ></div>
        </div>
      </div>

      <!-- Sections -->
      <nav>
        <div v-for="group in groupedLessons" :key="group.name" class="mb-4">
          <h3 class="text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-2 px-1">
            {{ group.name }}
            <span
              v-if="learnStore.isSectionPassed(learnStore.getSectionId(group.name))"
              class="ml-1 text-[#2AAFAA]"
            >✓</span>
          </h3>

          <div v-for="{ index, lesson } in group.lessons" :key="lesson.id" class="mb-0.5">
            <div
              class="flex items-center gap-2.5 px-2 py-2 rounded-lg text-sm transition-colors"
              :class="[
                index === learnStore.currentLessonIndex && !learnStore.showingTest && !learnStore.showingResult
                  ? 'bg-primary-50 text-primary-700 font-semibold'
                  : learnStore.isCompleted(lesson.id)
                    ? 'text-gray-500'
                    : learnStore.isUnlocked(index)
                      ? 'text-gray-600'
                      : 'text-gray-300'
              ]"
            >
              <!-- Status icon -->
              <div class="flex-shrink-0 w-5 h-5 flex items-center justify-center">
                <svg v-if="learnStore.isCompleted(lesson.id)" class="w-5 h-5 text-[#2AAFAA]" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
                </svg>
                <div v-else-if="index === learnStore.currentLessonIndex && !learnStore.showingTest && !learnStore.showingResult" class="w-3 h-3 rounded-full bg-primary-600 ring-2 ring-primary-200"></div>
                <div v-else-if="learnStore.isUnlocked(index)" class="w-3 h-3 rounded-full border-2 border-gray-300"></div>
                <svg v-else class="w-4 h-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
                </svg>
              </div>

              <span class="truncate text-[13px]">{{ lesson.title }}</span>
            </div>
          </div>
        </div>
      </nav>
    </aside>

    <!-- Mobile toggle -->
    <button
      v-if="!sidebarOpen"
      @click="sidebarOpen = true"
      class="md:hidden fixed top-[5rem] left-2 z-30 flex items-center gap-2 text-primary-700 font-semibold text-sm bg-white border border-gray-200 rounded-lg px-3 py-2 shadow-sm"
    >
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
      </svg>
      Progreso
    </button>

    <!-- Content -->
    <main class="md:ml-56 flex-1 min-w-0 px-4 sm:px-6 pt-16 pb-6 md:py-10 max-w-4xl">
      <!-- Test view -->
      <div v-if="learnStore.showingTest && currentQuiz">
        <SectionTest
          :section-name="currentQuiz.sectionName"
          :questions="currentQuiz.questions"
          @complete="handleTestComplete"
        />
      </div>

      <!-- Result view -->
      <div v-else-if="learnStore.showingResult">
        <SectionTestResult
          :score="learnStore.lastTestScore"
          :total="10"
          :section-name="currentQuiz?.sectionName || ''"
          @continue="handleTestContinue"
          @retry="handleTestRetry"
        />
      </div>

      <!-- Normal lesson content -->
      <div v-else>
        <router-view :key="route.fullPath" />

        <!-- Navigation buttons -->
        <div class="flex items-center justify-between mt-10 pt-6 border-t border-gray-200">
          <button
            v-if="!learnStore.isFirstLesson"
            @click="handlePrevious"
            class="flex items-center gap-2 px-5 py-2.5 text-sm font-medium text-primary-700 bg-white border border-gray-200 rounded-xl hover:bg-gray-50 transition-colors"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
            </svg>
            Anterior
          </button>
          <div v-else></div>

          <button
            @click="handleNext"
            class="flex items-center gap-2 px-5 py-2.5 text-sm font-semibold text-white bg-[#2AAFAA] hover:bg-[#239e99] rounded-xl transition-colors"
          >
            {{ learnStore.isLastLesson ? 'Finalizar curso' : 'Siguiente' }}
            <svg v-if="!learnStore.isLastLesson" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
            </svg>
            <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
            </svg>
          </button>
        </div>
      </div>
    </main>
  </div>
</template>
