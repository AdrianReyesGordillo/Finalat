import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ModuleUpdateTracker from './ModuleUpdateTracker.vue'
import type { ModuleUpdateStatus } from '../../types'

// Mock vue-router's router-link to simplify rendering
const RouterLinkStub = {
  template: '<a :href="to"><slot /></a>',
  props: ['to'],
}

function mountComponent(modules: ModuleUpdateStatus[]) {
  return mount(ModuleUpdateTracker, {
    props: { modules },
    global: {
      stubs: {
        'router-link': RouterLinkStub,
      },
    },
  })
}

describe('ModuleUpdateTracker', () => {
  it('renders all modules with correct labels', () => {
    const modules: ModuleUpdateStatus[] = [
      { module_name: 'ahorro', last_updated_at: new Date().toISOString(), stale: false },
      { module_name: 'creditos', last_updated_at: null, stale: true },
      { module_name: 'gastos_ingresos', last_updated_at: null, stale: true },
    ]

    const wrapper = mountComponent(modules)

    expect(wrapper.text()).toContain('Ahorro')
    expect(wrapper.text()).toContain('Créditos')
    expect(wrapper.text()).toContain('Gastos/Ingresos')
  })

  it('shows green status for up-to-date modules', () => {
    const modules: ModuleUpdateStatus[] = [
      { module_name: 'ahorro', last_updated_at: new Date().toISOString(), stale: false },
    ]

    const wrapper = mountComponent(modules)

    expect(wrapper.text()).toContain('Actualizado hoy')
    // Should have the green border class
    const link = wrapper.find('a')
    expect(link.classes()).toContain('border-green-200')
  })

  it('shows orange/yellow warning for stale modules', () => {
    // 10 days ago
    const tenDaysAgo = new Date()
    tenDaysAgo.setDate(tenDaysAgo.getDate() - 10)

    const modules: ModuleUpdateStatus[] = [
      { module_name: 'deudas', last_updated_at: tenDaysAgo.toISOString(), stale: true },
    ]

    const wrapper = mountComponent(modules)

    expect(wrapper.text()).toContain('Actualiza este módulo')
    expect(wrapper.text()).toContain('10 días sin actualizar')
    const link = wrapper.find('a')
    expect(link.classes()).toContain('border-yellow-200')
  })

  it('shows red status for never-updated modules', () => {
    const modules: ModuleUpdateStatus[] = [
      { module_name: 'afore', last_updated_at: null, stale: true },
    ]

    const wrapper = mountComponent(modules)

    expect(wrapper.text()).toContain('Sin actualizar')
    const link = wrapper.find('a')
    expect(link.classes()).toContain('border-red-200')
  })

  it('links each module to its corresponding page', () => {
    const modules: ModuleUpdateStatus[] = [
      { module_name: 'ahorro', last_updated_at: new Date().toISOString(), stale: false },
      { module_name: 'gbm_portfolio', last_updated_at: null, stale: true },
    ]

    const wrapper = mountComponent(modules)
    const links = wrapper.findAll('a')

    expect(links[0].attributes('href')).toBe('/ahorro')
    expect(links[1].attributes('href')).toBe('/gbm-portfolio')
  })

  it('displays the last updated date in local format', () => {
    const modules: ModuleUpdateStatus[] = [
      { module_name: 'creditos', last_updated_at: '2024-06-15T10:30:00Z', stale: true },
    ]

    const wrapper = mountComponent(modules)

    // Should contain "Última vez:" followed by a formatted date
    expect(wrapper.text()).toContain('Última vez:')
  })

  it('shows "Actualizado hace 1 día" for singular day', () => {
    const yesterday = new Date()
    yesterday.setDate(yesterday.getDate() - 1)

    const modules: ModuleUpdateStatus[] = [
      { module_name: 'ahorro', last_updated_at: yesterday.toISOString(), stale: false },
    ]

    const wrapper = mountComponent(modules)

    expect(wrapper.text()).toContain('Actualizado hace 1 día')
  })

  it('renders section heading and description', () => {
    const modules: ModuleUpdateStatus[] = [
      { module_name: 'ahorro', last_updated_at: null, stale: true },
    ]

    const wrapper = mountComponent(modules)

    expect(wrapper.text()).toContain('Estado de Módulos')
    expect(wrapper.text()).toContain('Mantén tus módulos actualizados')
  })
})
