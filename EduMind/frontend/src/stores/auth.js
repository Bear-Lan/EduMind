import { defineStore } from 'pinia';
import api from '../utils/api';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('em_token') || '',
    user: null, // Will hold basic user info like { student_id, username }
    config: JSON.parse(localStorage.getItem('em_cfg') || '{"apiKey":"","baseUrl":"https://api.deepseek.com/v1","model":"deepseek-chat"}')
  }),

  getters: {
    isAuthenticated: (state) => !!state.token,
  },

  actions: {
    async login(username, password) {
      try {
        const response = await api.post('/auth/login', { username, password });
        this.setToken(response.data.access_token);
        return true;
      } catch (error) {
        throw error;
      }
    },

    async register(userData) {
      try {
        const response = await api.post('/auth/register', userData);
        this.setToken(response.data.access_token);
        return true;
      } catch (error) {
        throw error;
      }
    },

    setToken(token) {
      this.token = token;
      localStorage.setItem('em_token', token);
    },

    logout() {
      this.token = '';
      this.user = null;
      localStorage.removeItem('em_token');
    },

    updateConfig(newConfig) {
      this.config = { ...this.config, ...newConfig };
      localStorage.setItem('em_cfg', JSON.stringify(this.config));
    }
  }
});
