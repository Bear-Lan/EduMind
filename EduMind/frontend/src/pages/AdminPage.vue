<template>
  <div class="admin-page">
    <header class="admin-header">
      <div>
        <div class="brand">🛡️ EduMind 管理中心</div>
        <p>统一管理系统模型服务，学生端不再接触任何密钥</p>
      </div>
      <div class="header-actions">
        <EduButton variant="ghost" size="sm" @click="router.push('/admin/users')">用户管理</EduButton>
        <span class="admin-badge">系统管理员</span>
        <EduButton variant="ghost" size="sm" @click="logout">退出</EduButton>
      </div>
    </header>

    <main class="admin-content">
      <div v-if="authStore.mustChangePassword" class="security-banner">
        <div><strong>请尽快修改初始管理员密码</strong><br><span>初始密码只适合首次登录，修改后安全性更高。</span></div>
        <button @click="scrollToPassword">立即修改</button>
      </div>

      <div v-if="pageMessage" class="page-message" :class="messageType">{{ pageMessage }}</div>

      <section class="overview-grid">
        <div class="status-card">
          <span class="status-icon">💬</span>
          <div><small>对话模型</small><strong>{{ config.llm_model || '加载中…' }}</strong></div>
          <span class="pill" :class="config.llm_api_key_configured ? 'ok' : 'off'">
            {{ config.llm_api_key_configured ? '已配置' : '未配置' }}
          </span>
        </div>
        <div class="status-card">
          <span class="status-icon">🧭</span>
          <div><small>向量模型</small><strong>{{ config.embedding_model || '加载中…' }}</strong></div>
          <span class="pill" :class="config.embedding_api_key_configured ? 'ok' : 'off'">
            {{ config.embedding_api_key_configured ? '已配置' : '未配置' }}
          </span>
        </div>
      </section>

      <section class="config-grid" v-if="loaded">
        <div class="config-card">
          <div class="card-heading">
            <div><span class="eyebrow">LLM SERVICE</span><h2>AI 对话模型</h2></div>
            <span class="secret-state">{{ config.llm_api_key_masked }}</span>
          </div>
          <p class="card-note">负责AI教练、学习计划讲解和个性化辅导。</p>
          <EduInput v-model="form.llm_api_key" type="password" label="更新 API Key" placeholder="留空则保持现有密钥" hint="完整密钥不会从服务器返回" />
          <EduInput v-model="form.llm_base_url" label="API Base URL" placeholder="https://api.siliconflow.cn/v1" />
          <EduInput v-model="form.llm_model" label="模型名称" placeholder="Qwen/Qwen3.5-9B" />
          <div class="two-cols">
            <EduInput v-model.number="form.llm_max_tokens" type="number" label="最大输出 Tokens" />
            <EduInput v-model.number="form.llm_timeout_seconds" type="number" label="超时时间（秒）" />
          </div>
          <div class="two-cols">
            <EduInput v-model.number="form.llm_temperature" type="number" step="0.1" label="随机性 Temperature" />
            <label class="check-field"><input v-model="form.llm_enable_thinking" type="checkbox"> 启用深度思考</label>
          </div>
          <div class="card-actions">
            <EduButton variant="ghost" :loading="testing === 'llm'" @click="testConnection('llm')">测试连接</EduButton>
            <label class="danger-check"><input v-model="form.clear_llm_api_key" type="checkbox"> 清除现有Key</label>
          </div>
        </div>

        <div class="config-card">
          <div class="card-heading">
            <div><span class="eyebrow">EMBEDDING SERVICE</span><h2>知识库向量模型</h2></div>
            <span class="secret-state">{{ config.embedding_api_key_masked }}</span>
          </div>
          <p class="card-note">负责教材入库、语义检索和知识库资料召回。</p>
          <EduInput v-model="form.embedding_api_key" type="password" label="更新 API Key" placeholder="留空则保持现有密钥" hint="可与对话模型使用同一平台Key" />
          <EduInput v-model="form.embedding_base_url" label="API Base URL" placeholder="https://api.siliconflow.cn/v1" />
          <EduInput v-model="form.embedding_model" label="模型名称" placeholder="BAAI/bge-m3" />
          <EduInput v-model.number="form.embedding_dimensions" type="number" label="向量维度" hint="修改模型或维度后，需要重新构建向量库" />
          <div class="warning-box">⚠️ 当前向量库按照固定维度创建。更换向量模型前请先测试维度，否则知识库检索会失败。</div>
          <div class="card-actions">
            <EduButton variant="ghost" :loading="testing === 'embedding'" @click="testConnection('embedding')">测试连接</EduButton>
            <label class="danger-check"><input v-model="form.clear_embedding_api_key" type="checkbox"> 清除现有Key</label>
          </div>
        </div>
      </section>

      <div class="save-bar" v-if="loaded">
        <div><strong>所有密钥均在后端加密保存</strong><span>学生浏览器无法查看或覆盖系统Key。</span></div>
        <EduButton size="lg" :loading="saving" @click="saveConfig">保存全部配置</EduButton>
      </div>

      <section ref="passwordSection" class="password-card">
        <div><span class="eyebrow">ACCOUNT SECURITY</span><h2>修改管理员密码</h2><p>新密码至少12位，建议同时包含大小写字母、数字和符号。</p></div>
        <form class="password-form" @submit.prevent="changePassword">
          <EduInput v-model="passwordForm.current_password" type="password" label="当前密码" required />
          <EduInput v-model="passwordForm.new_password" type="password" label="新密码" required />
          <EduInput v-model="passwordForm.confirm_password" type="password" label="确认新密码" required />
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
const loaded = ref(false);
const saving = ref(false);
const testing = ref('');
const changingPassword = ref(false);
const pageMessage = ref('');
const messageType = ref('success');
const passwordSection = ref(null);
const config = reactive({});
const form = reactive({
  llm_api_key: '', clear_llm_api_key: false, llm_base_url: '', llm_model: '', llm_max_tokens: 4096,
  llm_temperature: 0.3, llm_enable_thinking: false, llm_timeout_seconds: 60,
  embedding_api_key: '', clear_embedding_api_key: false, embedding_base_url: '', embedding_model: '', embedding_dimensions: 1024,
});
const passwordForm = reactive({ current_password: '', new_password: '', confirm_password: '' });

onMounted(loadConfig);

function showMessage(message, type = 'success') {
  pageMessage.value = message;
  messageType.value = type;
  window.setTimeout(() => { if (pageMessage.value === message) pageMessage.value = ''; }, 5000);
}

function applyConfig(data) {
  Object.assign(config, data);
  Object.assign(form, {
    llm_api_key: '', clear_llm_api_key: false,
    llm_base_url: data.llm_base_url, llm_model: data.llm_model,
    llm_max_tokens: data.llm_max_tokens, llm_temperature: data.llm_temperature,
    llm_enable_thinking: data.llm_enable_thinking, llm_timeout_seconds: data.llm_timeout_seconds,
    embedding_api_key: '', clear_embedding_api_key: false,
    embedding_base_url: data.embedding_base_url, embedding_model: data.embedding_model,
    embedding_dimensions: data.embedding_dimensions,
  });
}

async function loadConfig() {
  try {
    const response = await api.get('/admin/config');
    applyConfig(response.data);
    loaded.value = true;
  } catch (error) {
    showMessage(error.message || '无法读取管理员配置', 'error');
  }
}

async function saveConfig() {
  saving.value = true;
  try {
    const response = await api.put('/admin/config', form);
    applyConfig(response.data);
    showMessage('模型配置已经安全保存并立即生效');
  } catch (error) {
    showMessage(error.message || '保存失败', 'error');
  } finally {
    saving.value = false;
  }
}

async function testConnection(service) {
  testing.value = service;
  try {
    const payload = service === 'llm'
      ? { service, api_key: form.llm_api_key || null, base_url: form.llm_base_url, model: form.llm_model }
      : { service, api_key: form.embedding_api_key || null, base_url: form.embedding_base_url, model: form.embedding_model, embedding_dimensions: Number(form.embedding_dimensions) };
    const response = await api.post('/admin/config/test', payload);
    showMessage(response.data.detail);
  } catch (error) {
    showMessage(error.message || '连接测试失败', 'error');
  } finally {
    testing.value = '';
  }
}

async function changePassword() {
  if (passwordForm.new_password !== passwordForm.confirm_password) {
    showMessage('两次输入的新密码不一致', 'error');
    return;
  }
  changingPassword.value = true;
  try {
    await api.put('/admin/password', {
      current_password: passwordForm.current_password,
      new_password: passwordForm.new_password,
    });
    passwordForm.current_password = '';
    passwordForm.new_password = '';
    passwordForm.confirm_password = '';
    authStore.mustChangePassword = false;
    localStorage.setItem('em_admin_pwd_change', '0');
    showMessage('管理员密码已更新');
  } catch (error) {
    showMessage(error.message || '密码修改失败', 'error');
  } finally {
    changingPassword.value = false;
  }
}

function scrollToPassword() { passwordSection.value?.scrollIntoView({ behavior: 'smooth' }); }
function logout() { authStore.logout(); router.push('/admin-login'); }
</script>

<style scoped>
.admin-page { min-height: 100vh; background: #080a16; color: var(--text-primary); }
.admin-header { min-height: 76px; padding: 14px 32px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid var(--border-color); background: rgba(12,14,29,.88); position: sticky; top: 0; z-index: 5; backdrop-filter: blur(16px); }
.brand { color: white; font-size: 20px; font-weight: 800; }
.admin-header p { margin: 5px 0 0; color: var(--text-secondary); font-size: 12px; }
.header-actions { display: flex; align-items: center; gap: 12px; }
.admin-badge { color: #a7f3d0; background: rgba(16,185,129,.12); border: 1px solid rgba(16,185,129,.25); padding: 6px 10px; border-radius: 999px; font-size: 12px; }
.admin-content { width: min(1180px, calc(100% - 40px)); margin: 0 auto; padding: 30px 0 56px; }
.security-banner, .page-message { border-radius: 12px; padding: 14px 18px; margin-bottom: 18px; }
.security-banner { display: flex; justify-content: space-between; align-items: center; background: rgba(245,158,11,.1); border: 1px solid rgba(245,158,11,.28); color: #fde68a; }
.security-banner span { font-size: 12px; opacity: .8; }
.security-banner button { border: 0; border-radius: 8px; padding: 8px 12px; background: #f59e0b; color: #1f1300; font-weight: 700; cursor: pointer; }
.page-message.success { background: rgba(16,185,129,.12); border: 1px solid rgba(16,185,129,.25); color: #a7f3d0; }
.page-message.error { background: rgba(239,68,68,.12); border: 1px solid rgba(239,68,68,.25); color: #fecaca; }
.overview-grid, .config-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; }
.overview-grid { margin-bottom: 18px; }
.status-card, .config-card, .password-card { background: rgba(18,22,46,.72); border: 1px solid rgba(255,255,255,.08); border-radius: 16px; }
.status-card { display: flex; align-items: center; gap: 14px; padding: 16px 18px; }
.status-icon { font-size: 26px; }
.status-card div { display: flex; flex-direction: column; gap: 4px; min-width: 0; flex: 1; }
.status-card small, .eyebrow { color: var(--text-secondary); font-size: 10px; letter-spacing: 1.2px; }
.status-card strong { color: white; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.pill { font-size: 11px; padding: 5px 9px; border-radius: 999px; }
.pill.ok { color: #a7f3d0; background: rgba(16,185,129,.13); }
.pill.off { color: #fecaca; background: rgba(239,68,68,.13); }
.config-card { padding: 22px; }
.card-heading { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; }
h2 { margin: 5px 0 0; color: white; font-size: 20px; }
.secret-state { font-family: ui-monospace, monospace; font-size: 12px; color: #a5b4fc; background: rgba(99,102,241,.12); padding: 7px 9px; border-radius: 8px; }
.card-note, .password-card p { color: var(--text-secondary); font-size: 13px; margin: 8px 0 22px; }
.two-cols { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.check-field { height: 43px; margin-top: 18px; display: flex; align-items: center; gap: 8px; color: var(--text-secondary); font-size: 13px; }
.warning-box { color: #fde68a; background: rgba(245,158,11,.08); border: 1px solid rgba(245,158,11,.2); padding: 11px; border-radius: 9px; font-size: 12px; margin: 2px 0 18px; }
.card-actions { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-top: 4px; }
.danger-check { color: #fca5a5; font-size: 12px; }
.save-bar { margin: 18px 0; padding: 16px 20px; display: flex; align-items: center; justify-content: space-between; gap: 20px; background: linear-gradient(120deg, rgba(99,102,241,.16), rgba(6,182,212,.08)); border: 1px solid rgba(129,140,248,.25); border-radius: 14px; }
.save-bar div { display: flex; flex-direction: column; gap: 4px; }
.save-bar span { color: var(--text-secondary); font-size: 12px; }
.password-card { margin-top: 22px; padding: 22px; display: grid; grid-template-columns: .8fr 1.2fr; gap: 32px; }
.password-form { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; align-items: end; }
.password-form :deep(.edu-input-wrapper) { margin-bottom: 0; }
@media (max-width: 850px) {
  .config-grid, .overview-grid, .password-card { grid-template-columns: 1fr; }
  .password-form { grid-template-columns: 1fr; }
  .admin-header { padding: 14px 18px; }
  .admin-header p, .admin-badge { display: none; }
}
</style>
