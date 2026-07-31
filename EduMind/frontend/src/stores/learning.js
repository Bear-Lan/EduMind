import { defineStore } from 'pinia';
import api from '../utils/api';

export const useLearningStore = defineStore('learning', {
  state: () => ({
    profile: null,
    plan: null,
    topicsMap: {}, // Maps english topic key to chinese name
    loadingProfile: false,
    loadingPlan: false,
  }),

  actions: {
    async fetchProfile() {
      this.loadingProfile = true;
      try {
        const res = await api.get('/profile');
        this.profile = res.data;
        
        // Extract chinese topic names if available
        const prefs = this.profile?.learning_preferences || {};
        const curricula = prefs.curricula || {};
        const currentSubj = this.profile?.subject;
        if (currentSubj && curricula[currentSubj]) {
          this.topicsMap = curricula[currentSubj].__zh_names__ || {};
        }
      } catch (err) {
        console.error('Failed to fetch profile', err);
      } finally {
        this.loadingProfile = false;
      }
    },

    async fetchCurrentPlan() {
      this.loadingPlan = true;
      try {
        const res = await api.get('/plan/current');
        this.plan = res.data;
      } catch (err) {
        console.error('Failed to fetch plan', err);
        this.plan = null; // No current plan
      } finally {
        this.loadingPlan = false;
      }
    },

    async generatePlan(topicId = null) {
      this.loadingPlan = true;
      try {
        const url = topicId ? `/plan/generate?target_topic=${encodeURIComponent(topicId)}` : '/plan/generate';
        const res = await api.post(url);
        this.plan = res.data;
        // Regenerating a plan usually updates the profile goal
        await this.fetchProfile();
      } catch (err) {
        console.error('Failed to generate plan', err);
        alert('生成学习计划失败: ' + (err.message || '请检查右上角是否已配置正确的 API Key，或者检查后端运行日志。'));
        throw err;
      } finally {
        this.loadingPlan = false;
      }
    },

    async completeStep(planId, stepNumber, score) {
      try {
        await api.post('/learning/complete', {
          plan_id: planId,
          step_number: stepNumber,
          score,
          duration: 300 // mock duration
        });
        // Refresh everything
        await this.fetchProfile();
        await this.fetchCurrentPlan();
      } catch (err) {
        console.error('Failed to complete step', err);
        throw err;
      }
    }
  }
});
