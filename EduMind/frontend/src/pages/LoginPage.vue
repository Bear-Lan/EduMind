<template>
  <div class="login-page">
    <!-- Abstract background elements -->
    <div class="bg-shape shape-1"></div>
    <div class="bg-shape shape-2"></div>
    
    <div class="login-container">
      <div class="logo-area">
        <div class="logo-icon">✨</div>
        <h1 class="logo-text">EduMind</h1>
        <p class="logo-sub">AI-Powered Learning Coach</p>
      </div>

      <EduCard class="login-card" body-padding="32px">
        <div class="tabs">
          <div class="tab" :class="{ active: mode === 'login' }" @click="mode = 'login'">登录</div>
          <div class="tab" :class="{ active: mode === 'register' }" @click="mode = 'register'">注册新账号</div>
        </div>

        <form @submit.prevent="handleSubmit" class="login-form">
          <EduInput 
            v-model="form.username" 
            label="用户名" 
            placeholder="输入账号" 
            required 
          />
          <EduInput 
            v-model="form.password" 
            type="password" 
            label="密码" 
            placeholder="输入密码" 
            required 
          />

          <div v-if="mode === 'register'" class="register-extras">
            <EduInput v-model="form.name" label="姓名 (选填)" placeholder="你的称呼" />
            <div class="form-row">
              <EduInput v-model="form.grade" label="年级" placeholder="如: 初一" />
              <EduInput v-model="form.subject" label="学科" placeholder="如: 数学" />
            </div>
            <EduInput v-model.number="form.target_score" type="number" label="目标分数" placeholder="90" />
          </div>

          <div v-if="errorMessage" class="error-message">
            {{ errorMessage }}
          </div>

          <EduButton 
            type="submit" 
            full-width 
            size="lg" 
            :loading="loading"
            style="margin-top: 10px;"
          >
            {{ mode === 'login' ? '立即登录' : '创建账号并登录' }}
          </EduButton>
        </form>
        <button type="button" class="admin-entry" @click="router.push('/admin-login')">
          管理员入口
        </button>
      </EduCard>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import EduCard from '../components/EduCard.vue';
import EduInput from '../components/EduInput.vue';
import EduButton from '../components/EduButton.vue';

const router = useRouter();
const authStore = useAuthStore();

const mode = ref('login');
const loading = ref(false);
const errorMessage = ref('');

const form = reactive({
  username: '',
  password: '',
  name: '',
  grade: '初一',
  subject: '数学',
  target_score: 90
});

async function handleSubmit() {
  loading.value = true;
  errorMessage.value = '';
  
  try {
    if (mode.value === 'login') {
      await authStore.login(form.username, form.password);
    } else {
      await authStore.register({
        username: form.username,
        password: form.password,
        name: form.name || form.username,
        grade: form.grade,
        subject: form.subject,
        target_score: form.target_score
      });
    }
    router.push(authStore.studentMustChangePassword ? '/account' : '/dashboard');
  } catch (error) {
    errorMessage.value = error.message || '登录失败，请检查账号密码';
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.login-page {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--bg-primary);
  overflow: hidden;
}

/* Background shapes */
.bg-shape {
  position: absolute;
  border-radius: 50%;
  filter: blur(100px);
  z-index: 0;
  opacity: 0.4;
  animation: float 20s infinite alternate;
}
.shape-1 {
  width: 500px;
  height: 500px;
  background: var(--accent-primary);
  top: -100px;
  right: -100px;
}
.shape-2 {
  width: 400px;
  height: 400px;
  background: #c084fc;
  bottom: -50px;
  left: -150px;
  animation-delay: -5s;
}

@keyframes float {
  0% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(-30px, 50px) scale(1.1); }
  100% { transform: translate(20px, -30px) scale(0.9); }
}

.login-container {
  position: relative;
  z-index: 10;
  width: 100%;
  max-width: 420px;
  padding: 20px;
}

.logo-area {
  text-align: center;
  margin-bottom: 32px;
}
.logo-icon {
  font-size: 42px;
  margin-bottom: 8px;
}
.logo-text {
  font-size: 32px;
  font-weight: 800;
  background: linear-gradient(135deg, #818cf8, #c084fc);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  letter-spacing: 1px;
}
.logo-sub {
  color: var(--text-secondary);
  font-size: 14px;
  margin-top: 4px;
  letter-spacing: 0.5px;
}

.login-card {
  box-shadow: 0 24px 50px rgba(0,0,0,0.5);
  border: 1px solid rgba(255,255,255,0.1);
  background: rgba(18, 22, 46, 0.7);
}

.tabs {
  display: flex;
  border-bottom: 1px solid var(--border-color);
  margin-bottom: 24px;
}
.tab {
  flex: 1;
  text-align: center;
  padding: 12px;
  cursor: pointer;
  color: var(--text-secondary);
  font-weight: 600;
  font-size: 14px;
  transition: all var(--transition-fast);
  border-bottom: 2px solid transparent;
}
.tab.active {
  color: var(--accent-primary);
  border-bottom-color: var(--accent-primary);
}
.tab:hover:not(.active) {
  color: var(--text-primary);
}

.register-extras {
  animation: slideDown 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}
@keyframes slideDown {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}

.form-row {
  display: flex;
  gap: 12px;
}
.form-row > * {
  flex: 1;
}

.error-message {
  color: var(--status-danger);
  font-size: 13px;
  margin: 8px 0 16px;
  text-align: center;
  background: rgba(239, 68, 68, 0.1);
  padding: 8px;
  border-radius: var(--radius-sm);
}

.admin-entry {
  width: 100%;
  margin-top: 18px;
  padding-top: 14px;
  border: 0;
  border-top: 1px solid var(--border-color);
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 13px;
}
.admin-entry:hover { color: var(--accent-primary); }
</style>
