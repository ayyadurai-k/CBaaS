// src/apis/configs/axiosConfig.ts
import axios from "axios";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api",
  withCredentials: true,
  headers: { "Content-Type": "application/json" },
});

// Error handling interceptor
api.interceptors.response.use(
  (res) => res,
  (err) => {
    const status = err.response?.status;
    if (status && status !== 401) console.error("API Error:", err);
    return Promise.reject(err);
  }
);
