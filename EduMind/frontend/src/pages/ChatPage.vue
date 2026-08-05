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
              :key="ref.title || i"
              class="ref-chip"
            >
              <div class="ref-num">{{ i + 1 }}</div>
              <div class="ref-body">
                <div class="ref-title">{{ ref.title || '参考资料' }}</div>
                <div class="ref-source" v-if="ref.source">📖 {{ ref.source }}</div>
                <div class="ref-source" v-if="ref.topic">🏷 {{ ref.topic }}</div>
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
const messagesContainer = ref(null);
const textareaRef = ref(null);
const backendLlmConfigured = ref(false);
const hasApiKey = backendLlmConfigured;

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
      messages.value = res.data;
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
    const res = await api.post('/chat', { message: text });
    
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
.ref-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 2px;
}
.ref-source {
  font-size: 10px;
  color: var(--text-secondary);
  margin-top: 1px;
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
