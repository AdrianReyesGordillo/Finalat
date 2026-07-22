<script setup lang="ts">
/**
 * AsesorPage — Full-page wrapper for the Fina AI Advisor chat interface.
 * Houses the ChatWindow component within a flex layout that fills the available height.
 */
import ChatWindow from '../components/advisor/ChatWindow.vue'
</script>

<template>
  <div class="flex h-full flex-col">
    <!-- Page header -->
    <div class="flex items-center justify-between border-b border-gray-200 bg-white px-6 py-4 dark:border-gray-700 dark:bg-gray-900">
      <div>
        <h1 class="text-xl font-bold text-gray-900 dark:text-gray-100">Asesor Fina</h1>
        <p class="text-sm text-gray-600 dark:text-gray-400">
          Tu asesora financiera impulsada por IA
        </p>
      </div>
    </div>

    <!-- Chat window fills remaining space -->
    <div class="flex-1 overflow-hidden">
      <ChatWindow />
    </div>
  </div>
</template>
