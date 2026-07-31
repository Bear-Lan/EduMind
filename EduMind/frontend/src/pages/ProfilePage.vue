<template>
  <div class="profile-page">
    <div v-if="learningStore.loadingProfile" class="loading-state">
      <span class="spin"></span> 加载画像中...
    </div>
    
    <template v-else-if="profile">
      <!-- Current Goal -->
      <div class="goal-box">
        <div class="goal-tag">当前学习目标</div>
        <div class="goal-val">{{ profile.current_goal || '暂无目标' }}</div>
      </div>

      <!-- Mastery List -->
      <div class="mastery-section">
        <h4 class="section-label">各章节掌握度 ({{ profile.subject }})</h4>
        
        <div class="mastery-list">
          <div 
            v-for="topic in topicMastery" 
            :key="topic.key"
            class="mastery-item"
            @click="handleTopicClick(topic.key)"
          >
            <div class="mastery-row">
              <span class="topic-name" :class="{ 'is-current': topic.key === currentTargetTopic }">
                {{ topic.name }}
              </span>
              <span class="topic-score" :style="{ color: topic.color }">
                {{ topic.percentage }}%
              </span>
            </div>
            <div class="mbar">
              <div 
                class="mfill" 
                :style="{ 
                  width: `${topic.percentage}%`,
                  background: topic.percentage >= 80 ? 'var(--status-success)' : 'linear-gradient(90deg, var(--accent-primary), #a78bfa)'
                }"
              ></div>
            </div>
          </div>
        </div>
        
        <div v-if="topicMastery.length === 0" class="empty-state">
          暂无该学科课程大纲，系统正在生成或请重新选择。
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue';
import { useLearningStore } from '../stores/learning';

const learningStore = useLearningStore();

onMounted(() => {
  learningStore.fetchProfile();
});

const profile = computed(() => learningStore.profile);
const currentTargetTopic = computed(() => learningStore.plan?.target_topic);

const topicMastery = computed(() => {
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
    
    let color = 'var(--text-secondary)';
    if (percentage >= 80) color = 'var(--status-success)';
    else if (percentage > 0) color = 'var(--status-warning)';
    
    list.push({
      key: enKey,
      name: zhNames[enKey] || enKey,
      percentage,
      color
    });
  }
  
  return list;
});

function handleTopicClick(topicKey) {
  if (confirm(`是否切换学习目标至章节：${topicKey} ？`)) {
    learningStore.generatePlan(topicKey);
  }
}
</script>

<style scoped>
.profile-page {
  padding: 16px;
}

.loading-state {
  text-align: center;
  padding: 40px 0;
  color: var(--text-secondary);
  font-size: 14px;
}

.goal-box {
  background: var(--accent-dim);
  border: 1px solid rgba(99, 102, 241, 0.22);
  border-radius: var(--radius-sm);
  padding: 16px;
  margin-bottom: 24px;
}
.goal-tag {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  color: #818cf8;
  font-weight: 700;
  margin-bottom: 6px;
}
.goal-val {
  font-size: 14px;
  font-weight: 600;
  line-height: 1.5;
  color: var(--text-primary);
}

.section-label {
  font-size: 12px;
  font-weight: 700;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 16px;
}

.mastery-item {
  margin-bottom: 16px;
  cursor: pointer;
  padding: 8px;
  border-radius: var(--radius-sm);
  transition: background var(--transition-fast);
}
.mastery-item:hover {
  background: rgba(255, 255, 255, 0.05);
}

.mastery-row {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  margin-bottom: 6px;
}

.topic-name {
  color: var(--text-secondary);
  transition: color 0.2s;
}
.topic-name.is-current {
  color: var(--accent-primary);
  font-weight: 700;
}
.mastery-item:hover .topic-name {
  color: var(--text-primary);
}

.topic-score {
  font-weight: 700;
}

.mbar {
  background: rgba(255, 255, 255, 0.05);
  height: 6px;
  border-radius: 3px;
  overflow: hidden;
}
.mfill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.9s cubic-bezier(0.4, 0, 0.2, 1);
}

.empty-state {
  text-align: center;
  font-size: 12px;
  color: var(--text-secondary);
  padding: 20px;
}
</style>
