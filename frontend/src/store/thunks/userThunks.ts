/**
 * User Thunks
 * 
 * Complex async operations for user management.
 * These thunks combine multiple actions and handle business logic.
 */

import { createAsyncThunk } from '@reduxjs/toolkit';
import { UsersAPI, UpdateProfilePayload } from '@/apis/UsersAPI';
import {
  fetchProfileStart,
  fetchProfileSuccess,
  fetchProfileFailure,
  updateProfileStart,
  updateProfileSuccess,
  updateProfileFailure,
  uploadPictureStart,
  uploadPictureSuccess,
  uploadPictureFailure,
  deletePictureStart,
  deletePictureSuccess,
  deletePictureFailure,
} from '../slices/userSlice';
import { addToast } from '../slices/uiSlice';

// Fetch user profile
export const fetchUserProfile = createAsyncThunk(
  'user/fetchProfile',
  async (_, { dispatch, rejectWithValue }) => {
    try {
      dispatch(fetchProfileStart());
      const response = await UsersAPI.getProfile();
      dispatch(fetchProfileSuccess(response.data));
      return response.data;
    } catch (error: any) {
      const message = error.response?.data?.message || 'Failed to fetch profile';
      dispatch(fetchProfileFailure(message));
      return rejectWithValue(message);
    }
  }
);

// Update user profile
export const updateUserProfile = createAsyncThunk(
  'user/updateProfile',
  async (payload: UpdateProfilePayload, { dispatch, rejectWithValue }) => {
    try {
      dispatch(updateProfileStart());
      const response = await UsersAPI.updateProfile(payload);
      dispatch(updateProfileSuccess(response.data));
      
      dispatch(addToast({
        title: 'Profile Updated',
        description: 'Your profile has been successfully updated.',
        type: 'success',
        duration: 3000,
      }));
      
      return response.data;
    } catch (error: any) {
      const message = error.response?.data?.message || 'Failed to update profile';
      dispatch(updateProfileFailure(message));
      
      dispatch(addToast({
        title: 'Update Failed',
        description: message,
        type: 'error',
        duration: 5000,
      }));
      
      return rejectWithValue(message);
    }
  }
);

// Upload profile picture
export const uploadUserProfilePicture = createAsyncThunk(
  'user/uploadProfilePicture',
  async (file: File, { dispatch, rejectWithValue }) => {
    try {
      dispatch(uploadPictureStart());
      const response = await UsersAPI.uploadProfilePicture(file);
      dispatch(uploadPictureSuccess(response.data));
      
      dispatch(addToast({
        title: 'Picture Updated',
        description: 'Your profile picture has been successfully updated.',
        type: 'success',
        duration: 3000,
      }));
      
      return response.data;
    } catch (error: any) {
      const message = error.response?.data?.message || 'Failed to upload profile picture';
      dispatch(uploadPictureFailure(message));
      
      dispatch(addToast({
        title: 'Upload Failed',
        description: message,
        type: 'error',
        duration: 5000,
      }));
      
      return rejectWithValue(message);
    }
  }
);

// Delete profile picture
export const deleteUserProfilePicture = createAsyncThunk(
  'user/deleteProfilePicture',
  async (_, { dispatch, rejectWithValue }) => {
    try {
      dispatch(deletePictureStart());
      const response = await UsersAPI.deleteProfilePicture();
      dispatch(deletePictureSuccess(response.data));
      
      dispatch(addToast({
        title: 'Picture Removed',
        description: 'Your profile picture has been successfully removed.',
        type: 'success',
        duration: 3000,
      }));
      
      return response.data;
    } catch (error: any) {
      const message = error.response?.data?.message || 'Failed to delete profile picture';
      dispatch(deletePictureFailure(message));
      
      dispatch(addToast({
        title: 'Delete Failed',
        description: message,
        type: 'error',
        duration: 5000,
      }));
      
      return rejectWithValue(message);
    }
  }
);
