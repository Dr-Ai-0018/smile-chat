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
    client.post('/auth/register', { username, password, invite_code })
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
  // 发送消息
  sendMessage: (content) => client.post('/chat/send', { content }),
  
  // 获取聊天历史
  getHistory: (limit = 50) => client.get(`/chat/history?limit=${limit}`)
}

export const imageAPI = {
  // 上传图片
  upload: (formData) => client.post('/image/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  
  // 识别图片
  recognize: () => client.post('/image/recognize')
}

export const memoryAPI = {
  // 获取记忆
  getMemory: (userId) => client.get(`/memory/${userId}`),
  
  // 更新记忆
  updateMemory: (data) => client.post('/memory/update', data),
  
  // 压缩记忆
  compressMemory: (userId) => client.post('/memory/compress', { user_id: userId })
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
    client.post('/admin/reset_password', { user_id: userId, new_password: newPassword })
}

export const configAPI = {
  // 获取上下文配置
  getContextConfig: () => client.get('/config/context'),
  
  // 更新上下文配置
  updateContextConfig: (config) => client.post('/config/context', config),
  
  // 获取API配置
  getApiConfig: () => client.get('/config/api')
}
