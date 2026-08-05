import { defineStore } from 'pinia';
import api from '../utils/api';

// Model credentials are server-managed. Remove any legacy browser-stored key.
localStorage.removeItem('em_cfg');

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('em_token') || '',
    role: localStorage.getItem('em_role') || '',
    mustChangePassword: localStorage.getItem('em_admin_pwd_change') === '1',
    studentMustChangePassword: localStorage.getItem('em_student_pwd_change') === '1',
    user: null, // Will hold basic user info like { student_id, username }
  }),

  getters: {
    isAuthenticated: (state) => !!state.token,
    isAdmin: (state) => state.role === 'admin',
  },

  actions: {
    async login(username, password) {
      try {
        const response = await api.post('/auth/login', { username, password });
        this.setSession(response.data.access_token, 'student');
        this.studentMustChangePassword = Boolean(response.data.must_change_password);
        localStorage.setItem('em_student_pwd_change', this.studentMustChangePassword ? '1' : '0');
        return true;
      } catch (error) {
        throw error;
      }
    },

    async register(userData) {
      try {
        const response = await api.post('/auth/register', userData);
        this.setSession(response.data.access_token, 'student');
        this.studentMustChangePassword = false;
        localStorage.setItem('em_student_pwd_change', '0');
        return true;
      } catch (error) {
        throw error;
      }
    },

    async adminLogin(username, password) {
      const response = await api.post('/admin/login', { username, password });
      this.setSession(response.data.access_token, 'admin');
      this.mustChangePassword = Boolean(response.data.must_change_password);
      localStorage.setItem('em_admin_pwd_change', this.mustChangePassword ? '1' : '0');
      this.user = {
        username: response.data.username,
        displayName: response.data.display_name,
      };
      return response.data;
    },

    setSession(token, role) {
      this.token = token;
      this.role = role;
      localStorage.setItem('em_token', token);
      localStorage.setItem('em_role', role);
    },

    logout() {
      this.token = '';
      this.user = null;
      this.role = '';
      this.mustChangePassword = false;
      this.studentMustChangePassword = false;
      localStorage.removeItem('em_token');
      localStorage.removeItem('em_role');
      localStorage.removeItem('em_admin_pwd_change');
      localStorage.removeItem('em_student_pwd_change');
    }
  }
});
