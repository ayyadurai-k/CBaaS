// src/apis/configs/axiosConfig.ts
import axios, { AxiosResponse, AxiosError } from "axios";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api",
  withCredentials: true,
  headers: { "Content-Type": "application/json" },
  timeout: 10000,
});

// Request interceptor to add auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for error handling and token refresh
api.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error: AxiosError) => {
    const status = error.response?.status;
    
    // Handle 401 unauthorized - token expired
    if (status === 401) {
      // Try to refresh token
      const refreshToken = localStorage.getItem("refresh_token");
      if (refreshToken) {
        try {
          const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api";
          const refreshResponse = await axios.post(`${API_BASE_URL}/auth/token/refresh/`, {
            refresh: refreshToken,
          });
          
          const newToken = refreshResponse.data.access;
          localStorage.setItem("access_token", newToken);
          
          // Retry original request with new token
          if (error.config) {
            error.config.headers.Authorization = `Bearer ${newToken}`;
            return api.request(error.config);
          }
        } catch (refreshError) {
          // Refresh failed, clear tokens and redirect to login
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          // Only redirect if we're not already on login page
          if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
            window.location.href = "/login";
          }
        }
      } else {
        // No refresh token, clear any remaining tokens
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        // Only redirect if we're not already on login page
        if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
          window.location.href = "/login";
        }
      }
    }
    
    // Log other errors (but not 401s to avoid spam during token refresh)
    if (status && status !== 401) {
      console.error("API Error:", error);
    }
    
    return Promise.reject(error);
  }
);
