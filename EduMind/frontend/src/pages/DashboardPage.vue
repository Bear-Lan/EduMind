<template>
  <div class="layout-wrapper">
    <!-- Header -->
    <header class="app-header">
      <div class="logo">
        <span class="logo-icon">✨</span> EduMind
      </div>
      
      <SubjectSwitcher />
      
      <!-- Tab Switcher -->
      <div class="tab-switcher">
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'console' }"
          @click="activeTab = 'console'"
        >
          🧠 学习主控台
        </button>
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'assessment' }"
          @click="activeTab = 'assessment'"
        >
          📝 测评中心
        </button>
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'errorbook' }"
          @click="activeTab = 'errorbook'"
        >
          📕 错题本
        </button>
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'kmap' }"
          @click="activeTab = 'kmap'"
        >
          🕸️ 知识图谱
        </button>
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'progress' }"
          @click="activeTab = 'progress'"
        >
          📈 学习进度
        </button>
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'analytics' }"
          @click="activeTab = 'analytics'"
        >
          📊 数据分析
        </button>
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'magic' }"
          @click="activeTab = 'magic'"
        >
          ✨ Magic Notes
        </button>
      </div>

      <div class="header-actions">
        <EduButton variant="ghost" size="sm" @click="router.push('/account')">
          账户设置
        </EduButton>
        <div class="user-badge" v-if="authStore.user">
          学生 #{{ authStore.user.student_id }}
        </div>
        <EduButton variant="ghost" size="sm" @click="handleLogout">
          退出
        </EduButton>
      </div>
    </header>

    <!-- Main Content Area -->
    <main class="app-main">
      <div v-if="activeTab === 'console'" class="panel-container">
        <!-- 1. Profile / Assessment (Left Column) -->
        <div class="panel panel-left glass-panel">
          <div class="panel-header">
            <h2 class="panel-title">📊 学习画像</h2>
          </div>
          <div class="panel-body">
            <ProfilePage />
          </div>
        </div>

        <!-- 2. Learning Plan (Center Column) -->
        <div class="panel panel-center glass-panel">
          <div class="panel-header">
            <h2 class="panel-title">🎯 学习计划</h2>
          </div>
          <div class="panel-body">
            <PlanPage />
          </div>
        </div>

        <!-- 3. AI Chat (Right Column) -->
        <div class="panel panel-right glass-panel">
          <div class="panel-header">
            <h2 class="panel-title">💬 AI 教练</h2>
          </div>
          <div class="panel-body chat-container">
            <ChatPage />
          </div>
        </div>
      </div>
      
      <!-- Assessment View -->
      <div v-else-if="activeTab === 'assessment'" class="full-tab-container glass-panel">
        <AssessmentPage />
      </div>

      <!-- Error Book View -->
      <div v-else-if="activeTab === 'errorbook'" class="full-tab-container glass-panel">
        <ErrorBookPage />
      </div>

      <!-- Knowledge Map View -->
      <div v-else-if="activeTab === 'kmap'" class="full-tab-container glass-panel">
        <KnowledgeMapPage />
      </div>

      <!-- Progress View -->
      <div v-else-if="activeTab === 'progress'" class="full-tab-container glass-panel">
        <ProgressPage />
      </div>

      <!-- Analytics View -->
      <div v-else-if="activeTab === 'analytics'" class="analytics-container glass-panel">
        <AnalyticsPage />
      </div>

      <!-- Magic Notes View -->
      <div v-else-if="activeTab === 'magic'" class="full-tab-container glass-panel">
        <MagicNotesPage />
      </div>
    </main>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import EduButton from '../components/EduButton.vue';
import ProfilePage from './ProfilePage.vue';
import PlanPage from './PlanPage.vue';
import ChatPage from './ChatPage.vue';
import AnalyticsPage from './AnalyticsPage.vue';
import AssessmentPage from './AssessmentPage.vue';
import ProgressPage from './ProgressPage.vue';
import ErrorBookPage from './ErrorBookPage.vue';
import KnowledgeMapPage from './KnowledgeMapPage.vue';
import MagicNotesPage from './MagicNotesPage.vue';
import SubjectSwitcher from '../components/SubjectSwitcher.vue';

const router = useRouter();
const authStore = useAuthStore();
const activeTab = ref('console'); // 'console' | 'assessment' | 'progress' | 'analytics'

onMounted(() => {
  if (!authStore.isAuthenticated) {
    router.replace('/');
  }
});

function handleLogout() {
  authStore.logout();
  router.push('/');
}

</script>

<style scoped>
.layout-wrapper {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
  background-color: var(--bg-primary);
  background-image: 
    radial-gradient(circle at 15% 50%, rgba(99, 102, 241, 0.08) 0%, transparent 50%),
    radial-gradient(circle at 85% 30%, rgba(192, 132, 252, 0.08) 0%, transparent 50%);
}

.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 24px;
  background: rgba(8, 10, 22, 0.7);
  backdrop-filter: blur(14px);
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
  z-index: 100;
}

.logo {
  font-size: 20px;
  font-weight: 800;
  background: linear-gradient(to right, #818cf8, #c084fc);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  display: flex;
  align-items: center;
  gap: 8px;
}
.logo-icon {
  -webkit-text-fill-color: initial;
}

.tab-switcher {
  display: flex;
  background: rgba(0, 0, 0, 0.3);
  padding: 4px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.tab-btn {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  padding: 6px 16px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.tab-btn:hover {
  color: #fff;
}

.tab-btn.active {
  background: rgba(167, 139, 250, 0.15);
  color: #c4b5fd;
  box-shadow: 0 2px 8px rgba(0,0,0,0.2);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-badge {
  background: var(--accent-dim);
  border: 1px solid rgba(99,102,241,0.3);
  color: #a5b4fc;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
}

.app-main {
  flex: 1;
  padding: 16px 20px;
  overflow: hidden;
  display: flex;
}

.panel-container {
  display: flex;
  width: 100%;
  gap: 16px;
  height: 100%;
}

.analytics-container,
.full-tab-container {
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.panel {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-left {
  flex: 0 0 300px;
}

.panel-center {
  flex: 1;
  min-width: 400px;
}

.panel-right {
  flex: 0 0 380px;
}

.panel-header {
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
}

.panel-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.panel-body {
  flex: 1;
  overflow-y: auto;
  position: relative;
}

.chat-container {
  display: flex;
  flex-direction: column;
  padding: 0;
}

.config-section {
  margin-bottom: 24px;
}
.config-title {
  font-size: 12px;
  text-transform: uppercase;
  color: var(--text-secondary);
  letter-spacing: 1px;
  margin-bottom: 16px;
}
</style>
