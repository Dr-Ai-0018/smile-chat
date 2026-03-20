import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import './style.css'
import App from './App.vue'

// 导入页面组件
import Login from './pages/Login.vue'
import Register from './pages/Register.vue'
import Chat from './pages/Chat.vue'
import Settings from './pages/Settings.vue'
import Admin from './pages/Admin.vue'

// 路由配置
const routes = [
  { path: '/', redirect: '/chat' },
  { path: '/login', component: Login },
  { path: '/register', component: Register },
  { path: '/chat', component: Chat, meta: { requiresAuth: true } },
  { path: '/settings', component: Settings, meta: { requiresAuth: true } },
  { path: '/admin', component: Admin, meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/experiment/start', redirect: '/chat' },
  { path: '/experiment/end', redirect: '/chat' },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')

  if (to.meta.requiresAuth && !token) {
    return next('/login')
  }

  next()
})

const app = createApp(App)
app.use(router)
app.mount('#app')

if (import.meta.env.PROD && 'serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch((err) => {
      console.warn('Service worker 注册失败:', err)
    })
  })
} else if ('serviceWorker' in navigator) {
  navigator.serviceWorker.getRegistrations().then((registrations) => {
    registrations
      .filter((registration) => registration.active?.scriptURL?.includes('/sw.js'))
      .forEach((registration) => {
        registration.unregister().catch(() => {})
      })
  }).catch(() => {})
}
