import { defineStore } from 'pinia'
import { ref } from 'vue'

export type ThemeMode = 'light' | 'dark'

const STORAGE_KEY = 'finalat-theme'

function getInitialTheme(): ThemeMode {
  const stored = localStorage.getItem(STORAGE_KEY)
  if (stored === 'light' || stored === 'dark') return stored
  return 'light'
}

function applyTheme(mode: ThemeMode) {
  const root = document.documentElement
  if (mode === 'dark') {
    root.classList.add('dark')
  } else {
    root.classList.remove('dark')
  }
}

let transitionTimer: ReturnType<typeof setTimeout> | undefined

function enableThemeTransition() {
  const root = document.documentElement
  root.classList.add('theme-transition')
  if (transitionTimer) clearTimeout(transitionTimer)
  transitionTimer = setTimeout(() => root.classList.remove('theme-transition'), 320)
}

export const useThemeStore = defineStore('theme', () => {
  const mode = ref<ThemeMode>('light')

  function init() {
    mode.value = getInitialTheme()
    applyTheme(mode.value)
  }

  function setTheme(next: ThemeMode) {
    mode.value = next
    localStorage.setItem(STORAGE_KEY, next)
    enableThemeTransition()
    applyTheme(next)
  }

  function toggle() {
    setTheme(mode.value === 'dark' ? 'light' : 'dark')
  }

  return { mode, init, setTheme, toggle }
})
