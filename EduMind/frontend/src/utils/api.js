import axios from 'axios';
import { useAuthStore } from '../stores/auth';

// Create Axios instance
const api = axios.create({
  baseURL: 'http://127.0.0.1:8000/api/v1',
  timeout: 300000, // Increased to 5 minutes (300,000 ms) for slow LLM responses
});

// Request Interceptor: Add Token and API Key
api.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore();
    
    // Add Bearer token
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`;
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response Interceptor: Handle 401 and errors
api.interceptors.response.use(
  (response) => {
    // EduMind API wraps responses in { success, data, message, code }
    return response.data;
  },
  (error) => {
    const authStore = useAuthStore();
    
    if (error.response) {
      // Handle 401 Unauthorized globally
      if (error.response.status === 401) {
        authStore.logout();
        // The router should ideally handle the redirect, but doing it here is a fallback
        const adminArea = window.location.pathname.startsWith('/admin');
        const target = adminArea ? '/admin-login' : '/';
        if (window.location.pathname !== target) {
          window.location.href = target;
        }
      }
      
      // Extract backend error message if available
      const backendMessage = error.response.data?.message;
      if (backendMessage) {
        error.message = backendMessage;
      }
    } else if (error.request) {
      error.message = 'Network error: Cannot connect to server.';
    }
    
    return Promise.reject(error);
  }
);

export default api;
