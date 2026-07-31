<template>
  <button 
    class="edu-btn" 
    :class="[
      `variant-${variant}`, 
      `size-${size}`, 
      { 'is-loading': loading, 'is-full': fullWidth }
    ]"
    :disabled="disabled || loading"
    v-bind="$attrs"
  >
    <span v-if="loading" class="spin edu-btn-spinner"></span>
    <span class="edu-btn-content" :style="{ opacity: loading ? 0 : 1 }">
      <slot></slot>
    </span>
  </button>
</template>

<script setup>
defineProps({
  variant: {
    type: String,
    default: 'primary', // primary, ghost, danger, success
  },
  size: {
    type: String,
    default: 'md', // sm, md, lg
  },
  loading: {
    type: Boolean,
    default: false,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  fullWidth: {
    type: Boolean,
    default: false,
  }
});
</script>

<style scoped>
.edu-btn {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-family: var(--font-base);
  font-weight: 600;
  border: none;
  cursor: pointer;
  transition: all 0.22s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  box-sizing: border-box;
}

/* Base Styles */
.edu-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none !important;
  box-shadow: none !important;
}

.is-full {
  width: 100%;
}

.edu-btn-spinner {
  position: absolute;
  left: 50%;
  top: 50%;
  margin-left: -0.5em;
  margin-top: -0.5em;
}

/* Sizes */
.size-sm {
  padding: 6px 14px;
  font-size: 13px;
  border-radius: var(--radius-sm);
}
.size-md {
  padding: 10px 20px;
  font-size: 14px;
  border-radius: 8px;
}
.size-lg {
  padding: 14px 28px;
  font-size: 16px;
  border-radius: 10px;
}

/* Variants */
.variant-primary {
  background: var(--accent-primary);
  color: white;
  box-shadow: 0 2px 8px rgba(0,0,0,0.2);
}
.variant-primary:hover:not(:disabled) {
  background: var(--accent-hover);
  transform: translateY(-1px);
  box-shadow: var(--shadow-glow);
}
.variant-primary:active:not(:disabled) {
  transform: translateY(1px);
}

.variant-ghost {
  background: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
}
.variant-ghost:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-primary);
}

.variant-danger {
  background: var(--status-danger);
  color: white;
}
.variant-danger:hover:not(:disabled) {
  filter: brightness(1.1);
  box-shadow: 0 4px 14px rgba(239, 68, 68, 0.3);
}

.variant-success {
  background: var(--status-success);
  color: white;
}
.variant-success:hover:not(:disabled) {
  filter: brightness(1.1);
  box-shadow: 0 4px 14px rgba(16, 185, 129, 0.3);
}
</style>
