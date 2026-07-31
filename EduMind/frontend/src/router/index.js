import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/',          name: 'Login',      component: () => import('@/pages/LoginPage.vue') },
  { path: '/dashboard', name: 'Dashboard',  component: () => import('@/pages/DashboardPage.vue') },
  { path: '/profile',   name: 'Profile',    component: () => import('@/pages/ProfilePage.vue') },
  { path: '/assessment',name: 'Assessment', component: () => import('@/pages/AssessmentPage.vue') },
  { path: '/plan',      name: 'Plan',       component: () => import('@/pages/PlanPage.vue') },
  { path: '/chat',      name: 'Chat',       component: () => import('@/pages/ChatPage.vue') },
  { path: '/progress',  name: 'Progress',   component: () => import('@/pages/ProgressPage.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
