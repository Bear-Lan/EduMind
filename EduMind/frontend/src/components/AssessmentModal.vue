<template>
  <div v-if="modelValue" class="modal-overlay">
    <div class="modal-content glass-panel" @click.stop>
      <div class="modal-header">
        <h3 class="modal-title">📝 随堂测验：{{ topicName }}</h3>
        <button class="close-btn" @click="closeModal" v-if="state !== 'grading' && state !== 'generating'">✕</button>
      </div>
      
      <div class="modal-body">
        <!-- Generating State -->
        <div v-if="state === 'generating'" class="state-container">
          <span class="spin" style="font-size: 32px; margin-bottom: 16px;"></span>
          <p>AI 正在为你生成专属考题，请稍候...</p>
        </div>

        <!-- Answering State -->
        <div v-else-if="state === 'answering'" class="state-container answering-state">
          <div class="question-box md-content" v-html="renderMarkdown(question)"></div>
          <div class="answer-section">
            <label class="answer-label">你的回答：</label>
            <textarea 
              v-model="answer" 
              class="answer-input" 
              placeholder="请输入你的解答思路或最终答案..."
              rows="6"
            ></textarea>
          </div>
        </div>

        <!-- Grading State -->
        <div v-else-if="state === 'grading'" class="state-container">
          <span class="spin" style="font-size: 32px; margin-bottom: 16px;"></span>
          <p>AI 教练正在批改你的答卷...</p>
        </div>

        <!-- Result State -->
        <div v-else-if="state === 'result'" class="state-container result-state">
          <div class="score-display">
            <div class="score-circle" :class="scoreClass">
              <span class="score-value">{{ Math.round(gradeResult.score * 100) }}</span>
              <span class="score-unit">分</span>
            </div>
          </div>
          <div class="feedback-box md-content" v-html="renderMarkdown(gradeResult.feedback)"></div>
        </div>
      </div>
      
      <div class="modal-footer">
        <template v-if="state === 'answering'">
          <EduButton variant="ghost" @click="closeModal">稍后再测</EduButton>
          <EduButton variant="primary" :disabled="!answer.trim()" @click="submitAnswer">提交阅卷</EduButton>
        </template>
        <template v-else-if="state === 'result'">
          <EduButton full-width variant="success" @click="finishAssessment">完成学习打卡 ✓</EduButton>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue';
import { marked } from 'marked';
import api from '../utils/api';
import EduButton from './EduButton.vue';

const props = defineProps({
  modelValue: Boolean,
  topic: String,
  topicName: String,
});

const emit = defineEmits(['update:modelValue', 'completed']);

const state = ref('generating'); // 'generating' | 'answering' | 'grading' | 'result'
const question = ref('');
const answer = ref('');
const gradeResult = ref({ score: 0, feedback: '' });

watch(() => props.modelValue, async (newVal) => {
  if (newVal) {
    resetState();
    await generateQuestion();
  }
});

function resetState() {
  state.value = 'generating';
  question.value = '';
  answer.value = '';
  gradeResult.value = { score: 0, feedback: '' };
}

async function generateQuestion() {
  try {
    const res = await api.get(`/assessment/generate?topic=${encodeURIComponent(props.topic)}`);
    question.value = res.data.question;
    state.value = 'answering';
  } catch (err) {
    console.error('Failed to generate question', err);
    alert('出题失败，请检查网络或配置。');
    closeModal();
  }
}

async function submitAnswer() {
  if (!answer.value.trim()) return;
  
  state.value = 'grading';
  try {
    const res = await api.post('/assessment/grade', {
      topic: props.topic,
      question: question.value,
      answer: answer.value
    });
    gradeResult.value = res.data;
    state.value = 'result';
  } catch (err) {
    console.error('Failed to grade answer', err);
    alert('批改失败，系统已记录，将暂估一个分数。');
    gradeResult.value = { score: 0.8, feedback: '网络故障，暂估 80 分。继续加油！' };
    state.value = 'result';
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
  const score = gradeResult.value.score;
  if (score >= 0.8) return 'score-excellent';
  if (score >= 0.6) return 'score-good';
  return 'score-needs-work';
});
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
  max-width: 600px;
  background: rgba(15, 17, 33, 0.95);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  display: flex;
  flex-direction: column;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
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
}

.close-btn {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  font-size: 20px;
  cursor: pointer;
  padding: 4px;
}
.close-btn:hover {
  color: var(--text-primary);
}

.modal-body {
  padding: 24px;
  min-height: 250px;
  display: flex;
  flex-direction: column;
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

.answer-label {
  display: block;
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--text-primary);
}

.answer-input {
  width: 100%;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 12px;
  color: var(--text-primary);
  font-size: 14px;
  line-height: 1.6;
  resize: vertical;
  outline: none;
  transition: border-color var(--transition-fast);
}
.answer-input:focus {
  border-color: var(--accent-primary);
}

.result-state {
  justify-content: center;
}

.score-display {
  margin-bottom: 24px;
}

.score-circle {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  background: rgba(0,0,0,0.2);
  border: 4px solid var(--border-color);
}

.score-excellent {
  border-color: var(--status-success);
  color: var(--status-success);
  box-shadow: 0 0 20px rgba(16, 185, 129, 0.2);
}
.score-good {
  border-color: var(--status-warning);
  color: var(--status-warning);
}
.score-needs-work {
  border-color: var(--status-danger);
  color: var(--status-danger);
}

.score-value {
  font-size: 42px;
  font-weight: 800;
  line-height: 1;
}
.score-unit {
  font-size: 14px;
  font-weight: 600;
  opacity: 0.8;
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
</style>
