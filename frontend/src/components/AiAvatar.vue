<template>
  <svg class="ai-avatar" :width="size" :height="size" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
    <g transform="rotate(-15 50 50)">
      <!-- 黄色圆形背景 - 无边框 -->
      <circle cx="50" cy="50" r="48" fill="#FDD152"/>
      
      <!-- 笑脸眼睛 -->
      <circle cx="35" cy="40" r="4" fill="#000"/>
      <circle cx="65" cy="40" r="4" fill="#000"/>
      
      <!-- 笑脸嘴巴 -->
      <path d="M 30 55 Q 50 70 70 55" stroke="#000" stroke-width="3" fill="none" stroke-linecap="round"/>
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
.ai-avatar {
  flex-shrink: 0;
}
</style>
