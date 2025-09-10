/**
 * Redux Store Configuration
 * 
 * This file configures the Redux store using Redux Toolkit with best practices:
 * - Immutable state updates with Immer
 * - Built-in Redux DevTools integration
 * - Service-based API calls (no RTK Query)
 * - Type-safe throughout the application
 * 
 * @see https://redux-toolkit.js.org/tutorials/quick-start
 */

import { configureStore } from '@reduxjs/toolkit';
import { persistStore, persistReducer } from 'redux-persist';
import storage from 'redux-persist/lib/storage';
import { combineReducers } from '@reduxjs/toolkit';

// Import slices
import authSlice from './slices/authSlice';
import userSlice from './slices/userSlice';
import uiSlice from './slices/uiSlice';

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
    }).concat(authMiddleware),
  devTools: process.env.NODE_ENV !== 'production',
});

// Create persistor
export const persistor = persistStore(store);

// Infer the `RootState` and `AppDispatch` types from the store itself
export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
