<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const name = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const loading = ref(false)
const showPassword = ref(false)
const localError = ref('')

async function handleSignup() {
  localError.value = ''
  if (password.value !== confirmPassword.value) {
    localError.value = 'Las contraseñas no coinciden.'
    return
  }
  if (password.value.length < 6) {
    localError.value = 'La contraseña debe tener al menos 6 caracteres.'
    return
  }
  loading.value = true
  try {
    await authStore.signupWithEmail(email.value, password.value, name.value)
    router.push('/')
  } catch {
    // error from store
  } finally {
    loading.value = false
  }
}

async function handleGoogle() {
  loading.value = true
  try {
    await authStore.loginWithGoogle()
    router.push('/')
  } catch { /* */ } finally { loading.value = false }
}



</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-surface-50 px-4 login-force-light">
    <div class="w-full max-w-md">
      <!-- Logo -->
      <div class="text-center mb-8">
        <img src="/logo-full.jpg" alt="Finalat" class="h-12 mx-auto rounded-lg mb-4" />
        <h1 class="text-2xl font-bold text-primary-700">Crea tu cuenta</h1>
        <p class="text-primary-400 mt-1">Empieza a hacer crecer tu dinero hoy</p>
      </div>

      <!-- Card -->
      <div class="bg-white rounded-2xl shadow-sm border border-surface-200 p-6 sm:p-8">
        <!-- Social buttons -->
        <div class="space-y-3 mb-6">
          <button
            @click="handleGoogle"
            :disabled="loading"
            class="w-full flex items-center justify-center gap-3 px-4 py-3 border border-surface-200 rounded-xl hover:bg-surface-50 transition-colors text-primary-700 font-medium disabled:opacity-50"
          >
            <svg class="w-5 h-5" viewBox="0 0 24 24">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
            </svg>
            Registrarse con Google
          </button>
        </div>

        <!-- Divider -->
        <div class="relative my-6">
          <div class="absolute inset-0 flex items-center">
            <div class="w-full border-t border-surface-200"></div>
          </div>
          <div class="relative flex justify-center text-sm">
            <span class="px-3 bg-white text-primary-300">o usa tu correo</span>
          </div>
        </div>

        <!-- Email form -->
        <form @submit.prevent="handleSignup" class="space-y-4">
          <div>
            <label for="name" class="block text-sm font-medium text-primary-600 mb-1">Nombre</label>
            <input
              id="name"
              v-model="name"
              type="text"
              autocomplete="name"
              class="w-full px-4 py-3 border border-surface-200 rounded-xl focus:ring-2 focus:ring-accent-400 focus:border-accent-400 outline-none transition-all text-primary-700 placeholder-primary-300"
              placeholder="Tu nombre"
            />
          </div>

          <div>
            <label for="signup-email" class="block text-sm font-medium text-primary-600 mb-1">Correo electrónico</label>
            <input
              id="signup-email"
              v-model="email"
              type="email"
              autocomplete="email"
              required
              class="w-full px-4 py-3 border border-surface-200 rounded-xl focus:ring-2 focus:ring-accent-400 focus:border-accent-400 outline-none transition-all text-primary-700 placeholder-primary-300"
              placeholder="tu@correo.com"
            />
          </div>

          <div>
            <label for="signup-password" class="block text-sm font-medium text-primary-600 mb-1">Contraseña</label>
            <div class="relative">
              <input
                id="signup-password"
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                autocomplete="new-password"
                required
                class="w-full px-4 py-3 border border-surface-200 rounded-xl focus:ring-2 focus:ring-accent-400 focus:border-accent-400 outline-none transition-all text-primary-700 placeholder-primary-300 pr-12"
                placeholder="Mínimo 6 caracteres"
              />
              <button
                type="button"
                @click="showPassword = !showPassword"
                class="absolute right-3 top-1/2 -translate-y-1/2 text-primary-300 hover:text-primary-500"
              >
                <svg v-if="!showPassword" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                </svg>
                <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"/>
                </svg>
              </button>
            </div>
          </div>

          <div>
            <label for="confirm-password" class="block text-sm font-medium text-primary-600 mb-1">Confirmar contraseña</label>
            <input
              id="confirm-password"
              v-model="confirmPassword"
              type="password"
              autocomplete="new-password"
              required
              class="w-full px-4 py-3 border border-surface-200 rounded-xl focus:ring-2 focus:ring-accent-400 focus:border-accent-400 outline-none transition-all text-primary-700 placeholder-primary-300"
              placeholder="Repite tu contraseña"
            />
          </div>

          <!-- Error message -->
          <div v-if="authStore.error || localError" class="bg-red-50 border border-red-200 rounded-xl px-4 py-3 text-sm text-red-600">
            {{ localError || authStore.error }}
          </div>

          <button
            type="submit"
            :disabled="loading || !email || !password || !confirmPassword"
            class="w-full py-3 bg-accent-500 hover:bg-accent-600 text-primary-800 font-semibold rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span v-if="!loading">Crear cuenta</span>
            <span v-else class="flex items-center justify-center gap-2">
              <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
              </svg>
              Creando cuenta...
            </span>
          </button>
        </form>

        <!-- Login link -->
        <p class="text-center text-sm text-primary-400 mt-6">
          ¿Ya tienes cuenta?
          <RouterLink to="/login" class="text-accent-500 hover:text-accent-600 font-semibold">
            Iniciar sesión
          </RouterLink>
        </p>
      </div>
    </div>
  </div>
</template>
