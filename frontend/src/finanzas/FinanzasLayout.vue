<template>
  <div class="finanzas-app" :class="{ 'dark-mode': isDark }">
    <Sidebar />
    <main class="finanzas-main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import Sidebar from './components/Sidebar.vue'
import { useThemeStore } from '@/stores/theme'
// Register cache interceptor early so mutations always invalidate cache
import './utils/cache'

const themeStore = useThemeStore()
// El dashboard sigue el tema global (claro/oscuro) del sistema.
const isDark = computed(() => themeStore.mode === 'dark')
</script>

<style scoped>
/* ── Paleta del dashboard como variables CSS ──────────────────────────────────
   Valores CLAROS por defecto; los OSCUROS se aplican cuando el contenedor
   tiene la clase `.dark-mode` (controlada por el toggle global del NavBar).
   Las variables se heredan a las vistas hijas aunque usen estilos `scoped`. */
.finanzas-app {
  --fin-bg: #eef1f6;
  --fin-bg-2: #f4f6f9;
  --fin-surface: #ffffff;
  --fin-surface-2: #f4f6f9;
  --fin-hover: #e9eef4;
  --fin-border: #dde3ea;
  --fin-text: #1a2733;
  --fin-text-muted: #5e6b7a;

  display: flex;
  min-height: 100%;
  background-color: var(--fin-bg);
  color: var(--fin-text);
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

.finanzas-app.dark-mode {
  --fin-bg: #0f1419;
  --fin-bg-2: #0d1821;
  --fin-surface: #15202b;
  --fin-surface-2: #192734;
  --fin-hover: #1c2b3a;
  --fin-border: #2d3741;
  --fin-text: #e1e8ed;
  --fin-text-muted: #8899a6;
}

.finanzas-main-content {
  flex: 1;
  margin-left: 60px;
  padding: 24px 40px;
  transition: margin-left 0.3s ease;
  display: flex;
  justify-content: center;
  overflow-x: hidden;
  min-width: 0;
}

.finanzas-main-content > * {
  width: 100%;
  max-width: 1200px;
}

@media (max-width: 1024px) {
  .finanzas-main-content {
    padding: 24px 24px;
  }
}

@media (max-width: 768px) {
  .finanzas-main-content {
    margin-left: 0;
    padding: 16px 12px;
    padding-bottom: 80px;
  }
}
</style>
