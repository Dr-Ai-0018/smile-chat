<template>
  <Teleport to="body">
    <Transition name="notice-popup">
      <div v-if="visible && notice" class="notice-overlay">
        <div class="notice-card" ref="cardRef">
          <!-- 顶部装饰 -->
          <div class="notice-header">
            <div class="notice-envelope">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                <polyline points="22,6 12,13 2,6"/>
              </svg>
            </div>
            <div class="notice-badge">新消息</div>
          </div>

          <!-- 内容 -->
          <div class="notice-body">
            <h3 class="notice-title">{{ notice.title }}</h3>
            <p class="notice-content" v-html="renderedContent"></p>
            <div class="notice-time">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <polyline points="12 6 12 12 16 14"/>
              </svg>
              {{ formatTime(notice.created_at) }}
            </div>
          </div>

          <!-- 确认按钮 -->
          <div class="notice-footer">
            <button class="notice-confirm-btn" @click="handleConfirm">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
              我知道了
            </button>
          </div>

          <!-- 角落装饰星星 -->
          <div class="corner-deco corner-tl">✦</div>
          <div class="corner-deco corner-br">✦</div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed } from 'vue'
import { formatShanghaiDateTime } from '../utils/datetime'

const props = defineProps({
  visible: { type: Boolean, default: false },
  notice: { type: Object, default: null },
})

const emit = defineEmits(['read'])

const cardRef = ref(null)

const renderedContent = computed(() => {
  if (!props.notice?.content) return ''
  // 将 Markdown 链接 [text](url) 转为可点击的 <a>
  return props.notice.content
    .replace(/\[([^\]]+)\]\((https?:\/\/[^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>')
    .replace(/\n/g, '<br>')
})

const formatTime = (iso) => {
  if (!iso) return ''
  try {
    return formatShanghaiDateTime(iso)
  } catch {
    return iso
  }
}

const handleConfirm = () => {
  if (props.notice) {
    emit('read', props.notice.id)
  }
}
</script>

<style scoped>
.notice-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9000;
  padding: 1rem;
}

.notice-card {
  background: rgba(20, 20, 35, 0.82);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 24px;
  padding: 2rem;
  max-width: 380px;
  width: 100%;
  position: relative;
  box-shadow: 0 24px 64px rgba(0,0,0,0.45), 0 4px 16px rgba(0,0,0,0.25);
  overflow: hidden;
}

/* 顶部渐变条 */
.notice-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 3px;
  background: linear-gradient(90deg, #FDD152, #F4A500, #ff8a65);
  border-radius: 24px 24px 0 0;
}

.notice-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1.25rem;
}

.notice-envelope {
  width: 52px;
  height: 52px;
  background: linear-gradient(135deg, #FFF9E6, #FDD152);
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #F4A500;
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(253, 209, 82, 0.3);
}

.notice-badge {
  background: linear-gradient(135deg, #FDD152, #F4A500);
  color: #7a4f00;
  font-size: 0.75rem;
  font-weight: 700;
  padding: 0.25rem 0.625rem;
  border-radius: 20px;
  letter-spacing: 0.05em;
}

.notice-body {
  margin-bottom: 1.5rem;
}

.notice-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: #fff;
  margin: 0 0 0.625rem 0;
  line-height: 1.4;
}

.notice-content {
  font-size: 0.925rem;
  color: rgba(255, 255, 255, 0.8);
  line-height: 1.7;
  margin: 0 0 0.875rem 0;
  white-space: pre-wrap;
}

.notice-content :deep(a) {
  color: #FDD152;
  text-decoration: underline;
}

.notice-time {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.78rem;
  color: rgba(255, 255, 255, 0.4);
}

.notice-footer {
  display: flex;
  justify-content: flex-end;
}

.notice-confirm-btn {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  background: linear-gradient(135deg, #FDD152, #F4A500);
  color: #7a4f00;
  border: none;
  padding: 0.625rem 1.25rem;
  border-radius: 50px;
  font-size: 0.9rem;
  font-weight: 700;
  cursor: pointer;
  transition: transform 0.15s, box-shadow 0.15s;
  box-shadow: 0 4px 12px rgba(253, 209, 82, 0.35);
}

.notice-confirm-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 18px rgba(253, 209, 82, 0.5);
}

.notice-confirm-btn:active {
  transform: scale(0.97);
}

/* 角落装饰 */
.corner-deco {
  position: absolute;
  font-size: 0.75rem;
  color: rgba(253, 209, 82, 0.4);
  line-height: 1;
  pointer-events: none;
}

.corner-tl { top: 14px; left: 14px; }
.corner-br { bottom: 14px; right: 14px; }

/* 进入/离开动画 */
.notice-popup-enter-active {
  transition: all 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.notice-popup-leave-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.notice-popup-enter-from {
  opacity: 0;
  transform: scale(0.85) translateY(20px);
}

/* 离开时：卡片缩进到右上角（邮件图标方向） */
.notice-popup-leave-to .notice-card,
.notice-popup-leave-to {
  opacity: 0;
  transform: scale(0.05) translate(calc(50vw - 60px), calc(-50vh + 60px));
}
</style>
