<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { auth } from '@/firebase'

const api = axios.create({ baseURL: import.meta.env.VITE_API_URL || '/api' })
api.interceptors.request.use(async (config) => {
  const user = auth.currentUser
  if (user) { config.headers.Authorization = `Bearer ${await user.getIdToken()}` }
  return config
})

interface InstrumentRow {
  institution: string;
  referral_link: string; signup_link: string; editing?: boolean;
}

const instruments = ref<InstrumentRow[]>([])
const loading = ref(true)
const saving = ref<string | null>(null)

async function loadInstruments() {
  loading.value = true
  try {
    const { data } = await api.get('/admin/instruments')
    instruments.value = data.items.map((i: any) => ({ ...i, editing: false }))
  } catch (e: any) {
    console.error('Admin load error:', e)
  } finally { loading.value = false }
}

async function saveLinks(inst: InstrumentRow) {
  saving.value = inst.institution
  try {
    await api.put(`/admin/instruments/${encodeURIComponent(inst.institution)}/links`, {
      referral_link: inst.referral_link,
      signup_link: inst.referral_link,
    })
    inst.editing = false
  } catch (e: any) {
    alert('Error al guardar: ' + (e.response?.data?.error || e.message))
  } finally { saving.value = null }
}

onMounted(loadInstruments)
</script>

<template>
  <div class="admin-page">
    <h1>Admin — Links de Referido</h1>
    <p class="admin-desc">Agrega links de referido y registro para cada instrumento. El agente los incluirá en sus recomendaciones.</p>

    <div v-if="loading" class="admin-loading">Cargando...</div>

    <table v-else class="admin-table">
      <thead>
        <tr>
          <th>Institución</th>
          <th>Link de Referido</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="inst in instruments" :key="inst.institution">
          <td class="inst-institution">{{ inst.institution }}</td>
          <td>
            <input v-model="inst.referral_link" placeholder="https://..." class="admin-input" @focus="inst.editing = true" />
          </td>
          <td>
            <button v-if="inst.editing" class="btn-save" :disabled="saving === inst.institution" @click="saveLinks(inst)">
              {{ saving === inst.institution ? '...' : 'Guardar' }}
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.admin-page {
  max-width: 1200px; margin: 0 auto; padding: 2rem 1rem;
}
h1 { font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem; }
.admin-desc { color: #6b7280; font-size: 0.9rem; margin-bottom: 1.5rem; }
.admin-loading { text-align: center; padding: 3rem; color: #6b7280; }
.admin-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
.admin-table th { text-align: left; padding: 10px 12px; font-size: 0.75rem; text-transform: uppercase; color: #6b7280; border-bottom: 2px solid #e5e7eb; }
.admin-table td { padding: 10px 12px; border-bottom: 1px solid #f3f4f6; vertical-align: middle; }
.inst-institution { font-weight: 600; color: #374151; }
.inst-name { color: #6b7280; }
.inst-rate { font-weight: 700; color: #10b981; }
.admin-input { width: 100%; padding: 6px 10px; border: 1px solid #e5e7eb; border-radius: 6px; font-size: 0.8rem; }
.admin-input:focus { outline: none; border-color: #1da1f2; }
.btn-save { background: #1da1f2; color: #fff; border: none; padding: 6px 14px; border-radius: 6px; font-size: 0.8rem; font-weight: 600; cursor: pointer; }
.btn-save:disabled { opacity: 0.5; }

/* Dark mode */
html.dark .admin-page h1 { color: #e1e8ed; }
html.dark .admin-desc { color: #8899a6; }
html.dark .admin-table th { color: #8899a6; border-bottom-color: #2d3741; }
html.dark .admin-table td { border-bottom-color: #2d3741; }
html.dark .inst-institution { color: #e1e8ed; }
html.dark .inst-name { color: #8899a6; }
html.dark .admin-input { background: #15202b; border-color: #2d3741; color: #e1e8ed; }
html.dark .admin-input:focus { border-color: #1da1f2; }
</style>

<style>
/* Unscoped dark overrides */
html.dark .admin-page { color: #e1e8ed; }
</style>
