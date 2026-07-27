<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

defineProps<{
  open: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

const route = useRoute()
const authStore = useAuthStore()
const isAdmin = computed(() => authStore.userEmail === 'adriax45@gmail.com')

interface NavItem {
  label: string
  to: string
  icon: string
  adminOnly?: boolean
}

const navItems: NavItem[] = [
  { label: 'Dashboard', to: '/dashboard', icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6' },
  { label: 'Ahorro', to: '/ahorro', icon: 'M17 9V7a5 5 0 00-10 0v2M5 12h14l1 9H4l1-9z' },
  { label: 'Créditos', to: '/creditos', icon: 'M3 10h18M7 15h1m4 0h1m-7 4h12a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z' },
  { label: 'Gastos/Ingresos', to: '/gastos-ingresos', icon: 'M9 14l6-6m-5.5.5h.01m4.99 5h.01M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16l3.5-2 3.5 2 3.5-2 3.5 2z' },
  { label: 'Deudas', to: '/deudas', icon: 'M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z', adminOnly: true },
  { label: 'Aportaciones', to: '/aportaciones', icon: 'M12 4v16m8-8H4' },
  { label: 'Afore', to: '/afore', icon: 'M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4' },
  { label: 'GBM', to: '/gbm-portfolio', icon: 'M13 7h8m0 0v8m0-8l-8 8-4-4-6 6' },
  { label: 'Patrimonio', to: '/patrimonio', icon: 'M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3' },
  { label: 'Asesor Fina', to: '/asesor', icon: 'M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-4l-4 4z' },
  { label: 'Aprendizaje', to: '/aprendizaje', icon: 'M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253' },
]

const filteredNavItems = computed(() => navItems.filter(item => !item.adminOnly || isAdmin.value))

const currentPath = computed(() => route.path)

function isActive(to: string): boolean {
  return currentPath.value === to || currentPath.value.startsWith(to + '/')
}

function closeSidebar() {
  emit('close')
}
</script>

<template>
  <!-- Mobile overlay -->
  <div
    v-if="open"
    class="fixed inset-0 z-40 bg-black/50 md:hidden"
    aria-hidden="true"
    @click="closeSidebar"
  />

  <!-- Sidebar -->
  <aside
    :class="[
      'fixed top-16 left-0 z-40 h-[calc(100vh-4rem)] w-64 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700 overflow-y-auto transition-transform duration-300 ease-in-out',
      open ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
    ]"
    role="navigation"
    aria-label="Navegación principal"
  >
    <nav class="p-4 space-y-1">
      <router-link
        v-for="item in filteredNavItems"
        :key="item.to"
        :to="item.to"
        :class="[
          'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500',
          isActive(item.to)
            ? 'bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300'
            : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-gray-100'
        ]"
        :aria-current="isActive(item.to) ? 'page' : undefined"
        @click="closeSidebar"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          class="h-5 w-5 shrink-0"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          aria-hidden="true"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            :d="item.icon"
          />
        </svg>
        <span>{{ item.label }}</span>
      </router-link>
    </nav>
  </aside>
</template>
