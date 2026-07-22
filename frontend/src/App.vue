<script setup lang="ts">
import ErrorAlert from './components/ui/ErrorAlert.vue'
</script>

<template>
  <!-- Global error/notification alerts (API toast notifications) -->
  <ErrorAlert />

  <router-view />
</template>
