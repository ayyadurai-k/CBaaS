/**
 * Authentication Slice
 * 
 * Manages authentication state including:
 * - User authentication status
 * - Access tokens
 * - Authentication loading states
 * - Login/logout actions
 * 
 * This slice is persisted to localStorage to maintain login state across sessions.
 */

import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface AuthState {
  isAuthenticated: boolean;
  accessToken: string | null;
  refreshToken: string | null;
  isLoading: boolean;
  error: string | null;
  lastLoginTime: number | null;
}

const initialState: AuthState = {
  isAuthenticated: false,
  accessToken: null,
  refreshToken: null,
  isLoading: false,
  error: null,
  lastLoginTime: null,
};

export const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    // Login actions
    loginStart: (state) => {
      state.isLoading = true;
      state.error = null;
    },
    loginSuccess: (state, action: PayloadAction<{
      accessToken: string;
      refreshToken?: string;
    }>) => {
      state.isAuthenticated = true;
      state.accessToken = action.payload.accessToken;
      state.refreshToken = action.payload.refreshToken || null;
      state.isLoading = false;
      state.error = null;
      state.lastLoginTime = Date.now();
    },
    loginFailure: (state, action: PayloadAction<string>) => {
      state.isAuthenticated = false;
      state.accessToken = null;
      state.refreshToken = null;
      state.isLoading = false;
      state.error = action.payload;
      state.lastLoginTime = null;
    },

    // Logout action
    logout: (state) => {
      state.isAuthenticated = false;
      state.accessToken = null;
      state.refreshToken = null;
      state.isLoading = false;
      state.error = null;
      state.lastLoginTime = null;
    },

    // Token refresh
    refreshTokenSuccess: (state, action: PayloadAction<string>) => {
      state.accessToken = action.payload;
      state.error = null;
    },

    // Clear error
    clearError: (state) => {
      state.error = null;
    },

    // Set loading state
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },

    // Auth status check actions
    checkAuthStart: (state) => {
      state.isLoading = true;
      state.error = null;
    },
    checkAuthSuccess: (state, action: PayloadAction<{
      accessToken: string;
      refreshToken?: string;
    }>) => {
      state.isAuthenticated = true;
      state.accessToken = action.payload.accessToken;
      state.refreshToken = action.payload.refreshToken || state.refreshToken;
      state.isLoading = false;
      state.error = null;
    },
    checkAuthFailure: (state) => {
      state.isAuthenticated = false;
      state.accessToken = null;
      state.refreshToken = null;
      state.isLoading = false;
      state.error = null;
    },
  },
});

// Action creators
export const {
  loginStart,
  loginSuccess,
  loginFailure,
  logout,
  refreshTokenSuccess,
  clearError,
  setLoading,
  checkAuthStart,
  checkAuthSuccess,
  checkAuthFailure,
} = authSlice.actions;

// Selectors
export const selectAuth = (state: { auth: AuthState }) => state.auth;
export const selectIsAuthenticated = (state: { auth: AuthState }) => state.auth.isAuthenticated;
export const selectAccessToken = (state: { auth: AuthState }) => state.auth.accessToken;
export const selectAuthLoading = (state: { auth: AuthState }) => state.auth.isLoading;
export const selectAuthError = (state: { auth: AuthState }) => state.auth.error;

export default authSlice.reducer;
