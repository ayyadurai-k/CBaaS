// src/lib/api.ts
import axios, { AxiosError, AxiosInstance, AxiosRequestConfig, AxiosRequestHeaders } from "axios";
import { tokenStore } from "./auth/tokenStore";

// Use Vite env; fallback for local dev
const API_BASE_URL =
  import.meta?.env?.VITE_API_BASE_URL || "http://localhost:8000/api";

  console.log("API_BASE_URL ",API_BASE_URL);
  

// Create a dedicated axios instance for app calls
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
});

// A separate bare axios for refresh (to avoid interceptor recursion)
const raw: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 8000,
  withCredentials: true, // send the HttpOnly refresh cookie
});

// Single-flight refresh controller
let refreshPromise: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  try {
    // IMPORTANT (backend):
    // - Set refresh cookie as HttpOnly, Secure, SameSite=Lax(or Strict)
    // - Enable CORS with credentials for this endpoint if cross-origin
    //   Access-Control-Allow-Credentials: true
    //   Access-Control-Allow-Origin: https://your-frontend.example
    const res = await raw.post("/auth/refresh", {}); // cookie is sent via withCredentials
    const newToken = res.data?.accessToken;
    if (typeof newToken === "string" && newToken.length > 0) {
      tokenStore.set(newToken);
      return newToken;
    }
    return null;
  } catch {
    return null;
  } finally {
    refreshPromise = null;
  }
}

// Attach access token on every request (if present)
api.interceptors.request.use((config) => {
  const token = tokenStore.get();
  if (token) {
    if (config.headers) {
      (config.headers as Record<string, string>)["Authorization"] = `Bearer ${token}`;
    } else {
      config.headers = {} as AxiosRequestHeaders;
    }
    (config.headers as Record<string, string>)["Authorization"] = `Bearer ${token}`;
  }
  return config;
});

type RetriableConfig = AxiosRequestConfig & {
  _retry?: boolean;
  _skipAuthRefresh?: boolean;
};

api.interceptors.response.use(
  (res) => res,
  async (err: AxiosError) => {
    const status = err.response?.status;
    const original = (err.config || {}) as RetriableConfig;

    // If no response or already retried or this call explicitly skips refresh -> fail fast
    if (!status || original._retry || original._skipAuthRefresh) {
      return Promise.reject(err);
    }

    // Expired/unauthorized access token → try one refresh
    if (status === 401 || status === 419) {
      original._retry = true;

      try {
        if (!refreshPromise) {
          refreshPromise = refreshAccessToken();
        }
        const newToken = await refreshPromise;

        if (newToken) {
          // Retry original request with new token
          original.headers = {
            ...original.headers,
            Authorization: `Bearer ${newToken}`,
          };
          return api.request(original);
        }
      } catch {
        // fallthrough to logout
      }

      // Refresh failed → clear token and propagate error (UI can redirect to login)
      tokenStore.clear();
    }

    return Promise.reject(err);
  }
);

// Function to handle login API call
export async function login(email: string, password: string): Promise<{ success: boolean; message?: string }> {
  try {
    const response = await api.post('/auth/login/', { email, password });
    const token = response.data?.accessToken;
    if (token) {
      tokenStore.set(token);
      return { success: true };
    }
    return { success: false, message: 'Invalid response from server' };
  } catch (error: any) {
    return { success: false, message: error.response?.data?.message || 'Login failed' };
  }
}

export { api, tokenStore };
