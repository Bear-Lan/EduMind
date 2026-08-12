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
      <div class="toolbar">
        <EduButton size="sm" variant="ghost" :loading="learningStore.loadingPlan" @click="handleRegen">
          <template #prefix>🔄</template>
          重新推荐
        </EduButton>
      </div>

      <!-- 本章概念树：放在「突破章节」上方 -->
      <section class="visual-panel">
        <div class="visual-header">
          <h4>本章掌握度导图</h4>
          <p>参考技能树样式：圆点 + 曲线连线；点击分支可折叠。叶子亮度随刷题答对加深（L0–L3）。</p>
        </div>

        <div v-if="plan.reason" class="reason-box">
          <span class="reason-label">为什么推这一章</span>
          <p>{{ plan.reason }}</p>
        </div>

        <ChapterConceptTree
          :root="conceptTree"
          :loading="treeLoading"
          @lecture="onLecture"
          @quiz="onQuiz"
        />
      </section>

      <h3 class="topic-title">
        📌 当前突破章节：{{ topicZhName }}
      </h3>

      <div v-if="plan.ai_guide" class="ai-guide">
        <div class="guide-header">💡 知识点精讲</div>
        <div class="md-content" v-html="renderMarkdown(plan.ai_guide)"></div>
      </div>

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

    <LeafLectureModal
      v-model="showLecture"
      :leafId="activeLeafId"
      @done="onLectureDone"
    />

    <LeafQuizModal
      v-model="showLeafQuiz"
      :leafId="activeLeafId"
      :slot="activeQuizSlot"
      @done="onLeafQuizDone"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { useLearningStore } from '../stores/learning';
import { renderMarkdown } from '../utils/markdown';
import api from '../utils/api';
import EduButton from '../components/EduButton.vue';
import EduCard from '../components/EduCard.vue';
import AssessmentModal from '../components/AssessmentModal.vue';
import ChapterConceptTree from '../components/ChapterConceptTree.vue';
import LeafLectureModal from '../components/LeafLectureModal.vue';
import LeafQuizModal from '../components/LeafQuizModal.vue';

const learningStore = useLearningStore();
const showAssessment = ref(false);
const activeStep = ref(null);
const treeLoading = ref(false);
const conceptTree = ref(null);
const showLecture = ref(false);
const showLeafQuiz = ref(false);
const activeLeafId = ref('');
const activeQuizSlot = ref(1);

const plan = computed(() => learningStore.plan);

const topicZhName = computed(() => {
  if (!plan.value) return '';
  return learningStore.topicsMap[plan.value.target_topic] || plan.value.target_topic;
});

async function loadConceptTree() {
  const topic = plan.value?.target_topic;
  if (!topic) {
    conceptTree.value = null;
    return;
  }

  // 已有树时不要切 loading：否则 SVG 被拆掉，markmap 实例失联，图会“消失”
  const hasExisting = !!(conceptTree.value?.children?.length);
  if (!hasExisting) treeLoading.value = true;
  try {
    if (!learningStore.profile) {
      await learningStore.fetchProfile();
    }
    const res = await api.get('/resources/concept-tree', {
      params: {
        topic,
        label: topicZhName.value || topic,
      },
    });
    if (res?.data?.children?.length) {
      conceptTree.value = res.data;
    } else if (!hasExisting) {
      conceptTree.value = res?.data || null;
    }
    // 刷新失败/空结果时保留旧树，避免整图消失
  } catch (err) {
    console.error('Failed to load chapter concept tree', err);
    if (!hasExisting) conceptTree.value = null;
  } finally {
    treeLoading.value = false;
  }
}

onMounted(async () => {
  await learningStore.fetchCurrentPlan();
  await loadConceptTree();
});

watch(
  () => plan.value?.target_topic,
  () => {
    loadConceptTree();
  }
);

function handleRegen() {
  learningStore.generatePlan().then(() => loadConceptTree());
}

function onLecture(payload) {
  activeLeafId.value = payload.leaf_id;
  showLecture.value = true;
}

function onQuiz(payload) {
  activeLeafId.value = payload.leaf_id;
  // 后端给出第一个未通关的题位（1/2/null）；null 表示两题都对了，已通关
  if (!payload.slot) {
    alert('该要点已通关（精讲 + 两题全部答对），无需再练');
    return;
  }
  activeQuizSlot.value = payload.slot;
  showLeafQuiz.value = true;
}

async function onLectureDone() {
  await loadConceptTree();
}

async function onLeafQuizDone(payload) {
  // 若该 slot 不正确或想继续刷，可手动再点例题练习
  if (payload?.is_correct) {
    await loadConceptTree();
  }
}

async function completeStep(step) {
  activeStep.value = step;
  if (step.step_number === plan.value.learning_steps.length) {
    showAssessment.value = true;
  } else {
    await learningStore.completeStep(plan.value.plan_id, step.step_number, 1.0);
  }
}

async function onAssessmentCompleted(score) {
  if (activeStep.value) {
    await learningStore.completeStep(plan.value.plan_id, activeStep.value.step_number, score);
    activeStep.value = null;
  }
  await loadConceptTree();
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

.toolbar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 12px;
}

.visual-panel {
  margin-bottom: 14px;
  padding: 12px;
  border-radius: var(--radius-md);
  background: rgba(15, 23, 42, 0.45);
  border: 1px solid rgba(167, 139, 250, 0.18);
}

.visual-header h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 800;
  color: #ddd6fe;
}
.visual-header p {
  margin: 6px 0 0;
  font-size: 12px;
  color: var(--text-secondary);
}

.reason-box {
  margin: 14px 0;
  padding: 12px 14px;
  border-radius: 10px;
  background: rgba(167, 139, 250, 0.08);
  border: 1px solid rgba(167, 139, 250, 0.16);
}
.reason-label {
  display: inline-block;
  font-size: 11px;
  font-weight: 700;
  color: #c4b5fd;
  margin-bottom: 6px;
}
.reason-box p {
  margin: 0;
  font-size: 13px;
  line-height: 1.55;
  color: var(--text-primary);
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
