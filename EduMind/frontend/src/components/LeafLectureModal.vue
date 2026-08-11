<template>
  <div v-if="modelValue" class="modal-overlay" @click.self="close">
    <div class="modal-content glass-panel" @click.stop>
      <div class="modal-header">
        <h3 class="modal-title">📖 知识点精讲</h3>
        <button class="close-btn" @click="close">✕</button>
      </div>

      <div class="modal-body">
        <div v-if="loading" class="state-container">
          <span class="spin big"></span>
          <p>正在加载教辅原文…</p>
        </div>
        <div v-else-if="data" class="lecture-content">
          <div class="lecture-meta">
            <span class="meta-tag">{{ data.source || '教辅' }}</span>
            <span class="meta-title">{{ data.title }}</span>
          </div>
          <div class="lecture-text md-content" v-html="rendered"></div>
        </div>
        <div v-else class="state-container">
          <p>未能加载精讲内容</p>
        </div>
      </div>

      <div class="modal-footer">
        <EduButton variant="success" :disabled="loading || !data" @click="markDone">
          <template #prefix>✓</template>
          标记已学（+1 掌握度）
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
});
const emit = defineEmits(['update:modelValue', 'done']);

const loading = ref(false);
const data = ref(null);

const rendered = computed(() => renderMarkdown(data.value?.content || ''));

watch(
  () => [props.modelValue, props.leafId],
  async ([open, id]) => {
    if (!open || !id) return;
    data.value = null;
    loading.value = true;
    try {
      const res = await api.get('/resources/leaf-lecture', { params: { leaf_id: id } });
      data.value = res.data;
    } catch (err) {
      console.error('Failed to load lecture', err);
      data.value = null;
    } finally {
      loading.value = false;
    }
  },
  { immediate: true }
);

async function markDone() {
  try {
    await api.post('/resources/leaf-lecture/done', { leaf_id: props.leafId });
    emit('done', { leaf_id: props.leafId });
    close();
  } catch (err) {
    alert('标记失败：' + (err?.message || '网络异常'));
  }
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
  width: min(720px, 96vw);
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
.lecture-meta {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 14px;
}
.meta-tag {
  font-size: 11px;
  padding: 3px 10px;
  border-radius: 999px;
  background: rgba(167, 139, 250, 0.15);
  color: #c4b5fd;
  border: 1px solid rgba(167, 139, 250, 0.3);
}
.meta-title {
  font-size: 13px;
  color: var(--text-secondary);
}
.lecture-text {
  background: rgba(15, 23, 42, 0.5);
  padding: 16px;
  border-radius: 10px;
  border: 1px solid rgba(148, 163, 184, 0.15);
}
.modal-footer {
  padding: 14px 20px;
  border-top: 1px solid rgba(167, 139, 250, 0.2);
  display: flex;
  justify-content: flex-end;
}
</style>
