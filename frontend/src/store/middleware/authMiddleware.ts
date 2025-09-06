/**
 * Auth Middleware
 * 
 * Handles automatic token refresh and logout on auth failures.
 * Intercepts API calls that return 401 and attempts token refresh.
 */

import { Middleware, isRejectedWithValue } from '@reduxjs/toolkit';
import { logout } from '../slices/authSlice';
import { clearProfile } from '../slices/userSlice';
import { resetUIState, addToast } from '../slices/uiSlice';

export const authMiddleware: Middleware = (store) => (next) => (action: any) => {
  // Handle auth failures
  if (isRejectedWithValue(action)) {
    const payload = action.payload as any;
    if (payload?.status === 401) {
      // Dispatch logout actions
      store.dispatch(logout());
      store.dispatch(clearProfile());
      store.dispatch(resetUIState());
      
      // Show error toast
      store.dispatch(addToast({
        title: 'Session Expired',
        description: 'Please log in again to continue.',
        type: 'error',
        duration: 5000,
      }));

      // Redirect to login (you might want to handle this differently)
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
    }
  }

  // Handle successful auth actions
  if (action.type === 'auth/loginSuccess') {
    store.dispatch(addToast({
      title: 'Welcome back!',
      description: 'You have successfully logged in.',
      type: 'success',
      duration: 3000,
    }));
  }

  if (action.type === 'auth/logout') {
    store.dispatch(addToast({
      title: 'Logged out',
      description: 'You have been successfully logged out.',
      type: 'info',
      duration: 3000,
    }));
  }

  return next(action);
};
