import { defineStore } from 'pinia'
import { ref } from 'vue'
import { doc, getDoc, setDoc } from 'firebase/firestore'
import { db } from '@/firebase'
import { useAuthStore } from './auth'
import { COURSES, getSectionId } from '@/data/courses'

export interface CourseProgress {
  courseId: string
  currentLessonIndex: number
  completedLessons: string[]
  passedSections: string[]
  started: boolean
  completedAt?: string
}

export const useMultiCourseStore = defineStore('multiCourse', () => {
  const coursesProgress = ref<Record<string, CourseProgress>>({})
  const loading = ref(true)

  const showingTest = ref(false)
  const showingResult = ref(false)
  const lastTestScore = ref(0)
  const currentTestSection = ref('')
  const activeTestCourseId = ref('')

  function getProgress(courseId: string): CourseProgress {
    if (!coursesProgress.value[courseId]) {
      coursesProgress.value[courseId] = {
        courseId,
        currentLessonIndex: 0,
        completedLessons: [],
        passedSections: [],
        started: false,
      }
    }
    return coursesProgress.value[courseId]
  }

  function isCourseStarted(courseId: string): boolean {
    return getProgress(courseId).started
  }

  function isCourseCompleted(courseId: string): boolean {
    const course = COURSES.find(c => c.id === courseId)
    if (!course) return false
    const progress = getProgress(courseId)
    return progress.completedLessons.length >= course.lessons.length
  }

  function courseProgressPercent(courseId: string): number {
    const course = COURSES.find(c => c.id === courseId)
    if (!course) return 0
    const progress = getProgress(courseId)
    return Math.round((progress.completedLessons.length / course.lessons.length) * 100)
  }

  function isLessonCompleted(courseId: string, lessonId: string): boolean {
    return getProgress(courseId).completedLessons.includes(lessonId)
  }

  function isLessonUnlocked(courseId: string, index: number): boolean {
    const course = COURSES.find(c => c.id === courseId)
    if (!course) return false
    if (index === 0) return true
    const progress = getProgress(courseId)
    if (index === progress.currentLessonIndex) return true
    if (index < progress.currentLessonIndex) return true
    return progress.completedLessons.includes(course.lessons[index - 1].id)
  }

  function isSectionPassed(courseId: string, sectionId: string): boolean {
    return getProgress(courseId).passedSections.includes(sectionId)
  }

  function isLastOfSection(courseId: string, index: number): boolean {
    const course = COURSES.find(c => c.id === courseId)
    if (!course) return false
    const lesson = course.lessons[index]
    if (!lesson) return false
    const next = course.lessons[index + 1]
    return !next || next.section !== lesson.section
  }

  async function startCourse(courseId: string) {
    const progress = getProgress(courseId)
    progress.started = true
    await saveProgress()
  }

  async function completeAndNext(courseId: string): Promise<number> {
    const course = COURSES.find(c => c.id === courseId)
    if (!course) return -1

    const progress = getProgress(courseId)
    const lesson = course.lessons[progress.currentLessonIndex]

    if (lesson && !progress.completedLessons.includes(lesson.id)) {
      progress.completedLessons.push(lesson.id)
    }

    const lastOfSection = isLastOfSection(courseId, progress.currentLessonIndex)
    if (lastOfSection) {
      const sectionId = getSectionId(lesson.section)
      const courseHasTest = course.testSections.includes(sectionId)
      const alreadyPassed = isSectionPassed(courseId, sectionId)

      if (courseHasTest && !alreadyPassed) {
        currentTestSection.value = sectionId
        activeTestCourseId.value = courseId
        showingTest.value = true
        saveProgress()
        return -1
      }
    }

    showingTest.value = false
    showingResult.value = false

    if (progress.currentLessonIndex < course.lessons.length - 1) {
      progress.currentLessonIndex++
    } else {
      progress.completedAt = new Date().toISOString()
    }

    saveProgress()
    return progress.currentLessonIndex
  }

  async function goToPrevious(courseId: string) {
    const progress = getProgress(courseId)
    if (progress.currentLessonIndex > 0) {
      progress.currentLessonIndex--
      saveProgress()
    }
  }

  async function goToLesson(courseId: string, index: number) {
    const course = COURSES.find(c => c.id === courseId)
    if (!course) return
    if (index >= 0 && index < course.lessons.length && isLessonUnlocked(courseId, index)) {
      const progress = getProgress(courseId)
      progress.currentLessonIndex = index
      await saveProgress()
    }
  }

  function onTestComplete(score: number) {
    lastTestScore.value = score
    showingTest.value = false
    showingResult.value = true
  }

  async function onTestPass() {
    const courseId = activeTestCourseId.value
    const progress = getProgress(courseId)
    const course = COURSES.find(c => c.id === courseId)

    if (!progress.passedSections.includes(currentTestSection.value)) {
      progress.passedSections.push(currentTestSection.value)
    }

    showingResult.value = false
    currentTestSection.value = ''
    lastTestScore.value = 0

    if (course && progress.currentLessonIndex < course.lessons.length - 1) {
      progress.currentLessonIndex++
    } else if (course) {
      progress.completedAt = new Date().toISOString()
    }

    activeTestCourseId.value = ''
    await saveProgress()
  }

  function onTestRetry() {
    showingResult.value = false
    showingTest.value = true
    lastTestScore.value = 0
  }

  async function loadProgress() {
    const authStore = useAuthStore()

    const local = localStorage.getItem('multi_course_progress')
    let localData: Record<string, CourseProgress> | null = null
    if (local) {
      try {
        localData = JSON.parse(local)
        if (localData) {
          coursesProgress.value = localData
        }
      } catch {
        localData = null
      }
    }

    if (!authStore.user) {
      loading.value = false
      return
    }

    try {
      const docRef = doc(db, 'multi_course_progress', authStore.user.uid)
      const docSnap = await getDoc(docRef)

      if (docSnap.exists()) {
        const remoteData = docSnap.data().courses as Record<string, CourseProgress> | undefined
        if (remoteData) {
          const remoteTotal = Object.values(remoteData).reduce((sum, p) => sum + p.completedLessons.length, 0)
          const localTotal = Object.values(coursesProgress.value).reduce((sum, p) => sum + p.completedLessons.length, 0)

          if (remoteTotal > localTotal) {
            coursesProgress.value = remoteData
          }
        }
      }
    } catch (err) {
      console.warn('Error loading multi-course progress:', err)
    } finally {
      loading.value = false
    }
  }

  async function saveProgress() {
    const authStore = useAuthStore()
    const data = {
      courses: coursesProgress.value,
      updatedAt: new Date().toISOString(),
    }

    localStorage.setItem('multi_course_progress', JSON.stringify(coursesProgress.value))

    if (!authStore.user) return

    try {
      const docRef = doc(db, 'multi_course_progress', authStore.user.uid)
      await setDoc(docRef, data, { merge: true })
    } catch (err) {
      console.warn('Error saving multi-course progress:', err)
    }
  }

  return {
    coursesProgress,
    loading,
    showingTest,
    showingResult,
    lastTestScore,
    currentTestSection,
    activeTestCourseId,
    getProgress,
    isCourseStarted,
    isCourseCompleted,
    courseProgressPercent,
    isLessonCompleted,
    isLessonUnlocked,
    isSectionPassed,
    isLastOfSection,
    startCourse,
    completeAndNext,
    goToPrevious,
    goToLesson,
    onTestComplete,
    onTestPass,
    onTestRetry,
    loadProgress,
    saveProgress,
  }
})
