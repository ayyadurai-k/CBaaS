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
import { loginThunk, logoutThunk, checkAuthStatusThunk, refreshTokenThunk } from '../services/authApi';

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
    // Clear error
    clearError: (state) => {
      state.error = null;
    },

    // Set loading state
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },

    // Manual logout (for immediate local logout)
    logout: (state) => {
      state.isAuthenticated = false;
      state.accessToken = null;
      state.refreshToken = null;
      state.isLoading = false;
      state.error = null;
      state.lastLoginTime = null;
    },
  },
  extraReducers: (builder) => {
    // Login thunk
    builder
      .addCase(loginThunk.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(loginThunk.fulfilled, (state, action) => {
        state.isAuthenticated = true;
        state.accessToken = action.payload.accessToken;
        state.refreshToken = action.payload.refreshToken || null;
        state.isLoading = false;
        state.error = null;
        state.lastLoginTime = Date.now();
      })
      .addCase(loginThunk.rejected, (state, action) => {
        state.isAuthenticated = false;
        state.accessToken = null;
        state.refreshToken = null;
        state.isLoading = false;
        state.error = action.payload || 'Login failed';
        state.lastLoginTime = null;
      })

    // Logout thunk
    builder
      .addCase(logoutThunk.pending, (state) => {
        state.isLoading = true;
      })
      .addCase(logoutThunk.fulfilled, (state) => {
        state.isAuthenticated = false;
        state.accessToken = null;
        state.refreshToken = null;
        state.isLoading = false;
        state.error = null;
        state.lastLoginTime = null;
      })
      .addCase(logoutThunk.rejected, (state) => {
        // Even if logout API fails, clear local state
        state.isAuthenticated = false;
        state.accessToken = null;
        state.refreshToken = null;
        state.isLoading = false;
        state.error = null;
        state.lastLoginTime = null;
      })

    // Check auth status thunk
    builder
      .addCase(checkAuthStatusThunk.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(checkAuthStatusThunk.fulfilled, (state, action) => {
        if (action.payload.authenticated) {
          state.isAuthenticated = true;
          // Keep existing tokens if available
          if (!state.accessToken) {
            state.accessToken = localStorage.getItem('access_token');
          }
        } else {
          state.isAuthenticated = false;
          state.accessToken = null;
          state.refreshToken = null;
        }
        state.isLoading = false;
        state.error = null;
      })
      .addCase(checkAuthStatusThunk.rejected, (state, action) => {
        state.isAuthenticated = false;
        state.accessToken = null;
        state.refreshToken = null;
        state.isLoading = false;
        state.error = action.payload || 'Auth check failed';
      })

    // Refresh token thunk
    builder
      .addCase(refreshTokenThunk.fulfilled, (state, action) => {
        state.accessToken = action.payload;
        state.error = null;
      })
      .addCase(refreshTokenThunk.rejected, (state) => {
        state.isAuthenticated = false;
        state.accessToken = null;
        state.refreshToken = null;
      });
  },
});

// Action creators
export const {
  clearError,
  setLoading,
  logout,
} = authSlice.actions;

// Export thunks for use in components
export { loginThunk, logoutThunk, checkAuthStatusThunk, refreshTokenThunk };

// Selectors
export const selectAuth = (state: { auth: AuthState }) => state.auth;
export const selectIsAuthenticated = (state: { auth: AuthState }) => state.auth.isAuthenticated;
export const selectAccessToken = (state: { auth: AuthState }) => state.auth.accessToken;
export const selectAuthLoading = (state: { auth: AuthState }) => state.auth.isLoading;
export const selectAuthError = (state: { auth: AuthState }) => state.auth.error;

export default authSlice.reducer;
