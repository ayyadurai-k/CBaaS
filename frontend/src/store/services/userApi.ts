/**
 * User API Service
 * 
 * RTK Query service for user-related API calls.
 * Provides automatic caching, background updates, and optimistic updates.
 * 
 * @see https://redux-toolkit.js.org/rtk-query/overview
 */

import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import { UserDTO, UpdateProfilePayload } from '@/apis/UsersAPI';
import { RootState } from '../index';

// Base query with auth header
const baseQuery = fetchBaseQuery({
  baseUrl: '/api', // Adjust based on your API base URL
  prepareHeaders: (headers, { getState }) => {
    // Get token from Redux state
    const state = getState() as RootState;
    const token = state.auth?.accessToken;
    
    if (token) {
      headers.set('authorization', `Bearer ${token}`);
    }
    
    return headers;
  },
});

export const userApi = createApi({
  reducerPath: 'userApi',
  baseQuery,
  tagTypes: ['User'],
  endpoints: (builder) => ({
    // Get user profile
    getProfile: builder.query<UserDTO, void>({
      query: () => '/user/profile',
      providesTags: ['User'],
      // Stale time: data is considered fresh for 5 minutes
      keepUnusedDataFor: 300,
    }),

    // Update profile
    updateProfile: builder.mutation<UserDTO, UpdateProfilePayload>({
      query: (payload) => ({
        url: '/user/profile',
        method: 'PUT',
        body: payload,
      }),
      invalidatesTags: ['User'],
      // Optimistic update
      async onQueryStarted(payload, { dispatch, queryFulfilled }) {
        const patchResult = dispatch(
          userApi.util.updateQueryData('getProfile', undefined, (draft) => {
            Object.assign(draft, payload);
          })
        );
        try {
          await queryFulfilled;
        } catch {
          patchResult.undo();
        }
      },
    }),

    // Upload profile picture
    uploadProfilePicture: builder.mutation<UserDTO, File>({
      query: (file) => {
        const formData = new FormData();
        formData.append('profile_picture', file);
        
        return {
          url: '/user/profile/picture',
          method: 'POST',
          body: formData,
        };
      },
      invalidatesTags: ['User'],
    }),

    // Delete profile picture
    deleteProfilePicture: builder.mutation<UserDTO, void>({
      query: () => ({
        url: '/user/profile/picture',
        method: 'DELETE',
      }),
      invalidatesTags: ['User'],
    }),

    // Refresh profile (manual trigger)
    refreshProfile: builder.mutation<UserDTO, void>({
      query: () => '/user/profile',
      invalidatesTags: ['User'],
    }),
  }),
});

// Export hooks for use in components
export const {
  useGetProfileQuery,
  useUpdateProfileMutation,
  useUploadProfilePictureMutation,
  useDeleteProfilePictureMutation,
  useRefreshProfileMutation,
  
  // Utility exports
  util: userApiUtil,
} = userApi;

// Export endpoints for use in thunks if needed
export const userApiEndpoints = userApi.endpoints;
