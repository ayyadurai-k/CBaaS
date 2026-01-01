/**
 * Modern useProfile Hook with Redux Integration
 * 
 * This hook replaces the original useProfile hook and provides:
 * - Centralized state management
 * - Automatic synchronization across components
 * - Optimistic updates
 * - Better error handling
 * - Caching and performance optimizations
 */

import { useEffect } from 'react';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import {
  selectUserProfile,
  selectUserLoading,
  selectUserUpdating,
  selectUserUploadingPicture,
  selectUserError,
  selectProfilePictureVersion,
  selectUserInitials,
  selectUserDisplayName,
  selectUserAvatarUrl,
} from '@/store/slices/userSlice';
import { selectIsAuthenticated } from '@/store/slices/authSlice';
import {
  fetchUserProfile,
  updateUserProfile,
  uploadUserProfilePicture,
  deleteUserProfilePicture,
} from '@/store/thunks/userThunks';
import { UpdateProfilePayload } from '@/apis/UsersAPI';

export const useProfile = () => {
  const dispatch = useAppDispatch();
  
  // Select state from Redux store
  const profile = useAppSelector(selectUserProfile);
  const isLoading = useAppSelector(selectUserLoading);
  const isUpdating = useAppSelector(selectUserUpdating);
  const isUploadingPicture = useAppSelector(selectUserUploadingPicture);
  const error = useAppSelector(selectUserError);
  const profilePictureVersion = useAppSelector(selectProfilePictureVersion);
  const isAuthenticated = useAppSelector(selectIsAuthenticated);
  
  // Computed selectors
  const initials = useAppSelector(selectUserInitials);
  const displayName = useAppSelector(selectUserDisplayName);
  const avatarUrl = useAppSelector(selectUserAvatarUrl);

  // Load profile on mount if authenticated and not loaded
  useEffect(() => {
    if (isAuthenticated && !profile && !isLoading) {
      dispatch(fetchUserProfile());
    }
  }, [isAuthenticated, profile, isLoading, dispatch]);

  // Action handlers
  const updateProfile = async (payload: UpdateProfilePayload): Promise<boolean> => {
    try {
      await dispatch(updateUserProfile(payload)).unwrap();
      return true;
    } catch (error) {
      return false;
    }
  };

  const uploadProfilePicture = async (file: File): Promise<boolean> => {
    try {
      await dispatch(uploadUserProfilePicture(file)).unwrap();
      return true;
    } catch (error) {
      return false;
    }
  };

  const deleteProfilePicture = async (): Promise<boolean> => {
    try {
      await dispatch(deleteUserProfilePicture()).unwrap();
      return true;
    } catch (error) {
      return false;
    }
  };

  const refetchProfile = async (): Promise<void> => {
    await dispatch(fetchUserProfile());
  };

  return {
    // State
    profile,
    isLoading,
    isUpdating,
    isUploadingPicture,
    error,
    profilePictureVersion,
    
    // Computed values
    initials,
    displayName,
    avatarUrl,
    
    // Actions
    updateProfile,
    uploadProfilePicture,
    deleteProfilePicture,
    refetchProfile,
  };
};
