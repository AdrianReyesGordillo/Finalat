<template>
  <!-- Desktop Sidebar -->
  <nav
    class="sidebar desktop-sidebar"
    :class="{ expanded: isExpanded }"
    @mouseenter="isExpanded = true"
    @mouseleave="isExpanded = false"
  >
    <ul class="sidebar-menu">
      <li v-for="route in routes" :key="route.path">
        <router-link
          :to="route.path"
          custom
          v-slot="{ href, navigate, isActive, isExactActive }"
        >
          <a
            :href="href"
            class="sidebar-link"
            :class="{ active: route.path === '/finanzas' ? isExactActive : isActive }"
            @click="navigate"
          >
            <i :class="route.meta.icon"></i>
            <span v-if="isExpanded" class="link-label">{{ route.meta.label }}</span>
          </a>
        </router-link>
      </li>
    </ul>
  </nav>

  <!-- Mobile Bottom Nav -->
  <nav class="mobile-nav">
    <router-link
      v-for="route in mobileRoutes"
      :key="route.path"
      :to="route.path"
      custom
      v-slot="{ href, navigate, isActive, isExactActive }"
    >
      <a
        :href="href"
        class="mobile-nav-item"
        :class="{ active: route.path === '/finanzas' ? isExactActive : isActive }"
        @click="navigate"
      >
        <i :class="route.meta.icon"></i>
        <span>{{ route.meta.shortLabel || route.meta.label }}</span>
      </a>
    </router-link>
  </nav>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { usePreferencesStore } from '../stores/preferences'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const isExpanded = ref(false)
const authStore = useAuthStore()
const isAdmin = computed(() => authStore.userEmail === 'adriax45@gmail.com')
const ADMIN_ONLY_ROUTES = ['fin-deudas']
const prefsStore = usePreferencesStore()

// Load preferences if not loaded yet
if (!prefsStore.loaded) {
  prefsStore.load()
}

// Orden explícito del menú (Dashboard siempre primero).
const ORDER = [
  'fin-dashboard',
  'fin-inversiones',
  'fin-creditos',
  'fin-gastos-ingresos',
  'fin-deudas',
  'fin-aportaciones',
]

// Map route names to panel keys
const ROUTE_PANEL_MAP = {
  'fin-deudas': 'deudas',
  'fin-creditos': 'creditos',
  'fin-inversiones': 'inversiones',
  'fin-gastos-ingresos': 'gastos_ingresos',
  'fin-aportaciones': 'aportaciones',
}

// Solo mostramos las rutas del dashboard financiero (meta.finanzas), ordenadas y filtradas por preferencias.
const allRoutes = router
  .getRoutes()
  .filter(r => r.meta && r.meta.finanzas && r.meta.label)
  .sort((a, b) => ORDER.indexOf(a.name) - ORDER.indexOf(b.name))

const routes = computed(() =>
  allRoutes.filter(r => {
    // Admin-only routes
    if (ADMIN_ONLY_ROUTES.includes(r.name) && !isAdmin.value) return false
    const panelKey = ROUTE_PANEL_MAP[r.name]
    if (!panelKey) return true // Always show dashboard
    return prefsStore.isPanelEnabled(panelKey)
  })
)

const mobileRoutes = routes // Show same filtered routes in mobile nav
</script>

<style scoped>
/* ===== DESKTOP SIDEBAR ===== */
.desktop-sidebar {
  position: fixed;
  left: 0;
  top: 64px;
  height: calc(100vh - 64px);
  width: 60px;
  background-color: var(--fin-surface);
  border-right: 1px solid var(--fin-border);
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
  z-index: 40;
  overflow: hidden;
}

.desktop-sidebar.expanded {
  width: 240px;
}

.sidebar-menu {
  list-style: none;
  padding: 12px 0;
  flex: 1;
}

.sidebar-link {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  gap: 12px;
  color: var(--fin-text-muted);
  text-decoration: none;
  transition: all 0.2s ease;
  cursor: pointer;
}

.sidebar-link:hover {
  color: var(--fin-text);
  background-color: var(--fin-hover);
}

.sidebar-link.active {
  color: #1da1f2;
  background-color: var(--fin-hover);
  border-right: 3px solid #1da1f2;
}

.sidebar-link i {
  font-size: 1.2rem;
  min-width: 28px;
  text-align: center;
}

.link-label {
  white-space: nowrap;
  font-size: 0.9rem;
}

/* ===== MOBILE BOTTOM NAV ===== */
.mobile-nav {
  display: none;
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 64px;
  background-color: var(--fin-surface);
  border-top: 1px solid var(--fin-border);
  z-index: 40;
  justify-content: space-around;
  align-items: center;
  padding: 0 4px;
}

.mobile-nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  color: var(--fin-text-muted);
  text-decoration: none;
  font-size: 0.58rem;
  padding: 6px 2px;
  border-radius: 8px;
  transition: color 0.2s;
  min-width: 0;
  flex: 1;
}

.mobile-nav-item i {
  font-size: 1.15rem;
}

.mobile-nav-item span {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
  text-align: center;
}

.mobile-nav-item.active {
  color: #1da1f2;
}

/* ===== RESPONSIVE ===== */
@media (max-width: 768px) {
  .desktop-sidebar {
    display: none;
  }

  .mobile-nav {
    display: flex;
  }
}
</style>
