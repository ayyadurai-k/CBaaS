// src/apis/configs/axiosConfig.ts
import axios, { AxiosResponse, AxiosError, InternalAxiosRequestConfig } from "axios";
import { TokenStorage } from "../../lib/utils/security";

// Define public endpoints that don't require authentication
const PUBLIC_ENDPOINTS = [
  "/auth/signup/",
  "/auth/login/",
  "/auth/token/refresh/",
  "/auth/password-reset/",
  "/auth/password-reset/confirm/",
  "/auth/check-email/",
  "/health/",
  "/docs/",
];

/**
 * Checks if endpoint requires authentication
 * @param url - The request URL
 * @returns boolean indicating if auth is required
 */
const requiresAuth = (url: string): boolean => {
  if (!url) return false;
  
  // Extract path from full URL if needed
  const path = url.startsWith('http') ? new URL(url).pathname : url;
  
  return !PUBLIC_ENDPOINTS.some(endpoint => path.startsWith(endpoint));
};

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api",
  withCredentials: true,
  headers: { 
    "Content-Type": "application/json",
    "Accept": "application/json"
  },
  timeout: 10000,
});

// Request interceptor - only add auth token for protected endpoints
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Only add auth header for protected endpoints
    if (requiresAuth(config.url || '')) {
      const token = TokenStorage.getAccessToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    
    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error: AxiosError) => {
    const status = error.response?.status;
    const config = error.config as InternalAxiosRequestConfig;
    
    // Only handle 401 for protected endpoints
    if (status === 401 && requiresAuth(config?.url || '')) {
      const refreshToken = TokenStorage.getRefreshToken();
      
      if (refreshToken && !config._retry) {
        config._retry = true; // Prevent infinite retry loop
        
        try {
          const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api";
          const refreshResponse = await axios.post(`${API_BASE_URL}/auth/token/refresh/`, {
            refresh: refreshToken,
          }, {
            withCredentials: true,
            headers: {
              "Content-Type": "application/json",
              "Accept": "application/json"
            }
          });
          
          const newToken = refreshResponse.data.access;
          TokenStorage.setTokens(newToken, refreshToken);
          
          // Retry original request with new token
          config.headers.Authorization = `Bearer ${newToken}`;
          return api.request(config);
          
        } catch (refreshError) {
          // Refresh failed, clear tokens and redirect to login
          TokenStorage.clearTokens();
          // Only redirect if we're not already on login page
          if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
            window.location.href = "/login";
          }
        }
      } else {
        // No refresh token or already retried, clear tokens
        TokenStorage.clearTokens();
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

// Extend AxiosRequestConfig to include retry flag
declare module 'axios' {
  export interface InternalAxiosRequestConfig {
    _retry?: boolean;
  }
}
