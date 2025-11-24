<template>
  <svg class="user-avatar" :width="size" :height="size" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
    <!-- 蓝色圆形背景 -->
    <circle cx="50" cy="50" r="48" fill="#2B7AB3" stroke="#000" stroke-width="2"/>
    
    <!-- 用户图标 - 简化的人形 -->
    <circle cx="50" cy="35" r="12" fill="#fff"/>
    <path d="M 30 70 Q 30 55 50 55 Q 70 55 70 70" fill="#fff"/>
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
.user-avatar {
  flex-shrink: 0;
}
</style>
