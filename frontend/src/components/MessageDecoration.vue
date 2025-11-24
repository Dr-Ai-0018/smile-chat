<template>
  <svg class="message-decoration" :width="size" :height="size" viewBox="0 0 30 30" xmlns="http://www.w3.org/2000/svg">
    <g v-if="type === 'ai'">
      <!-- AI消息装饰 - 左下角橙色小星星 -->
      <path d="M 8 15 L 10 10 L 12 15 L 17 17 L 12 19 L 10 24 L 8 19 L 3 17 Z" 
            fill="#FFA500" 
            stroke="#F4A500" 
            stroke-width="1"/>
      <circle cx="10" cy="17" r="1.5" fill="#FFD700"/>
    </g>
    
    <g v-if="type === 'user'">
      <!-- 用户消息装饰 - 右上角蓝色音符 -->
      <g transform="translate(12, 5)">
        <circle cx="0" cy="10" r="3" fill="#2B7AB3"/>
        <rect x="3" y="0" width="1.5" height="10" fill="#2B7AB3"/>
        <path d="M 4.5 0 Q 8 2 4.5 4" fill="#2B7AB3"/>
      </g>
    </g>
  </svg>
</template>

<script setup>
defineProps({
  type: {
    type: String,
    required: true,
    validator: (value) => ['ai', 'user'].includes(value)
  },
  size: {
    type: Number,
    default: 60
  }
})
</script>

<style scoped>
.message-decoration {
  position: absolute;
  pointer-events: none;
}
</style>
