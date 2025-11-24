<template>
  <div class="register-page">
    <div class="register-card">
      <h1>启明聊天</h1>
      <p class="subtitle">创建新账号</p>
      
      <form @submit.prevent="handleRegister">
        <div class="form-group">
          <input
            v-model="form.username"
            type="text"
            placeholder="用户名（3-20个字符）"
            required
            minlength="3"
            maxlength="20"
          />
        </div>
        
        <div class="form-group">
          <input
            v-model="form.password"
            type="password"
            placeholder="密码（至少6个字符）"
            required
            minlength="6"
          />
        </div>
        
        <div class="form-group">
          <input
            v-model="form.confirmPassword"
            type="password"
            placeholder="确认密码"
            required
          />
        </div>
        
        <div class="form-group">
          <input
            v-model="form.inviteCode"
            type="text"
            placeholder="邀请码"
            required
          />
        </div>
        
        <button type="submit" :disabled="loading">
          {{ loading ? '注册中...' : '注册' }}
        </button>
      </form>
      
      <div class="footer">
        已有账号？<router-link to="/login">立即登录</router-link>
      </div>
      
      <div v-if="error" class="error-message">
        {{ error }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { authAPI } from '../api'

const router = useRouter()

const form = ref({
  username: '',
  password: '',
  confirmPassword: '',
  inviteCode: ''
})

const loading = ref(false)
const error = ref('')

const handleRegister = async () => {
  // 验证密码匹配
  if (form.value.password !== form.value.confirmPassword) {
    error.value = '两次密码输入不一致'
    return
  }
  
  loading.value = true
  error.value = ''
  
  try {
    const response = await authAPI.register(
      form.value.username,
      form.value.password,
      form.value.inviteCode
    )
    
    // 保存token和用户信息
    localStorage.setItem('token', response.access_token)
    localStorage.setItem('user', JSON.stringify({
      id: response.user_id,
      username: response.username
    }))
    
    // 跳转到聊天页面
    router.push('/chat')
  } catch (err) {
    error.value = err.response?.data?.detail || '注册失败，请检查信息'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.register-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, var(--color-accent) 0%, var(--color-light) 100%);
}

.register-card {
  background: white;
  padding: 3rem;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 400px;
}

h1 {
  color: var(--color-dark);
  margin-bottom: 0.5rem;
  font-size: 2rem;
}

.subtitle {
  color: #666;
  margin-bottom: 2rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

input {
  width: 100%;
  padding: 0.8rem 1rem;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 1rem;
}

input:focus {
  border-color: var(--color-accent);
}

button {
  width: 100%;
  padding: 0.8rem;
  font-size: 1rem;
  border-radius: 8px;
  margin-top: 1rem;
}

.footer {
  margin-top: 1.5rem;
  text-align: center;
  color: #666;
}

.error-message {
  margin-top: 1rem;
  padding: 0.8rem;
  background: #fee;
  color: #c00;
  border-radius: 8px;
  text-align: center;
}
</style>
