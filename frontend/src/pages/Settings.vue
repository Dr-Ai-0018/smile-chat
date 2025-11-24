<template>
  <div class="settings-page">
    <header class="settings-header">
      <button class="back-btn" @click="$router.back()">
        <span>← 返回</span>
      </button>
      <h1>个人设置</h1>
      <div></div>
    </header>

    <div class="settings-content">
      <!-- 用户信息 -->
      <section class="settings-section">
        <h2>用户信息</h2>
        <div class="user-info">
          <div class="avatar-section">
            <div class="avatar-display" @click="triggerFileUpload">
              <img v-if="profile.avatar" :src="profile.avatar" alt="头像" />
              <div v-else class="avatar-placeholder">
                {{ profile.username?.[0]?.toUpperCase() }}
              </div>
              <div class="avatar-overlay">
                <span>更换头像</span>
              </div>
            </div>
            <input
              ref="fileInput"
              type="file"
              accept="image/*"
              @change="uploadAvatar"
              style="display: none"
            />
          </div>
          <div class="user-details">
            <p><strong>用户名:</strong> {{ profile.username }}</p>
            <p><strong>用户ID:</strong> {{ profile.id }}</p>
          </div>
        </div>
      </section>

      <!-- 聊天设置 -->
      <section class="settings-section">
        <h2>聊天设置</h2>
        <div class="setting-item">
          <label>
            <input type="checkbox" v-model="settings.customBackground" />
            自定义聊天背景
          </label>
        </div>
        <div class="setting-item">
          <label>
            <input type="checkbox" v-model="settings.showTimestamp" />
            显示消息时间戳
          </label>
        </div>
        <div class="setting-item">
          <label>
            <input type="checkbox" v-model="settings.enableNotifications" />
            启用通知
          </label>
        </div>
      </section>

      <!-- 记忆管理 -->
      <section class="settings-section">
        <h2>记忆管理</h2>
        <p class="section-description">
          查看和管理AI助手对你的记忆
        </p>
        <div class="button-group">
          <button @click="viewMemory" class="secondary-btn">
            查看记忆
          </button>
          <button @click="compressMemory" class="secondary-btn">
            压缩记忆
          </button>
        </div>
      </section>

      <!-- 危险操作 -->
      <section class="settings-section danger-zone">
        <h2>危险操作</h2>
        <div class="button-group">
          <button @click="clearHistory" class="danger-btn">
            清空聊天记录
          </button>
          <button @click="logout" class="danger-btn">
            退出登录
          </button>
        </div>
      </section>
    </div>

    <!-- 加载提示 -->
    <div v-if="loading" class="loading-overlay">
      <div class="loading-spinner"></div>
      <p>{{ loadingText }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { userAPI, memoryAPI } from '../api'

const router = useRouter()

const profile = ref({
  id: 0,
  username: '',
  avatar: ''
})

const settings = ref({
  customBackground: false,
  showTimestamp: true,
  enableNotifications: false
})

const loading = ref(false)
const loadingText = ref('')
const fileInput = ref(null)

// 加载用户信息
const loadProfile = async () => {
  try {
    const data = await userAPI.getProfile()
    profile.value = data
  } catch (err) {
    console.error('加载用户信息失败:', err)
  }
}

// 触发文件选择
const triggerFileUpload = () => {
  fileInput.value?.click()
}

// 上传头像
const uploadAvatar = async (event) => {
  const file = event.target.files[0]
  if (!file) return

  // 检查文件大小（不超过5MB）
  if (file.size > 5 * 1024 * 1024) {
    alert('图片大小不能超过5MB')
    return
  }

  loading.value = true
  loadingText.value = '上传头像中...'

  try {
    const formData = new FormData()
    formData.append('file', file)

    const response = await userAPI.uploadAvatar(formData)
    profile.value.avatar = response.avatar
    
    // 更新localStorage
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    user.avatar = response.avatar
    localStorage.setItem('user', JSON.stringify(user))
    
    alert('头像上传成功！')
  } catch (err) {
    console.error('头像上传失败:', err)
    alert('头像上传失败，请重试')
  } finally {
    loading.value = false
  }
}

// 查看记忆
const viewMemory = async () => {
  loading.value = true
  loadingText.value = '加载记忆中...'

  try {
    const memory = await memoryAPI.getMemory(profile.value.id)
    console.log('用户记忆:', memory)
    
    // 简单展示记忆（实际应该有更好的UI）
    let memoryText = '=== 聊天历史 ===\n'
    memory.history.forEach(h => {
      memoryText += `${h.file}:\n${h.content.substring(0, 100)}...\n\n`
    })
    
    memoryText += '\n=== JSON记忆 ===\n'
    memoryText += JSON.stringify(memory.json, null, 2).substring(0, 200) + '...\n\n'
    
    memoryText += '\n=== 长期记忆 ===\n'
    memory.memory.forEach((m, i) => {
      if (i < 3) memoryText += `${m}\n\n`
    })
    
    alert(memoryText)
  } catch (err) {
    console.error('加载记忆失败:', err)
    alert('加载记忆失败')
  } finally {
    loading.value = false
  }
}

// 压缩记忆
const compressMemory = async () => {
  if (!confirm('确定要压缩记忆吗？这将使用AI对历史记录进行总结。')) {
    return
  }

  loading.value = true
  loadingText.value = '压缩记忆中...'

  try {
    await memoryAPI.compressMemory(profile.value.id)
    alert('记忆压缩成功！')
  } catch (err) {
    console.error('压缩记忆失败:', err)
    alert('压缩记忆失败')
  } finally {
    loading.value = false
  }
}

// 清空聊天记录
const clearHistory = () => {
  if (confirm('确定要清空所有聊天记录吗？此操作无法撤销！')) {
    // TODO: 实现清空历史的API
    alert('清空功能开发中')
  }
}

// 退出登录
const logout = () => {
  if (confirm('确定要退出登录吗？')) {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    router.push('/login')
  }
}

onMounted(() => {
  loadProfile()
  
  // 从localStorage加载设置
  const savedSettings = localStorage.getItem('chat_settings')
  if (savedSettings) {
    settings.value = JSON.parse(savedSettings)
  }
})

// 监听设置变化并保存
const saveSettings = () => {
  localStorage.setItem('chat_settings', JSON.stringify(settings.value))
}
</script>

<style scoped>
.settings-page {
  min-height: 100vh;
  background: var(--color-bg-light);
}

.settings-header {
  background: var(--color-primary);
  padding: 1rem 1.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.settings-header h1 {
  font-size: 1.5rem;
  margin: 0;
}

.back-btn {
  background: transparent;
  border: none;
  font-size: 1rem;
  cursor: pointer;
  padding: 0.5rem;
  color: var(--color-dark);
}

.settings-content {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem 1.5rem;
}

.settings-section {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  margin-bottom: 1.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.settings-section h2 {
  margin: 0 0 1.5rem 0;
  font-size: 1.25rem;
  color: var(--color-dark);
}

.section-description {
  color: #666;
  margin-bottom: 1rem;
}

/* 用户信息 */
.user-info {
  display: flex;
  align-items: center;
  gap: 2rem;
}

.avatar-section {
  position: relative;
}

.avatar-display {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  overflow: hidden;
  cursor: pointer;
  position: relative;
  border: 3px solid var(--color-primary);
}

.avatar-display img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  width: 100%;
  height: 100%;
  background: var(--color-accent);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2.5rem;
  font-weight: 600;
}

.avatar-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s;
  font-size: 0.85rem;
}

.avatar-display:hover .avatar-overlay {
  opacity: 1;
}

.user-details p {
  margin: 0.5rem 0;
  color: var(--color-dark);
}

/* 设置项 */
.setting-item {
  padding: 1rem 0;
  border-bottom: 1px solid #e0e0e0;
}

.setting-item:last-child {
  border-bottom: none;
}

.setting-item label {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  cursor: pointer;
  font-size: 1rem;
}

.setting-item input[type="checkbox"] {
  width: 20px;
  height: 20px;
  cursor: pointer;
}

/* 按钮组 */
.button-group {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.secondary-btn {
  background: var(--color-accent);
  color: white;
}

.secondary-btn:hover {
  background: #1e5f8a;
}

.danger-btn {
  background: #dc3545;
  color: white;
}

.danger-btn:hover {
  background: #c82333;
}

.danger-zone {
  border: 2px solid #dc3545;
}

/* 加载覆盖层 */
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  color: white;
}

.loading-spinner {
  width: 50px;
  height: 50px;
  border: 4px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-overlay p {
  margin-top: 1rem;
  font-size: 1.1rem;
}

@media (max-width: 768px) {
  .user-info {
    flex-direction: column;
    text-align: center;
  }
  
  .button-group {
    flex-direction: column;
  }
  
  .button-group button {
    width: 100%;
  }
}
</style>
