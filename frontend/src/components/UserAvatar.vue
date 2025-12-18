<template>
  <div class="user-avatar-container" :style="{ width: size + 'px', height: size + 'px' }">
    <!-- 有头像时显示真实头像 -->
    <img 
      v-if="displayUrl" 
      :src="displayUrl" 
      class="user-avatar-img"
      @error="handleImageError"
    />
    <!-- 无头像时显示默认蓝色图标 -->
    <svg v-else class="user-avatar-default" :width="size" :height="size" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
      <!-- 蓝色圆形背景带边框 -->
      <circle cx="50" cy="50" r="46" fill="white" stroke="#2B7AB3" stroke-width="4"/>
      
      <!-- 波浪图标 M形 -->
      <path 
        d="M 22 55 
           Q 28 35, 38 55 
           Q 48 75, 58 50 
           Q 68 25, 78 50"
        stroke="#2B7AB3" 
        stroke-width="6" 
        fill="none" 
        stroke-linecap="round"
        stroke-linejoin="round"/>
    </svg>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const props = defineProps({
  size: {
    type: Number,
    default: 40
  },
  // 外部传入的头像URL（优先使用）
  avatarUrl: {
    type: String,
    default: ''
  }
})

const imageError = ref(false)
const localUrl = ref('')

// 计算最终显示的URL（优先用prop传入的，否则用本地读取的）
const displayUrl = computed(() => {
  if (imageError.value) return ''
  return props.avatarUrl || localUrl.value
})

// 从localStorage读取（作为备选）
const loadFromLocal = () => {
  try {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    if (user.avatar) {
      // avatar已经是 /uploads/avatars/xxx 格式的相对路径，直接使用
      localUrl.value = user.avatar
    }
  } catch {
    localUrl.value = ''
  }
}

const handleImageError = () => {
  imageError.value = true
}

onMounted(() => {
  // 如果没传avatarUrl，从本地读取
  if (!props.avatarUrl) {
    loadFromLocal()
  }
})
</script>

<style scoped>
.user-avatar-container {
  flex-shrink: 0;
  border-radius: 50%;
  overflow: hidden;
}

.user-avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 50%;
  border: 2px solid #6BB8D9;
}

.user-avatar-default {
  display: block;
}
</style>
