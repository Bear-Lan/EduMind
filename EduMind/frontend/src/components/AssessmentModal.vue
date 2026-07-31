<template>
  <div v-if="modelValue" class="modal-overlay">
    <div class="modal-content glass-panel" @click.stop>
      <div class="modal-header">
        <h3 class="modal-title">
          📝 随堂测验：{{ topicName }}
          <span class="diff-badge" :class="`diff-${difficulty}`">{{ difficultyLabel }}</span>
        </h3>
        <button
          class="close-btn"
          @click="closeModal"
          v-if="state !== 'grading'"
        >✕</button>
      </div>

      <div class="modal-body">
        <!-- Loading -->
        <div v-if="state === 'generating'" class="state-container">
          <span class="spin big"></span>
          <p>正在从题库为你抽取专属考题…</p>
        </div>

        <!-- Answering -->
        <div v-else-if="state === 'answering'" class="state-container answering-state">
          <div class="question-box md-content" v-html="renderMarkdown(question.stem)"></div>

          <!-- Single choice / True-False -->
          <div
            v-if="question.question_type === 'single_choice' || question.question_type === 'true_false'"
            class="choice-list"
          >
            <label
              v-for="(text, key) in question.options"
              :key="key"
              class="choice-item"
              :class="{ selected: userAnswer.answer === key }"
            >
              <input
                type="radio"
                :value="key"
                v-model="userAnswer.answer"
                class="choice-radio"
              />
              <span class="choice-key">{{ key }}</span>
              <span class="choice-text">{{ text }}</span>
            </label>
          </div>

          <!-- Multiple choice -->
          <div v-else-if="question.question_type === 'multiple_choice'" class="choice-list">
            <div class="hint-tip">💡 多选题：错选不得分，漏选按比例给分</div>
            <label
              v-for="(text, key) in question.options"
              :key="key"
              class="choice-item"
              :class="{ selected: (userAnswer.answers || []).includes(key) }"
            >
              <input
                type="checkbox"
                :value="key"
                v-model="userAnswer.answers"
                class="choice-radio"
              />
              <span class="choice-key">{{ key }}</span>
              <span class="choice-text">{{ text }}</span>
            </label>
          </div>

          <!-- Fill blank -->
          <div v-else-if="question.question_type === 'fill_blank'" class="fill-section">
            <label class="answer-label">你的答案：</label>
            <input
              v-model="userAnswer.text"
              type="text"
              class="fill-input"
              placeholder="请输入答案…"
            />
          </div>

          <!-- Short answer -->
          <div v-else-if="question.question_type === 'short_answer'" class="answer-section">
            <label class="answer-label">你的解答：</label>
            <textarea
              v-model="userAnswer.text"
              class="answer-input"
              placeholder="请输入你的解题思路或最终答案…"
              rows="6"
            ></textarea>
          </div>
        </div>

        <!-- Grading -->
        <div v-else-if="state === 'grading'" class="state-container">
          <span class="spin big"></span>
          <p>正在客观判分中…</p>
        </div>

        <!-- Result -->
        <div v-else-if="state === 'result'" class="state-container result-state">
          <div class="score-display">
            <div class="score-circle" :class="scoreClass">
              <span class="score-value">{{ Math.round(gradeResult.score * 100) }}</span>
              <span class="score-unit">分</span>
            </div>
            <div class="result-tag" :class="scoreClass">
              {{ scoreTagText }}
            </div>
          </div>

          <!-- 客观判分说明 -->
          <div class="objective-detail">
            <strong>客观判分：</strong>{{ gradeResult.details }}
          </div>

          <!-- 正确答案（仅答错时显示） -->
          <div v-if="!gradeResult.is_correct" class="correct-answer-box">
            <strong>✅ 参考答案：</strong>
            <pre>{{ formatCorrectAnswer(gradeResult.correct_answer) }}</pre>
          </div>

          <!-- 反馈（AI 评语） -->
          <div class="feedback-box md-content" v-html="renderMarkdown(gradeResult.feedback)"></div>
        </div>
      </div>

      <div class="modal-footer">
        <template v-if="state === 'answering'">
          <EduButton variant="ghost" @click="closeModal">稍后再测</EduButton>
          <EduButton
            variant="primary"
            :disabled="!canSubmit"
            @click="submitAnswer"
          >提交阅卷</EduButton>
        </template>
        <template v-else-if="state === 'result'">
          <EduButton full-width variant="success" @click="finishAssessment">完成学习打卡 ✓</EduButton>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed, reactive } from 'vue';
import { marked } from 'marked';
import api from '../utils/api';
import EduButton from './EduButton.vue';

const props = defineProps({
  modelValue: Boolean,
  topic: String,
  topicName: String,
});

const emit = defineEmits(['update:modelValue', 'completed']);

const state = ref('generating'); // generating | answering | grading | result
const question = ref(null);
const userAnswer = reactive({});
const gradeResult = ref({ score: 0, is_correct: false, details: '', correct_answer: null });
const difficulty = ref(1);

const difficultyLabel = computed(() => '★'.repeat(difficulty.value));

watch(() => props.modelValue, async (newVal) => {
  if (newVal) {
    resetState();
    await generateQuestion();
  }
});

function resetState() {
  state.value = 'generating';
  question.value = null;
  gradeResult.value = { score: 0, is_correct: false, details: '', correct_answer: null };
  Object.keys(userAnswer).forEach(k => delete userAnswer[k]);
}

async function generateQuestion() {
  try {
    const res = await api.get(`/assessment/quiz?topic=${encodeURIComponent(props.topic)}`);
    if (!res.data.success) {
      alert(res.data.message || '抽题失败');
      closeModal();
      return;
    }
    question.value = res.data.data;
    difficulty.value = question.value.difficulty;

    // 初始化答案结构
    if (question.value.question_type === 'multiple_choice') {
      userAnswer.answers = [];
    } else if (question.value.question_type === 'fill_blank' || question.value.question_type === 'short_answer') {
      userAnswer.text = '';
    } else {
      userAnswer.answer = '';
    }

    state.value = 'answering';
  } catch (err) {
    console.error('Failed to fetch quiz', err);
    alert('出题失败：' + (err?.response?.data?.message || err.message));
    closeModal();
  }
}

const canSubmit = computed(() => {
  if (!question.value) return false;
  if (question.value.question_type === 'multiple_choice') {
    return (userAnswer.answers || []).length > 0;
  }
  if (question.value.question_type === 'fill_blank' || question.value.question_type === 'short_answer') {
    return (userAnswer.text || '').trim().length > 0;
  }
  return !!userAnswer.answer;
});

async function submitAnswer() {
  if (!canSubmit.value) return;
  state.value = 'grading';

  try {
    const payload = {
      question_id: question.value.question_id,
      user_answer: { ...userAnswer },
      duration: 60,
    };
    const res = await api.post('/assessment/submit', payload);
    if (!res.data.success) {
      alert(res.data.message || '判分失败');
      state.value = 'answering';
      return;
    }
    gradeResult.value = res.data.data;
    state.value = 'result';
  } catch (err) {
    console.error('Failed to submit', err);
    alert('判分失败：' + (err?.response?.data?.message || err.message));
    state.value = 'answering';
  }
}

function finishAssessment() {
  emit('completed', gradeResult.value.score);
  closeModal();
}

function closeModal() {
  emit('update:modelValue', false);
}

function renderMarkdown(text) {
  return marked.parse(text || '');
}

const scoreClass = computed(() => {
  const s = gradeResult.value.score || 0;
  if (s >= 0.8) return 'score-excellent';
  if (s >= 0.6) return 'score-good';
  return 'score-needs-work';
});

const scoreTagText = computed(() => {
  if (gradeResult.value.is_correct) return '🎉 回答正确';
  const s = gradeResult.value.score || 0;
  if (s >= 0.7) return '接近正确';
  if (s >= 0.4) return '部分正确';
  return '需要加强';
});

function formatCorrectAnswer(ans) {
  if (!ans) return '';
  if (typeof ans === 'string') return ans;
  if (ans.answer) return ans.answer;
  if (ans.answers) return (ans.answers || []).join(', ');
  return JSON.stringify(ans);
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.modal-content {
  width: 100%;
  max-width: 640px;
  background: rgba(15, 17, 33, 0.96);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  display: flex;
  flex-direction: column;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.6);
  max-height: 90vh;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-color);
}

.modal-title {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 10px;
}

.diff-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 600;
}
.diff-1, .diff-2 { background: rgba(16, 185, 129, 0.15); color: #10b981; }
.diff-3 { background: rgba(245, 158, 11, 0.15); color: #f59e0b; }
.diff-4, .diff-5 { background: rgba(239, 68, 68, 0.15); color: #ef4444; }

.close-btn {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  font-size: 20px;
  cursor: pointer;
  padding: 4px;
}
.close-btn:hover { color: var(--text-primary); }

.modal-body {
  padding: 24px;
  min-height: 280px;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.state-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
  color: var(--text-secondary);
}

.answering-state {
  justify-content: flex-start;
  text-align: left;
  align-items: stretch;
}

.question-box {
  background: rgba(167, 139, 250, 0.05);
  border: 1px solid rgba(167, 139, 250, 0.2);
  padding: 16px;
  border-radius: var(--radius-md);
  margin-bottom: 20px;
  color: var(--text-primary);
  font-size: 15px;
  line-height: 1.6;
}

.hint-tip {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 10px;
  padding: 6px 10px;
  background: rgba(99, 102, 241, 0.1);
  border-radius: 6px;
}

.choice-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.choice-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s;
}
.choice-item:hover {
  background: rgba(99, 102, 241, 0.08);
  border-color: rgba(99, 102, 241, 0.3);
}
.choice-item.selected {
  background: rgba(99, 102, 241, 0.15);
  border-color: var(--accent-primary);
}

.choice-radio {
  accent-color: var(--accent-primary);
  cursor: pointer;
}

.choice-key {
  font-weight: 700;
  color: var(--accent-primary);
  width: 20px;
  text-align: center;
}

.choice-text {
  flex: 1;
  color: var(--text-primary);
  font-size: 14px;
}

.fill-section, .answer-section {
  display: flex;
  flex-direction: column;
}

.answer-label {
  display: block;
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--text-primary);
}

.fill-input, .answer-input {
  width: 100%;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 12px;
  color: var(--text-primary);
  font-size: 14px;
  line-height: 1.6;
  outline: none;
  transition: border-color var(--transition-fast);
}
.answer-input {
  resize: vertical;
  font-family: inherit;
}
.fill-input:focus, .answer-input:focus {
  border-color: var(--accent-primary);
}

.result-state {
  justify-content: flex-start;
  align-items: stretch;
}

.score-display {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.score-circle {
  width: 110px;
  height: 110px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  background: rgba(0, 0, 0, 0.2);
  border: 4px solid var(--border-color);
}

.score-excellent { border-color: var(--status-success); color: var(--status-success); box-shadow: 0 0 20px rgba(16, 185, 129, 0.3); }
.score-good { border-color: var(--status-warning); color: var(--status-warning); }
.score-needs-work { border-color: var(--status-danger); color: var(--status-danger); }

.score-value {
  font-size: 38px;
  font-weight: 800;
  line-height: 1;
}
.score-unit {
  font-size: 13px;
  font-weight: 600;
  opacity: 0.8;
}

.result-tag {
  padding: 4px 16px;
  border-radius: 16px;
  font-size: 13px;
  font-weight: 600;
}
.result-tag.score-excellent { background: rgba(16, 185, 129, 0.15); color: #10b981; }
.result-tag.score-good { background: rgba(245, 158, 11, 0.15); color: #f59e0b; }
.result-tag.score-needs-work { background: rgba(239, 68, 68, 0.15); color: #ef4444; }

.objective-detail {
  background: rgba(255, 255, 255, 0.04);
  padding: 12px 16px;
  border-left: 3px solid var(--accent-primary);
  border-radius: 6px;
  font-size: 13px;
  margin-bottom: 12px;
  color: var(--text-primary);
}

.correct-answer-box {
  background: rgba(16, 185, 129, 0.08);
  border: 1px solid rgba(16, 185, 129, 0.3);
  padding: 12px 16px;
  border-radius: 6px;
  font-size: 13px;
  margin-bottom: 12px;
  color: var(--text-primary);
}
.correct-answer-box pre {
  margin: 6px 0 0;
  font-family: 'Consolas', monospace;
  font-size: 14px;
  color: #10b981;
  white-space: pre-wrap;
}

.feedback-box {
  background: rgba(255, 255, 255, 0.05);
  padding: 16px;
  border-radius: var(--radius-md);
  text-align: left;
  line-height: 1.6;
}

.modal-footer {
  padding: 16px 24px;
  border-top: 1px solid var(--border-color);
  display: flex;
  justify-content: flex-end;
  gap: 12px;
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
.spin.big {
  width: 36px;
  height: 36px;
  border-width: 3px;
  margin-bottom: 14px;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>