import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { doc, getDoc, setDoc } from 'firebase/firestore'
import { db } from '@/firebase'
import { useAuthStore } from './auth'

export interface CourseLesson {
  id: string
  title: string
  route: string
}

export const COURSE_LESSONS: CourseLesson[] = [
  { id: 'introduccion', title: 'Introducción a las finanzas', route: '/curso/introduccion' },
  { id: 'renta-fija', title: 'Renta fija', route: '/curso/renta-fija' },
  { id: 'renta-variable', title: 'Renta variable', route: '/curso/renta-variable' },
  { id: 'conceptos', title: 'Conceptos financieros', route: '/curso/conceptos' },
  { id: 'fondo-emergencia', title: 'Fondo de emergencia', route: '/curso/fondo-emergencia' },
  { id: 'diversificacion', title: 'Diversificación', route: '/curso/diversificacion' },
  { id: 'tarjeta-credito', title: '¿Cómo funciona una TDC?', route: '/curso/tarjeta-credito' },
  { id: 'cetes', title: 'CETES', route: '/curso/cetes' },
  { id: 'cuentas-ahorro', title: 'Cuentas de ahorro', route: '/curso/cuentas-ahorro' },
  { id: 'acciones', title: 'Acciones', route: '/curso/acciones' },
  { id: 'trading', title: 'Trading: Introducción', route: '/curso/trading' },
  { id: 'tendencias', title: 'Trading: Tendencias', route: '/curso/tendencias' },
  { id: 'velas', title: 'Trading: Velas japonesas', route: '/curso/velas' },
  { id: 'patrones', title: 'Trading: Patrones', route: '/curso/patrones' },
  { id: 'indicadores', title: 'Trading: Indicadores', route: '/curso/indicadores' },
  { id: 'gestion-riesgo', title: 'Trading: Gestión de riesgo', route: '/curso/gestion-riesgo' },
]

export const useCourseStore = defineStore('course', () => {
  const enrolled = ref(false)
  const currentLessonIndex = ref(0)
  const completedLessons = ref<string[]>([])
  const loading = ref(true)

  const totalLessons = computed(() => COURSE_LESSONS.length)
  const currentLesson = computed(() => COURSE_LESSONS[currentLessonIndex.value])
  const progressPercent = computed(() =>
    Math.round((completedLessons.value.length / totalLessons.value) * 100)
  )
  const isFirstLesson = computed(() => currentLessonIndex.value === 0)
  const isLastLesson = computed(() => currentLessonIndex.value === totalLessons.value - 1)

  async function loadProgress() {
    const authStore = useAuthStore()
    if (!authStore.user) {
      loading.value = false
      return
    }

    try {
      const docRef = doc(db, 'course_progress', authStore.user.uid)
      const docSnap = await getDoc(docRef)

      if (docSnap.exists()) {
        const data = docSnap.data()
        enrolled.value = data.enrolled || false
        currentLessonIndex.value = data.currentLessonIndex || 0
        completedLessons.value = data.completedLessons || []
      }
    } catch (err) {
      console.warn('Error loading course progress:', err)
      const local = localStorage.getItem('course_progress')
      if (local) {
        const data = JSON.parse(local)
        enrolled.value = data.enrolled || false
        currentLessonIndex.value = data.currentLessonIndex || 0
        completedLessons.value = data.completedLessons || []
      }
    } finally {
      loading.value = false
    }
  }

  async function saveProgress() {
    const authStore = useAuthStore()
    const data = {
      enrolled: enrolled.value,
      currentLessonIndex: currentLessonIndex.value,
      completedLessons: completedLessons.value,
      updatedAt: new Date().toISOString(),
    }

    localStorage.setItem('course_progress', JSON.stringify(data))

    if (!authStore.user) return

    try {
      const docRef = doc(db, 'course_progress', authStore.user.uid)
      await setDoc(docRef, data, { merge: true })
    } catch (err) {
      console.warn('Error saving course progress:', err)
    }
  }

  async function enroll() {
    enrolled.value = true
    currentLessonIndex.value = 0
    completedLessons.value = []
    await saveProgress()
  }

  async function completeCurrentAndNext() {
    const lesson = COURSE_LESSONS[currentLessonIndex.value]
    if (lesson && !completedLessons.value.includes(lesson.id)) {
      completedLessons.value.push(lesson.id)
    }

    if (currentLessonIndex.value < totalLessons.value - 1) {
      currentLessonIndex.value++
    }

    await saveProgress()
  }

  async function goToPrevious() {
    if (currentLessonIndex.value > 0) {
      currentLessonIndex.value--
      await saveProgress()
    }
  }

  async function goToLesson(index: number) {
    if (index >= 0 && index < totalLessons.value) {
      currentLessonIndex.value = index
      await saveProgress()
    }
  }

  return {
    enrolled,
    currentLessonIndex,
    completedLessons,
    loading,
    totalLessons,
    currentLesson,
    progressPercent,
    isFirstLesson,
    isLastLesson,
    loadProgress,
    saveProgress,
    enroll,
    completeCurrentAndNext,
    goToPrevious,
    goToLesson,
  }
})
