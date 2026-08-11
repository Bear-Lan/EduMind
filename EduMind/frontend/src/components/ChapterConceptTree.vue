<template>
  <div class="skill-tree">
    <div v-if="loading" class="tree-empty">正在加载本章掌握度导图…</div>
    <div v-else-if="!root || !root.children?.length" class="tree-empty">
      本章暂无入库教辅要点。请确认已 seed 对应 topic 的学习资源。
    </div>
    <div v-else class="tree-stage">
      <div class="stage-top">
        <div class="legend">
          <span v-for="item in legend" :key="item.level" class="legend-item">
            <i class="swatch" :class="`lv-${item.level}`" />
            {{ item.label }}
          </span>
        </div>
        <button class="reset-btn" type="button" title="展开全部" @click="expandAll">⟲</button>
      </div>

      <div class="canvas-wrap" ref="wrapRef">
        <svg ref="svgRef" class="tree-svg" @click="onSvgClick" />
      </div>

      <div class="mastery-footer">
        MASTERY {{ masteryPercent }}%
      </div>
      <p class="hint">点击叶子末尾圆点展开「知识点精讲 / 例题练习」；完成精讲 +1，两道例题各 +1，合计 L3</p>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch, nextTick } from 'vue';
import { Markmap } from 'markmap-view';
import { Transformer } from 'markmap-lib';

const props = defineProps({
  root: { type: Object, default: null },
  loading: { type: Boolean, default: false },
});

const emit = defineEmits(['lecture', 'quiz']);

const legend = [
  { level: 0, label: '未开始' },
  { level: 1, label: '了解' },
  { level: 2, label: '熟练' },
  { level: 3, label: '精通' },
];

const svgRef = ref(null);
const wrapRef = ref(null);
let mm = null;
const transformer = new Transformer();

const MASTERY_COLORS = {
  0: '#64748b',
  1: '#6ee7b7',
  2: '#10b981',
  3: '#34d399',
};

function masteryColor(level) {
  return MASTERY_COLORS[level] || MASTERY_COLORS[0];
}

function shortText(text, max = 18) {
  const t = (text || '').replace(/^\d+\.\s*/, '').trim();
  if (t.length <= max) return t;
  return `${t.slice(0, max)}…`;
}

function escapeHtml(s) {
  return (s || '').replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[c]));
}

/** 把后端 concept tree 转成 markmap IPureNode；叶子末尾加可点击圆点，并挂精讲/例题子分支 */
function toPureNode(node, isLeaf = false) {
  const level = Number(node.level || 0);

  // 叶子：文案 + 圆点 + 虚拟子分支（精讲/例题）
  if (isLeaf || node.leaf) {
    const label = shortText(node.label, 26);
    const dot = `<span class="mm-dot" data-leaf-id="${escapeHtml(node.id)}" data-action="toggle" title="点击展开精讲/例题">●</span>`;
    const content = `<span class="mm-node lv-${level}" data-level="${level}">${escapeHtml(label)} ${dot}</span>`;

    const kids = (node.children || []).map((c) => {
      const done = c.done ? '✅ ' : '';
      const cLabel = `${done}${c.label}`;
      const action = c.virtual === 'lecture' ? 'lecture' : 'quiz';
      // quiz 虚拟子节点带 next_slot（1/2/null），让前端打开第一个未通关的题位
      const slotAttr = action === 'quiz' ? ` data-slot="${c.next_slot ?? ''}"` : '';
      return {
        content: `<span class="mm-virtual" data-leaf-id="${escapeHtml(c.leaf_id || node.id)}" data-action="${action}" data-virtual="${action}"${slotAttr}>${escapeHtml(cLabel)}</span>`,
        payload: { level: c.level || 0, virtual: action, leaf_id: c.leaf_id || node.id, next_slot: c.next_slot },
      };
    });

    return {
      content,
      payload: { level, id: node.id, isLeaf: true },
      children: kids,
    };
  }

  // 普通节点（root / branch）
  const label = shortText(node.label, 14);
  return {
    content: `<span class="mm-node lv-${level}" data-level="${level}">${escapeHtml(label)}</span>`,
    payload: { level, id: node.id },
    children: (node.children || []).map((c) => toPureNode(c, c.leaf === true)),
  };
}

function colorFn(node) {
  const lv = node?.payload?.level ?? 0;
  return masteryColor(lv);
}

function styleFn(id) {
  return `
#${id} .markmap-node text { fill: #e2e8f0; font-weight: 600; font-size: 12px; }
#${id} .markmap-node circle { stroke-width: 2; transition: all .3s ease; }
#${id} .markmap-link { stroke-width: 1.6; fill: none; opacity: .9; }
#${id} .mm-node.lv-0 { color: #94a3b8; }
#${id} .mm-node.lv-1 { color: #a7f3d0; }
#${id} .mm-node.lv-2 { color: #d1fae5; }
#${id} .mm-node.lv-3 { color: #ecfdf5; text-shadow: 0 0 8px rgba(52,211,153,.6); }
#${id} .mm-dot { color: #a78bfa; cursor: pointer; margin-left: 6px; font-size: 14px; }
#${id} .mm-dot:hover { color: #ddd6fe; text-shadow: 0 0 8px rgba(167,139,250,.8); }
#${id} .mm-virtual { color: #c4b5fd; cursor: pointer; text-decoration: underline; }
#${id} .mm-virtual:hover { color: #ddd6fe; }
  `.trim();
}

function buildOptions() {
  return {
    autoFit: true,
    initialExpandLevel: 3,
    color: colorFn,
    style: styleFn,
    duration: 300,
    maxWidth: 320,
    spacingHorizontal: 70,
    spacingVertical: 12,
    paddingX: 8,
  };
}

function initMarkmap() {
  if (!svgRef.value) return;
  mm = Markmap.create(svgRef.value, buildOptions());
  render();
}

function render() {
  if (!mm || !props.root) return;
  const pure = toPureNode(props.root, false);
  mm.setData(pure);
  mm.fit();
}

function expandAll() {
  if (!mm) return;
  mm.setOptions({ ...buildOptions(), initialExpandLevel: -1 });
  render();
}

/** 点击委托：识别 data-action 触发对应事件 */
function onSvgClick(e) {
  const target = e.target;
  if (!target) return;
  // SVG 中 HTML 内容会被渲染到 foreignObject 内的 span
  const el = target.closest?.('[data-action]') || target;
  const action = el.getAttribute?.('data-action');
  const leafId = el.getAttribute?.('data-leaf-id');
  if (!action || !leafId) return;

  if (action === 'toggle') {
    // 让 markmap 折叠/展开该叶子的子分支：模拟点击节点
    // markmap 自身点击节点会 toggle，这里圆点在节点内，直接调用 toggleNode
    const node = findMarkmapNodeByLeafId(leafId);
    if (node && mm) {
      mm.toggleNode(node);
    }
    return;
  }
  if (action === 'lecture') {
    emit('lecture', { leaf_id: leafId });
    return;
  }
  if (action === 'quiz') {
    const slotAttr = el.getAttribute('data-slot');
    const slot = slotAttr ? Number(slotAttr) : null;
    emit('quiz', { leaf_id: leafId, slot });
    return;
  }
}

function findMarkmapNodeByLeafId(leafId) {
  if (!mm?.state?.data) return null;
  let found = null;
  function walk(n) {
    if (n?.payload?.id === leafId && n?.payload?.isLeaf) {
      found = n;
      return;
    }
    for (const c of n?.children || []) {
      walk(c);
      if (found) return;
    }
  }
  walk(mm.state.data);
  return found;
}

onMounted(async () => {
  await nextTick();
  initMarkmap();
});

watch(
  () => props.root,
  () => {
    if (!mm) initMarkmap();
    else render();
  },
  { deep: false }
);

onBeforeUnmount(() => {
  mm = null;
});

const masteryPercent = computed(() => {
  const root = props.root;
  if (!root) return 0;
  const leaves = [];
  for (const b of root.children || []) {
    for (const leaf of b.children || []) {
      if (leaf.leaf) leaves.push(leaf);
    }
  }
  if (!leaves.length) return 0;
  const sum = leaves.reduce((acc, l) => acc + (l.level || 0), 0);
  return Math.round((sum / (leaves.length * 3)) * 100);
});
</script>

<style scoped>
.skill-tree {
  width: 100%;
}

.tree-empty {
  padding: 20px 12px;
  text-align: center;
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.5;
}

.tree-stage {
  width: 100%;
  background: rgba(12, 14, 29, 0.55);
  border-radius: 12px;
  padding: 8px 10px 6px;
  border: 1px solid rgba(167, 139, 250, 0.18);
  backdrop-filter: blur(8px);
  box-sizing: border-box;
}

.stage-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 4px;
}

.legend {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 10px;
  font-size: 10px;
  color: var(--text-secondary);
}
.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}
.swatch {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  display: inline-block;
}
.swatch.lv-0 { background: #64748b; }
.swatch.lv-1 { background: #6ee7b7; box-shadow: 0 0 8px rgba(110, 231, 183, 0.45); }
.swatch.lv-2 { background: #10b981; box-shadow: 0 0 10px rgba(16, 185, 129, 0.5); }
.swatch.lv-3 { background: #34d399; box-shadow: 0 0 12px rgba(52, 211, 153, 0.65); }

.reset-btn {
  width: 24px;
  height: 24px;
  border-radius: 999px;
  border: 1px solid rgba(167, 139, 250, 0.28);
  background: rgba(167, 139, 250, 0.08);
  color: #c4b5fd;
  cursor: pointer;
  font-size: 12px;
  line-height: 1;
  flex-shrink: 0;
}
.reset-btn:hover {
  background: rgba(167, 139, 250, 0.18);
  border-color: rgba(167, 139, 250, 0.5);
  color: #ddd6fe;
}

.canvas-wrap {
  width: 100%;
  height: min(46vh, 340px);
  overflow: auto;
}

.tree-svg {
  width: 100%;
  height: 100%;
  display: block;
  background: transparent;
}

.mastery-footer {
  margin-top: 4px;
  text-align: center;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.06em;
  color: #a7f3d0;
  text-shadow: 0 0 12px rgba(52, 211, 153, 0.35);
}

.hint {
  margin: 4px 0 0;
  text-align: center;
  font-size: 10px;
  color: var(--text-secondary);
}

:deep(.markmap-node text) {
  fill: #e2e8f0 !important;
}
:deep(.markmap-node circle) {
  stroke-width: 2;
}
:deep(.markmap-link) {
  stroke-width: 1.6;
  fill: none;
}
:deep(.mm-dot) {
  cursor: pointer;
}
:deep(.mm-virtual) {
  cursor: pointer;
}
</style>
