<template>
  <div class="assessment-page">
    <!-- Loading State -->
    <div v-if="loading" class="loading-state">
      <span class="spin"></span>
      <span>加载测评数据中...</span>
    </div>

    <template v-else>
      <!-- Page Header -->
      <div class="page-header">
        <div class="header-left">
          <h2 class="page-title">📝 知识测评中心</h2>
          <p class="page-subtitle">点击任意知识点，发起 AI 智能出题测验</p>
        </div>
        <div class="header-stats">
          <div class="stat-pill" :class="masteredClass">
            <span class="stat-icon">🏆</span>
            <div>
              <div class="stat-num">{{ masteredCount }} / {{ totalCount }}</div>
              <div class="stat-txt">已掌握</div>
            </div>
          </div>
          <div class="stat-pill">
            <span class="stat-icon">📈</span>
            <div>
              <div class="stat-num">{{ avgScore }}%</div>
              <div class="stat-txt">综合掌握度</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Overall Progress Bar -->
      <div class="overall-bar-wrap">
        <div class="overall-bar-label">
          <span>综合进度</span>
          <span>{{ avgScore }}%</span>
        </div>
        <div class="overall-bar-track">
          <div
            class="overall-bar-fill"
            :style="{ width: avgScore + '%' }"
          ></div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-if="topicList.length === 0" class="empty-state">
        <div class="empty-icon">🎓</div>
        <h3>暂无课程大纲</h3>
        <p>请先在学习画像中选择科目，系统将自动加载知识点测评</p>
      </div>

      <!-- Topic Grid -->
      <div v-else class="topic-grid">
        <div
          v-for="topic in topicList"
          :key="topic.key"
          class="topic-card"
          :class="[`level-${topic.level}`, { 'is-active': activeTopic === topic.key }]"
          @click="startQuiz(topic)"
        >
          <!-- Level Badge -->
          <div class="level-badge" :class="`badge-${topic.level}`">
            {{ levelLabel[topic.level] }}
          </div>

          <!-- Circular Progress Ring -->
          <div class="ring-wrap">
            <svg class="ring-svg" viewBox="0 0 64 64">
              <circle class="ring-track" cx="32" cy="32" r="26" />
              <circle
                class="ring-fill"
                cx="32"
                cy="32"
                r="26"
                :stroke="topic.ringColor"
                :stroke-dasharray="`${topic.dash} 163.4`"
              />
            </svg>
            <div class="ring-label">
              <span class="ring-pct">{{ topic.percentage }}</span>
              <span class="ring-unit">%</span>
            </div>
          </div>

          <!-- Topic Info -->
          <div class="topic-info">
            <div class="topic-name">{{ topic.name }}</div>
            <div class="topic-status" :style="{ color: topic.color }">
              {{ topic.statusText }}
            </div>
          </div>

          <!-- Quiz Button Hint -->
          <div class="quiz-hint">
            <span>点击出题 ›</span>
          </div>
        </div>
      </div>
    </template>

    <!-- Assessment Modal (reused component) -->
    <AssessmentModal
      v-model="showModal"
      :topic="activeTopic"
      :topicName="activeTopicName"
      @completed="onQuizCompleted"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useLearningStore } from '../stores/learning';
import AssessmentModal from '../components/AssessmentModal.vue';

const learningStore = useLearningStore();
const loading = ref(true);
const showModal = ref(false);
const activeTopic = ref('');
const activeTopicName = ref('');

const levelLabel = {
  mastered: '已掌握',
  learning: '学习中',
  weak: '待加强',
  untouched: '未接触',
};

onMounted(async () => {
  loading.value = true;
  await learningStore.fetchProfile();
  loading.value = false;
});

const profile = computed(() => learningStore.profile);

const topicList = computed(() => {
  if (!profile.value) return [];

  const mm = profile.value.mastery_map || {};
  const prefs = profile.value.learning_preferences || {};
  const curricula = prefs.curricula || {};
  const currentSubj = profile.value.subject;

  if (!currentSubj || !curricula[currentSubj]) return [];

  const curriculum = curricula[currentSubj];
  const zhNames = curriculum.__zh_names__ || {};

  const list = [];
  for (const enKey in curriculum) {
    if (enKey === '__zh_names__') continue;

    const rawVal = mm[enKey] || 0;
    const percentage = Math.min(100, Math.round(rawVal * 100));
    const dash = Math.round((percentage / 100) * 163.4);

    // Determine level
    let level, color, ringColor, statusText;
    if (percentage >= 80) {
      level = 'mastered';
      color = '#10b981';
      ringColor = '#10b981';
      statusText = '已掌握 ✓';
    } else if (percentage >= 50) {
      level = 'learning';
      color = '#f59e0b';
      ringColor = '#f59e0b';
      statusText = '巩固中...';
    } else if (percentage > 0) {
      level = 'weak';
      color = '#ef4444';
      ringColor = '#ef4444';
      statusText = '需要加强';
    } else {
      level = 'untouched';
      color = '#6b7280';
      ringColor = '#6366f1';
      statusText = '尚未接触';
    }

    list.push({
      key: enKey,
      name: zhNames[enKey] || enKey,
      percentage,
      dash,
      level,
      color,
      ringColor,
      statusText,
    });
  }

  // Sort: weak first, then learning, then mastered, then untouched
  const order = { weak: 0, learning: 1, untouched: 2, mastered: 3 };
  return list.sort((a, b) => order[a.level] - order[b.level]);
});

const masteredCount = computed(() =>
  topicList.value.filter((t) => t.level === 'mastered').length
);
const totalCount = computed(() => topicList.value.length);
const avgScore = computed(() => {
  if (!topicList.value.length) return 0;
  const sum = topicList.value.reduce((acc, t) => acc + t.percentage, 0);
  return Math.round(sum / topicList.value.length);
});
const masteredClass = computed(() => {
  const ratio = masteredCount.value / Math.max(totalCount.value, 1);
  if (ratio >= 0.8) return 'pill-green';
  if (ratio >= 0.4) return 'pill-yellow';
  return 'pill-default';
});

function startQuiz(topic) {
  activeTopic.value = topic.key;
  activeTopicName.value = topic.name;
  showModal.value = true;
}

async function onQuizCompleted(score) {
  // After quiz, submit the score to assessment API and refresh profile
  try {
    const { default: api } = await import('../utils/api.js');
    await api.post('/assessment', {
      topic: activeTopic.value,
      score: score,
      duration: 300,
    });
    await learningStore.fetchProfile();
  } catch (err) {
    console.error('Failed to submit assessment score', err);
  }
}
</script>

<style scoped>
.assessment-page {
  height: 100%;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* ── Loading ── */
.loading-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--text-secondary);
  font-size: 15px;
}
.spin {
  display: inline-block;
  width: 20px;
  height: 20px;
  border: 2px solid var(--border-color);
  border-top-color: var(--accent-primary);
  border-radius: 50%;
  animation: spin 0.75s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ── Page Header ── */
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 16px;
}
.page-title {
  font-size: 20px;
  font-weight: 800;
  color: var(--text-primary);
  margin: 0 0 4px;
}
.page-subtitle {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 0;
}

.header-stats {
  display: flex;
  gap: 12px;
}
.stat-pill {
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 10px 16px;
}
.stat-icon {
  font-size: 22px;
}
.stat-num {
  font-size: 18px;
  font-weight: 800;
  color: var(--text-primary);
  line-height: 1;
}
.stat-txt {
  font-size: 11px;
  color: var(--text-secondary);
  margin-top: 3px;
}
.pill-green .stat-num { color: #10b981; }
.pill-yellow .stat-num { color: #f59e0b; }

/* ── Overall Progress Bar ── */
.overall-bar-wrap {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 16px 20px;
}
.overall-bar-label {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 10px;
}
.overall-bar-label span:last-child {
  font-weight: 700;
  color: var(--text-primary);
}
.overall-bar-track {
  height: 8px;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 4px;
  overflow: hidden;
}
.overall-bar-fill {
  height: 100%;
  border-radius: 4px;
  background: linear-gradient(90deg, #6366f1, #a78bfa, #10b981);
  transition: width 1.2s cubic-bezier(0.4, 0, 0.2, 1);
}

/* ── Empty State ── */
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  color: var(--text-secondary);
  gap: 10px;
}
.empty-icon { font-size: 52px; }
.empty-state h3 { color: var(--text-primary); font-size: 18px; }
.empty-state p { font-size: 14px; max-width: 300px; }

/* ── Topic Grid ── */
.topic-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 14px;
}

.topic-card {
  position: relative;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 20px 16px 16px;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  overflow: hidden;
}
.topic-card::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 16px;
  opacity: 0;
  transition: opacity 0.25s;
  background: radial-gradient(circle at center, rgba(99,102,241,0.1), transparent 70%);
}
.topic-card:hover {
  transform: translateY(-3px);
  border-color: rgba(99, 102, 241, 0.4);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}
.topic-card:hover::before { opacity: 1; }

/* Level-specific tints */
.topic-card.level-mastered { border-color: rgba(16, 185, 129, 0.2); }
.topic-card.level-mastered:hover { border-color: rgba(16, 185, 129, 0.5); }
.topic-card.level-weak { border-color: rgba(239, 68, 68, 0.2); }
.topic-card.level-weak:hover { border-color: rgba(239, 68, 68, 0.5); }
.topic-card.level-learning { border-color: rgba(245, 158, 11, 0.2); }
.topic-card.level-learning:hover { border-color: rgba(245, 158, 11, 0.5); }

/* Level Badge */
.level-badge {
  position: absolute;
  top: 10px;
  right: 10px;
  font-size: 10px;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 20px;
  letter-spacing: 0.5px;
}
.badge-mastered { background: rgba(16,185,129,0.15); color: #10b981; }
.badge-learning { background: rgba(245,158,11,0.15); color: #f59e0b; }
.badge-weak { background: rgba(239,68,68,0.15); color: #ef4444; }
.badge-untouched { background: rgba(99,102,241,0.12); color: #818cf8; }

/* Ring */
.ring-wrap {
  position: relative;
  width: 72px;
  height: 72px;
}
.ring-svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}
.ring-track {
  fill: none;
  stroke: rgba(255, 255, 255, 0.06);
  stroke-width: 6;
}
.ring-fill {
  fill: none;
  stroke-width: 6;
  stroke-linecap: round;
  transition: stroke-dasharray 1.2s cubic-bezier(0.4, 0, 0.2, 1);
}
.ring-label {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}
.ring-pct {
  font-size: 18px;
  font-weight: 800;
  color: var(--text-primary);
  line-height: 1;
}
.ring-unit {
  font-size: 11px;
  color: var(--text-secondary);
  align-self: flex-end;
  margin-bottom: 2px;
}

/* Topic Info */
.topic-info {
  text-align: center;
}
.topic-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.4;
  margin-bottom: 4px;
}
.topic-status {
  font-size: 11px;
  font-weight: 600;
}

/* Quiz Hint */
.quiz-hint {
  font-size: 11px;
  color: var(--text-secondary);
  opacity: 0;
  transform: translateY(4px);
  transition: all 0.2s ease;
}
.topic-card:hover .quiz-hint {
  opacity: 1;
  transform: translateY(0);
}
</style>
