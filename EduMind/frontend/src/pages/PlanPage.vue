<template>
  <div class="plan-page">
    <div v-if="learningStore.loadingPlan" class="loading-state">
      <span class="spin" style="font-size: 24px; margin-bottom: 16px;"></span>
      <div>AI 推荐引擎运算中，请稍候...</div>
    </div>
    
    <div v-else-if="!plan || !plan.plan_id" class="empty-state">
      <div class="emoji-huge">📚</div>
      <h3>还没有学习计划</h3>
      <p>系统将根据您的基础自动为您安排第一个学习任务</p>
      <EduButton 
        variant="primary" 
        size="lg" 
        style="margin-top: 24px;" 
        @click="handleRegen"
      >
        <template #prefix>✨</template>
        立即生成学习计划
      </EduButton>
    </div>

    <div v-else class="plan-content">
      <div class="toolbar" style="display: flex; justify-content: flex-end; margin-bottom: 16px;">
        <EduButton size="sm" variant="ghost" :loading="learningStore.loadingPlan" @click="handleRegen">
          <template #prefix>🔄</template>
          重新推荐
        </EduButton>
      </div>
      <!-- AI Guide / Carousel -->
      <div v-if="plan.ai_guide" class="ai-guide">
        <div class="guide-header">💡 知识点精讲</div>
        <!-- Simplified markdown rendering for now -->
        <div class="md-content" v-html="renderMarkdown(plan.ai_guide)"></div>
      </div>

      <h3 class="topic-title">
        📌 当前突破章节：{{ topicZhName }}
      </h3>

      <div class="steps-list">
        <EduCard 
          v-for="(step, idx) in plan.learning_steps" 
          :key="step.step_number"
          class="step-card"
          :class="{ 'is-completed': step.completed }"
          hoverable
        >
          <div class="step-num">0{{ step.step_number }}</div>
          <div class="step-title">
            <span class="dot" :class="{ 'is-ok': step.completed }"></span>
            {{ step.title }}
          </div>
          <p class="step-desc">{{ step.description }}</p>
          
          <div class="step-footer">
            <span class="step-meta">第 {{ step.step_number }} / {{ plan.learning_steps.length }} 步</span>
            
            <div v-if="step.completed" class="status-done">✅ 已完成</div>
            <div v-else-if="idx === 0 || plan.learning_steps[idx-1].completed" class="action-btn">
              <EduButton size="sm" variant="success" @click="completeStep(step)">
                {{ step.step_number === plan.learning_steps.length ? '开始测验 📝' : '标记完成 ✓' }}
              </EduButton>
            </div>
            <div v-else class="status-locked">🔒 前序未完成</div>
          </div>
        </EduCard>
      </div>
    </div>
    
    <AssessmentModal 
      v-model="showAssessment"
      :topic="plan?.target_topic"
      :topicName="topicZhName"
      @completed="onAssessmentCompleted"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useLearningStore } from '../stores/learning';
import { marked } from 'marked';
import EduButton from '../components/EduButton.vue';
import EduCard from '../components/EduCard.vue';
import AssessmentModal from '../components/AssessmentModal.vue';

const learningStore = useLearningStore();
const showAssessment = ref(false);
const activeStep = ref(null);

onMounted(() => {
  learningStore.fetchCurrentPlan();
});

const plan = computed(() => learningStore.plan);

const topicZhName = computed(() => {
  if (!plan.value) return '';
  return learningStore.topicsMap[plan.value.target_topic] || plan.value.target_topic;
});

function handleRegen() {
  learningStore.generatePlan();
}

function renderMarkdown(text) {
  if (!text) return '';
  // In a real app we'd handle carousel, here we just join them and parse
  const cleanText = text.replace(/\n\s*[-*_]{3,}\s*\n/g, '\n\n---\n\n');
  return marked.parse(cleanText);
}

async function completeStep(step) {
  activeStep.value = step;
  if (step.step_number === plan.value.learning_steps.length) {
    // This is the last step (assessment), show modal
    showAssessment.value = true;
  } else {
    // Normal step, mark as complete with 1.0 score
    await learningStore.completeStep(plan.value.plan_id, step.step_number, 1.0);
  }
}

async function onAssessmentCompleted(score) {
  if (activeStep.value) {
    await learningStore.completeStep(plan.value.plan_id, activeStep.value.step_number, score);
    activeStep.value = null;
  }
}
</script>

<style scoped>
.plan-page {
  position: relative;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.loading-state, .empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-secondary);
  text-align: center;
  padding: 40px;
}

.emoji-huge {
  font-size: 48px;
  margin-bottom: 16px;
}
.empty-state h3 {
  color: var(--text-primary);
  margin-bottom: 8px;
}

.plan-content {
  padding: 16px;
}

.ai-guide {
  background: rgba(167, 139, 250, 0.05);
  border: 1px solid rgba(167, 139, 250, 0.1);
  border-radius: var(--radius-md);
  padding: 24px;
  margin-bottom: 24px;
}
.guide-header {
  font-weight: 800;
  color: #ddd6fe;
  font-size: 16px;
  margin-bottom: 16px;
  border-bottom: 1px solid rgba(167, 139, 250, 0.2);
  padding-bottom: 12px;
}

.topic-title {
  font-size: 16px;
  font-weight: 800;
  color: #a78bfa;
  margin-bottom: 16px;
  line-height: 1.4;
}

.step-card {
  margin-bottom: 16px;
  position: relative;
}
.step-card.is-completed {
  border-color: rgba(16, 185, 129, 0.28);
  background: rgba(16, 185, 129, 0.03);
}

.step-num {
  font-size: 32px;
  font-weight: 800;
  color: rgba(255, 255, 255, 0.04);
  position: absolute;
  top: 8px;
  right: 16px;
}

.step-title {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--status-danger);
}
.dot.is-ok {
  background: var(--status-success);
}

.step-desc {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 16px;
  line-height: 1.6;
}

.step-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: auto;
}
.step-meta {
  font-size: 12px;
  color: var(--text-secondary);
}
.status-done {
  color: var(--status-success);
  font-weight: 700;
  font-size: 13px;
}
.status-locked {
  font-size: 12px;
  color: var(--text-secondary);
}
</style>
