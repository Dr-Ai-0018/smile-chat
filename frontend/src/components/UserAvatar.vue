<template>
  <div class="user-avatar-container" :style="{ width: size + 'px', height: size + 'px' }">
    <!-- 有头像时显示真实头像 -->
    <img 
      v-if="avatarUrl" 
      :src="avatarUrl" 
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
import { ref, onMounted } from 'vue'
import { userAPI } from '../api'

const props = defineProps({
  size: {
    type: Number,
    default: 40
  }
})

const avatarUrl = ref('')
const imageError = ref(false)

// 全局缓存，避免重复请求
let avatarCache = null
let cacheTime = 0
const CACHE_DURATION = 60000 // 缓存1分钟

// 获取头像URL
const loadAvatar = async () => {
  if (imageError.value) return
  
  const now = Date.now()
  
  // 如果有缓存且未过期，直接使用
  if (avatarCache && (now - cacheTime) < CACHE_DURATION) {
    avatarUrl.value = avatarCache
    return
  }
  
  try {
    const profile = await userAPI.getProfile()
    if (profile && profile.avatar) {
      const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
      avatarUrl.value = `${baseUrl}${profile.avatar}?t=${now}`
      
      // 更新缓存
      avatarCache = avatarUrl.value
      cacheTime = now
      
      // 同步更新localStorage
      const user = JSON.parse(localStorage.getItem('user') || '{}')
      user.avatar = profile.avatar
      localStorage.setItem('user', JSON.stringify(user))
    }
  } catch (err) {
    console.error('获取头像失败:', err)
    // 尝试从localStorage读取
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    if (user.avatar) {
      const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
      avatarUrl.value = `${baseUrl}${user.avatar}?t=${now}`
      avatarCache = avatarUrl.value
      cacheTime = now
    }
  }
}

const handleImageError = () => {
  imageError.value = true
  avatarUrl.value = ''
  avatarCache = null
}

onMounted(() => {
  loadAvatar()
})

// 暴露刷新方法
defineExpose({ loadAvatar })
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
