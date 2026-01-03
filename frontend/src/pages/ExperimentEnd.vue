<template>
  <div class="experiment-page">
    <div class="experiment-container">
    <!-- 左侧：实验流程 -->
    <div class="panel-info">
      <div class="header">
        <div class="brand">QIMING LAB</div>
        <h1 class="title">
          对话已结束<br>
          <span class="subtitle">请完成后测问卷</span>
        </h1>
      </div>

      <div class="timeline">
        <!-- 步骤1 -->
        <div class="timeline-item done">
          <div class="timeline-dot"></div>
          <div class="t-title">账号登录 <span class="tag">已完成</span></div>
          <div class="t-desc">系统已记录你的基本信息。</div>
        </div>

        <!-- 步骤2 -->
        <div class="timeline-item done">
          <div class="timeline-dot"></div>
          <div class="t-title">前测问卷 <span class="tag">已完成</span></div>
          <div class="t-desc">问卷已提交。</div>
        </div>

        <!-- 步骤3 -->
        <div class="timeline-item done">
          <div class="timeline-dot"></div>
          <div class="t-title">正式对话 <span class="tag">已完成</span></div>
          <div class="t-desc">感谢你参与本次对话实验。</div>
        </div>

        <!-- 步骤4 -->
        <div class="timeline-item active">
          <div class="timeline-dot"></div>
          <div class="t-title">后测反馈 <span class="tag highlight">当前步骤</span></div>
          <div class="t-desc">请扫描右侧二维码或点击链接完成后测问卷。</div>
        </div>
      </div>
    </div>

    <!-- 右侧：核心任务区 -->
    <div class="panel-action">
      <div class="bg-circle"></div>

      <!-- 二维码区 -->
      <div class="qr-card">
        <div class="qr-img">
          <img v-if="qrImageUrl" :src="qrImageUrl" alt="后测问卷二维码" />
          <svg v-else width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="3" width="7" height="7"></rect>
            <rect x="14" y="3" width="7" height="7"></rect>
            <rect x="14" y="14" width="7" height="7"></rect>
            <rect x="3" y="14" width="7" height="7"></rect>
          </svg>
        </div>
        <div class="qr-hint">扫描二维码填写问卷</div>
        <a :href="questionnaireLink" target="_blank" class="qr-link">或点击此处打开链接</a>
      </div>

      <!-- 确认区 -->
      <div class="confirm-area">
        <label class="confirm-label">请确认：你是否已完成提交？</label>
        
        <div class="options">
          <div 
            class="option-btn" 
            :class="{ selected: selectedOption === 'no' }"
            @click="selectOption('no')"
          >
            还没完成
          </div>
          <div 
            class="option-btn" 
            :class="{ selected: selectedOption === 'yes' }"
            @click="selectOption('yes')"
          >
            ✅ 是，已提交
          </div>
        </div>

        <div class="error-msg" :class="{ show: showError }">{{ errorMessage }}</div>

        <button 
          class="cta-btn" 
          :disabled="!isCompleted"
          @click="finishExperiment"
        >
          完成实验
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="20 6 9 17 4 12"></polyline>
          </svg>
        </button>

        <div class="thank-you" v-if="showThankYou">
          <div class="thank-icon">🎉</div>
          <p>感谢你参与本次实验！</p>
        </div>
      </div>
    </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// 占位符配置 - 后续替换为真实链接
const POSTTEST_QR_IMAGE_URL = 'https://imgbed.killerbest.com/file/1766064425104_0.png' // 替换为真实二维码图片URL
const POSTTEST_LINK = 'https://www.credamo.com/s/zeE73i/' // 后测问卷链接

// 响应式状态
const selectedOption = ref(null)
const showError = ref(false)
const errorMessage = ref('')
const showThankYou = ref(false)

// 计算属性
const isCompleted = computed(() => selectedOption.value === 'yes')
const qrImageUrl = computed(() => POSTTEST_QR_IMAGE_URL)
const questionnaireLink = computed(() => POSTTEST_LINK)

// 选项选择
function selectOption(value) {
  selectedOption.value = value
  
  if (value === 'yes') {
    showError.value = false
  } else {
    errorMessage.value = '需完成问卷才能继续'
    showError.value = true
  }
}

// 完成实验
function finishExperiment() {
  if (!isCompleted.value) return
  
  showThankYou.value = true
  
  // 2秒后跳转到设置页
  setTimeout(() => {
    router.push('/settings')
  }, 2000)
}
</script>

<style scoped>
/* 品牌色变量 */
.experiment-page {
  --primary: #F59E0B;
  --primary-light: #FFF7ED;
  --primary-hover: #D97706;
  --bg-body: #FAFAF9;
  --surface: #FFFFFF;
  --text-main: #1C1917;
  --text-sub: #57534E;
  --text-muted: #A8A29E;
  --border: #E7E5E4;
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.05);
  --shadow-md: 0 10px 30px -5px rgba(0,0,0,0.06);
  --radius-lg: 24px;
  --radius-md: 12px;
}

.experiment-page {
  width: 100%;
  min-height: 100vh;
  background-color: var(--bg-body);
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
  box-sizing: border-box;
}

.experiment-container {
  width: 100%;
  max-width: 1000px;
  min-height: 600px;
  background: var(--surface);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  overflow: hidden;
  display: grid;
  grid-template-columns: 1.2fr 0.8fr;
}

/* 左侧面板 */
.panel-info {
  padding: 48px;
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--border);
}

.header {
  margin-bottom: 40px;
}

.brand {
  font-size: 20px;
  font-weight: 800;
  color: var(--primary);
  letter-spacing: 1px;
  margin-bottom: 8px;
  display: inline-block;
}

.title {
  font-size: 32px;
  font-weight: 700;
  line-height: 1.2;
  color: var(--text-main);
  margin: 0;
}

.subtitle {
  font-size: 24px;
  color: var(--text-sub);
  font-weight: 500;
}

/* 时间轴 */
.timeline {
  flex: 1;
  position: relative;
  margin-left: 10px;
  padding-left: 30px;
  border-left: 2px solid var(--border);
}

.timeline-item {
  position: relative;
  margin-bottom: 40px;
}

.timeline-item:last-child {
  margin-bottom: 0;
}

.timeline-dot {
  width: 14px;
  height: 14px;
  background: var(--surface);
  border: 3px solid var(--border);
  border-radius: 50%;
  position: absolute;
  left: -38px;
  top: 5px;
  transition: all 0.3s;
}

.timeline-item.active .timeline-dot {
  border-color: var(--primary);
  background: var(--primary);
  box-shadow: 0 0 0 4px var(--primary-light);
}

.timeline-item.done .timeline-dot {
  background: var(--text-sub);
  border-color: var(--text-sub);
}

.t-title {
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 6px;
  color: var(--text-main);
}

.t-desc {
  font-size: 14px;
  color: var(--text-sub);
  line-height: 1.6;
}

.tag {
  display: inline-block;
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
  background: var(--bg-body);
  color: var(--text-muted);
  margin-left: 8px;
  font-weight: normal;
}

.tag.highlight {
  background: var(--primary-light);
  color: var(--primary);
  font-weight: 600;
}

/* 右侧面板 */
.panel-action {
  background: #FFFFFF;
  padding: 48px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
}

.bg-circle {
  position: absolute;
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, rgba(245,158,11,0.08) 0%, rgba(255,255,255,0) 70%);
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 0;
  pointer-events: none;
}

/* 二维码卡片 */
.qr-card {
  position: relative;
  z-index: 1;
  background: var(--surface);
  padding: 20px;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
  border: 1px solid rgba(0,0,0,0.04);
  text-align: center;
  margin-bottom: 30px;
  width: 240px;
}

.qr-img {
  width: 100%;
  min-height: 180px;
  background: #F0F0F0;
  border-radius: 8px;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  font-size: 12px;
  overflow: hidden;
}

.qr-img img {
  width: 100%;
  height: auto;
  object-fit: contain;
}

.qr-hint {
  font-size: 13px;
  color: var(--text-sub);
  font-weight: 500;
}

.qr-link {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: var(--primary);
  text-decoration: none;
  font-weight: 600;
}

.qr-link:hover {
  text-decoration: underline;
}

/* 确认区域 */
.confirm-area {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 320px;
}

.confirm-label {
  display: block;
  text-align: center;
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 16px;
  color: var(--text-main);
}

.options {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 24px;
}

.option-btn {
  cursor: pointer;
  border: 2px solid var(--border);
  border-radius: 12px;
  padding: 12px;
  text-align: center;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-muted);
  transition: all 0.2s;
  background: transparent;
  user-select: none;
}

.option-btn:hover {
  border-color: var(--text-muted);
}

.option-btn.selected {
  border-color: var(--primary);
  background: var(--primary-light);
  color: var(--primary-hover);
}

/* 按钮 */
.cta-btn {
  width: 100%;
  height: 56px;
  border: none;
  border-radius: 56px;
  background: var(--primary);
  color: #FFF;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.3);
}

.cta-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(245, 158, 11, 0.4);
  background: var(--primary-hover);
}

.cta-btn:disabled {
  background: #E5E5E5;
  color: #A3A3A3;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

/* 错误提示 */
.error-msg {
  text-align: center;
  color: #EF4444;
  font-size: 13px;
  height: 20px;
  margin-top: -10px;
  margin-bottom: 10px;
  opacity: 0;
  transition: opacity 0.3s;
}

.error-msg.show {
  opacity: 1;
}

/* 感谢提示 */
.thank-you {
  text-align: center;
  margin-top: 24px;
  animation: fadeIn 0.5s ease;
}

.thank-icon {
  font-size: 48px;
  margin-bottom: 8px;
}

.thank-you p {
  color: var(--text-main);
  font-weight: 600;
  font-size: 16px;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 响应式 - 平板 */
@media (max-width: 900px) {
  .experiment-container {
    grid-template-columns: 1fr;
    max-width: 600px;
    margin: 0 auto;
  }
  
  .panel-info {
    padding: 32px;
    border-right: none;
    border-bottom: 1px solid var(--border);
  }
  
  .panel-action {
    padding: 32px;
  }
  
  .timeline {
    border-left: 2px dashed var(--border);
  }
}

/* 响应式 - 手机 */
@media (max-width: 480px) {
  .experiment-page {
    padding: 12px;
  }

  .experiment-container {
    border-radius: 16px;
  }
  
  .panel-info {
    padding: 24px 20px;
  }
  
  .panel-action {
    padding: 24px 20px;
  }
  
  .header {
    margin-bottom: 28px;
  }
  
  .brand {
    font-size: 16px;
  }
  
  .title {
    font-size: 24px;
  }
  
  .subtitle {
    font-size: 18px;
  }
  
  .timeline {
    padding-left: 24px;
    margin-left: 6px;
  }
  
  .timeline-dot {
    left: -32px;
    width: 12px;
    height: 12px;
  }
  
  .timeline-item {
    margin-bottom: 28px;
  }
  
  .t-title {
    font-size: 15px;
  }
  
  .t-desc {
    font-size: 13px;
  }
  
  .qr-card {
    width: 100%;
    max-width: 280px;
    padding: 16px;
    margin-bottom: 24px;
  }
  
  .confirm-area {
    max-width: 100%;
  }
  
  .options {
    gap: 10px;
  }
  
  .option-btn {
    padding: 10px 8px;
    font-size: 13px;
  }
  
  .cta-btn {
    height: 50px;
    font-size: 15px;
  }
  
  .thank-icon {
    font-size: 36px;
  }
  
  .thank-you p {
    font-size: 14px;
  }
}
</style>
