<template>
  <div class="chat-page">
    <!-- 顶部标题栏 -->
    <header class="chat-header">
      <button class="menu-btn" @click="showMenu = !showMenu">
        <span class="menu-icon">☰</span>
      </button>
      <div class="header-center">
        <h1 class="title">
          启明
          <span v-if="isTyping" class="typing-indicator">正在输入中...</span>
        </h1>
      </div>
      <!-- 计时器显示 -->
      <div v-if="chatStartTime" class="timer-display" :class="{ warning: showTimeWarning }">
        <span class="timer-icon">⏱</span>
        <span class="timer-value">{{ formatRemainingTime() }}</span>
      </div>
      <button class="settings-btn" @click="$router.push('/settings')">
        <span>⚙</span>
      </button>
    </header>

    <!-- 侧边栏菜单 -->
    <div class="sidebar" :class="{ show: showMenu }">
      <div class="sidebar-header">
        <h3>菜单</h3>
        <button @click="showMenu = false" class="close-btn">×</button>
      </div>
      <nav class="sidebar-nav">
        <a href="#" @click.prevent="showAbout">ℹ️ 关于启明</a>
        <a href="#" @click.prevent="goToSettings">⚙️ 个人设置</a>
        <a href="#" @click.prevent="logout">🚪 退出登录</a>
      </nav>
    </div>
    
    <!-- 侧边栏遮罩 -->
    <div v-if="showMenu" class="sidebar-overlay" @click="showMenu = false"></div>

    <!-- 聊天消息区域 -->
    <div class="chat-messages" ref="messagesContainer">
      <div v-if="messages.length === 0" class="empty-state">
        <AiAvatar :size="60" />
        <p class="greeting">{{ currentGreeting }}，{{ user.username }}！</p>
        <p class="intro">我是启明，你有什么想和我聊的吗？</p>
      </div>

      <div v-for="(msg, index) in messages" :key="msg.id || index" class="message-group">
        <!-- 时间戳 -->
        <div v-if="shouldShowTimestamp(index)" class="timestamp">
          {{ formatTimestamp(msg.timestamp) }}
        </div>

        <!-- 消息 -->
        <div class="message" :class="msg.role">
          <!-- AI消息：头像在左 -->
          <template v-if="msg.role === 'assistant'">
            <AiAvatar :size="40" />
            <div class="message-body">
              <div v-if="msg.content" class="message-content-wrapper assistant">
                <MessageDecoration type="ai" :size="30" class="bubble-decoration" />
                <div class="message-content assistant">
                  <div v-html="renderMarkdown(msg.content)"></div>
                </div>
              </div>
            </div>
          </template>
          
          <!-- 用户消息：头像在右 -->
          <template v-else>
            <div class="message-body">
              <!-- 纯图片消息 - 无气泡直接展示（只有图片没有文字时显示） -->
              <div v-if="msg.image && isValidImage(msg.image)" class="image-message">
                <img :src="msg.image" @click="previewImage(msg.image)" />
              </div>
              <!-- 文字消息 - 不带图片 -->
              <div v-if="msg.content" class="message-content-wrapper user">
                <MessageDecoration type="user" :size="30" class="bubble-decoration" />
                <div class="message-content user">
                  <div v-html="renderMarkdown(msg.content)"></div>
                </div>
              </div>
            </div>
            <UserAvatar :size="40" :avatarUrl="userAvatarUrl" />
          </template>
        </div>
      </div>

      <!-- 加载中指示器 -->
      <div v-if="loading && !isStreaming" class="message assistant">
        <AiAvatar :size="40" />
        <div class="message-content-wrapper assistant">
          <MessageDecoration type="ai" :size="30" class="bubble-decoration" />
          <div class="message-content assistant loading">
            <span class="loading-dot"></span>
            <span class="loading-dot"></span>
            <span class="loading-dot"></span>
          </div>
        </div>
      </div>
    </div>

    <!-- 输入区域 -->
    <div class="chat-input-area">
      <div class="input-divider">
        <svg class="star-deco" width="50" height="50" viewBox="0 0 50 50" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <filter id="starGlow">
              <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
              <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>
          </defs>
          <g transform="rotate(-20 25 25)">
            <path d="M 25 5 L 28 18 L 42 18 L 31 26 L 34 39 L 25 31 L 16 39 L 19 26 L 8 18 L 22 18 Z" 
                  fill="#FDD152" 
                  stroke="#F4A500" 
                  stroke-width="2"
                  filter="url(#starGlow)"/>
            <circle cx="25" cy="20" r="2" fill="#FFF" opacity="0.8"/>
          </g>
        </svg>
        <div class="divider-line"></div>
      </div>
      <div class="input-container">
        <button class="icon-btn attach-btn" @click="triggerImageUpload" title="发送图片">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
            <circle cx="8.5" cy="8.5" r="1.5"/>
            <polyline points="21 15 16 10 5 21"/>
          </svg>
        </button>
        <input
          ref="imageInput"
          type="file"
          accept="image/*"
          @change="handleImageSelect"
          style="display: none"
        />
        <input
          type="text"
          v-model="inputMessage"
          @keydown.enter.exact.prevent="sendMessage"
          placeholder="输入消息..."
          ref="inputElement"
          class="message-input"
        />
        <button class="icon-btn send-btn" @click="sendMessage" :disabled="!canSend">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M22 2L11 13"/>
            <path d="M22 2L15 22L11 13L2 9L22 2Z"/>
          </svg>
        </button>
      </div>
    </div>
    
    <!-- 图片预览 -->
    <Transition name="fade">
      <div v-if="previewImageUrl" class="image-preview-overlay" @click="previewImageUrl = null">
        <img :src="previewImageUrl" @click.stop />
        <button class="close-preview" @click="previewImageUrl = null">×</button>
      </div>
    </Transition>

    <!-- 计时器提示气泡 -->
    <Transition name="slide-up">
      <div v-if="showTimeWarning && !chatEnded" class="time-warning-bubble">
        <span class="warning-icon">⏰</span>
        <span class="warning-text">聊天即将结束</span>
        <span class="warning-time">{{ formatRemainingTime() }}</span>
      </div>
    </Transition>

    <!-- 聊天结束遮罩 -->
    <Transition name="fade">
      <div v-if="chatEnded" class="chat-ended-overlay">
        <div class="ended-card">
          <div class="ended-icon">🌙</div>
          <h2>今日聊天时间已结束</h2>
          <p>感谢你今天的陪伴，明天再来和我聊天吧~</p>
          <p class="ended-hint">每天的聊天时间为16分钟</p>
          <button class="ended-btn" @click="$router.push('/settings')">去设置页面</button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, computed, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { chatAPI, userAPI } from '../api'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { toast, confirm } from '../utils/toast'
import AiAvatar from '../components/AiAvatar.vue'
import UserAvatar from '../components/UserAvatar.vue'
import MessageDecoration from '../components/MessageDecoration.vue'

const router = useRouter()
const user = ref(JSON.parse(localStorage.getItem('user') || '{}'))

// 消息列表
const messages = ref([])
const inputMessage = ref('')
const loading = ref(false)
const isTyping = ref(false)
const isStreaming = ref(false)
const showMenu = ref(false)
const messagesContainer = ref(null)
const inputElement = ref(null)
const imageInput = ref(null)
const previewImageUrl = ref(null)

// 请求控制
let currentAbortController = null
let hasPendingAfterStream = false

// 用户头像URL（全页面共享，避免重复请求）
const userAvatarUrl = ref('')

// 聊天计时系统
const CHAT_DURATION_WARNING = 15 * 60 * 1000  // 15分钟提示
const CHAT_DURATION_LIMIT = 16 * 60 * 1000    // 16分钟强制结束
const chatStartTime = ref(null)
const chatElapsedTime = ref(0)
const showTimeWarning = ref(false)
const chatEnded = ref(false)
let timerInterval = null

// 计算是否可以发送（loading时也可以发，用于中断当前请求）
const canSend = computed(() => {
  return inputMessage.value.trim().length > 0
})

// 根据时间显示问候语
const currentGreeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 6) return '夜深了'
  if (hour < 9) return '早上好'
  if (hour < 12) return '上午好'
  if (hour < 14) return '中午好'
  if (hour < 18) return '下午好'
  return '晚上好'
})

// 生成消息ID
const generateId = () => Date.now().toString(36) + Math.random().toString(36).substr(2)

// ==================== 聊天计时系统 ====================
const getTimerStorageKey = () => `chat_timer_${user.value.id}`

const loadTimerState = () => {
  const key = getTimerStorageKey()
  const stored = localStorage.getItem(key)
  if (stored) {
    try {
      const data = JSON.parse(stored)
      // 检查是否是今天的记录（每天重置）
      const storedDate = new Date(data.startTime).toDateString()
      const today = new Date().toDateString()
      if (storedDate === today) {
        chatStartTime.value = data.startTime
        // 计算已过时间
        const elapsed = Date.now() - data.startTime
        if (elapsed >= CHAT_DURATION_LIMIT) {
          chatEnded.value = true
        }
        return true
      } else {
        // 新的一天，清除旧记录
        localStorage.removeItem(key)
      }
    } catch (e) {
      localStorage.removeItem(key)
    }
  }
  return false
}

const saveTimerState = () => {
  if (chatStartTime.value) {
    const key = getTimerStorageKey()
    localStorage.setItem(key, JSON.stringify({
      startTime: chatStartTime.value
    }))
  }
}

const startChatTimer = () => {
  if (chatStartTime.value) return // 已经开始了
  
  chatStartTime.value = Date.now()
  saveTimerState()
  startTimerInterval()
}

const startTimerInterval = () => {
  if (timerInterval) return
  
  timerInterval = setInterval(() => {
    if (!chatStartTime.value) return
    
    chatElapsedTime.value = Date.now() - chatStartTime.value
    
    // 15分钟提示
    if (chatElapsedTime.value >= CHAT_DURATION_WARNING && !showTimeWarning.value && !chatEnded.value) {
      showTimeWarning.value = true
      toast.info('聊天即将结束，还有约1分钟哦~', 5000)
    }
    
    // 16分钟强制结束
    if (chatElapsedTime.value >= CHAT_DURATION_LIMIT && !chatEnded.value) {
      chatEnded.value = true
      stopTimerInterval()
    }
  }, 1000)
}

const stopTimerInterval = () => {
  if (timerInterval) {
    clearInterval(timerInterval)
    timerInterval = null
  }
}

const formatRemainingTime = () => {
  const remaining = Math.max(0, CHAT_DURATION_LIMIT - chatElapsedTime.value)
  const minutes = Math.floor(remaining / 60000)
  const seconds = Math.floor((remaining % 60000) / 1000)
  return `${minutes}:${seconds.toString().padStart(2, '0')}`
}

const normalizeSegment = (content) => {
  if (!content) return ''
  return String(content).replace(/。\s*$/, '')
}

// 加载聊天历史
const loadHistory = async () => {
  try {
    const response = await chatAPI.getHistory(100)
    if (response.history && response.history.length > 0) {
      messages.value = response.history.map(msg => ({
        id: msg.id || generateId(),
        role: msg.role,
        content: msg.content,
        image: msg.image || null,
        timestamp: new Date(msg.timestamp)
      }))
    }
    scrollToBottom()
  } catch (err) {
    console.error('加载历史失败:', err)
  }
}

// 发送消息（核心逻辑）
const sendMessage = async (imageBase64 = null) => {
  // 检查聊天是否已结束
  if (chatEnded.value) {
    toast.error('今日聊天时间已用完，明天再来吧~')
    return
  }
  
  const textContent = inputMessage.value.trim()
  
  // 如果没有内容和图片，直接返回
  if (!textContent && !imageBase64) return
  
  // 第一次发送消息时启动计时器
  if (!chatStartTime.value) {
    startChatTimer()
  }
  
  // 清空输入
  inputMessage.value = ''
  
  // 添加用户消息（无论什么状态都先添加）
  const userMsg = {
    id: generateId(),
    role: 'user',
    content: textContent || '',
    image: imageBase64 || null,
    timestamp: new Date()
  }
  messages.value.push(userMsg)
  scrollToBottom()
  
  // 情况1：AI正在等待回复（loading但还没开始流式输出）
  // → 立即中断当前请求，重新发送包含新消息的请求
  if (loading.value && !isStreaming.value) {
    console.log('AI等待中，中断并重新发送')
    // 取消当前请求
    if (currentAbortController) {
      currentAbortController.abort()
      currentAbortController = null
    }
    loading.value = false
    isTyping.value = false
    // 重新发送请求（包含刚添加的新消息）
    await requestAIResponse()
    return
  }
  
  // 情况2：AI正在流式输出
  // → 顺序处理，等AI输出完再发送
  if (isStreaming.value) {
    hasPendingAfterStream = true
    toast.info('消息已排队，等待当前回复完成')
    return
  }
  
  // 情况3：空闲状态，直接发送
  await requestAIResponse()
}

// 请求AI回复
const requestAIResponse = async () => {
  loading.value = true
  isTyping.value = true
  
  // 创建新的AbortController
  currentAbortController = new AbortController()
  
  try {
    // 收集最近的消息（包含图片）
    const recentMessages = collectRecentMessages()
    
    const response = await chatAPI.sendMessageWithContext(recentMessages, {
      signal: currentAbortController.signal
    })
    
    // 开始流式渲染
    isStreaming.value = true
    loading.value = false
    isTyping.value = false
    
    // 检查是否有 segments（多条消息分开显示）
    const segments = response.segments && response.segments.length > 0
      ? response.segments
      : [response.reply || response.content || '']
    
    // 逐条显示每个 segment
    for (let i = 0; i < segments.length; i++) {
      let segmentContent = segments[i]
      if (!segmentContent) continue
      segmentContent = normalizeSegment(segmentContent)
      
      // 添加AI回复消息
      const aiMsg = {
        id: generateId(),
        role: 'assistant',
        content: '',
        timestamp: new Date()
      }
      messages.value.push(aiMsg)
      const msgIndex = messages.value.length - 1
      
      // 流式渲染当前 segment
      await streamRenderMessage(segmentContent, msgIndex)
      
      // 如果还有下一条，稍作停顿（模拟多条消息发送）
      if (i < segments.length - 1) {
        await new Promise(resolve => setTimeout(resolve, 400))
      }
    }
    
    isStreaming.value = false
    
    // 如果期间有新的用户消息，按顺序在当前回复完成后再请求AI
    if (hasPendingAfterStream) {
      hasPendingAfterStream = false
      await requestAIResponse()
    }
    
  } catch (err) {
    const status = err?.response?.status
    const isCanceled = err?.code === 'ERR_CANCELED' || err?.name === 'AbortError'
    const isTimeout = err?.code === 'ECONNABORTED' || /timeout/i.test(err?.message || '')
    const isNetworkError = !status && (err?.code === 'ERR_NETWORK' || /network error/i.test(err?.message || ''))
    if (isCanceled || status === 499) {
      console.log('请求已取消/被新消息中断')
    } else if (isTimeout || isNetworkError) {
      const reason = isTimeout ? '超时' : '网络异常'
      console.error(`请求${reason}:`, err)
      toast.error(`等待回复${reason}，已自动刷新对话历史`)
      try {
        await loadHistory()
      } catch (refreshErr) {
        console.error(`${reason}后刷新历史失败:`, refreshErr)
      }
    } else {
      console.error('发送消息失败:', err)
      toast.error('消息发送失败，请重试')
    }
    loading.value = false
    isTyping.value = false
    isStreaming.value = false
  }
  
  currentAbortController = null
}

// 收集最近消息（包含图片，用于发送给AI）
const collectRecentMessages = () => {
  const result = []
  const imageRoundLimit = 5 // 最近5轮内的图片
  let roundCount = 0
  
  // 从最新消息往前遍历
  for (let i = messages.value.length - 1; i >= 0 && result.length < 80; i--) {
    const msg = messages.value[i]
    
    // 计算轮次（每个assistant回复算一轮）
    if (msg.role === 'assistant') {
      roundCount++
    }
    
    const msgData = {
      role: msg.role,
      content: msg.content || ''
    }
    
    // 如果在图片轮次限制内且有图片，添加图片（确保是字符串）
    if (msg.image && typeof msg.image === 'string' && roundCount <= imageRoundLimit) {
      msgData.image = msg.image
    }
    
    result.unshift(msgData)
  }
  
  return result
}

// 流式渲染消息
const streamRenderMessage = async (fullContent, messageIndex) => {
  if (!fullContent) return
  
  let displayed = ''
  
  for (let i = 0; i < fullContent.length; i++) {
    displayed += fullContent[i]
    messages.value[messageIndex].content = displayed
    
    const char = fullContent[i]
    const isChineseChar = /[\u4e00-\u9fff]/.test(char)
    await new Promise(resolve => setTimeout(resolve, isChineseChar ? 25 : 12))
    
    if (i % 15 === 0) scrollToBottom()
  }
  
  messages.value[messageIndex].content = fullContent
  scrollToBottom()
}

// 触发图片选择
const triggerImageUpload = () => {
  imageInput.value?.click()
}

// 处理图片选择
const handleImageSelect = async (event) => {
  const file = event.target.files[0]
  if (!file) return
  
  // 检查文件大小
  if (file.size > 10 * 1024 * 1024) {
    toast.error('图片大小不能超过10MB')
    return
  }
  
  // 转换为base64
  const reader = new FileReader()
  reader.onload = async (e) => {
    const base64 = e.target.result
    await sendMessage(base64)
  }
  reader.readAsDataURL(file)
  
  // 清空input
  event.target.value = ''
}

// 预览图片
const previewImage = (url) => {
  previewImageUrl.value = url
}

// 检查是否是有效的图片（base64或URL）
const isValidImage = (img) => {
  if (!img || typeof img !== 'string') return false
  return img.startsWith('data:image') || img.startsWith('http')
}

// 渲染Markdown (with XSS sanitization)
const renderMarkdown = (content) => {
  if (!content) return ''
  try {
    const html = marked(content, { breaks: true })
    return DOMPurify.sanitize(html)
  } catch {
    return DOMPurify.sanitize(String(content))
  }
}

// 判断是否显示时间戳
const shouldShowTimestamp = (index) => {
  if (index === 0) return true
  const current = new Date(messages.value[index].timestamp)
  const previous = new Date(messages.value[index - 1].timestamp)
  return (current - previous) > 5 * 60 * 1000
}

// 格式化时间戳
const formatTimestamp = (timestamp) => {
  const date = new Date(timestamp)
  const month = date.getMonth() + 1
  const day = date.getDate()
  const hours = date.getHours().toString().padStart(2, '0')
  const minutes = date.getMinutes().toString().padStart(2, '0')
  const period = hours < 12 ? '上午' : '下午'
  return `${month}/${day} ${period} ${hours}:${minutes}`
}

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

// 显示关于
const showAbout = () => {
  showMenu.value = false
  toast.info('启明 - 你的AI伙伴 v1.0')
}

// 跳转设置
const goToSettings = () => {
  showMenu.value = false
  router.push('/settings')
}

// 退出登录
const logout = async () => {
  showMenu.value = false
  const confirmed = await confirm({
    title: '退出登录',
    message: '确定要退出登录吗？',
    type: 'danger',
    confirmText: '退出'
  })
  
  if (confirmed) {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    router.push('/login')
  }
}

// 同步用户头像（只请求一次，更新响应式变量）
const syncUserAvatar = async () => {
  const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
  
  // 先从localStorage读取，立即显示
  try {
    const storedUser = JSON.parse(localStorage.getItem('user') || '{}')
    if (storedUser.avatar) {
      userAvatarUrl.value = `${baseUrl}${storedUser.avatar}`
    }
  } catch {}
  
  // 然后请求profile更新（如果有变化）
  try {
    const profile = await userAPI.getProfile()
    if (profile && profile.avatar) {
      userAvatarUrl.value = `${baseUrl}${profile.avatar}`
      
      // 同步到localStorage
      const storedUser = JSON.parse(localStorage.getItem('user') || '{}')
      if (storedUser.avatar !== profile.avatar) {
        storedUser.avatar = profile.avatar
        localStorage.setItem('user', JSON.stringify(storedUser))
      }
    }
  } catch {
    // 静默失败，使用localStorage中的缓存
  }
}

onMounted(async () => {
  // 加载计时器状态
  loadTimerState()
  if (chatStartTime.value && !chatEnded.value) {
    startTimerInterval()
  }
  
  // 并行加载历史和同步头像
  await Promise.all([loadHistory(), syncUserAvatar()])
  if (inputElement.value) {
    inputElement.value.focus()
  }
})

onUnmounted(() => {
  // 清理AbortController
  if (currentAbortController) {
    currentAbortController.abort()
  }
  // 清理计时器
  stopTimerInterval()
})
</script>

<style scoped>
.chat-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--color-bg);
  overflow: hidden;
  max-width: 50%;
  min-width: 800px;
  margin: 0 auto;
}

/* 顶部标题栏 */
.chat-header {
  background: var(--color-primary);
  padding: 1rem 1.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  z-index: 10;
}

.title {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--color-dark);
  margin: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
}

.typing-indicator {
  font-size: 0.75rem;
  font-weight: 400;
  color: #666;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.menu-btn, .settings-btn {
  background: transparent;
  border: none;
  font-size: 1.5rem;
  padding: 0.5rem;
  cursor: pointer;
  color: var(--color-dark);
}

.menu-btn:hover, .settings-btn:hover {
  background: rgba(0, 0, 0, 0.05);
  border-radius: 8px;
}

/* 计时器显示 */
.timer-display {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  background: rgba(0, 0, 0, 0.08);
  padding: 0.4rem 0.75rem;
  border-radius: 20px;
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--color-dark);
  transition: all 0.3s ease;
}

.timer-display.warning {
  background: linear-gradient(135deg, #ff6b6b, #ee5a5a);
  color: white;
  animation: timer-pulse 1s ease-in-out infinite;
}

@keyframes timer-pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

.timer-icon {
  font-size: 1rem;
}

.timer-value {
  font-family: 'JetBrains Mono', monospace;
  min-width: 45px;
  text-align: center;
}

/* 侧边栏 */
.sidebar {
  position: fixed;
  top: 0;
  left: -300px;
  width: 280px;
  height: 100vh;
  background: white;
  box-shadow: 2px 0 10px rgba(0, 0, 0, 0.1);
  transition: left 0.3s;
  z-index: 101;
}

.sidebar.show {
  left: 0;
}

.sidebar-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.3);
  z-index: 100;
}

.sidebar-header {
  background: var(--color-primary);
  padding: 1rem 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sidebar-header h3 {
  margin: 0;
}

.close-btn {
  background: transparent;
  border: none;
  font-size: 2rem;
  cursor: pointer;
  padding: 0;
  width: 2rem;
  height: 2rem;
  line-height: 1;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  padding: 1rem 0;
}

.sidebar-nav a {
  padding: 1rem 1.5rem;
  color: var(--color-dark);
  text-decoration: none;
  transition: background 0.2s;
}

.sidebar-nav a:hover {
  background: var(--color-bg-light);
}

/* 消息区域 */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
  background: var(--color-bg);
  min-height: 0;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  gap: 1rem;
}

.greeting {
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0.5rem 0;
}

.intro {
  color: #666;
  font-size: 1.1rem;
}

/* 消息组 */
.message-group {
  margin-bottom: 1rem;
  overflow: visible;
}

.timestamp {
  text-align: center;
  color: #999;
  font-size: 0.85rem;
  margin: 1rem 0;
}

/* 消息 */
.message {
  display: flex;
  align-items: flex-start;
  margin-bottom: 0.75rem;
  gap: 0.75rem;
  overflow: visible;
}

.message.assistant {
  justify-content: flex-start;
}

.message.user {
  justify-content: flex-end;
}

.message-body {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-width: 70%;
  min-width: 0;
  overflow: visible;
  padding-bottom: 12px;
  padding-right: 12px;
}

/* 图片消息 - 无气泡直接展示 */
.image-message {
  max-width: 300px;
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.image-message img {
  width: 100%;
  display: block;
  transition: transform 0.2s;
}

.image-message:hover img {
  transform: scale(1.02);
}

.message-content-wrapper {
  position: relative;
  display: inline-block;
  overflow: visible;
}

.message-content-wrapper.user {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  overflow: visible;
}

.message-content-wrapper.assistant {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  overflow: visible;
}

.bubble-decoration {
  position: absolute;
  z-index: 2;
  pointer-events: none;
}

/* AI消息装饰：黄色星星在右下角 */
.message-content-wrapper.assistant .bubble-decoration {
  bottom: -10px;
  right: -10px;
}

/* 用户消息装饰：蓝色星星在右下角 */
.message-content-wrapper.user .bubble-decoration {
  bottom: -10px;
  right: -10px;
}

.message-content {
  padding: 0.875rem 1.125rem;
  border-radius: 16px;
  line-height: 1.6;
  text-align: left;
  background: white;
  color: #333;
  font-weight: 500;
  position: relative;
  z-index: 1;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.message-content.assistant {
  border: 2.5px solid #F4A500;
  border-radius: 4px 16px 16px 16px;
  box-shadow: 
    2px 2px 0 rgba(244, 165, 0, 0.15),
    0 2px 8px rgba(0, 0, 0, 0.05);
}

.message-content.user {
  border: 2.5px solid #6BB8D9;
  border-radius: 16px 16px 16px 4px;
  box-shadow: 
    2px 2px 0 rgba(107, 184, 217, 0.15),
    0 2px 8px rgba(0, 0, 0, 0.05);
}

/* Markdown内容样式修复 */
.message-content :deep(p) {
  margin: 0 0 0.5em 0;
}

.message-content :deep(p:last-child) {
  margin-bottom: 0;
}

.message-content :deep(ul),
.message-content :deep(ol) {
  margin: 0.5em 0;
  padding-left: 1.5em;
}

.message-content :deep(li) {
  margin: 0.25em 0;
}

.message-content :deep(pre) {
  margin: 0.5em 0;
  padding: 0.75em;
  background: #f5f5f5;
  border-radius: 8px;
  overflow-x: auto;
  font-size: 0.9em;
}

.message-content :deep(code) {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 0.9em;
  background: #f5f5f5;
  padding: 0.15em 0.4em;
  border-radius: 4px;
}

.message-content :deep(pre code) {
  background: none;
  padding: 0;
}

.message-content :deep(blockquote) {
  margin: 0.5em 0;
  padding-left: 1em;
  border-left: 3px solid #ddd;
  color: #666;
}

.message-content :deep(h1),
.message-content :deep(h2),
.message-content :deep(h3),
.message-content :deep(h4) {
  margin: 0.5em 0 0.25em 0;
  font-weight: 600;
}

.message-content :deep(h1) { font-size: 1.3em; }
.message-content :deep(h2) { font-size: 1.2em; }
.message-content :deep(h3) { font-size: 1.1em; }

.message-content :deep(table) {
  border-collapse: collapse;
  margin: 0.5em 0;
  width: 100%;
}

.message-content :deep(th),
.message-content :deep(td) {
  border: 1px solid #ddd;
  padding: 0.5em;
  text-align: left;
}

.message-content :deep(th) {
  background: #f5f5f5;
  font-weight: 600;
}

.message-content :deep(hr) {
  border: none;
  border-top: 1px solid #ddd;
  margin: 1em 0;
}

.message-content :deep(a) {
  color: #3b82f6;
  text-decoration: none;
}

.message-content :deep(a:hover) {
  text-decoration: underline;
}

.message-content :deep(img) {
  max-width: 100%;
  border-radius: 8px;
}

/* 确保所有内容不溢出 */
.message-content :deep(*) {
  max-width: 100%;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

/* 长代码块横向滚动而非溢出 */
.message-content :deep(pre) {
  max-width: 100%;
  overflow-x: auto;
}

/* 长单词/URL换行 */
.message-content :deep(p),
.message-content :deep(li) {
  word-break: break-word;
}

.message-content.loading {
  display: flex;
  gap: 0.5rem;
  padding: 1rem 1.5rem;
  border: 2.5px solid #F4A500;
  border-radius: 4px 16px 16px 16px;
  background: white;
  box-shadow: 
    2px 2px 0 rgba(244, 165, 0, 0.15),
    0 2px 8px rgba(0, 0, 0, 0.05);
}

.loading-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #F4A500;
  animation: loading 1.4s infinite;
}

.loading-dot:nth-child(2) { animation-delay: 0.2s; }
.loading-dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes loading {
  0%, 60%, 100% {
    transform: translateY(0);
    opacity: 0.5;
  }
  30% {
    transform: translateY(-10px);
    opacity: 1;
  }
}

/* 输入区域 */
.chat-input-area {
  padding: 1.5rem;
  background: white;
  border-top: 3px solid var(--color-primary);
  position: relative;
}

.input-divider {
  position: absolute;
  top: -3px;
  left: 0;
  right: 0;
  height: 3px;
  display: flex;
  align-items: center;
}

.divider-line {
  flex: 1;
  height: 2px;
  background: linear-gradient(to right, transparent, #FDD152 10%, #FDD152 90%, transparent);
}

.star-deco {
  position: absolute;
  left: 10px;
  top: -45px;
  animation: starFloat 3s ease-in-out infinite;
}

@keyframes starFloat {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}

.input-container {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  background: var(--color-primary);
  padding: 0.5rem;
  border-radius: 50px;
  border: 3px solid #000;
  box-shadow: 3px 3px 0 rgba(0, 0, 0, 0.2);
}

.message-input {
  flex: 1;
  border: none;
  background: white;
  padding: 0.75rem 1.25rem;
  border-radius: 50px;
  font-family: inherit;
  font-size: 1rem;
  color: #000;
  font-weight: 500;
  border: 2px solid #000;
}

.message-input:focus {
  outline: none;
  box-shadow: 0 0 0 2px var(--color-secondary);
}

.icon-btn {
  width: 40px;
  height: 40px;
  padding: 0;
  border: none;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
  background: white;
  border: 2px solid #000;
}

.icon-btn:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: 2px 2px 0 rgba(0, 0, 0, 0.2);
}

.send-btn {
  background: var(--color-primary);
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 图片预览 */
.image-preview-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.image-preview-overlay img {
  max-width: 90%;
  max-height: 90%;
  object-fit: contain;
  border-radius: 8px;
}

.close-preview {
  position: absolute;
  top: 20px;
  right: 20px;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: none;
  background: rgba(255, 255, 255, 0.2);
  color: white;
  font-size: 24px;
  cursor: pointer;
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

/* 计时器提示气泡 */
.time-warning-bubble {
  position: fixed;
  bottom: 120px;
  left: 50%;
  transform: translateX(-50%);
  background: linear-gradient(135deg, #FDD152, #F4A500);
  color: #333;
  padding: 0.75rem 1.25rem;
  border-radius: 50px;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  box-shadow: 0 4px 20px rgba(244, 165, 0, 0.4);
  z-index: 100;
  font-weight: 500;
}

.warning-icon {
  font-size: 1.2rem;
}

.warning-text {
  font-size: 0.95rem;
}

.warning-time {
  background: rgba(255, 255, 255, 0.9);
  padding: 0.25rem 0.5rem;
  border-radius: 20px;
  font-weight: 700;
  font-size: 0.9rem;
  font-family: 'JetBrains Mono', monospace;
}

.slide-up-enter-active, .slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from, .slide-up-leave-to {
  opacity: 0;
  transform: translate(-50%, 20px);
}

/* 聊天结束遮罩 */
.chat-ended-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(8px);
}

.ended-card {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  border-radius: 24px;
  padding: 3rem;
  text-align: center;
  max-width: 400px;
  border: 2px solid rgba(253, 209, 82, 0.3);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}

.ended-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.ended-card h2 {
  color: #FDD152;
  margin: 0 0 1rem 0;
  font-size: 1.5rem;
}

.ended-card p {
  color: rgba(255, 255, 255, 0.8);
  margin: 0 0 0.5rem 0;
  font-size: 1rem;
  line-height: 1.6;
}

.ended-hint {
  color: rgba(255, 255, 255, 0.5) !important;
  font-size: 0.85rem !important;
  margin-top: 1rem !important;
}

.ended-btn {
  margin-top: 1.5rem;
  background: linear-gradient(135deg, #FDD152, #F4A500);
  color: #1a1a2e;
  border: none;
  padding: 0.875rem 2rem;
  border-radius: 50px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.ended-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(253, 209, 82, 0.4);
}

/* 移动端适配 */
@media (max-width: 768px) {
  .chat-page {
    max-width: 100%;
    min-width: 100%;
  }
  
  .image-message {
    max-width: 200px;
  }
  
  .sidebar {
    width: 80%;
    max-width: 300px;
  }
}
</style>
