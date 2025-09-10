/**
 * Auth Redux Thunks
 * 
 * Redux thunks for authentication using our existing AuthService.
 * This maintains consistency with our service layer architecture.
 */

import { createAsyncThunk } from '@reduxjs/toolkit';
import { authService, AuthUser } from '@/services/auth/AuthService';

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  user: AuthUser;
  accessToken: string;
  refreshToken?: string;
}

// Login thunk
export const loginThunk = createAsyncThunk<
  LoginResponse,
  LoginRequest,
  { rejectValue: string }
>(
  'auth/login',
  async (credentials, { rejectWithValue }) => {
    try {
      const result = await authService.login(credentials);
      if (result.success && result.user) {
        return {
          user: result.user,
          accessToken: authService.getAccessToken() || '',
          refreshToken: localStorage.getItem('refresh_token') || undefined,
        };
      } else {
        return rejectWithValue(result.message || 'Login failed');
      }
    } catch (error: any) {
      return rejectWithValue(error.message || 'Login failed');
    }
  }
);

// Logout thunk
export const logoutThunk = createAsyncThunk<
  void,
  void,
  { rejectValue: string }
>(
  'auth/logout',
  async (_, { rejectWithValue }) => {
    try {
      await authService.logout();
    } catch (error: any) {
      return rejectWithValue(error.message || 'Logout failed');
    }
  }
);

// Refresh token thunk
export const refreshTokenThunk = createAsyncThunk<
  string,
  void,
  { rejectValue: string }
>(
  'auth/refreshToken',
  async (_, { rejectWithValue }) => {
    try {
      const success = await authService.refreshToken();
      if (success) {
        return authService.getAccessToken() || '';
      } else {
        return rejectWithValue('Token refresh failed');
      }
    } catch (error: any) {
      return rejectWithValue(error.message || 'Token refresh failed');
    }
  }
);
