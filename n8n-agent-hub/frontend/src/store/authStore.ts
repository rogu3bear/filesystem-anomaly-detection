import { create } from 'zustand';
import axios from 'axios';

interface User {
  id: string;
  name: string;
  email: string;
  role: string;
  subscription: {
    plan: string;
    validUntil?: string;
    features: {
      maxAgents: number;
      customModels: boolean;
      advancedAnalytics: boolean;
    };
  };
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<void>;
  clearErrors: () => void;
}

// API URL from environment or default
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:3000/api';

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  token: localStorage.getItem('token'),
  isAuthenticated: false,
  loading: false,
  error: null,

  login: async (email, password) => {
    set({ loading: true, error: null });
    try {
      const response = await axios.post(`${API_URL}/auth/login`, {
        email,
        password,
      });

      const { token, user } = response.data.data;

      // Save token to localStorage
      localStorage.setItem('token', token);

      // Set auth header for future requests
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;

      set({
        token,
        user,
        isAuthenticated: true,
        loading: false,
      });
    } catch (error: any) {
      set({
        error: error.response?.data?.error?.message || 'Login failed',
        loading: false,
      });
    }
  },

  register: async (name, email, password) => {
    set({ loading: true, error: null });
    try {
      const response = await axios.post(`${API_URL}/auth/register`, {
        name,
        email,
        password,
      });

      const { token, user } = response.data.data;

      // Save token to localStorage
      localStorage.setItem('token', token);

      // Set auth header for future requests
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;

      set({
        token,
        user,
        isAuthenticated: true,
        loading: false,
      });
    } catch (error: any) {
      set({
        error: error.response?.data?.error?.message || 'Registration failed',
        loading: false,
      });
    }
  },

  logout: () => {
    // Remove token from localStorage
    localStorage.removeItem('token');

    // Remove auth header
    delete axios.defaults.headers.common['Authorization'];

    set({
      token: null,
      user: null,
      isAuthenticated: false,
    });
  },

  checkAuth: async () => {
    const token = get().token;
    
    if (!token) {
      set({ isAuthenticated: false });
      return;
    }

    set({ loading: true });
    
    try {
      // Set auth header
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      
      // Get current user
      const response = await axios.get(`${API_URL}/auth/me`);
      
      set({
        user: response.data.data,
        isAuthenticated: true,
        loading: false,
      });
    } catch (error) {
      // If the token is invalid, clear everything
      localStorage.removeItem('token');
      delete axios.defaults.headers.common['Authorization'];
      
      set({
        token: null,
        user: null,
        isAuthenticated: false,
        loading: false,
      });
    }
  },

  clearErrors: () => {
    set({ error: null });
  },
})); 