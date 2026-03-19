<template>
  <div class="ema-overlay" @click.self="$emit('close')">
    <div class="ema-modal">
      <div class="ema-header">
        <h2>📝 本次交流反馈</h2>
        <p>⚠️ 填完以下 {{ questions.length }} 题并提交，即算作本次打卡成功！</p>
      </div>

      <div class="ema-body">
        <div v-for="(q, i) in questions" :key="i" class="question-item">
          <p class="q-title">{{ i + 1 }}. {{ q }}</p>
          <div class="scale-anchors">
            <span>完全不同意 (1)</span>
            <span>完全同意 (7)</span>
          </div>
          <div class="scale-options">
            <label v-for="n in 7" :key="n">
              <input type="radio" :name="`q${i}`" :value="n" v-model="answers[i]" />
              <div class="radio-circle" :class="{ selected: answers[i] === n }">{{ n }}</div>
            </label>
          </div>
        </div>
      </div>

      <div class="ema-footer">
        <div v-if="!allAnswered" class="ema-hint">请完成所有题目后提交</div>
        <button
          class="submit-btn"
          :disabled="submitting || !allAnswered"
          @click="handleSubmit"
        >
          {{ submitting ? '提交中...' : '🚀 提交并完成打卡' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { checkinAPI } from '../api/index.js'
import { toast } from '../utils/toast'

const props = defineProps({
  questions: { type: Array, default: () => [] }
})

const emit = defineEmits(['close', 'success'])

const answers = ref(props.questions.map(() => null))
const submitting = ref(false)

watch(() => props.questions, (qs) => {
  answers.value = qs.map(() => null)
}, { immediate: true })

const allAnswered = computed(() => answers.value.every(a => a !== null))

async function handleSubmit() {
  if (!allAnswered.value) return
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
.ema-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  overflow-y: auto;
  padding: 16px;
}

.ema-modal {
  background: #fff;
  width: 92%;
  max-width: 400px;
  border-radius: 16px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.ema-header {
  background: #FACC15;
  padding: 12px 15px;
  text-align: center;
}

.ema-header h2 {
  margin: 0;
  font-size: 18px;
  color: #333;
  font-weight: 600;
}

.ema-header p {
  margin: 4px 0 0;
  font-size: 12px;
  color: #554400;
  font-weight: bold;
}

.ema-body {
  padding: 12px 16px;
  overflow-y: auto;
  max-height: 60vh;
}

.question-item {
  margin-bottom: 12px;
  border-bottom: 1px dashed #eee;
  padding-bottom: 8px;
}

.question-item:last-child {
  border-bottom: none;
  margin-bottom: 0;
}

.q-title {
  font-size: 13.5px;
  color: #333;
  margin: 0 0 6px;
  font-weight: 500;
  line-height: 1.3;
}

.scale-anchors {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: #666;
  margin-bottom: 4px;
}

.scale-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.scale-options label {
  position: relative;
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
}

.scale-options input[type="radio"] {
  display: none;
}

.radio-circle {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: #f5f5f5;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 13px;
  color: #666;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}

.radio-circle.selected {
  background: #FACC15;
  color: #000;
  font-weight: bold;
  box-shadow: 0 2px 6px rgba(250, 204, 21, 0.4);
  border: 1px solid #DCA100;
  transform: scale(1.1);
}

.ema-footer {
  padding: 10px 16px 16px;
}

.ema-hint {
  text-align: center;
  font-size: 12px;
  color: #999;
  margin-bottom: 8px;
}

.submit-btn {
  width: 100%;
  background: #FACC15;
  color: #333;
  border: none;
  padding: 14px 0;
  border-radius: 25px;
  font-size: 16px;
  font-weight: bold;
  cursor: pointer;
  transition: background 0.2s;
  box-shadow: 0 4px 10px rgba(250, 204, 21, 0.3);
}

.submit-btn:hover:not(:disabled) {
  background: #EAB308;
}

.submit-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
