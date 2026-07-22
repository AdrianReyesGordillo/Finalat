<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth'

const router = useRouter()
const { register, loginWithGoogle, loading, error } = useAuth()

const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const emailError = ref<string | null>(null)
const passwordError = ref<string | null>(null)
const confirmPasswordError = ref<string | null>(null)
const submitted = ref(false)

function validateEmail(): boolean {
  if (!email.value.trim()) {
    emailError.value = 'El correo electrónico es obligatorio.'
    return false
  }
  const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailPattern.test(email.value.trim())) {
    emailError.value = 'El formato del correo electrónico no es válido.'
    return false
  }
  emailError.value = null
  return true
}

function validatePassword(): boolean {
  if (!password.value) {
    passwordError.value = 'La contraseña es obligatoria.'
    return false
  }
  if (password.value.length < 8) {
    passwordError.value = 'La contraseña debe tener al menos 8 caracteres.'
    return false
  }
  passwordError.value = null
  return true
}

function validateConfirmPassword(): boolean {
  if (!confirmPassword.value) {
    confirmPasswordError.value = 'Debes confirmar tu contraseña.'
    return false
  }
  if (confirmPassword.value !== password.value) {
    confirmPasswordError.value = 'Las contraseñas no coinciden.'
    return false
  }
  confirmPasswordError.value = null
  return true
}

function validateForm(): boolean {
  const isEmailValid = validateEmail()
  const isPasswordValid = validatePassword()
  const isConfirmValid = validateConfirmPassword()
  return isEmailValid && isPasswordValid && isConfirmValid
}

async function handleSubmit() {
  submitted.value = true
  if (!validateForm()) return

  const success = await register(email.value.trim(), password.value)
  if (success) {
    router.push('/dashboard')
  }
}

async function handleGoogleLogin() {
  const success = await loginWithGoogle()
  if (success) {
    router.push('/dashboard')
  }
}
</script>

<template>
  <main
    class="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 px-4 py-12"
  >
    <div
      class="w-full max-w-md bg-white dark:bg-gray-800 rounded-lg shadow-md p-8"
    >
      <h1
        class="text-2xl font-bold text-center text-gray-900 dark:text-white mb-6"
      >
        Crear Cuenta
      </h1>

      <form
        @submit.prevent="handleSubmit"
        novalidate
        aria-label="Formulario de registro"
      >
        <!-- Email field -->
        <div class="mb-4">
          <label
            for="register-email"
            class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
          >
            Correo electrónico
          </label>
          <input
            id="register-email"
            v-model="email"
            type="email"
            autocomplete="email"
            required
            :aria-invalid="submitted && !!emailError"
            :aria-describedby="emailError ? 'register-email-error' : undefined"
            class="w-full px-3 py-2 border rounded-md text-gray-900 dark:text-white bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            @blur="validateEmail"
          />
          <p
            v-if="submitted && emailError"
            id="register-email-error"
            role="alert"
            class="mt-1 text-sm text-red-600 dark:text-red-400"
          >
            {{ emailError }}
          </p>
        </div>

        <!-- Password field -->
        <div class="mb-4">
          <label
            for="register-password"
            class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
          >
            Contraseña
          </label>
          <input
            id="register-password"
            v-model="password"
            type="password"
            autocomplete="new-password"
            required
            :aria-invalid="submitted && !!passwordError"
            :aria-describedby="passwordError ? 'register-password-error' : undefined"
            class="w-full px-3 py-2 border rounded-md text-gray-900 dark:text-white bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            @blur="validatePassword"
          />
          <p
            v-if="submitted && passwordError"
            id="register-password-error"
            role="alert"
            class="mt-1 text-sm text-red-600 dark:text-red-400"
          >
            {{ passwordError }}
          </p>
        </div>

        <!-- Confirm Password field -->
        <div class="mb-6">
          <label
            for="register-confirm-password"
            class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
          >
            Confirmar contraseña
          </label>
          <input
            id="register-confirm-password"
            v-model="confirmPassword"
            type="password"
            autocomplete="new-password"
            required
            :aria-invalid="submitted && !!confirmPasswordError"
            :aria-describedby="confirmPasswordError ? 'register-confirm-error' : undefined"
            class="w-full px-3 py-2 border rounded-md text-gray-900 dark:text-white bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            @blur="validateConfirmPassword"
          />
          <p
            v-if="submitted && confirmPasswordError"
            id="register-confirm-error"
            role="alert"
            class="mt-1 text-sm text-red-600 dark:text-red-400"
          >
            {{ confirmPasswordError }}
          </p>
        </div>

        <!-- Auth error from store -->
        <div
          v-if="error"
          role="alert"
          aria-live="assertive"
          class="mb-4 p-3 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-md"
        >
          <p class="text-sm text-red-700 dark:text-red-300">{{ error }}</p>
        </div>

        <!-- Submit button -->
        <button
          type="submit"
          :disabled="loading"
          class="w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:focus:ring-offset-gray-800 transition-colors flex items-center justify-center"
        >
          <svg
            v-if="loading"
            class="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <circle
              class="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              stroke-width="4"
            />
            <path
              class="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
          {{ loading ? 'Registrando...' : 'Crear Cuenta' }}
        </button>
      </form>

      <!-- Divider -->
      <div class="relative my-6">
        <div class="absolute inset-0 flex items-center">
          <div class="w-full border-t border-gray-300 dark:border-gray-600"></div>
        </div>
        <div class="relative flex justify-center text-sm">
          <span class="px-2 bg-white dark:bg-gray-800 text-gray-500 dark:text-gray-400">
            o continúa con
          </span>
        </div>
      </div>

      <!-- Google sign-in button -->
      <button
        type="button"
        :disabled="loading"
        class="w-full py-2 px-4 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50 text-gray-700 dark:text-gray-200 font-medium focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:focus:ring-offset-gray-800 transition-colors flex items-center justify-center gap-2"
        @click="handleGoogleLogin"
      >
        <svg class="h-5 w-5" viewBox="0 0 24 24" aria-hidden="true">
          <path
            d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
            fill="#4285F4"
          />
          <path
            d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
            fill="#34A853"
          />
          <path
            d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
            fill="#FBBC05"
          />
          <path
            d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
            fill="#EA4335"
          />
        </svg>
        Registrarse con Google
      </button>

      <!-- Link to login -->
      <p class="mt-6 text-center text-sm text-gray-600 dark:text-gray-400">
        ¿Ya tienes cuenta?
        <router-link
          to="/login"
          class="font-medium text-blue-600 dark:text-blue-400 hover:text-blue-500 dark:hover:text-blue-300 focus:outline-none focus:underline"
        >
          Inicia sesión
        </router-link>
      </p>
    </div>
  </main>
</template>
