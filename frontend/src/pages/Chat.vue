<template>
  <div class="chat-page">
    <!-- 顶部标题栏 -->
    <header class="chat-header">
      <button class="menu-btn" @click="showMenu = !showMenu">
        <span class="menu-icon">☰</span>
      </button>
      <h1 class="title">
        启明
        <span v-if="isTyping" class="typing-indicator">正在输入中...</span>
      </h1>
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
        <a href="#" @click="showAbout">ℹ️ 关于启明</a>
        <a href="#" @click="logout">🚪 退出登录</a>
      </nav>
    </div>

    <!-- 聊天消息区域 -->
    <div class="chat-messages" ref="messagesContainer">
      <div v-if="messages.length === 0" class="empty-state">
        <AiAvatar :size="60" />
        <p class="greeting">{{ currentGreeting }}，{{ user.username }}！</p>
        <p class="intro">我是启明，你有什么想和我聊的吗？</p>
      </div>

      <div v-for="(msg, index) in messages" :key="index" class="message-group">
        <!-- 时间戳 -->
        <div v-if="shouldShowTimestamp(index)" class="timestamp">
          {{ formatTimestamp(msg.timestamp) }}
        </div>

        <!-- 消息 -->
        <div class="message" :class="msg.role">
          <AiAvatar v-if="msg.role === 'assistant'" :size="40" />
          <div class="message-content-wrapper" :class="msg.role">
            <MessageDecoration 
              :type="msg.role === 'assistant' ? 'ai' : 'user'" 
              :size="30" 
              class="bubble-decoration"
            />
            <div class="message-content" :class="msg.role">
              <div v-html="renderMarkdown(msg.content)"></div>
            </div>
          </div>
          <UserAvatar v-if="msg.role === 'user'" :size="40" />
        </div>
      </div>

      <!-- 加载中指示器 -->
      <div v-if="loading" class="message assistant">
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
        <button class="icon-btn attach-btn" @click="showAttachMenu = !showAttachMenu" title="附件">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="12" y1="5" x2="12" y2="19"/>
            <line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
        </button>
        <input
          type="text"
          v-model="inputMessage"
          @keydown.enter.exact.prevent="sendMessage"
          placeholder="输入消息..."
          ref="inputElement"
          class="message-input"
        />
        <button class="icon-btn send-btn" @click="sendMessage" :disabled="!inputMessage.trim() || loading">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M22 2L11 13"/>
            <path d="M22 2L15 22L11 13L2 9L22 2Z"/>
          </svg>
        </button>
      </div>

      <!-- 附件菜单 -->
      <div v-if="showAttachMenu" class="attach-menu">
        <button @click="uploadImage">📷 图片识别</button>
        <button @click="uploadFile">📎 读取文件</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, computed } from 'vue'
import { useRouter } from 'vue-router'
import { chatAPI } from '../api'
import { marked } from 'marked'
import AiAvatar from '../components/AiAvatar.vue'
import UserAvatar from '../components/UserAvatar.vue'
import StarIcon from '../components/StarIcon.vue'
import MessageDecoration from '../components/MessageDecoration.vue'

const router = useRouter()

const user = ref(JSON.parse(localStorage.getItem('user') || '{}'))

// 从本地存储加载消息
const loadLocalMessages = () => {
  const saved = localStorage.getItem('chat_messages')
  return saved ? JSON.parse(saved) : []
}

// 保存消息到本地存储
const saveLocalMessages = () => {
  localStorage.setItem('chat_messages', JSON.stringify(messages.value))
}

const messages = ref(loadLocalMessages())
const inputMessage = ref('')
const loading = ref(false)
const isTyping = ref(false)
let typingTimer = null
const showMenu = ref(false)
const showAttachMenu = ref(false)
const messagesContainer = ref(null)
const inputElement = ref(null)

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

// 加载聊天历史
const loadHistory = async () => {
  try {
    const response = await chatAPI.getHistory(50)
    messages.value = response.history.map(msg => ({
      role: msg.role,
      content: msg.content,
      timestamp: new Date(msg.timestamp)
    }))
    scrollToBottom()
  } catch (err) {
    console.error('加载历史失败:', err)
  }
}

// 发送消息
const sendMessage = async () => {
  if (!inputMessage.value.trim() || loading.value) return

  const userMessage = inputMessage.value.trim()
  inputMessage.value = ''

  // 添加用户消息
  messages.value.push({
    role: 'user',
    content: userMessage,
    timestamp: new Date()
  })
  saveLocalMessages()

  scrollToBottom()
  loading.value = true
  
  // 开始显示“正在输入中”
  isTyping.value = true
  
  // 模拟偶尔中断输入（20%概率）
  if (Math.random() < 0.2) {
    await new Promise(resolve => setTimeout(resolve, 800 + Math.random() * 1200))
    isTyping.value = false
    await new Promise(resolve => setTimeout(resolve, 300 + Math.random() * 500))
    isTyping.value = true
  }

  try {
    const response = await chatAPI.sendMessage(userMessage)
    
    // 添加AI回复
    messages.value.push({
      role: 'assistant',
      content: response.content,
      timestamp: new Date(response.timestamp)
    })
    saveLocalMessages()

    scrollToBottom()
  } catch (err) {
    console.error('发送消息失败:', err)
    messages.value.push({
      role: 'assistant',
      content: '抱歉，我现在无法回复。请稍后再试。',
      timestamp: new Date()
    })
    saveLocalMessages()
  } finally {
    loading.value = false
    isTyping.value = false
  }
}

// 渲染Markdown
const renderMarkdown = (content) => {
  try {
    return marked(content, { breaks: true })
  } catch {
    return content
  }
}

// 判断是否显示时间戳
const shouldShowTimestamp = (index) => {
  if (index === 0) return true
  
  const current = messages.value[index].timestamp
  const previous = messages.value[index - 1].timestamp
  
  // 如果时间相差超过5分钟，显示时间戳
  return (current - previous) > 5 * 60 * 1000
}

// 格式化时间戳
const formatTimestamp = (timestamp) => {
  const date = new Date(timestamp)
  const now = new Date()
  
  const month = date.getMonth() + 1
  const day = date.getDate()
  const hours = date.getHours().toString().padStart(2, '0')
  const minutes = date.getMinutes().toString().padStart(2, '0')
  
  // 判断上午/下午
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

// 上传图片
const uploadImage = () => {
  showAttachMenu.value = false
  // TODO: 实现图片上传功能
  alert('图片识别功能开发中')
}

// 上传文件
const uploadFile = () => {
  showAttachMenu.value = false
  // TODO: 实现文件上传功能
  alert('文件读取功能开发中')
}

// 显示关于信息
const showAbout = () => {
  showMenu.value = false
  alert('启明 - 你的AI聊天伙伴\n版本 1.0\n\n一个友好、智能的聊天助手。')
}

// 退出登录
const logout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  router.push('/login')
}

onMounted(() => {
  // 自动聚焦输入框
  if (inputElement.value) {
    inputElement.value.focus()
  }
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
  z-index: 100;
}

.sidebar.show {
  left: 0;
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

/* 消息区域 - 固定头尾，只滚动内容 */
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
  margin-bottom: 1.5rem;
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
  margin-bottom: 1rem;
  gap: 0.75rem;
}

.message.assistant {
  flex-direction: row;
  justify-content: flex-start;
}

.message.user {
  flex-direction: row;
  justify-content: flex-end;
  width: 100%;
}

.message :deep(.ai-avatar) {
  margin-right: 0.75rem;
}

.message :deep(.user-avatar) {
  margin-left: 0.75rem;
  order: 2;
}

.message-content-wrapper {
  position: relative;
  max-width: 70%;
}

.message-content-wrapper.user {
  order: 1;
}

.bubble-decoration {
  position: absolute;
}

.message.assistant .bubble-decoration {
  bottom: -8px;
  left: -8px;
}

.message.user .bubble-decoration {
  top: -8px;
  right: -8px;
}

.message-content {
  padding: 0.75rem 1rem;
  border-radius: 12px;
  line-height: 1.5;
  text-align: left;
  background: white;
  color: #000;
  font-weight: 500;
  position: relative;
  z-index: 1;
}

.message-content.assistant {
  border: 3px solid #FFA500;
  border-bottom-left-radius: 4px;
}

.message-content.user {
  border: 3px solid var(--color-accent);
  border-bottom-right-radius: 4px;
}

.message-content.loading {
  display: flex;
  gap: 0.5rem;
  padding: 1rem 1.5rem;
  border: 3px solid #FFA500;
  background: white;
}

.loading-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-dark);
  animation: loading 1.4s infinite;
}

.loading-dot:nth-child(2) {
  animation-delay: 0.2s;
}

.loading-dot:nth-child(3) {
  animation-delay: 0.4s;
}

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
  position: relative;
}

.divider-line::before {
  content: '';
  position: absolute;
  top: -1px;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(to right, transparent, rgba(253, 209, 82, 0.3) 10%, rgba(253, 209, 82, 0.3) 90%, transparent);
  filter: blur(2px);
}

.star-deco {
  position: absolute;
  left: 10px;
  top: -45px;
  animation: starFloat 3s ease-in-out infinite;
}

@keyframes starFloat {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-8px);
  }
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

.message-input::placeholder {
  color: #999;
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

.icon-btn:active {
  transform: scale(0.95);
}

.attach-btn {
  color: #000;
}

.send-btn {
  background: var(--color-primary);
  color: #000;
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

/* 附件菜单 */
.attach-menu {
  position: absolute;
  bottom: 100%;
  left: 1.5rem;
  margin-bottom: 0.5rem;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  padding: 0.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  z-index: 10;
}

.attach-menu button {
  padding: 0.75rem 1rem;
  border: none;
  background: transparent;
  text-align: left;
  cursor: pointer;
  border-radius: 8px;
  white-space: nowrap;
}

.attach-menu button:hover {
  background: var(--color-bg-light);
}

/* 移动端适配 */
@media (max-width: 768px) {
  .chat-page {
    max-width: 100%;
    min-width: 100%;
  }
  
  .message-content {
    max-width: 85%;
  }
  
  .sidebar {
    width: 80%;
    max-width: 300px;
  }
}
</style>
