/**
 * API接口定义
 */
import client from './client'
import axios from 'axios'
import { API_BASE_URL } from './client'

export const authAPI = {
  // 登录
  login: (username, password) => 
    client.post('/auth/login', { username, password }),
  
  // 注册
  register: (username, password, invite_code) => 
    client.post('/auth/register', { username, password, invite_code }),
  
  // 获取邀请码系统状态
  getInviteCodeStatus: () => client.get('/auth/invite_code_status')
}

export const userAPI = {
  // 获取个人信息
  getProfile: () => client.get('/user/profile'),
  
  // 上传头像
  uploadAvatar: (formData) => client.post('/user/avatar', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export const chatAPI = {
  // 发送消息（带完整上下文，支持图片）
  sendMessageWithContext: (messages, options = {}) => 
    client.post('/chat/send_with_context', { messages }, options),
  
  // 发送消息（旧接口兼容）
  sendMessage: (content) => client.post('/chat/send', { content }),
  
  // 获取聊天历史
  getHistory: (limit = 100) => client.get(`/chat/history?limit=${limit}`)
}

export const imageAPI = {
  // 上传图片
  upload: (formData) => client.post('/image/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export const adminAPI = {
  // 获取用户列表
  getUsers: () => client.get('/admin/users'),
  
  // 创建邀请码
  createInvites: (count) => client.post('/admin/create_invite', { count }),
  
  // 获取邀请码列表
  getInvites: () => client.get('/admin/invites'),
  
  // 重置密码
  resetPassword: (userId, newPassword) => 
    client.post('/admin/reset_password', { user_id: userId, new_password: newPassword }),
  
  // 查看用户聊天记录（管理员权限）
  getUserHistory: (userId, limit = 100) => 
    client.get(`/admin/user/${userId}/history?limit=${limit}`),
  
  // 查看用户记忆（管理员权限）
  getUserMemory: (userId) => client.get(`/admin/user/${userId}/memory`),
  
  // 清空用户聊天记录（管理员权限）
  clearUserHistory: (userId) => client.delete(`/admin/user/${userId}/history`),
  
  // 获取所有用户的记忆状态
  getAllMemory: () => client.get('/admin/memory/all'),
  
  // 更新用户长期记忆
  updateUserLongTermMemory: (userId, content) => 
    client.put(`/admin/user/${userId}/memory/long_term`, { content }),
  
  // 清空用户记忆
  clearUserMemory: (userId) => client.delete(`/admin/user/${userId}/memory`),

  // 手动压缩用户记忆
  compressUserMemory: (userId) => client.post(`/admin/user/${userId}/memory/compress`),
  
  // 获取历史文件内容
  getHistoryFile: (userId, filename) => 
    client.get(`/admin/user/${userId}/history_file/${filename}`),
  
  // 删除用户
  deleteUser: (userId) => client.delete(`/admin/user/${userId}`),
  
  // 获取系统统计
  getStats: () => client.get('/admin/stats'),
  getDetailedStats: () => client.get('/admin/stats/detailed'),
  getUserDetail: (userId, params = {}) => {
    const query = new URLSearchParams()
    if (params.log_limit) query.set('log_limit', params.log_limit)
    if (params.history_limit) query.set('history_limit', params.history_limit)
    const suffix = query.toString() ? `?${query.toString()}` : ''
    return client.get(`/admin/user/${userId}/detail${suffix}`)
  },
  updateUserCondition: (userId, condition) =>
    client.put(`/admin/user/${userId}/condition`, { condition }),
  exportUsers: (userIds) => client.post('/admin/users/export', { user_ids: userIds }),
  exportUsersZip: (userIds) => {
    const token = localStorage.getItem('token')
    return axios.post(`${API_BASE_URL}/admin/users/export-zip`, { user_ids: userIds }, {
      responseType: 'blob',
      timeout: 300000,
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
  },
  
  // 获取邀请码开关状态
  getInviteCodeSetting: () => client.get('/admin/settings/invite_code'),
  
  // 设置邀请码开关状态
  setInviteCodeSetting: (enabled) =>
    client.post('/admin/settings/invite_code', { enabled }),

  // 获取本周未完成打卡的用户
  getIncompleteCheckins: () => client.get('/admin/checkin/incomplete'),
  triggerWeeklyCleanup: (reset_checkins = false) =>
    client.post('/admin/checkin/weekly-cleanup', { reset_checkins }),

  // 系统提示词管理
  listSystemPrompts: () => client.get('/admin/system-prompts'),
  getSystemPrompt: (condition) => client.get(`/admin/system-prompts/${condition}`),
  updateSystemPrompt: (condition, content) =>
    client.put(`/admin/system-prompts/${condition}`, { content }),
}

export const configAPI = {
  // 获取上下文配置
  getContextConfig: () => client.get('/config/context'),
  
  // 更新上下文配置
  updateContextConfig: (config) => client.post('/config/context', config),
  
  // 获取API配置
  getApiConfig: () => client.get('/config/api'),

  // 更新API配置
  updateApiConfig: (config) => client.put('/config/api', config)
}

export const promptAPI = {
  // 用户端：评估是否需要展示提示
  evaluate: (sinceResetUserMessageCount) => 
    client.post('/prompts/evaluate', { since_reset_user_message_count: sinceResetUserMessageCount }),
  
  // 用户端：记录提示已展示
  recordShown: (groupId, clientRequestId, chatCountSnapshot = 0) =>
    client.post(`/prompts/${groupId}/shown`, { 
      client_request_id: clientRequestId, 
      chat_count_snapshot: chatCountSnapshot 
    }),
  
  // 用户端：提交回答
  submitAnswer: (groupId, clientRequestId, answer, chatCountSnapshot = 0) =>
    client.post(`/prompts/${groupId}/answer`, { 
      client_request_id: clientRequestId, 
      answer, 
      chat_count_snapshot: chatCountSnapshot 
    }),
  
  // 用户端：跳过提示
  skip: (groupId, clientRequestId, chatCountSnapshot = 0) =>
    client.post(`/prompts/${groupId}/skip`, { 
      client_request_id: clientRequestId, 
      chat_count_snapshot: chatCountSnapshot 
    }),
  
  // 用户端：重置计数器
  resetCounter: (promptGroupId = null) =>
    client.post('/prompts/reset-counter', { prompt_group_id: promptGroupId }),

  // 管理端：获取提示组列表
  getGroups: (includeDeleted = false) => 
    client.get(`/admin/prompt-groups?include_deleted=${includeDeleted}`),
  
  // 管理端：创建提示组
  createGroup: (data) => client.post('/admin/prompt-groups', data),
  
  // 管理端：更新提示组
  updateGroup: (groupId, data) => client.put(`/admin/prompt-groups/${groupId}`, data),
  
  // 管理端：删除提示组
  deleteGroup: (groupId, hard = false) => 
    client.delete(`/admin/prompt-groups/${groupId}?hard=${hard}`),
  
  // 管理端：获取统计数据
  getStats: () => client.get('/admin/prompt-stats'),
  
  // 管理端：获取事件日志
  getEvents: (params = {}) => {
    const query = new URLSearchParams()
    if (params.user_id) query.set('user_id', params.user_id)
    if (params.group_id) query.set('group_id', params.group_id)
    if (params.event_type) query.set('event_type', params.event_type)
    if (params.limit) query.set('limit', params.limit)
    return client.get(`/admin/prompt-events?${query.toString()}`)
  },
  
  // 管理端：获取回答列表
  getAnswers: (groupId, limit = 100) =>
    client.get(`/admin/prompt-groups/${groupId}/answers?limit=${limit}`)
}

export const noticeAPI = {
  getPending: () => client.get('/notices/pending'),
  getInbox: () => client.get('/notices/inbox'),
  markShown: (id) => client.post(`/notices/${id}/shown`),
  markRead: (id) => client.post(`/notices/${id}/read`),
}

export const checkinAPI = {
  getStatus: () => client.get('/checkin/status'),
  submit: (answers) => client.post('/checkin/submit', { answers }),
  checkWeekendSurvey: () => client.get('/checkin/weekend_survey_check'),
  getQuestions: () => client.get('/checkin/questions'),
}

export const settingsAPI = {
  getAdmin: () => client.get('/admin/settings'),
  updateAdmin: (data) => client.put('/admin/settings', data),
}
