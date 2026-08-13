<template>
  <div class="mn-practice">
    <!-- Progress bar -->
    <div class="mn-progress-bar">
      <div class="mn-progress-fill" :style="{ width: progressPercent }"></div>
      <span class="mn-progress-text">{{ currentIdx + 1 }} / {{ quizSet.length }}</span>
    </div>

    <!-- Final score -->
    <div v-if="practiceDone" class="mn-final-score">
      <div class="mn-score-icon">{{ scoreEmoji }}</div>
      <div class="mn-score-text">
        <div class="mn-score-percent">{{ correctCount }} / {{ quizSet.length }} 正确</div>
        <div class="mn-score-big">{{ Math.round((correctCount / quizSet.length) * 100) }}%</div>
      </div>
      <EduButton variant="primary" @click="$emit('exit')">再来一次</EduButton>
    </div>

    <!-- Current question -->
    <div v-else class="mn-practice-card" v-if="currentQuestion">
      <div class="mn-practice-meta">
        <span class="mn-quiz-type">{{ typeLabel(currentQuestion.question_type) }}</span>
        <span class="mn-quiz-diff">难度 {{ currentQuestion.difficulty }}/3</span>
      </div>
      <div class="mn-practice-stem">{{ currentQuestion.stem }}</div>

      <!-- Choice / True-False -->
      <div v-if="currentQuestion.options" class="mn-practice-options">
        <label
          v-for="(opt, key) in currentQuestion.options"
          :key="key"
          class="mn-practice-opt"
          :class="{
            selected: userAnswer === key,
            correct: showResult && isCorrectOption(key),
            wrong: showResult && userAnswer === key && !isCorrectOption(key),
          }"
        >
          <input type="radio" :value="key" v-model="userAnswer" :disabled="showResult" />
          <span class="mn-opt-key">{{ key }}</span> {{ opt }}
        </label>
      </div>

      <!-- Fill blank / Short answer -->
      <div v-else class="mn-practice-text">
        <textarea
          v-model="userAnswerText"
          class="mn-practice-input"
          placeholder="输入你的答案..."
          rows="3"
          :disabled="showResult"
        ></textarea>
      </div>

      <!-- Result feedback -->
      <div v-if="showResult" class="mn-result" :class="{ correct: lastResult?.is_correct, wrong: !lastResult?.is_correct }">
        <span class="mn-result-icon">{{ lastResult?.is_correct ? '✅' : '❌' }}</span>
        <span>正确答案：<strong>{{ formatCorrectAnswer(currentQuestion) }}</strong></span>
      </div>

      <!-- Actions -->
      <div class="mn-practice-actions">
        <EduButton v-if="!showResult" variant="primary" @click="submitAnswer" :disabled="!canSubmit">提交答案</EduButton>
        <EduButton v-if="showResult && currentIdx < quizSet.length - 1" variant="primary" @click="nextQuestion">下一题 →</EduButton>
        <EduButton v-if="showResult && currentIdx >= quizSet.length - 1" variant="primary" @click="finishPractice">查看结果 🎉</EduButton>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import EduButton from './EduButton.vue';

const props = defineProps({
  quizSet: { type: Array, default: () => [] },
});
const emit = defineEmits(['done', 'exit']);

const currentIdx = ref(0);
const userAnswer = ref('');
const userAnswerText = ref('');
const showResult = ref(false);
const lastResult = ref(null);
const correctCount = ref(0);
const practiceDone = ref(false);

const TYPE_MAP = {
  single_choice: '单选题', multiple_choice: '多选题',
  true_false: '判断题', fill_blank: '填空题', short_answer: '简答题',
};
const typeLabel = (t) => TYPE_MAP[t] || t;

const currentQuestion = computed(() => props.quizSet[currentIdx.value] || null);
const progressPercent = computed(() => {
  if (!props.quizSet.length) return '0%';
  return `${((currentIdx.value + (showResult.value ? 1 : 0)) / props.quizSet.length) * 100}%`;
});
const canSubmit = computed(() => {
  if (!currentQuestion.value) return false;
  if (currentQuestion.value.options) return !!userAnswer.value;
  return !!userAnswerText.value.trim();
});
const scoreEmoji = computed(() => {
  const pct = correctCount.value / props.quizSet.length;
  if (pct >= 0.8) return '🏆';
  if (pct >= 0.6) return '👍';
  if (pct >= 0.4) return '💪';
  return '📚';
});

function submitAnswer() {
  const q = currentQuestion.value;
  if (!q) return;
  let userAns = q.options ? { answer: userAnswer.value } : { answer: userAnswerText.value.trim() };
  const correct = q.correct_answer;
  let isCorrect = false;
  if (q.question_type === 'single_choice' || q.question_type === 'true_false') {
    isCorrect = userAns.answer === correct.answer;
  } else if (q.question_type === 'fill_blank') {
    const norm = (s) => s.toLowerCase().replace(/\s+/g, '').trim();
    isCorrect = norm(userAns.answer) === norm(correct.answer) ||
      (correct.aliases || []).some(a => norm(userAns.answer) === norm(a));
  } else if (q.question_type === 'short_answer') {
    const norm = (s) => s.toLowerCase();
    isCorrect = (correct.keywords || []).some(kw => norm(userAns.answer).includes(norm(kw)));
  }
  showResult.value = true;
  lastResult.value = { is_correct: isCorrect };
  if (isCorrect) correctCount.value++;
}

function isCorrectOption(key) {
  const q = currentQuestion.value;
  return q && q.correct_answer && key === q.correct_answer.answer;
}

function nextQuestion() {
  currentIdx.value++;
  userAnswer.value = '';
  userAnswerText.value = '';
  showResult.value = false;
  lastResult.value = null;
}

function finishPractice() {
  practiceDone.value = true;
  emit('done', { correct: correctCount.value, total: props.quizSet.length });
}

function formatCorrectAnswer(q) {
  if (!q || !q.correct_answer) return '';
  const ca = q.correct_answer;
  if (ca.answer) return ca.answer;
  if (ca.sample) return ca.sample;
  return JSON.stringify(ca);
}
</script>

<style scoped>
.mn-practice { display: flex; flex-direction: column; gap: 16px; }
.mn-progress-bar { position: relative; height: 28px; background: rgba(255,255,255,0.06); border-radius: 14px; overflow: hidden; }
.mn-progress-fill { position: absolute; top: 0; left: 0; height: 100%; background: linear-gradient(90deg, #818cf8, #a78bfa); border-radius: 14px; transition: width 0.3s ease; }
.mn-progress-text { position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%); font-size: 12px; font-weight: 700; color: var(--text-primary); z-index: 1; }
.mn-practice-card { background: rgba(255,255,255,0.03); border: 1px solid var(--border-color); border-radius: 12px; padding: 20px; }
.mn-practice-meta { display: flex; gap: 10px; align-items: center; margin-bottom: 12px; }
.mn-quiz-type { font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 6px; background: rgba(167,139,250,0.15); color: #c4b5fd; }
.mn-quiz-diff { font-size: 11px; color: var(--text-tertiary, #64748b); }
.mn-practice-stem { font-size: 15px; color: var(--text-primary); line-height: 1.6; margin-bottom: 16px; }
.mn-practice-options { display: flex; flex-direction: column; gap: 8px; }
.mn-practice-opt { display: flex; align-items: center; gap: 8px; padding: 10px 14px; background: rgba(255,255,255,0.04); border: 1px solid var(--border-color); border-radius: 8px; cursor: pointer; font-size: 14px; color: var(--text-secondary); transition: all 0.2s; }
.mn-practice-opt:hover { border-color: var(--accent-primary, #818cf8); background: rgba(99,102,241,0.08); }
.mn-practice-opt.selected { border-color: var(--accent-primary, #818cf8); background: rgba(99,102,241,0.12); }
.mn-practice-opt.correct { border-color: #10b981; background: rgba(16,185,129,0.12); }
.mn-practice-opt.wrong { border-color: #ef4444; background: rgba(239,68,68,0.12); }
.mn-opt-key { font-weight: 700; color: var(--accent-primary, #818cf8); }
.mn-practice-text { display: flex; flex-direction: column; gap: 8px; }
.mn-practice-input { width: 100%; background: rgba(6,8,20,0.9); border: 1px solid var(--border-color); border-radius: 8px; color: var(--text-primary); padding: 12px; font-size: 14px; font-family: inherit; outline: none; resize: vertical; box-sizing: border-box; }
.mn-practice-input:focus { border-color: var(--accent-primary, #818cf8); }
.mn-result { display: flex; align-items: center; gap: 10px; padding: 12px 16px; border-radius: 8px; font-size: 14px; margin-top: 12px; }
.mn-result.correct { background: rgba(16,185,129,0.1); border: 1px solid rgba(16,185,129,0.3); color: #6ee7b7; }
.mn-result.wrong { background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.3); color: #fca5a5; }
.mn-result-icon { font-size: 18px; }
.mn-practice-actions { display: flex; gap: 8px; margin-top: 16px; }
.mn-final-score { text-align: center; padding: 40px 20px; background: rgba(255,255,255,0.03); border: 1px solid var(--border-color); border-radius: 12px; display: flex; flex-direction: column; align-items: center; gap: 16px; }
.mn-score-icon { font-size: 48px; }
.mn-score-text { display: flex; flex-direction: column; gap: 4px; }
.mn-score-percent { font-size: 16px; color: var(--text-secondary); }
.mn-score-big { font-size: 36px; font-weight: 700; color: var(--accent-primary, #818cf8); }
</style>
