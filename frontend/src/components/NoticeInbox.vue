<template>
  <div class="notice-inbox" ref="inboxRef">
    <!-- 邮件图标按钮 -->
    <button
      class="inbox-btn"
      :class="{ 'has-unread': unreadCount > 0 }"
      @click="togglePanel"
      title="消息收件箱"
    >
      <span class="inbox-emoji">{{ unreadCount > 0 ? '📬' : '📭' }}</span>
      <Transition name="badge-pop">
        <span v-if="unreadCount > 0" class="unread-badge">
          {{ unreadCount > 99 ? '99+' : unreadCount }}
        </span>
      </Transition>
    </button>

    <!-- 收件箱面板 -->
    <Transition name="inbox-panel">
      <div v-if="panelOpen" class="inbox-panel">
        <div class="panel-header">
          <div class="panel-title">
            📬 消息收件箱
          </div>
          <button class="panel-close" @click="panelOpen = false">×</button>
        </div>

        <div class="panel-body">
          <div v-if="notices.length === 0" class="empty-inbox">
            <div class="empty-icon">📭</div>
            <p>暂无消息</p>
          </div>

          <div
            v-for="notice in notices"
            :key="notice.id"
            class="notice-item"
            :class="{ unread: !notice.read_at }"
            @click="toggleExpand(notice)"
          >
            <div class="item-header">
              <div class="item-left">
                <span class="unread-dot" :class="{ visible: !notice.read_at }"></span>
                <span class="item-title">{{ notice.title }}</span>
              </div>
              <span class="item-time">{{ formatTimeShort(notice.created_at) }}</span>
            </div>

            <Transition name="expand">
              <div v-if="expandedId === notice.id" class="item-content">
                <div class="item-content-markdown" v-html="renderContent(notice.content)"></div>
                <div class="item-meta">
                  <span v-if="notice.read_at" class="read-label">
                    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                      <polyline points="20 6 9 17 4 12"/>
                    </svg>
                    已读
                  </span>
                  <span v-else class="unread-label">未读</span>
                </div>
              </div>
            </Transition>
          </div>
        </div>
      </div>
    </Transition>

    <!-- 点击遮罩关闭 -->
    <div v-if="panelOpen" class="inbox-backdrop" @click="panelOpen = false"></div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { formatShanghaiMonthDay, formatShanghaiTime, getShanghaiDayNumber } from '../utils/datetime'

const props = defineProps({
  notices: { type: Array, default: () => [] },
  unreadCount: { type: Number, default: 0 },
})

const emit = defineEmits(['open', 'read'])

const panelOpen = ref(false)
const expandedId = ref(null)
const inboxRef = ref(null)

marked.setOptions({
  gfm: true,
  breaks: true,
})

const togglePanel = () => {
  panelOpen.value = !panelOpen.value
  if (panelOpen.value) {
    expandedId.value = null
    emit('open')
  }
}

const toggleExpand = (notice) => {
  const id = notice.id
  if (expandedId.value === id) {
    expandedId.value = null
  } else {
    expandedId.value = id
    // 展开时标记已读
    if (!notice.read_at) {
      emit('read', id)
    }
  }
}

const renderContent = (content) => {
  if (!content) return ''
  const rawHtml = marked.parse(content)
  const cleanHtml = DOMPurify.sanitize(rawHtml)
  return cleanHtml.replace(/<a\s+/g, '<a target="_blank" rel="noopener noreferrer" ')
}

const formatTimeShort = (iso) => {
  if (!iso) return ''
  try {
    const d = new Date(iso)
    const now = new Date()
    const diffDays = getShanghaiDayNumber(now) - getShanghaiDayNumber(d)
    if (diffDays === 0) {
      return formatShanghaiTime(d)
    } else if (diffDays < 7) {
      return `${diffDays}天前`
    } else {
      return formatShanghaiMonthDay(d)
    }
  } catch {
    return ''
  }
}
</script>

<style scoped>
.notice-inbox {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 邮件按钮 */
.inbox-btn {
  position: relative;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background: transparent;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s, transform 0.2s;
  flex-shrink: 0;
  padding: 0;
  line-height: 1;
}

.inbox-emoji {
  font-size: 1.25rem;
  line-height: 1;
  display: block;
}

.inbox-btn:hover {
  background: rgba(0, 0, 0, 0.08);
  transform: scale(1.05);
}

.inbox-btn.has-unread {
  animation: gentle-shake 2s ease-in-out infinite;
}

@keyframes gentle-shake {
  0%, 90%, 100% { transform: rotate(0deg); }
  92% { transform: rotate(-8deg); }
  96% { transform: rotate(8deg); }
}

/* 未读徽章 */
.unread-badge {
  position: absolute;
  top: -2px;
  right: -2px;
  background: #ff4757;
  color: white;
  font-size: 0.6rem;
  font-weight: 700;
  min-width: 16px;
  height: 16px;
  padding: 0 3px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1.5px solid white;
  line-height: 1;
}

.badge-pop-enter-active { transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1); }
.badge-pop-enter-from { transform: scale(0); opacity: 0; }
.badge-pop-leave-active { transition: all 0.15s ease; }
.badge-pop-leave-to { transform: scale(0); opacity: 0; }

/* 收件箱面板 */
.inbox-panel {
  position: absolute;
  top: calc(100% + 10px);
  right: 0;
  width: 320px;
  max-height: 420px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 8px 40px rgba(0,0,0,0.18), 0 2px 8px rgba(0,0,0,0.1);
  z-index: 8000;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* 面板进出动画 */
.inbox-panel-enter-active {
  transition: all 0.25s cubic-bezier(0.34, 1.2, 0.64, 1);
}
.inbox-panel-leave-active {
  transition: all 0.2s ease;
}
.inbox-panel-enter-from {
  opacity: 0;
  transform: translateY(-8px) scale(0.96);
}
.inbox-panel-leave-to {
  opacity: 0;
  transform: translateY(-4px) scale(0.97);
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.875rem 1rem;
  border-bottom: 1px solid #f0f0f0;
  background: linear-gradient(to right, #FFF9E6, #fff);
  flex-shrink: 0;
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.875rem;
  font-weight: 700;
  color: #1a1a2e;
}

.panel-close {
  border: none;
  background: none;
  color: #aaa;
  font-size: 1.1rem;
  cursor: pointer;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: background 0.15s;
}
.panel-close:hover { background: #f0f0f0; color: #555; }

.panel-body {
  overflow-y: auto;
  flex: 1;
}

.empty-inbox {
  padding: 2rem;
  text-align: center;
  color: #bbb;
}
.empty-icon { font-size: 2rem; margin-bottom: 0.5rem; }
.empty-inbox p { font-size: 0.85rem; margin: 0; }

/* 通知条目 */
.notice-item {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #f5f5f5;
  cursor: pointer;
  transition: background 0.15s;
}
.notice-item:hover { background: #fafafa; }
.notice-item.unread { background: #FFFDF0; }
.notice-item.unread:hover { background: #FFF9E6; }

.item-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

.item-left {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  min-width: 0;
}

.unread-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: transparent;
  flex-shrink: 0;
  transition: background 0.2s;
}
.unread-dot.visible { background: #F4A500; }

.item-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: #1a1a2e;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.item-time {
  font-size: 0.72rem;
  color: #bbb;
  flex-shrink: 0;
}

/* 展开内容 */
.item-content {
  margin-top: 0.5rem;
  padding-top: 0.5rem;
  border-top: 1px dashed #eee;
}

.item-content-markdown {
  font-size: 0.83rem;
  color: #666;
  line-height: 1.65;
  margin: 0 0 0.5rem 0;
  overflow-wrap: anywhere;
}

.item-content-markdown :deep(*:first-child) {
  margin-top: 0;
}

.item-content-markdown :deep(*:last-child) {
  margin-bottom: 0;
}

.item-content-markdown :deep(p),
.item-content-markdown :deep(ul),
.item-content-markdown :deep(ol),
.item-content-markdown :deep(blockquote) {
  margin: 0 0 0.7rem;
}

.item-content-markdown :deep(ul),
.item-content-markdown :deep(ol) {
  padding-left: 1.15rem;
}

.item-content-markdown :deep(a) {
  color: #4a9edd;
  text-decoration: underline;
}

.item-content-markdown :deep(img) {
  display: block;
  width: auto;
  max-width: min(100%, 240px);
  height: auto;
  max-height: 260px;
  margin: 0.7rem 0;
  border-radius: 12px;
  object-fit: contain;
  background: #f6f7fb;
}

.item-content-markdown :deep(code) {
  background: #f3f4f6;
  border-radius: 5px;
  padding: 0.1rem 0.3rem;
  font-size: 0.86em;
}

.item-content-markdown :deep(pre) {
  margin: 0 0 0.75rem;
  padding: 0.7rem 0.8rem;
  background: #f6f7fb;
  border-radius: 10px;
  overflow-x: auto;
}

.item-content-markdown :deep(pre code) {
  background: transparent;
  padding: 0;
}

.item-meta {
  display: flex;
  justify-content: flex-end;
}

.read-label {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.72rem;
  color: #4caf50;
  font-weight: 600;
}

.unread-label {
  font-size: 0.72rem;
  color: #F4A500;
  font-weight: 600;
}

.expand-enter-active { transition: all 0.2s ease; }
.expand-leave-active { transition: all 0.15s ease; }
.expand-enter-from { opacity: 0; transform: translateY(-4px); max-height: 0; }
.expand-leave-to { opacity: 0; max-height: 0; }

/* 遮罩 */
.inbox-backdrop {
  position: fixed;
  inset: 0;
  z-index: 7999;
}

/* 移动端 */
@media (max-width: 480px) {
  .inbox-panel {
    width: 290px;
    right: -10px;
  }
}
</style>
