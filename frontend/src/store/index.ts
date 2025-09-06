/**
 * Redux Store Configuration
 * 
 * This file configures the Redux store using Redux Toolkit with best practices:
 * - Immutable state updates with Immer
 * - Built-in Redux DevTools integration
 * - RTK Query for efficient data fetching
 * - Type-safe throughout the application
 * 
 * @see https://redux-toolkit.js.org/tutorials/quick-start
 */

import { configureStore } from '@reduxjs/toolkit';
import { setupListeners } from '@reduxjs/toolkit/query';
import { persistStore, persistReducer } from 'redux-persist';
import storage from 'redux-persist/lib/storage';
import { combineReducers } from '@reduxjs/toolkit';

// Import slices
import authSlice from './slices/authSlice';
import userSlice from './slices/userSlice';
import uiSlice from './slices/uiSlice';

// Import RTK Query APIs
import { userApi } from './services/userApi';
import { authApi } from './services/authApi';

// Import middleware
import { authMiddleware } from './middleware/authMiddleware';

// Persist configuration
const persistConfig = {
  key: 'root',
  storage,
  whitelist: ['auth'], // Only persist auth slice
  blacklist: ['ui'], // Don't persist UI state
};

// Root reducer
const rootReducer = combineReducers({
  auth: authSlice,
  user: userSlice,
  ui: uiSlice,
  // RTK Query APIs
  [userApi.reducerPath]: userApi.reducer,
  [authApi.reducerPath]: authApi.reducer,
});

// Persisted reducer
const persistedReducer = persistReducer(persistConfig, rootReducer);

// Configure store
export const store = configureStore({
  reducer: persistedReducer,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST', 'persist/REHYDRATE'],
      },
    }).concat(
      userApi.middleware,
      authApi.middleware,
      authMiddleware
    ),
  devTools: process.env.NODE_ENV !== 'production',
});

// Create persistor
export const persistor = persistStore(store);

// Setup listeners for RTK Query
setupListeners(store.dispatch);

// Infer types from store
export type RootState = ReturnType<typeof rootReducer>;
export type AppDispatch = typeof store.dispatch;
