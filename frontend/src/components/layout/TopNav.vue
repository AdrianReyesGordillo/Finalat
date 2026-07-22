<script setup lang="ts">
import { computed } from 'vue'
import { useAuthStore } from '../../stores/auth'

const props = defineProps<{
  sidebarOpen?: boolean
}>()

const emit = defineEmits<{
  (e: 'toggle-sidebar'): void
  (e: 'logout'): void
}>()

const authStore = useAuthStore()

const displayName = computed(() => {
  if (authStore.user?.displayName) return authStore.user.displayName
  if (authStore.user?.email) return authStore.user.email
  return 'Usuario'
})

function handleLogout() {
  emit('logout')
}

function toggleSidebar() {
  emit('toggle-sidebar')
}
</script>

<template>
  <header
    class="fixed top-0 left-0 right-0 z-50 h-16 flex items-center justify-between px-4 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 shadow-sm"
    role="banner"
  >
    <!-- Left: Hamburger (mobile) + Logo -->
    <div class="flex items-center gap-3">
      <button
        class="md:hidden p-2 rounded-lg text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        aria-label="Abrir menú de navegación"
        @click="toggleSidebar"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          class="h-6 w-6"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          aria-hidden="true"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M4 6h16M4 12h16M4 18h16"
          />
        </svg>
      </button>

      <a
        href="/"
        class="flex items-center gap-2 text-xl font-bold text-indigo-600 dark:text-indigo-400"
        aria-label="Ir al inicio - Finalat"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          class="h-7 w-7"
          viewBox="0 0 24 24"
          fill="currentColor"
          aria-hidden="true"
        >
          <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
        </svg>
        <span>Finalat</span>
      </a>
    </div>

    <!-- Right: User info + Dark mode slot + Logout -->
    <div class="flex items-center gap-3">
      <!-- Dark mode toggle slot -->
      <slot name="dark-mode-toggle" />

      <!-- User display name -->
      <span
        class="hidden sm:inline-block text-sm text-gray-700 dark:text-gray-300 max-w-[150px] truncate"
        :title="displayName"
      >
        {{ displayName }}
      </span>

      <!-- Logout button -->
      <button
        class="px-3 py-1.5 text-sm rounded-lg text-gray-600 dark:text-gray-300 hover:bg-red-50 dark:hover:bg-red-900/20 hover:text-red-600 dark:hover:text-red-400 focus:outline-none focus:ring-2 focus:ring-red-500 transition-colors"
        aria-label="Cerrar sesión"
        @click="handleLogout"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          class="h-5 w-5 inline-block mr-1"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          aria-hidden="true"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a2 2 0 01-2 2H6a2 2 0 01-2-2V7a2 2 0 012-2h5a2 2 0 012 2v1"
          />
        </svg>
        <span class="hidden sm:inline">Salir</span>
      </button>
    </div>
  </header>
</template>
