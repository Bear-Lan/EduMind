<template>
  <div class="edu-input-wrapper" :class="{ 'has-error': !!error, 'is-focused': isFocused }">
    <label v-if="label" class="edu-input-label" :for="id">{{ label }}</label>
    
    <div class="edu-input-inner">
      <div v-if="$slots.prefix" class="edu-input-prefix">
        <slot name="prefix"></slot>
      </div>
      
      <input
        :id="id"
        :type="type"
        class="edu-input-field"
        :value="modelValue"
        :placeholder="placeholder"
        :disabled="disabled"
        :required="required"
        @input="$emit('update:modelValue', $event.target.value)"
        @focus="isFocused = true; $emit('focus', $event)"
        @blur="isFocused = false; $emit('blur', $event)"
        v-bind="$attrs"
      >
      
      <div v-if="$slots.suffix" class="edu-input-suffix">
        <slot name="suffix"></slot>
      </div>
    </div>
    
    <div v-if="error || hint" class="edu-input-msg" :class="{ 'is-error': !!error }">
      {{ error || hint }}
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';

defineProps({
  modelValue: {
    type: [String, Number],
    default: ''
  },
  label: String,
  type: {
    type: String,
    default: 'text'
  },
  placeholder: String,
  error: String,
  hint: String,
  disabled: Boolean,
  required: Boolean,
  id: {
    type: String,
    default: () => `input-${Math.random().toString(36).substring(2, 9)}`
  }
});

defineEmits(['update:modelValue', 'focus', 'blur']);

const isFocused = ref(false);
</script>

<style scoped>
.edu-input-wrapper {
  display: flex;
  flex-direction: column;
  margin-bottom: 16px;
  width: 100%;
}

.edu-input-label {
  font-size: 12px;
  font-weight: 700;
  color: var(--text-secondary);
  margin-bottom: 6px;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  transition: color var(--transition-fast);
}

.is-focused .edu-input-label {
  color: var(--accent-primary);
}

.edu-input-inner {
  position: relative;
  display: flex;
  align-items: center;
  background: rgba(6, 8, 20, 0.8);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
  overflow: hidden;
}

.is-focused .edu-input-inner {
  border-color: var(--accent-primary);
  box-shadow: 0 0 0 3px var(--accent-dim);
  background: rgba(12, 14, 29, 0.9);
}

.has-error .edu-input-inner {
  border-color: var(--status-danger);
}

.has-error.is-focused .edu-input-inner {
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.15);
}

.edu-input-field {
  flex: 1;
  width: 100%;
  background: transparent;
  border: none;
  color: var(--text-primary);
  padding: 12px 14px;
  font-size: 14px;
  font-family: inherit;
  outline: none;
}

.edu-input-field::placeholder {
  color: rgba(255, 255, 255, 0.2);
}

.edu-input-field:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.edu-input-prefix,
.edu-input-suffix {
  padding: 0 12px;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
}
.edu-input-prefix { padding-right: 0; }
.edu-input-suffix { padding-left: 0; }

.edu-input-msg {
  font-size: 11px;
  margin-top: 6px;
  color: var(--text-secondary);
  min-height: 16px;
}
.edu-input-msg.is-error {
  color: var(--status-danger);
}
</style>
