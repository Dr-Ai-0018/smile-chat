/**
 * 全局Toast服务
 * 用于在任何组件中显示提示和确认弹窗
 */
import { ref } from 'vue'

// 存储Toast组件实例
let toastInstance = null

// 设置Toast实例
export const setToastInstance = (instance) => {
  toastInstance = instance
}

// Toast方法
export const toast = {
  success: (message) => toastInstance?.success(message),
  error: (message) => toastInstance?.error(message),
  warning: (message) => toastInstance?.warning(message),
  info: (message) => toastInstance?.info(message),
  show: (message, type, duration) => toastInstance?.showToast(message, type, duration)
}

// 确认弹窗
export const confirm = (options) => {
  if (typeof options === 'string') {
    options = { message: options }
  }
  return toastInstance?.showConfirm(options)
}

export default { toast, confirm, setToastInstance }

