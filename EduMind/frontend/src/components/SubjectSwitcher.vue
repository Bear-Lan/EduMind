<template>
  <div class="subject-switcher" :class="{ 'is-loading': isLoading }">
    <div class="switcher-trigger" @click="toggleDropdown">
      <span class="icon">🎯</span>
      <span class="current-subject">{{ currentGoal || '未设定目标' }}</span>
      <span class="arrow" :class="{ 'is-open': isOpen }">▼</span>
    </div>

    <!-- Dropdown Menu -->
    <div v-if="isOpen" class="dropdown-menu">
      <div class="dropdown-header">设定新学习目标</div>
      
      <div class="selection-grid">
        <!-- Grade Column -->
        <div class="selection-col">
          <div class="col-title">年级 / 阶段</div>
          <div class="preset-tags">
            <span 
              v-for="g in gradePresets" 
              :key="g"
              class="preset-tag"
              :class="{ active: g === selectedGrade }"
              @click="setGrade(g)"
            >
              {{ g }}
            </span>
          </div>
          <input 
            v-model="customGrade" 
            class="custom-input" 
            placeholder="自定义阶段..." 
            @focus="selectedGrade = ''"
          />
        </div>

        <!-- Subject Column -->
        <div class="selection-col">
          <div class="col-title">学科 / 方向</div>
          <div class="preset-tags">
            <span 
              v-for="s in subjectPresets" 
              :key="s"
              class="preset-tag"
              :class="{ active: s === selectedSubject }"
              @click="setSubject(s)"
            >
              {{ s }}
            </span>
          </div>
          <input 
            v-model="customSubject" 
            class="custom-input" 
            placeholder="自定义学科..." 
            @focus="selectedSubject = ''"
          />
        </div>
      </div>

      <div class="dropdown-footer">
        <button class="btn-cancel" @click="isOpen = false">取消</button>
        <button class="btn-confirm" :disabled="!finalSubject" @click="submitGoal">确认切换</button>
      </div>
    </div>

    <!-- Loading Overlay -->
    <div v-if="isLoading" class="loading-overlay">
      <span class="spin"></span> 正在为您编排专属大纲体系，请稍候...
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { useLearningStore } from '../stores/learning';
import api from '../utils/api';

const learningStore = useLearningStore();

const gradePresets = ['小学', '初中', '高中', '大学', '职业/兴趣'];
const subjectPresets = ['数学', '英语', '物理', '化学', '计算机科学', '通识'];

const currentGoal = computed(() => learningStore.profile?.current_goal || learningStore.profile?.subject);

const isOpen = ref(false);
const isLoading = ref(false);

const selectedGrade = ref('');
const customGrade = ref('');

const selectedSubject = ref('');
const customSubject = ref('');

const finalGrade = computed(() => customGrade.value.trim() || selectedGrade.value);
const finalSubject = computed(() => customSubject.value.trim() || selectedSubject.value);

function toggleDropdown() {
  isOpen.value = !isOpen.value;
  if (isOpen.value) {
    // Reset selections on open
    selectedGrade.value = '';
    customGrade.value = '';
    selectedSubject.value = '';
    customSubject.value = '';
  }
}

function setGrade(g) {
  selectedGrade.value = g;
  customGrade.value = '';
}

function setSubject(s) {
  selectedSubject.value = s;
  customSubject.value = '';
}

// Close dropdown when clicking outside
window.addEventListener('click', (e) => {
  if (!e.target.closest('.subject-switcher') && isOpen.value) {
    isOpen.value = false;
  }
});

async function submitGoal() {
  if (!finalSubject.value) return;
  
  const g = finalGrade.value;
  const s = finalSubject.value;
  const goalStr = g ? `${g} ${s}` : s;

  if (goalStr === currentGoal.value) {
    isOpen.value = false;
    return;
  }

  try {
    isLoading.value = true;
    isOpen.value = false;
    
    // Call API to update profile
    const res = await api.put('/profile', {
      subject: s,
      current_goal: goalStr
    });
    
    if (res.data) {
      learningStore.profile = res.data;
      window.location.reload();
    }
  } catch (err) {
    console.error("Failed to update goal:", err);
    alert(err.response?.data?.message || '切换学习目标失败');
  } finally {
    isLoading.value = false;
  }
}
</script>

<style scoped>
.subject-switcher {
  position: relative;
  margin-left: 24px;
  margin-right: auto;
  z-index: 200;
}

.switcher-trigger {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: rgba(167, 139, 250, 0.1);
  border: 1px solid rgba(167, 139, 250, 0.3);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  color: #c4b5fd;
  font-size: 14px;
  font-weight: 600;
}

.switcher-trigger:hover {
  background: rgba(167, 139, 250, 0.2);
  border-color: rgba(167, 139, 250, 0.5);
}

.arrow {
  font-size: 10px;
  transition: transform 0.2s ease;
}
.arrow.is-open {
  transform: rotate(180deg);
}

.dropdown-menu {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  width: 360px;
  background: rgba(12, 14, 29, 0.98);
  backdrop-filter: blur(10px);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.6);
  display: flex;
  flex-direction: column;
}

.dropdown-header {
  padding: 12px 16px;
  font-size: 14px;
  font-weight: 700;
  color: #fff;
  border-bottom: 1px solid var(--border-color);
}

.selection-grid {
  display: flex;
  padding: 16px;
  gap: 20px;
}

.selection-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.col-title {
  font-size: 12px;
  color: var(--text-secondary);
  text-transform: uppercase;
  font-weight: 700;
}

.preset-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.preset-tag {
  padding: 4px 10px;
  font-size: 12px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  color: var(--text-primary);
  cursor: pointer;
  transition: all 0.2s;
}

.preset-tag:hover {
  background: rgba(167, 139, 250, 0.2);
  border-color: rgba(167, 139, 250, 0.3);
}

.preset-tag.active {
  background: #a78bfa;
  border-color: #a78bfa;
  color: #0f1121;
  font-weight: 700;
}

.custom-input {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  padding: 6px 10px;
  color: #fff;
  font-size: 12px;
  outline: none;
  transition: border-color 0.2s;
}

.custom-input:focus {
  border-color: #a78bfa;
}

.dropdown-footer {
  padding: 12px 16px;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  border-top: 1px solid var(--border-color);
  background: rgba(255, 255, 255, 0.02);
  border-radius: 0 0 12px 12px;
}

.btn-cancel, .btn-confirm {
  padding: 6px 16px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all 0.2s;
}

.btn-cancel {
  background: transparent;
  color: var(--text-secondary);
}
.btn-cancel:hover {
  color: #fff;
}

.btn-confirm {
  background: #a78bfa;
  color: #0f1121;
}
.btn-confirm:hover:not(:disabled) {
  background: #c4b5fd;
}
.btn-confirm:disabled {
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.3);
  cursor: not-allowed;
}

.loading-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.7);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 16px;
  z-index: 9999;
}

.spin {
  display: inline-block;
  width: 20px;
  height: 20px;
  border: 3px solid currentColor;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-right: 12px;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
