/**
 * API客户端封装
 */
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'
const API_ORIGIN = new URL(API_BASE_URL, window.location.origin).origin

// 创建axios实例
const client = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json'
  },
  // 支持大图片传输（base64编码后可能很大）
  maxContentLength: Infinity,
  maxBodyLength: Infinity
})

// 请求拦截器 - 添加Token
client.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器 - 处理错误
client.interceptors.response.use(
  response => response.data,
  error => {
    if (error.response?.status === 401) {
      // Token过期或无效，清除并跳转登录
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export { API_BASE_URL, API_ORIGIN }
export default client
