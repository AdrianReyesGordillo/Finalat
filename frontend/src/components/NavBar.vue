<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { RouterLink, useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useCourseStore } from '@/stores/course'
import { useThemeStore } from '@/stores/theme'

const userMenuOpen = ref(false)
const authStore = useAuthStore()
const courseStore = useCourseStore()
const themeStore = useThemeStore()
const router = useRouter()
const route = useRoute()

const navItems = computed(() => {
  return [
    { label: 'Home', path: '/', icon: 'home' },
    { label: 'Agente', path: '/agente', icon: 'agent' },
    { label: 'Cursos', path: '/aprende', icon: 'courses' },
    { label: 'Dashboard', path: '/finanzas', icon: 'dashboard' },
  ]
})

function isActive(path: string): boolean {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}

onMounted(async () => {
  if (authStore.isAuthenticated && courseStore.loading) {
    await courseStore.loadProgress()
  }
})

async function handleLogout() {
  await authStore.logout()
  userMenuOpen.value = false
  router.push('/login')
}

function handleClickOutside(e: MouseEvent) {
  const target = e.target as HTMLElement
  if (!target.closest('.user-menu-container')) {
    userMenuOpen.value = false
  }
}

onMounted(() => document.addEventListener('click', handleClickOutside))
onBeforeUnmount(() => document.removeEventListener('click', handleClickOutside))
</script>

<template>
  <nav class="bg-white border-b border-gray-200 fixed top-0 left-0 right-0 z-50">
    <div class="max-w-6xl mx-auto px-4">
      <div class="flex justify-between items-center h-16">
        <!-- Logo -->
        <RouterLink to="/" class="hidden sm:inline-flex items-center gap-2 bg-[#ffffff] rounded-lg px-3 py-1">
          <img src="/logo-icon.jpg" alt="" class="h-9 object-contain" />
          <img src="/logo-full.jpg" alt="Finalat" class="h-10 object-contain hidden md:block" />
        </RouterLink>

        <!-- Navigation links -->
        <div v-if="authStore.isAuthenticated" class="nav-links">
          <RouterLink
            v-for="item in navItems"
            :key="item.path"
            :to="item.path"
            class="nav-link"
            :class="{ active: isActive(item.path) }"
          >
            <svg v-if="item.icon === 'home'" class="nav-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>
            </svg>
            <svg v-else-if="item.icon === 'courses'" class="nav-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
            </svg>
            <svg v-else-if="item.icon === 'agent'" class="nav-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"/>
            </svg>
            <svg v-else-if="item.icon === 'dashboard'" class="nav-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M4 5a1 1 0 011-1h4a1 1 0 011 1v5a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM14 5a1 1 0 011-1h4a1 1 0 011 1v2a1 1 0 01-1 1h-4a1 1 0 01-1-1V5zM4 15a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1v-4zM14 12a1 1 0 011-1h4a1 1 0 011 1v7a1 1 0 01-1 1h-4a1 1 0 01-1-1v-7z"/>
            </svg>
            <span class="nav-label">{{ item.label }}</span>
          </RouterLink>
        </div>

        <!-- User menu -->
        <div class="flex items-center gap-1">
          <div v-if="authStore.isAuthenticated" class="user-menu-container relative">
            <button
              @click="userMenuOpen = !userMenuOpen"
              class="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-gray-100 transition-all"
              aria-label="Menú de usuario"
            >
              <div v-if="authStore.userPhoto" class="w-8 h-8 rounded-full overflow-hidden border border-gray-200">
                <img :src="authStore.userPhoto" alt="" class="w-full h-full object-cover" />
              </div>
              <div v-else class="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center">
                <svg class="w-4.5 h-4.5 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
                </svg>
              </div>
              <span class="hidden sm:block text-sm text-primary-700 font-medium max-w-[120px] truncate">
                {{ authStore.displayName }}
              </span>
              <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
              </svg>
            </button>

            <!-- Dropdown -->
            <div v-if="userMenuOpen" class="user-dropdown absolute right-0 mt-2 w-48 bg-white rounded-xl shadow-lg border border-surface-200 py-2 z-50">
              <p class="dropdown-email px-4 py-2 text-xs text-primary-400 truncate">{{ authStore.userEmail }}</p>
              <hr class="dropdown-divider border-surface-200" />
              <RouterLink
                to="/configuracion"
                class="dropdown-item flex items-center gap-2 w-full text-left px-4 py-2 text-sm text-primary-700 hover:bg-gray-100 transition-colors"
                @click="userMenuOpen = false"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                </svg>
                Configuración
              </RouterLink>
              <button
                @click="themeStore.toggle()"
                class="dropdown-item flex items-center gap-2 w-full text-left px-4 py-2 text-sm text-primary-700 hover:bg-gray-100 transition-colors"
              >
                <svg v-if="themeStore.mode === 'dark'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <circle cx="12" cy="12" r="4" stroke-width="2" />
                  <path stroke-linecap="round" stroke-width="2" d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" />
                </svg>
                <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z" />
                </svg>
                {{ themeStore.mode === 'dark' ? 'Modo claro' : 'Modo oscuro' }}
              </button>
              <hr class="dropdown-divider border-surface-200" />
              <button
                @click="handleLogout"
                class="dropdown-item dropdown-logout flex items-center gap-2 w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>
                </svg>
                Cerrar sesión
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </nav>
</template>

<style scoped>
.nav-links {
  display: flex;
  align-items: center;
  gap: 4px;
  height: 100%;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  font-size: 14px;
  font-weight: 500;
  color: #8899a6;
  text-decoration: none;
  position: relative;
  transition: color 0.2s ease, background-color 0.2s ease;
  border-radius: 8px;
}

.nav-link:hover {
  color: #1a2733;
  background-color: #f9fafb;
}

.nav-link.active {
  color: #1a2733;
}

.nav-link.active::after {
  content: '';
  position: absolute;
  bottom: -12px;
  left: 12px;
  right: 12px;
  height: 2.5px;
  background-color: #1a2733;
  border-radius: 2px;
}

.nav-icon {
  width: 27px;
  height: 27px;
  flex-shrink: 0;
}

.nav-label {
  white-space: nowrap;
}

@media (max-width: 768px) {
  .nav-links {
    gap: 8px;
    flex: 1;
    justify-content: center;
  }
  .nav-link {
    padding: 8px 12px;
    gap: 4px;
  }
  .nav-label {
    display: none;
  }
  .nav-link.active::after {
    left: 8px;
    right: 8px;
  }
}
</style>
