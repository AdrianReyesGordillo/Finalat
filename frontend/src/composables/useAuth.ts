import { computed, onMounted, onUnmounted } from 'vue'
import {
  signInWithEmailAndPassword,
  signInWithPopup,
  GoogleAuthProvider,
  createUserWithEmailAndPassword,
  signOut,
  onAuthStateChanged,
  type User,
  type Unsubscribe,
} from 'firebase/auth'
import { auth } from '../config/firebase'
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'

/**
 * Maps Firebase auth error codes to user-friendly messages in Spanish.
 */
function getAuthErrorMessage(errorCode: string): string {
  const messages: Record<string, string> = {
    'auth/invalid-email': 'El correo electrónico no es válido.',
    'auth/user-disabled': 'Esta cuenta ha sido deshabilitada.',
    'auth/user-not-found': 'Las credenciales son incorrectas.',
    'auth/wrong-password': 'Las credenciales son incorrectas.',
    'auth/invalid-credential': 'Las credenciales son incorrectas.',
    'auth/email-already-in-use': 'Este correo electrónico ya está registrado.',
    'auth/weak-password': 'La contraseña debe tener al menos 8 caracteres.',
    'auth/operation-not-allowed': 'Esta operación no está permitida.',
    'auth/too-many-requests': 'Demasiados intentos. Tu cuenta está temporalmente bloqueada. Intenta más tarde.',
    'auth/network-request-failed': 'Error de conexión. Verifica tu conexión a internet.',
    'auth/popup-closed-by-user': 'Se cerró la ventana de autenticación.',
    'auth/cancelled-popup-request': 'Se canceló la solicitud de autenticación.',
  }

  return messages[errorCode] || 'Ocurrió un error inesperado. Intenta de nuevo.'
}

/**
 * Refreshes and returns the current user's Firebase ID token.
 * Forces a refresh to ensure the token is not expired.
 */
export async function getIdToken(): Promise<string | null> {
  const currentUser = auth.currentUser
  if (!currentUser) return null

  try {
    const token = await currentUser.getIdToken(true)
    return token
  } catch {
    return null
  }
}

/**
 * Composable for Firebase Authentication.
 * Provides login, register, logout, and reactive auth state.
 */
export function useAuth() {
  const store = useAuthStore()
  const router = useRouter()

  let unsubscribe: Unsubscribe | null = null

  const currentUser = computed(() => store.user)
  const isAuthenticated = computed(() => store.isAuthenticated)
  const loading = computed(() => store.loading)
  const error = computed(() => store.error)

  /**
   * Authenticates a user with email and password.
   */
  async function login(email: string, password: string): Promise<boolean> {
    store.setError(null)
    store.setLoading(true)

    try {
      const credential = await signInWithEmailAndPassword(auth, email, password)
      const token = await credential.user.getIdToken()
      store.setUser(credential.user)
      store.setToken(token)
      store.setLoading(false)
      return true
    } catch (err: unknown) {
      const firebaseError = err as { code?: string }
      const message = getAuthErrorMessage(firebaseError.code || '')
      store.setError(message)
      store.setLoading(false)
      return false
    }
  }

  /**
   * Authenticates a user with Google popup.
   */
  async function loginWithGoogle(): Promise<boolean> {
    store.setError(null)
    store.setLoading(true)

    try {
      const provider = new GoogleAuthProvider()
      const credential = await signInWithPopup(auth, provider)
      const token = await credential.user.getIdToken()
      store.setUser(credential.user)
      store.setToken(token)
      store.setLoading(false)
      return true
    } catch (err: unknown) {
      const firebaseError = err as { code?: string }
      const message = getAuthErrorMessage(firebaseError.code || '')
      store.setError(message)
      store.setLoading(false)
      return false
    }
  }

  /**
   * Registers a new user with email and password.
   */
  async function register(email: string, password: string): Promise<boolean> {
    store.setError(null)
    store.setLoading(true)

    try {
      const credential = await createUserWithEmailAndPassword(auth, email, password)
      const token = await credential.user.getIdToken()
      store.setUser(credential.user)
      store.setToken(token)
      store.setLoading(false)
      return true
    } catch (err: unknown) {
      const firebaseError = err as { code?: string }
      const message = getAuthErrorMessage(firebaseError.code || '')
      store.setError(message)
      store.setLoading(false)
      return false
    }
  }

  /**
   * Signs out the current user, clears auth state, and redirects to /login.
   */
  async function logout(): Promise<void> {
    try {
      await signOut(auth)
      store.clearAuth()
      router.push('/login')
    } catch {
      store.clearAuth()
      router.push('/login')
    }
  }

  /**
   * Initializes the onAuthStateChanged listener.
   * Updates the store automatically when auth state changes and refreshes the token.
   */
  function initAuthListener(): void {
    unsubscribe = onAuthStateChanged(auth, async (firebaseUser: User | null) => {
      if (firebaseUser) {
        const token = await firebaseUser.getIdToken()
        store.setUser(firebaseUser)
        store.setToken(token)
      } else {
        store.clearAuth()
      }
      store.setLoading(false)
    })
  }

  /**
   * Cleans up the auth state listener.
   */
  function destroyAuthListener(): void {
    if (unsubscribe) {
      unsubscribe()
      unsubscribe = null
    }
  }

  onMounted(() => {
    initAuthListener()
  })

  onUnmounted(() => {
    destroyAuthListener()
  })

  return {
    currentUser,
    isAuthenticated,
    loading,
    error,
    login,
    loginWithGoogle,
    register,
    logout,
    initAuthListener,
    destroyAuthListener,
  }
}
