<script setup lang="ts">
import { onMounted, ref } from 'vue'

const props = withDefaults(defineProps<{
  adSlot?: string
  adFormat?: string
  fullWidthResponsive?: boolean
  insStyle?: string
}>(), {
  adSlot: '',
  adFormat: 'auto',
  fullWidthResponsive: true,
  insStyle: 'display:block'
})

const adRef = ref<HTMLElement | null>(null)

onMounted(() => {
  try {
    // @ts-ignore
    ;(window.adsbygoogle = window.adsbygoogle || []).push({})
  } catch (e) {
    console.warn('AdSense not loaded', e)
  }
})
</script>

<template>
  <div ref="adRef" class="ad-container">
    <ins
      class="adsbygoogle"
      :style="props.insStyle"
      data-ad-client="ca-pub-4298163486394678"
      :data-ad-slot="props.adSlot"
      :data-ad-format="props.adFormat"
      :data-full-width-responsive="props.fullWidthResponsive"
    ></ins>
  </div>
</template>

<style scoped>
.ad-container {
  min-height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
