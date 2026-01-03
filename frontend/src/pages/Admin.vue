<template>
  <div class="admin-page">
    <!-- 顶部导航 -->
    <header class="admin-header">
      <div class="header-left">
        <button class="back-btn" @click="$router.push('/chat')">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M19 12H5M12 19l-7-7 7-7"/>
          </svg>
          <span>返回聊天</span>
        </button>
      </div>
      <h1 class="header-title">
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 15a3 3 0 100-6 3 3 0 000 6z"/>
          <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z"/>
        </svg>
        启明管理后台
      </h1>
      <div class="header-right">
        <span class="admin-badge">管理员</span>
      </div>
    </header>

    <!-- 标签页导航 -->
    <nav class="tab-nav">
      <button 
        v-for="tab in tabs" 
        :key="tab.id"
        class="tab-btn"
        :class="{ active: activeTab === tab.id }"
        @click="activeTab = tab.id"
      >
        <span class="tab-icon" v-html="tab.icon"></span>
        <span class="tab-label">{{ tab.label }}</span>
      </button>
    </nav>

    <!-- 内容区域 -->
    <main class="admin-content">
      <!-- 仪表盘 -->
      <section v-if="activeTab === 'dashboard'" class="panel dashboard-panel">
        <h2>系统概览</h2>
        <div class="stats-grid">
          <div class="stat-card users">
            <div class="stat-icon">👥</div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.user_count || 0 }}</div>
              <div class="stat-label">总用户数</div>
            </div>
          </div>
          <div class="stat-card messages">
            <div class="stat-icon">💬</div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.message_count || 0 }}</div>
              <div class="stat-label">总消息数</div>
            </div>
          </div>
          <div class="stat-card active">
            <div class="stat-icon">🔥</div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.active_users_today || 0 }}</div>
              <div class="stat-label">今日活跃</div>
            </div>
          </div>
          <div class="stat-card today">
            <div class="stat-icon">📊</div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.today_messages || 0 }}</div>
              <div class="stat-label">今日消息</div>
            </div>
          </div>
          <div class="stat-card invites">
            <div class="stat-icon">🎫</div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.available_invites || 0 }}</div>
              <div class="stat-label">可用邀请码</div>
            </div>
          </div>
        </div>
      </section>

      <!-- 用户管理 -->
      <section v-if="activeTab === 'users'" class="panel users-panel">
        <div class="panel-header">
          <h2>用户管理</h2>
          <div class="panel-actions">
            <input 
              v-model="userSearch" 
              type="text" 
              placeholder="搜索用户..."
              class="search-input"
            />
          </div>
        </div>

        <div class="users-table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>用户名</th>
                <th>实验条件</th>
                <th>消息数</th>
                <th>注册时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="user in filteredUsers" :key="user.id">
                <td class="id-cell">{{ user.id }}</td>
                <td class="username-cell">
                  <span class="username">{{ user.username }}</span>
                  <span v-if="user.id === 1" class="admin-tag">管理员</span>
                </td>
                <td class="condition-cell">
                  <span :class="['condition-badge', user.condition || 'none']">
                    {{ formatCondition(user.condition) }}
                  </span>
                </td>
                <td class="count-cell">{{ user.message_count }}</td>
                <td class="date-cell">{{ formatDate(user.created_at) }}</td>
                <td class="actions-cell">
                  <button class="action-btn view" @click="viewUserDetail(user)" title="查看详情">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                      <circle cx="12" cy="12" r="3"/>
                    </svg>
                  </button>
                  <button class="action-btn memory" @click="viewUserMemory(user)" title="查看记忆">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z"/>
                      <polyline points="3.27 6.96 12 12.01 20.73 6.96"/>
                      <line x1="12" y1="22.08" x2="12" y2="12"/>
                    </svg>
                  </button>
                  <button class="action-btn reset" @click="resetUserPassword(user)" title="重置密码">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                      <path d="M7 11V7a5 5 0 0110 0v4"/>
                    </svg>
                  </button>
                  <button 
                    v-if="user.id !== 1" 
                    class="action-btn delete" 
                    @click="deleteUser(user)" 
                    title="删除用户"
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <polyline points="3 6 5 6 21 6"/>
                      <path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/>
                    </svg>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- 记忆管理 -->
      <section v-if="activeTab === 'memory'" class="panel memory-panel">
        <div class="panel-header">
          <h2>记忆管理</h2>
          <button class="refresh-btn" @click="loadAllMemory">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="23 4 23 10 17 10"/>
              <path d="M20.49 15a9 9 0 11-2.12-9.36L23 10"/>
            </svg>
            刷新
          </button>
        </div>

        <div class="memory-grid">
          <div v-for="mem in memories" :key="mem.user_id" class="memory-card">
            <div class="memory-header">
              <span class="memory-user">{{ mem.username }}</span>
              <span class="memory-id">#{{ mem.user_id }}</span>
            </div>
            <div class="memory-stats">
              <span :class="['memory-badge', mem.has_long_term ? 'active' : '']">
                {{ mem.has_long_term ? '✓ 长期记忆' : '✗ 无长期记忆' }}
              </span>
              <span class="memory-badge">📁 {{ mem.history_count }} 历史文件</span>
            </div>
            <div v-if="mem.long_term_preview" class="memory-preview">
              {{ mem.long_term_preview }}
            </div>
            <div class="memory-actions">
              <button class="mem-btn edit" @click="editUserMemory(mem)">编辑记忆</button>
              <button class="mem-btn clear" @click="clearUserMemory(mem)">清空记忆</button>
            </div>
          </div>
        </div>
      </section>

      <!-- 邀请码管理 -->
      <section v-if="activeTab === 'invites'" class="panel invites-panel">
        <div class="panel-header">
          <h2>邀请码管理</h2>
          <div class="invite-create">
            <input 
              v-model.number="inviteCount" 
              type="number" 
              min="1" 
              max="50"
              placeholder="数量"
              class="invite-count-input"
            />
            <button class="create-btn" @click="createInvites" :disabled="loading">
              {{ loading ? '生成中...' : '生成邀请码' }}
            </button>
          </div>
        </div>

        <!-- 邀请码开关 -->
        <div class="invite-toggle-section">
          <div class="toggle-row">
            <div class="toggle-info">
              <span class="toggle-label">邀请码制度</span>
              <span class="toggle-desc">{{ inviteCodeEnabled ? '用户注册需要邀请码' : '用户可自由注册（无需邀请码）' }}</span>
            </div>
            <label class="toggle-switch">
              <input 
                type="checkbox" 
                v-model="inviteCodeEnabled" 
                @change="toggleInviteCode"
              />
              <span class="toggle-slider"></span>
            </label>
          </div>
        </div>

        <!-- 新生成的邀请码 -->
        <div v-if="newInvites.length > 0" class="new-invites-section">
          <h3>🎉 新生成的邀请码</h3>
          <div class="new-invites-list">
            <div v-for="code in newInvites" :key="code" class="new-invite-item">
              <code>{{ code }}</code>
              <button class="copy-btn" @click="copyCode(code)">复制</button>
            </div>
          </div>
        </div>

        <div class="invites-list">
          <div class="invites-filter">
            <button 
              :class="['filter-btn', inviteFilter === 'all' ? 'active' : '']"
              @click="inviteFilter = 'all'"
            >全部 ({{ invites.length }})</button>
            <button 
              :class="['filter-btn', inviteFilter === 'available' ? 'active' : '']"
              @click="inviteFilter = 'available'"
            >可用 ({{ invites.filter(i => !i.used).length }})</button>
            <button 
              :class="['filter-btn', inviteFilter === 'used' ? 'active' : '']"
              @click="inviteFilter = 'used'"
            >已用 ({{ invites.filter(i => i.used).length }})</button>
          </div>

          <table class="data-table invites-table">
            <thead>
              <tr>
                <th>邀请码</th>
                <th>状态</th>
                <th>使用者</th>
                <th>创建时间</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="invite in filteredInvites" :key="invite.code">
                <td class="code-cell">
                  <code>{{ invite.code }}</code>
                  <button class="mini-copy" @click="copyCode(invite.code)" title="复制">📋</button>
                </td>
                <td>
                  <span :class="['status-badge', invite.used ? 'used' : 'available']">
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

      <!-- 系统配置 -->
      <section v-if="activeTab === 'config'" class="panel config-panel">
        <div class="panel-header">
          <h2>系统配置</h2>
        </div>

        <div class="config-sections">
          <div class="config-section">
            <h3>上下文管理</h3>
            <p class="config-desc">配置AI对话的上下文参数</p>
            
            <div class="config-form">
              <div class="config-row">
                <label>最大消息条数</label>
                <input v-model.number="contextConfig.max_messages" type="number" min="10" max="100" />
                <span class="config-hint">保留最近N条消息</span>
              </div>
              <div class="config-row">
                <label>最大Token数</label>
                <input v-model.number="contextConfig.max_tokens" type="number" min="1000" max="32000" />
                <span class="config-hint">总上下文token限制</span>
              </div>
              <div class="config-row">
                <label>系统提示Token</label>
                <input v-model.number="contextConfig.system_prompt_tokens" type="number" min="50" max="500" />
                <span class="config-hint">预留给系统提示</span>
              </div>
              <div class="config-row">
                <label>保留Token</label>
                <input v-model.number="contextConfig.reserve_tokens" type="number" min="500" max="4000" />
                <span class="config-hint">预留给AI回复</span>
              </div>
            </div>
            
            <button class="save-btn" @click="saveContextConfig" :disabled="loading">
              {{ loading ? '保存中...' : '保存配置' }}
            </button>
          </div>
        </div>
      </section>
    </main>

    <!-- 用户详情弹窗 -->
    <Transition name="modal">
      <div v-if="showUserModal" class="modal-overlay" @click.self="showUserModal = false">
        <div class="modal user-detail-modal">
          <div class="modal-header">
            <h3>用户详情 - {{ selectedUser?.username }}</h3>
            <button class="close-btn" @click="showUserModal = false">×</button>
          </div>
          <div class="modal-body">
            <div class="user-info-grid">
              <div class="info-item">
                <span class="info-label">用户ID</span>
                <span class="info-value">{{ selectedUser?.id }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">用户名</span>
                <span class="info-value">{{ selectedUser?.username }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">消息数</span>
                <span class="info-value">{{ selectedUser?.message_count }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">注册时间</span>
                <span class="info-value">{{ formatDate(selectedUser?.created_at) }}</span>
              </div>
            </div>
            
            <div class="chat-history-section">
              <h4>最近聊天记录</h4>
              <div class="history-list">
                <div 
                  v-for="msg in userHistory" 
                  :key="msg.id" 
                  :class="['history-msg', msg.role]"
                >
                  <span class="msg-role">{{ msg.role === 'user' ? '用户' : '启明' }}</span>
                  <span class="msg-content">{{ msg.content?.substring(0, 100) }}{{ msg.content?.length > 100 ? '...' : '' }}</span>
                  <span class="msg-time">{{ formatTime(msg.timestamp) }}</span>
                </div>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button class="modal-btn danger" @click="clearUserHistoryAction">清空聊天记录</button>
            <button class="modal-btn" @click="showUserModal = false">关闭</button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- 记忆编辑弹窗 -->
    <Transition name="modal">
      <div v-if="showMemoryModal" class="modal-overlay" @click.self="showMemoryModal = false">
        <div class="modal memory-edit-modal">
          <div class="modal-header">
            <h3>编辑记忆 - {{ editingMemory?.username }}</h3>
            <button class="close-btn" @click="showMemoryModal = false">×</button>
          </div>
          <div class="modal-body">
            <div v-if="memoryLoading" class="loading-state">加载中...</div>
            <template v-else>
              <div class="memory-section">
                <h4>长期记忆</h4>
                <textarea 
                  v-model="editingLongTermMemory"
                  class="memory-textarea"
                  rows="15"
                  placeholder="输入用户的长期记忆内容..."
                ></textarea>
              </div>
              
              <div v-if="editingMemoryHistory.length" class="history-files-section">
                <h4>历史文件 ({{ editingMemoryHistory.length }})</h4>
                <div class="history-files-list">
                  <div v-for="file in editingMemoryHistory" :key="file.name" class="history-file">
                    <span class="file-name">{{ file.name }}</span>
                    <button class="view-file-btn" @click="viewHistoryFile(file)">查看</button>
                  </div>
                </div>
              </div>
            </template>
          </div>
          <div class="modal-footer">
            <button class="modal-btn primary" @click="saveMemoryEdit" :disabled="loading">
              {{ loading ? '保存中...' : '保存记忆' }}
            </button>
            <button class="modal-btn" @click="showMemoryModal = false">取消</button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { adminAPI, configAPI } from '../api'
import { toast, confirm } from '../utils/toast'

// 标签页配置
const tabs = [
  { id: 'dashboard', label: '仪表盘', icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="9"/><rect x="14" y="3" width="7" height="5"/><rect x="14" y="12" width="7" height="9"/><rect x="3" y="16" width="7" height="5"/></svg>' },
  { id: 'users', label: '用户管理', icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/></svg>' },
  { id: 'memory', label: '记忆管理', icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z"/></svg>' },
  { id: 'invites', label: '邀请码', icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="M7 8h10M7 12h10M7 16h6"/></svg>' },
  { id: 'config', label: '系统配置', icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"/></svg>' }
]

const activeTab = ref('dashboard')
const loading = ref(false)

// 数据
const stats = ref({})
const users = ref([])
const invites = ref([])
const memories = ref([])
const userSearch = ref('')
const inviteFilter = ref('all')
const inviteCount = ref(5)
const newInvites = ref([])
const inviteCodeEnabled = ref(true)

// 用户详情弹窗
const showUserModal = ref(false)
const selectedUser = ref(null)
const userHistory = ref([])

// 记忆编辑弹窗
const showMemoryModal = ref(false)
const editingMemory = ref(null)
const editingLongTermMemory = ref('')
const editingMemoryHistory = ref([])
const memoryLoading = ref(false)

// 配置
const contextConfig = ref({
  max_messages: 80,
  max_tokens: 12000,
  system_prompt_tokens: 100,
  reserve_tokens: 1000
})

// 过滤用户
const filteredUsers = computed(() => {
  if (!userSearch.value) return users.value
  const search = userSearch.value.toLowerCase()
  return users.value.filter(u => 
    u.username.toLowerCase().includes(search) || 
    u.id.toString().includes(search)
  )
})

// 过滤邀请码
const filteredInvites = computed(() => {
  if (inviteFilter.value === 'all') return invites.value
  if (inviteFilter.value === 'available') return invites.value.filter(i => !i.used)
  return invites.value.filter(i => i.used)
})

// 加载数据
const loadStats = async () => {
  try {
    stats.value = await adminAPI.getStats()
  } catch (err) {
    console.error('加载统计失败:', err)
  }
}

const loadUsers = async () => {
  try {
    const res = await adminAPI.getUsers()
    users.value = res.users
  } catch (err) {
    console.error('加载用户失败:', err)
    if (err.response?.status === 403) {
      toast.error('需要管理员权限')
    }
  }
}

const loadInvites = async () => {
  try {
    const res = await adminAPI.getInvites()
    invites.value = res.invites
  } catch (err) {
    console.error('加载邀请码失败:', err)
  }
}

const loadInviteCodeSetting = async () => {
  try {
    const res = await adminAPI.getInviteCodeSetting()
    inviteCodeEnabled.value = res.invite_code_enabled
  } catch (err) {
    console.error('加载邀请码设置失败:', err)
  }
}

const toggleInviteCode = async () => {
  try {
    const res = await adminAPI.setInviteCodeSetting(inviteCodeEnabled.value)
    toast.success(res.message)
  } catch (err) {
    console.error('切换邀请码设置失败:', err)
    toast.error('设置失败')
    // 恢复原值
    inviteCodeEnabled.value = !inviteCodeEnabled.value
  }
}

const loadAllMemory = async () => {
  try {
    const res = await adminAPI.getAllMemory()
    memories.value = res.memories
  } catch (err) {
    console.error('加载记忆失败:', err)
  }
}

const loadContextConfig = async () => {
  try {
    contextConfig.value = await configAPI.getContextConfig()
  } catch (err) {
    console.error('加载配置失败:', err)
  }
}

// 操作
const createInvites = async () => {
  if (inviteCount.value < 1 || inviteCount.value > 50) {
    toast.error('生成数量需在1-50之间')
    return
  }
  
  loading.value = true
  try {
    const res = await adminAPI.createInvites(inviteCount.value)
    newInvites.value = res.codes
    await loadInvites()
    toast.success(`成功生成 ${res.count} 个邀请码`)
  } catch (err) {
    toast.error('生成邀请码失败')
  } finally {
    loading.value = false
  }
}

const copyCode = (code) => {
  navigator.clipboard.writeText(code).then(() => {
    toast.success('已复制到剪贴板')
  }).catch(() => {
    toast.error('复制失败')
  })
}

const viewUserDetail = async (user) => {
  selectedUser.value = user
  showUserModal.value = true
  
  try {
    const res = await adminAPI.getUserHistory(user.id, 50)
    userHistory.value = res.history
  } catch (err) {
    console.error('加载聊天记录失败:', err)
  }
}

const viewUserMemory = async (user) => {
  editingMemory.value = user
  showMemoryModal.value = true
  memoryLoading.value = true
  
  try {
    const res = await adminAPI.getUserMemory(user.id)
    editingLongTermMemory.value = res.memory.long_term || ''
    editingMemoryHistory.value = res.memory.history_files || []
  } catch (err) {
    console.error('加载记忆失败:', err)
    toast.error('加载记忆失败')
  } finally {
    memoryLoading.value = false
  }
}

const editUserMemory = async (mem) => {
  editingMemory.value = mem
  showMemoryModal.value = true
  memoryLoading.value = true
  
  try {
    const res = await adminAPI.getUserMemory(mem.user_id)
    editingLongTermMemory.value = res.memory.long_term || ''
    editingMemoryHistory.value = res.memory.history_files || []
  } catch (err) {
    console.error('加载记忆失败:', err)
    toast.error('加载记忆失败')
  } finally {
    memoryLoading.value = false
  }
}

const saveMemoryEdit = async () => {
  if (!editingMemory.value) return
  
  loading.value = true
  try {
    await adminAPI.updateUserLongTermMemory(
      editingMemory.value.user_id || editingMemory.value.id,
      editingLongTermMemory.value
    )
    toast.success('记忆保存成功')
    showMemoryModal.value = false
    await loadAllMemory()
  } catch (err) {
    toast.error('保存记忆失败')
  } finally {
    loading.value = false
  }
}

const clearUserMemory = async (mem) => {
  const confirmed = await confirm({
    title: '清空记忆',
    message: `确定要清空 ${mem.username} 的所有记忆吗？此操作不可恢复！`,
    type: 'danger',
    confirmText: '确认清空'
  })
  
  if (confirmed) {
    try {
      await adminAPI.clearUserMemory(mem.user_id)
      toast.success('记忆已清空')
      await loadAllMemory()
    } catch (err) {
      toast.error('清空记忆失败')
    }
  }
}

const viewHistoryFile = async (file) => {
  try {
    const res = await adminAPI.getHistoryFile(
      editingMemory.value.user_id || editingMemory.value.id,
      file.name
    )
    alert(res.content)
  } catch (err) {
    toast.error('加载文件失败')
  }
}

const resetUserPassword = async (user) => {
  const newPassword = prompt(`请输入 ${user.username} 的新密码:`)
  if (!newPassword) return
  
  if (newPassword.length < 6) {
    toast.error('密码至少需要6个字符')
    return
  }
  
  try {
    await adminAPI.resetPassword(user.id, newPassword)
    toast.success(`已重置 ${user.username} 的密码`)
  } catch (err) {
    toast.error('重置密码失败')
  }
}

const deleteUser = async (user) => {
  const confirmed = await confirm({
    title: '删除用户',
    message: `确定要删除用户 ${user.username} 吗？此操作将删除该用户的所有数据！`,
    type: 'danger',
    confirmText: '确认删除'
  })
  
  if (confirmed) {
    try {
      await adminAPI.deleteUser(user.id)
      toast.success('用户已删除')
      await loadUsers()
      await loadStats()
    } catch (err) {
      toast.error(err.response?.data?.detail || '删除失败')
    }
  }
}

const clearUserHistoryAction = async () => {
  if (!selectedUser.value) return
  
  const confirmed = await confirm({
    title: '清空聊天记录',
    message: `确定要清空 ${selectedUser.value.username} 的所有聊天记录吗？`,
    type: 'danger',
    confirmText: '确认清空'
  })
  
  if (confirmed) {
    try {
      await adminAPI.clearUserHistory(selectedUser.value.id)
      toast.success('聊天记录已清空')
      userHistory.value = []
    } catch (err) {
      toast.error('清空失败')
    }
  }
}

const saveContextConfig = async () => {
  loading.value = true
  try {
    await configAPI.updateContextConfig(contextConfig.value)
    toast.success('配置保存成功')
  } catch (err) {
    toast.error('保存配置失败')
  } finally {
    loading.value = false
  }
}

// 格式化
const formatDate = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('zh-CN')
}

const formatTime = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return `${date.getMonth() + 1}/${date.getDate()} ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
}

const formatCondition = (condition) => {
  const map = {
    'emotional': '情感表露',
    'factual': '事实表露',
    'none': '无表露'
  }
  return map[condition] || '无表露'
}

onMounted(() => {
  loadStats()
  loadUsers()
  loadInvites()
  loadInviteCodeSetting()
  loadAllMemory()
  loadContextConfig()
})
</script>

<style scoped>
.admin-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  color: #fff;
}

/* Header */
.admin-header {
  background: rgba(0, 0, 0, 0.3);
  padding: 1rem 2rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
}

.header-left {
  flex: 1;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #fff;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.back-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

.header-title {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0;
  color: #ffd700;
}

.header-right {
  flex: 1;
  display: flex;
  justify-content: flex-end;
}

.admin-badge {
  background: linear-gradient(135deg, #ffd700, #ffa500);
  color: #1a1a2e;
  padding: 0.4rem 1rem;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 600;
}

/* Tab Navigation */
.tab-nav {
  display: flex;
  gap: 0.5rem;
  padding: 1rem 2rem;
  background: rgba(0, 0, 0, 0.2);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  overflow-x: auto;
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.7);
  padding: 0.75rem 1.25rem;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.tab-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.tab-btn.active {
  background: linear-gradient(135deg, #ffd700, #ffa500);
  color: #1a1a2e;
  border-color: transparent;
}

.tab-icon {
  display: flex;
}

/* Content Area */
.admin-content {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.panel {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  padding: 1.5rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.panel h2 {
  margin: 0 0 1.5rem 0;
  font-size: 1.5rem;
  color: #ffd700;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.panel-header h2 {
  margin: 0;
}

/* Dashboard Stats */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
}

.stat-card {
  background: rgba(0, 0, 0, 0.3);
  border-radius: 12px;
  padding: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
  transition: transform 0.2s;
}

.stat-card:hover {
  transform: translateY(-4px);
}

.stat-icon {
  font-size: 2.5rem;
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: #ffd700;
}

.stat-label {
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.9rem;
}

/* Search Input */
.search-input {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #fff;
  padding: 0.6rem 1rem;
  border-radius: 8px;
  width: 200px;
}

.search-input::placeholder {
  color: rgba(255, 255, 255, 0.5);
}

/* Data Table */
.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table thead {
  background: rgba(0, 0, 0, 0.3);
}

.data-table th {
  padding: 1rem;
  text-align: left;
  color: #ffd700;
  font-weight: 600;
  border-bottom: 2px solid rgba(255, 215, 0, 0.3);
}

.data-table td {
  padding: 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.data-table tbody tr:hover {
  background: rgba(255, 255, 255, 0.05);
}

.username-cell {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.admin-tag {
  background: linear-gradient(135deg, #ffd700, #ffa500);
  color: #1a1a2e;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 600;
}

/* Condition Badge */
.condition-badge {
  padding: 0.25rem 0.6rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
}

.condition-badge.emotional {
  background: rgba(239, 68, 68, 0.2);
  color: #f87171;
  border: 1px solid rgba(239, 68, 68, 0.3);
}

.condition-badge.factual {
  background: rgba(59, 130, 246, 0.2);
  color: #60a5fa;
  border: 1px solid rgba(59, 130, 246, 0.3);
}

.condition-badge.none {
  background: rgba(156, 163, 175, 0.2);
  color: #9ca3af;
  border: 1px solid rgba(156, 163, 175, 0.3);
}

/* Action Buttons */
.actions-cell {
  display: flex;
  gap: 0.5rem;
}

.action-btn {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  border: none;
  padding: 0;
  line-height: 0;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.action-btn svg {
  display: block;
}

.action-btn.view {
  background: rgba(59, 130, 246, 0.2);
  color: #3b82f6;
}

.action-btn.memory {
  background: rgba(168, 85, 247, 0.2);
  color: #a855f7;
}

.action-btn.reset {
  background: rgba(245, 158, 11, 0.2);
  color: #f59e0b;
}

.action-btn.delete {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

.action-btn:hover {
  transform: scale(1.1);
}

/* Memory Panel */
.memory-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1rem;
}

.memory-card {
  background: rgba(0, 0, 0, 0.3);
  border-radius: 12px;
  padding: 1.25rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.memory-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}

.memory-user {
  font-weight: 600;
  color: #ffd700;
}

.memory-id {
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.85rem;
}

.memory-stats {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
  flex-wrap: wrap;
}

.memory-badge {
  background: rgba(255, 255, 255, 0.1);
  padding: 0.3rem 0.6rem;
  border-radius: 6px;
  font-size: 0.8rem;
}

.memory-badge.active {
  background: rgba(34, 197, 94, 0.2);
  color: #22c55e;
}

.memory-preview {
  background: rgba(0, 0, 0, 0.2);
  padding: 0.75rem;
  border-radius: 8px;
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 0.75rem;
  max-height: 100px;
  overflow: hidden;
}

.memory-actions {
  display: flex;
  gap: 0.5rem;
}

.mem-btn {
  flex: 1;
  padding: 0.5rem;
  border-radius: 6px;
  border: none;
  cursor: pointer;
  font-size: 0.85rem;
  transition: all 0.2s;
}

.mem-btn.edit {
  background: rgba(59, 130, 246, 0.2);
  color: #3b82f6;
}

.mem-btn.clear {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

.mem-btn:hover {
  transform: translateY(-2px);
}

/* Invites */
.invite-create {
  display: flex;
  gap: 0.75rem;
}

.invite-count-input {
  width: 80px;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #fff;
  padding: 0.6rem;
  border-radius: 8px;
  text-align: center;
}

.create-btn {
  background: linear-gradient(135deg, #ffd700, #ffa500);
  color: #1a1a2e;
  border: none;
  padding: 0.6rem 1.25rem;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.create-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(255, 215, 0, 0.3);
}

.new-invites-section {
  background: rgba(34, 197, 94, 0.1);
  border: 1px solid rgba(34, 197, 94, 0.3);
  border-radius: 12px;
  padding: 1.25rem;
  margin-bottom: 1.5rem;
}

.new-invites-section h3 {
  margin: 0 0 1rem 0;
  color: #22c55e;
}

.new-invites-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.new-invite-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  background: rgba(0, 0, 0, 0.2);
  padding: 0.75rem;
  border-radius: 8px;
}

.new-invite-item code {
  flex: 1;
  font-family: 'JetBrains Mono', monospace;
  color: #22c55e;
}

.copy-btn {
  background: rgba(34, 197, 94, 0.2);
  color: #22c55e;
  border: none;
  padding: 0.4rem 0.75rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85rem;
}

.invites-filter {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.filter-btn {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: rgba(255, 255, 255, 0.7);
  padding: 0.5rem 1rem;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.filter-btn.active {
  background: rgba(255, 215, 0, 0.2);
  color: #ffd700;
  border-color: #ffd700;
}

.code-cell {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.code-cell code {
  font-family: 'JetBrains Mono', monospace;
  color: #ffd700;
}

.mini-copy {
  background: transparent;
  border: none;
  cursor: pointer;
  opacity: 0.5;
  transition: opacity 0.2s;
}

.mini-copy:hover {
  opacity: 1;
}

.status-badge {
  padding: 0.3rem 0.75rem;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 600;
}

.status-badge.available {
  background: rgba(34, 197, 94, 0.2);
  color: #22c55e;
}

.status-badge.used {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

/* Config */
.config-sections {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.config-section {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 12px;
  padding: 1.5rem;
}

.config-section h3 {
  margin: 0 0 0.5rem 0;
  color: #ffd700;
}

.config-desc {
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 1.5rem;
}

.config-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.config-row {
  display: grid;
  grid-template-columns: 150px 150px 1fr;
  gap: 1rem;
  align-items: center;
}

.config-row label {
  font-weight: 500;
}

.config-row input {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #fff;
  padding: 0.6rem;
  border-radius: 8px;
}

.config-hint {
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.85rem;
}

.save-btn {
  background: linear-gradient(135deg, #ffd700, #ffa500);
  color: #1a1a2e;
  border: none;
  padding: 0.75rem 2rem;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  margin-top: 1rem;
  align-self: flex-start;
}

.save-btn:hover:not(:disabled) {
  transform: translateY(-2px);
}

.refresh-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #fff;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  cursor: pointer;
}

/* Modals */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 2rem;
}

.modal {
  background: #1a1a2e;
  border-radius: 16px;
  width: 100%;
  max-width: 700px;
  max-height: 80vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.modal-header h3 {
  margin: 0;
  color: #ffd700;
}

.close-btn {
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.7);
  font-size: 1.5rem;
  cursor: pointer;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.1);
}

.modal-body {
  padding: 1.5rem;
  overflow-y: auto;
  flex: 1;
}

.modal-footer {
  padding: 1rem 1.5rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

.modal-btn {
  padding: 0.6rem 1.25rem;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: transparent;
  color: #fff;
  cursor: pointer;
  transition: all 0.2s;
}

.modal-btn:hover {
  background: rgba(255, 255, 255, 0.1);
}

.modal-btn.primary {
  background: linear-gradient(135deg, #ffd700, #ffa500);
  color: #1a1a2e;
  border: none;
  font-weight: 600;
}

.modal-btn.danger {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
  border-color: rgba(239, 68, 68, 0.3);
}

/* User Info Grid */
.user-info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.info-item {
  background: rgba(0, 0, 0, 0.2);
  padding: 0.75rem;
  border-radius: 8px;
}

.info-label {
  display: block;
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.85rem;
  margin-bottom: 0.25rem;
}

.info-value {
  font-weight: 500;
  color: #ffd700;
}

/* Chat History */
.chat-history-section h4 {
  margin: 0 0 1rem 0;
  color: #ffd700;
}

.history-list {
  max-height: 300px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.history-msg {
  display: flex;
  gap: 0.75rem;
  padding: 0.75rem;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  align-items: flex-start;
}

.history-msg.assistant {
  border-left: 3px solid #ffd700;
}

.history-msg.user {
  border-left: 3px solid #3b82f6;
}

.msg-role {
  font-weight: 600;
  min-width: 40px;
  color: #ffd700;
}

.history-msg.user .msg-role {
  color: #3b82f6;
}

.msg-content {
  flex: 1;
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.9rem;
}

.msg-time {
  color: rgba(255, 255, 255, 0.4);
  font-size: 0.75rem;
  white-space: nowrap;
}

/* Memory Edit Modal */
.memory-textarea {
  width: 100%;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #fff;
  padding: 1rem;
  border-radius: 8px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.9rem;
  resize: vertical;
}

.memory-section h4 {
  margin: 0 0 0.75rem 0;
  color: #ffd700;
}

.history-files-section {
  margin-top: 1.5rem;
}

.history-files-section h4 {
  margin: 0 0 0.75rem 0;
  color: #ffd700;
}

.history-files-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.history-file {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(0, 0, 0, 0.2);
  padding: 0.6rem 0.75rem;
  border-radius: 6px;
}

.file-name {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.9rem;
}

.view-file-btn {
  background: rgba(59, 130, 246, 0.2);
  color: #3b82f6;
  border: none;
  padding: 0.3rem 0.6rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.8rem;
}

.loading-state {
  text-align: center;
  padding: 2rem;
  color: rgba(255, 255, 255, 0.5);
}

/* Invite Toggle Section */
.invite-toggle-section {
  background: rgba(0, 0, 0, 0.3);
  border-radius: 12px;
  padding: 1.25rem;
  margin-bottom: 1.5rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.toggle-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.toggle-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.toggle-label {
  font-weight: 600;
  font-size: 1rem;
  color: #ffd700;
}

.toggle-desc {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.6);
}

.toggle-switch {
  position: relative;
  display: inline-block;
  width: 56px;
  height: 30px;
}

.toggle-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.2);
  transition: 0.3s;
  border-radius: 30px;
}

.toggle-slider:before {
  position: absolute;
  content: "";
  height: 22px;
  width: 22px;
  left: 4px;
  bottom: 4px;
  background-color: white;
  transition: 0.3s;
  border-radius: 50%;
}

.toggle-switch input:checked + .toggle-slider {
  background: linear-gradient(135deg, #ffd700, #ffa500);
}

.toggle-switch input:checked + .toggle-slider:before {
  transform: translateX(26px);
}

/* Modal Transitions */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}

.modal-enter-active .modal,
.modal-leave-active .modal {
  transition: transform 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .modal,
.modal-leave-to .modal {
  transform: scale(0.95);
}

/* Responsive */
@media (max-width: 768px) {
  .admin-header {
    flex-direction: column;
    gap: 1rem;
    padding: 1rem;
  }
  
  .header-left, .header-right {
    justify-content: center;
  }
  
  .tab-nav {
    padding: 0.75rem 1rem;
  }
  
  .tab-label {
    display: none;
  }
  
  .admin-content {
    padding: 1rem;
  }
  
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .config-row {
    grid-template-columns: 1fr;
  }
  
  .user-info-grid {
    grid-template-columns: 1fr;
  }
  
  .panel-header {
    flex-direction: column;
    gap: 1rem;
    align-items: flex-start;
  }
  
  .invite-create {
    width: 100%;
  }
  
  .invite-count-input {
    flex: 1;
  }
}
</style>
