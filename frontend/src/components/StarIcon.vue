<template>
  <svg class="star-icon" :width="size" :height="size" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <linearGradient id="starGradient" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" style="stop-color:#FDD152;stop-opacity:1" />
        <stop offset="100%" style="stop-color:#F4C430;stop-opacity:1" />
      </linearGradient>
      <filter id="starShadow">
        <feGaussianBlur in="SourceAlpha" stdDeviation="2"/>
        <feOffset dx="2" dy="2" result="offsetblur"/>
        <feComponentTransfer>
          <feFuncA type="linear" slope="0.3"/>
        </feComponentTransfer>
        <feMerge>
          <feMergeNode/>
          <feMergeNode in="SourceGraphic"/>
        </feMerge>
      </filter>
    </defs>
    <g transform="rotate(-15 50 50)">
      <path d="M 50 5 L 58 38 L 92 38 L 65 57 L 73 90 L 50 71 L 27 90 L 35 57 L 8 38 L 42 38 Z" 
            fill="url(#starGradient)" 
            stroke="#F4A500" 
            stroke-width="1.5"
            filter="url(#starShadow)"/>
      <!-- 高光效果 -->
      <path d="M 50 8 L 55 30" stroke="#FFF" stroke-width="2" opacity="0.6" stroke-linecap="round"/>
    </g>
  </svg>
</template>

<script setup>
defineProps({
  size: {
    type: Number,
    default: 40
  }
})
</script>

<style scoped>
.star-icon {
  flex-shrink: 0;
}
</style>
