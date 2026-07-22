import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import finApi from '@/finanzas/utils/api'

export type Tier = 'free' | 'student' | 'family'

export interface Permissions {
  dashboard_basico: boolean
  gastos_ingresos: boolean
  cursos_gratuitos: boolean
  agente_limitado: boolean
  inversiones: boolean
  agente_ilimitado: boolean
  analisis_avanzado: boolean
  proyecciones: boolean
  soporte_prioritario: boolean
}

export interface FamilyMember {
  userId: string
  tier: string
}

export interface FamilyGroup {
  id: number
  ownerId: string
  name: string
  inviteCode: string
  maxMembers: number
  createdAt: string
  members: FamilyMember[]
  memberCount: number
  isOwner: boolean
}

export interface SubscriptionInfo {
  tier: Tier
  status: string
  familyGroupId: number | null
  startedAt: string | null
  expiresAt: string | null
  permissions: Permissions
  familyGroup: FamilyGroup | null
}

const DEFAULT_PERMISSIONS: Permissions = {
  dashboard_basico: true,
  gastos_ingresos: true,
  cursos_gratuitos: true,
  agente_limitado: true,
  inversiones: false,
  agente_ilimitado: false,
  analisis_avanzado: false,
  proyecciones: false,
  soporte_prioritario: false,
}

export const useSubscriptionStore = defineStore('subscription', () => {
  const tier = ref<Tier>('free')
  const status = ref('active')
  const permissions = ref<Permissions>({ ...DEFAULT_PERMISSIONS })
  const familyGroup = ref<FamilyGroup | null>(null)
  const loaded = ref(false)
  const loading = ref(false)

  const isFree = computed(() => tier.value === 'free')
  const isStudent = computed(() => tier.value === 'student')
  const isFamily = computed(() => tier.value === 'family')
  const isPremium = computed(() => tier.value === 'student' || tier.value === 'family')

  function hasPermission(key: keyof Permissions): boolean {
    return permissions.value[key] ?? false
  }

  async function load() {
    if (loading.value) return
    loading.value = true

    if ((window as any).__kiro_subscription) {
      const data = (window as any).__kiro_subscription
      delete (window as any).__kiro_subscription
      tier.value = data.tier || 'free'
      status.value = data.status || 'active'
      permissions.value = data.permissions || { ...DEFAULT_PERMISSIONS }
      familyGroup.value = data.familyGroup || null
      loaded.value = true
      loading.value = false
      return
    }

    try {
      const { data } = await finApi.get('/api/subscription')
      tier.value = data.tier || 'free'
      status.value = data.status || 'active'
      permissions.value = data.permissions || { ...DEFAULT_PERMISSIONS }
      familyGroup.value = data.familyGroup || null
      loaded.value = true
    } catch {
      tier.value = 'free'
      permissions.value = { ...DEFAULT_PERMISSIONS }
      loaded.value = true
    } finally {
      loading.value = false
    }
  }

  async function updateTier(newTier: Tier) {
    try {
      const { data } = await finApi.post('/api/subscription', { tier: newTier })
      if (data.success) {
        await load()
      }
      return data
    } catch (err: any) {
      throw new Error(err.response?.data?.detail || 'Error al actualizar la suscripción.')
    }
  }

  async function joinFamily(inviteCode: string) {
    try {
      const { data } = await finApi.post('/api/family-group/join', { inviteCode })
      if (data.success) {
        await load()
      }
      return data
    } catch (err: any) {
      throw new Error(err.response?.data?.detail || 'Error al unirse al grupo familiar.')
    }
  }

  async function leaveFamily() {
    try {
      const { data } = await finApi.post('/api/family-group/leave')
      if (data.success) {
        await load()
      }
      return data
    } catch (err: any) {
      throw new Error(err.response?.data?.detail || 'Error al salir del grupo.')
    }
  }

  async function removeMember(memberId: string) {
    try {
      const { data } = await finApi.post('/api/family-group/remove-member', { memberId })
      if (data.success) {
        await load()
      }
      return data
    } catch (err: any) {
      throw new Error(err.response?.data?.detail || 'Error al remover miembro.')
    }
  }

  async function deleteGroup() {
    try {
      const { data } = await finApi.delete('/api/family-group')
      if (data.success) {
        await load()
      }
      return data
    } catch (err: any) {
      throw new Error(err.response?.data?.detail || 'Error al eliminar el grupo.')
    }
  }

  return {
    tier,
    status,
    permissions,
    familyGroup,
    loaded,
    loading,
    isFree,
    isStudent,
    isFamily,
    isPremium,
    hasPermission,
    load,
    updateTier,
    joinFamily,
    leaveFamily,
    removeMember,
    deleteGroup,
  }
})
