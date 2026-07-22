/**
 * User Preferences Store
 *
 * Manages panel visibility preferences (e.g., show/hide deudas tab and dashboard section).
 * Preferences are persisted on the backend per user.
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import finApi from '../utils/api'

// Available panel keys
export type PanelKey = 'deudas' | 'creditos' | 'inversiones' | 'gastos_ingresos' | 'aportaciones' | 'prestamos' | 'acciones' | 'ahorro' | 'afore'

export const usePreferencesStore = defineStore('finPreferences', () => {
  const preferences = ref<Record<string, string>>({})
  const loaded = ref(false)

  // Panel visibility helpers
  function isPanelEnabled(panel: PanelKey): boolean {
    const key = `panel_${panel}`
    // While loading, show all panels to avoid flicker
    if (!loaded.value) return true
    // Default: all panels enabled unless explicitly disabled
    return preferences.value[key] !== 'false'
  }

  const panelDeudas = computed(() => isPanelEnabled('deudas'))
  const panelCreditos = computed(() => isPanelEnabled('creditos'))
  const panelInversiones = computed(() => isPanelEnabled('inversiones'))
  const panelGastosIngresos = computed(() => isPanelEnabled('gastos_ingresos'))
  const panelAportaciones = computed(() => isPanelEnabled('aportaciones'))
  const panelPrestamos = computed(() => isPanelEnabled('prestamos'))
  const panelAcciones = computed(() => isPanelEnabled('acciones'))

  async function load() {
    // Check if preferences were pre-loaded during auth init
    if ((window as any).__kiro_prefs) {
      preferences.value = (window as any).__kiro_prefs
      delete (window as any).__kiro_prefs
      loaded.value = true
      return
    }

    try {
      const { data } = await finApi.get('/api/preferences')
      preferences.value = data
      loaded.value = true
    } catch {
      // If endpoint fails, use defaults (all enabled)
      loaded.value = true
    }
  }

  async function save(key: string, value: string) {
    const previousValue = preferences.value[key]
    preferences.value[key] = value
    try {
      await finApi.post('/api/preferences', { key, value })
    } catch (e) {
      console.error('[Preferences] Save failed, reverting:', e)
      // Revert local state on failure so UI reflects reality
      if (previousValue !== undefined) {
        preferences.value[key] = previousValue
      } else {
        delete preferences.value[key]
      }
    }
  }

  async function togglePanel(panel: PanelKey) {
    const enabled = !isPanelEnabled(panel)
    await save(`panel_${panel}`, enabled ? 'true' : 'false')
  }

  return {
    preferences,
    loaded,
    panelDeudas,
    panelCreditos,
    panelInversiones,
    panelGastosIngresos,
    panelAportaciones,
    panelPrestamos,
    panelAcciones,
    isPanelEnabled,
    load,
    save,
    togglePanel,
  }
})
