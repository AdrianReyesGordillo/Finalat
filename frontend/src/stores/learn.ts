import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { doc, getDoc, setDoc } from 'firebase/firestore'
import { db } from '@/firebase'
import { useAuthStore } from './auth'

export interface LearnLesson {
  id: string
  title: string
  route: string
  section: string
}

export const LEARN_LESSONS: LearnLesson[] = [
  { id: 'introduccion', title: 'Introducción', route: '/aprende/como-empiezo/introduccion', section: '¿Cómo empiezo?' },
  { id: 'renta-fija', title: 'Renta fija', route: '/aprende/como-empiezo/renta-fija', section: '¿Cómo empiezo?' },
  { id: 'renta-variable', title: 'Renta variable', route: '/aprende/como-empiezo/renta-variable', section: '¿Cómo empiezo?' },
  { id: 'cetes', title: 'CETES', route: '/aprende/cetes', section: 'Instrumentos' },
  { id: 'cuentas-ahorro', title: 'Cuentas de ahorro', route: '/aprende/cuentas-ahorro', section: 'Instrumentos' },
  { id: 'acciones', title: 'Acciones', route: '/aprende/acciones', section: 'Instrumentos' },
  { id: 'trading', title: 'Trading: Introducción', route: '/aprende/trading', section: 'Trading' },
  { id: 'tendencias', title: 'Trading: Tendencias', route: '/aprende/trading/tendencias', section: 'Trading' },
  { id: 'velas', title: 'Trading: Velas japonesas', route: '/aprende/trading/velas', section: 'Trading' },
  { id: 'patrones', title: 'Trading: Patrones', route: '/aprende/trading/patrones', section: 'Trading' },
  { id: 'indicadores', title: 'Trading: Indicadores', route: '/aprende/trading/indicadores', section: 'Trading' },
  { id: 'gestion-riesgo', title: 'Trading: Gestión de riesgo', route: '/aprende/trading/gestion-riesgo', section: 'Trading' },
  { id: 'conceptos', title: 'Conceptos generales', route: '/aprende/conceptos', section: 'Conceptos' },
  { id: 'fondo-emergencia', title: 'Fondo de emergencia', route: '/aprende/conceptos/fondo-emergencia', section: 'Conceptos' },
  { id: 'diversificacion', title: 'Diversificación', route: '/aprende/conceptos/diversificacion', section: 'Conceptos' },
  { id: 'tarjeta-credito', title: '¿Cómo funciona una TDC?', route: '/aprende/conceptos/tarjeta-credito', section: 'Conceptos' },
]

export const useLearnStore = defineStore('learn', () => {
  const currentLessonIndex = ref(0)
  const completedLessons = ref<string[]>([])
  const passedSections = ref<string[]>([])
  const loading = ref(true)

  const showingTest = ref(false)
  const showingResult = ref(false)
  const lastTestScore = ref(0)
  const currentTestSection = ref('')

  const totalLessons = computed(() => LEARN_LESSONS.length)
  const currentLesson = computed(() => LEARN_LESSONS[currentLessonIndex.value])
  const progressPercent = computed(() =>
    Math.round((completedLessons.value.length / totalLessons.value) * 100)
  )
  const isFirstLesson = computed(() => currentLessonIndex.value === 0)
  const isLastLesson = computed(() => currentLessonIndex.value === totalLessons.value - 1)

  function isLastOfSection(index: number): boolean {
    const lesson = LEARN_LESSONS[index]
    if (!lesson) return false
    const next = LEARN_LESSONS[index + 1]
    return !next || next.section !== lesson.section
  }

  function getSectionId(section: string): string {
    if (section === '¿Cómo empiezo?') return 'como-empiezo'
    if (section === 'Instrumentos') return 'instrumentos'
    if (section === 'Trading') return 'trading'
    if (section === 'Conceptos') return 'conceptos'
    return section.toLowerCase()
  }

  function isSectionPassed(sectionId: string): boolean {
    return passedSections.value.includes(sectionId)
  }

  function isCompleted(lessonId: string): boolean {
    return completedLessons.value.includes(lessonId)
  }

  function isUnlocked(index: number): boolean {
    if (index === 0) return true
    if (index === currentLessonIndex.value) return true
    return completedLessons.value.includes(LEARN_LESSONS[index - 1].id)
  }

  function getLessonIndexByRoute(route: string): number {
    return LEARN_LESSONS.findIndex(l => l.route === route)
  }

  async function loadProgress() {
    const authStore = useAuthStore()

    const local = localStorage.getItem('learn_progress')
    let localData: { currentLessonIndex?: number; completedLessons?: string[]; passedSections?: string[] } | null = null
    if (local) {
      try {
        localData = JSON.parse(local)
        currentLessonIndex.value = localData?.currentLessonIndex || 0
        completedLessons.value = localData?.completedLessons || []
        passedSections.value = localData?.passedSections || []
      } catch {
        localData = null
      }
    }

    if (!authStore.user) {
      loading.value = false
      return
    }

    try {
      const docRef = doc(db, 'learn_progress', authStore.user.uid)
      const docSnap = await getDoc(docRef)

      if (docSnap.exists()) {
        const remoteData = docSnap.data()
        const remoteCompleted = remoteData.completedLessons?.length || 0
        const localCompleted = localData?.completedLessons?.length || 0

        if (remoteCompleted > localCompleted) {
          currentLessonIndex.value = remoteData.currentLessonIndex || 0
          completedLessons.value = remoteData.completedLessons || []
          passedSections.value = remoteData.passedSections || []
        }
      }
    } catch (err) {
      console.warn('Error loading learn progress from Firestore:', err)
    } finally {
      loading.value = false
    }
  }

  async function saveProgress() {
    const authStore = useAuthStore()
    const data = {
      currentLessonIndex: currentLessonIndex.value,
      completedLessons: completedLessons.value,
      passedSections: passedSections.value,
      updatedAt: new Date().toISOString(),
    }

    localStorage.setItem('learn_progress', JSON.stringify(data))

    if (!authStore.user) return

    try {
      const docRef = doc(db, 'learn_progress', authStore.user.uid)
      await setDoc(docRef, data, { merge: true })
    } catch (err) {
      console.warn('Error saving learn progress:', err)
    }
  }

  async function completeAndNext(): Promise<number> {
    const lesson = LEARN_LESSONS[currentLessonIndex.value]
    if (lesson && !completedLessons.value.includes(lesson.id)) {
      completedLessons.value.push(lesson.id)
    }

    const lastOfSection = isLastOfSection(currentLessonIndex.value)
    if (lastOfSection) {
      const sectionId = getSectionId(lesson.section)
      const alreadyPassed = isSectionPassed(sectionId)
      if (!alreadyPassed) {
        currentTestSection.value = sectionId
        showingTest.value = true
        saveProgress()
        return -1
      }
    }

    showingTest.value = false
    showingResult.value = false

    let newIndex = currentLessonIndex.value
    if (currentLessonIndex.value < totalLessons.value - 1) {
      currentLessonIndex.value++
      newIndex = currentLessonIndex.value
    }

    saveProgress()
    return newIndex
  }

  function onTestComplete(score: number) {
    lastTestScore.value = score
    showingTest.value = false
    showingResult.value = true
  }

  async function onTestPass() {
    if (!passedSections.value.includes(currentTestSection.value)) {
      passedSections.value.push(currentTestSection.value)
    }
    showingResult.value = false
    currentTestSection.value = ''
    lastTestScore.value = 0

    if (currentLessonIndex.value < totalLessons.value - 1) {
      currentLessonIndex.value++
    }

    await saveProgress()
  }

  function onTestRetry() {
    showingResult.value = false
    showingTest.value = true
    lastTestScore.value = 0
  }

  async function goToPrevious() {
    if (currentLessonIndex.value > 0) {
      currentLessonIndex.value--
      saveProgress()
    }
  }

  async function goToLesson(index: number) {
    if (index >= 0 && index < totalLessons.value && isUnlocked(index)) {
      currentLessonIndex.value = index
      await saveProgress()
    }
  }

  return {
    currentLessonIndex,
    completedLessons,
    passedSections,
    loading,
    totalLessons,
    currentLesson,
    progressPercent,
    isFirstLesson,
    isLastLesson,
    showingTest,
    showingResult,
    lastTestScore,
    currentTestSection,
    isCompleted,
    isUnlocked,
    isLastOfSection,
    getSectionId,
    isSectionPassed,
    getLessonIndexByRoute,
    loadProgress,
    saveProgress,
    completeAndNext,
    goToPrevious,
    goToLesson,
    onTestComplete,
    onTestPass,
    onTestRetry,
  }
})
