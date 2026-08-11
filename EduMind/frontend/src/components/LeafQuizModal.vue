<template>
  <div v-if="modelValue" class="modal-overlay" @click.self="close">
    <div class="modal-content glass-panel" @click.stop>
      <div class="modal-header">
        <h3 class="modal-title">
          📝 例题练习
          <span v-if="slotLabel" class="slot-badge">第 {{ slot }} 题</span>
        </h3>
        <button class="close-btn" @click="close">✕</button>
      </div>

      <div class="modal-body">
        <div v-if="state === 'loading'" class="state-container">
          <span class="spin big"></span>
          <p>正在抽取/生成题目…</p>
        </div>

        <div v-else-if="state === 'answering' && question" class="answering-state">
          <div class="question-box md-content" v-html="renderMarkdown(question.stem)"></div>

          <div
            v-if="question.question_type === 'single_choice' || question.question_type === 'true_false'"
            class="choice-list"
          >
            <label
              v-for="(text, key) in question.options || {}"
              :key="key"
              class="choice-item"
              :class="{ selected: userAnswer.answer === key }"
            >
              <input type="radio" :value="key" v-model="userAnswer.answer" class="choice-radio" />
              <span class="choice-key">{{ key }}</span>
              <span class="choice-text">{{ text }}</span>
            </label>
          </div>

          <div v-else-if="question.question_type === 'fill_blank'" class="fill-section">
            <label class="answer-label">你的答案：</label>
            <input v-model="userAnswer.text" type="text" class="fill-input" placeholder="请输入答案…" />
          </div>
        </div>

        <div v-else-if="state === 'grading'" class="state-container">
          <span class="spin big"></span>
          <p>正在判分…</p>
        </div>

        <div v-else-if="state === 'result' && gradeResult" class="result-state">
          <div class="score-display">
            <div class="score-circle" :class="scoreClass">
              <span class="score-value">{{ Math.round(gradeResult.score * 100) }}</span>
              <span class="score-unit">分</span>
            </div>
            <div class="result-tag" :class="scoreClass">{{ resultTag }}</div>
          </div>
          <div v-if="!gradeResult.is_correct" class="correct-answer-box">
            <strong>✅ 参考答案：</strong>
            <pre>{{ formatAnswer(gradeResult.correct_answer) }}</pre>
          </div>
          <div class="detail-box">{{ gradeResult.details }}</div>
        </div>

        <div v-else-if="state === 'error'" class="state-container">
          <p>{{ errorMsg }}</p>
        </div>
      </div>

      <div class="modal-footer">
        <EduButton v-if="state === 'answering'" variant="success" :disabled="!canSubmit" @click="submit">
          提交作答
        </EduButton>
        <EduButton v-if="state === 'result'" variant="primary" @click="close">
          完成
        </EduButton>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue';
import api from '../utils/api';
import { renderMarkdown } from '../utils/markdown';
import EduButton from './EduButton.vue';

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  leafId: { type: String, default: '' },
  slot: { type: Number, default: 1 },
});
const emit = defineEmits(['update:modelValue', 'done']);

const state = ref('loading');
const question = ref(null);
const userAnswer = ref({});
const gradeResult = ref(null);
const errorMsg = ref('');

const slotLabel = computed(() => props.slot);

const canSubmit = computed(() => {
  if (!question.value) return false;
  if (question.value.question_type === 'fill_blank') {
    return (userAnswer.value.text || '').trim().length > 0;
  }
  return !!userAnswer.value.answer;
});

const scoreClass = computed(() => {
  const s = gradeResult.value?.score || 0;
  if (s >= 0.8) return 'score-excellent';
  if (s >= 0.6) return 'score-good';
  return 'score-needs-work';
});

const resultTag = computed(() => {
  if (gradeResult.value?.is_correct) return '🎉 回答正确（+1 掌握度）';
  const s = gradeResult.value?.score || 0;
  if (s >= 0.7) return '接近正确';
  if (s >= 0.4) return '部分正确';
  return '需要加强';
});

watch(
  () => [props.modelValue, props.leafId, props.slot],
  async ([open, id, slot]) => {
    if (!open || !id) return;
    state.value = 'loading';
    question.value = null;
    userAnswer.value = {};
    gradeResult.value = null;
    try {
      const res = await api.get('/resources/leaf-quiz', {
        params: { leaf_id: id, slot: Number(slot) },
      });
      question.value = res.data;
      state.value = 'answering';
    } catch (err) {
      errorMsg.value = err?.response?.data?.message || err?.message || '无题且 AI 生成失败';
      state.value = 'error';
    }
  },
  { immediate: true }
);

async function submit() {
  if (!canSubmit.value) return;
  state.value = 'grading';
  try {
    const res = await api.post('/resources/leaf-quiz/submit', {
      leaf_id: props.leafId,
      slot: props.slot,
      question_id: question.value.question_id,
      user_answer: { ...userAnswer.value },
    });
    gradeResult.value = res.data;
    state.value = 'result';
    emit('done', {
      leaf_id: props.leafId,
      slot: props.slot,
      is_correct: res.data.is_correct,
      level: res.data.level,
    });
  } catch (err) {
    errorMsg.value = '判分失败：' + (err?.message || '网络异常');
    state.value = 'error';
  }
}

function formatAnswer(ans) {
  if (!ans) return '';
  if (typeof ans === 'string') return ans;
  if (ans.answer) return ans.answer;
  if (ans.answers) return (ans.answers || []).join(', ');
  return JSON.stringify(ans);
}

function close() {
  emit('update:modelValue', false);
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
  width: min(640px, 96vw);
  max-height: 86vh;
  display: flex;
  flex-direction: column;
  border-radius: 16px;
}
.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(167, 139, 250, 0.2);
}
.modal-title {
  margin: 0;
  font-size: 16px;
  font-weight: 800;
  color: #ddd6fe;
  display: flex;
  align-items: center;
  gap: 10px;
}
.slot-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(167, 139, 250, 0.15);
  color: #c4b5fd;
  border: 1px solid rgba(167, 139, 250, 0.3);
}
.close-btn {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 18px;
}
.close-btn:hover { color: var(--text-primary); }
.modal-body {
  padding: 20px;
  overflow-y: auto;
  color: var(--text-primary);
  line-height: 1.7;
  font-size: 14px;
}
.state-container {
  text-align: center;
  padding: 32px;
  color: var(--text-secondary);
}
.question-box {
  background: rgba(15, 23, 42, 0.5);
  padding: 16px;
  border-radius: 10px;
  margin-bottom: 16px;
  border: 1px solid rgba(148, 163, 184, 0.15);
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
  border-radius: 10px;
  border: 1px solid rgba(148, 163, 184, 0.2);
  background: rgba(30, 41, 59, 0.5);
  cursor: pointer;
  transition: all 0.2s ease;
}
.choice-item:hover {
  border-color: rgba(167, 139, 250, 0.4);
  background: rgba(51, 65, 85, 0.6);
}
.choice-item.selected {
  border-color: #a78bfa;
  background: rgba(167, 139, 250, 0.12);
}
.choice-radio {
  accent-color: #a78bfa;
}
.choice-key {
  font-weight: 800;
  color: #c4b5fd;
  width: 22px;
}
.choice-text {
  flex: 1;
}
.fill-section {
  display: flex;
  align-items: center;
  gap: 10px;
}
.fill-input {
  flex: 1;
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid rgba(148, 163, 184, 0.3);
  background: rgba(15, 23, 42, 0.6);
  color: var(--text-primary);
}
.result-state {
  text-align: center;
}
.score-display {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}
.score-circle {
  width: 96px;
  height: 96px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  border: 3px solid;
  flex-direction: column;
}
.score-circle.score-excellent { border-color: #10b981; color: #6ee7b7; }
.score-circle.score-good { border-color: #f59e0b; color: #fcd34d; }
.score-circle.score-needs-work { border-color: #ef4444; color: #fca5a5; }
.score-value {
  font-size: 28px;
  font-weight: 800;
}
.score-unit {
  font-size: 12px;
}
.result-tag {
  font-size: 14px;
  font-weight: 700;
}
.result-tag.score-excellent { color: #6ee7b7; }
.result-tag.score-good { color: #fcd34d; }
.result-tag.score-needs-work { color: #fca5a5; }
.correct-answer-box {
  margin: 12px 0;
  padding: 12px;
  background: rgba(16, 185, 129, 0.08);
  border: 1px solid rgba(16, 185, 129, 0.25);
  border-radius: 8px;
  text-align: left;
}
.correct-answer-box pre {
  margin: 6px 0 0;
  white-space: pre-wrap;
  font-family: inherit;
}
.detail-box {
  font-size: 13px;
  color: var(--text-secondary);
}
.modal-footer {
  padding: 14px 20px;
  border-top: 1px solid rgba(167, 139, 250, 0.2);
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>
