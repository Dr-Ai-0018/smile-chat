<template>
  <div class="checkin-overlay" @click.self="$emit('close')">
    <div class="checkin-dialog">
      <div class="checkin-header">
        <span class="checkin-title">每日打卡</span>
        <button class="close-btn" @click="$emit('close')">×</button>
      </div>

      <div class="checkin-body">
        <p class="checkin-desc">请根据你现在的感受，为以下问题打分（1~10）</p>

        <div v-for="(q, i) in questions" :key="i" class="question-item">
          <div class="question-label">
            <span>{{ q }}</span>
            <span class="score-badge">{{ answers[i] }}</span>
          </div>
          <input
            type="range"
            min="1"
            max="10"
            step="1"
            v-model.number="answers[i]"
            class="slider"
          />
          <div class="slider-labels">
            <span>1</span>
            <span>10</span>
          </div>
        </div>
      </div>

      <div class="checkin-footer">
        <button class="submit-btn" :disabled="submitting" @click="handleSubmit">
          {{ submitting ? '提交中...' : '提交打卡' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { checkinAPI } from '../api/index.js'
import { toast } from '../utils/toast'

const props = defineProps({
  questions: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['close', 'success'])

const answers = ref(props.questions.map(() => 5))
const submitting = ref(false)

watch(() => props.questions, (qs) => {
  answers.value = qs.map(() => 5)
}, { immediate: true })

async function handleSubmit() {
  submitting.value = true
  try {
    await checkinAPI.submit(answers.value)
    emit('success')
  } catch (e) {
    console.error('打卡提交失败', e)
    toast.error('提交失败，请重试')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.checkin-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.checkin-dialog {
  background: #fff;
  border-radius: 16px;
  width: 90%;
  max-width: 420px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 8px 32px rgba(0,0,0,0.18);
  overflow: hidden;
}

.checkin-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px 12px;
  border-bottom: 1px solid #f0f0f0;
}

.checkin-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 20px;
  color: #999;
  cursor: pointer;
  line-height: 1;
  padding: 0 4px;
}

.checkin-body {
  padding: 16px 20px;
  overflow-y: auto;
  flex: 1;
}

.checkin-desc {
  font-size: 13px;
  color: #888;
  margin: 0 0 16px;
}

.question-item {
  margin-bottom: 20px;
}

.question-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 14px;
  color: #444;
}

.score-badge {
  background: #e8f4fd;
  color: #4a9edd;
  font-weight: 600;
  font-size: 14px;
  min-width: 28px;
  text-align: center;
  border-radius: 6px;
  padding: 2px 6px;
}

.slider {
  width: 100%;
  accent-color: #4a9edd;
  cursor: pointer;
}

.slider-labels {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: #bbb;
  margin-top: 2px;
}

.checkin-footer {
  padding: 12px 20px 16px;
  border-top: 1px solid #f0f0f0;
}

.submit-btn {
  width: 100%;
  padding: 12px;
  background: #4a9edd;
  color: #fff;
  border: none;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.2s;
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.submit-btn:not(:disabled):hover {
  opacity: 0.88;
}
</style>
