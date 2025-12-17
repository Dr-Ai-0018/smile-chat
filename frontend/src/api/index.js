/**
 * API接口定义
 */
import client from './client'

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
  
  // 获取历史文件内容
  getHistoryFile: (userId, filename) => 
    client.get(`/admin/user/${userId}/history_file/${filename}`),
  
  // 删除用户
  deleteUser: (userId) => client.delete(`/admin/user/${userId}`),
  
  // 获取系统统计
  getStats: () => client.get('/admin/stats'),
  
  // 获取邀请码开关状态
  getInviteCodeSetting: () => client.get('/admin/settings/invite_code'),
  
  // 设置邀请码开关状态
  setInviteCodeSetting: (enabled) => 
    client.post('/admin/settings/invite_code', { enabled })
}

export const configAPI = {
  // 获取上下文配置
  getContextConfig: () => client.get('/config/context'),
  
  // 更新上下文配置
  updateContextConfig: (config) => client.post('/config/context', config),
  
  // 获取API配置
  getApiConfig: () => client.get('/config/api')
}
