<template>
  <div class="admin-page">
    <header class="admin-header">
      <button class="back-btn" @click="$router.back()">
        <span>← 返回</span>
      </button>
      <h1>管理面板</h1>
      <div></div>
    </header>

    <div class="admin-content">
      <!-- 用户管理 -->
      <section class="admin-section">
        <h2>📊 用户管理</h2>
        <div class="stats">
          <div class="stat-card">
            <div class="stat-value">{{ users.length }}</div>
            <div class="stat-label">总用户数</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ invites.filter(i => !i.used).length }}</div>
            <div class="stat-label">可用邀请码</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ invites.filter(i => i.used).length }}</div>
            <div class="stat-label">已使用邀请码</div>
          </div>
        </div>

        <div class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>用户名</th>
                <th>注册时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="user in users" :key="user.id">
                <td>{{ user.id }}</td>
                <td>{{ user.username }}</td>
                <td>{{ formatDate(user.created_at) }}</td>
                <td>
                  <button @click="resetUserPassword(user)" class="action-btn">
                    重置密码
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- 邀请码管理 -->
      <section class="admin-section">
        <h2>🎫 邀请码管理</h2>
        
        <div class="create-invite">
          <label>生成数量:</label>
          <input 
            v-model.number="inviteCount" 
            type="number" 
            min="1" 
            max="100"
            placeholder="1-100"
          />
          <button @click="createInvites" :disabled="loading">
            {{ loading ? '生成中...' : '生成邀请码' }}
          </button>
        </div>

        <div v-if="newInvites.length > 0" class="new-invites">
          <h3>新生成的邀请码:</h3>
          <div v-for="code in newInvites" :key="code" class="invite-code">
            <code>{{ code }}</code>
            <button @click="copyToClipboard(code)" class="copy-btn">复制</button>
          </div>
        </div>

        <h3>所有邀请码</h3>
        <div class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>邀请码</th>
                <th>状态</th>
                <th>使用者ID</th>
                <th>创建时间</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="invite in invites" :key="invite.code">
                <td><code>{{ invite.code }}</code></td>
                <td>
                  <span class="status-badge" :class="invite.used ? 'used' : 'available'">
                    {{ invite.used ? '已使用' : '可用' }}
                  </span>
                </td>
                <td>{{ invite.used_by || '-' }}</td>
                <td>{{ formatDate(invite.created_at) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- 上下文配置 -->
      <section class="admin-section">
        <h2>⚙️ 上下文配置</h2>
        <p class="section-description">配置AI对话的上下文管理参数</p>
        
        <div class="config-form">
          <div class="config-item">
            <label>最大消息条数：</label>
            <input
              v-model.number="contextConfig.max_messages"
              type="number"
              min="1"
              max="100"
            />
            <span class="config-hint">保留最近N条消息（1-100）</span>
          </div>
          
          <div class="config-item">
            <label>最大Token数：</label>
            <input
              v-model.number="contextConfig.max_tokens"
              type="number"
              min="500"
              max="32000"
            />
            <span class="config-hint">总上下文token限制（500-32000）</span>
          </div>
          
          <div class="config-item">
            <label>系统提示Token：</label>
            <input
              v-model.number="contextConfig.system_prompt_tokens"
              type="number"
              min="50"
              max="500"
            />
            <span class="config-hint">预留给系统提示的token数</span>
          </div>
          
          <div class="config-item">
            <label>保留Token：</label>
            <input
              v-model.number="contextConfig.reserve_tokens"
              type="number"
              min="500"
              max="4000"
            />
            <span class="config-hint">预留给AI回复的token数</span>
          </div>
          
          <button @click="saveContextConfig" :disabled="loading" class="save-config-btn">
            {{ loading ? '保存中...' : '保存配置' }}
          </button>
        </div>
      </section>

      <!-- 系统推送 -->
      <section class="admin-section">
        <h2>📢 系统推送</h2>
        <p class="section-description">向所有用户推送系统消息（定时消息功能）</p>
        
        <div class="push-form">
          <textarea
            v-model="pushMessage"
            placeholder="输入系统消息..."
            rows="4"
          ></textarea>
          <button @click="sendPushMessage" :disabled="!pushMessage.trim() || loading">
            发送推送
          </button>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { adminAPI, configAPI } from '../api'

const users = ref([])
const invites = ref([])
const inviteCount = ref(1)
const newInvites = ref([])
const pushMessage = ref('')
const loading = ref(false)

// 上下文配置
const contextConfig = ref({
  max_messages: 20,
  max_tokens: 4000,
  system_prompt_tokens: 100,
  reserve_tokens: 1000
})

// 加载用户列表
const loadUsers = async () => {
  try {
    const response = await adminAPI.getUsers()
    users.value = response.users
  } catch (err) {
    console.error('加载用户失败:', err)
    if (err.response?.status === 403) {
      alert('需要管理员权限')
    }
  }
}

// 加载邀请码列表
const loadInvites = async () => {
  try {
    const response = await adminAPI.getInvites()
    invites.value = response.invites
  } catch (err) {
    console.error('加载邀请码失败:', err)
  }
}

// 加载上下文配置
const loadContextConfig = async () => {
  try {
    const config = await configAPI.getContextConfig()
    contextConfig.value = config
  } catch (err) {
    console.error('加载上下文配置失败:', err)
  }
}

// 保存上下文配置
const saveContextConfig = async () => {
  loading.value = true
  try {
    await configAPI.updateContextConfig(contextConfig.value)
    alert('配置保存成功！')
  } catch (err) {
    console.error('保存配置失败:', err)
    alert('保存配置失败：' + (err.response?.data?.detail || '未知错误'))
  } finally {
    loading.value = false
  }
}

// 创建邀请码
const createInvites = async () => {
  if (inviteCount.value < 1 || inviteCount.value > 100) {
    alert('生成数量必须在1-100之间')
    return
  }

  loading.value = true
  try {
    const response = await adminAPI.createInvites(inviteCount.value)
    newInvites.value = response.codes
    await loadInvites()
    alert(`成功生成 ${response.count} 个邀请码`)
  } catch (err) {
    console.error('创建邀请码失败:', err)
    alert('创建邀请码失败')
  } finally {
    loading.value = false
  }
}

// 重置用户密码
const resetUserPassword = async (user) => {
  const newPassword = prompt(`请输入 ${user.username} 的新密码:`)
  if (!newPassword) return

  if (newPassword.length < 6) {
    alert('密码至少需要6个字符')
    return
  }

  try {
    await adminAPI.resetPassword(user.id, newPassword)
    alert(`已成功重置 ${user.username} 的密码`)
  } catch (err) {
    console.error('重置密码失败:', err)
    alert('重置密码失败')
  }
}

// 发送推送消息
const sendPushMessage = async () => {
  if (!pushMessage.value.trim()) return

  if (!confirm('确定要向所有用户发送这条消息吗？')) {
    return
  }

  loading.value = true
  try {
    // TODO: 后端实现推送功能
    alert('推送功能开发中')
    pushMessage.value = ''
  } catch (err) {
    console.error('发送推送失败:', err)
    alert('发送推送失败')
  } finally {
    loading.value = false
  }
}

// 复制到剪贴板
const copyToClipboard = (text) => {
  navigator.clipboard.writeText(text).then(() => {
    alert('已复制到剪贴板')
  }).catch(() => {
    alert('复制失败')
  })
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}

onMounted(() => {
  loadUsers()
  loadInvites()
  loadContextConfig()
})
</script>

<style scoped>
.admin-page {
  min-height: 100vh;
  background: var(--color-bg-light);
}

.admin-header {
  background: var(--color-secondary);
  padding: 1rem 1.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.admin-header h1 {
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

.admin-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem 1.5rem;
}

.admin-section {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  margin-bottom: 2rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.admin-section h2 {
  margin: 0 0 1.5rem 0;
  font-size: 1.5rem;
  color: var(--color-dark);
}

.section-description {
  color: #666;
  margin-bottom: 1rem;
}

/* 统计卡片 */
.stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%);
  padding: 2rem;
  border-radius: 12px;
  text-align: center;
  color: var(--color-dark);
}

.stat-value {
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}

.stat-label {
  font-size: 1rem;
  opacity: 0.8;
}

/* 表格 */
.table-container {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table thead {
  background: var(--color-bg-light);
}

.data-table th {
  padding: 1rem;
  text-align: left;
  font-weight: 600;
  border-bottom: 2px solid var(--color-primary);
}

.data-table td {
  padding: 1rem;
  border-bottom: 1px solid #e0e0e0;
}

.data-table tbody tr:hover {
  background: var(--color-bg-light);
}

.action-btn {
  padding: 0.5rem 1rem;
  font-size: 0.9rem;
  background: var(--color-accent);
  color: white;
}

/* 邀请码生成 */
.create-invite {
  display: flex;
  gap: 1rem;
  align-items: center;
  margin-bottom: 2rem;
}

.create-invite label {
  font-weight: 600;
}

.create-invite input {
  width: 150px;
}

.new-invites {
  background: var(--color-bg-light);
  padding: 1.5rem;
  border-radius: 8px;
  margin-bottom: 2rem;
}

.new-invites h3 {
  margin: 0 0 1rem 0;
}

.invite-code {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 0.75rem;
}

.invite-code code {
  flex: 1;
  background: white;
  padding: 0.75rem;
  border-radius: 6px;
  font-family: 'Courier New', monospace;
  border: 1px solid #ddd;
}

.copy-btn {
  padding: 0.5rem 1rem;
  font-size: 0.9rem;
  background: var(--color-primary);
}

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 600;
}

.status-badge.available {
  background: #d4edda;
  color: #155724;
}

.status-badge.used {
  background: #f8d7da;
  color: #721c24;
}

/* 推送表单 */
.push-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.push-form textarea {
  width: 100%;
  padding: 1rem;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-family: inherit;
  resize: vertical;
}

.push-form button {
  align-self: flex-start;
}

/* 配置表单 */
.config-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.config-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.config-item label {
  font-weight: 600;
  color: var(--color-dark);
}

.config-item input {
  padding: 0.6rem;
  border: 2px solid #ddd;
  border-radius: 6px;
  font-size: 1rem;
}

.config-hint {
  font-size: 0.85rem;
  color: #666;
}

.save-config-btn {
  background: var(--color-primary);
  align-self: flex-start;
  padding: 0.8rem 2rem;
}

@media (max-width: 768px) {
  .create-invite {
    flex-direction: column;
    align-items: stretch;
  }
  
  .create-invite input {
    width: 100%;
  }
  
  .stats {
    grid-template-columns: 1fr;
  }
  
  .config-item input {
    width: 100%;
  }
}
</style>
