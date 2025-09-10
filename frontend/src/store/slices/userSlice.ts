/**
 * User Slice
 * 
 * Manages user profile data and user-related state including:
 * - User profile information
 * - Profile update states
 * - Profile picture management
 * - Organization data
 * 
 * This slice works with Redux thunks using our existing service layer.
 */

import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { UserDTO } from '@/apis/UsersAPI';
import { User } from '@/services/UsersService';
import { getUserProfileThunk, updateProfileThunk } from '../services/userApi';

export interface UserState {
  profile: User | null;
  isLoading: boolean;
  isUpdating: boolean;
  isUploadingPicture: boolean;
  error: string | null;
  profilePictureVersion: number;
  lastUpdated: number | null;
}

const initialState: UserState = {
  profile: null,
  isLoading: false,
  isUpdating: false,
  isUploadingPicture: false,
  error: null,
  profilePictureVersion: Date.now(),
  lastUpdated: null,
};

export const userSlice = createSlice({
  name: 'user',
  initialState,
  reducers: {
    // Update profile field (for optimistic updates)
    updateProfileField: (state, action: PayloadAction<Partial<User>>) => {
      if (state.profile) {
        state.profile = { ...state.profile, ...action.payload };
      }
    },

    // Clear error
    clearUserError: (state) => {
      state.error = null;
    },

    // Clear profile (on logout)
    clearProfile: (state) => {
      state.profile = null;
      state.isLoading = false;
      state.isUpdating = false;
      state.isUploadingPicture = false;
      state.error = null;
      state.lastUpdated = null;
    },

    // Update profile picture version (for cache busting)
    updateProfilePictureVersion: (state) => {
      state.profilePictureVersion = Date.now();
    },

    // Profile picture actions (for picture upload/delete operations)
    uploadPictureStart: (state) => {
      state.isUploadingPicture = true;
      state.error = null;
    },
    uploadPictureSuccess: (state, action: PayloadAction<User>) => {
      state.profile = action.payload;
      state.isUploadingPicture = false;
      state.error = null;
      state.profilePictureVersion = Date.now();
      state.lastUpdated = Date.now();
    },
    uploadPictureFailure: (state, action: PayloadAction<string>) => {
      state.isUploadingPicture = false;
      state.error = action.payload;
    },

    deletePictureStart: (state) => {
      state.isUploadingPicture = true;
      state.error = null;
    },
    deletePictureSuccess: (state, action: PayloadAction<User>) => {
      state.profile = action.payload;
      state.isUploadingPicture = false;
      state.error = null;
      state.profilePictureVersion = Date.now();
      state.lastUpdated = Date.now();
    },
    deletePictureFailure: (state, action: PayloadAction<string>) => {
      state.isUploadingPicture = false;
      state.error = action.payload;
    },
  },
  extraReducers: (builder) => {
    // Get user profile thunk
    builder
      .addCase(getUserProfileThunk.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(getUserProfileThunk.fulfilled, (state, action) => {
        state.profile = action.payload;
        state.isLoading = false;
        state.error = null;
        state.lastUpdated = Date.now();
      })
      .addCase(getUserProfileThunk.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload || 'Failed to fetch profile';
      })

    // Update profile thunk
    builder
      .addCase(updateProfileThunk.pending, (state) => {
        state.isUpdating = true;
        state.error = null;
      })
      .addCase(updateProfileThunk.fulfilled, (state, action) => {
        state.profile = action.payload;
        state.isUpdating = false;
        state.error = null;
        state.lastUpdated = Date.now();
      })
      .addCase(updateProfileThunk.rejected, (state, action) => {
        state.isUpdating = false;
        state.error = action.payload || 'Failed to update profile';
      });
  },
});

// Action creators
export const {
  updateProfileField,
  clearUserError,
  clearProfile,
  updateProfilePictureVersion,
  uploadPictureStart,
  uploadPictureSuccess,
  uploadPictureFailure,
  deletePictureStart,
  deletePictureSuccess,
  deletePictureFailure,
} = userSlice.actions;

// Export thunks for use in components
export { getUserProfileThunk, updateProfileThunk };

// Selectors
export const selectUser = (state: { user: UserState }) => state.user;
export const selectUserProfile = (state: { user: UserState }) => state.user.profile;
export const selectUserLoading = (state: { user: UserState }) => state.user.isLoading;
export const selectUserUpdating = (state: { user: UserState }) => state.user.isUpdating;
export const selectUserUploadingPicture = (state: { user: UserState }) => state.user.isUploadingPicture;
export const selectUserError = (state: { user: UserState }) => state.user.error;
export const selectProfilePictureVersion = (state: { user: UserState }) => state.user.profilePictureVersion;
export const selectUserLastUpdated = (state: { user: UserState }) => state.user.lastUpdated;

// Complex selectors
export const selectUserInitials = (state: { user: UserState }) => {
  const profile = state.user.profile;
  if (!profile?.name) return '';
  
  return profile.name
    .split(' ')
    .map(name => name.charAt(0))
    .join('')
    .toUpperCase()
    .slice(0, 2);
};

export const selectUserDisplayName = (state: { user: UserState }) => {
  const profile = state.user.profile;
  return profile?.name || 'Unknown User';
};

export const selectUserAvatarUrl = (state: { user: UserState }) => {
  const profile = state.user.profile;
  const version = state.user.profilePictureVersion;
  
  if (!profile?.profile_picture_url) return null;
  
  return `${profile.profile_picture_url}?v=${version}`;
};

export default userSlice.reducer;
