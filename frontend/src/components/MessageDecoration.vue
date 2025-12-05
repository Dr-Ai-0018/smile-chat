<template>
  <svg class="message-decoration" :width="size" :height="size" viewBox="0 0 30 30" xmlns="http://www.w3.org/2000/svg">
    <g v-if="type === 'ai'">
      <!-- AI消息装饰 - 星星（金黄色） -->
      <g transform="translate(5, 5)">
        <path d="M 10 2 L 12 7 L 18 8 L 13 12 L 14.5 18 L 10 14.5 L 5.5 18 L 7 12 L 2 8 L 8 7 Z" 
              fill="#FDD152" 
              stroke="#F4A500" 
              stroke-width="1"/>
        <circle cx="10" cy="9" r="1.5" fill="#FFF" opacity="0.7"/>
      </g>
    </g>
    
    <g v-if="type === 'user'">
      <!-- 用户消息装饰 - 四角星（蓝色） -->
      <g transform="translate(5, 5)">
        <path d="M 10 2 L 12 8 L 18 10 L 12 12 L 10 18 L 8 12 L 2 10 L 8 8 Z" 
              fill="#6BB8D9" 
              stroke="#2B7AB3" 
              stroke-width="1"/>
        <circle cx="10" cy="10" r="1.5" fill="#FFF" opacity="0.7"/>
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
