<template>
  <div class="analytics-page">
    <div v-if="loading" class="loading-state">
      <span class="spin"></span> 正在拉取多维数据面板...
    </div>

    <div v-else class="bento-grid">
      <!-- Top Row -->
      <div class="bento-box stats-summary">
        <h3 class="box-title">📊 学习总览</h3>
        <div class="stats-row">
          <div class="stat-item">
            <div class="stat-val">{{ totalMinutes }} <span class="stat-unit">分钟</span></div>
            <div class="stat-label">近7天总学习时长</div>
          </div>
          <div class="stat-item">
            <div class="stat-val">{{ masteredTopicsCount }} <span class="stat-unit">个</span></div>
            <div class="stat-label">已掌握知识点</div>
          </div>
        </div>
      </div>

      <!-- Main Row -->
      <div class="bento-box radar-box">
        <h3 class="box-title">🎯 知识点掌握度 (Radar)</h3>
        <div class="chart-container">
          <Radar :data="radarData" :options="radarOptions" />
        </div>
      </div>

      <div class="bento-box trend-box">
        <h3 class="box-title">📈 近7天学习时长趋势 (Line)</h3>
        <div class="chart-container">
          <Line :data="lineData" :options="lineOptions" />
        </div>
      </div>

      <div class="bento-box distribution-box">
        <h3 class="box-title">⏱️ 耗时分布 (Doughnut)</h3>
        <div class="chart-container">
          <Doughnut :data="doughnutData" :options="doughnutOptions" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useLearningStore } from '../stores/learning';
import api from '../utils/api';

import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
  CategoryScale,
  LinearScale,
  ArcElement
} from 'chart.js';
import { Radar, Line, Doughnut } from 'vue-chartjs';

ChartJS.register(
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
  CategoryScale,
  LinearScale,
  ArcElement
);

const learningStore = useLearningStore();
const loading = ref(true);
const analyticsData = ref(null);

onMounted(async () => {
  await fetchAnalytics();
});

async function fetchAnalytics() {
  loading.value = true;
  try {
    const res = await api.get('/analytics/dashboard');
    analyticsData.value = res.data;
  } catch (err) {
    console.error("Failed to load analytics", err);
  } finally {
    loading.value = false;
  }
}

// Summary Metrics
const totalMinutes = computed(() => {
  if (!analyticsData.value) return 0;
  return analyticsData.value.trend.durations_minutes.reduce((a, b) => a + b, 0);
});

const masteredTopicsCount = computed(() => {
  if (!analyticsData.value) return 0;
  return Object.values(analyticsData.value.mastery_map).filter(score => score >= 0.8).length;
});

// Common Chart Options for Dark Theme
const commonOptions = {
  responsive: true,
  maintainAspectRatio: false,
  color: '#c4b5fd',
  plugins: {
    legend: {
      labels: { color: '#c4b5fd' }
    }
  }
};

// Radar Chart
const radarData = computed(() => {
  const rawMap = analyticsData.value?.mastery_map || {};
  const profile = learningStore.profile || {};
  const prefs = profile.learning_preferences || {};
  const curricula = prefs.curricula || {};
  const currentSubj = profile.subject;
  
  // Filter map to only include topics from the current subject
  const map = {};
  if (currentSubj && curricula[currentSubj]) {
    const curriculum = curricula[currentSubj];
    for (const key in rawMap) {
      if (key in curriculum) {
        map[key] = rawMap[key];
      }
    }
  } else {
    Object.assign(map, rawMap); // fallback if no curriculum
  }

  const labels = Object.keys(map).map(k => learningStore.topicsMap[k] || k);
  const data = Object.values(map).map(v => Math.round(v * 100));

  if (labels.length === 0) {
    labels.push('暂无数据');
    data.push(0);
  }

  return {
    labels,
    datasets: [{
      label: '掌握度 (%)',
      backgroundColor: 'rgba(167, 139, 250, 0.2)',
      borderColor: '#a78bfa',
      pointBackgroundColor: '#a78bfa',
      pointBorderColor: '#fff',
      pointHoverBackgroundColor: '#fff',
      pointHoverBorderColor: '#a78bfa',
      data
    }]
  };
});

const radarOptions = {
  ...commonOptions,
  scales: {
    r: {
      angleLines: { color: 'rgba(255, 255, 255, 0.1)' },
      grid: { color: 'rgba(255, 255, 255, 0.1)' },
      pointLabels: { color: '#e2e8f0', font: { size: 12 } },
      ticks: { 
        display: false,
        min: 0,
        max: 100
      }
    }
  }
};

// Line Chart
const lineData = computed(() => {
  const trend = analyticsData.value?.trend || { dates: [], durations_minutes: [] };
  // Format dates to MM-DD
  const labels = trend.dates.map(d => d.substring(5));
  
  return {
    labels,
    datasets: [{
      label: '学习时长 (分钟)',
      backgroundColor: 'rgba(16, 185, 129, 0.1)',
      borderColor: '#10b981',
      borderWidth: 2,
      pointBackgroundColor: '#10b981',
      fill: true,
      tension: 0.4,
      data: trend.durations_minutes
    }]
  };
});

const lineOptions = {
  ...commonOptions,
  scales: {
    x: {
      grid: { color: 'rgba(255, 255, 255, 0.05)' },
      ticks: { color: '#94a3b8' }
    },
    y: {
      grid: { color: 'rgba(255, 255, 255, 0.05)' },
      ticks: { color: '#94a3b8' },
      beginAtZero: true
    }
  }
};

// Doughnut Chart
const doughnutData = computed(() => {
  const dist = analyticsData.value?.distribution || { labels: [], durations_minutes: [] };
  return {
    labels: dist.labels,
    datasets: [{
      backgroundColor: ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b'],
      borderColor: 'rgba(15, 17, 33, 1)',
      borderWidth: 2,
      hoverOffset: 4,
      data: dist.durations_minutes
    }]
  };
});

const doughnutOptions = {
  ...commonOptions,
  plugins: {
    legend: {
      position: 'right',
      labels: { color: '#e2e8f0' }
    }
  }
};
</script>

<style scoped>
.analytics-page {
  height: 100%;
  padding: 24px;
  overflow-y: auto;
}

.loading-state {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  font-size: 16px;
}
.spin {
  display: inline-block;
  width: 20px;
  height: 20px;
  border: 2px solid var(--text-secondary);
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-right: 12px;
}

.bento-grid {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.bento-box {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 20px;
  padding: 24px;
  backdrop-filter: blur(12px);
  display: flex;
  flex-direction: column;
}

.box-title {
  font-size: 16px;
  font-weight: 700;
  color: #fff;
  margin-bottom: 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  padding-bottom: 12px;
}

.chart-container {
  flex: 1;
  position: relative;
  min-height: 250px;
}

/* Specific Grid Placements */
.stats-summary {
  grid-column: span 12;
}

.radar-box {
  grid-column: span 4;
}

.trend-box {
  grid-column: span 8;
}

.distribution-box {
  grid-column: span 12;
  height: 350px;
}

.stats-row {
  display: flex;
  gap: 40px;
}
.stat-item {
  display: flex;
  flex-direction: column;
}
.stat-val {
  font-size: 42px;
  font-weight: 900;
  background: linear-gradient(135deg, #a78bfa, #3b82f6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.stat-unit {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-secondary);
  -webkit-text-fill-color: initial;
}
.stat-label {
  font-size: 14px;
  color: var(--text-secondary);
  margin-top: 4px;
}

@media (max-width: 1024px) {
  .radar-box, .trend-box {
    grid-column: span 12;
  }
}
</style>
