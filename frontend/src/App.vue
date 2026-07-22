<script setup lang="ts">
import { RouterView, useRoute } from 'vue-router'
import { computed } from 'vue'
import NavBar from './components/NavBar.vue'
import { useAuthStore } from './stores/auth'

const route = useRoute()
const authStore = useAuthStore()

const isAuthPage = computed(() => 
  route.path === '/login' || route.path === '/registro'
)

// El dashboard financiero conserva el NavBar superior de Finalat, pero
// se muestra a pantalla completa (sin footer) con su propia barra lateral.
const isFinanzas = computed(() => route.path.startsWith('/finanzas'))

const showFooter = computed(() => 
  !isAuthPage.value && !isFinanzas.value && route.path !== '/agente' && route.path !== '/configuracion'
)
</script>

<template>
  <div class="min-h-screen flex flex-col bg-surface-50">
    <NavBar v-if="!isAuthPage" />
    <!-- Loading state while Firebase initializes auth -->
    <template v-if="authStore.loading && !isAuthPage">
      <main class="flex-1 flex items-center justify-center pt-16">
        <div class="flex flex-col items-center gap-3">
          <svg class="animate-spin h-8 w-8 text-primary-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
          </svg>
          <span class="text-sm text-gray-500">Cargando...</span>
        </div>
      </main>
    </template>
    <template v-else>
      <main :class="['flex-1', isFinanzas ? 'overflow-auto' : 'overflow-hidden', { 'pt-16': !isAuthPage }]">
        <RouterView />
      </main>
      <footer v-if="showFooter" class="relative z-20 bg-[#1a2540] dark:bg-[#15202b] text-white/70 py-12">
      <div class="max-w-6xl mx-auto px-4">
        <!-- Top section: Logo + columns -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-8 pb-8 border-b border-white/10">
          <!-- Logo & description -->
          <div class="lg:col-span-1">
            <RouterLink to="/" class="flex items-center gap-2 mb-3">
              <img src="/logo-icon.jpg" alt="" class="h-9 object-contain" />
              <img src="/logo-full.jpg" alt="Finalat" class="h-8 object-contain rounded-md" />
            </RouterLink>
            <p class="text-xs text-white/50 leading-relaxed">
              Educación financiera clara y herramientas inteligentes para invertir mejor en México.
            </p>
          </div>

          <!-- Explora -->
          <div>
            <h4 class="text-sm font-semibold text-white mb-3">Explora</h4>
            <ul class="space-y-2 text-sm">
              <li><RouterLink to="/aprende" class="hover:text-white transition-colors">Aprende</RouterLink></li>
              <li><RouterLink to="/tasas" class="hover:text-white transition-colors">Tasas</RouterLink></li>
              <li><RouterLink to="/agente" class="hover:text-white transition-colors">Agente</RouterLink></li>
            </ul>
          </div>

          <!-- Recursos -->
          <div>
            <h4 class="text-sm font-semibold text-white mb-3">Recursos</h4>
            <ul class="space-y-2 text-sm">
              <li><RouterLink to="/aprende" class="hover:text-white transition-colors">Guías</RouterLink></li>
              <li><RouterLink to="/tasas" class="hover:text-white transition-colors">Comparador de tasas</RouterLink></li>
            </ul>
          </div>

          <!-- Empresa -->
          <div>
            <h4 class="text-sm font-semibold text-white mb-3">Empresa</h4>
            <ul class="space-y-2 text-sm">
              <li><RouterLink to="/nosotros" class="hover:text-white transition-colors">Acerca de Finalat</RouterLink></li>
              <li><RouterLink to="/terminos" class="hover:text-white transition-colors">Términos y condiciones</RouterLink></li>
              <li><RouterLink to="/privacidad" class="hover:text-white transition-colors">Aviso de privacidad</RouterLink></li>
              <li><RouterLink to="/disclaimer" class="hover:text-white transition-colors">Disclaimer Financiero</RouterLink></li>
            </ul>
          </div>
        </div>

        <!-- Bottom -->
        <p class="text-xs text-white/40 text-center mt-6">
          &copy; {{ new Date().getFullYear() }} Finalat. Todos los derechos reservados.
        </p>
      </div>
    </footer>
    </template>
  </div>
</template>
