// src/apis/configs/axiosConfig.ts
import axios, { AxiosResponse, AxiosError, InternalAxiosRequestConfig } from "axios";
import { TokenStorage } from "@/lib/utils/security";

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

// Debug: Log environment configuration
console.log('🔧 [API Config] Initializing axios with:');
console.log('  - VITE_API_BASE_URL:', import.meta.env.VITE_API_BASE_URL);
console.log('  - Final baseURL:', import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api");
console.log('  - Environment mode:', import.meta.env.MODE);

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
    const fullURL = `${config.baseURL}${config.url}`;
    const needsAuth = requiresAuth(config.url || '');
    
    console.log('📤 [API Request]', {
      method: config.method?.toUpperCase(),
      url: config.url,
      fullURL,
      baseURL: config.baseURL,
      requiresAuth: needsAuth,
      hasToken: !!TokenStorage.getAccessToken()
    });
    
    // Only add auth header for protected endpoints
    if (needsAuth) {
      const token = TokenStorage.getAccessToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
        console.log('🔐 [Auth] Token added to request');
      } else {
        console.warn('⚠️ [Auth] Protected endpoint but no token available');
      }
    } else {
      console.log('🌐 [Public] Public endpoint, no auth required');
    }
    
    return config;
  },
  (error) => {
    console.error('❌ [Request Error]', error);
    return Promise.reject(error);
  }
);

api.interceptors.response.use(
  (response: AxiosResponse) => {
    console.log('📥 [API Response]', {
      status: response.status,
      url: response.config.url,
      method: response.config.method?.toUpperCase()
    });
    return response;
  },
  async (error: AxiosError) => {
    const status = error.response?.status;
    const config = error.config as InternalAxiosRequestConfig;
    
    console.error('❌ [API Error]', {
      status,
      url: config?.url,
      method: config?.method?.toUpperCase(),
      message: error.message,
      isNetworkError: !error.response
    });
    
    // Only handle 401 for protected endpoints
    if (status === 401 && requiresAuth(config?.url || '')) {
      console.log('🔄 [Auth] 401 detected on protected endpoint, attempting token refresh');
      const refreshToken = TokenStorage.getRefreshToken();
      
      if (refreshToken && !config._retry) {
        config._retry = true; // Prevent infinite retry loop
        console.log('🔄 [Token Refresh] Starting token refresh...');
        
        try {
          const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api";
          console.log('🔄 [Token Refresh] Using API_BASE_URL:', API_BASE_URL);
          
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
          console.log('✅ [Token Refresh] Success! Retrying original request');
          
          // Retry original request with new token
          config.headers.Authorization = `Bearer ${newToken}`;
          return api.request(config);
          
        } catch (refreshError) {
          console.error('❌ [Token Refresh] Failed:', refreshError);
          // Refresh failed, clear tokens and redirect to login
          TokenStorage.clearTokens();
          console.log('🚪 [Auth] Redirecting to login...');
          // Only redirect if we're not already on login page
          if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
            window.location.href = "/login";
          }
        }
      } else {
        console.log('🚪 [Auth] No refresh token or retry exhausted, redirecting to login');
        // No refresh token or already retried, clear tokens
        TokenStorage.clearTokens();
        // Only redirect if we're not already on login page
        if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
          window.location.href = "/login";
        }
      }
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
