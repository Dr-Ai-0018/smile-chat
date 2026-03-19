<template>
  <div class="login-page">
    <div class="login-card">
      <h1>启明聊天</h1>
      <p class="subtitle">欢迎回来</p>
      
      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <input
            v-model="form.username"
            type="text"
            placeholder="用户名"
            required
          />
        </div>
        
        <div class="form-group">
          <input
            v-model="form.password"
            type="password"
            placeholder="密码"
            required
          />
        </div>
        
        <button type="submit" :disabled="loading">
          {{ loading ? '登录中...' : '登录' }}
        </button>
      </form>
      
      <div class="footer">
        还没有账号？<router-link to="/register">立即注册</router-link>
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
  password: ''
})

const loading = ref(false)
const error = ref('')

const handleLogin = async () => {
  loading.value = true
  error.value = ''
  
  try {
    const response = await authAPI.login(form.value.username, form.value.password)
    
    // 保存token和用户信息
    localStorage.setItem('token', response.access_token)
    localStorage.setItem('user', JSON.stringify({
      id: response.user_id,
      username: response.username
    }))
    
    router.push('/chat')
  } catch (err) {
    error.value = err.response?.data?.detail || '登录失败，请检查用户名和密码'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%);
}

.login-card {
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
  border-color: var(--color-primary);
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
