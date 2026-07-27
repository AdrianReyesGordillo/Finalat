<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import StrandsAnimation from '@/components/StrandsAnimation.vue'

const router = useRouter()
const authStore = useAuthStore()

const ADMIN_EMAIL = 'adriax45@gmail.com'
const showPlan = computed(() => authStore.userEmail === ADMIN_EMAIL)

function goToAgent() {
  router.push('/agente')
}

function goToLearn() {
  router.push('/aprende')
}

function goToDashboard() {
  router.push('/finanzas')
}

function goToPlan() {
  router.push('/planes')
}

function goToAdmin() {
  router.push('/admin')
}
</script>

<template>
  <div class="flex flex-col min-h-[calc(100dvh-56px)]">
    <!-- Hero Banner -->
    <section class="relative bg-gradient-to-r from-[#1a2540] via-[#1e3a55] to-[#1a4a4a] overflow-hidden">
      <!-- Decorative curves -->
      <div class="absolute inset-0 pointer-events-none overflow-hidden">
        <svg class="absolute right-0 top-0 w-full h-full" viewBox="0 0 800 400" fill="none" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="none">
          <path d="M400 400C500 350 650 280 800 250" stroke="rgba(255,255,255,0.06)" stroke-width="1.5"/>
          <path d="M350 400C480 330 650 240 800 200" stroke="rgba(255,255,255,0.05)" stroke-width="1.5"/>
          <path d="M300 400C460 310 650 200 800 150" stroke="rgba(255,255,255,0.04)" stroke-width="1.5"/>
          <path d="M250 400C440 290 650 160 800 100" stroke="rgba(255,255,255,0.03)" stroke-width="1.5"/>
        </svg>
      </div>

      <div class="max-w-6xl mx-auto px-4 py-10 md:py-14 lg:py-16 flex flex-col md:flex-row items-center gap-8 relative z-10">
        <!-- Text -->
        <div class="flex-1 text-center md:text-left md:pl-8 lg:pl-12">
          <h1 class="text-3xl sm:text-4xl lg:text-5xl font-bold text-white leading-tight">
            Aprende hoy,<br />
            invierte en tu futuro.
          </h1>
        </div>

        <!-- Strands animation -->
        <div class="flex-1 flex justify-center md:justify-end md:-ml-4">
          <div class="w-72 h-40 sm:w-96 sm:h-48 lg:w-[28rem] lg:h-52 rounded-xl overflow-hidden">
            <StrandsAnimation
              :colors="['#2AAFAA', '#F0A500', '#2D2B6B', '#3DC4BE']"
              :count="5"
              :speed="0.4"
              :amplitude="1.2"
              :waviness="1.2"
              :thickness="0.8"
              :glow="2.8"
              :taper="2.5"
              :spread="1.2"
              :intensity="0.7"
              :saturation="1.6"
              :opacity="0.9"
              :scale="1.4"
            />
          </div>
        </div>
      </div>
    </section>

    <!-- Cards Section -->
    <section class="flex-1 bg-surface-50 pt-5 md:pt-7 lg:pt-8 pb-10 md:pb-14 lg:pb-16 px-4">
      <div class="max-w-5xl mx-auto">
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 md:gap-8">
          <!-- Card: Aprendizaje -->
          <button
            @click="goToLearn"
            class="bg-white rounded-2xl border border-surface-200 shadow-sm hover:shadow-md hover:border-primary-200 transition-all p-3 md:p-4 flex flex-col items-center text-center group cursor-pointer"
          >
            <div class="w-20 h-20 md:w-24 md:h-24 rounded-2xl bg-[#E8F8F7] flex items-center justify-center mb-5 group-hover:scale-105 transition-transform">
              <svg class="w-11 h-11 md:w-14 md:h-14" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
                <!-- Graduation cap - top diamond -->
                <path d="M32 14L8 28L32 42L56 28L32 14Z" fill="#2AAFAA"/>
                <!-- Cap body/band -->
                <path d="M18 33V45C18 45 23 53 32 53C41 53 46 45 46 45V33L32 43L18 33Z" fill="#2AAFAA" opacity="0.7"/>
                <!-- Tassel pole -->
                <rect x="51" y="28" width="2.5" height="20" rx="1.25" fill="#2AAFAA" opacity="0.6"/>
                <!-- Tassel ball -->
                <circle cx="52.25" cy="50" r="3" fill="#2AAFAA" opacity="0.6"/>
              </svg>
            </div>
            <h3 class="text-lg font-bold text-primary-700 mb-2">Cursos</h3>
            <p class="text-sm text-primary-400 leading-relaxed">Cursos y lecciones para dominar tus finanzas personales.</p>
          </button>

          <!-- Card: Agente -->
          <button
            @click="goToAgent"
            class="bg-white rounded-2xl border border-surface-200 shadow-sm hover:shadow-md hover:border-primary-200 transition-all p-3 md:p-4 flex flex-col items-center text-center group cursor-pointer"
          >
            <div class="w-20 h-20 md:w-24 md:h-24 rounded-2xl bg-[#E8F8F7] flex items-center justify-center mb-5 group-hover:scale-105 transition-transform">
              <svg class="w-11 h-11 md:w-14 md:h-14" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
                <!-- Robot head -->
                <rect x="14" y="20" width="36" height="30" rx="6" fill="#2AAFAA"/>
                <!-- Antenna -->
                <rect x="30" y="10" width="4" height="10" rx="2" fill="#2AAFAA" opacity="0.7"/>
                <circle cx="32" cy="8" r="4" fill="#2AAFAA" opacity="0.8"/>
                <!-- Eyes -->
                <circle cx="24" cy="34" r="5" fill="white"/>
                <circle cx="40" cy="34" r="5" fill="white"/>
                <circle cx="24" cy="34" r="2.5" fill="#0f2027"/>
                <circle cx="40" cy="34" r="2.5" fill="#0f2027"/>
                <!-- Mouth -->
                <rect x="24" y="43" width="16" height="3" rx="1.5" fill="white" opacity="0.9"/>
                <!-- Ears -->
                <rect x="8" y="30" width="6" height="12" rx="3" fill="#2AAFAA" opacity="0.6"/>
                <rect x="50" y="30" width="6" height="12" rx="3" fill="#2AAFAA" opacity="0.6"/>
              </svg>
            </div>
            <h3 class="text-lg font-bold text-primary-700 mb-2">Agente</h3>
            <p class="text-sm text-primary-400 leading-relaxed">Tu asesor financiero con IA para tomar mejores decisiones.</p>
          </button>

          <!-- Card: Dashboard Financiero -->
          <button
            @click="goToDashboard"
            class="bg-white rounded-2xl border border-surface-200 shadow-sm hover:shadow-md hover:border-primary-200 transition-all p-3 md:p-4 flex flex-col items-center text-center group cursor-pointer sm:col-span-2 lg:col-span-1"
          >
            <div class="w-20 h-20 md:w-24 md:h-24 rounded-2xl bg-[#FFF7E6] flex items-center justify-center mb-5 group-hover:scale-105 transition-transform">
              <svg class="w-11 h-11 md:w-14 md:h-14" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
                <!-- Trophy cup -->
                <path d="M22 12H42V32C42 40 37.5 46 32 46C26.5 46 22 40 22 32V12Z" fill="#F0A500"/>
                <!-- Cup shine -->
                <path d="M26 16H30V28C30 32 28 34 26 34V16Z" fill="#FFCC44" opacity="0.4"/>
                <!-- Left handle -->
                <path d="M22 16C22 16 14 16 14 22C14 28 20 30 22 30" stroke="#F0A500" stroke-width="4" stroke-linecap="round" fill="none"/>
                <!-- Right handle -->
                <path d="M42 16C42 16 50 16 50 22C50 28 44 30 42 30" stroke="#F0A500" stroke-width="4" stroke-linecap="round" fill="none"/>
                <!-- Stem -->
                <rect x="29" y="46" width="6" height="6" rx="1" fill="#D49200"/>
                <!-- Base -->
                <rect x="24" y="52" width="16" height="4" rx="2" fill="#D49200"/>
                <!-- Star on cup -->
                <path d="M32 22L33.5 26H37.5L34.5 28.5L35.5 32.5L32 30L28.5 32.5L29.5 28.5L26.5 26H30.5L32 22Z" fill="#FFCC44" opacity="0.7"/>
              </svg>
            </div>
            <h3 class="text-lg font-bold text-primary-700 mb-2">Dashboard Financiero</h3>
            <p class="text-sm text-primary-400 leading-relaxed">Dashboard de control de tus finanzas</p>
          </button>
        </div>

        <!-- Cards: Plan Estudiantil + Admin (side by side, admin only) -->
        <div v-if="showPlan" class="flex flex-wrap justify-center gap-4 mt-6 md:mt-8">
          <button
            @click="goToPlan"
            class="bg-white rounded-2xl border border-surface-200 shadow-sm hover:shadow-md hover:border-primary-200 transition-all p-3 md:p-4 flex flex-col items-center text-center group cursor-pointer w-full sm:w-[calc(50%-12px)] lg:w-[calc(33.333%-22px)]"
          >
            <div class="w-20 h-20 md:w-24 md:h-24 rounded-2xl bg-[#F0EAFF] flex items-center justify-center mb-5 group-hover:scale-105 transition-transform">
              <svg class="w-11 h-11 md:w-14 md:h-14" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect x="12" y="14" width="40" height="36" rx="6" fill="#6e6bab"/>
                <path d="M32 24L34.5 30H41L35.5 34L37.5 40L32 36L26.5 40L28.5 34L23 30H29.5L32 24Z" fill="#FFCC44"/>
                <rect x="22" y="44" width="20" height="2.5" rx="1.25" fill="white" opacity="0.5"/>
              </svg>
            </div>
            <h3 class="text-lg font-bold text-primary-700 mb-2">Plan Estudiantil</h3>
            <p class="text-sm text-primary-400 leading-relaxed">Accede a herramientas premium y contenido exclusivo.</p>
          </button>

          <button
            @click="goToAdmin"
            class="bg-white rounded-2xl border border-surface-200 shadow-sm hover:shadow-md hover:border-red-300 transition-all p-3 md:p-4 flex flex-col items-center text-center group cursor-pointer w-full sm:w-[calc(50%-12px)] lg:w-[calc(33.333%-22px)]"
          >
            <div class="w-20 h-20 md:w-24 md:h-24 rounded-2xl bg-red-50 flex items-center justify-center mb-5 group-hover:scale-105 transition-transform">
              <svg class="w-11 h-11 md:w-14 md:h-14" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect x="12" y="16" width="40" height="32" rx="4" fill="#ef4444" opacity="0.8"/>
                <rect x="18" y="24" width="28" height="3" rx="1.5" fill="white" opacity="0.7"/>
                <rect x="18" y="31" width="20" height="3" rx="1.5" fill="white" opacity="0.5"/>
                <rect x="18" y="38" width="24" height="3" rx="1.5" fill="white" opacity="0.5"/>
              </svg>
            </div>
            <h3 class="text-lg font-bold text-primary-700 mb-2">Admin</h3>
            <p class="text-sm text-primary-400 leading-relaxed">Gestionar links de referido</p>
          </button>
        </div>
      </div>
    </section>
  </div>
</template>
