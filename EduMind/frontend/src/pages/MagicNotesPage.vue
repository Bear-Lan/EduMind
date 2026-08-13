<template>
  <div class="magic-notes">
    <div class="mn-header">
      <h2 class="mn-title">✨ Magic Notes — 笔记一键变刷题集</h2>
      <p class="mn-subtitle">粘贴课堂笔记或学习材料，AI 自动生成一套结构化测验题，可立即练习并自动批改。</p>
    </div>

    <!-- Step 1: Input notes -->
    <div class="mn-input-section" v-if="!quizSet.length">
      <textarea
        v-model="notes"
        class="mn-textarea"
        placeholder="在此粘贴你的课堂笔记、学习材料、知识点总结……"
        rows="12"
        :disabled="generating"
      ></textarea>
      <div class="mn-input-meta">
        <span class="mn-char-count">{{ notes.length }} 字符</span>
        <span v-if="notes.length < 20" class="mn-hint-warn">至少需要 20 个字符</span>
      </div>
      <div class="mn-actions">
        <EduButton variant="primary" :disabled="notes.trim().length < 20 || generating" :loading="generating" @click="generateQuiz">
          🪄 生成刷题集
        </EduButton>
        <EduButton variant="ghost" @click="notes = ''" :disabled="generating">清空</EduButton>
      </div>
      <p v-if="!hasApiKey" class="mn-warn">
        ⚠️ 当前未配置 API Key，Magic Notes 需要 AI 大脑支持。请联系管理员配置 LLM 密钥。
      </p>
    </div>

    <!-- Step 2: Quiz set generated -->
    <div v-if="quizSet.length" class="mn-quiz-section">
      <div class="mn-quiz-header">
        <div class="mn-quiz-stats">
          <span class="mn-badge">📚 {{ quizSet.length }} 道题</span>
          <span v-for="t in typeBreakdown" :key="t.label" class="mn-badge mn-badge-type">{{ t.icon }} {{ t.label }} ×{{ t.count }}</span>
          <span class="mn-badge mn-badge-subject">{{ subject }} · {{ grade }}</span>
        </div>
        <div class="mn-quiz-actions">
          <EduButton variant="ghost" size="sm" @click="resetAll" :disabled="practicing">🔄 重新生成</EduButton>
          <EduButton variant="primary" size="sm" @click="startPractice" :disabled="practicing">✏️ 开始练习</EduButton>
        </div>
      </div>

      <!-- Quiz list preview -->
      <div v-if="!practicing" class="mn-quiz-list">
        <div v-for="(q, i) in quizSet" :key="i" class="mn-quiz-card">
          <div class="mn-quiz-card-header">
            <span class="mn-quiz-num">{{ i + 1 }}</span>
            <span class="mn-quiz-type">{{ typeLabel(q.question_type) }}</span>
            <span class="mn-quiz-diff">难度 {{ q.difficulty }}/3</span>
          </div>
          <div class="mn-quiz-stem">{{ q.stem }}</div>
          <div v-if="q.options" class="mn-quiz-options">
            <div v-for="(opt, key) in q.options" :key="key" class="mn-quiz-opt">
              <span class="mn-opt-key">{{ key }}</span> {{ opt }}
            </div>
          </div>
        </div>
      </div>

      <!-- Practice mode -->
      <PracticeView
        v-if="practicing"
        :quizSet="quizSet"
        @done="onPracticeDone"
        @exit="resetAll"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import api from '../utils/api';
import EduButton from '../components/EduButton.vue';
import PracticeView from '../components/MagicNotesPractice.vue';

const notes = ref('');
const generating = ref(false);
const hasApiKey = ref(false);
const quizSet = ref([]);
const subject = ref('');
const grade = ref('');
const practicing = ref(false);

const TYPE_MAP = {
  single_choice: { label: '单选题', icon: '🔘' },
  multiple_choice: { label: '多选题', icon: '☑️' },
  true_false: { label: '判断题', icon: '✓✗' },
  fill_blank: { label: '填空题', icon: '✏️' },
  short_answer: { label: '简答题', icon: '📝' },
};

const typeLabel = (t) => TYPE_MAP[t]?.label || t;

const typeBreakdown = computed(() => {
  const counts = {};
  for (const q of quizSet.value) {
    const t = q.question_type;
    if (!counts[t]) counts[t] = 0;
    counts[t]++;
  }
  return Object.entries(counts).map(([t, c]) => ({
    label: TYPE_MAP[t]?.label || t,
    icon: TYPE_MAP[t]?.icon || '❓',
    count: c,
  }));
});

onMounted(async () => {
  try {
    const res = await api.get('/health');
    hasApiKey.value = res.data?.llm === 'ok';
  } catch (_) {}
});

async function generateQuiz() {
  generating.value = true;
  quizSet.value = [];
  try {
    const res = await api.post('/resources/notes-to-quiz', { notes: notes.value });
    const data = res.data;
    quizSet.value = data.questions || [];
    subject.value = data.subject || '';
    grade.value = data.grade || '';
    if (!quizSet.value.length) {
      alert(data.note || '生成失败，请检查 API Key 是否已配置');
    }
  } catch (err) {
    alert('生成失败: ' + (err.message || '网络错误'));
  } finally {
    generating.value = false;
  }
}

function startPractice() {
  practicing.value = true;
}

function onPracticeDone(result) {
  // result = { correct, total }
}

function resetAll() {
  quizSet.value = [];
  practicing.value = false;
}
</script>

<style scoped>
.magic-notes { max-width: 800px; margin: 0 auto; padding: 24px; }
.mn-header { text-align: center; margin-bottom: 28px; }
.mn-title { font-size: 22px; font-weight: 700; color: var(--text-primary); margin-bottom: 8px; }
.mn-subtitle { font-size: 14px; color: var(--text-secondary); line-height: 1.5; }
.mn-input-section { display: flex; flex-direction: column; gap: 12px; }
.mn-textarea {
  width: 100%; background: rgba(6, 8, 20, 0.9);
  border: 1px solid var(--border-color); border-radius: 12px;
  color: var(--text-primary); padding: 16px; font-size: 14px;
  font-family: inherit; line-height: 1.6; resize: vertical; outline: none;
  transition: border-color 0.2s; box-sizing: border-box;
}
.mn-textarea:focus { border-color: var(--accent-primary, #818cf8); }
.mn-input-meta { display: flex; justify-content: space-between; font-size: 12px; color: var(--text-tertiary, #64748b); }
.mn-hint-warn { color: var(--status-warning, #fbbf24); }
.mn-actions { display: flex; gap: 12px; }
.mn-warn { font-size: 13px; color: var(--status-warning, #fbbf24); padding: 10px 14px; background: rgba(251, 191, 36, 0.08); border-radius: 8px; border: 1px solid rgba(251, 191, 36, 0.2); }
.mn-quiz-section { display: flex; flex-direction: column; gap: 16px; }
.mn-quiz-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; padding-bottom: 12px; border-bottom: 1px solid var(--border-color); }
.mn-quiz-stats { display: flex; gap: 8px; flex-wrap: wrap; }
.mn-badge { font-size: 12px; font-weight: 600; padding: 4px 10px; border-radius: 999px; background: rgba(99, 102, 241, 0.12); border: 1px solid rgba(99, 102, 241, 0.25); color: var(--text-primary); }
.mn-badge-type { background: rgba(167, 139, 250, 0.1); border-color: rgba(167, 139, 250, 0.25); }
.mn-badge-subject { background: rgba(16, 185, 129, 0.1); border-color: rgba(16, 185, 129, 0.25); }
.mn-quiz-actions { display: flex; gap: 8px; }
.mn-quiz-list { display: flex; flex-direction: column; gap: 12px; }
.mn-quiz-card { background: rgba(255, 255, 255, 0.03); border: 1px solid var(--border-color); border-radius: 12px; padding: 16px; }
.mn-quiz-card-header { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.mn-quiz-num { width: 24px; height: 24px; border-radius: 50%; background: rgba(99, 102, 241, 0.2); color: var(--text-primary); font-size: 12px; font-weight: 700; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.mn-quiz-type { font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 6px; background: rgba(167, 139, 250, 0.15); color: #c4b5fd; }
.mn-quiz-diff { font-size: 11px; color: var(--text-tertiary, #64748b); margin-left: auto; }
.mn-quiz-stem { font-size: 14px; color: var(--text-primary); line-height: 1.6; margin-bottom: 10px; }
.mn-quiz-options { display: flex; flex-direction: column; gap: 6px; }
.mn-quiz-opt { font-size: 13px; color: var(--text-secondary); padding: 6px 10px; background: rgba(255, 255, 255, 0.02); border-radius: 6px; }
.mn-opt-key { font-weight: 700; color: var(--accent-primary, #818cf8); margin-right: 6px; }
</style>
