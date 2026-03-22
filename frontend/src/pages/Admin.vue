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
        <div class="charts-row">
          <div class="chart-card">
            <div class="chart-card-header">
              <h3>用户消息量</h3>
              <span>按用户统计</span>
            </div>
            <div class="chart-wrap">
              <canvas ref="barChartRef"></canvas>
            </div>
          </div>
          <div class="chart-card">
            <div class="chart-card-header">
              <h3>实验条件分布</h3>
              <span>none / emotional / factual</span>
            </div>
            <div class="chart-wrap">
              <canvas ref="doughnutChartRef"></canvas>
            </div>
          </div>
        </div>
      </section>

      <section v-if="activeTab === 'analytics'" class="panel analytics-panel">
        <div class="panel-header">
          <h2>详细统计</h2>
          <button class="refresh-btn" @click="loadDetailedStats">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="23 4 23 10 17 10"/>
              <path d="M20.49 15a9 9 0 11-2.12-9.36L23 10"/>
            </svg>
            刷新
          </button>
        </div>

        <div class="stats-grid analytics-overview">
          <div class="stat-card">
            <div class="stat-icon">🧾</div>
            <div class="stat-info">
              <div class="stat-value">{{ detailedStats.overview?.request_count || 0 }}</div>
              <div class="stat-label">总请求数</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">✅</div>
            <div class="stat-info">
              <div class="stat-value">{{ detailedStats.overview?.successful_request_count || 0 }}</div>
              <div class="stat-label">成功请求</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">🔁</div>
            <div class="stat-info">
              <div class="stat-value">{{ detailedStats.overview?.effective_dialogue_count || 0 }}</div>
              <div class="stat-label">有效对话轮次</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">🗓️</div>
            <div class="stat-info">
              <div class="stat-value">{{ detailedStats.overview?.current_week_checkin_count || 0 }}</div>
              <div class="stat-label">本周打卡总数</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">⚡</div>
            <div class="stat-info">
              <div class="stat-value">{{ formatLatency(detailedStats.overview?.avg_latency_ms) }}</div>
              <div class="stat-label">平均延迟</div>
            </div>
          </div>
        </div>

        <div class="analytics-grid">
          <div class="analytics-card">
            <div class="analytics-card-header">
              <h3>周统计</h3>
              <span>按周汇总消息、请求、打卡与活跃用户</span>
            </div>
            <div class="analytics-table-wrap">
              <table class="data-table analytics-table">
                <thead>
                  <tr>
                    <th>周</th>
                    <th>活跃用户</th>
                    <th>消息</th>
                    <th>有效对话</th>
                    <th>请求</th>
                    <th>成功请求</th>
                    <th>打卡</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="week in detailedStats.weekly || []" :key="week.week_key">
                    <td>{{ week.week_key }}</td>
                    <td>{{ week.active_user_count }}</td>
                    <td>{{ week.message_count }}</td>
                    <td>{{ week.effective_dialogue_count }}</td>
                    <td>{{ week.request_count }}</td>
                    <td>{{ week.successful_request_count }}</td>
                    <td>{{ week.checkin_count }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div class="analytics-card">
            <div class="analytics-card-header">
              <h3>用户明细</h3>
              <span>查看每个人的请求、轮次、打卡与提示事件</span>
            </div>
            <div class="analytics-table-wrap">
              <table class="data-table analytics-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>用户名</th>
                    <th>条件</th>
                    <th>消息</th>
                    <th>有效对话</th>
                    <th>本周打卡</th>
                    <th>当前轮次</th>
                    <th>请求</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="user in detailedStats.users || []" :key="`analytics-${user.user_id}`">
                    <td>{{ user.user_id }}</td>
                    <td>{{ user.username }}</td>
                    <td>{{ formatCondition(user.condition) }}</td>
                    <td>{{ user.message_count }}</td>
                    <td>{{ user.effective_dialogue_count }}</td>
                    <td>{{ user.weekly_checkin_count }}/{{ user.required_weekly_checkins }}</td>
                    <td>{{ user.current_round_count }}</td>
                    <td>{{ user.request_count }}</td>
                    <td>
                      <button class="action-btn view" @click="viewUserDetail({ id: user.user_id, username: user.username, message_count: user.message_count, created_at: user.created_at, condition: user.condition })" title="查看详情">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                          <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                          <circle cx="12" cy="12" r="3"/>
                        </svg>
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </section>

      <!-- 用户管理 -->
      <section v-if="activeTab === 'users'" class="panel users-panel">
        <div class="panel-header">
          <h2>用户管理</h2>
          <div class="panel-actions">
            <button class="export-btn" @click="exportIncompleteCheckins" title="导出本周未完成打卡的用户">
              导出未完成打卡
            </button>
            <button
              class="bulk-export-btn"
              :disabled="selectedUserIds.size === 0"
              @click="exportSelectedUsers"
              title="导出选中用户的 ZIP 数据包"
            >
              批量导出 ZIP ({{ selectedUserIds.size }})
            </button>
            <input
              v-model="userSearch"
              type="text"
              placeholder="搜索用户..."
              class="search-input"
            />
          </div>
        </div>

        <!-- 全选行 -->
        <div class="select-all-row">
          <label>
            <input
              ref="selectAllCheckbox"
              type="checkbox"
              :checked="filteredUsers.length > 0 && selectedUserIds.size === filteredUsers.length"
              @change="toggleSelectAll"
              class="row-checkbox"
            />
            全选当前页 ({{ filteredUsers.length }} 人)
          </label>
          <span v-if="selectedUserIds.size > 0" style="font-size:0.82rem;color:rgba(255,255,255,0.55)">
            已选 {{ selectedUserIds.size }} 人
          </span>
        </div>

        <div class="users-table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th style="width:36px"></th>
                <th>ID</th>
                <th>用户名</th>
                <th>实验条件</th>
                <th>消息数</th>
                <th>本周打卡</th>
                <th>注册时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="user in filteredUsers"
                :key="user.id"
                :class="{ 'selected-row': selectedUserIds.has(user.id) }"
              >
                <td>
                  <input
                    type="checkbox"
                    :checked="selectedUserIds.has(user.id)"
                    @change="toggleSelectUser(user.id)"
                    class="row-checkbox"
                  />
                </td>
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
                <td class="checkin-cell">
                  <span :class="['checkin-badge', (user.weekly_checkin_count || 0) >= checkinThreshold ? 'done' : 'pending']">
                    {{ user.weekly_checkin_count || 0 }}/{{ checkinThreshold }}
                  </span>
                </td>
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
                    disabled
                    title="实验原始数据保护已开启，禁止删除用户"
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
          <div>
            <h2>邀请码管理</h2>
            <p class="invite-panel-subtitle">支持用手机号作为邀请码，并为每条邀请码补充备注，方便后续统计。</p>
          </div>
          <div class="invite-create">
            <div class="invite-random-create">
              <input
                v-model.number="inviteCount"
                type="number"
                min="1"
                max="50"
                placeholder="数量"
                class="invite-count-input"
              />
              <button class="create-btn" @click="createInvites" :disabled="inviteLoading">
                {{ inviteLoading ? '生成中...' : '随机生成邀请码' }}
              </button>
            </div>
            <button class="create-btn secondary" @click="openCustomInviteModal" :disabled="customInviteLoading">
              批量自定义邀请码
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
          <div class="new-invites-header">
            <div>
              <h3>最近新增的邀请码</h3>
              <p>按 ID、邀请码、备注 逐条展示，方便直接复制和登记。</p>
            </div>
            <button class="copy-btn" @click="copyInviteBatch(newInvites)">复制全部</button>
          </div>
          <div class="new-invites-list">
            <div v-for="invite in newInvites" :key="`new-${invite.id ?? invite.code}`" class="new-invite-item">
              <span class="new-invite-id">#{{ invite.id ?? '-' }}</span>
              <code>{{ invite.code }}</code>
              <span :class="['new-invite-remark', !invite.remark ? 'empty' : '']">
                {{ invite.remark || '无备注' }}
              </span>
              <button class="copy-btn" @click="copyCode(invite.code)">复制</button>
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
            <input
              v-model.trim="inviteSearch"
              type="text"
              class="invite-search-input"
              placeholder="搜索 ID / 邀请码 / 备注 / 用户ID / 用户名"
            />
          </div>
          <div class="mapping-hint">1 对 1 映射：ID / 邀请码 / 备注 / 使用人，支持按任意字段搜索筛选。</div>

          <table class="data-table invites-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>邀请码</th>
                <th>备注</th>
                <th>状态</th>
                <th>用户ID</th>
                <th>用户名</th>
                <th>实验条件</th>
                <th>创建时间</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="invite in filteredInvites" :key="invite.id ?? invite.code">
                <td class="id-cell">{{ invite.id ?? '-' }}</td>
                <td class="code-cell">
                  <code>{{ invite.code }}</code>
                  <button class="mini-copy" @click="copyCode(invite.code)" title="复制">复制</button>
                </td>
                <td class="invite-remark-cell">{{ invite.remark || '-' }}</td>
                <td>
                  <span :class="['status-badge', invite.used ? 'used' : 'available']">
                    {{ invite.used ? '已使用' : '可用' }}
                  </span>
                </td>
                <td>{{ invite.used_by ?? '-' }}</td>
                <td>{{ invite.used_username || '-' }}</td>
                <td>{{ invite.used_condition ? formatCondition(invite.used_condition) : '-' }}</td>
                <td>{{ formatDate(invite.created_at) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <Transition name="modal">
        <div v-if="showCustomInviteModal" class="modal-overlay" @click.self="closeCustomInviteModal">
          <div class="modal custom-invite-modal">
            <div class="modal-header">
              <h3>批量新增自定义邀请码</h3>
              <button class="close-btn" @click="closeCustomInviteModal">×</button>
            </div>
            <div class="modal-body">
              <div class="custom-invite-toolbar">
                <p class="custom-invite-tip">支持直接填写手机号作为邀请码。留空行会自动忽略，同一批次内的邀请码不能重复。</p>
                <div class="custom-invite-actions">
                  <button class="modal-btn accent" @click="appendCustomInviteRows(5)" :disabled="customInviteRows.length >= 50">新增 5 行</button>
                  <button class="modal-btn" @click="appendCustomInviteRows(1)" :disabled="customInviteRows.length >= 50">新增 1 行</button>
                </div>
              </div>

              <div class="custom-invite-grid">
                <div class="custom-invite-grid-header">
                  <span>序号</span>
                  <span>邀请码 / 手机号</span>
                  <span>备注</span>
                  <span>操作</span>
                </div>
                <div v-for="(item, index) in customInviteRows" :key="item.key" class="custom-invite-row">
                  <span class="custom-row-index">{{ index + 1 }}</span>
                  <input
                    v-model.trim="item.code"
                    type="text"
                    maxlength="64"
                    placeholder="例如：13800138000"
                  />
                  <input
                    v-model.trim="item.remark"
                    type="text"
                    maxlength="100"
                    placeholder="例如：张三 / 1班 / 备选"
                  />
                  <button
                    class="remove-row-btn"
                    @click="removeCustomInviteRow(index)"
                    :disabled="customInviteRows.length <= 1"
                  >
                    删除
                  </button>
                </div>
              </div>
            </div>
            <div class="modal-footer">
              <button class="modal-btn" @click="resetCustomInviteRows()">重置</button>
              <button class="modal-btn primary" @click="submitCustomInvites" :disabled="customInviteLoading">
                {{ customInviteLoading ? '提交中...' : `批量新增 (${filledCustomInviteCount})` }}
              </button>
              <button class="modal-btn" @click="closeCustomInviteModal" :disabled="customInviteLoading">取消</button>
            </div>
          </div>
        </div>
      </Transition>

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
              <div class="config-row">
                <label>图片保留轮次</label>
                <input v-model.number="contextConfig.image_rounds" type="number" min="1" max="20" />
                <span class="config-hint">最近N轮对话内保留图片</span>
              </div>
            </div>
            
            <button class="save-btn" @click="saveContextConfig" :disabled="loading">
              {{ loading ? '保存中...' : '保存配置' }}
            </button>
          </div>

          <div class="config-section">
            <h3>系统设置</h3>
            <p class="config-desc">管理邀请码、聊天轮次、打卡阈值与新用户条件分配</p>

            <div class="config-form">
              <div class="config-row">
                <label>邀请码注册</label>
                <input v-model="systemSettings.invite_code_enabled" type="checkbox" class="config-checkbox" />
                <span class="config-hint">关闭后用户无需邀请码即可注册</span>
              </div>
              <div class="config-row">
                <label>聊天时长限制</label>
                <input v-model="systemSettings.chat_timer_enabled" type="checkbox" class="config-checkbox" />
                <span class="config-hint">开启后按分钟限制单日聊天时长</span>
              </div>
              <div class="config-row">
                <label>聊天时长(分钟)</label>
                <input v-model.number="systemSettings.chat_timer_duration_minutes" type="number" min="1" max="240" />
                <span class="config-hint">单日聊天时长上限</span>
              </div>
              <div class="config-row">
                <label>记忆压缩阈值</label>
                <input v-model.number="systemSettings.memory_compress_threshold" type="number" min="0" max="200" />
                <span class="config-hint">
                  0 = 动态阈值（高频聊天≤5min: 40条；中频≤30min: 30条；低频: 20条；另外距上次压缩超2小时且新增≥10条也会触发）；
                  N &gt; 0 = 固定每 N 条新消息压缩一次。压缩时 AI 将近期对话与现有长期记忆合并提炼，写入 ltm/，原始聊天记录不删除。
                </span>
              </div>
              <div class="config-row">
                <label>最短有效消息</label>
                <input v-model.number="systemSettings.min_user_message_length" type="number" min="1" max="200" />
                <span class="config-hint">用户消息达到该长度，AI 成功回复后才计入有效轮次</span>
              </div>
              <div class="config-row">
                <label>轮次超时重置(分钟)</label>
                <input v-model.number="systemSettings.round_reset_interval_minutes" type="number" min="1" max="10080" />
                <span class="config-hint">超过该间隔，当前轮次会自动清零并开始新会话</span>
              </div>
              <div class="config-row">
                <label>打卡所需轮次</label>
                <input v-model.number="systemSettings.min_rounds_for_checkin" type="number" min="1" max="200" />
                <span class="config-hint">达到该轮次才允许打卡</span>
              </div>
              <div class="config-row">
                <label>打卡冷却(小时)</label>
                <input v-model.number="systemSettings.checkin_cooldown_hours" type="number" min="0" max="168" />
                <span class="config-hint">两次打卡的最短间隔</span>
              </div>
              <div class="config-row">
                <label>周末问卷阈值</label>
                <input v-model.number="systemSettings.min_weekly_checkins_for_survey" type="number" min="0" max="20" />
                <span class="config-hint">达到该本周打卡次数才触发周末问卷</span>
              </div>
            </div>

            <div class="strategy-card">
              <div class="strategy-header">
                <h4>实验条件分配</h4>
                <span>{{ conditionLabel(systemSettings.condition_assignment_mode) }}</span>
              </div>
              <div class="strategy-options">
                <label v-for="option in strategyModeOptions" :key="option.value" class="strategy-option">
                  <input
                    type="radio"
                    name="condition-mode"
                    :value="option.value"
                    v-model="systemSettings.condition_assignment_mode"
                  />
                  <div>
                    <strong>{{ option.label }}</strong>
                    <p>{{ option.desc }}</p>
                  </div>
                </label>
              </div>
              <div v-if="systemSettings.condition_assignment_mode === 'fixed'" class="fixed-condition-row">
                <label>固定条件</label>
                <div class="condition-chip-row">
                  <button
                    v-for="option in fixedConditionOptions"
                    :key="option.value"
                    type="button"
                    class="condition-chip"
                    :class="{ active: systemSettings.fixed_condition === option.value }"
                    @click="systemSettings.fixed_condition = option.value"
                  >
                    {{ option.label }}
                  </button>
                </div>
              </div>
            </div>

            <button class="save-btn" @click="saveSystemSettings" :disabled="loading">
              {{ loading ? '保存中...' : '保存系统设置' }}
            </button>
          </div>

          <div class="config-section">
            <div class="section-headline">
              <div>
                <h3>API 通道配置</h3>
                <p class="config-desc">可视化查看与修改主通道、备份通道、搜索与上下文相关参数</p>
              </div>
              <button class="refresh-btn" @click="loadApiConfig">刷新</button>
            </div>

            <div class="api-config-block">
              <h4>主通道</h4>
              <div class="config-form">
                <div class="config-row">
                  <label>名称</label>
                  <input v-model="apiConfig.stored.primary.name" type="text" placeholder="OpenAI / Gemini / 自定义名称" />
                  <span class="config-hint">若同名 env 覆盖存在，右侧会显示当前生效值</span>
                </div>
                <div class="config-row">
                  <label>Base URL</label>
                  <input v-model="apiConfig.stored.primary.base_url" type="text" placeholder="https://..." />
                  <span class="config-hint">{{ formatApiOverrideHint('primary', 'base_url', apiConfig.effective.primary?.base_url) }}</span>
                </div>
                <div class="config-row">
                  <label>模型</label>
                  <input v-model="apiConfig.stored.primary.model" type="text" placeholder="gpt-4.1-mini / gemini-..." />
                  <span class="config-hint">{{ formatApiOverrideHint('primary', 'model', apiConfig.effective.primary?.model) }}</span>
                </div>
                <div class="config-row">
                  <label>API Key</label>
                  <input v-model="apiConfig.stored.primary.api_key" type="password" placeholder="留空表示不修改当前密钥；填写才会更新" />
                  <span class="config-hint">当前生效密钥：{{ apiConfig.effective.primary?.api_key_masked || '未配置' }}，留空保存不会覆盖旧值</span>
                </div>
                <div class="config-row">
                  <label>名称 Env</label>
                  <input v-model="apiConfig.stored.primary.name_env" type="text" placeholder="AI_PRIMARY_NAME" />
                  <span class="config-hint">存在 env 时会覆盖输入框中的名称</span>
                </div>
                <div class="config-row">
                  <label>Base URL Env</label>
                  <input v-model="apiConfig.stored.primary.base_url_env" type="text" placeholder="AI_PRIMARY_BASE_URL" />
                  <span class="config-hint">存在 env 时会覆盖 Base URL</span>
                </div>
                <div class="config-row">
                  <label>模型 Env</label>
                  <input v-model="apiConfig.stored.primary.model_env" type="text" placeholder="AI_PRIMARY_MODEL" />
                  <span class="config-hint">存在 env 时会覆盖模型</span>
                </div>
                <div class="config-row">
                  <label>Key Env</label>
                  <input v-model="apiConfig.stored.primary.api_key_env" type="text" placeholder="AI_PRIMARY_KEY" />
                  <span class="config-hint">存在 env 时会覆盖 API Key</span>
                </div>
                <div class="config-row">
                  <label>协议类型</label>
                  <select v-model="apiConfig.stored.primary.api_type">
                    <option value="openai">openai/chat_completions</option>
                    <option value="gemini">gemini/generateContent</option>
                  </select>
                  <span class="config-hint">控制图片与 JSON 输出的上游调用协议</span>
                </div>
              </div>
            </div>

            <div class="api-config-block">
              <div class="section-headline small">
                <h4>备份通道</h4>
                <button class="create-btn" @click="addBackupChannel">新增备份</button>
              </div>
              <div v-if="!apiConfig.stored.backup.length" class="empty-inline">当前没有备份通道</div>
              <div v-for="(backup, index) in apiConfig.stored.backup" :key="`backup-${index}`" class="backup-channel-card">
                <div class="section-headline small">
                  <strong>备份通道 {{ index + 1 }}</strong>
                  <button class="modal-btn danger" @click="removeBackupChannel(index)">删除</button>
                </div>
                <div class="config-form">
                  <div class="config-row">
                    <label>名称</label>
                    <input v-model="backup.name" type="text" placeholder="备用模型名称" />
                    <span class="config-hint">{{ formatApiOverrideHint('backup', 'name', apiConfig.effective.backup?.[index]?.name, index) }}</span>
                  </div>
                  <div class="config-row">
                    <label>Base URL</label>
                    <input v-model="backup.base_url" type="text" placeholder="https://..." />
                    <span class="config-hint">{{ formatApiOverrideHint('backup', 'base_url', apiConfig.effective.backup?.[index]?.base_url, index) }}</span>
                  </div>
                  <div class="config-row">
                    <label>模型</label>
                    <input v-model="backup.model" type="text" placeholder="备用模型" />
                    <span class="config-hint">{{ formatApiOverrideHint('backup', 'model', apiConfig.effective.backup?.[index]?.model, index) }}</span>
                  </div>
                  <div class="config-row">
                    <label>API Key</label>
                    <input v-model="backup.api_key" type="password" placeholder="留空表示不修改当前密钥；填写才会更新" />
                    <span class="config-hint">当前生效密钥：{{ apiConfig.effective.backup?.[index]?.api_key_masked || '未配置' }}，留空保存不会覆盖旧值</span>
                  </div>
                  <div class="config-row">
                    <label>名称 Env</label>
                    <input v-model="backup.name_env" type="text" placeholder="AI_BACKUP_NAME" />
                    <span class="config-hint">env 优先</span>
                  </div>
                  <div class="config-row">
                    <label>Base URL Env</label>
                    <input v-model="backup.base_url_env" type="text" placeholder="AI_BACKUP_BASE_URL" />
                    <span class="config-hint">env 优先</span>
                  </div>
                  <div class="config-row">
                    <label>模型 Env</label>
                    <input v-model="backup.model_env" type="text" placeholder="AI_BACKUP_MODEL" />
                    <span class="config-hint">env 优先</span>
                  </div>
                  <div class="config-row">
                    <label>Key Env</label>
                    <input v-model="backup.api_key_env" type="text" placeholder="AI_BACKUP_KEY" />
                    <span class="config-hint">env 优先</span>
                  </div>
                  <div class="config-row">
                    <label>协议类型</label>
                    <select v-model="backup.api_type">
                      <option value="openai">openai/chat_completions</option>
                      <option value="gemini">gemini/generateContent</option>
                    </select>
                    <span class="config-hint">备用通道调用协议</span>
                  </div>
                </div>
              </div>
            </div>

            <div class="api-config-block">
              <h4>运行参数</h4>
              <div class="config-form">
                <div class="config-row">
                  <label>启用搜索</label>
                  <input v-model="apiConfig.stored.enable_search" type="checkbox" class="config-checkbox" />
                  <span class="config-hint">是否允许上游 API 使用搜索能力</span>
                </div>
                <div class="config-row">
                  <label>上下文消息上限</label>
                  <input v-model.number="apiConfig.stored.max_context_messages" type="number" min="1" max="200" />
                  <span class="config-hint">API 通道配置中的最大上下文消息数</span>
                </div>
                <div class="config-row">
                  <label>图片上下文轮次</label>
                  <input v-model.number="apiConfig.stored.image_context_rounds" type="number" min="1" max="20" />
                  <span class="config-hint">会保留最近 N 轮中的图片</span>
                </div>
              </div>
            </div>

            <button class="save-btn" @click="saveApiConfig" :disabled="loading">
              {{ loading ? '保存中...' : '保存 API 配置' }}
            </button>
          </div>
        </div>
      </section>

      <section v-if="activeTab === 'sysprompts'" class="panel sysprompts-panel">
        <div class="panel-header">
          <h2>系统提示词</h2>
        </div>

        <div class="sysprompt-layout">
          <div class="sysprompt-sidebar">
            <button
              v-for="prompt in systemPrompts"
              :key="prompt.condition"
              class="prompt-tab-btn"
              :class="{ active: activeSysPrompt === prompt.condition }"
              @click="activeSysPrompt = prompt.condition"
            >
              <span>{{ formatCondition(prompt.condition) }}</span>
              <small>{{ prompt.lines || 0 }} 行</small>
            </button>
          </div>

          <div class="sysprompt-editor-card">
            <div class="sysprompt-editor-header">
              <div>
                <h3>{{ formatCondition(activeSysPrompt) }}</h3>
                <p>{{ currentSystemPromptMeta?.filename || '' }}</p>
              </div>
              <button class="save-btn" @click="saveSysPrompt" :disabled="loading || sysPromptLoading">
                {{ loading ? '保存中...' : '保存提示词' }}
              </button>
            </div>

            <div class="sysprompt-hint">
              当前新用户分配策略：{{ conditionLabel(systemSettings.condition_assignment_mode) }}
            </div>

            <textarea
              v-model="sysPromptContent"
              class="prompt-textarea"
              rows="20"
              :disabled="sysPromptLoading"
              placeholder="输入系统提示词内容..."
            ></textarea>
          </div>
        </div>
      </section>

      <!-- 提示系统 -->
      <section v-if="activeTab === 'prompts'" class="panel prompts-panel">
        <div class="panel-header">
          <h2>提示系统</h2>
          <button class="create-btn" @click="openCreatePromptModal">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
            新建提示组
          </button>
        </div>

        <div v-if="promptGroups.length === 0" class="empty-state">
          <p>暂无提示组，点击上方按钮创建</p>
        </div>

        <div v-else class="prompt-groups-list">
          <div v-for="group in promptGroups" :key="group.id" class="prompt-group-card" :class="{ disabled: !group.enabled }">
            <div class="pg-header">
              <div class="pg-title-row">
                <span class="pg-type-badge" :class="group.type">{{ formatPromptType(group.type) }}</span>
                <h4 class="pg-name">{{ group.name }}</h4>
                <span v-if="!group.enabled" class="pg-disabled-badge">已停用</span>
              </div>
              <div class="pg-actions">
                <button class="pg-btn toggle" @click="togglePromptEnabled(group)" :title="group.enabled ? '停用' : '启用'">
                  {{ group.enabled ? '⏸' : '▶' }}
                </button>
                <button class="pg-btn edit" @click="openEditPromptModal(group)" title="编辑">✏️</button>
                <button class="pg-btn answers" @click="viewPromptAnswers(group)" title="查看回答">📊</button>
                <button class="pg-btn delete" @click="deletePromptGroup(group)" title="删除">🗑️</button>
              </div>
            </div>
            <div class="pg-body">
              <div class="pg-info">
                <span><strong>触发阈值:</strong> {{ group.threshold }} 条消息</span>
                <span><strong>触发模式:</strong> {{ group.frequency_mode === 'once' ? '仅一次' : '重复触发' }}</span>
                <span><strong>题型:</strong> {{ formatQuestionKind(group.question?.kind || 'ack') }}</span>
              </div>
              <div class="pg-content-preview">
                <strong>标题:</strong> {{ group.content?.title || '(无)' }}<br/>
                <strong>内容:</strong> {{ (group.content?.body || '').substring(0, 100) }}{{ (group.content?.body?.length || 0) > 100 ? '...' : '' }}
              </div>
              <div class="pg-stats">
                <span>展示 {{ getStatForGroup(group.id).shown_count || 0 }} 次</span>
                <span>回答 {{ getStatForGroup(group.id).answered_count || 0 }} 次</span>
                <span>转化率 {{ ((getStatForGroup(group.id).conversion_rate || 0) * 100).toFixed(1) }}%</span>
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>

    <!-- 用户详情弹窗 -->
    <Transition name="modal">
      <div v-if="showUserModal" class="modal-overlay" @click.self="showUserModal = false">
        <div class="modal user-detail-modal">
          <div class="modal-header">
            <h3>用户详情</h3>
            <button class="close-btn" @click="showUserModal = false">×</button>
          </div>
          <div class="modal-body">
            <!-- 用户头像+基本信息 -->
            <div class="user-detail-hero">
              <div class="user-avatar-circle">{{ (selectedUser?.username || '?')[0].toUpperCase() }}</div>
              <div class="user-hero-info">
                <div class="user-hero-name">
                  {{ selectedUser?.username }}
                  <span v-if="selectedUser?.id === 1" class="admin-tag" style="margin-left:6px">管理员</span>
                </div>
                <div class="user-hero-meta">
                  ID #{{ selectedUser?.id }} · 注册于 {{ formatDate(selectedUser?.created_at) }} ·
                  <span :class="['condition-badge', selectedUser?.condition || 'none']" style="font-size:0.78rem;padding:0.15rem 0.5rem">
                    {{ formatCondition(userDetail.metrics?.condition || selectedUser?.condition) }}
                  </span>
                </div>
                <div class="user-condition-editor">
                  <label>
                    <span>手动调整系统提示词</span>
                    <select v-model="selectedUserCondition">
                      <option v-for="option in fixedConditionOptions" :key="option.value" :value="option.value">
                        {{ option.label }}
                      </option>
                    </select>
                  </label>
                  <button
                    class="mini-action-btn"
                    @click="saveSelectedUserCondition"
                    :disabled="savingUserCondition || !selectedUser || selectedUserCondition === (selectedUser?.condition || 'none')"
                  >
                    {{ savingUserCondition ? '保存中...' : '保存' }}
                  </button>
                </div>
              </div>
            </div>

            <!-- 关键指标卡片 -->
            <div class="user-metrics-grid">
              <div class="metric-card">
                <div class="metric-value">{{ userDetail.metrics?.message_count || 0 }}</div>
                <div class="metric-label">总消息数</div>
              </div>
              <div class="metric-card">
                <div class="metric-value">{{ userDetail.metrics?.effective_dialogue_count || 0 }}</div>
                <div class="metric-label">有效对话</div>
              </div>
              <div class="metric-card">
                <div class="metric-value">{{ userDetail.metrics?.current_round_count || 0 }}</div>
                <div class="metric-label">当前轮次</div>
              </div>
              <div class="metric-card">
                <div class="metric-value">{{ userDetail.metrics?.weekly_checkin_count || 0 }}/{{ userDetail.metrics?.required_weekly_checkins || checkinThreshold }}</div>
                <div class="metric-label">本周打卡</div>
              </div>
              <div class="metric-card">
                <div class="metric-value">{{ userDetail.metrics?.request_count || 0 }}</div>
                <div class="metric-label">总请求数</div>
              </div>
              <div class="metric-card">
                <div class="metric-value">{{ userDetail.metrics?.successful_request_count || 0 }}</div>
                <div class="metric-label">成功请求</div>
              </div>
              <div class="metric-card">
                <div class="metric-value">{{ formatLatency(userDetail.metrics?.avg_latency_ms) }}</div>
                <div class="metric-label">平均延迟</div>
              </div>
              <div class="metric-card">
                <div class="metric-value">{{ userDetail.metrics?.total_checkin_count || 0 }}</div>
                <div class="metric-label">累计打卡</div>
              </div>
            </div>

            <!-- 时间信息 -->
            <div class="detail-block" style="margin-bottom:1rem">
              <div class="user-info-grid" style="margin-bottom:0">
                <div class="info-item">
                  <span class="info-label">最后用户消息</span>
                  <span class="info-value">{{ formatDate(userDetail.metrics?.last_user_message_time) || '-' }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">最后打卡</span>
                  <span class="info-value">{{ formatDate(userDetail.metrics?.last_checkin_at) || '-' }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">当前周</span>
                  <span class="info-value">{{ userDetail.metrics?.current_week_key || '-' }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">提示事件</span>
                  <span class="info-value">展示 {{ userDetail.metrics?.prompt_shown_count || 0 }} / 回答 {{ userDetail.metrics?.prompt_answered_count || 0 }}</span>
                </div>
              </div>
            </div>

            <div class="detail-block">
              <h4>请求日志</h4>
              <div class="analytics-table-wrap compact">
                <table class="data-table analytics-table compact">
                  <thead>
                    <tr>
                      <th>时间</th>
                      <th>请求ID</th>
                      <th>轮次</th>
                      <th>本周打卡</th>
                      <th>图片</th>
                      <th>延迟</th>
                      <th>解析</th>
                      <th>摘要</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="log in userDetail.request_logs || []" :key="`log-${log.request_id}`">
                      <td>{{ formatTime(log.timestamp) }}</td>
                      <td class="mono-cell">{{ log.request_id }}</td>
                      <td>{{ log.state_snapshot?.current_round_count ?? '-' }}</td>
                      <td>{{ log.state_snapshot?.weekly_checkin_count ?? '-' }}</td>
                      <td>{{ getOutboundImageCount(log) }}</td>
                      <td>{{ formatLatency(log.latency_ms) }}</td>
                      <td>{{ log.parse_success ? '✓' : '✗' }}</td>
                      <td class="wide-cell">{{ log.parsed_reply_preview || log.request?.user_message_preview || '-' }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <div class="detail-block">
              <h4>打卡记录</h4>
              <div class="analytics-table-wrap compact">
                <table class="data-table analytics-table compact">
                  <thead>
                    <tr>
                      <th>时间</th>
                      <th>周</th>
                      <th>打卡时轮次</th>
                      <th>答案</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="record in userDetail.checkins || []" :key="`checkin-${record.id}`">
                      <td>{{ formatTime(record.created_at) }}</td>
                      <td>{{ record.week_key }}</td>
                      <td>{{ record.round_count_at_checkin }}</td>
                      <td class="wide-cell checkin-answer-cell">
                        <div v-if="getCheckinAnswerItems(record).length > 0" class="checkin-answer-list">
                          <div
                            v-for="item in getCheckinAnswerItems(record)"
                            :key="`${record.id}-${item.key}`"
                            class="checkin-answer-item"
                          >
                            <span class="checkin-answer-question">{{ item.label }}</span>
                            <span class="checkin-answer-score">{{ item.value }}</span>
                          </div>
                        </div>
                        <span v-else class="checkin-answer-empty">-</span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <div class="detail-block">
              <h4>周问卷历史</h4>
              <div class="analytics-table-wrap compact">
                <table class="data-table analytics-table compact">
                  <thead>
                    <tr>
                      <th>周</th>
                      <th>打卡快照</th>
                      <th>状态</th>
                      <th>达标时间</th>
                      <th>已展示</th>
                      <th>已读</th>
                      <th>问卷链接</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="record in userDetail.weekly_surveys || []" :key="`weekly-survey-${record.id}`">
                      <td>{{ record.week_key }}</td>
                      <td>{{ formatWeeklySurveyCheckins(record) }}</td>
                      <td>{{ formatWeeklySurveyStatus(record.status) }}</td>
                      <td>{{ formatTime(record.qualified_at) || '-' }}</td>
                      <td>{{ formatTime(record.shown_at) || '-' }}</td>
                      <td>{{ formatTime(record.read_at) || '-' }}</td>
                      <td class="wide-cell">
                        <a
                          v-if="record.survey_url_snapshot"
                          :href="record.survey_url_snapshot"
                          target="_blank"
                          rel="noopener noreferrer"
                          class="download-link"
                        >
                          打开该周问卷
                        </a>
                        <span v-else>-</span>
                      </td>
                    </tr>
                  </tbody>
                </table>
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

            <div class="detail-block">
              <h4>提示事件</h4>
              <div class="analytics-table-wrap compact">
                <table class="data-table analytics-table compact">
                  <thead>
                    <tr>
                      <th>时间</th>
                      <th>组ID</th>
                      <th>类型</th>
                      <th>聊天快照</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="event in userDetail.prompt_events || []" :key="`prompt-${event.id}`">
                      <td>{{ formatTime(event.created_at) }}</td>
                      <td>{{ event.prompt_group_id }}</td>
                      <td>{{ event.event_type }}</td>
                      <td>{{ event.chat_count_snapshot }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button class="modal-btn danger" disabled title="实验原始数据保护已开启，禁止清空聊天记录">清空聊天记录已禁用</button>
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
            <button class="modal-btn accent" @click="compressUserMemory" :disabled="compressing || memoryLoading">
              {{ compressing ? '生成中...' : '🧠 生成/压缩记忆' }}
            </button>
            <button class="modal-btn primary" @click="saveMemoryEdit" :disabled="loading">
              {{ loading ? '保存中...' : '保存记忆' }}
            </button>
            <button class="modal-btn" @click="showMemoryModal = false">取消</button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- 提示组编辑弹窗 -->
    <Transition name="modal">
      <div v-if="showPromptModal" class="modal-overlay" @click.self="showPromptModal = false">
        <div class="modal prompt-edit-modal">
          <div class="modal-header">
            <h3>{{ editingPromptGroup ? '编辑提示组' : '新建提示组' }}</h3>
            <button class="close-btn" @click="showPromptModal = false">×</button>
          </div>
          <div class="modal-body prompt-form">
            <div class="form-row">
              <label>名称 *</label>
              <input v-model="promptForm.name" type="text" placeholder="提示组名称" />
            </div>
            <div class="form-row">
              <label>类型</label>
              <select v-model="promptForm.type">
                <option value="daily">日常提醒</option>
                <option value="survey">问卷提醒</option>
                <option value="feedback">反馈提醒</option>
              </select>
            </div>
            <div class="form-row">
              <label>触发阈值</label>
              <input v-model.number="promptForm.threshold" type="number" min="1" />
              <span class="form-hint">用户发送多少条消息后触发</span>
            </div>
            <div class="form-row">
              <label>触发模式</label>
              <select v-model="promptForm.frequency_mode">
                <option value="once">仅触发一次</option>
                <option value="repeat_every_n">重复触发</option>
              </select>
            </div>
            <div v-if="promptForm.frequency_mode === 'repeat_every_n'" class="form-row">
              <label>重复间隔</label>
              <input v-model.number="promptForm.repeat_every_n" type="number" min="1" placeholder="每隔N条" />
            </div>
            <div class="form-row">
              <label>最大展示次数</label>
              <input v-model.number="promptForm.max_times" type="number" min="1" placeholder="不限制留空" />
            </div>
            <div class="form-row">
              <label>优先级</label>
              <input v-model.number="promptForm.priority" type="number" />
              <span class="form-hint">数字越大优先级越高</span>
            </div>
            <hr class="form-divider" />
            <div class="form-row">
              <label>弹窗标题</label>
              <input v-model="promptForm.content.title" type="text" placeholder="弹窗标题" />
            </div>
            <div class="form-row">
              <label>弹窗内容</label>
              <textarea v-model="promptForm.content.body" rows="3" placeholder="弹窗正文内容"></textarea>
            </div>
            <hr class="form-divider" />
            <div class="form-row">
              <label>题型</label>
              <select v-model="promptForm.question.kind">
                <option value="ack">确认按钮（知道了）</option>
                <option value="choice_single">单选题</option>
                <option value="choice_multi">多选题</option>
                <option value="text">填空题</option>
              </select>
            </div>
            <div v-if="promptForm.question.kind === 'choice_single' || promptForm.question.kind === 'choice_multi'" class="form-row">
              <label>选项（每行一个）</label>
              <textarea 
                :value="(promptForm.question.options || []).join('\n')"
                @input="promptForm.question.options = $event.target.value.split('\n').filter(s => s.trim())"
                rows="4" 
                placeholder="选项1&#10;选项2&#10;选项3"
              ></textarea>
            </div>
            <div v-if="promptForm.question.kind === 'text'" class="form-row">
              <label>输入框占位符</label>
              <input v-model="promptForm.question.placeholder" type="text" placeholder="请输入..." />
            </div>
            <div class="form-row">
              <label>按钮文案</label>
              <input v-model="promptForm.question.submit_text" type="text" placeholder="确定" />
            </div>
            <div class="form-row checkbox-row">
              <label>
                <input type="checkbox" v-model="promptForm.question.required" />
                必须回答（不可跳过）
              </label>
            </div>
            <div class="form-row checkbox-row">
              <label>
                <input type="checkbox" v-model="promptForm.enabled" />
                立即启用
              </label>
            </div>
          </div>
          <div class="modal-footer">
            <button class="modal-btn primary" @click="savePromptGroup" :disabled="loading">
              {{ loading ? '保存中...' : '保存' }}
            </button>
            <button class="modal-btn" @click="showPromptModal = false">取消</button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- 查看回答弹窗 -->
    <Transition name="modal">
      <div v-if="showAnswersModal" class="modal-overlay" @click.self="showAnswersModal = false">
        <div class="modal answers-modal">
          <div class="modal-header">
            <h3>回答记录 - {{ viewingGroupName }}</h3>
            <button class="close-btn" @click="showAnswersModal = false">×</button>
          </div>
          <div class="modal-body">
            <div v-if="viewingAnswers.length === 0" class="empty-state">
              <p>暂无回答记录</p>
            </div>
            <div v-else class="answers-list">
              <div v-for="ans in viewingAnswers" :key="ans.event_id" class="answer-item">
                <div class="answer-header">
                  <span class="answer-user">{{ ans.username || '用户#' + ans.user_id }}</span>
                  <span class="answer-time">{{ formatDate(ans.created_at) }}</span>
                </div>
                <div class="answer-content">
                  <template v-if="ans.answer?.ok">✓ 已确认</template>
                  <template v-else-if="ans.answer?.selected">
                    选择: {{ ans.answer.selected.join(', ') }}
                  </template>
                  <template v-else-if="ans.answer?.text">
                    {{ ans.answer.text }}
                  </template>
                  <template v-else>{{ JSON.stringify(ans.answer) }}</template>
                </div>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button class="modal-btn" @click="showAnswersModal = false">关闭</button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- 打卡设置 -->
    <section v-if="activeTab === 'checkin'" class="panel checkin-panel">
      <div class="panel-header">
        <h2>打卡设置</h2>
        <button class="save-btn" @click="saveCheckinSettings" :disabled="loading" style="margin:0">
          {{ loading ? '保存中...' : '保存设置' }}
        </button>
      </div>

      <div class="checkin-layout">
        <!-- 左列：题目配置 -->
        <div class="checkin-col">
          <div class="checkin-card">
            <div class="checkin-card-header">
              <div>
                <h3>EMA 打卡题目</h3>
                <p class="config-desc">用户打卡时显示的题目，采用 1~7 李克特量表</p>
              </div>
              <button class="create-btn small" @click="addCheckinQuestion">+ 添加</button>
            </div>
            <div class="questions-list">
              <div v-for="(q, i) in checkinSettings.checkin_questions" :key="i" class="question-edit-row">
                <span class="q-num">{{ i + 1 }}</span>
                <input
                  v-model="checkinSettings.checkin_questions[i]"
                  type="text"
                  class="q-input"
                  :placeholder="`题目 ${i + 1}`"
                />
                <button
                  class="q-del-btn"
                  @click="removeCheckinQuestion(i)"
                  :disabled="checkinSettings.checkin_questions.length <= 1"
                  title="删除"
                >×</button>
              </div>
            </div>
          </div>

          <div class="checkin-card">
            <h3>周末问卷链接</h3>
            <p class="config-desc">本周打卡达标后，周末上线时自动弹出此链接（通过通知收件箱推送）</p>
            <input
              v-model="checkinSettings.weekly_survey_url"
              type="url"
              class="url-input"
              placeholder="https://..."
            />
          </div>
        </div>

        <!-- 右列：每周清理 -->
        <div class="checkin-col">
          <div class="checkin-card cleanup-card">
            <h3>每周清理</h3>
            <div class="cleanup-explain">
              <div class="explain-block">
                <span class="explain-icon">🔄</span>
                <div>
                  <strong>清零当前轮次</strong>
                  <p>只清空 <code>current_round_count</code>、<code>session_start_time</code> 和 <code>last_user_message_time</code>。<br/>
                  <em>不会推进</em> <code>current_week_key</code>，也不会删除任何落盘记录；如果系统已经进入新的一周，后端仍会在下次读取用户状态时自动执行跨周重置。</p>
                </div>
              </div>
              <div class="explain-block">
                <span class="explain-icon">🗑️</span>
                <div>
                  <strong>进入下一周（轮次 + 周统计重置）</strong>
                  <p>在清零轮次的基础上，同时将 <code>weekly_checkin_count</code> 和 <code>weekly_survey_popup_shown</code> 重置为 0/false。<br/>
                  并将 <code>current_week_key</code> 推进为本周，用于手动切换到新的实验周次。<em>同样不会删除</em> <code>checkin_records.json</code> 等原始数据。</p>
                </div>
              </div>
            </div>
            <div class="cleanup-actions">
              <button class="cleanup-btn secondary" @click="runWeeklyCleanup(false)">
                🔄 仅清空轮次缓存
              </button>
              <button class="cleanup-btn danger" @click="runWeeklyCleanup(true)">
                🗑️ 进入下一周（轮次 + 周统计重置）
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>

    <div v-if="showExportModal" class="modal-overlay">
      <div class="modal export-modal">
        <div class="modal-header">
          <span class="modal-icon" :class="exportState === 'ready' ? 'success' : exportState === 'error' ? 'danger' : 'normal'">
            <template v-if="exportState === 'ready'">✓</template>
            <template v-else-if="exportState === 'error'">✕</template>
            <template v-else>⏳</template>
          </span>
          <h3>{{ exportState === 'ready' ? '导出已完成' : exportState === 'error' ? '导出失败' : '正在打包导出' }}</h3>
        </div>
        <p class="modal-message">
          <template v-if="exportState === 'packaging'">
            正在整理选中用户的原始数据并打包为 ZIP，请稍候，不要关闭页面。
          </template>
          <template v-else-if="exportState === 'ready'">
            已为 {{ exportTargetCount }} 位用户生成 ZIP 数据包，浏览器已尝试自动下载。
          </template>
          <template v-else>
            {{ exportErrorMessage || '导出失败，请稍后重试。' }}
          </template>
        </p>
        <div v-if="exportState === 'packaging'" class="export-progress">
          <div class="export-spinner"></div>
          <span>打包中...</span>
        </div>
        <div v-if="exportState === 'ready'" class="export-ready">
          <div class="export-file">{{ exportFilename }}</div>
          <a
            v-if="exportDownloadUrl"
            class="download-link"
            :href="exportDownloadUrl"
            :download="exportFilename"
          >
            如果没有自动下载，点击这里手动下载
          </a>
        </div>
        <div class="modal-actions">
          <button
            v-if="exportState === 'ready' && exportDownloadUrl"
            class="modal-btn confirm"
            @click="downloadPreparedExport"
          >
            再次下载
          </button>
          <button
            class="modal-btn cancel"
            :disabled="exportState === 'packaging'"
            @click="closeExportModal"
          >
            {{ exportState === 'packaging' ? '打包中...' : '关闭' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { Chart, registerables } from 'chart.js'
import { adminAPI, configAPI, promptAPI, settingsAPI } from '../api'
import { toast, confirm } from '../utils/toast'
import { formatShanghaiDateTime, formatShanghaiMonthDayTime, getShanghaiDateStamp } from '../utils/datetime'

Chart.register(...registerables)

// 标签页配置
const tabs = [
  { id: 'dashboard', label: '仪表盘', icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="9"/><rect x="14" y="3" width="7" height="5"/><rect x="14" y="12" width="7" height="9"/><rect x="3" y="16" width="7" height="5"/></svg>' },
  { id: 'analytics', label: '详细统计', icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 3v18h18"/><path d="M7 15l4-4 3 3 5-7"/></svg>' },
  { id: 'users', label: '用户管理', icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/></svg>' },
  { id: 'memory', label: '记忆管理', icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z"/></svg>' },
  { id: 'prompts', label: '提示系统', icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/><path d="M8 9h8M8 13h6"/></svg>' },
  { id: 'invites', label: '邀请码', icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="M7 8h10M7 12h10M7 16h6"/></svg>' },
  { id: 'config', label: '系统配置', icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"/></svg>' },
  { id: 'sysprompts', label: '系统提示词', icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 016.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z"/></svg>' },
  { id: 'checkin', label: '打卡设置', icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>' }
]

const activeTab = ref('dashboard')
const loading = ref(false)

// 数据
const stats = ref({})
const detailedStats = ref({
  overview: {},
  weekly: [],
  users: [],
})
const users = ref([])
const invites = ref([])
const memories = ref([])
const userSearch = ref('')
const inviteFilter = ref('all')
const inviteSearch = ref('')
const inviteCount = ref(5)
const newInvites = ref([])
const inviteLoading = ref(false)
const customInviteLoading = ref(false)
const inviteCodeEnabled = ref(true)
const checkinThreshold = ref(2)
const showCustomInviteModal = ref(false)
const customInviteRows = ref([])

// 用户多选
const selectedUserIds = ref(new Set())
const selectAllCheckbox = ref(null)
const showExportModal = ref(false)
const exportState = ref('idle')
const exportFilename = ref('')
const exportDownloadUrl = ref('')
const exportTargetCount = ref(0)
const exportErrorMessage = ref('')

// 用户详情弹窗
const showUserModal = ref(false)
const selectedUser = ref(null)
const selectedUserCondition = ref('none')
const savingUserCondition = ref(false)
const userHistory = ref([])
const userDetail = ref({
  metrics: {},
  request_logs: [],
  checkins: [],
  prompt_events: [],
  weekly_surveys: [],
})

// 记忆编辑弹窗
const showMemoryModal = ref(false)
const editingMemory = ref(null)
const editingLongTermMemory = ref('')
const editingMemoryHistory = ref([])
const memoryLoading = ref(false)
const compressing = ref(false)

// 配置
const contextConfig = ref({
  max_messages: 80,
  max_tokens: 12000,
  system_prompt_tokens: 100,
  reserve_tokens: 1000,
  image_rounds: 5
})
const systemSettings = ref({
  invite_code_enabled: true,
  chat_timer_enabled: false,
  chat_timer_duration_minutes: 16,
  memory_compress_threshold: 0,
  min_user_message_length: 10,
  round_reset_interval_minutes: 60,
  min_rounds_for_checkin: 10,
  checkin_cooldown_hours: 4,
  min_weekly_checkins_for_survey: 2,
  condition_assignment_mode: 'modulo',
  fixed_condition: 'emotional',
})
const apiConfig = ref({
  stored: {
    primary: {
      name: '',
      base_url: '',
      model: '',
      api_key: '',
      name_env: 'AI_PRIMARY_NAME',
      base_url_env: 'AI_PRIMARY_BASE_URL',
      model_env: 'AI_PRIMARY_MODEL',
      api_key_env: 'AI_PRIMARY_KEY',
      api_type: 'openai',
      price: '',
    },
    backup: [],
    enable_search: true,
    max_context_messages: 80,
    image_context_rounds: 5,
  },
  effective: {
    primary: {},
    backup: [],
  },
  env_overrides: {
    primary: {},
    backup: [],
  },
})
const strategyModeOptions = [
  { value: 'modulo', label: '按用户ID循环', desc: '按 user_id % 3 固定轮转分配三种条件' },
  { value: 'random', label: '随机分配', desc: '每个新用户随机分到一种实验条件' },
  { value: 'fixed', label: '固定条件', desc: '所有新用户都使用同一种实验条件' },
]
const fixedConditionOptions = [
  { value: 'emotional', label: '情感表露', desc: '' },
  { value: 'factual', label: '事实表露', desc: '' },
  { value: 'none', label: '无表露', desc: '' },
]
const systemPrompts = ref([])
const activeSysPrompt = ref('emotional')
const sysPromptContent = ref('')
const sysPromptLoading = ref(false)
const barChartRef = ref(null)
const doughnutChartRef = ref(null)
let barChartInstance = null
let doughnutChartInstance = null

// 提示系统
const promptGroups = ref([])
const promptStats = ref([])
const showPromptModal = ref(false)
const editingPromptGroup = ref(null)
const promptForm = ref({
  type: 'daily',
  name: '',
  enabled: true,
  threshold: 10,
  frequency_mode: 'once',
  repeat_every_n: null,
  max_times: null,
  cooldown_seconds: null,
  priority: 0,
  content: { title: '', body: '' },
  question: { kind: 'ack', required: false, options: [], placeholder: '', submit_text: '知道了' }
})
const showAnswersModal = ref(false)
const viewingAnswers = ref([])
const viewingGroupName = ref('')

const createInviteDraft = () => ({
  key: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
  code: '',
  remark: '',
})

const resetCustomInviteRows = (count = 5) => {
  customInviteRows.value = Array.from({ length: count }, () => createInviteDraft())
}

const normalizeInviteItems = (items = []) =>
  items
    .map(item => ({
      id: item?.id ?? null,
      code: String(item?.code || '').trim(),
      remark: String(item?.remark || '').trim(),
    }))
    .filter(item => item.code)

const normalizedCustomInviteItems = computed(() => normalizeInviteItems(customInviteRows.value))

const filledCustomInviteCount = computed(() => normalizedCustomInviteItems.value.length)

const findDuplicateInviteCodes = (items) => {
  const seen = new Set()
  const duplicates = []
  items.forEach(item => {
    if (seen.has(item.code)) {
      duplicates.push(item.code)
      return
    }
    seen.add(item.code)
  })
  return [...new Set(duplicates)]
}

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
  let base = invites.value
  if (inviteFilter.value === 'available') {
    base = base.filter(i => !i.used)
  } else if (inviteFilter.value === 'used') {
    base = base.filter(i => i.used)
  }

  const keyword = inviteSearch.value.trim().toLowerCase()
  if (!keyword) return base

  return base.filter(invite => {
    const fields = [
      invite.id == null ? '' : String(invite.id),
      invite.code,
      invite.remark || '',
      invite.used_by == null ? '' : String(invite.used_by),
      invite.used_username || '',
      invite.used_condition || '',
    ]
    return fields.some(v => String(v).toLowerCase().includes(keyword))
  })
})
const currentSystemPromptMeta = computed(() =>
  systemPrompts.value.find(item => item.condition === activeSysPrompt.value) || null
)

// 加载数据
const loadStats = async () => {
  try {
    stats.value = await adminAPI.getStats()
    await renderCharts()
  } catch (err) {
    console.error('加载统计失败:', err)
  }
}

const loadDetailedStats = async () => {
  try {
    detailedStats.value = await adminAPI.getDetailedStats()
  } catch (err) {
    console.error('加载详细统计失败:', err)
    toast.error('加载详细统计失败')
  }
}

const loadUsers = async () => {
  try {
    const res = await adminAPI.getUsers()
    users.value = res.users
    checkinThreshold.value = res.threshold || checkinThreshold.value
  } catch (err) {
    console.error('加载用户失败:', err)
    if (err.response?.status === 403) {
      toast.error('需要管理员权限')
    }
  }
}

const getLocalDateStamp = () => {
  return getShanghaiDateStamp()
}

const revokeExportUrl = () => {
  if (exportDownloadUrl.value) {
    URL.revokeObjectURL(exportDownloadUrl.value)
    exportDownloadUrl.value = ''
  }
}

const parseDownloadFilename = (headers = {}) => {
  const disposition = headers['content-disposition'] || headers['Content-Disposition'] || ''
  const utf8Match = disposition.match(/filename\*\s*=\s*UTF-8''([^;]+)/i)
  if (utf8Match?.[1]) {
    try {
      return decodeURIComponent(utf8Match[1])
    } catch {}
  }
  const match = disposition.match(/filename=\"?([^\";]+)\"?/)
  if (match?.[1]) {
    return decodeURIComponent(match[1])
  }
  return `用户全量原始数据_${getLocalDateStamp()}.zip`
}

const triggerBrowserDownload = () => {
  if (!exportDownloadUrl.value) return
  const a = document.createElement('a')
  a.href = exportDownloadUrl.value
  a.download = exportFilename.value || `用户全量原始数据_${getLocalDateStamp()}.zip`
  a.click()
}

const closeExportModal = () => {
  if (exportState.value === 'packaging') return
  showExportModal.value = false
  exportState.value = 'idle'
  exportFilename.value = ''
  exportTargetCount.value = 0
  exportErrorMessage.value = ''
  revokeExportUrl()
}

const downloadPreparedExport = () => {
  triggerBrowserDownload()
}

const readExportErrorMessage = async (err) => {
  const blob = err?.response?.data
  if (blob instanceof Blob) {
    try {
      const text = await blob.text()
      const data = JSON.parse(text)
      if (data?.detail) return data.detail
    } catch {}
  }
  return err?.response?.data?.detail || '批量导出失败'
}

// 多选操作
const toggleSelectUser = (userId) => {
  const s = new Set(selectedUserIds.value)
  if (s.has(userId)) s.delete(userId)
  else s.add(userId)
  selectedUserIds.value = s
}

const toggleSelectAll = (e) => {
  if (e.target.checked) {
    selectedUserIds.value = new Set(filteredUsers.value.map(u => u.id))
  } else {
    selectedUserIds.value = new Set()
  }
}

const exportSelectedUsers = async () => {
  if (selectedUserIds.value.size === 0) return
  const ids = [...selectedUserIds.value]
  revokeExportUrl()
  exportTargetCount.value = ids.length
  exportFilename.value = ''
  exportErrorMessage.value = ''
  exportState.value = 'packaging'
  showExportModal.value = true
  try {
    const res = await adminAPI.exportUsersZip(ids)
    const blob = new Blob([res.data], { type: 'application/zip' })
    exportDownloadUrl.value = URL.createObjectURL(blob)
    exportFilename.value = parseDownloadFilename(res.headers)
    exportState.value = 'ready'
    triggerBrowserDownload()
    toast.success(`已打包 ${ids.length} 位用户的数据`)
  } catch (err) {
    console.error('批量导出失败:', err)
    exportState.value = 'error'
    exportErrorMessage.value = await readExportErrorMessage(err)
    toast.error(exportErrorMessage.value)
  }
}

const exportIncompleteCheckins = async () => {
  try {
    const res = await adminAPI.getIncompleteCheckins()
    checkinThreshold.value = res.threshold
    if (res.users.length === 0) {
      toast.success('本周所有用户均已完成打卡')
      return
    }
    const lines = [`本周未完成打卡用户（需 ${res.threshold} 次）`, '']
    res.users.forEach(u => {
      lines.push(`ID: ${u.id}  用户名: ${u.username}  已打卡: ${u.weekly_checkin_count}/${u.required}`)
    })
    const blob = new Blob([lines.join('\n')], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `未完成打卡_${getLocalDateStamp()}.txt`
    a.click()
    URL.revokeObjectURL(url)
    toast.success(`已导出 ${res.users.length} 名未完成打卡用户`)
  } catch (err) {
    console.error('导出失败:', err)
    toast.error('导出失败')
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
    systemSettings.value.invite_code_enabled = res.invite_code_enabled
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

const loadApiConfig = async () => {
  try {
    apiConfig.value = await configAPI.getApiConfig()
  } catch (err) {
    console.error('加载 API 配置失败:', err)
    toast.error('加载 API 配置失败')
  }
}

const loadSystemSettings = async () => {
  try {
    const res = await settingsAPI.getAdmin()
    systemSettings.value = {
      ...systemSettings.value,
      ...res,
    }
    checkinThreshold.value = Number(systemSettings.value.min_weekly_checkins_for_survey || checkinThreshold.value || 2)
    inviteCodeEnabled.value = !!systemSettings.value.invite_code_enabled
  } catch (err) {
    console.error('加载系统设置失败:', err)
  }
}

const saveSystemSettings = async () => {
  loading.value = true
  try {
    await settingsAPI.updateAdmin({
      memory_compress_threshold: Number(systemSettings.value.memory_compress_threshold || 0),
      min_user_message_length: Number(systemSettings.value.min_user_message_length || 10),
      round_reset_interval_minutes: Number(systemSettings.value.round_reset_interval_minutes || 60),
      min_rounds_for_checkin: Number(systemSettings.value.min_rounds_for_checkin || 10),
      checkin_cooldown_hours: Number(systemSettings.value.checkin_cooldown_hours || 4),
      min_weekly_checkins_for_survey: Number(systemSettings.value.min_weekly_checkins_for_survey || 2),
      condition_assignment_mode: systemSettings.value.condition_assignment_mode,
      fixed_condition: systemSettings.value.fixed_condition,
      chat_timer_enabled: !!systemSettings.value.chat_timer_enabled,
      chat_timer_duration_minutes: Number(systemSettings.value.chat_timer_duration_minutes || 16),
      invite_code_enabled: !!systemSettings.value.invite_code_enabled,
    })
    toast.success('系统设置已保存')
    await loadSystemSettings()
    await Promise.all([loadUsers(), loadDetailedStats()])
  } catch (err) {
    console.error('保存系统设置失败:', err)
    toast.error('保存系统设置失败')
  } finally {
    loading.value = false
  }
}

const saveApiConfig = async () => {
  loading.value = true
  try {
    await configAPI.updateApiConfig(apiConfig.value.stored)
    toast.success('API 配置已保存')
    await loadApiConfig()
  } catch (err) {
    console.error('保存 API 配置失败:', err)
    toast.error(err.response?.data?.detail || '保存 API 配置失败')
  } finally {
    loading.value = false
  }
}

const addBackupChannel = () => {
  apiConfig.value.stored.backup.push({
    name: '',
    base_url: '',
    model: '',
    api_key: '',
    name_env: 'AI_BACKUP_NAME',
    base_url_env: 'AI_BACKUP_BASE_URL',
    model_env: 'AI_BACKUP_MODEL',
    api_key_env: 'AI_BACKUP_KEY',
    api_type: 'openai',
    price: '',
  })
}

const removeBackupChannel = (index) => {
  apiConfig.value.stored.backup.splice(index, 1)
}

const loadSystemPrompts = async () => {
  try {
    const res = await adminAPI.listSystemPrompts()
    systemPrompts.value = res.prompts || []
    await loadSystemPrompt(activeSysPrompt.value)
  } catch (err) {
    console.error('加载系统提示词失败:', err)
    toast.error('加载系统提示词失败')
  }
}

const loadSystemPrompt = async (condition = activeSysPrompt.value) => {
  sysPromptLoading.value = true
  try {
    const res = await adminAPI.getSystemPrompt(condition)
    sysPromptContent.value = res.content || ''
  } catch (err) {
    console.error('加载提示词内容失败:', err)
    toast.error('加载提示词内容失败')
  } finally {
    sysPromptLoading.value = false
  }
}

const saveSysPrompt = async () => {
  loading.value = true
  try {
    await adminAPI.updateSystemPrompt(activeSysPrompt.value, sysPromptContent.value)
    toast.success('系统提示词已保存')
    await loadSystemPrompts()
  } catch (err) {
    console.error('保存系统提示词失败:', err)
    toast.error('保存系统提示词失败')
  } finally {
    loading.value = false
  }
}

const destroyCharts = () => {
  if (barChartInstance) {
    barChartInstance.destroy()
    barChartInstance = null
  }
  if (doughnutChartInstance) {
    doughnutChartInstance.destroy()
    doughnutChartInstance = null
  }
}

const renderCharts = async () => {
  if (activeTab.value !== 'dashboard') return
  await nextTick()
  if (!barChartRef.value || !doughnutChartRef.value) return

  destroyCharts()

  const perUserMessages = stats.value.per_user_messages || []
  const conditionDistribution = stats.value.condition_distribution || {}

  barChartInstance = new Chart(barChartRef.value, {
    type: 'bar',
    data: {
      labels: perUserMessages.map(item => item.username || `用户${item.user_id}`),
      datasets: [
        {
          label: '消息数',
          data: perUserMessages.map(item => item.message_count || 0),
          backgroundColor: 'rgba(251, 191, 36, 0.72)',
          borderColor: 'rgba(251, 191, 36, 1)',
          borderWidth: 1,
          borderRadius: 8,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false,
        },
      },
      scales: {
        x: {
          ticks: { color: 'rgba(255,255,255,0.78)' },
          grid: { color: 'rgba(255,255,255,0.08)' },
        },
        y: {
          beginAtZero: true,
          ticks: { color: 'rgba(255,255,255,0.78)' },
          grid: { color: 'rgba(255,255,255,0.08)' },
        },
      },
    },
  })

  doughnutChartInstance = new Chart(doughnutChartRef.value, {
    type: 'doughnut',
    data: {
      labels: ['无表露', '情感表露', '事实表露'],
      datasets: [
        {
          data: [
            conditionDistribution.none || 0,
            conditionDistribution.emotional || 0,
            conditionDistribution.factual || 0,
          ],
          backgroundColor: [
            'rgba(148, 163, 184, 0.85)',
            'rgba(244, 114, 182, 0.85)',
            'rgba(96, 165, 250, 0.85)',
          ],
          borderColor: 'rgba(255,255,255,0.12)',
          borderWidth: 1,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: {
            color: 'rgba(255,255,255,0.82)',
          },
        },
      },
    },
  })
}

// 操作
const openCustomInviteModal = () => {
  if (customInviteRows.value.length === 0) {
    resetCustomInviteRows()
  }
  showCustomInviteModal.value = true
}

const closeCustomInviteModal = () => {
  showCustomInviteModal.value = false
}

const appendCustomInviteRows = (count = 1) => {
  const remaining = 50 - customInviteRows.value.length
  if (remaining <= 0) {
    toast.error('单次最多编辑 50 个邀请码')
    return
  }
  customInviteRows.value = [
    ...customInviteRows.value,
    ...Array.from({ length: Math.min(count, remaining) }, () => createInviteDraft()),
  ]
}

const removeCustomInviteRow = (index) => {
  if (customInviteRows.value.length <= 1) {
    customInviteRows.value = [createInviteDraft()]
    return
  }
  customInviteRows.value = customInviteRows.value.filter((_, idx) => idx !== index)
}

const copyInviteBatch = (items) => {
  const rows = normalizeInviteItems(items)
  if (rows.length === 0) {
    toast.error('没有可复制的邀请码')
    return
  }
  const content = [
    'ID\t邀请码\t备注',
    ...rows.map(item => `${item.id ?? '-'}\t${item.code}\t${item.remark || '-'}`),
  ].join('\n')
  navigator.clipboard.writeText(content).then(() => {
    toast.success('整批邀请码已复制到剪贴板')
  }).catch(() => {
    toast.error('复制失败')
  })
}

const createInvites = async () => {
  if (inviteCount.value < 1 || inviteCount.value > 50) {
    toast.error('生成数量需在1-50之间')
    return
  }
  
  inviteLoading.value = true
  try {
    const res = await adminAPI.createInvites(inviteCount.value)
    newInvites.value = normalizeInviteItems(res.items?.length ? res.items : res.codes?.map(code => ({ code })))
    await loadInvites()
    toast.success(`成功生成 ${res.count} 个邀请码`)
  } catch (err) {
    toast.error('生成邀请码失败')
  } finally {
    inviteLoading.value = false
  }
}

const submitCustomInvites = async () => {
  const items = normalizedCustomInviteItems.value
  if (items.length === 0) {
    toast.error('请至少填写一个邀请码')
    return
  }

  const duplicates = findDuplicateInviteCodes(items)
  if (duplicates.length > 0) {
    toast.error(`存在重复邀请码：${duplicates.join('、')}`)
    return
  }

  customInviteLoading.value = true
  try {
    const res = await adminAPI.createInvites({ items })
    const createdItems = normalizeInviteItems(res.items)
    await loadInvites()

    if ((res.count || 0) === 0) {
      toast.error('填写的邀请码都已存在，未创建新记录')
      return
    }

    newInvites.value = createdItems
    showCustomInviteModal.value = false
    resetCustomInviteRows()

    if (res.skipped?.length) {
      toast.success(`成功新增 ${res.count} 个邀请码，跳过 ${res.skipped.length} 个已存在邀请码`)
    } else {
      toast.success(`成功新增 ${res.count} 个邀请码`)
    }
  } catch (err) {
    toast.error(err?.response?.data?.detail || '批量新增邀请码失败')
  } finally {
    customInviteLoading.value = false
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
  selectedUserCondition.value = user?.condition || 'none'
  showUserModal.value = true
  
  try {
    const res = await adminAPI.getUserDetail(user.id, { log_limit: 120, history_limit: 120 })
    selectedUser.value = {
      ...selectedUser.value,
      ...(res.user || {}),
      message_count: res.metrics?.message_count ?? selectedUser.value?.message_count,
      condition: res.metrics?.condition ?? selectedUser.value?.condition,
    }
    selectedUserCondition.value = res.metrics?.condition ?? res.user?.condition ?? selectedUser.value?.condition ?? 'none'
    userHistory.value = res.history || []
    userDetail.value = {
      metrics: res.metrics || {},
      request_logs: res.request_logs || [],
      checkins: res.checkins || [],
      prompt_events: res.prompt_events || [],
      weekly_surveys: res.weekly_surveys || [],
    }
  } catch (err) {
    console.error('加载聊天记录失败:', err)
    toast.error('加载用户详情失败')
  }
}

const saveSelectedUserCondition = async () => {
  if (!selectedUser.value) return
  savingUserCondition.value = true
  try {
    const res = await adminAPI.updateUserCondition(selectedUser.value.id, selectedUserCondition.value)
    const nextCondition = res.condition || selectedUserCondition.value
    selectedUser.value = {
      ...selectedUser.value,
      condition: nextCondition,
    }
    userDetail.value = {
      ...userDetail.value,
      metrics: {
        ...(userDetail.value.metrics || {}),
        condition: nextCondition,
      },
    }
    toast.success('该被试的系统提示词条件已更新')
    await Promise.all([loadUsers(), loadStats(), loadDetailedStats()])
  } catch (err) {
    console.error('更新用户提示词条件失败:', err)
    toast.error(err.response?.data?.detail || '更新失败')
  } finally {
    savingUserCondition.value = false
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
    const res = await adminAPI.updateUserLongTermMemory(
      editingMemory.value.user_id || editingMemory.value.id,
      editingLongTermMemory.value
    )
    const backupName = res?.backup?.filename
    toast.success(backupName ? `记忆保存成功，已自动备份：${backupName}` : '记忆保存成功，已自动备份')
    showMemoryModal.value = false
    await loadAllMemory()
  } catch (err) {
    toast.error('保存记忆失败')
  } finally {
    loading.value = false
  }
}

const compressUserMemory = async () => {
  if (!editingMemory.value) return
  compressing.value = true
  try {
    const userId = editingMemory.value.user_id || editingMemory.value.id
    await adminAPI.compressUserMemory(userId)
    toast.success('记忆压缩成功')
    await loadAllMemory()
    if (editingMemory.value) {
      const res = await adminAPI.getUserMemory(userId)
      editingLongTermMemory.value = res.memory.long_term || ''
      editingMemoryHistory.value = res.memory.history_files || []
    }
  } catch (err) {
    console.error('压缩记忆失败:', err)
    toast.error(err.response?.data?.detail || '压缩记忆失败')
  } finally {
    compressing.value = false
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
      const res = await adminAPI.clearUserMemory(mem.user_id)
      const backupName = res?.backup?.filename
      toast.success(backupName ? `记忆已清空，已自动备份：${backupName}` : '记忆已清空，已自动备份')
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

// ==================== 提示系统 ====================
const loadPromptGroups = async () => {
  try {
    const res = await promptAPI.getGroups()
    promptGroups.value = res.prompt_groups || []
  } catch (err) {
    console.error('加载提示组失败:', err)
  }
}

const loadPromptStats = async () => {
  try {
    const res = await promptAPI.getStats()
    promptStats.value = res.stats || []
  } catch (err) {
    console.error('加载提示统计失败:', err)
  }
}

const openCreatePromptModal = () => {
  editingPromptGroup.value = null
  promptForm.value = {
    type: 'daily',
    name: '',
    enabled: true,
    threshold: 10,
    frequency_mode: 'once',
    repeat_every_n: null,
    max_times: null,
    cooldown_seconds: null,
    priority: 0,
    content: { title: '', body: '' },
    question: { kind: 'ack', required: false, options: [], placeholder: '', submit_text: '知道了' }
  }
  showPromptModal.value = true
}

const openEditPromptModal = (group) => {
  editingPromptGroup.value = group
  promptForm.value = {
    type: group.type || 'daily',
    name: group.name || '',
    enabled: group.enabled !== false,
    threshold: group.threshold || 10,
    frequency_mode: group.frequency_mode || 'once',
    repeat_every_n: group.repeat_every_n,
    max_times: group.max_times,
    cooldown_seconds: group.cooldown_seconds,
    priority: group.priority || 0,
    content: { ...group.content } || { title: '', body: '' },
    question: group.question ? { ...group.question } : { kind: 'ack', required: false, options: [], placeholder: '', submit_text: '知道了' }
  }
  showPromptModal.value = true
}

const savePromptGroup = async () => {
  if (!promptForm.value.name.trim()) {
    toast.error('请输入提示组名称')
    return
  }

  if (promptForm.value.frequency_mode === 'repeat_every_n') {
    const n = Number(promptForm.value.repeat_every_n)
    if (!Number.isFinite(n) || n < 1) {
      toast.error('重复触发需要填写“重复间隔（每隔N条）”且至少为1')
      return
    }
  }
  
  loading.value = true
  try {
    const data = { ...promptForm.value }
    if (editingPromptGroup.value) {
      await promptAPI.updateGroup(editingPromptGroup.value.id, data)
      toast.success('提示组已更新')
    } else {
      await promptAPI.createGroup(data)
      toast.success('提示组已创建')
    }
    showPromptModal.value = false
    await loadPromptGroups()
    await loadPromptStats()
  } catch (err) {
    toast.error('保存提示组失败')
  } finally {
    loading.value = false
  }
}

const deletePromptGroup = async (group) => {
  const confirmed = await confirm({
    title: '删除提示组',
    message: `确定要删除提示组 "${group.name}" 吗？`,
    type: 'danger',
    confirmText: '确认删除'
  })
  
  if (confirmed) {
    try {
      await promptAPI.deleteGroup(group.id)
      toast.success('提示组已删除')
      await loadPromptGroups()
      await loadPromptStats()
    } catch (err) {
      toast.error('删除失败')
    }
  }
}

const togglePromptEnabled = async (group) => {
  try {
    await promptAPI.updateGroup(group.id, { enabled: !group.enabled })
    group.enabled = !group.enabled
    toast.success(group.enabled ? '已启用' : '已停用')
  } catch (err) {
    toast.error('操作失败')
  }
}

const viewPromptAnswers = async (group) => {
  viewingGroupName.value = group.name
  try {
    const res = await promptAPI.getAnswers(group.id, 200)
    viewingAnswers.value = res.answers || []
    showAnswersModal.value = true
  } catch (err) {
    toast.error('加载回答失败')
  }
}

const formatPromptType = (type) => {
  const map = { daily: '日常提醒', survey: '问卷提醒', feedback: '反馈提醒' }
  return map[type] || type
}

const formatQuestionKind = (kind) => {
  const map = { ack: '确认按钮', choice_single: '单选题', choice_multi: '多选题', text: '填空题' }
  return map[kind] || kind
}

const getStatForGroup = (groupId) => {
  return promptStats.value.find(s => s.group_id === groupId) || {}
}

// 格式化
const formatDate = (dateString) => {
  if (!dateString) return '-'
  return formatShanghaiDateTime(dateString) || '-'
}

const formatTime = (dateString) => {
  if (!dateString) return ''
  return formatShanghaiMonthDayTime(dateString)
}

const formatCondition = (condition) => {
  const map = {
    'emotional': '情感表露',
    'factual': '事实表露',
    'none': '无表露'
  }
  return map[condition] || '无表露'
}

const formatLatency = (value) => {
  if (value === null || value === undefined || value === '') return '-'
  const n = Number(value)
  if (Number.isNaN(n)) return '-'
  return `${Math.round(n)} ms`
}

const getCheckinAnswerItems = (record) => {
  const target = record && typeof record === 'object' && 'answers' in record ? record : { answers: record }
  const answers = target?.answers
  if (!answers || typeof answers !== 'object') return []

  const questions = Array.isArray(target?.questions_snapshot) ? target.questions_snapshot : []
  if (questions.length > 0) {
    return questions
      .map((question, index) => ({
        key: `q${index}`,
        label: `${index + 1}. ${question}`,
        value: answers[`q${index}`] ?? '-',
      }))
  }

  return Object.entries(answers)
    .sort(([a], [b]) => {
      const ai = Number(String(a).replace(/[^0-9]/g, ''))
      const bi = Number(String(b).replace(/[^0-9]/g, ''))
      if (!Number.isNaN(ai) && !Number.isNaN(bi)) return ai - bi
      return String(a).localeCompare(String(b))
    })
    .map(([key, value], idx) => ({
      key,
      label: `${idx + 1}. ${key}`,
      value: value ?? '-',
    }))
}

const formatWeeklySurveyStatus = (status) => {
  const map = {
    read: '已读',
    shown: '已弹窗',
    pending: '待提醒',
    eligible: '已达标待派发',
    not_qualified: '未达标',
  }
  return map[status] || status || '-'
}

const formatWeeklySurveyCheckins = (record) => {
  if (!record) return '-'
  const current = Number(record.weekly_checkin_count_snapshot || 0)
  const required = Number(record.required_checkins_snapshot || 0)
  const qualified = record.qualified_checkin_count_snapshot
  if (qualified !== null && qualified !== undefined && qualified !== '') {
    return `${current}/${required || '-'}（触发时 ${qualified} 次）`
  }
  return `${current}/${required || '-'}`
}

const formatApiOverrideHint = (scope, field, effectiveValue, index = 0) => {
  const source = scope === 'primary'
    ? apiConfig.value.env_overrides?.primary
    : apiConfig.value.env_overrides?.backup?.[index]
  if (source?.[field]) {
    return `当前由环境变量覆盖，生效值：${effectiveValue || '-'}`
  }
  return `当前生效值：${effectiveValue || '-'}`
}

const getOutboundImageCount = (log) => {
  const messages = log?.outbound_summary?.messages
  if (!Array.isArray(messages)) return 0
  return messages.reduce((sum, item) => sum + Number(item?.image_count || 0), 0)
}

const conditionLabel = (mode) => {
  const map = {
    modulo: '按用户ID循环分配',
    random: '随机分配',
    fixed: `固定为${formatCondition(systemSettings.value.fixed_condition)}`,
    emotional: '情感表露',
    factual: '事实表露',
    none: '无表露',
  }
  return map[mode] || mode
}

// ==================== 打卡设置 ====================
const DEFAULT_CHECKIN_QUESTIONS = [
  '你现在的孤独感如何？',
  '你现在的情绪状态如何？',
  '你现在的压力程度如何？',
  '你现在的满足感如何？',
  '你现在的社交需求如何？',
]

const checkinSettings = ref({
  weekly_survey_url: '',
  checkin_questions: [...DEFAULT_CHECKIN_QUESTIONS],
})

const loadCheckinSettings = async () => {
  try {
    const res = await settingsAPI.getAdmin()
    checkinSettings.value.weekly_survey_url = res.weekly_survey_url || ''
    checkinSettings.value.checkin_questions = res.checkin_questions?.length
      ? res.checkin_questions
      : [...DEFAULT_CHECKIN_QUESTIONS]
  } catch (e) {
    console.error('加载打卡设置失败', e)
  }
}

const saveCheckinSettings = async () => {
  const validQuestions = checkinSettings.value.checkin_questions.filter(q => q.trim())
  if (validQuestions.length === 0) {
    toast.error('至少需要1道打卡题目')
    return
  }
  loading.value = true
  try {
    await settingsAPI.updateAdmin({
      weekly_survey_url: checkinSettings.value.weekly_survey_url,
      checkin_questions: validQuestions,
    })
    toast.success('打卡设置已保存')
    await loadCheckinSettings()
  } catch (e) {
    toast.error('保存失败')
  } finally {
    loading.value = false
  }
}

const addCheckinQuestion = () => {
  checkinSettings.value.checkin_questions.push('')
}

const removeCheckinQuestion = (i) => {
  checkinSettings.value.checkin_questions.splice(i, 1)
}

const runWeeklyCleanup = async (resetCheckins = false) => {
  const confirmed = await confirm({
    title: '执行每周清理',
    message: resetCheckins
      ? '这会把所有用户推进到新的实验周次：清空当前轮次，并同时重置本周打卡统计与周问卷弹窗标记。所有历史记录会完整保留，确定继续吗？'
      : '这会只清空所有用户的当前轮次缓存，不会修改周统计，也不会删除任何落盘记录。确定继续吗？',
    type: 'danger',
    confirmText: '确认执行',
  })
  if (!confirmed) return

  try {
    const res = await adminAPI.triggerWeeklyCleanup(resetCheckins)
    toast.success(
      resetCheckins
        ? `${res.message}，已将 ${res.updated_users} 位用户切换到 ${res.current_week_key}`
        : `${res.message}，已清空 ${res.updated_users} 位用户的轮次缓存`
    )
    await Promise.all([loadUsers(), loadDetailedStats(), loadStats()])
  } catch (err) {
    console.error('执行每周清理失败:', err)
    toast.error(err.response?.data?.detail || '执行每周清理失败')
  }
}

watch(activeTab, async (tab) => {
  if (tab === 'dashboard') {
    await renderCharts()
  }
  if (tab === 'analytics') {
    await loadDetailedStats()
  }
  if (tab === 'config') {
    await loadSystemSettings()
    await loadApiConfig()
  }
  if (tab === 'sysprompts') {
    await loadSystemSettings()
    await loadSystemPrompts()
  }
  if (tab === 'checkin') {
    await loadCheckinSettings()
  }
  if (tab === 'users') {
    await loadUsers()
  }
})

watch([filteredUsers, selectedUserIds], () => {
  if (!selectAllCheckbox.value) return
  const selectedCount = selectedUserIds.value.size
  const totalCount = filteredUsers.value.length
  selectAllCheckbox.value.indeterminate = selectedCount > 0 && selectedCount < totalCount
})

watch(activeSysPrompt, async (condition) => {
  if (activeTab.value === 'sysprompts') {
    await loadSystemPrompt(condition)
  }
})

onMounted(async () => {
  resetCustomInviteRows()
  await loadStats()
  await loadDetailedStats()
  loadUsers()
  loadInvites()
  loadInviteCodeSetting()
  loadAllMemory()
  loadContextConfig()
  loadSystemSettings()
  loadApiConfig()
  loadPromptGroups()
  loadPromptStats()
  loadCheckinSettings()
})

onUnmounted(() => {
  revokeExportUrl()
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

.panel-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
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

.users-table-wrapper {
  overflow-x: auto;
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

/* Checkin Badge */
.checkin-badge {
  padding: 0.25rem 0.6rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
}

.checkin-badge.done {
  background: rgba(34, 197, 94, 0.2);
  color: #4ade80;
  border: 1px solid rgba(34, 197, 94, 0.3);
}

.checkin-badge.pending {
  background: rgba(251, 191, 36, 0.2);
  color: #fbbf24;
  border: 1px solid rgba(251, 191, 36, 0.3);
}

/* Export Button */
.export-btn {
  background: rgba(99, 102, 241, 0.2);
  border: 1px solid rgba(99, 102, 241, 0.4);
  color: #a5b4fc;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.85rem;
  transition: background 0.2s;
}

.export-btn:hover {
  background: rgba(99, 102, 241, 0.35);
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
.invite-panel-subtitle {
  margin: 0.35rem 0 0;
  color: rgba(255, 255, 255, 0.68);
  font-size: 0.9rem;
}

.invite-create {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.75rem;
}

.invite-random-create {
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

.create-btn.secondary {
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.18);
}

.create-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(255, 215, 0, 0.3);
}

.create-btn:disabled,
.copy-btn:disabled,
.remove-row-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.new-invites-section {
  background: rgba(34, 197, 94, 0.1);
  border: 1px solid rgba(34, 197, 94, 0.3);
  border-radius: 12px;
  padding: 1.25rem;
  margin-bottom: 1.5rem;
}

.new-invites-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 1rem;
}

.new-invites-section h3 {
  margin: 0;
  color: #22c55e;
}

.new-invites-header p {
  margin: 0.35rem 0 0;
  color: rgba(255, 255, 255, 0.72);
  font-size: 0.85rem;
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

.new-invite-id {
  min-width: 56px;
  color: rgba(255, 255, 255, 0.68);
  font-weight: 600;
}

.new-invite-item code {
  flex: 1 1 240px;
  font-family: 'JetBrains Mono', monospace;
  color: #22c55e;
}

.new-invite-remark {
  min-width: 180px;
  max-width: 320px;
  color: rgba(255, 255, 255, 0.84);
  word-break: break-word;
}

.new-invite-remark.empty {
  color: rgba(255, 255, 255, 0.45);
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
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
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

.invite-search-input {
  min-width: 220px;
  flex: 1;
  background: rgba(0, 0, 0, 0.28);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: rgba(255, 255, 255, 0.9);
  padding: 0.52rem 0.75rem;
  border-radius: 8px;
  outline: none;
}

.invite-search-input::placeholder {
  color: rgba(255, 255, 255, 0.45);
}

.invite-search-input:focus {
  border-color: rgba(255, 215, 0, 0.65);
  box-shadow: 0 0 0 2px rgba(255, 215, 0, 0.15);
}

.mapping-hint {
  margin: 0 0 0.8rem 0;
  font-size: 0.82rem;
  color: rgba(255, 255, 255, 0.65);
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

.invite-remark-cell {
  min-width: 180px;
  max-width: 260px;
  word-break: break-word;
  color: rgba(255, 255, 255, 0.82);
}

.mini-copy {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: rgba(255, 255, 255, 0.82);
  padding: 0.2rem 0.45rem;
  border-radius: 6px;
  cursor: pointer;
  opacity: 0.72;
  transition: all 0.2s;
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

.custom-invite-modal {
  max-width: 980px;
}

.custom-invite-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
}

.custom-invite-tip {
  margin: 0;
  color: rgba(255, 255, 255, 0.72);
  line-height: 1.6;
}

.custom-invite-actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.custom-invite-grid {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.custom-invite-grid-header,
.custom-invite-row {
  display: grid;
  grid-template-columns: 72px minmax(220px, 1.6fr) minmax(220px, 1.2fr) 84px;
  gap: 0.75rem;
  align-items: center;
}

.custom-invite-grid-header {
  padding: 0 0.25rem;
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.82rem;
}

.custom-invite-row {
  background: rgba(0, 0, 0, 0.22);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  padding: 0.75rem;
}

.custom-row-index {
  color: #ffd700;
  font-weight: 700;
}

.custom-invite-row input {
  width: 100%;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  color: #fff;
  padding: 0.68rem 0.8rem;
  outline: none;
}

.custom-invite-row input:focus {
  border-color: rgba(255, 215, 0, 0.7);
  box-shadow: 0 0 0 2px rgba(255, 215, 0, 0.12);
}

.remove-row-btn {
  background: rgba(239, 68, 68, 0.12);
  border: 1px solid rgba(239, 68, 68, 0.22);
  color: #fca5a5;
  border-radius: 8px;
  padding: 0.55rem 0.4rem;
  cursor: pointer;
}

/* Config */
.config-sections {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.section-headline {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
}

.section-headline.small {
  margin-bottom: 0.75rem;
}

.config-section {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 12px;
  padding: 1.5rem;
}

.api-config-block,
.analytics-card,
.detail-block {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 12px;
  padding: 1rem;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.detail-block h4 {
  margin: 0 0 0.75rem;
  color: #ffd700;
  font-size: 0.95rem;
}

.api-config-block + .api-config-block,
.detail-block + .detail-block {
  margin-top: 1rem;
}

.backup-channel-card {
  margin-top: 0.75rem;
  padding: 1rem;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.empty-inline {
  color: rgba(255, 255, 255, 0.55);
}

.inline-actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
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

.config-row select,
.config-row textarea {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #fff;
  padding: 0.6rem;
  border-radius: 8px;
}

.config-checkbox {
  width: 18px;
  height: 18px;
  accent-color: #ffd700;
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

.modal-icon {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-right: 0.75rem;
  font-size: 1rem;
  font-weight: 700;
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
}

.modal-icon.success {
  background: rgba(16, 185, 129, 0.18);
  color: #34d399;
}

.modal-icon.danger {
  background: rgba(239, 68, 68, 0.18);
  color: #f87171;
}

.modal-message {
  margin: 0;
  padding: 0 1.5rem;
  color: rgba(255, 255, 255, 0.78);
  line-height: 1.7;
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

.export-modal {
  max-width: 560px;
  max-height: none;
}

.export-modal .modal-header {
  justify-content: flex-start;
}

.export-progress,
.export-ready {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.9rem;
  padding: 0.5rem 0 1rem;
}

.export-progress {
  color: rgba(255, 255, 255, 0.8);
}

.export-spinner {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  border: 4px solid rgba(255, 255, 255, 0.12);
  border-top-color: #ffd700;
  animation: exportSpin 0.85s linear infinite;
}

.export-file {
  width: 100%;
  padding: 0.9rem 1rem;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: #fff;
  font-size: 0.92rem;
  word-break: break-all;
}

.download-link {
  color: #ffd700;
  text-decoration: underline;
  font-size: 0.92rem;
}

@keyframes exportSpin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.mono-cell {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.82rem;
}

.wide-cell {
  max-width: 320px;
  word-break: break-word;
}

.checkin-answer-cell {
  min-width: 420px;
}

.checkin-answer-list {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.checkin-answer-item {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 0.6rem;
  padding: 0.4rem 0.55rem;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.04);
}

.checkin-answer-question {
  color: rgba(255, 255, 255, 0.85);
  font-size: 0.8rem;
  line-height: 1.35;
}

.checkin-answer-score {
  min-width: 28px;
  text-align: center;
  padding: 0.2rem 0.45rem;
  border-radius: 999px;
  background: rgba(250, 204, 21, 0.16);
  border: 1px solid rgba(250, 204, 21, 0.42);
  color: #fde68a;
  font-size: 0.75rem;
  font-weight: 700;
}

.checkin-answer-empty {
  color: rgba(255, 255, 255, 0.5);
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
.chat-history-section {
  margin-top: 1rem;
}

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
  background: rgba(12, 18, 32, 0.42);
  border: 1px solid rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(12px);
  border-radius: 8px;
  align-items: flex-start;
}

.history-msg.assistant {
  background: rgba(251, 191, 36, 0.08);
  border-color: rgba(251, 191, 36, 0.18);
}

.history-msg.user {
  background: rgba(59, 130, 246, 0.08);
  border-color: rgba(59, 130, 246, 0.18);
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
    flex-direction: column;
    align-items: stretch;
  }

  .invite-random-create {
    width: 100%;
  }
  
  .invite-count-input {
    flex: 1;
  }

  .new-invites-header,
  .new-invite-item,
  .custom-invite-toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .custom-invite-grid-header {
    display: none;
  }

  .custom-invite-row {
    grid-template-columns: 1fr;
  }
}

/* ==================== 提示系统样式 ==================== */
.prompts-panel .empty-state {
  text-align: center;
  padding: 3rem;
  color: rgba(255, 255, 255, 0.5);
}

.prompt-groups-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.prompt-group-card {
  background: rgba(0, 0, 0, 0.3);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  overflow: hidden;
  transition: all 0.2s;
}

.prompt-group-card:hover {
  border-color: rgba(255, 215, 0, 0.3);
}

.prompt-group-card.disabled {
  opacity: 0.6;
}

.pg-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.25rem;
  background: rgba(255, 255, 255, 0.05);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.pg-title-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.pg-type-badge {
  padding: 0.25rem 0.6rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
}

.pg-type-badge.daily {
  background: #FFF3CD;
  color: #856404;
}

.pg-type-badge.survey {
  background: #CCE5FF;
  color: #004085;
}

.pg-type-badge.feedback {
  background: #D4EDDA;
  color: #155724;
}

.pg-name {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: #fff;
}

.pg-disabled-badge {
  padding: 0.2rem 0.5rem;
  background: rgba(255, 0, 0, 0.2);
  color: #ff6b6b;
  border-radius: 4px;
  font-size: 0.7rem;
}

.pg-actions {
  display: flex;
  gap: 0.5rem;
}

.pg-btn {
  background: rgba(255, 255, 255, 0.1);
  border: none;
  padding: 0.4rem 0.6rem;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.9rem;
}

.pg-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

.pg-btn.delete:hover {
  background: rgba(255, 0, 0, 0.3);
}

.pg-body {
  padding: 1rem 1.25rem;
}

.pg-info {
  display: flex;
  gap: 1.5rem;
  margin-bottom: 0.75rem;
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.7);
}

.pg-info strong {
  color: rgba(255, 255, 255, 0.9);
}

.pg-content-preview {
  background: rgba(0, 0, 0, 0.2);
  padding: 0.75rem;
  border-radius: 6px;
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 0.75rem;
}

.pg-stats {
  display: flex;
  gap: 1.5rem;
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.5);
}

/* 提示组编辑弹窗 */
.prompt-edit-modal {
  max-width: 600px;
  max-height: 85vh;
  overflow-y: auto;
}

.prompt-form .form-row {
  margin-bottom: 1rem;
}

.prompt-form .form-row label {
  display: block;
  margin-bottom: 0.4rem;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.9);
}

.prompt-form input[type="text"],
.prompt-form input[type="number"],
.prompt-form select,
.prompt-form textarea {
  width: 100%;
  padding: 0.6rem 0.8rem;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  color: #fff;
  font-size: 0.95rem;
}

.prompt-form input:focus,
.prompt-form select:focus,
.prompt-form textarea:focus {
  outline: none;
  border-color: #ffd700;
}

.prompt-form .form-hint {
  display: block;
  margin-top: 0.3rem;
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.5);
}

.prompt-form .form-divider {
  border: none;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  margin: 1.5rem 0;
}

.prompt-form .checkbox-row label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}

.prompt-form .checkbox-row input[type="checkbox"] {
  width: auto;
  accent-color: #ffd700;
}

/* 回答列表弹窗 */
.answers-modal {
  max-width: 600px;
  max-height: 80vh;
}

.answers-list {
  max-height: 50vh;
  overflow-y: auto;
}

.answer-item {
  background: rgba(0, 0, 0, 0.2);
  padding: 0.75rem 1rem;
  border-radius: 8px;
  margin-bottom: 0.5rem;
}

.answer-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
  font-size: 0.85rem;
}

.answer-user {
  font-weight: 600;
  color: #ffd700;
}

.answer-time {
  color: rgba(255, 255, 255, 0.5);
}

.answer-content {
  color: rgba(255, 255, 255, 0.9);
  font-size: 0.95rem;
}

.charts-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1.25rem;
  margin-top: 1.5rem;
}

.analytics-grid {
  display: grid;
  gap: 1rem;
  margin-top: 1.5rem;
}

.analytics-card-header {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: baseline;
  margin-bottom: 0.75rem;
}

.analytics-card-header h3 {
  margin: 0;
  color: #ffd700;
}

.analytics-card-header span {
  color: rgba(255, 255, 255, 0.58);
  font-size: 0.85rem;
}

.analytics-table-wrap {
  overflow: auto;
}

.analytics-table.compact {
  font-size: 0.84rem;
}

.analytics-table-wrap.compact {
  max-height: 260px;
}

.chart-card,
.strategy-card,
.sysprompt-editor-card {
  background: rgba(10, 18, 36, 0.45);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 18px;
  backdrop-filter: blur(16px);
}

.chart-card {
  padding: 1rem 1rem 0.75rem;
}

.chart-card-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}

.chart-card-header h3,
.strategy-header h4,
.sysprompt-editor-header h3 {
  margin: 0;
  color: #ffd700;
}

.chart-card-header span,
.strategy-header span,
.sysprompt-editor-header p,
.sysprompt-hint {
  color: rgba(255, 255, 255, 0.62);
  font-size: 0.86rem;
}

.chart-wrap {
  position: relative;
  height: 280px;
}

.strategy-card {
  padding: 1rem;
  margin-bottom: 1rem;
}

.strategy-header {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 0.9rem;
}

.strategy-options {
  display: grid;
  gap: 0.75rem;
}

.strategy-option {
  display: flex;
  gap: 0.75rem;
  align-items: flex-start;
  padding: 0.85rem 1rem;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  cursor: pointer;
}

.strategy-option input {
  margin-top: 0.2rem;
  accent-color: #ffd700;
}

.strategy-option p {
  margin: 0.2rem 0 0;
  color: rgba(255, 255, 255, 0.58);
  font-size: 0.84rem;
}

.fixed-condition-row {
  margin-top: 1rem;
}

.condition-chip-row {
  display: flex;
  gap: 0.75rem;
  margin-top: 0.5rem;
  flex-wrap: wrap;
}

.condition-chip {
  padding: 0.55rem 0.9rem;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.06);
  color: rgba(255, 255, 255, 0.82);
  cursor: pointer;
}

.condition-chip.active {
  background: rgba(251, 191, 36, 0.18);
  color: #ffd700;
  border-color: rgba(251, 191, 36, 0.45);
}

.sysprompt-layout {
  display: grid;
  grid-template-columns: 220px minmax(0, 1fr);
  gap: 1rem;
}

.sysprompt-sidebar {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.prompt-tab-btn {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.75rem;
  width: 100%;
  padding: 0.9rem 1rem;
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.04);
  color: rgba(255, 255, 255, 0.9);
  cursor: pointer;
  text-align: left;
}

.prompt-tab-btn small {
  color: rgba(255, 255, 255, 0.52);
}

.prompt-tab-btn.active {
  background: rgba(251, 191, 36, 0.16);
  border-color: rgba(251, 191, 36, 0.38);
  color: #ffd700;
}

.sysprompt-editor-card {
  padding: 1rem;
}

.sysprompt-editor-header {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: center;
  margin-bottom: 0.75rem;
}

.sysprompt-hint {
  margin-bottom: 0.8rem;
}

.prompt-textarea {
  width: 100%;
  min-height: 420px;
  padding: 1rem;
  background: rgba(0, 0, 0, 0.28);
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 14px;
  color: #fff;
  font-size: 0.95rem;
  line-height: 1.6;
  resize: vertical;
}

.prompt-textarea:focus {
  outline: none;
  border-color: rgba(251, 191, 36, 0.5);
}

.modal-btn.accent {
  background: rgba(59, 130, 246, 0.18);
  border-color: rgba(59, 130, 246, 0.4);
  color: #93c5fd;
}

.modal-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

@media (max-width: 960px) {
  .charts-row,
  .sysprompt-layout {
    grid-template-columns: 1fr;
  }

  .sysprompt-sidebar {
    flex-direction: row;
    overflow-x: auto;
  }
}

/* ==================== 打卡设置页 ==================== */
.checkin-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

@media (max-width: 900px) {
  .checkin-layout { grid-template-columns: 1fr; }
}

.checkin-col {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.checkin-card {
  background: rgba(0, 0, 0, 0.25);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 14px;
  padding: 1.25rem;
}

.checkin-card h3 {
  margin: 0 0 0.4rem;
  color: #ffd700;
  font-size: 1rem;
}

.checkin-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.checkin-card-header > div { flex: 1; }

.create-btn.small {
  padding: 0.4rem 0.8rem;
  font-size: 0.82rem;
  white-space: nowrap;
}

.questions-list {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.question-edit-row {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.q-num {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: rgba(255, 215, 0, 0.15);
  color: #ffd700;
  font-size: 0.78rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.q-input {
  flex: 1;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.15);
  color: #fff;
  padding: 0.5rem 0.75rem;
  border-radius: 8px;
  font-size: 0.9rem;
}

.q-input:focus {
  outline: none;
  border-color: rgba(255, 215, 0, 0.5);
}

.q-del-btn {
  width: 26px;
  height: 26px;
  border-radius: 6px;
  border: none;
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
  cursor: pointer;
  font-size: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.q-del-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.url-input {
  width: 100%;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.15);
  color: #fff;
  padding: 0.6rem 0.75rem;
  border-radius: 8px;
  font-size: 0.9rem;
  box-sizing: border-box;
}

.url-input:focus {
  outline: none;
  border-color: rgba(255, 215, 0, 0.5);
}

.cleanup-card { }

.cleanup-explain {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin: 1rem 0;
}

.explain-block {
  display: flex;
  gap: 0.75rem;
  align-items: flex-start;
  background: rgba(255, 255, 255, 0.04);
  border-radius: 10px;
  padding: 0.85rem;
}

.explain-icon {
  font-size: 1.4rem;
  flex-shrink: 0;
  margin-top: 2px;
}

.explain-block strong {
  display: block;
  color: #fff;
  margin-bottom: 0.3rem;
  font-size: 0.95rem;
}

.explain-block p {
  margin: 0;
  font-size: 0.82rem;
  color: rgba(255, 255, 255, 0.6);
  line-height: 1.5;
}

.explain-block code {
  background: rgba(255, 215, 0, 0.12);
  color: #ffd700;
  padding: 0 4px;
  border-radius: 3px;
  font-size: 0.8rem;
}

.explain-block em {
  color: rgba(255, 255, 255, 0.8);
  font-style: normal;
  font-weight: 600;
}

.cleanup-actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.cleanup-btn {
  flex: 1;
  min-width: 140px;
  padding: 0.7rem 1rem;
  border-radius: 10px;
  border: none;
  font-size: 0.88rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.cleanup-btn.secondary {
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.85);
  border: 1px solid rgba(255, 255, 255, 0.15);
}

.cleanup-btn.secondary:hover {
  background: rgba(255, 255, 255, 0.18);
}

.cleanup-btn.danger {
  background: rgba(239, 68, 68, 0.15);
  color: #f87171;
  border: 1px solid rgba(239, 68, 68, 0.25);
}

.cleanup-btn.danger:hover {
  background: rgba(239, 68, 68, 0.28);
}

/* ==================== 用户详情弹窗改进 ==================== */
.user-detail-modal {
  max-width: 900px;
  max-height: 88vh;
}

.user-detail-hero {
  display: flex;
  align-items: center;
  gap: 1.25rem;
  padding: 1rem 1.25rem;
  background: rgba(255, 215, 0, 0.06);
  border-radius: 12px;
  margin-bottom: 1.25rem;
  border: 1px solid rgba(255, 215, 0, 0.12);
}

.user-avatar-circle {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: linear-gradient(135deg, #ffd700, #ffa500);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.4rem;
  font-weight: 700;
  color: #1a1a2e;
  flex-shrink: 0;
}

.user-hero-info { flex: 1; }

.user-hero-name {
  font-size: 1.15rem;
  font-weight: 700;
  color: #fff;
  margin-bottom: 0.2rem;
}

.user-hero-meta {
  font-size: 0.82rem;
  color: rgba(255, 255, 255, 0.55);
}

.user-condition-editor {
  margin-top: 0.8rem;
  display: flex;
  align-items: end;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.user-condition-editor label {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  font-size: 0.78rem;
  color: rgba(255, 255, 255, 0.72);
}

.user-condition-editor select {
  min-width: 180px;
  padding: 0.45rem 0.65rem;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(15, 23, 42, 0.82);
  color: #fff;
}

.mini-action-btn {
  border: 1px solid rgba(250, 204, 21, 0.28);
  background: rgba(250, 204, 21, 0.14);
  color: #fde68a;
  border-radius: 8px;
  padding: 0.48rem 0.9rem;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.mini-action-btn:hover:not(:disabled) {
  background: rgba(250, 204, 21, 0.22);
}

.mini-action-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.user-metrics-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.75rem;
  margin-bottom: 1.25rem;
}

@media (max-width: 700px) {
  .user-metrics-grid { grid-template-columns: repeat(2, 1fr); }
}

.metric-card {
  background: rgba(0, 0, 0, 0.25);
  border-radius: 10px;
  padding: 0.75rem;
  text-align: center;
  border: 1px solid rgba(255, 255, 255, 0.07);
}

.metric-value {
  font-size: 1.4rem;
  font-weight: 700;
  color: #ffd700;
  line-height: 1;
  margin-bottom: 0.3rem;
}

.metric-label {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
}

/* 用户多选 */
.select-all-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem 0;
  margin-bottom: 0.5rem;
}

.select-all-row label {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  cursor: pointer;
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.8);
}

.bulk-export-btn {
  background: rgba(99, 102, 241, 0.2);
  border: 1px solid rgba(99, 102, 241, 0.4);
  color: #a5b4fc;
  padding: 0.4rem 0.9rem;
  border-radius: 7px;
  cursor: pointer;
  font-size: 0.82rem;
  transition: background 0.2s;
}

.bulk-export-btn:hover:not(:disabled) {
  background: rgba(99, 102, 241, 0.35);
}

.bulk-export-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.row-checkbox {
  accent-color: #ffd700;
  width: 15px;
  height: 15px;
  cursor: pointer;
}

.selected-row {
  background: rgba(255, 215, 0, 0.06) !important;
}
</style>
