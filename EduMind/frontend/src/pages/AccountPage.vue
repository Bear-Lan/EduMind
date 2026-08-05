<template>
  <div class="account-page">
    <header class="account-header">
      <button class="back-link" @click="router.push('/dashboard')">← 返回学习中心</button>
      <div><strong>学生账户设置</strong><span>管理登录信息和个人资料</span></div>
      <EduButton variant="ghost" size="sm" @click="logout">退出登录</EduButton>
    </header>

    <main class="account-content">
      <div v-if="authStore.studentMustChangePassword" class="warning-banner">
        管理员刚刚重置了你的密码。为了账户安全，请立即设置只有你知道的新密码。
      </div>
      <div v-if="message" class="message" :class="messageType">{{ message }}</div>

      <section class="account-card">
        <div class="card-intro">
          <span class="eyebrow">BASIC INFORMATION</span>
          <h1>基本资料</h1>
          <p>用户名修改后，下次登录需要使用新用户名。</p>
        </div>
        <form class="form-grid" @submit.prevent="saveAccount">
          <EduInput v-model="account.username" label="用户名" required />
          <EduInput v-model="account.name" label="姓名或称呼" required />
          <EduInput v-model="account.grade" label="年级" placeholder="例如：初一" />
          <EduInput v-model="account.subject" label="主要学科" placeholder="例如：数学" />
          <EduInput v-model.number="account.target_score" type="number" min="0" max="100" label="目标分数" />
          <div class="submit-cell"><EduButton type="submit" :loading="saving">保存基本资料</EduButton></div>
        </form>
      </section>

      <section class="account-card password-card">
        <div class="card-intro">
          <span class="eyebrow">ACCOUNT SECURITY</span>
          <h2>修改登录密码</h2>
          <p>新密码至少8位，建议包含字母、数字和符号。</p>
        </div>
        <form class="password-form" @submit.prevent="changePassword">
          <EduInput v-model="password.current_password" type="password" label="当前密码" required />
          <EduInput v-model="password.new_password" type="password" label="新密码" required />
          <EduInput v-model="password.confirm_password" type="password" label="确认新密码" required />
          <EduButton type="submit" :loading="changingPassword">更新密码</EduButton>
        </form>
      </section>
    </main>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue';
import { useRouter } from 'vue-router';
import api from '../utils/api';
import { useAuthStore } from '../stores/auth';
import EduButton from '../components/EduButton.vue';
import EduInput from '../components/EduInput.vue';

const router = useRouter();
const authStore = useAuthStore();
const saving = ref(false);
const changingPassword = ref(false);
const message = ref('');
const messageType = ref('success');
const account = reactive({ username: '', name: '', grade: '', subject: '', target_score: null });
const password = reactive({ current_password: '', new_password: '', confirm_password: '' });

onMounted(loadAccount);

function showMessage(text, type = 'success') {
  message.value = text;
  messageType.value = type;
  window.setTimeout(() => { if (message.value === text) message.value = ''; }, 5000);
}

async function loadAccount() {
  try {
    const response = await api.get('/auth/account');
    Object.assign(account, response.data);
  } catch (error) {
    showMessage(error.message || '账户资料读取失败', 'error');
  }
}

async function saveAccount() {
  saving.value = true;
  try {
    const response = await api.put('/auth/account', account);
    Object.assign(account, response.data);
    showMessage('基本资料已保存');
  } catch (error) {
    showMessage(error.message || '基本资料保存失败', 'error');
  } finally {
    saving.value = false;
  }
}

async function changePassword() {
  if (password.new_password.length < 8) {
    showMessage('新密码至少需要8位', 'error');
    return;
  }
  if (password.new_password !== password.confirm_password) {
    showMessage('两次输入的新密码不一致', 'error');
    return;
  }
  changingPassword.value = true;
  try {
    await api.put('/auth/password', {
      current_password: password.current_password,
      new_password: password.new_password,
    });
    password.current_password = '';
    password.new_password = '';
    password.confirm_password = '';
    authStore.studentMustChangePassword = false;
    localStorage.setItem('em_student_pwd_change', '0');
    showMessage('密码修改成功，下次请使用新密码登录');
  } catch (error) {
    showMessage(error.message || '密码修改失败', 'error');
  } finally {
    changingPassword.value = false;
  }
}

function logout() {
  authStore.logout();
  router.push('/');
}
</script>

<style scoped>
.account-page { min-height: 100vh; background: #080a16; color: var(--text-primary); }
.account-header { min-height: 74px; padding: 12px 28px; display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; border-bottom: 1px solid var(--border-color); background: rgba(12,14,29,.9); }
.account-header > div { display: flex; flex-direction: column; align-items: center; gap: 4px; }
.account-header strong { color: white; font-size: 18px; }
.account-header span { color: var(--text-secondary); font-size: 12px; }
.account-header > :last-child { justify-self: end; }
.back-link { justify-self: start; border: 0; background: transparent; color: #a5b4fc; cursor: pointer; }
.account-content { width: min(980px, calc(100% - 36px)); margin: 0 auto; padding: 32px 0 60px; }
.warning-banner, .message { margin-bottom: 18px; border-radius: 12px; padding: 14px 17px; }
.warning-banner { color: #fde68a; background: rgba(245,158,11,.1); border: 1px solid rgba(245,158,11,.28); }
.message.success { color: #a7f3d0; background: rgba(16,185,129,.12); border: 1px solid rgba(16,185,129,.25); }
.message.error { color: #fecaca; background: rgba(239,68,68,.12); border: 1px solid rgba(239,68,68,.25); }
.account-card { padding: 24px; margin-bottom: 20px; border: 1px solid rgba(255,255,255,.08); border-radius: 16px; background: rgba(18,22,46,.72); display: grid; grid-template-columns: .7fr 1.3fr; gap: 34px; }
.card-intro h1, .card-intro h2 { color: white; margin: 6px 0 8px; font-size: 22px; }
.card-intro p { color: var(--text-secondary); font-size: 13px; line-height: 1.7; }
.eyebrow { color: #818cf8; font-size: 10px; letter-spacing: 1.2px; }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px 16px; }
.password-form { display: grid; gap: 12px; }
.submit-cell { display: flex; align-items: end; padding-bottom: 16px; }
.form-grid :deep(.edu-input-wrapper), .password-form :deep(.edu-input-wrapper) { margin-bottom: 0; }
@media (max-width: 760px) {
  .account-header { grid-template-columns: 1fr auto; }
  .account-header > div { display: none; }
  .account-card { grid-template-columns: 1fr; }
  .form-grid { grid-template-columns: 1fr; }
}
</style>
