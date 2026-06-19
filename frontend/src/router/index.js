import { createRouter, createWebHistory } from 'vue-router'
import axios from 'axios'

const routes = [
  { path: '/setup', component: () => import('../views/Setup.vue'), meta: { guest: true, setup: true } },
  { path: '/login', component: () => import('../views/Login.vue'), meta: { guest: true } },
  {
    path: '/',
    component: () => import('../components/Layout.vue'),
    children: [
      { path: '', redirect: '/dashboard' },
      { path: 'dashboard', component: () => import('../views/Dashboard.vue') },
      { path: 'subscriptions', component: () => import('../views/Subscriptions.vue') },
      { path: 'calendar', component: () => import('../views/Calendar.vue') },
      { path: 'reports', component: () => import('../views/Reports.vue') },
      { path: 'notifications', component: () => import('../views/Notifications.vue') },
      { path: 'logs', component: () => import('../views/Logs.vue') },
      { path: 'settings', component: () => import('../views/Settings.vue') },
      { path: 'users', component: () => import('../views/Users.vue') }
    ]
  }
]

const router = createRouter({ history: createWebHistory(), routes })

// 缓存安装状态，避免每次导航都请求
let configured = null

async function checkConfigured() {
  if (configured !== null) return configured
  try {
    const { data } = await axios.get('/api/setup/status')
    configured = !!data.configured
  } catch {
    configured = false
  }
  return configured
}

router.beforeEach(async (to) => {
  const isConfigured = await checkConfigured()

  // 未配置数据库：强制进入安装向导
  if (!isConfigured) {
    return to.meta.setup ? true : '/setup'
  }
  // 已配置：不再允许访问安装向导
  if (to.meta.setup) return '/login'

  // 登录态校验
  const loggedIn = !!localStorage.getItem('access_token')
  if (!to.meta.guest && !loggedIn) return '/login'
  if (to.meta.guest && loggedIn) return '/dashboard'
})

export default router
