<script setup lang="ts">
import { ref } from 'vue'

const showAlert = ref(false)

function handleLockedClick() {
  showAlert.value = true
}

function closeAlert() {
  showAlert.value = false
}
</script>

<template>
  <div class="min-h-[calc(100dvh-4rem)] bg-surface-50 py-10 px-4">
    <div class="max-w-3xl mx-auto">
      <!-- Header -->
      <div class="text-center mb-10">
        <div class="w-16 h-16 mx-auto rounded-2xl bg-[#FFF7E6] flex items-center justify-center mb-4">
          <svg class="w-9 h-9" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M22 12H42V32C42 40 37.5 46 32 46C26.5 46 22 40 22 32V12Z" fill="#F0A500"/>
            <path d="M26 16H30V28C30 32 28 34 26 34V16Z" fill="#FFCC44" opacity="0.4"/>
            <path d="M22 16C22 16 14 16 14 22C14 28 20 30 22 30" stroke="#F0A500" stroke-width="4" stroke-linecap="round" fill="none"/>
            <path d="M42 16C42 16 50 16 50 22C50 28 44 30 42 30" stroke="#F0A500" stroke-width="4" stroke-linecap="round" fill="none"/>
            <rect x="29" y="46" width="6" height="6" rx="1" fill="#D49200"/>
            <rect x="24" y="52" width="16" height="4" rx="2" fill="#D49200"/>
            <path d="M32 22L33.5 26H37.5L34.5 28.5L35.5 32.5L32 30L28.5 32.5L29.5 28.5L26.5 26H30.5L32 22Z" fill="#FFCC44" opacity="0.7"/>
          </svg>
        </div>
        <h1 class="text-2xl sm:text-3xl font-bold text-primary-700 mb-2">Dashboard Financiero</h1>
        <p class="text-sm text-gray-500 max-w-md mx-auto">
          Controla tus finanzas desde donde quieras, con nuestro portal personalizable web.
        </p>
      </div>

      <!-- App Preview Card -->
      <div class="bg-white rounded-2xl border border-surface-200 shadow-sm p-6 sm:p-8 mb-8">
        <div class="flex flex-col sm:flex-row items-center gap-6">
          <!-- Portal icon -->
          <div class="w-24 h-24 rounded-3xl bg-gradient-to-br from-[#2AAFAA] to-[#1a8a85] flex items-center justify-center shadow-lg flex-shrink-0">
            <svg class="w-12 h-12 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
            </svg>
          </div>

          <div class="text-center sm:text-left flex-1">
            <h2 class="text-lg font-bold text-primary-700 mb-1">Finalat Dashboard</h2>
            <p class="text-sm text-gray-500 mb-3">
              Portal financiero web con seguimiento de gastos, metas de ahorro e inversiones — totalmente personalizable.
            </p>
            <div class="flex flex-wrap gap-2 justify-center sm:justify-start">
              <span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-[#E8F8F7] text-xs font-medium text-[#1a8a85]">
                <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/></svg>
                Personalizable
              </span>
              <span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-[#E8F8F7] text-xs font-medium text-[#1a8a85]">
                <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/></svg>
                Acceso web
              </span>
              <span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-[#E8F8F7] text-xs font-medium text-[#1a8a85]">
                <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/></svg>
                Sincronización en la nube
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Download Button (Locked) -->
      <div class="flex justify-center">
        <button
          @click="handleLockedClick"
          @mouseenter="handleLockedClick"
          class="relative flex items-center gap-3 px-8 py-4 rounded-2xl bg-gray-100 border-2 border-dashed border-gray-300 text-gray-400 font-semibold cursor-not-allowed transition-colors hover:border-gray-400 hover:bg-gray-50"
        >
          <!-- Lock icon -->
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
          </svg>
          <span>Comenzar</span>
        </button>
      </div>

      <!-- Subscription Alert -->
      <Transition
        enter-active-class="transition duration-200 ease-out"
        enter-from-class="opacity-0 translate-y-2"
        enter-to-class="opacity-100 translate-y-0"
        leave-active-class="transition duration-150 ease-in"
        leave-from-class="opacity-100 translate-y-0"
        leave-to-class="opacity-0 translate-y-2"
      >
        <div
          v-if="showAlert"
          class="fixed inset-0 z-50 flex items-center justify-center px-4"
          @click.self="closeAlert"
        >
          <!-- Backdrop -->
          <div class="absolute inset-0 bg-black/30" @click="closeAlert"></div>

          <!-- Alert card -->
          <div class="relative bg-white rounded-2xl shadow-xl border border-surface-200 p-6 sm:p-8 max-w-sm w-full text-center">
            <!-- Close button -->
            <button
              @click="closeAlert"
              class="absolute top-3 right-3 w-8 h-8 flex items-center justify-center rounded-full text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
              aria-label="Cerrar"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>

            <!-- Lock icon -->
            <div class="w-14 h-14 mx-auto rounded-full bg-accent-50 flex items-center justify-center mb-4">
              <svg class="w-7 h-7 text-accent-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
              </svg>
            </div>

            <h3 class="text-lg font-bold text-primary-700 mb-2">Contenido bloqueado</h3>
            <p class="text-sm text-gray-500 leading-relaxed">
              Para acceder a este producto debes suscribirte al <strong class="text-primary-700">Plan Estudiantil</strong>.
            </p>

            <!-- CTA button -->
            <button
              @click="closeAlert"
              class="mt-6 w-full px-6 py-3 rounded-xl bg-[#2AAFAA] hover:bg-[#239e99] text-white text-sm font-semibold transition-colors"
            >
              Entendido
            </button>
          </div>
        </div>
      </Transition>
    </div>
  </div>
</template>
