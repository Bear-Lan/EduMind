<template>
  <div class="error-book-page">
    <!-- Header -->
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">📕 错题本</h2>
        <p class="page-subtitle">所有答错的题目集中复盘，按知识点分组</p>
      </div>
      <div class="header-stats">
        <div class="stat-pill">
          <span class="stat-icon">📕</span>
          <div>
            <div class="stat-num">{{ items.length }}</div>
            <div class="stat-txt">错题数</div>
          </div>
        </div>
        <div class="stat-pill">
          <span class="stat-icon">🎯</span>
          <div>
            <div class="stat-num">{{ topics.length }}</div>
            <div class="stat-txt">涉及知识点</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading-state">
      <span class="spin"></span>
      <span>加载错题数据中…</span>
    </div>

    <!-- Empty -->
    <div v-else-if="items.length === 0" class="empty-state">
      <div class="empty-icon">🎉</div>
      <h3>暂无错题</h3>
      <p>继续保持！在测评中心多答几道题，错题会自动出现在这里</p>
    </div>

    <!-- Content -->
    <div v-else class="content-area">
      <!-- Filter Tabs -->
      <div class="filter-bar">
        <button
          v-for="t in ['all', ...topics]"
          :key="t"
          class="filter-tab"
          :class="{ active: activeTopic === t }"
          @click="activeTopic = t"
        >
          {{ t === 'all' ? '全部' : topicName(t) }}
          <span class="filter-count">{{ topicCount(t) }}</span>
        </button>
      </div>

      <!-- Items -->
      <div class="items-list">
        <div v-for="item in filteredItems" :key="item.attempt_id" class="error-item">
          <!-- Header Strip -->
          <div class="item-header">
            <div class="header-tags">
              <span class="topic-tag">📘 {{ topicName(item.topic) }}</span>
              <span class="diff-badge" :class="`diff-${item.difficulty}`">
                {{ '★'.repeat(item.difficulty) }}
              </span>
              <span class="type-tag">{{ typeLabel(item.question_type) }}</span>
            </div>
            <div class="header-time">{{ formatTime(item.created_at) }}</div>
          </div>

          <!-- Question Stem -->
          <div class="question-section">
            <div class="section-label">📝 题目</div>
            <div class="stem-text md-content" v-html="renderMarkdown(item.stem)"></div>
          </div>

          <!-- Choices (if any) -->
          <div v-if="item.options" class="choices-section">
            <div
              v-for="(text, key) in item.options"
              :key="key"
              class="choice-row"
              :class="getChoiceClass(item, key)"
            >
              <span class="choice-key">{{ key }}</span>
              <span class="choice-text">{{ text }}</span>
              <span v-if="isCorrectKey(item, key)" class="choice-mark correct">✓ 正确答案</span>
              <span v-else-if="isUserKey(item, key)" class="choice-mark wrong">✗ 你选的</span>
            </div>
          </div>

          <!-- User answer (text types) -->
          <div v-if="!item.options && (item.user_answer?.text || item.user_answer?.answer)" class="text-answer">
            <div class="section-label">✏️ 你的答案</div>
            <div class="answer-text wrong">{{ item.user_answer.text || item.user_answer.answer }}</div>
            <div class="section-label correct-label">✅ 参考答案</div>
            <div class="answer-text correct">
              {{ formatCorrect(item.correct_answer) }}
            </div>
          </div>

          <!-- Feedback -->
          <div v-if="item.feedback" class="feedback-section">
            <div class="section-label">🤖 AI 教练评语</div>
            <div class="feedback-text md-content" v-html="renderMarkdown(stripScore(item.feedback))"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import api from '../utils/api';
import { useLearningStore } from '../stores/learning';
import { renderMarkdown } from '../utils/markdown';

const learningStore = useLearningStore();

const loading = ref(true);
const items = ref([]);
const activeTopic = ref('all');

const topics = computed(() => {
  const set = new Set(items.value.map(i => i.topic));
  return [...set];
});

const filteredItems = computed(() => {
  if (activeTopic.value === 'all') return items.value;
  return items.value.filter(i => i.topic === activeTopic.value);
});

const topicName = (enKey) => {
  return learningStore.topicsMap[enKey] || enKey;
};

const topicCount = (topicKey) => {
  if (topicKey === 'all') return items.value.length;
  return items.value.filter(i => i.topic === topicKey).length;
};

const typeLabel = (type) => {
  return ({
    single_choice: '单选题',
    multiple_choice: '多选题',
    true_false: '判断题',
    fill_blank: '填空题',
    short_answer: '简答题',
  })[type] || type;
};

const formatTime = (iso) => {
  if (!iso) return '';
  const d = new Date(iso);
  return `${d.getMonth() + 1}-${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
};

const formatCorrect = (ca) => {
  if (!ca) return '';
  if (typeof ca === 'string') return ca;
  if (ca.answer) return ca.answer;
  if (ca.answers) return (ca.answers || []).join(', ');
  return JSON.stringify(ca);
};

const stripScore = (text) => {
  if (!text) return '';
  // 去掉末尾的"客观判分："行
  return text.split('\n---')[0].trim();
};

const isCorrectKey = (item, key) => {
  const ca = item.correct_answer || {};
  if (ca.answer === key) return true;
  if (Array.isArray(ca.answers) && ca.answers.includes(key)) return true;
  return false;
};

const isUserKey = (item, key) => {
  const ua = item.user_answer || {};
  if (ua.answer === key) return true;
  if (Array.isArray(ua.answers) && ua.answers.includes(key)) return true;
  return false;
};

const getChoiceClass = (item, key) => {
  if (isCorrectKey(item, key)) return 'choice-correct';
  if (isUserKey(item, key)) return 'choice-wrong';
  return '';
};

onMounted(async () => {
  loading.value = true;
  try {
    if (!learningStore.profile) {
      await learningStore.fetchProfile();
    }
    const res = await api.get('/assessment/error-book');
    items.value = res.data?.items || [];
  } catch (err) {
    console.error('Failed to load error book', err);
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.error-book-page {
  height: 100%;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.loading-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--text-secondary);
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

/* Header */
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
  margin: 0 0 4px;
  color: var(--text-primary);
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
.stat-icon { font-size: 22px; }
.stat-num { font-size: 18px; font-weight: 800; color: var(--text-primary); line-height: 1; }
.stat-txt { font-size: 11px; color: var(--text-secondary); margin-top: 3px; }

/* Empty */
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
.empty-state h3 { color: var(--text-primary); font-size: 18px; margin: 0; }
.empty-state p { font-size: 14px; max-width: 300px; margin: 0; }

/* Filter Bar */
.filter-bar {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.filter-tab {
  display: flex;
  align-items: center;
  gap: 6px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--border-color);
  border-radius: 20px;
  padding: 6px 14px;
  font-size: 13px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}
.filter-tab:hover {
  border-color: rgba(99, 102, 241, 0.4);
  color: var(--text-primary);
}
.filter-tab.active {
  background: rgba(99, 102, 241, 0.18);
  border-color: var(--accent-primary);
  color: var(--text-primary);
}
.filter-count {
  background: rgba(255, 255, 255, 0.1);
  font-size: 11px;
  padding: 1px 7px;
  border-radius: 10px;
  font-weight: 600;
}

/* Items */
.items-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.error-item {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border-color);
  border-radius: 14px;
  padding: 18px 20px;
  transition: all 0.2s;
}
.error-item:hover {
  border-color: rgba(239, 68, 68, 0.4);
  background: rgba(239, 68, 68, 0.04);
}

.item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}
.header-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.topic-tag {
  background: rgba(99, 102, 241, 0.15);
  color: #818cf8;
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 12px;
}
.diff-badge {
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 10px;
  font-weight: 600;
}
.diff-1, .diff-2 { background: rgba(16, 185, 129, 0.15); color: #10b981; }
.diff-3 { background: rgba(245, 158, 11, 0.15); color: #f59e0b; }
.diff-4, .diff-5 { background: rgba(239, 68, 68, 0.15); color: #ef4444; }
.type-tag {
  background: rgba(167, 139, 250, 0.15);
  color: #c4b5fd;
  font-size: 11px;
  padding: 3px 10px;
  border-radius: 12px;
  font-weight: 600;
}
.header-time {
  font-size: 11px;
  color: var(--text-secondary);
}

.section-label {
  font-size: 11px;
  color: var(--text-secondary);
  font-weight: 600;
  letter-spacing: 0.5px;
  margin-bottom: 6px;
  margin-top: 12px;
}
.section-label:first-child { margin-top: 0; }
.correct-label { color: #10b981; }

.question-section, .choices-section, .text-answer, .feedback-section {
  margin-top: 12px;
}
.stem-text {
  background: rgba(167, 139, 250, 0.05);
  border: 1px solid rgba(167, 139, 250, 0.2);
  padding: 12px 16px;
  border-radius: 8px;
  color: var(--text-primary);
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
}

.choices-section {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.choice-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  font-size: 13px;
  color: var(--text-primary);
}
.choice-key {
  font-weight: 700;
  color: var(--accent-primary);
  width: 22px;
  flex-shrink: 0;
}
.choice-text { flex: 1; }
.choice-mark {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 8px;
  white-space: nowrap;
}
.choice-mark.correct {
  background: rgba(16, 185, 129, 0.2);
  color: #10b981;
}
.choice-mark.wrong {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}
.choice-row.choice-correct {
  background: rgba(16, 185, 129, 0.08);
  border-color: rgba(16, 185, 129, 0.4);
}
.choice-row.choice-wrong {
  background: rgba(239, 68, 68, 0.08);
  border-color: rgba(239, 68, 68, 0.4);
}

.answer-text {
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 13px;
  font-family: 'Consolas', 'Monaco', monospace;
  white-space: pre-wrap;
}
.answer-text.wrong {
  background: rgba(239, 68, 68, 0.08);
  border-left: 3px solid #ef4444;
  color: var(--text-primary);
}
.answer-text.correct {
  background: rgba(16, 185, 129, 0.08);
  border-left: 3px solid #10b981;
  color: var(--text-primary);
}

.feedback-section {
  background: rgba(99, 102, 241, 0.06);
  border: 1px solid rgba(99, 102, 241, 0.2);
  border-radius: 8px;
  padding: 12px 16px;
}
.feedback-text {
  font-size: 13px;
  color: var(--text-primary);
  line-height: 1.6;
  white-space: pre-wrap;
}
</style>
