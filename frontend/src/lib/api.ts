// src/lib/api.ts
import axios, { AxiosInstance, AxiosResponse, AxiosError } from "axios";

// Use Vite env; fallback for local dev
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

console.log("API_BASE_URL:", API_BASE_URL);

// Create axios instance
export const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor to add auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for error handling
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
          window.location.href = "/login";
        }
      } else {
        // No refresh token, redirect to login
        window.location.href = "/login";
      }
    }
    
    return Promise.reject(error);
  }
);

export default api;
