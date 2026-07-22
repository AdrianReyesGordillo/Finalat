import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent, nextTick } from 'vue'
import { useTheme } from './useTheme'

/**
 * Helper to mount a dummy component that uses the composable.
 */
function mountWithTheme() {
  const TestComponent = defineComponent({
    setup() {
      return useTheme()
    },
    template: '<div />',
  })
  return mount(TestComponent)
}

describe('useTheme', () => {
  let matchMediaListeners: Array<(e: MediaQueryListEvent) => void>
  let matchMediaMatches: boolean

  beforeEach(() => {
    // Clear localStorage
    localStorage.clear()

    // Remove dark class
    document.documentElement.classList.remove('dark')

    // Reset module-level state by clearing any stale initialized state
    matchMediaListeners = []
    matchMediaMatches = false

    // Mock matchMedia
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: vi.fn().mockImplementation((query: string) => ({
        matches: matchMediaMatches,
        media: query,
        addEventListener: (_event: string, handler: (e: MediaQueryListEvent) => void) => {
          matchMediaListeners.push(handler)
        },
        removeEventListener: (_event: string, handler: (e: MediaQueryListEvent) => void) => {
          matchMediaListeners = matchMediaListeners.filter((h) => h !== handler)
        },
        dispatchEvent: vi.fn(),
      })),
    })
  })

  afterEach(() => {
    document.documentElement.classList.remove('dark')
  })

  it('defaults to system preference on first visit (no localStorage)', () => {
    const wrapper = mountWithTheme()
    const vm = wrapper.vm as unknown as ReturnType<typeof useTheme>

    // System prefers light, so isDark should be false
    expect(vm.isDark).toBe(false)
    expect(vm.currentPreference).toBe('system')
    expect(document.documentElement.classList.contains('dark')).toBe(false)

    wrapper.unmount()
  })

  it('applies dark class when system prefers dark and preference is system', () => {
    matchMediaMatches = true

    const wrapper = mountWithTheme()
    const vm = wrapper.vm as unknown as ReturnType<typeof useTheme>

    expect(vm.isDark).toBe(true)
    expect(document.documentElement.classList.contains('dark')).toBe(true)

    wrapper.unmount()
  })

  it('persists theme preference to localStorage', () => {
    const wrapper = mountWithTheme()
    const vm = wrapper.vm as unknown as ReturnType<typeof useTheme>

    vm.setTheme('dark')
    expect(localStorage.getItem('finalat-theme-preference')).toBe('dark')

    vm.setTheme('light')
    expect(localStorage.getItem('finalat-theme-preference')).toBe('light')

    vm.setTheme('system')
    expect(localStorage.getItem('finalat-theme-preference')).toBe('system')

    wrapper.unmount()
  })

  it('loads persisted preference from localStorage', () => {
    localStorage.setItem('finalat-theme-preference', 'dark')

    const wrapper = mountWithTheme()
    const vm = wrapper.vm as unknown as ReturnType<typeof useTheme>

    expect(vm.currentPreference).toBe('dark')
    expect(vm.isDark).toBe(true)
    expect(document.documentElement.classList.contains('dark')).toBe(true)

    wrapper.unmount()
  })

  it('toggleTheme switches from light to dark', () => {
    const wrapper = mountWithTheme()
    const vm = wrapper.vm as unknown as ReturnType<typeof useTheme>

    expect(vm.isDark).toBe(false)

    vm.toggleTheme()

    expect(vm.isDark).toBe(true)
    expect(document.documentElement.classList.contains('dark')).toBe(true)
    expect(localStorage.getItem('finalat-theme-preference')).toBe('dark')

    wrapper.unmount()
  })

  it('toggleTheme switches from dark to light', () => {
    localStorage.setItem('finalat-theme-preference', 'dark')

    const wrapper = mountWithTheme()
    const vm = wrapper.vm as unknown as ReturnType<typeof useTheme>

    expect(vm.isDark).toBe(true)

    vm.toggleTheme()

    expect(vm.isDark).toBe(false)
    expect(document.documentElement.classList.contains('dark')).toBe(false)
    expect(localStorage.getItem('finalat-theme-preference')).toBe('light')

    wrapper.unmount()
  })

  it('setTheme explicitly sets dark mode', () => {
    const wrapper = mountWithTheme()
    const vm = wrapper.vm as unknown as ReturnType<typeof useTheme>

    vm.setTheme('dark')

    expect(vm.isDark).toBe(true)
    expect(vm.currentPreference).toBe('dark')
    expect(document.documentElement.classList.contains('dark')).toBe(true)

    wrapper.unmount()
  })

  it('setTheme explicitly sets light mode', () => {
    matchMediaMatches = true

    const wrapper = mountWithTheme()
    const vm = wrapper.vm as unknown as ReturnType<typeof useTheme>

    // Initially dark because system prefers dark
    expect(vm.isDark).toBe(true)

    vm.setTheme('light')

    expect(vm.isDark).toBe(false)
    expect(vm.currentPreference).toBe('light')
    expect(document.documentElement.classList.contains('dark')).toBe(false)

    wrapper.unmount()
  })

  it('responds to system preference changes when set to system', async () => {
    const wrapper = mountWithTheme()
    const vm = wrapper.vm as unknown as ReturnType<typeof useTheme>

    expect(vm.isDark).toBe(false)

    // Simulate system switching to dark
    for (const listener of matchMediaListeners) {
      listener({ matches: true } as MediaQueryListEvent)
    }
    await nextTick()

    expect(vm.isDark).toBe(true)
    expect(document.documentElement.classList.contains('dark')).toBe(true)

    wrapper.unmount()
  })

  it('ignores system preference changes when set to explicit theme', async () => {
    const wrapper = mountWithTheme()
    const vm = wrapper.vm as unknown as ReturnType<typeof useTheme>

    vm.setTheme('light')

    // Simulate system switching to dark
    for (const listener of matchMediaListeners) {
      listener({ matches: true } as MediaQueryListEvent)
    }
    await nextTick()

    // Should stay light because explicit preference overrides system
    expect(vm.isDark).toBe(false)
    expect(document.documentElement.classList.contains('dark')).toBe(false)

    wrapper.unmount()
  })

  it('removes dark class when switching from dark to light', () => {
    localStorage.setItem('finalat-theme-preference', 'dark')

    const wrapper = mountWithTheme()
    const vm = wrapper.vm as unknown as ReturnType<typeof useTheme>

    expect(document.documentElement.classList.contains('dark')).toBe(true)

    vm.setTheme('light')

    expect(document.documentElement.classList.contains('dark')).toBe(false)

    wrapper.unmount()
  })

  it('handles invalid localStorage value gracefully', () => {
    localStorage.setItem('finalat-theme-preference', 'invalid-value')

    const wrapper = mountWithTheme()
    const vm = wrapper.vm as unknown as ReturnType<typeof useTheme>

    // Falls back to 'system'
    expect(vm.currentPreference).toBe('system')

    wrapper.unmount()
  })
})
