/**
 * Modern useAuth Hook with Redux Integration
 * 
 * Manages authentication state with Redux integration:
 * - Login/logout functionality
 * - Token management
 * - Auth state persistence
 * - Route protection utilities
 */

import { useAppDispatch, useAppSelector } from '@/store/hooks';
import {
  selectAuth,
  selectIsAuthenticated,
  selectAccessToken,
  selectAuthLoading,
  selectAuthError,
  loginStart,
  loginSuccess,
  loginFailure,
  logout as logoutAction,
  clearError,
} from '@/store/slices/authSlice';
import { clearProfile } from '@/store/slices/userSlice';
import { resetUIState } from '@/store/slices/uiSlice';
import { useLoginMutation, useLogoutMutation } from '@/store/services/authApi';

export const useAuth = () => {
  const dispatch = useAppDispatch();
  const [loginMutation] = useLoginMutation();
  const [logoutMutation] = useLogoutMutation();
  
  // Select state from Redux store
  const auth = useAppSelector(selectAuth);
  const isAuthenticated = useAppSelector(selectIsAuthenticated);
  const accessToken = useAppSelector(selectAccessToken);
  const isLoading = useAppSelector(selectAuthLoading);
  const error = useAppSelector(selectAuthError);

  // Login function
  const login = async (email: string, password: string): Promise<boolean> => {
    try {
      dispatch(loginStart());
      
      const result = await loginMutation({ email, password }).unwrap();
      
      dispatch(loginSuccess({
        accessToken: result.access_token,
        refreshToken: result.refresh_token,
      }));
      
      return true;
    } catch (error: any) {
      const message = error.data?.message || 'Login failed';
      dispatch(loginFailure(message));
      return false;
    }
  };

  // Logout function
  const logout = async (): Promise<void> => {
    try {
      // Call logout API
      await logoutMutation().unwrap();
    } catch (error) {
      // Even if API call fails, we still logout locally
      console.warn('Logout API call failed, logging out locally');
    } finally {
      // Clear all state
      dispatch(logoutAction());
      dispatch(clearProfile());
      dispatch(resetUIState());
    }
  };

  // Clear error function
  const clearAuthError = () => {
    dispatch(clearError());
  };

  // Check if user has specific role
  const hasRole = (role: string): boolean => {
    // You would need to store user role in auth state or get it from profile
    return false; // Implement based on your auth structure
  };

  // Check if user is admin
  const isAdmin = (): boolean => {
    return hasRole('admin');
  };

  return {
    // State
    auth,
    isAuthenticated,
    accessToken,
    isLoading,
    error,
    
    // Actions
    login,
    logout,
    clearAuthError,
    
    // Utilities
    hasRole,
    isAdmin,
  };
};
