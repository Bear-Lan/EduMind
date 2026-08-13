<template>
  <div class="chat-page">
    <div class="chat-messages" ref="messagesContainer">
      <!-- Welcome Message -->
      <div class="message coach">
        <div class="bubble md-content">
          <p>你好！我是 EduMind AI 学习教练 👋</p>
          <p>你可以向我提问任何问题，我会用启发式方式一步一步引导你思考，不会直接给出答案。</p>
          
          <div class="quick-actions">
            <button class="quick-btn" @click="sendQuickAction('帮我用生活中的例子解释一下刚才的知识点。')">💡 生活化举例</button>
            <button class="quick-btn" @click="sendQuickAction('给我出一道这方面的练习题。')">📝 出一道题</button>
            <button class="quick-btn" @click="sendQuickAction('我还没太懂，能换个角度再讲讲吗？')">🔄 换个角度</button>
          </div>

          <p v-if="!hasApiKey" style="color: var(--status-warning); margin-top: 12px; font-size: 13px;">
            ⚠️ 当前未配置真实的 API Key，我将使用模拟回复。点击右上角 [配置] 填入密钥即可体验完整功能。
          </p>
        </div>
      </div>

      <!-- Chat History -->
      <div 
        v-for="(msg, idx) in messages" 
        :key="idx" 
        class="message" 
        :class="msg.role"
      >
        <div class="bubble md-content" v-html="msg.role === 'coach' ? renderMarkdown(msg.content) : escapeHtml(msg.content)"></div>
        <div v-if="msg.references && msg.references.length" class="refs">
          <div class="refs-header">
            <span class="refs-icon">📚</span>
            <span class="refs-title">参考教辅资料（来自 RAG 检索）</span>
          </div>
          <div class="ref-list">
            <div
              v-for="(ref, i) in msg.references"
              :key="ref.id || ref.title || i"
              class="ref-chip"
              :class="{ expanded: isRefExpanded(idx, i) }"
            >
              <div class="ref-num">{{ i + 1 }}</div>
              <div class="ref-body">
                <div class="ref-top">
                  <div class="ref-title">{{ ref.title || '参考资料' }}</div>
                  <span v-if="ref.score != null" class="ref-score" :title="'相关度 ' + formatScore(ref.score)">
                    {{ formatScore(ref.score) }}
                  </span>
                </div>
                <div class="ref-meta">
                  <span v-if="ref.parent_doc || ref.source">📖 {{ ref.parent_doc || ref.source }}</span>
                  <span v-if="ref.chapter">· {{ ref.chapter }}</span>
                  <span v-if="ref.section">· {{ ref.section }}</span>
                  <span v-if="ref.subject">· {{ ref.subject }}</span>
                  <span v-if="ref.chunk_index != null">· chunk#{{ Number(ref.chunk_index) + 1 }}</span>
                </div>
                <p v-if="ref.snippet && !isRefExpanded(idx, i)" class="ref-snippet">
                  {{ ref.snippet }}
                </p>
                <div v-if="isRefExpanded(idx, i) && ref.content" class="ref-full">
                  {{ ref.content }}
                </div>
                <button
                  v-if="ref.content || ref.snippet"
                  type="button"
                  class="ref-toggle"
                  @click="toggleRef(idx, i)"
                >
                  {{ isRefExpanded(idx, i) ? '收起原文' : '展开原文' }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Loading indicator -->
      <div v-if="isTyping" class="message coach">
        <div class="bubble typing-indicator">
          <span class="spin"></span> 教练思考中...
        </div>
      </div>
    </div>

    <!-- Input Area -->
    <div class="chat-input-area">
      <!-- Socratic mode toggle -->
      <div class="mode-bar">
        <label class="mode-toggle" :class="{ active: socraticMode }" :title="socraticMode ? '苏格拉底模式已开启：教练不会直接给答案，而是用提问引导你推理' : '点击开启苏格拉底模式'">
          <input type="checkbox" v-model="socraticMode" class="mode-checkbox" />
          <span class="mode-indicator"></span>
          <span class="mode-label">🧠 苏格拉底引导</span>
        </label>
        <span v-if="socraticMode" class="mode-hint">教练不会直接给答案，而是用提问引导你思考</span>
      </div>
      <form @submit.prevent="sendMessage" class="chat-form">
        <textarea
          v-model="inputText"
          class="chat-input"
          placeholder="向教练提问... (Shift+Enter换行, Enter发送)"
          @keydown="handleKeydown"
          rows="1"
          ref="textareaRef"
          :disabled="isTyping"
        ></textarea>
        <EduButton 
          type="submit" 
          variant="primary" 
          class="send-btn"
          :disabled="!inputText.trim() || isTyping"
        >
          ➔
        </EduButton>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue';
import { marked } from 'marked';
import hljs from 'highlight.js';
import 'highlight.js/styles/atom-one-dark.css'; // Add syntax highlighting theme
import api from '../utils/api';
import { renderMarkdown } from '../utils/markdown';
import EduButton from '../components/EduButton.vue';

// Configure marked to use highlight.js
marked.setOptions({
  highlight: function(code, lang) {
    const language = hljs.getLanguage(lang) ? lang : 'plaintext';
    return hljs.highlight(code, { language }).value;
  },
  langPrefix: 'hljs language-', // highlight.js css expects a top-level 'hljs' class.
});

const messages = ref([]);
const inputText = ref('');
const isTyping = ref(false);
const socraticMode = ref(false);
const messagesContainer = ref(null);
const textareaRef = ref(null);
const backendLlmConfigured = ref(false);
const hasApiKey = backendLlmConfigured;
/** messageIdx -> Set(refIdx) */
const expandedRefs = ref({});

function refKey(msgIdx, refIdx) {
  return `${msgIdx}:${refIdx}`;
}

function isRefExpanded(msgIdx, refIdx) {
  return !!expandedRefs.value[refKey(msgIdx, refIdx)];
}

function toggleRef(msgIdx, refIdx) {
  const key = refKey(msgIdx, refIdx);
  expandedRefs.value = {
    ...expandedRefs.value,
    [key]: !expandedRefs.value[key],
  };
}

function formatScore(score) {
  const n = Number(score);
  if (Number.isNaN(n)) return '';
  return `${Math.round(n * 100)}%`;
}

onMounted(async () => {
  await Promise.all([loadHistory(), checkLlmConfig()]);
  scrollToBottom();
});

async function checkLlmConfig() {
  try {
    const res = await api.get('/health');
    backendLlmConfigured.value = res.data?.llm === 'ok';
  } catch (err) {
    console.warn('Failed to check backend LLM configuration:', err);
  }
}

async function loadHistory() {
  try {
    const res = await api.get('/chat/history');
    if (res.data && res.data.length > 0) {
      // API returns role='assistant', template expects 'coach' for Markdown rendering
      messages.value = res.data.map(m => ({
        ...m,
        role: m.role === 'assistant' ? 'coach' : m.role,
      }));
    }
  } catch (err) {
    console.error('Failed to load chat history:', err);
  }
}

async function sendQuickAction(text) {
  inputText.value = text;
  await sendMessage();
}

async function sendMessage() {
  const text = inputText.value.trim();
  if (!text || isTyping.value) return;

  // Add user message
  messages.value.push({
    role: 'user',
    content: text
  });
  
  inputText.value = '';
  isTyping.value = true;
  resetTextareaHeight();
  await scrollToBottom();

  try {
    const res = await api.post('/chat', {
      message: text,
      mode: socraticMode.value ? 'socratic' : 'normal',
    });
    
    messages.value.push({
      role: 'coach',
      content: res.data.response,
      references: res.data.references || []
    });
  } catch (err) {
    messages.value.push({
      role: 'coach',
      content: `⚠️ 发送失败: ${err.message}`
    });
  } finally {
    isTyping.value = false;
    await scrollToBottom();
  }
}

function handleKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  } else {
    // Auto resize
    nextTick(resizeTextarea);
  }
}

function resizeTextarea() {
  const el = textareaRef.value;
  if (!el) return;
  el.style.height = '38px';
  el.style.height = Math.min(el.scrollHeight, 150) + 'px';
}

function resetTextareaHeight() {
  if (textareaRef.value) {
    textareaRef.value.style.height = '38px';
  }
}

async function scrollToBottom() {
  await nextTick();
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
  }
}

function escapeHtml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\n/g, '<br>');
}
</script>

<style scoped>
.chat-page {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message {
  display: flex;
  flex-direction: column;
  max-width: 90%;
}

.message.user {
  align-self: flex-end;
}

.message.coach {
  align-self: flex-start;
}

.bubble {
  padding: 12px 16px;
  border-radius: var(--radius-md);
  font-size: 14px;
}

.message.user .bubble {
  background: var(--accent-primary);
  color: white;
  border-bottom-right-radius: 4px;
}

.message.coach .bubble {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border-color);
  border-bottom-left-radius: 4px;
}

.typing-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-secondary);
}

.refs {
  margin-top: 12px;
  padding: 12px 14px;
  background: linear-gradient(135deg, rgba(99,102,241,0.08), rgba(167,139,250,0.05));
  border: 1px solid rgba(99,102,241,0.25);
  border-radius: 10px;
  font-size: 12px;
  color: var(--text-secondary);
}
.refs-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
  font-weight: 600;
  color: var(--text-primary);
}
.refs-icon { font-size: 14px; }
.refs-title { font-size: 12px; }
.ref-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.ref-chip {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  background: rgba(255, 255, 255, 0.04);
  padding: 8px 10px;
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  transition: all 0.2s;
}
.ref-chip:hover {
  background: rgba(99, 102, 241, 0.12);
  border-color: rgba(99, 102, 241, 0.4);
}
.ref-chip.expanded {
  border-color: rgba(167, 139, 250, 0.45);
  background: rgba(99, 102, 241, 0.1);
}
.ref-num {
  flex-shrink: 0;
  width: 22px;
  height: 22px;
  background: var(--accent-primary);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
}
.ref-body { flex: 1; min-width: 0; }
.ref-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
}
.ref-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 2px;
}
.ref-score {
  flex-shrink: 0;
  font-size: 10px;
  font-weight: 700;
  color: #a7f3d0;
  background: rgba(16, 185, 129, 0.15);
  border: 1px solid rgba(52, 211, 153, 0.35);
  padding: 1px 6px;
  border-radius: 999px;
}
.ref-meta {
  font-size: 10px;
  color: var(--text-secondary);
  margin-top: 2px;
  line-height: 1.4;
}
.ref-snippet {
  margin: 6px 0 0;
  font-size: 11px;
  line-height: 1.55;
  color: #cbd5e1;
}
.ref-full {
  margin-top: 8px;
  padding: 10px;
  border-radius: 8px;
  background: rgba(15, 23, 42, 0.55);
  border: 1px solid rgba(148, 163, 184, 0.18);
  font-size: 12px;
  line-height: 1.65;
  color: var(--text-primary);
  white-space: pre-wrap;
  max-height: 240px;
  overflow-y: auto;
}
.ref-toggle {
  margin-top: 6px;
  padding: 0;
  border: none;
  background: transparent;
  color: #c4b5fd;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
}
.ref-toggle:hover {
  color: #ddd6fe;
  text-decoration: underline;
}

.quick-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 16px;
}
.quick-btn {
  background: rgba(167, 139, 250, 0.1);
  border: 1px solid rgba(167, 139, 250, 0.3);
  color: #c4b5fd;
  padding: 6px 12px;
  border-radius: 16px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}
.quick-btn:hover {
  background: rgba(167, 139, 250, 0.2);
  transform: translateY(-1px);
}

.chat-input-area {
  padding: 16px;
  background: rgba(0, 0, 0, 0.2);
  border-top: 1px solid var(--border-color);
  flex-shrink: 0;
}

/* ── Socratic mode toggle ── */
.mode-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.mode-toggle {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  user-select: none;
  padding: 4px 12px;
  border-radius: var(--radius-full, 999px);
  border: 1px solid var(--border-color);
  background: rgba(255, 255, 255, 0.04);
  transition: all var(--transition-fast, 0.2s);
}

.mode-toggle.active {
  border-color: rgba(167, 139, 250, 0.5);
  background: rgba(167, 139, 250, 0.12);
}

.mode-checkbox {
  display: none;
}

.mode-indicator {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  border: 2px solid var(--text-secondary, #94a3b8);
  background: transparent;
  transition: all var(--transition-fast, 0.2s);
  flex-shrink: 0;
}

.mode-toggle.active .mode-indicator {
  border-color: #a78bfa;
  background: #a78bfa;
  box-shadow: 0 0 8px rgba(167, 139, 250, 0.5);
}

.mode-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary, #94a3b8);
  transition: color var(--transition-fast, 0.2s);
}

.mode-toggle.active .mode-label {
  color: #c4b5fd;
}

.mode-hint {
  font-size: 12px;
  color: var(--text-tertiary, #64748b);
}

.chat-form {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.chat-input {
  flex: 1;
  background: rgba(6, 8, 20, 0.9);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  padding: 10px 16px;
  border-radius: var(--radius-lg);
  outline: none;
  font-size: 14px;
  font-family: inherit;
  resize: none;
  min-height: 42px;
  max-height: 150px;
  line-height: 20px;
  transition: border-color var(--transition-fast);
}

.chat-input:focus {
  border-color: var(--accent-primary);
}

.send-btn {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
</style>
