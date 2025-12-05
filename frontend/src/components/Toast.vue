<template>
  <Teleport to="body">
    <!-- 提示型弹窗（右上角飞入飞出） -->
    <TransitionGroup name="toast" tag="div" class="toast-container">
      <div
        v-for="toast in toasts"
        :key="toast.id"
        class="toast"
        :class="toast.type"
      >
        <span class="toast-icon">
          <template v-if="toast.type === 'success'">✓</template>
          <template v-else-if="toast.type === 'error'">✕</template>
          <template v-else-if="toast.type === 'warning'">⚠</template>
          <template v-else>ℹ</template>
        </span>
        <span class="toast-message">{{ toast.message }}</span>
        <div class="toast-progress" :style="{ animationDuration: toast.duration + 'ms' }"></div>
      </div>
    </TransitionGroup>

    <!-- 确认型弹窗 -->
    <Transition name="modal">
      <div v-if="confirmModal" class="modal-overlay" @click.self="cancelConfirm">
        <div class="modal-content">
          <div class="modal-header">
            <span class="modal-icon" :class="confirmModal.type">
              <template v-if="confirmModal.type === 'danger'">⚠</template>
              <template v-else>?</template>
            </span>
            <h3>{{ confirmModal.title }}</h3>
          </div>
          <p class="modal-message">{{ confirmModal.message }}</p>
          <div class="modal-actions">
            <button class="modal-btn cancel" @click="cancelConfirm">取消</button>
            <button class="modal-btn confirm" :class="confirmModal.type" @click="doConfirm">
              {{ confirmModal.confirmText || '确认' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref } from 'vue'

const toasts = ref([])
const confirmModal = ref(null)
let confirmResolve = null

// 显示提示弹窗
const showToast = (message, type = 'info', duration = 3000) => {
  const id = Date.now() + Math.random()
  toasts.value.push({ id, message, type, duration })
  
  setTimeout(() => {
    const index = toasts.value.findIndex(t => t.id === id)
    if (index > -1) {
      toasts.value.splice(index, 1)
    }
  }, duration)
}

// 显示确认弹窗
const showConfirm = (options) => {
  return new Promise((resolve) => {
    confirmResolve = resolve
    confirmModal.value = {
      title: options.title || '确认',
      message: options.message,
      type: options.type || 'normal',
      confirmText: options.confirmText || '确认'
    }
  })
}

const doConfirm = () => {
  confirmModal.value = null
  confirmResolve?.(true)
}

const cancelConfirm = () => {
  confirmModal.value = null
  confirmResolve?.(false)
}

// 暴露方法
defineExpose({
  showToast,
  showConfirm,
  success: (msg) => showToast(msg, 'success'),
  error: (msg) => showToast(msg, 'error'),
  warning: (msg) => showToast(msg, 'warning'),
  info: (msg) => showToast(msg, 'info')
})
</script>

<style scoped>
/* Toast容器 - 右上角 */
.toast-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 10000;
  display: flex;
  flex-direction: column;
  gap: 10px;
  pointer-events: none;
}

/* 单个Toast */
.toast {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  border-left: 4px solid;
  min-width: 280px;
  max-width: 400px;
  position: relative;
  overflow: hidden;
  pointer-events: auto;
}

.toast.success {
  border-color: #10b981;
  background: linear-gradient(135deg, #ecfdf5 0%, white 100%);
}

.toast.error {
  border-color: #ef4444;
  background: linear-gradient(135deg, #fef2f2 0%, white 100%);
}

.toast.warning {
  border-color: #f59e0b;
  background: linear-gradient(135deg, #fffbeb 0%, white 100%);
}

.toast.info {
  border-color: var(--color-accent);
  background: linear-gradient(135deg, #eff6ff 0%, white 100%);
}

.toast-icon {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: bold;
  flex-shrink: 0;
}

.toast.success .toast-icon {
  background: #10b981;
  color: white;
}

.toast.error .toast-icon {
  background: #ef4444;
  color: white;
}

.toast.warning .toast-icon {
  background: #f59e0b;
  color: white;
}

.toast.info .toast-icon {
  background: var(--color-accent);
  color: white;
}

.toast-message {
  flex: 1;
  font-size: 14px;
  color: #333;
  font-weight: 500;
}

/* 进度条 */
.toast-progress {
  position: absolute;
  bottom: 0;
  left: 0;
  height: 3px;
  background: currentColor;
  animation: progress linear forwards;
  opacity: 0.3;
}

.toast.success .toast-progress { background: #10b981; }
.toast.error .toast-progress { background: #ef4444; }
.toast.warning .toast-progress { background: #f59e0b; }
.toast.info .toast-progress { background: var(--color-accent); }

@keyframes progress {
  from { width: 100%; }
  to { width: 0%; }
}

/* Toast动画 */
.toast-enter-active {
  animation: slideIn 0.3s ease-out;
}

.toast-leave-active {
  animation: slideOut 0.3s ease-in;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

@keyframes slideOut {
  from {
    transform: translateX(0);
    opacity: 1;
  }
  to {
    transform: translateX(100%);
    opacity: 0;
  }
}

/* 确认弹窗 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10001;
  backdrop-filter: blur(4px);
}

.modal-content {
  background: white;
  border-radius: 16px;
  padding: 24px;
  min-width: 320px;
  max-width: 420px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  border: 3px solid var(--color-primary);
}

.modal-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.modal-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  background: var(--color-primary);
  color: #333;
}

.modal-icon.danger {
  background: #fee2e2;
  color: #dc2626;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  color: #333;
}

.modal-message {
  color: #666;
  line-height: 1.6;
  margin: 0 0 24px 0;
}

.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.modal-btn {
  padding: 10px 24px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  border: 2px solid;
}

.modal-btn.cancel {
  background: white;
  border-color: #ddd;
  color: #666;
}

.modal-btn.cancel:hover {
  background: #f5f5f5;
  border-color: #ccc;
}

.modal-btn.confirm {
  background: var(--color-primary);
  border-color: #333;
  color: #333;
}

.modal-btn.confirm:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.modal-btn.confirm.danger {
  background: #dc2626;
  border-color: #991b1b;
  color: white;
}

.modal-btn.confirm.danger:hover {
  background: #b91c1c;
}

/* Modal动画 */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s;
}

.modal-enter-active .modal-content,
.modal-leave-active .modal-content {
  transition: transform 0.2s;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .modal-content,
.modal-leave-to .modal-content {
  transform: scale(0.9);
}
</style>

