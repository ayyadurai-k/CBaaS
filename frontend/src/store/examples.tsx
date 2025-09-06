/**
 * Example: Redux Implementation Usage
 * 
 * This file demonstrates how to use the Redux implementation in components.
 * It shows the before/after comparison and common usage patterns.
 */

import React from 'react';
import { useProfile } from '@/hooks/redux/useProfile';
import { useAuth } from '@/hooks/redux/useAuth';
import { useAppSelector, useAppDispatch } from '@/store/hooks';
import { addToast } from '@/store/slices/uiSlice';

// ============================================================================
// EXAMPLE 1: Basic Profile Usage (Same as before, but now with Redux)
// ============================================================================

const ProfileExample: React.FC = () => {
  const { 
    profile, 
    isLoading, 
    updateProfile,
    displayName,
    initials,
    avatarUrl 
  } = useProfile();

  const handleUpdateName = async () => {
    const success = await updateProfile({ name: 'New Name' });
    if (success) {
      // ✅ This update will automatically reflect in:
      // - TopNavbar
      // - ProfilePage  
      // - Any other component using useProfile()
      console.log('Profile updated and synced everywhere!');
    }
  };

  if (isLoading) return <div>Loading...</div>;

  return (
    <div>
      <h1>Welcome, {displayName}</h1>
      <img src={avatarUrl || '/default-avatar.png'} alt="Avatar" />
      <p>Initials: {initials}</p>
      <button onClick={handleUpdateName}>Update Name</button>
    </div>
  );
};

// ============================================================================
// EXAMPLE 2: Authentication with Redux
// ============================================================================

const AuthExample: React.FC = () => {
  const { isAuthenticated, login, logout, isLoading } = useAuth();

  const handleLogin = async () => {
    const success = await login('user@example.com', 'password');
    if (success) {
      // ✅ Auth state is automatically persisted
      // ✅ User profile will be loaded automatically
      console.log('Logged in successfully!');
    }
  };

  const handleLogout = async () => {
    await logout();
    // ✅ All state is cleared (auth, user, UI)
    // ✅ User is redirected to login
  };

  return (
    <div>
      {isAuthenticated ? (
        <button onClick={handleLogout}>Logout</button>
      ) : (
        <button onClick={handleLogin} disabled={isLoading}>
          {isLoading ? 'Logging in...' : 'Login'}
        </button>
      )}
    </div>
  );
};

// ============================================================================
// EXAMPLE 3: Direct Redux Access (Advanced)
// ============================================================================

const AdvancedExample: React.FC = () => {
  const dispatch = useAppDispatch();
  
  // Direct state access
  const profile = useAppSelector(state => state.user.profile);
  const isUpdating = useAppSelector(state => state.user.isUpdating);
  const theme = useAppSelector(state => state.ui.theme);

  // Direct action dispatch
  const showToast = () => {
    dispatch(addToast({
      title: 'Hello!',
      description: 'This is a Redux toast',
      type: 'success',
      duration: 3000,
    }));
  };

  return (
    <div>
      <p>Theme: {theme}</p>
      <p>Profile: {profile?.name}</p>
      <p>Updating: {isUpdating ? 'Yes' : 'No'}</p>
      <button onClick={showToast}>Show Toast</button>
    </div>
  );
};

// ============================================================================
// EXAMPLE 4: Migration Guide - Before vs After
// ============================================================================

// ❌ BEFORE: Multiple API calls, no sync
const BeforeComponent = () => {
  // Each component makes its own API call
  // No automatic synchronization
  // Manual refetching required
  
  // In TopNavbar:
  // const { profile: navProfile } = useProfile(); // API call #1
  
  // In ProfilePage:
  // const { profile: pageProfile, updateProfile } = useProfile(); // API call #2
  
  // Problem: navProfile and pageProfile are different instances
  // Update in ProfilePage doesn't update TopNavbar
};

// ✅ AFTER: Single source of truth, automatic sync
const AfterComponent = () => {
  // All components share the same Redux state
  // Automatic synchronization everywhere
  // Optimistic updates
  
  // In TopNavbar:
  const { profile, displayName, avatarUrl } = useProfile(); // Redux state
  
  // In ProfilePage:
  const { profile: sameProfile, updateProfile } = useProfile(); // Same Redux state
  
  // ✅ profile === sameProfile (same object reference)
  // ✅ Updates in ProfilePage automatically reflect in TopNavbar
  
  return (
    <div>
      <p>This component uses the shared Redux state</p>
      <p>Any updates will be reflected everywhere automatically</p>
    </div>
  );
};

// ============================================================================
// EXAMPLE 5: Error Handling
// ============================================================================

const ErrorHandlingExample: React.FC = () => {
  const { profile, error, updateProfile } = useProfile();

  const handleUpdate = async () => {
    try {
      const success = await updateProfile({ name: 'New Name' });
      if (!success) {
        // Error is automatically handled and displayed via toast
        console.log('Update failed, but error is handled gracefully');
      }
    } catch (err) {
      // Additional custom error handling if needed
      console.error('Custom error handling:', err);
    }
  };

  return (
    <div>
      {error && <div className="error">Error: {error}</div>}
      <button onClick={handleUpdate}>Update Profile</button>
    </div>
  );
};

// ============================================================================
// EXAMPLE 6: Performance Optimization
// ============================================================================

const OptimizedComponent: React.FC = () => {
  // Only re-renders when displayName changes
  const displayName = useAppSelector(state => 
    state.user.profile?.name || 'Unknown'
  );
  
  // Only re-renders when isLoading changes
  const isLoading = useAppSelector(state => state.user.isLoading);

  // This component won't re-render if other user properties change
  return (
    <div>
      <h1>{displayName}</h1>
      {isLoading && <div>Loading...</div>}
    </div>
  );
};

export {
  ProfileExample,
  AuthExample,
  AdvancedExample,
  AfterComponent,
  ErrorHandlingExample,
  OptimizedComponent,
};
