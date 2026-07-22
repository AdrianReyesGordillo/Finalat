import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const MainLayout = () => import('../layouts/MainLayout.vue')

const routes: RouteRecordRaw[] = [
  // Public routes
  {
    path: '/login',
    name: 'login',
    component: () => import('../pages/LoginPage.vue'),
    meta: { title: 'Iniciar Sesión', requiresAuth: false },
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('../pages/RegisterPage.vue'),
    meta: { title: 'Registro', requiresAuth: false },
  },

  // Root redirect
  {
    path: '/',
    redirect: '/dashboard',
  },

  // Authenticated routes wrapped in MainLayout
  {
    path: '/',
    component: MainLayout,
    meta: { requiresAuth: true },
    children: [
      {
        path: 'dashboard',
        name: 'dashboard',
        component: () => import('../pages/DashboardPage.vue'),
        meta: { title: 'Dashboard', requiresAuth: true },
      },
      {
        path: 'ahorro',
        name: 'ahorro',
        component: () => import('../pages/AhorroPage.vue'),
        meta: { title: 'Ahorro', requiresAuth: true },
      },
      {
        path: 'creditos',
        name: 'creditos',
        component: () => import('../pages/CreditosPage.vue'),
        meta: { title: 'Créditos', requiresAuth: true },
      },
      {
        path: 'gastos-ingresos',
        name: 'gastos-ingresos',
        component: () => import('../pages/GastosIngresosPage.vue'),
        meta: { title: 'Gastos e Ingresos', requiresAuth: true },
      },
      {
        path: 'deudas',
        name: 'deudas',
        component: () => import('../pages/DeudasPage.vue'),
        meta: { title: 'Deudas', requiresAuth: true },
      },
      {
        path: 'aportaciones',
        name: 'aportaciones',
        component: () => import('../pages/AportacionesPage.vue'),
        meta: { title: 'Aportaciones', requiresAuth: true },
      },
      {
        path: 'afore',
        name: 'afore',
        component: () => import('../pages/AforePage.vue'),
        meta: { title: 'Afore', requiresAuth: true },
      },
      {
        path: 'gbm-portfolio',
        name: 'gbm-portfolio',
        component: () => import('../pages/GbmPortfolioPage.vue'),
        meta: { title: 'Portafolio GBM', requiresAuth: true },
      },
      {
        path: 'patrimonio',
        name: 'patrimonio',
        component: () => import('../pages/PatrimonioPage.vue'),
        meta: { title: 'Patrimonio Neto', requiresAuth: true },
      },
      {
        path: 'asesor',
        name: 'asesor',
        component: () => import('../pages/AsesorPage.vue'),
        meta: { title: 'Asesor Fina', requiresAuth: true },
      },
      {
        path: 'aprendizaje',
        name: 'aprendizaje',
        component: () => import('../pages/AprendizajePage.vue'),
        meta: { title: 'Aprendizaje', requiresAuth: true },
      },
      {
        path: 'aprendizaje/:courseId',
        name: 'aprendizaje-curso',
        component: () => import('../pages/AprendizajeCursePage.vue'),
        meta: { title: 'Curso', requiresAuth: true },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

// Navigation guards
router.beforeEach((to, _from, next) => {
  const authStore = useAuthStore()

  const requiresAuth = to.matched.some((record) => record.meta.requiresAuth)
  const isPublicAuthPage = to.name === 'login' || to.name === 'register'

  // If authenticated user tries to access login/register, redirect to dashboard
  if (isPublicAuthPage && authStore.isAuthenticated) {
    next({ name: 'dashboard' })
    return
  }

  // If route requires auth and user is not authenticated, redirect to login
  if (requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'login' })
    return
  }

  next()
})

// Update document title after each navigation
router.afterEach((to) => {
  const title = to.meta.title as string | undefined
  document.title = title ? `${title} — Finalat` : 'Finalat'
})

export default router
