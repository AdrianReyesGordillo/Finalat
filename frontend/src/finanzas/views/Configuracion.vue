<template>
  <div class="configuracion" :class="{ 'dark-mode': isDark }">
    <h1 class="page-title">Configuración</h1>

    <!-- Tabs -->
    <div class="config-tabs">
      <button class="tab-btn" :class="{ active: activeTab === 'paneles' }" @click="activeTab = 'paneles'">
        <i class="pi pi-th-large"></i> Paneles
      </button>
      <button class="tab-btn" :class="{ active: activeTab === 'ahorro' }" @click="activeTab = 'ahorro'">
        <i class="pi pi-wallet"></i> Cuentas de Ahorro
      </button>
      <button class="tab-btn" :class="{ active: activeTab === 'creditos' }" @click="activeTab = 'creditos'">
        <i class="pi pi-credit-card"></i> Créditos
      </button>
      <button class="tab-btn" :class="{ active: activeTab === 'aportaciones' }" @click="activeTab = 'aportaciones'">
        <i class="pi pi-calendar"></i> Aportaciones
      </button>
    </div>

    <!-- PANELES -->
    <div v-if="activeTab === 'paneles'" class="config-section">
      <div class="section-header">
        <h2>Paneles Visibles</h2>
      </div>
      <p class="panel-description">Selecciona qué secciones deseas ver en la navegación y en el dashboard.</p>

      <div class="panels-list">
        <div class="panel-toggle-item">
          <div class="panel-toggle-info">
            <i class="pi pi-money-bill panel-toggle-icon" style="color: #ef4444;"></i>
            <div>
              <span class="panel-toggle-name">Deudas</span>
              <span class="panel-toggle-desc">Panel de seguimiento de deudas y próximos pagos</span>
            </div>
          </div>
          <label class="toggle-switch">
            <input type="checkbox" :checked="prefsStore.panelDeudas" @change="prefsStore.togglePanel('deudas')">
            <span class="toggle-slider"></span>
          </label>
        </div>

        <div class="panel-toggle-item">
          <div class="panel-toggle-info">
            <i class="pi pi-credit-card panel-toggle-icon" style="color: #8b5cf6;"></i>
            <div>
              <span class="panel-toggle-name">Créditos</span>
              <span class="panel-toggle-desc">Tarjetas de crédito, deuda y disponible</span>
            </div>
          </div>
          <label class="toggle-switch">
            <input type="checkbox" :checked="prefsStore.panelCreditos" @change="prefsStore.togglePanel('creditos')">
            <span class="toggle-slider"></span>
          </label>
        </div>

        <div class="panel-toggle-item panel-toggle-clickable" @click.self="showInversionesModal = true">
          <div class="panel-toggle-info" @click="showInversionesModal = true">
            <i class="pi pi-chart-bar panel-toggle-icon" style="color: #0075eb;"></i>
            <div>
              <span class="panel-toggle-name">Inversiones <i class="pi pi-chevron-right panel-chevron"></i></span>
              <span class="panel-toggle-desc">Ahorro, afore y portafolio general</span>
            </div>
          </div>
          <label class="toggle-switch" @click.stop>
            <input type="checkbox" :checked="prefsStore.panelInversiones" @change="prefsStore.togglePanel('inversiones')">
            <span class="toggle-slider"></span>
          </label>
        </div>

        <div class="panel-toggle-item panel-toggle-clickable" @click.self="showGICategoriasModal = true">
          <div class="panel-toggle-info" @click="showGICategoriasModal = true">
            <i class="pi pi-list panel-toggle-icon" style="color: #f59e0b;"></i>
            <div>
              <span class="panel-toggle-name">Gastos / Ingresos <i class="pi pi-chevron-right panel-chevron"></i></span>
              <span class="panel-toggle-desc">Registro de movimientos financieros</span>
            </div>
          </div>
          <label class="toggle-switch" @click.stop>
            <input type="checkbox" :checked="prefsStore.panelGastosIngresos" @change="prefsStore.togglePanel('gastos_ingresos')">
            <span class="toggle-slider"></span>
          </label>
        </div>

        <div class="panel-toggle-item">
          <div class="panel-toggle-info">
            <i class="pi pi-calendar panel-toggle-icon" style="color: #10b981;"></i>
            <div>
              <span class="panel-toggle-name">Aportaciones</span>
              <span class="panel-toggle-desc">Seguimiento de aportaciones periódicas</span>
            </div>
          </div>
          <label class="toggle-switch">
            <input type="checkbox" :checked="prefsStore.panelAportaciones" @change="prefsStore.togglePanel('aportaciones')">
            <span class="toggle-slider"></span>
          </label>
        </div>
      </div>
    </div>

    <!-- MODAL SUB-OPCIONES DE INVERSIONES -->
    <div v-if="showInversionesModal" class="modal-overlay" @click.self="showInversionesModal = false">
      <div class="modal-box">
        <div class="modal-header">
          <h3><i class="pi pi-chart-bar" style="color: #0075eb;"></i> Inversiones</h3>
          <button class="btn-close" @click="showInversionesModal = false"><i class="pi pi-times"></i></button>
        </div>
        <div class="modal-body">
          <p class="panel-description" style="margin-bottom: 16px;">Configura qué secciones se muestran dentro de Inversiones y en el Dashboard.</p>

          <div class="panels-list">
            <div class="panel-toggle-item">
              <div class="panel-toggle-info">
                <i class="pi pi-wallet panel-toggle-icon" style="color: #0075eb;"></i>
                <div>
                  <span class="panel-toggle-name">Ahorro</span>
                  <span class="panel-toggle-desc">Cuentas de ahorro y liquidez</span>
                </div>
              </div>
              <label class="toggle-switch">
                <input type="checkbox" :checked="prefsStore.isPanelEnabled('ahorro')" @change="prefsStore.togglePanel('ahorro')">
                <span class="toggle-slider"></span>
              </label>
            </div>

            <div class="panel-toggle-item">
              <div class="panel-toggle-info">
                <i class="pi pi-users panel-toggle-icon" style="color: #10b981;"></i>
                <div>
                  <span class="panel-toggle-name">Préstamos</span>
                  <span class="panel-toggle-desc">Seguimiento de préstamos activos</span>
                </div>
              </div>
              <label class="toggle-switch">
                <input type="checkbox" :checked="prefsStore.panelPrestamos" @change="prefsStore.togglePanel('prestamos')">
                <span class="toggle-slider"></span>
              </label>
            </div>

            <div class="panel-toggle-item">
              <div class="panel-toggle-info">
                <i class="pi pi-shield panel-toggle-icon" style="color: #1da1f2;"></i>
                <div>
                  <span class="panel-toggle-name">Afore</span>
                  <span class="panel-toggle-desc">Cuenta de retiro y proyecciones</span>
                </div>
              </div>
              <label class="toggle-switch">
                <input type="checkbox" :checked="prefsStore.isPanelEnabled('afore')" @change="prefsStore.togglePanel('afore')">
                <span class="toggle-slider"></span>
              </label>
            </div>

            <div class="panel-toggle-item">
              <div class="panel-toggle-info">
                <i class="pi pi-chart-line panel-toggle-icon" style="color: #8b5cf6;"></i>
                <div>
                  <span class="panel-toggle-name">Acciones</span>
                  <span class="panel-toggle-desc">Portafolio de acciones y ETFs (nacional e internacional)</span>
                </div>
              </div>
              <label class="toggle-switch">
                <input type="checkbox" :checked="prefsStore.panelAcciones" @change="prefsStore.togglePanel('acciones')">
                <span class="toggle-slider"></span>
              </label>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-save" @click="showInversionesModal = false">
            <i class="pi pi-check"></i> Listo
          </button>
        </div>
      </div>
    </div>

    <!-- MODAL SUB-OPCIONES DE GASTOS/INGRESOS (Categorías) -->
    <div v-if="showGICategoriasModal" class="modal-overlay" @click.self="showGICategoriasModal = false">
      <div class="modal-box" style="max-width: 400px;">
        <div class="modal-header">
          <h3><i class="pi pi-list" style="color: #f59e0b;"></i> Categorías</h3>
          <button class="btn-close" @click="showGICategoriasModal = false"><i class="pi pi-times"></i></button>
        </div>
        <div class="modal-body" style="padding: 16px;">
          <p class="panel-description" style="margin-bottom: 12px;">Categorías para registrar gastos e ingresos.</p>

          <div class="gi-cat-list">
            <div v-for="cat in giCategoriesList" :key="cat.id" class="gi-cat-item">
              <span class="gi-cat-name">{{ cat.name }}</span>
              <div class="gi-cat-actions">
                <button class="btn-edit" @click="openGICategoryModal(cat)"><i class="pi pi-pencil"></i></button>
                <button class="btn-delete" @click="deleteGICategory(cat.id)"><i class="pi pi-trash"></i></button>
              </div>
            </div>
            <div v-if="!giCategoriesList.length" class="config-empty">No hay categorías configuradas.</div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-add" @click="openGICategoryModal(null)" style="margin-right: auto;">
            <i class="pi pi-plus"></i> Agregar
          </button>
          <button class="btn-save" @click="showGICategoriasModal = false">
            <i class="pi pi-check"></i> Listo
          </button>
        </div>
      </div>
    </div>

    <!-- MODAL EDITAR/CREAR CATEGORÍA GI -->
    <div v-if="showGICategoryEditModal" class="modal-overlay" @click.self="showGICategoryEditModal = false">
      <div class="modal-box" style="max-width: 360px;">
        <div class="modal-header">
          <h3>{{ editingGICategory ? 'Editar' : 'Nueva' }} Categoría</h3>
          <button class="btn-close" @click="showGICategoryEditModal = false"><i class="pi pi-times"></i></button>
        </div>
        <div class="modal-body">
          <div class="form-field">
            <label>Nombre</label>
            <input type="text" v-model="giCategoryForm.name" placeholder="Ej: Comida, Transporte..." />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="showGICategoryEditModal = false">Cancelar</button>
          <button class="btn-save" :disabled="!giCategoryForm.name || saving" @click="saveGICategory">
            <i :class="saving ? 'pi pi-spin pi-spinner' : 'pi pi-check'"></i>
            {{ saving ? 'Guardando...' : 'Guardar' }}
          </button>
        </div>
      </div>
    </div>

    <!-- AHORRO -->
    <div v-if="activeTab === 'ahorro'" class="config-section">
      <div class="section-header">
        <h2>Cuentas de Ahorro</h2>
        <button class="btn-add" @click="openAhorroModal(null)">
          <i class="pi pi-plus"></i> Agregar
        </button>
      </div>

      <div class="config-list">
        <div v-for="item in ahorroList" :key="item.id" class="config-item" :style="{ borderLeftColor: item.color }">
          <div class="config-item-info">
            <span class="config-item-dot" :style="{ backgroundColor: item.color }"></span>
            <div>
              <span class="config-item-name">{{ item.name }}</span>
              <span class="config-item-desc">{{ item.description }} — {{ item.annual_rate }}% anual{{ item.rate_cap ? ' (tope $' + item.rate_cap + ', excedente ' + item.excess_rate + '%)' : '' }}</span>
            </div>
          </div>
          <div class="config-item-actions">
            <button class="btn-edit" @click="openAhorroModal(item)"><i class="pi pi-pencil"></i></button>
            <button class="btn-delete" @click="deleteAhorro(item.id)"><i class="pi pi-trash"></i></button>
          </div>
        </div>
        <div v-if="!ahorroList.length" class="config-empty">No hay cuentas de ahorro configuradas.</div>
      </div>
    </div>

    <!-- CREDITOS -->
    <div v-if="activeTab === 'creditos'" class="config-section">
      <div class="section-header">
        <h2>Tarjetas de Crédito</h2>
        <button class="btn-add" @click="openCreditoModal(null)">
          <i class="pi pi-plus"></i> Agregar
        </button>
      </div>

      <div class="config-list">
        <div v-for="item in creditosList" :key="item.id" class="config-item" :style="{ borderLeftColor: item.color }">
          <div class="config-item-info">
            <span class="config-item-dot" :style="{ backgroundColor: item.color }"></span>
            <div>
              <span class="config-item-name">{{ item.name }}</span>
            </div>
          </div>
          <div class="config-item-actions">
            <button class="btn-edit" @click="openCreditoModal(item)"><i class="pi pi-pencil"></i></button>
            <button class="btn-delete" @click="deleteCredito(item.id)"><i class="pi pi-trash"></i></button>
          </div>
        </div>
        <div v-if="!creditosList.length" class="config-empty">No hay tarjetas de crédito configuradas.</div>
      </div>
    </div>

    <!-- APORTACIONES -->
    <div v-if="activeTab === 'aportaciones'" class="config-section">
      <div class="section-header">
        <h2>Aportaciones</h2>
        <button class="btn-add" @click="openAportacionModal(null)">
          <i class="pi pi-plus"></i> Agregar
        </button>
      </div>

      <div class="config-list">
        <div v-for="item in aportacionesList" :key="item.id" class="config-item" :style="{ borderLeftColor: item.color }">
          <div class="config-item-info">
            <span class="config-item-dot" :style="{ backgroundColor: item.color }"></span>
            <div>
              <span class="config-item-name">{{ item.category }}{{ item.person ? ' — ' + item.person : '' }}</span>
              <span class="config-item-desc">${{ item.amount }}/{{ frequencyLabel(item.frequency) }}</span>
            </div>
          </div>
          <div class="config-item-actions">
            <button class="btn-edit" @click="openAportacionModal(item)"><i class="pi pi-pencil"></i></button>
            <button class="btn-delete" @click="deleteAportacion(item.id)"><i class="pi pi-trash"></i></button>
          </div>
        </div>
        <div v-if="!aportacionesList.length" class="config-empty">No hay aportaciones configuradas.</div>
      </div>
    </div>

    <!-- MODAL AHORRO -->
    <div v-if="showAhorroModal" class="modal-overlay" @click.self="showAhorroModal = false">
      <div class="modal-box">
        <div class="modal-header">
          <h3>{{ editingAhorro ? 'Editar' : 'Nueva' }} Cuenta de Ahorro</h3>
          <button class="btn-close" @click="showAhorroModal = false"><i class="pi pi-times"></i></button>
        </div>
        <div class="modal-body">
          <div class="form-field">
            <label>Banco / Nombre</label>
            <input type="text" v-model="ahorroForm.name" placeholder="Ej: Revolut, Nu..." />
          </div>
          <div class="form-field">
            <label>Descripción</label>
            <input type="text" v-model="ahorroForm.description" placeholder="Ej: Cuenta principal" />
          </div>
          <div class="form-field">
            <label>Tasa Anual (%)</label>
            <input type="number" step="0.01" min="0" v-model.number="ahorroForm.annualRate" placeholder="0.00" />
          </div>
          <div class="form-field">
            <label>Tope para tasa preferente ($)</label>
            <input type="number" step="0.01" min="0" v-model.number="ahorroForm.rateCap" placeholder="0 = sin tope" />
          </div>
          <div class="form-field">
            <label>Tasa sobre excedente (%)</label>
            <input type="number" step="0.01" min="0" v-model.number="ahorroForm.excessRate" placeholder="0.00" />
          </div>
          <div class="form-field">
            <label>Color</label>
            <div class="color-picker">
              <input type="color" v-model="ahorroForm.color" />
              <span class="color-preview" :style="{ backgroundColor: ahorroForm.color }">{{ ahorroForm.color }}</span>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="showAhorroModal = false">Cancelar</button>
          <button class="btn-save" :disabled="!ahorroForm.name || saving" @click="saveAhorro">
            <i :class="saving ? 'pi pi-spin pi-spinner' : 'pi pi-check'"></i>
            {{ saving ? 'Guardando...' : 'Guardar' }}
          </button>
        </div>
      </div>
    </div>

    <!-- MODAL CREDITO -->
    <div v-if="showCreditoModal" class="modal-overlay" @click.self="showCreditoModal = false">
      <div class="modal-box">
        <div class="modal-header">
          <h3>{{ editingCredito ? 'Editar' : 'Nueva' }} Tarjeta de Crédito</h3>
          <button class="btn-close" @click="showCreditoModal = false"><i class="pi pi-times"></i></button>
        </div>
        <div class="modal-body">
          <div class="form-field">
            <label>Nombre del Banco</label>
            <input type="text" v-model="creditoForm.name" placeholder="Ej: BBVA, Nu..." />
          </div>
          <div class="form-field">
            <label>Color</label>
            <div class="color-picker">
              <input type="color" v-model="creditoForm.color" />
              <span class="color-preview" :style="{ backgroundColor: creditoForm.color }">{{ creditoForm.color }}</span>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="showCreditoModal = false">Cancelar</button>
          <button class="btn-save" :disabled="!creditoForm.name || saving" @click="saveCredito">
            <i :class="saving ? 'pi pi-spin pi-spinner' : 'pi pi-check'"></i>
            {{ saving ? 'Guardando...' : 'Guardar' }}
          </button>
        </div>
      </div>
    </div>

    <!-- MODAL APORTACION -->
    <div v-if="showAportacionModal" class="modal-overlay" @click.self="showAportacionModal = false">
      <div class="modal-box">
        <div class="modal-header">
          <h3>{{ editingAportacion ? 'Editar' : 'Nueva' }} Aportación</h3>
          <button class="btn-close" @click="showAportacionModal = false"><i class="pi pi-times"></i></button>
        </div>
        <div class="modal-body">
          <div class="form-field">
            <label>Nombre / Categoría</label>
            <input type="text" v-model="aportacionForm.category" placeholder="Ej: GBM, Afore..." />
          </div>
          <div class="form-field">
            <label>Persona (opcional)</label>
            <input type="text" v-model="aportacionForm.person" placeholder="Ej: Adrian, Karime..." />
          </div>
          <div class="form-field">
            <label>Frecuencia</label>
            <select v-model="aportacionForm.frequency" class="form-select">
              <option value="semanal">Semanal</option>
              <option value="quincenal">Quincenal</option>
              <option value="mensual">Mensual</option>
            </select>
          </div>
          <div class="form-field">
            <label>Cantidad por periodo ($)</label>
            <input type="number" step="1" min="1" v-model.number="aportacionForm.amount" placeholder="50" />
          </div>
          <div class="form-field">
            <label>Color</label>
            <div class="color-picker">
              <input type="color" v-model="aportacionForm.color" />
              <span class="color-preview" :style="{ backgroundColor: aportacionForm.color }">{{ aportacionForm.color }}</span>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="showAportacionModal = false">Cancelar</button>
          <button class="btn-save" :disabled="!aportacionForm.category || !aportacionForm.amount || saving" @click="saveAportacion">
            <i :class="saving ? 'pi pi-spin pi-spinner' : 'pi pi-check'"></i>
            {{ saving ? 'Guardando...' : 'Guardar' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import finApi from '../utils/api'
import { cachedGet } from '../utils/cache'
import { usePreferencesStore } from '../stores/preferences'
import { useThemeStore } from '@/stores/theme'

const prefsStore = usePreferencesStore()
const themeStore = useThemeStore()
const isDark = computed(() => themeStore.mode === 'dark')
const activeTab = ref('paneles')
const saving = ref(false)
const showInversionesModal = ref(false)
const showGICategoriasModal = ref(false)
const showGICategoryEditModal = ref(false)

// --- Ahorro ---
const ahorroList = ref([])
const showAhorroModal = ref(false)
const editingAhorro = ref(null)
const ahorroForm = ref({ name: '', description: '', annualRate: 0, color: '#1da1f2', rateCap: 0, excessRate: 0 })

async function loadAhorro() {
  const { data } = await cachedGet('/api/config/ahorro')
  ahorroList.value = data
}

function openAhorroModal(item) {
  if (item) {
    editingAhorro.value = item
    ahorroForm.value = { name: item.name, description: item.description, annualRate: item.annual_rate, color: item.color, rateCap: item.rate_cap || 0, excessRate: item.excess_rate || 0 }
  } else {
    editingAhorro.value = null
    ahorroForm.value = { name: '', description: '', annualRate: 0, color: '#1da1f2', rateCap: 0, excessRate: 0 }
  }
  showAhorroModal.value = true
}

async function saveAhorro() {
  saving.value = true
  try {
    if (editingAhorro.value) {
      await finApi.put(`/api/config/ahorro/${editingAhorro.value.id}`, ahorroForm.value)
    } else {
      await finApi.post('/api/config/ahorro', ahorroForm.value)
    }
    showAhorroModal.value = false
    await loadAhorro()
  } catch (e) { console.error(e) }
  saving.value = false
}

async function deleteAhorro(id) {
  if (!confirm('¿Eliminar esta cuenta de ahorro?')) return
  await finApi.delete(`/api/config/ahorro/${id}`)
  await loadAhorro()
}

// --- Creditos ---
const creditosList = ref([])
const showCreditoModal = ref(false)
const editingCredito = ref(null)
const creditoForm = ref({ name: '', color: '#1da1f2' })

async function loadCreditos() {
  const { data } = await cachedGet('/api/config/creditos')
  creditosList.value = data
}

function openCreditoModal(item) {
  if (item) {
    editingCredito.value = item
    creditoForm.value = { name: item.name, color: item.color }
  } else {
    editingCredito.value = null
    creditoForm.value = { name: '', color: '#1da1f2' }
  }
  showCreditoModal.value = true
}

async function saveCredito() {
  saving.value = true
  try {
    if (editingCredito.value) {
      await finApi.put(`/api/config/creditos/${editingCredito.value.id}`, creditoForm.value)
    } else {
      await finApi.post('/api/config/creditos', creditoForm.value)
    }
    showCreditoModal.value = false
    await loadCreditos()
  } catch (e) { console.error(e) }
  saving.value = false
}

async function deleteCredito(id) {
  if (!confirm('¿Eliminar esta tarjeta de crédito?')) return
  await finApi.delete(`/api/config/creditos/${id}`)
  await loadCreditos()
}

// --- Aportaciones ---
const aportacionesList = ref([])
const showAportacionModal = ref(false)
const editingAportacion = ref(null)
const aportacionForm = ref({ category: '', person: '', amount: 0, color: '#1da1f2', frequency: 'semanal' })

function frequencyLabel(freq) {
  const labels = { semanal: 'semana', quincenal: 'quincena', mensual: 'mes' }
  return labels[freq] || 'periodo'
}

async function loadAportaciones() {
  const { data } = await cachedGet('/api/config/aportaciones')
  aportacionesList.value = data
}

function openAportacionModal(item) {
  if (item) {
    editingAportacion.value = item
    aportacionForm.value = { category: item.category, person: item.person, amount: item.amount, color: item.color, frequency: item.frequency || 'semanal' }
  } else {
    editingAportacion.value = null
    aportacionForm.value = { category: '', person: '', amount: 0, color: '#1da1f2', frequency: 'semanal' }
  }
  showAportacionModal.value = true
}

async function saveAportacion() {
  saving.value = true
  try {
    if (editingAportacion.value) {
      await finApi.put(`/api/config/aportaciones/${editingAportacion.value.id}`, aportacionForm.value)
    } else {
      await finApi.post('/api/config/aportaciones', aportacionForm.value)
    }
    showAportacionModal.value = false
    await loadAportaciones()
  } catch (e) { console.error(e) }
  saving.value = false
}

async function deleteAportacion(id) {
  if (!confirm('¿Eliminar esta aportación?')) return
  await finApi.delete(`/api/config/aportaciones/${id}`)
  await loadAportaciones()
}

// --- GI Categories ---
const giCategoriesList = ref([])
const editingGICategory = ref(null)
const giCategoryForm = ref({ name: '' })

async function loadGICategories() {
  const { data } = await cachedGet('/api/gi/categories')
  giCategoriesList.value = data.filter(c => !c.system)
}

function openGICategoryModal(item) {
  if (item) {
    editingGICategory.value = item
    giCategoryForm.value = { name: item.name }
  } else {
    editingGICategory.value = null
    giCategoryForm.value = { name: '' }
  }
  showGICategoryEditModal.value = true
}

async function saveGICategory() {
  saving.value = true
  try {
    if (editingGICategory.value) {
      await finApi.put(`/api/gi/categories/${editingGICategory.value.id}`, giCategoryForm.value)
    } else {
      await finApi.post('/api/gi/categories', giCategoryForm.value)
    }
    showGICategoryEditModal.value = false
    await loadGICategories()
  } catch (e) {
    const detail = e.response?.data?.detail
    if (detail) alert(detail)
    else console.error(e)
  }
  saving.value = false
}

async function deleteGICategory(id) {
  if (!confirm('¿Eliminar esta categoría? Los registros existentes conservarán su categoría.')) return
  await finApi.delete(`/api/gi/categories/${id}`)
  await loadGICategories()
}

onMounted(() => {
  prefsStore.load()
  loadAhorro()
  loadCreditos()
  loadAportaciones()
  loadGICategories()
})
</script>

<style scoped>
.configuracion {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px 40px;
  min-height: calc(100vh - 64px);

  /* Finanzas theme variables (standalone, outside FinanzasLayout) */
  --fin-bg: #eef1f6;
  --fin-bg-2: #f4f6f9;
  --fin-surface: #ffffff;
  --fin-surface-2: #f4f6f9;
  --fin-hover: #e9eef4;
  --fin-border: #dde3ea;
  --fin-text: #1a2733;
  --fin-text-muted: #5e6b7a;

  background-color: var(--fin-bg);
  color: var(--fin-text);
}

.page-title {
  color: var(--fin-text);
  font-size: 1.5rem;
  margin-bottom: 24px;
}

.config-tabs {
  display: flex;
  gap: 4px;
  border-bottom: 1px solid var(--fin-border);
  margin-bottom: 24px;
}

.tab-btn {
  flex: none;
  padding: 12px 18px;
  border: none;
  background: transparent;
  color: var(--fin-text-muted);
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: 500;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: color 0.2s;
  position: relative;
}

.tab-btn:hover { color: var(--fin-text); }

.tab-btn.active {
  color: var(--fin-text);
}

.tab-btn.active::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 12px;
  right: 12px;
  height: 2.5px;
  background-color: var(--fin-text);
  border-radius: 2px;
}

.configuracion.dark-mode .tab-btn.active {
  color: #ffffff;
}

.configuracion.dark-mode .tab-btn.active::after {
  background-color: #ffffff;
}

.configuracion.dark-mode .tab-btn:hover {
  color: #ffffff;
}

.config-section {
  background-color: var(--fin-surface-2);
  border: 1px solid var(--fin-border);
  border-radius: 12px;
  padding: 24px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-header h2 {
  color: var(--fin-text);
  font-size: 1.1rem;
}

.btn-add {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background-color: #1da1f2;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.85rem;
  transition: background-color 0.2s;
}

.btn-add:hover { background-color: #1a91da; }

.config-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.config-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  background-color: var(--fin-hover);
  border-radius: 8px;
  border-left: 4px solid #1da1f2;
}

.config-item-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.config-item-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.config-item-name {
  color: var(--fin-text);
  font-weight: 500;
  display: block;
  font-size: 0.9rem;
}

.config-item-desc {
  color: var(--fin-text-muted);
  font-size: 0.8rem;
  display: block;
  margin-top: 2px;
}

.config-item-actions {
  display: flex;
  gap: 8px;
}

.config-item-actions .btn-edit,
.config-item-actions .btn-delete {
  padding: 6px 10px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.config-item-actions .btn-edit {
  background-color: rgba(29, 161, 242, 0.15);
  color: #1da1f2;
}

.config-item-actions .btn-edit:hover { background-color: rgba(29, 161, 242, 0.3); }

.config-item-actions .btn-delete {
  background-color: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}

.config-item-actions .btn-delete:hover { background-color: rgba(239, 68, 68, 0.3); }

.config-empty {
  color: var(--fin-text-muted);
  text-align: center;
  padding: 32px;
  font-size: 0.9rem;
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background-color: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.modal-box {
  background-color: var(--fin-surface-2);
  border: 1px solid var(--fin-border);
  border-radius: 12px;
  width: 100%;
  max-width: 440px;
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--fin-border);
}

.modal-header h3 {
  color: var(--fin-text);
  font-size: 1rem;
}

.btn-close {
  background: none;
  border: none;
  color: var(--fin-text-muted);
  cursor: pointer;
  font-size: 1.1rem;
}

.btn-close:hover { color: var(--fin-text); }

.modal-body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-field label {
  display: block;
  color: var(--fin-text-muted);
  font-size: 0.8rem;
  margin-bottom: 6px;
}

.form-field input[type="text"],
.form-field input[type="number"],
.form-field select {
  width: 100%;
  padding: 10px 12px;
  background-color: var(--fin-hover);
  border: 1px solid var(--fin-border);
  border-radius: 8px;
  color: var(--fin-text);
  font-size: 0.9rem;
  outline: none;
  transition: border-color 0.2s;
}

.form-field input:focus,
.form-field select:focus { border-color: #1da1f2; }

.color-picker {
  display: flex;
  align-items: center;
  gap: 12px;
}

.color-picker input[type="color"] {
  width: 40px;
  height: 40px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  background: none;
}

.color-preview {
  padding: 4px 12px;
  border-radius: 6px;
  color: white;
  font-size: 0.8rem;
  font-family: monospace;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 16px 20px;
  border-top: 1px solid var(--fin-border);
}

.btn-cancel {
  padding: 8px 16px;
  background: transparent;
  border: 1px solid var(--fin-border);
  color: var(--fin-text-muted);
  border-radius: 8px;
  cursor: pointer;
}

.btn-cancel:hover { border-color: var(--fin-text-muted); color: var(--fin-text); }

.btn-save {
  padding: 8px 16px;
  background-color: #1da1f2;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.85rem;
}

.btn-save:hover { background-color: #1a91da; }
.btn-save:disabled { opacity: 0.5; cursor: not-allowed; }

@media (max-width: 768px) {
  .config-tabs { overflow-x: auto; gap: 0; }
  .tab-btn { flex: none; padding: 10px 12px; font-size: 0.8rem; white-space: nowrap; }

  .configuracion {
    padding: 16px 0;
  }

  .config-section {
    padding: 16px;
  }

  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .btn-add {
    width: 100%;
    justify-content: center;
  }

  .config-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .config-item-actions {
    width: 100%;
    justify-content: flex-end;
  }

  .modal-box {
    max-width: 95vw;
  }
}

/* Panels toggle styles */
.panel-description {
  color: var(--fin-text-muted);
  font-size: 0.85rem;
  margin-bottom: 20px;
}

.panels-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.panel-toggle-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background-color: var(--fin-hover);
  border-radius: 10px;
  transition: background-color 0.2s;
}

.panel-toggle-item:hover {
  background-color: var(--fin-border);
}

.panel-toggle-clickable {
  cursor: pointer;
}

.panel-chevron {
  font-size: 0.7rem;
  margin-left: 4px;
  opacity: 0.5;
}

.panel-toggle-info {
  display: flex;
  align-items: center;
  gap: 14px;
}

.panel-toggle-icon {
  font-size: 1.3rem;
  min-width: 24px;
  text-align: center;
}

.panel-toggle-name {
  display: block;
  color: var(--fin-text);
  font-weight: 500;
  font-size: 0.9rem;
}

.panel-toggle-desc {
  display: block;
  color: var(--fin-text-muted);
  font-size: 0.78rem;
  margin-top: 2px;
}

/* Toggle Switch */
.toggle-switch {
  position: relative;
  display: inline-block;
  width: 44px;
  height: 24px;
  flex-shrink: 0;
}

.toggle-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: var(--fin-border);
  transition: 0.3s;
  border-radius: 24px;
}

.toggle-slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: 0.3s;
  border-radius: 50%;
}

.toggle-switch input:checked + .toggle-slider {
  background-color: #1da1f2;
}

.toggle-switch input:checked + .toggle-slider:before {
  transform: translateX(20px);
}

/* GI Categories compact list */
.gi-cat-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.gi-cat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background-color: var(--fin-hover);
  border-radius: 6px;
}

.gi-cat-name {
  color: var(--fin-text);
  font-size: 0.85rem;
  font-weight: 500;
}

.gi-cat-actions {
  display: flex;
  gap: 6px;
}

.gi-cat-actions .btn-edit,
.gi-cat-actions .btn-delete {
  padding: 4px 8px;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 0.75rem;
  transition: all 0.2s;
}

.gi-cat-actions .btn-edit {
  background-color: rgba(29, 161, 242, 0.15);
  color: #1da1f2;
}

.gi-cat-actions .btn-edit:hover { background-color: rgba(29, 161, 242, 0.3); }

.gi-cat-actions .btn-delete {
  background-color: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}

.gi-cat-actions .btn-delete:hover { background-color: rgba(239, 68, 68, 0.3); }

/* Dark mode variables */
.configuracion.dark-mode {
  --fin-bg: #0f1419;
  --fin-bg-2: #0d1821;
  --fin-surface: #15202b;
  --fin-surface-2: #192734;
  --fin-hover: #1c2b3a;
  --fin-border: #2d3741;
  --fin-text: #e1e8ed;
  --fin-text-muted: #8899a6;
  color-scheme: dark;
}

.configuracion.dark-mode .form-field input,
.configuracion.dark-mode .form-field select {
  color-scheme: dark;
}

.configuracion.dark-mode .form-field select option {
  background-color: #192734;
  color: #e1e8ed;
}
</style>
