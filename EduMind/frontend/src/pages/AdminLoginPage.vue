<template>
  <div class="admin-login-page">
    <div class="ambient ambient-a"></div>
    <div class="ambient ambient-b"></div>
    <div class="login-shell">
      <button class="back-link" @click="router.push('/')">← 返回学生登录</button>
      <div class="brand-mark">🛡️</div>
      <h1>EduMind 管理中心</h1>
      <p class="subtitle">仅限系统管理员登录</p>

      <EduCard class="login-card" body-padding="32px">
        <form @submit.prevent="submit">
          <EduInput v-model="form.username" label="管理员账号" placeholder="请输入管理员账号" required />
          <EduInput v-model="form.password" type="password" label="管理员密码" placeholder="请输入管理员密码" required />
          <div v-if="errorMessage" class="message error">{{ errorMessage }}</div>
          <EduButton type="submit" size="lg" full-width :loading="loading">进入管理中心</EduButton>
        </form>
      </EduCard>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import EduCard from '../components/EduCard.vue';
import EduInput from '../components/EduInput.vue';
import EduButton from '../components/EduButton.vue';

const router = useRouter();
const authStore = useAuthStore();
const loading = ref(false);
const errorMessage = ref('');
const form = reactive({ username: '', password: '' });

async function submit() {
  loading.value = true;
  errorMessage.value = '';
  try {
    await authStore.adminLogin(form.username.trim(), form.password);
    router.push('/admin');
  } catch (error) {
    errorMessage.value = error.message || '管理员登录失败';
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.admin-login-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  position: relative;
  overflow: hidden;
  background: #080a16;
}
.ambient { position: absolute; width: 420px; height: 420px; border-radius: 50%; filter: blur(110px); opacity: .24; }
.ambient-a { background: #6366f1; top: -170px; right: -100px; }
.ambient-b { background: #06b6d4; bottom: -190px; left: -100px; }
.login-shell { position: relative; z-index: 1; width: min(430px, calc(100% - 32px)); text-align: center; }
.back-link { display: block; border: 0; background: transparent; color: var(--text-secondary); cursor: pointer; margin-bottom: 26px; }
.back-link:hover { color: white; }
.brand-mark { font-size: 44px; margin-bottom: 10px; }
h1 { font-size: 30px; margin: 0; color: white; }
.subtitle { color: var(--text-secondary); margin: 8px 0 26px; }
.login-card { text-align: left; background: rgba(18, 22, 46, .78); border: 1px solid rgba(255,255,255,.1); }
.message { padding: 10px 12px; border-radius: 8px; margin-bottom: 16px; font-size: 13px; }
.error { color: #fca5a5; background: rgba(239,68,68,.12); }
</style>
