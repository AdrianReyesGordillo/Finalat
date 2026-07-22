import { ref, computed, onMounted, onUnmounted } from 'vue'

export type ThemePreference = 'light' | 'dark' | 'system'

const STORAGE_KEY = 'finalat-theme-preference'

/** Reactive state shared across all consumers of this composable. */
const preference = ref<ThemePreference>('system')
const systemPrefersDark = ref(false)

let initialized = false
let mediaQuery: MediaQueryList | null = null
let listenerCount = 0

function handleSystemChange(e: MediaQueryListEvent) {
  systemPrefersDark.value = e.matches
  applyTheme()
}

function applyTheme() {
  const shouldBeDark =
    preference.value === 'dark' ||
    (preference.value === 'system' && systemPrefersDark.value)

  if (shouldBeDark) {
    document.documentElement.classList.add('dark')
  } else {
    document.documentElement.classList.remove('dark')
  }
}

function loadPreference(): ThemePreference {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored === 'light' || stored === 'dark' || stored === 'system') {
      return stored
    }
  } catch {
    // localStorage unavailable (e.g., private browsing restrictions)
  }
  return 'system'
}

function savePreference(pref: ThemePreference) {
  try {
    localStorage.setItem(STORAGE_KEY, pref)
  } catch {
    // localStorage unavailable
  }
}

function initTheme() {
  if (initialized) return

  preference.value = loadPreference()

  mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
  systemPrefersDark.value = mediaQuery.matches
  mediaQuery.addEventListener('change', handleSystemChange)

  applyTheme()
  initialized = true
}

function teardown() {
  if (mediaQuery) {
    mediaQuery.removeEventListener('change', handleSystemChange)
    mediaQuery = null
  }
  initialized = false
}

/**
 * Composable for dark mode toggle.
 * Provides reactive isDark state, toggleTheme(), and setTheme() functions.
 *
 * - Checks localStorage for saved preference ('light' | 'dark' | 'system')
 * - Defaults to system preference on first visit
 * - Watches for system preference changes via matchMedia
 * - Adds/removes 'dark' class on document.documentElement
 */
export function useTheme() {
  onMounted(() => {
    listenerCount++
    initTheme()
  })

  onUnmounted(() => {
    listenerCount--
    if (listenerCount <= 0) {
      teardown()
      listenerCount = 0
    }
  })

  /** Whether dark mode is currently active. */
  const isDark = computed(() => {
    if (preference.value === 'dark') return true
    if (preference.value === 'light') return false
    return systemPrefersDark.value
  })

  /** The current stored preference. */
  const currentPreference = computed(() => preference.value)

  /**
   * Sets the theme preference explicitly.
   * @param pref - 'light', 'dark', or 'system'
   */
  function setTheme(pref: ThemePreference) {
    preference.value = pref
    savePreference(pref)
    applyTheme()
  }

  /**
   * Toggles between light and dark.
   * If currently in 'system' mode, toggles to the opposite of the current effective state.
   */
  function toggleTheme() {
    if (isDark.value) {
      setTheme('light')
    } else {
      setTheme('dark')
    }
  }

  return {
    isDark,
    currentPreference,
    toggleTheme,
    setTheme,
  }
}
