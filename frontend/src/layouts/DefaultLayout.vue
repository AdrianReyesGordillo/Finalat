<script setup lang="ts">
</script>

<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-950 flex flex-col">
    <!-- Skip to content link for keyboard navigation -->
    <a
      href="#main-content"
      class="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-[100] focus:rounded-lg focus:bg-indigo-600 focus:px-4 focus:py-2 focus:text-sm focus:font-medium focus:text-white focus:outline-2 focus:outline-offset-2 focus:outline-indigo-500"
    >
      Saltar al contenido principal
    </a>

    <!-- Simple top bar for public pages -->
    <header
      class="h-16 flex items-center justify-center bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 shadow-sm"
      role="banner"
    >
      <a
        href="/"
        class="flex items-center gap-2 text-xl font-bold text-indigo-600 dark:text-indigo-400"
        aria-label="Ir al inicio - Finalat"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          class="h-7 w-7"
          viewBox="0 0 24 24"
          fill="currentColor"
          aria-hidden="true"
        >
          <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
        </svg>
        <span>Finalat</span>
      </a>
    </header>

    <!-- Main content area -->
    <main id="main-content" class="flex-1 flex items-center justify-center p-4" role="main">
      <router-view />
    </main>
  </div>
</template>
