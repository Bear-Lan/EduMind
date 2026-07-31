<template>
  <div class="progress-page">
    <!-- Loading State -->
    <div v-if="loading" class="loading-state">
      <span class="spin"></span>
      <span>加载进度数据中...</span>
    </div>

    <template v-else>
      <!-- Page Header -->
      <div class="page-header">
        <div>
          <h2 class="page-title">📊 学习进度总览</h2>
          <p class="page-subtitle">全面追踪你的学习旅程与成长轨迹</p>
        </div>
        <button class="refresh-btn" @click="loadData" :disabled="loading">
          🔄 刷新
        </button>
      </div>

      <!-- KPI Cards -->
      <div class="kpi-grid">
        <div class="kpi-card kpi-blue">
          <div class="kpi-icon">🎯</div>
          <div class="kpi-body">
            <div class="kpi-val">{{ avgMastery }}%</div>
            <div class="kpi-label">综合掌握度</div>
          </div>
          <div class="kpi-bg-text">MASTERY</div>
        </div>

        <div class="kpi-card kpi-green">
          <div class="kpi-icon">✅</div>
          <div class="kpi-body">
            <div class="kpi-val">{{ completionsCount }}</div>
            <div class="kpi-label">累计完成步骤</div>
          </div>
          <div class="kpi-bg-text">STEPS</div>
        </div>

        <div class="kpi-card kpi-purple">
          <div class="kpi-icon">🏅</div>
          <div class="kpi-body">
            <div class="kpi-val">{{ masteredTopics }}</div>
            <div class="kpi-label">已掌握知识点</div>
          </div>
          <div class="kpi-bg-text">TOPICS</div>
        </div>

        <div class="kpi-card kpi-amber">
          <div class="kpi-icon">⚡</div>
          <div class="kpi-body">
            <div class="kpi-val">{{ pendingTopics }}</div>
            <div class="kpi-label">待突破知识点</div>
          </div>
          <div class="kpi-bg-text">PENDING</div>
        </div>
      </div>

      <!-- Main Content: Mastery Map + Target -->
      <div class="content-row">
        <!-- Mastery Map -->
        <div class="section-card mastery-section">
          <div class="section-header">
            <h3 class="section-title">📚 知识点掌握地图</h3>
            <div class="legend">
              <span class="legend-dot dot-green"></span>已掌握
              <span class="legend-dot dot-amber"></span>巩固中
              <span class="legend-dot dot-red"></span>待加强
              <span class="legend-dot dot-gray"></span>未接触
            </div>
          </div>

          <div v-if="topicMastery.length === 0" class="inner-empty">
            <p>暂无课程数据，请先在学习画像中选择科目</p>
          </div>

          <div v-else class="mastery-list">
            <div
              v-for="topic in topicMastery"
              :key="topic.key"
              class="mastery-row"
            >
              <div class="mastery-left">
                <span class="mastery-dot" :style="{ background: topic.dotColor }"></span>
                <span class="mastery-name">{{ topic.name }}</span>
              </div>
              <div class="mastery-right">
                <div class="mastery-bar-track">
                  <div
                    class="mastery-bar-fill"
                    :style="{ width: topic.percentage + '%', background: topic.barColor }"
                  ></div>
                </div>
                <span class="mastery-pct" :style="{ color: topic.dotColor }">
                  {{ topic.percentage }}%
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Goal & Current Plan Summary -->
        <div class="right-col">
          <!-- Current Goal -->
          <div class="section-card goal-card">
            <h3 class="section-title">🎯 当前学习目标</h3>
            <div class="goal-display">
              <div v-if="currentGoal" class="goal-text">{{ currentGoal }}</div>
              <div v-else class="no-goal">暂未设定目标，请生成学习计划</div>
            </div>
            <div v-if="currentTopic" class="current-topic-chip">
              <span class="chip-label">当前突破章节</span>
              <span class="chip-value">{{ currentTopicName }}</span>
            </div>
          </div>

          <!-- Progress Donut -->
          <div class="section-card donut-card">
            <h3 class="section-title">📈 总体完成率</h3>
            <div class="donut-wrap">
              <svg class="donut-svg" viewBox="0 0 120 120">
                <circle class="donut-track" cx="60" cy="60" r="50" />
                <circle
                  class="donut-fill"
                  cx="60"
                  cy="60"
                  r="50"
                  :stroke-dasharray="`${donutDash} 314.2`"
                />
              </svg>
              <div class="donut-center">
                <span class="donut-pct">{{ avgMastery }}</span>
                <span class="donut-unit">%</span>
              </div>
            </div>
            <div class="donut-legend">
              <div class="dleg-item">
                <span class="dleg-dot" style="background: #10b981;"></span>
                已掌握 ({{ masteredTopics }}个)
              </div>
              <div class="dleg-item">
                <span class="dleg-dot" style="background: #f59e0b;"></span>
                巩固中 ({{ learningTopics }}个)
              </div>
              <div class="dleg-item">
                <span class="dleg-dot" style="background: #ef4444;"></span>
                待加强 ({{ weakTopics }}个)
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Milestone Timeline -->
      <div class="section-card timeline-section">
        <h3 class="section-title">🗺️ 学习里程碑</h3>
        <div class="timeline">
          <div
            v-for="(milestone, idx) in milestones"
            :key="idx"
            class="milestone-item"
            :class="{ 'is-done': milestone.done, 'is-current': milestone.current }"
          >
            <div class="ms-icon">{{ milestone.icon }}</div>
            <div class="ms-line" v-if="idx < milestones.length - 1"></div>
            <div class="ms-label">{{ milestone.label }}</div>
            <div class="ms-status">{{ milestone.status }}</div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useLearningStore } from '../stores/learning';
import api from '../utils/api.js';

const learningStore = useLearningStore();
const loading = ref(true);
const progressData = ref(null);

onMounted(() => loadData());

async function loadData() {
  loading.value = true;
  try {
    await learningStore.fetchProfile();
    const res = await api.get('/learning/progress');
    progressData.value = res.data;
  } catch (err) {
    console.error('Failed to load progress data', err);
  } finally {
    loading.value = false;
  }
}

const profile = computed(() => learningStore.profile);
const completionsCount = computed(() => progressData.value?.completions_count ?? 0);
const currentGoal = computed(() => profile.value?.current_goal || '');
const currentTopic = computed(() => learningStore.plan?.target_topic || '');
const currentTopicName = computed(
  () => learningStore.topicsMap[currentTopic.value] || currentTopic.value
);

// Build topic mastery list from profile
const topicMastery = computed(() => {
  if (!profile.value) return [];
  const mm = profile.value.mastery_map || {};
  const prefs = profile.value.learning_preferences || {};
  const curricula = prefs.curricula || {};
  const subj = profile.value.subject;
  if (!subj || !curricula[subj]) return [];
  const curriculum = curricula[subj];
  const zhNames = curriculum.__zh_names__ || {};

  return Object.keys(curriculum)
    .filter((k) => k !== '__zh_names__')
    .map((k) => {
      const pct = Math.min(100, Math.round((mm[k] || 0) * 100));
      let dotColor, barColor;
      if (pct >= 80) { dotColor = '#10b981'; barColor = '#10b981'; }
      else if (pct >= 50) { dotColor = '#f59e0b'; barColor = '#f59e0b'; }
      else if (pct > 0) { dotColor = '#ef4444'; barColor = '#ef4444'; }
      else { dotColor = '#4b5563'; barColor = '#6366f1'; }
      return { key: k, name: zhNames[k] || k, percentage: pct, dotColor, barColor };
    })
    .sort((a, b) => b.percentage - a.percentage);
});

const avgMastery = computed(() => {
  if (!topicMastery.value.length) return 0;
  const sum = topicMastery.value.reduce((a, b) => a + b.percentage, 0);
  return Math.round(sum / topicMastery.value.length);
});

const masteredTopics = computed(() => topicMastery.value.filter((t) => t.percentage >= 80).length);
const learningTopics = computed(() => topicMastery.value.filter((t) => t.percentage >= 50 && t.percentage < 80).length);
const weakTopics = computed(() => topicMastery.value.filter((t) => t.percentage > 0 && t.percentage < 50).length);
const pendingTopics = computed(() => topicMastery.value.filter((t) => t.percentage < 80).length);

// Donut ring circumference = 2πr = 314.16
const donutDash = computed(() => Math.round((avgMastery.value / 100) * 314.2));

// Milestone logic
const milestones = computed(() => {
  const total = topicMastery.value.length;
  const mastered = masteredTopics.value;
  const ratio = total > 0 ? mastered / total : 0;

  return [
    {
      icon: '🌱',
      label: '开始学习',
      status: completionsCount.value > 0 ? '已完成' : '未开始',
      done: completionsCount.value > 0,
      current: false,
    },
    {
      icon: '📖',
      label: '完成首个知识点',
      status: mastered > 0 ? '已达成' : '进行中',
      done: mastered > 0,
      current: mastered === 0 && completionsCount.value > 0,
    },
    {
      icon: '⚡',
      label: '掌握 50% 知识点',
      status: ratio >= 0.5 ? '已达成' : `${Math.round(ratio * 100)}% 完成`,
      done: ratio >= 0.5,
      current: ratio > 0 && ratio < 0.5,
    },
    {
      icon: '🔥',
      label: '掌握 80% 知识点',
      status: ratio >= 0.8 ? '已达成' : `${Math.round(ratio * 100)}% 完成`,
      done: ratio >= 0.8,
      current: ratio >= 0.5 && ratio < 0.8,
    },
    {
      icon: '🏆',
      label: '全科目通关',
      status: ratio >= 1.0 ? '🎉 恭喜完成！' : '敬请期待',
      done: ratio >= 1.0,
      current: ratio >= 0.8 && ratio < 1.0,
    },
  ];
});
</script>

<style scoped>
.progress-page {
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
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Header ── */
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
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
.refresh-btn {
  background: rgba(99,102,241,0.12);
  border: 1px solid rgba(99,102,241,0.25);
  color: #818cf8;
  padding: 7px 14px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}
.refresh-btn:hover { background: rgba(99,102,241,0.2); }
.refresh-btn:disabled { opacity: 0.5; cursor: default; }

/* ── KPI Grid ── */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
}
.kpi-card {
  position: relative;
  overflow: hidden;
  border-radius: 16px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 14px;
  border: 1px solid var(--border-color);
}
.kpi-blue  { background: linear-gradient(135deg, rgba(99,102,241,0.12), rgba(99,102,241,0.04)); border-color: rgba(99,102,241,0.25); }
.kpi-green { background: linear-gradient(135deg, rgba(16,185,129,0.12), rgba(16,185,129,0.04)); border-color: rgba(16,185,129,0.25); }
.kpi-purple{ background: linear-gradient(135deg, rgba(167,139,250,0.12), rgba(167,139,250,0.04)); border-color: rgba(167,139,250,0.25); }
.kpi-amber { background: linear-gradient(135deg, rgba(245,158,11,0.12), rgba(245,158,11,0.04)); border-color: rgba(245,158,11,0.25); }

.kpi-icon { font-size: 28px; }
.kpi-val {
  font-size: 28px;
  font-weight: 900;
  color: var(--text-primary);
  line-height: 1;
}
.kpi-label { font-size: 12px; color: var(--text-secondary); margin-top: 4px; }
.kpi-bg-text {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 36px;
  font-weight: 900;
  opacity: 0.04;
  color: #fff;
  letter-spacing: -1px;
  user-select: none;
}

/* ── Content Row ── */
.content-row {
  display: flex;
  gap: 16px;
  min-height: 320px;
}
.mastery-section {
  flex: 1;
  min-width: 0;
}
.right-col {
  display: flex;
  flex-direction: column;
  gap: 14px;
  width: 260px;
  flex-shrink: 0;
}

/* ── Section Card ── */
.section-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 20px;
}
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 8px;
}
.section-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 16px;
}
.section-header .section-title { margin: 0; }

/* Legend */
.legend {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 11px;
  color: var(--text-secondary);
}
.legend-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 3px;
}
.dot-green  { background: #10b981; }
.dot-amber  { background: #f59e0b; }
.dot-red    { background: #ef4444; }
.dot-gray   { background: #4b5563; }

.inner-empty {
  text-align: center;
  padding: 40px 0;
  color: var(--text-secondary);
  font-size: 13px;
}

/* Mastery List */
.mastery-list { display: flex; flex-direction: column; gap: 12px; }
.mastery-row {
  display: flex;
  align-items: center;
  gap: 12px;
}
.mastery-left {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 140px;
  flex-shrink: 0;
}
.mastery-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.mastery-name {
  font-size: 13px;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.mastery-right {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10px;
}
.mastery-bar-track {
  flex: 1;
  height: 6px;
  background: rgba(255,255,255,0.06);
  border-radius: 3px;
  overflow: hidden;
}
.mastery-bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 1s cubic-bezier(0.4,0,0.2,1);
}
.mastery-pct {
  font-size: 12px;
  font-weight: 700;
  width: 36px;
  text-align: right;
}

/* ── Goal Card ── */
.goal-card .section-title { margin-bottom: 12px; }
.goal-display { margin-bottom: 12px; }
.goal-text {
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-primary);
  padding: 10px 12px;
  background: rgba(99,102,241,0.08);
  border-radius: 8px;
  border-left: 3px solid var(--accent-primary);
}
.no-goal {
  font-size: 13px;
  color: var(--text-secondary);
  font-style: italic;
}
.current-topic-chip {
  display: flex;
  flex-direction: column;
  gap: 2px;
  background: rgba(167,139,250,0.08);
  border: 1px solid rgba(167,139,250,0.2);
  border-radius: 8px;
  padding: 8px 12px;
}
.chip-label { font-size: 10px; color: #a78bfa; font-weight: 700; letter-spacing: 0.5px; }
.chip-value { font-size: 13px; color: var(--text-primary); font-weight: 600; }

/* ── Donut Card ── */
.donut-card .section-title { margin-bottom: 12px; }
.donut-wrap {
  position: relative;
  width: 120px;
  height: 120px;
  margin: 0 auto 16px;
}
.donut-svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}
.donut-track {
  fill: none;
  stroke: rgba(255,255,255,0.06);
  stroke-width: 10;
}
.donut-fill {
  fill: none;
  stroke: url(#grad);
  stroke: #6366f1;
  stroke-width: 10;
  stroke-linecap: round;
  transition: stroke-dasharray 1.2s cubic-bezier(0.4,0,0.2,1);
}
.donut-center {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}
.donut-pct {
  font-size: 28px;
  font-weight: 900;
  background: linear-gradient(135deg, #818cf8, #a78bfa);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.donut-unit {
  font-size: 13px;
  color: var(--text-secondary);
  align-self: flex-end;
  margin-bottom: 4px;
}
.donut-legend { display: flex; flex-direction: column; gap: 6px; }
.dleg-item { display: flex; align-items: center; gap: 8px; font-size: 12px; color: var(--text-secondary); }
.dleg-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }

/* ── Timeline Section ── */
.timeline-section .section-title { margin-bottom: 20px; }
.timeline {
  display: flex;
  align-items: flex-start;
  gap: 0;
  overflow-x: auto;
  padding-bottom: 8px;
}
.milestone-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 100px;
  position: relative;
}
.ms-icon {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: rgba(255,255,255,0.05);
  border: 2px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  transition: all 0.3s;
  position: relative;
  z-index: 1;
}
.milestone-item.is-done .ms-icon {
  background: rgba(16,185,129,0.15);
  border-color: #10b981;
  box-shadow: 0 0 14px rgba(16,185,129,0.25);
}
.milestone-item.is-current .ms-icon {
  background: rgba(99,102,241,0.15);
  border-color: var(--accent-primary);
  box-shadow: 0 0 14px rgba(99,102,241,0.3);
  animation: pulse 2s ease-in-out infinite;
}
@keyframes pulse {
  0%, 100% { box-shadow: 0 0 14px rgba(99,102,241,0.3); }
  50% { box-shadow: 0 0 24px rgba(99,102,241,0.6); }
}

.ms-line {
  position: absolute;
  top: 22px;
  left: calc(50% + 22px);
  right: calc(-50% + 22px);
  height: 2px;
  background: linear-gradient(90deg, var(--border-color), var(--border-color));
  z-index: 0;
}
.milestone-item.is-done .ms-line {
  background: linear-gradient(90deg, #10b981, rgba(16,185,129,0.3));
}

.ms-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  text-align: center;
}
.milestone-item.is-done .ms-label { color: var(--text-primary); }
.milestone-item.is-current .ms-label { color: #818cf8; }

.ms-status {
  font-size: 11px;
  color: var(--text-secondary);
  text-align: center;
}
.milestone-item.is-done .ms-status { color: #10b981; font-weight: 600; }
.milestone-item.is-current .ms-status { color: var(--accent-primary); }

/* Responsive */
@media (max-width: 1100px) {
  .kpi-grid { grid-template-columns: repeat(2, 1fr); }
  .content-row { flex-direction: column; }
  .right-col { width: 100%; flex-direction: row; }
  .goal-card, .donut-card { flex: 1; }
}
</style>
