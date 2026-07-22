import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import PrimeVue from 'primevue/config'
import Aura from '@primevue/themes/aura'
import 'primeicons/primeicons.css'
import App from './App.vue'
import { useThemeStore } from './stores/theme'
import './style.css'

const pinia = createPinia()

const router = createRouter({
  history: createWebHistory(),
  scrollBehavior() {
    return { top: 0 }
  },
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('./views/LoginView.vue'),
      meta: { guest: true },
    },
    {
      path: '/registro',
      name: 'signup',
      component: () => import('./views/SignupView.vue'),
      meta: { guest: true },
    },
    {
      path: '/',
      name: 'menu',
      component: () => import('./views/MainMenuView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/agente',
      name: 'home',
      component: () => import('./views/HomeView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/curso',
      name: 'course',
      component: () => import('./views/CourseView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/resultados',
      name: 'results',
      component: () => import('./views/ResultsView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/tasas',
      name: 'rates',
      component: () => import('./views/RatesView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: () => import('./views/DashboardView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/finanzas',
      component: () => import('./finanzas/FinanzasLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'fin-dashboard',
          component: () => import('./finanzas/views/Dashboard.vue'),
          meta: { requiresAuth: true, finanzas: true, icon: 'pi pi-home', label: 'Dashboard', shortLabel: 'Inicio' },
        },
        {
          path: 'inversiones',
          name: 'fin-inversiones',
          component: () => import('./finanzas/views/Inversiones.vue'),
          meta: { requiresAuth: true, finanzas: true, icon: 'pi pi-chart-bar', label: 'Inversiones', shortLabel: 'Inv.' },
        },
        {
          path: 'creditos',
          name: 'fin-creditos',
          component: () => import('./finanzas/views/Creditos.vue'),
          meta: { requiresAuth: true, finanzas: true, icon: 'pi pi-credit-card', label: 'Créditos', shortLabel: 'Créd.' },
        },
        {
          path: 'gastos-ingresos',
          name: 'fin-gastos-ingresos',
          component: () => import('./finanzas/views/GastosIngresos.vue'),
          meta: { requiresAuth: true, finanzas: true, icon: 'pi pi-list', label: 'Gastos / Ingresos', shortLabel: 'G/I' },
        },
        {
          path: 'deudas',
          name: 'fin-deudas',
          component: () => import('./finanzas/views/Deudas.vue'),
          meta: { requiresAuth: true, finanzas: true, icon: 'pi pi-money-bill', label: 'Deudas', shortLabel: 'Deudas' },
        },
        {
          path: 'aportaciones',
          name: 'fin-aportaciones',
          component: () => import('./finanzas/views/Aportaciones.vue'),
          meta: { requiresAuth: true, finanzas: true, icon: 'pi pi-calendar', label: 'Aportaciones', shortLabel: 'Aport.' },
        },
      ],
    },
    {
      path: '/configuracion',
      name: 'configuracion',
      component: () => import('./finanzas/views/Configuracion.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/aprende',
      name: 'learn-catalog',
      component: () => import('./views/CourseCatalog.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/aprende/:courseId',
      name: 'learn-course',
      component: () => import('./views/CourseLearnView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/planes',
      name: 'plans',
      component: () => import('./views/PlanesView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/privacidad',
      name: 'privacy',
      component: () => import('./views/PrivacyView.vue'),
    },
    {
      path: '/terminos',
      name: 'terms',
      component: () => import('./views/TermsView.vue'),
    },
    {
      path: '/disclaimer',
      name: 'disclaimer',
      component: () => import('./views/DisclaimerView.vue'),
    },
    {
      path: '/nosotros',
      name: 'about',
      component: () => import('./views/AboutView.vue'),
    },
  ],
})

// Auth guard

router.beforeEach(async (to, _from, next) => {
  const { useAuthStore } = await import('./stores/auth')
  const authStore = useAuthStore()

  // Wait for Firebase to initialize
  if (authStore.loading) {
    await authStore.init()
  }

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else if (to.meta.guest && authStore.isAuthenticated) {
    next('/')
  } else {
    next()
  }
})

const app = createApp(App)
app.use(pinia)
app.use(router)
app.use(PrimeVue, {
  theme: {
    preset: Aura,
    options: {
      // El tema oscuro de PrimeVue solo aplica dentro del dashboard (.dark-mode)
      darkModeSelector: '.dark-mode',
    },
  },
})

// Inicializa el tema (claro/oscuro) antes de montar para evitar parpadeo.
useThemeStore().init()

app.mount('#app')
