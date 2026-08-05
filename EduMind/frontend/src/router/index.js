import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/',              name: 'Login',          component: () => import('@/pages/LoginPage.vue') },
  { path: '/dashboard',     name: 'Dashboard',      component: () => import('@/pages/DashboardPage.vue'), meta: { requiresStudent: true } },
  { path: '/profile',       name: 'Profile',        component: () => import('@/pages/ProfilePage.vue'), meta: { requiresStudent: true } },
  { path: '/account',       name: 'Account',        component: () => import('@/pages/AccountPage.vue'), meta: { requiresStudent: true } },
  { path: '/assessment',    name: 'Assessment',     component: () => import('@/pages/AssessmentPage.vue'), meta: { requiresStudent: true } },
  { path: '/plan',          name: 'Plan',           component: () => import('@/pages/PlanPage.vue'), meta: { requiresStudent: true } },
  { path: '/chat',          name: 'Chat',           component: () => import('@/pages/ChatPage.vue'), meta: { requiresStudent: true } },
  { path: '/progress',      name: 'Progress',       component: () => import('@/pages/ProgressPage.vue'), meta: { requiresStudent: true } },
  { path: '/error-book',    name: 'ErrorBook',      component: () => import('@/pages/ErrorBookPage.vue'), meta: { requiresStudent: true } },
  { path: '/knowledge-map', name: 'KnowledgeMap',   component: () => import('@/pages/KnowledgeMapPage.vue'), meta: { requiresStudent: true } },
  { path: '/admin-login',   name: 'AdminLogin',     component: () => import('@/pages/AdminLoginPage.vue'), meta: { public: true } },
  { path: '/admin',         name: 'AdminConsole',   component: () => import('@/pages/AdminPage.vue'), meta: { requiresAdmin: true } },
  { path: '/admin/users',   name: 'AdminUsers',     component: () => import('@/pages/AdminUsersPage.vue'), meta: { requiresAdmin: true } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const token = localStorage.getItem('em_token') || ''
  const role = localStorage.getItem('em_role') || ''
  if (to.meta.requiresAdmin && (!token || role !== 'admin')) return '/admin-login'
  if (to.meta.requiresStudent && (!token || role !== 'student')) return '/'
  if (!to.meta.public && to.name !== 'Login' && !to.meta.requiresAdmin && !token) return '/'
  if (to.name === 'Login' && token && role === 'admin') return '/admin'
  return true
})

export default router
