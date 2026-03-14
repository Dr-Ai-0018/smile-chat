<template>
  <Teleport to="body">
    <Transition name="prompt-fade">
      <div v-if="visible" class="prompt-overlay" @click.self="handleClose">
        <div class="prompt-dialog" :class="promptType">
          <div class="prompt-header">
            <span class="prompt-icon">{{ typeIcon }}</span>
            <h3 class="prompt-title">{{ prompt?.content?.title || '提示' }}</h3>
          </div>
          
          <div class="prompt-body">
            <p class="prompt-message">{{ prompt?.content?.body }}</p>
            
            <!-- 选择题 - 单选 -->
            <div v-if="questionKind === 'choice_single'" class="prompt-options">
              <label 
                v-for="(option, index) in question?.options" 
                :key="index"
                class="option-item"
                :class="{ selected: selectedOptions.includes(option) }"
              >
                <input 
                  type="radio" 
                  :value="option" 
                  v-model="singleChoice"
                  class="option-radio"
                />
                <span class="option-text">{{ option }}</span>
              </label>
            </div>
            
            <!-- 选择题 - 多选 -->
            <div v-if="questionKind === 'choice_multi'" class="prompt-options">
              <label 
                v-for="(option, index) in question?.options" 
                :key="index"
                class="option-item"
                :class="{ selected: selectedOptions.includes(option) }"
              >
                <input 
                  type="checkbox" 
                  :value="option" 
                  v-model="selectedOptions"
                  class="option-checkbox"
                />
                <span class="option-text">{{ option }}</span>
              </label>
            </div>
            
            <!-- 填空题 -->
            <div v-if="questionKind === 'text'" class="prompt-textarea-wrapper">
              <textarea 
                v-model="textAnswer"
                :placeholder="question?.placeholder || '请输入...'"
                class="prompt-textarea"
                rows="3"
              ></textarea>
            </div>
          </div>
          
          <div class="prompt-footer">
            <button 
              v-if="canSkip" 
              class="btn-skip" 
              @click="handleSkip"
            >
              {{ skipText }}
            </button>
            <button 
              class="btn-submit" 
              @click="handleSubmit"
              :disabled="!canSubmit"
            >
              {{ submitText }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  prompt: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['submit', 'skip', 'close'])

// 响应式状态
const singleChoice = ref('')
const selectedOptions = ref([])
const textAnswer = ref('')

// 计算属性
const question = computed(() => props.prompt?.question)
const questionKind = computed(() => question.value?.kind || 'ack')
const promptType = computed(() => props.prompt?.type || 'daily')

const typeIcon = computed(() => {
  const icons = {
    daily: '💡',
    survey: '📋',
    feedback: '💬'
  }
  return icons[promptType.value] || '💡'
})

const submitText = computed(() => {
  if (questionKind.value === 'ack') {
    return question.value?.submit_text || '知道了'
  }
  return question.value?.submit_text || '提交'
})

const skipText = computed(() => '稍后再说')

const canSkip = computed(() => {
  // 如果是必填题，不能跳过
  if (question.value?.required) return false
  // ack类型不显示跳过按钮
  if (questionKind.value === 'ack') return false
  return true
})

const canSubmit = computed(() => {
  if (questionKind.value === 'ack') return true
  if (questionKind.value === 'choice_single') return !!singleChoice.value
  if (questionKind.value === 'choice_multi') return selectedOptions.value.length > 0
  if (questionKind.value === 'text') {
    if (question.value?.required) return textAnswer.value.trim().length > 0
    return true
  }
  return true
})

// 重置表单
const resetForm = () => {
  singleChoice.value = ''
  selectedOptions.value = []
  textAnswer.value = ''
}

// 监听visible变化，重置表单
watch(() => props.visible, (newVal) => {
  if (newVal) {
    resetForm()
  }
})

// 构建回答对象
const buildAnswer = () => {
  switch (questionKind.value) {
    case 'ack':
      return { ok: true }
    case 'choice_single':
      return { selected: [singleChoice.value] }
    case 'choice_multi':
      return { selected: [...selectedOptions.value] }
    case 'text':
      return { text: textAnswer.value.trim() }
    default:
      return { ok: true }
  }
}

const handleSubmit = () => {
  if (!canSubmit.value) return
  emit('submit', buildAnswer())
}

const handleSkip = () => {
  emit('skip')
}

const handleClose = () => {
  if (canSkip.value) {
    emit('skip')
  }
}
</script>

<style scoped>
.prompt-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 1rem;
}

.prompt-dialog {
  background: white;
  border-radius: 16px;
  width: 100%;
  max-width: 400px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  overflow: hidden;
  animation: dialogSlideIn 0.3s ease-out;
}

@keyframes dialogSlideIn {
  from {
    opacity: 0;
    transform: translateY(-20px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.prompt-header {
  padding: 1.25rem 1.5rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  border-bottom: 1px solid #eee;
}

.prompt-dialog.daily .prompt-header {
  background: linear-gradient(135deg, #FFF8E1, #FFF3CD);
}

.prompt-dialog.survey .prompt-header {
  background: linear-gradient(135deg, #E3F2FD, #BBDEFB);
}

.prompt-dialog.feedback .prompt-header {
  background: linear-gradient(135deg, #E8F5E9, #C8E6C9);
}

.prompt-icon {
  font-size: 1.5rem;
}

.prompt-title {
  margin: 0;
  font-size: 1.125rem;
  font-weight: 600;
  color: #333;
}

.prompt-body {
  padding: 1.5rem;
}

.prompt-message {
  margin: 0 0 1rem;
  color: #555;
  line-height: 1.6;
  white-space: pre-wrap;
}

.prompt-options {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.option-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  border: 2px solid #e0e0e0;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.option-item:hover {
  border-color: #F4A500;
  background: #FFFBF0;
}

.option-item.selected {
  border-color: #F4A500;
  background: #FFF8E1;
}

.option-radio,
.option-checkbox {
  width: 18px;
  height: 18px;
  accent-color: #F4A500;
}

.option-text {
  flex: 1;
  color: #333;
}

.prompt-textarea-wrapper {
  margin-top: 0.5rem;
}

.prompt-textarea {
  width: 100%;
  padding: 0.75rem 1rem;
  border: 2px solid #e0e0e0;
  border-radius: 10px;
  font-family: inherit;
  font-size: 1rem;
  resize: vertical;
  min-height: 80px;
  transition: border-color 0.2s;
}

.prompt-textarea:focus {
  outline: none;
  border-color: #F4A500;
}

.prompt-textarea::placeholder {
  color: #999;
}

.prompt-footer {
  display: flex;
  gap: 0.75rem;
  padding: 1rem 1.5rem 1.5rem;
  justify-content: flex-end;
}

.btn-skip,
.btn-submit {
  padding: 0.625rem 1.25rem;
  border-radius: 8px;
  font-size: 0.95rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-skip {
  background: #f5f5f5;
  border: 1px solid #ddd;
  color: #666;
}

.btn-skip:hover {
  background: #eee;
}

.btn-submit {
  background: #F4A500;
  border: none;
  color: white;
  min-width: 80px;
}

.btn-submit:hover:not(:disabled) {
  background: #e09500;
  transform: translateY(-1px);
}

.btn-submit:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 过渡动画 */
.prompt-fade-enter-active,
.prompt-fade-leave-active {
  transition: opacity 0.3s ease;
}

.prompt-fade-enter-from,
.prompt-fade-leave-to {
  opacity: 0;
}

.prompt-fade-enter-active .prompt-dialog {
  animation: dialogSlideIn 0.3s ease-out;
}

.prompt-fade-leave-active .prompt-dialog {
  animation: dialogSlideOut 0.2s ease-in;
}

@keyframes dialogSlideOut {
  from {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
  to {
    opacity: 0;
    transform: translateY(-10px) scale(0.98);
  }
}
</style>
