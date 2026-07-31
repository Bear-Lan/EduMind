<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="modelValue" class="edu-modal-overlay" @click.self="closeOnMask && close()">
        <Transition name="slide-up">
          <div v-if="modelValue" class="edu-modal-content" :style="{ width, maxWidth }">
            
            <div v-if="showClose" class="edu-modal-close" @click="close">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                <path d="M1 1l12 12M13 1L1 13"/>
              </svg>
            </div>
            
            <div v-if="title || $slots.header" class="edu-modal-header">
              <slot name="header">
                <h3 class="edu-modal-title">{{ title }}</h3>
                <p v-if="subtitle" class="edu-modal-subtitle">{{ subtitle }}</p>
              </slot>
            </div>
            
            <div class="edu-modal-body">
              <slot></slot>
            </div>
            
            <div v-if="$slots.footer" class="edu-modal-footer">
              <slot name="footer"></slot>
            </div>
            
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { watch, onMounted, onUnmounted } from 'vue';

const props = defineProps({
  modelValue: Boolean,
  title: String,
  subtitle: String,
  width: { type: String, default: '440px' },
  maxWidth: { type: String, default: '90vw' },
  showClose: { type: Boolean, default: true },
  closeOnMask: { type: Boolean, default: true },
});

const emit = defineEmits(['update:modelValue', 'close']);

function close() {
  emit('update:modelValue', false);
  emit('close');
}

// Lock body scroll when open
watch(() => props.modelValue, (val) => {
  if (val) {
    document.body.style.overflow = 'hidden';
  } else {
    document.body.style.overflow = '';
  }
});

onUnmounted(() => {
  document.body.style.overflow = '';
});
</script>

<style scoped>
.edu-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(4, 5, 14, 0.85);
  backdrop-filter: blur(8px);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.edu-modal-content {
  background: var(--bg-panel-solid);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  position: relative;
  display: flex;
  flex-direction: column;
  max-height: 90vh;
}

.edu-modal-close {
  position: absolute;
  top: 20px;
  right: 20px;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  color: var(--text-secondary);
  cursor: pointer;
  background: rgba(255, 255, 255, 0.05);
  transition: all 0.2s;
  z-index: 10;
}
.edu-modal-close:hover {
  background: rgba(255, 255, 255, 0.1);
  color: var(--text-primary);
  transform: rotate(90deg);
}

.edu-modal-header {
  padding: 32px 32px 16px;
  text-align: center;
}

.edu-modal-title {
  font-size: 22px;
  font-weight: 800;
  margin-bottom: 6px;
  color: var(--text-primary);
}

.edu-modal-subtitle {
  font-size: 14px;
  color: var(--text-secondary);
}

.edu-modal-body {
  padding: 16px 32px 32px;
  overflow-y: auto;
}

.edu-modal-footer {
  padding: 20px 32px;
  background: rgba(0, 0, 0, 0.2);
  border-top: 1px solid var(--border-color);
  border-radius: 0 0 var(--radius-lg) var(--radius-lg);
}

/* Animations */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}
.slide-up-enter-from,
.slide-up-leave-to {
  opacity: 0;
  transform: scale(0.95) translateY(20px);
}
</style>
