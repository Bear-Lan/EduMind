<template>
  <div class="kg-page">
    <!-- Header -->
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">🕸️ 知识图谱</h2>
        <p class="page-subtitle">
          当前学科：<strong>{{ subject }}</strong> ·
          共 {{ nodes.length }} 个知识点 · {{ edges.length }} 条依赖关系
        </p>
      </div>
      <div class="header-actions">
        <button class="action-btn" @click="resetZoom">⟲ 重置视图</button>
        <button class="action-btn" @click="forceRun">⚡ 重新布局</button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading-state">
      <span class="spin"></span>
      <span>加载知识图谱中…</span>
    </div>

    <!-- Empty -->
    <div v-else-if="nodes.length === 0" class="empty-state">
      <div class="empty-icon">🌐</div>
      <h3>暂无图谱</h3>
      <p>请先在右上角切换到有知识点的学科</p>
    </div>

    <!-- Graph SVG -->
    <div v-else class="graph-wrapper">
      <svg
        ref="svgRef"
        :viewBox="`0 0 ${width} ${height}`"
        preserveAspectRatio="xMidYMid meet"
        @wheel.prevent="onWheel"
      >
        <!-- Arrow marker -->
        <defs>
          <marker
            id="arrow"
            viewBox="0 -5 10 10"
            refX="22"
            refY="0"
            markerWidth="6"
            markerHeight="6"
            orient="auto"
          >
            <path d="M0,-5L10,0L0,5" fill="rgba(167,139,250,0.6)" />
          </marker>
          <filter id="glow">
            <feGaussianBlur stdDeviation="3" result="b" />
            <feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
        </defs>

        <!-- Edges -->
        <g class="edges">
          <line
            v-for="(e, i) in renderEdges"
            :key="`e-${i}`"
            :x1="e.x1"
            :y1="e.y1"
            :x2="e.x2"
            :y2="e.y2"
            stroke="rgba(167,139,250,0.5)"
            stroke-width="1.6"
            marker-end="url(#arrow)"
          />
        </g>

        <!-- Nodes -->
        <g class="nodes">
          <g
            v-for="n in renderNodes"
            :key="n.id"
            :transform="`translate(${n.x},${n.y})`"
            class="node"
            @mouseenter="hover = n"
            @mouseleave="hover = null"
            @click="onNodeClick(n)"
          >
            <circle
              :r="n.radius"
              :fill="n.color"
              :stroke="n.stroke"
              stroke-width="2"
              :filter="hover === n ? 'url(#glow)' : ''"
            />
            <text
              v-if="n.label.length <= 12"
              text-anchor="middle"
              dy="0.3em"
              fill="white"
              font-size="11"
              font-weight="600"
            >{{ n.label }}</text>
            <text
              v-else
              text-anchor="middle"
              fill="white"
              font-size="10"
              font-weight="600"
            >
              <tspan x="0" dy="-0.3em">{{ n.label.slice(0, 12) }}</tspan>
              <tspan x="0" dy="1.2em">{{ n.label.slice(12, 24) }}</tspan>
            </text>
            <text
              text-anchor="middle"
              dy="2.4em"
              :fill="n.color"
              font-size="10"
              font-weight="700"
            >{{ Math.round(n.mastery * 100) }}%</text>
          </g>
        </g>
      </svg>

      <!-- Legend -->
      <div class="legend">
        <div class="legend-row">
          <span class="dot" style="background:#10b981"></span> 已掌握 ≥ 80%
        </div>
        <div class="legend-row">
          <span class="dot" style="background:#f59e0b"></span> 巩固中 50-80%
        </div>
        <div class="legend-row">
          <span class="dot" style="background:#ef4444"></span> 待加强 &lt; 50%
        </div>
        <div class="legend-row">
          <span class="dot" style="background:#6366f1"></span> 未接触
        </div>
        <div class="legend-tip">鼠标滚轮缩放 · 拖动节点 · 点击节点高亮</div>
      </div>

      <!-- Hover Tooltip -->
      <div
        v-if="hover"
        class="tooltip"
        :style="{
          left: hover.x + 30 + 'px',
          top: hover.y - 20 + 'px'
        }"
      >
        <div class="tt-title">{{ hover.label }}</div>
        <div class="tt-row">掌握度：<strong>{{ Math.round(hover.mastery * 100) }}%</strong></div>
        <div class="tt-row tt-status">状态：{{ hover.statusText }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue';
import api from '../utils/api';
import { useLearningStore } from '../stores/learning';

const learningStore = useLearningStore();

const loading = ref(true);
const subject = ref('');
const nodes = ref([]);
const edges = ref([]);
const hover = ref(null);

const svgRef = ref(null);
const width = 900;
const height = 600;

// 拖拽相关
const dragNode = ref(null);
const dragging = ref(false);
const dragOffset = ref({ x: 0, y: 0 });

// 缩放
const viewBox = ref(`0 0 ${width} ${height}`);
const scale = ref(1);
const panX = ref(0);
const panY = ref(0);

// 力导向：node.x / node.y 会随模拟更新
const renderNodes = ref([]);
const renderEdges = ref([]);

// 颜色映射
const colorFor = (mastery) => {
  if (mastery >= 0.8) return '#10b981';
  if (mastery >= 0.5) return '#f59e0b';
  if (mastery > 0) return '#ef4444';
  return '#6366f1';
};

const strokeFor = (mastery) => {
  if (mastery >= 0.8) return 'rgba(16, 185, 129, 0.5)';
  if (mastery >= 0.5) return 'rgba(245, 158, 11, 0.5)';
  if (mastery > 0) return 'rgba(239, 68, 68, 0.5)';
  return 'rgba(99, 102, 241, 0.5)';
};

const statusTextFor = (mastery) => {
  if (mastery >= 0.8) return '已掌握';
  if (mastery >= 0.5) return '巩固中';
  if (mastery > 0) return '需要加强';
  return '未接触';
};

// ───── 力导向布局（手写 d3-force 简化版） ─────
function forceLayout(nodesArr, edgesArr, iterations = 200) {
  const cx = width / 2;
  const cy = height / 2;
  const repulsion = 6000;   // 排斥力强度
  const linkDist = 130;     // 理想连边距离
  const linkStrength = 0.05;
  const centerStrength = 0.02;

  // 随机初始位置
  nodesArr.forEach((n, i) => {
    if (typeof n.x !== 'number') {
      n.x = cx + Math.cos(i * 0.5) * 150 + (Math.random() - 0.5) * 80;
      n.y = cy + Math.sin(i * 0.5) * 150 + (Math.random() - 0.5) * 80;
    }
    n.vx = 0;
    n.vy = 0;
  });

  for (let iter = 0; iter < iterations; iter++) {
    // 排斥力（Coulomb-like）
    for (let i = 0; i < nodesArr.length; i++) {
      for (let j = i + 1; j < nodesArr.length; j++) {
        const a = nodesArr[i];
        const b = nodesArr[j];
        let dx = a.x - b.x;
        let dy = a.y - b.y;
        let dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 1) {
          dx = (Math.random() - 0.5) * 0.1;
          dy = (Math.random() - 0.5) * 0.1;
          dist = 0.1;
        }
        const force = repulsion / (dist * dist);
        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;
        a.vx += fx;
        a.vy += fy;
        b.vx -= fx;
        b.vy -= fy;
      }
    }

    // 弹簧力（连边）
    const nodeMap = new Map(nodesArr.map(n => [n.id, n]));
    for (const e of edgesArr) {
      const a = nodeMap.get(e.source);
      const b = nodeMap.get(e.target);
      if (!a || !b) continue;
      const dx = b.x - a.x;
      const dy = b.y - a.y;
      const dist = Math.sqrt(dx * dx + dy * dy) || 1;
      const diff = dist - linkDist;
      const force = diff * linkStrength;
      const fx = (dx / dist) * force;
      const fy = (dy / dist) * force;
      a.vx += fx;
      a.vy += fy;
      b.vx -= fx;
      b.vy -= fy;
    }

    // 向心力
    for (const n of nodesArr) {
      n.vx += (cx - n.x) * centerStrength;
      n.vy += (cy - n.y) * centerStrength;
    }

    // 应用速度 + 阻尼
    const damping = 0.75;
    for (const n of nodesArr) {
      n.vx *= damping;
      n.vy *= damping;
      n.x += n.vx;
      n.y += n.vy;
      // 边界
      n.x = Math.max(40, Math.min(width - 40, n.x));
      n.y = Math.max(40, Math.min(height - 40, n.y));
    }
  }

  // 计算半径（按 mastery 大小）
  nodesArr.forEach(n => {
    n.radius = 18 + n.mastery * 16;
  });

  // 渲染边
  renderEdges.value = edgesArr.map(e => {
    const a = nodeMap.get(e.source);
    const b = nodeMap.get(e.target);
    if (!a || !b) return null;
    return {
      x1: a.x, y1: a.y, x2: b.x, y2: b.y,
    };
  }).filter(Boolean);
}

// 拖拽支持
function onPointerDown(e, n) {
  if (e.button !== 0) return;
  dragging.value = true;
  dragNode.value = n;
  const pt = svgPoint(e);
  dragOffset.value = { x: pt.x - n.x, y: pt.y - n.y };
  e.target.setPointerCapture?.(e.pointerId);
}
function onPointerMove(e) {
  if (!dragging.value || !dragNode.value) return;
  const pt = svgPoint(e);
  dragNode.value.x = pt.x - dragOffset.value.x;
  dragNode.value.y = pt.y - dragOffset.value.y;
  refreshRender();
}
function onPointerUp() {
  dragging.value = false;
  dragNode.value = null;
}
function svgPoint(e) {
  const svg = svgRef.value;
  const rect = svg.getBoundingClientRect();
  const scaleX = width / rect.width;
  const scaleY = height / rect.height;
  return {
    x: (e.clientX - rect.left) * scaleX,
    y: (e.clientY - rect.top) * scaleY,
  };
}

// 渲染节点（带颜色 / 状态）
function refreshRender() {
  renderNodes.value = nodes.value.map(n => ({
    ...n,
    color: colorFor(n.mastery),
    stroke: strokeFor(n.mastery),
    statusText: statusTextFor(n.mastery),
  }));
}

function resetZoom() {
  viewBox.value = `0 0 ${width} ${height}`;
}
function forceRun() {
  forceLayout(nodes.value, edges.value);
  refreshRender();
}
function onWheel(e) {
  // 简化：阻止浏览器默认
}
function onNodeClick(n) {
  hover.value = n;
  setTimeout(() => { if (hover.value?.id === n.id) hover.value = null; }, 3000);
}

// 数据加载
async function loadGraph() {
  loading.value = true;
  try {
    if (!learningStore.profile) {
      await learningStore.fetchProfile();
    }
    const res = await api.get('/knowledge-graph');
    subject.value = res.data.subject;
    // 浅拷贝避免被 forceLayout 改引用
    nodes.value = (res.data.nodes || []).map(n => ({ ...n }));
    edges.value = res.data.edges || [];
    await nextTick();
    forceLayout(nodes.value, edges.value);
    refreshRender();
  } catch (err) {
    console.error('Failed to load knowledge graph', err);
  } finally {
    loading.value = false;
  }
}

// 监听 subject 变化（学科切换后重新画图）
watch(() => learningStore.profile?.subject, () => {
  loadGraph();
});

onMounted(loadGraph);
</script>

<style scoped>
.kg-page {
  height: 100%;
  overflow: hidden;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 16px;
}
.page-title {
  font-size: 20px;
  font-weight: 800;
  margin: 0 0 4px;
  color: var(--text-primary);
}
.page-subtitle {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 0;
}
.header-actions {
  display: flex;
  gap: 8px;
}
.action-btn {
  background: rgba(99, 102, 241, 0.12);
  border: 1px solid rgba(99, 102, 241, 0.3);
  color: #c4b5fd;
  padding: 6px 14px;
  border-radius: 16px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}
.action-btn:hover {
  background: rgba(99, 102, 241, 0.2);
  border-color: var(--accent-primary);
}

.loading-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--text-secondary);
}
.spin {
  display: inline-block;
  width: 20px;
  height: 20px;
  border: 2px solid var(--border-color);
  border-top-color: var(--accent-primary);
  border-radius: 50%;
  animation: spin 0.75s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  color: var(--text-secondary);
}
.empty-icon { font-size: 52px; }
.empty-state h3 { color: var(--text-primary); margin: 0; }
.empty-state p { font-size: 14px; max-width: 300px; }

.graph-wrapper {
  flex: 1;
  position: relative;
  background: linear-gradient(135deg, rgba(15,17,33,0.6), rgba(20,24,40,0.4));
  border: 1px solid var(--border-color);
  border-radius: 14px;
  overflow: hidden;
  min-height: 500px;
}

.graph-wrapper svg {
  width: 100%;
  height: 100%;
  display: block;
  cursor: grab;
}

.node {
  cursor: pointer;
  transition: transform 0.15s;
}
.node:hover {
  transform: translate(var(--tx, 0), var(--ty, 0)) scale(1.08);
}

.legend {
  position: absolute;
  top: 16px;
  right: 16px;
  background: rgba(15, 17, 33, 0.92);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 12px 16px;
  font-size: 12px;
  color: var(--text-secondary);
  backdrop-filter: blur(8px);
}
.legend-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}
.legend-row:last-child { margin-bottom: 0; }
.dot {
  display: inline-block;
  width: 12px;
  height: 12px;
  border-radius: 50%;
}
.legend-tip {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid var(--border-color);
  font-size: 11px;
  color: var(--text-secondary);
}

.tooltip {
  position: absolute;
  background: rgba(15, 17, 33, 0.96);
  border: 1px solid var(--accent-primary);
  border-radius: 8px;
  padding: 10px 14px;
  pointer-events: none;
  font-size: 12px;
  z-index: 10;
  backdrop-filter: blur(8px);
  box-shadow: 0 4px 16px rgba(99, 102, 241, 0.3);
}
.tt-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 6px;
}
.tt-row {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 2px;
}
.tt-row strong { color: var(--text-primary); margin-left: 4px; }
.tt-status { font-weight: 600; }
</style>