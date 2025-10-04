/**
 * User Redux Thunks
 * 
 * Redux thunks for user-related operations using our existing UsersService.
 * This maintains consistency with our service layer architecture.
 */

import { createAsyncThunk } from '@reduxjs/toolkit';
import { usersService, User } from '@/services/UsersService';
import { UpdateProfilePayload } from '@/apis/UsersAPI';

// Get user profile thunk
export const getUserProfileThunk = createAsyncThunk<
  User,
  void,
  { rejectValue: string }
>(
  'user/getProfile',
  async (_, { rejectWithValue }) => {
    try {
      const result = await usersService.getProfile();
      return result;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to fetch profile');
    }
  }
);

// Update profile thunk
export const updateProfileThunk = createAsyncThunk<
  User,
  UpdateProfilePayload,
  { rejectValue: string }
>(
  'user/updateProfile',
  async (payload, { rejectWithValue }) => {
    try {
      const result = await usersService.updateProfile(payload);
      return result;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to update profile');
    }
  }
);
