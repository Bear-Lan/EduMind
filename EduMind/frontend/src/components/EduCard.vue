<template>
  <div class="edu-card glass-panel" :class="{ 'is-hoverable': hoverable, 'is-active': active }">
    <div v-if="$slots.header || title" class="edu-card-header">
      <slot name="header">
        <div class="edu-card-title">{{ title }}</div>
      </slot>
    </div>
    
    <div class="edu-card-body" :style="{ padding: bodyPadding }">
      <slot></slot>
    </div>
    
    <div v-if="$slots.footer" class="edu-card-footer">
      <slot name="footer"></slot>
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: String,
  hoverable: Boolean,
  active: Boolean,
  bodyPadding: {
    type: String,
    default: '16px'
  }
});
</script>

<style scoped>
.edu-card {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: all var(--transition-normal);
}

.is-hoverable {
  cursor: pointer;
}
.is-hoverable:hover {
  border-color: var(--accent-primary);
  background: rgba(255, 255, 255, 0.04);
  transform: translateY(-2px);
  box-shadow: var(--shadow-sm);
}

.is-active {
  border-color: var(--accent-primary);
  background: var(--accent-dim);
}

.edu-card-header {
  padding: 14px 16px;
  border-bottom: 1px solid var(--border-color);
  font-weight: 600;
  font-size: 14px;
}

.edu-card-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.edu-card-body {
  flex: 1;
}

.edu-card-footer {
  padding: 12px 16px;
  border-top: 1px dashed rgba(255, 255, 255, 0.06);
  background: rgba(0, 0, 0, 0.1);
}
</style>
