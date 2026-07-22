import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signInWithPopup,
  signOut,
  onAuthStateChanged,
  updateProfile,
  type User,
} from 'firebase/auth'
import { auth, googleProvider } from '@/firebase'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const loading = ref(true)
  const error = ref('')

  const isAuthenticated = computed(() => !!user.value)
  const displayName = computed(() => user.value?.displayName || user.value?.email?.split('@')[0] || '')
  const userEmail = computed(() => user.value?.email || '')
  const userPhoto = computed(() => user.value?.photoURL || '')

  // Listen to auth state changes
  function init() {
    return new Promise<void>((resolve) => {
      onAuthStateChanged(auth, async (firebaseUser) => {
        user.value = firebaseUser
        loading.value = false
        resolve()

        if (firebaseUser) {
          // Load subscription info eagerly
          try {
            const token = await firebaseUser.getIdToken()
            const apiUrl = import.meta.env.VITE_API_URL || ''
            const subRes = await fetch(`${apiUrl}/api/subscription`, {
              headers: { Authorization: `Bearer ${token}` },
            })
            if (subRes.ok) {
              const subData = await subRes.json()
              ;(window as any).__kiro_subscription = subData
            }
          } catch {
            // Non-critical
          }
        }
      })
    })
  }

  async function loginWithEmail(email: string, password: string) {
    error.value = ''
    try {
      const result = await signInWithEmailAndPassword(auth, email, password)
      user.value = result.user
    } catch (err: any) {
      error.value = mapFirebaseError(err.code)
      throw err
    }
  }

  async function signupWithEmail(email: string, password: string, name: string) {
    error.value = ''
    try {
      const result = await createUserWithEmailAndPassword(auth, email, password)
      if (name) {
        await updateProfile(result.user, { displayName: name })
      }
      user.value = result.user
    } catch (err: any) {
      error.value = mapFirebaseError(err.code)
      throw err
    }
  }

  async function loginWithGoogle() {
    error.value = ''
    try {
      const result = await signInWithPopup(auth, googleProvider)
      user.value = result.user
    } catch (err: any) {
      error.value = mapFirebaseError(err.code)
      throw err
    }
  }

  async function logout() {
    await signOut(auth)
    user.value = null
  }

  async function getIdToken(): Promise<string | null> {
    if (!user.value) return null
    return user.value.getIdToken()
  }

  function mapFirebaseError(code: string): string {
    const errors: Record<string, string> = {
      'auth/user-not-found': 'No existe una cuenta con este correo.',
      'auth/wrong-password': 'Contraseña incorrecta.',
      'auth/invalid-credential': 'Credenciales inválidas. Verifica tu correo y contraseña.',
      'auth/email-already-in-use': 'Ya existe una cuenta con este correo.',
      'auth/weak-password': 'La contraseña debe tener al menos 6 caracteres.',
      'auth/invalid-email': 'El correo electrónico no es válido.',
      'auth/too-many-requests': 'Demasiados intentos. Intenta más tarde.',
      'auth/popup-closed-by-user': 'Se cerró la ventana de inicio de sesión.',
      'auth/account-exists-with-different-credential': 'Ya existe una cuenta con este correo usando otro método de inicio de sesión.',
    }
    return errors[code] || 'Ocurrió un error. Intenta de nuevo.'
  }

  return {
    user,
    loading,
    error,
    isAuthenticated,
    displayName,
    userEmail,
    userPhoto,
    init,
    loginWithEmail,
    signupWithEmail,
    loginWithGoogle,
    logout,
    getIdToken,
  }
})
