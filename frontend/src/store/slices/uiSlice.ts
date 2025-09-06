/**
 * UI Slice
 * 
 * Manages global UI state including:
 * - Sidebar state
 * - Theme preferences  
 * - Loading states
 * - Toast notifications
 * - Modal states
 * 
 * This slice is NOT persisted as UI state should reset on page reload.
 */

import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface ToastNotification {
  id: string;
  title: string;
  description?: string;
  type: 'success' | 'error' | 'warning' | 'info';
  duration?: number;
  timestamp: number;
}

export interface UIState {
  // Sidebar
  sidebarCollapsed: boolean;
  sidebarOpen: boolean; // For mobile

  // Theme
  theme: 'light' | 'dark' | 'system';

  // Global loading
  globalLoading: boolean;

  // Toast notifications
  toasts: ToastNotification[];

  // Modals
  modals: {
    profilePictureModal: boolean;
    settingsModal: boolean;
    confirmDialog: {
      open: boolean;
      title?: string;
      description?: string;
      onConfirm?: () => void;
    };
  };

  // Page states
  pageLoading: Record<string, boolean>;
}

const initialState: UIState = {
  sidebarCollapsed: false,
  sidebarOpen: false,
  theme: 'system',
  globalLoading: false,
  toasts: [],
  modals: {
    profilePictureModal: false,
    settingsModal: false,
    confirmDialog: {
      open: false,
    },
  },
  pageLoading: {},
};

export const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    // Sidebar actions
    toggleSidebar: (state) => {
      state.sidebarCollapsed = !state.sidebarCollapsed;
    },
    setSidebarCollapsed: (state, action: PayloadAction<boolean>) => {
      state.sidebarCollapsed = action.payload;
    },
    setSidebarOpen: (state, action: PayloadAction<boolean>) => {
      state.sidebarOpen = action.payload;
    },

    // Theme actions
    setTheme: (state, action: PayloadAction<'light' | 'dark' | 'system'>) => {
      state.theme = action.payload;
    },

    // Global loading
    setGlobalLoading: (state, action: PayloadAction<boolean>) => {
      state.globalLoading = action.payload;
    },

    // Page loading
    setPageLoading: (state, action: PayloadAction<{ page: string; loading: boolean }>) => {
      state.pageLoading[action.payload.page] = action.payload.loading;
    },

    // Toast actions
    addToast: (state, action: PayloadAction<Omit<ToastNotification, 'id' | 'timestamp'>>) => {
      const toast: ToastNotification = {
        ...action.payload,
        id: Math.random().toString(36).substr(2, 9),
        timestamp: Date.now(),
      };
      state.toasts.push(toast);
    },
    removeToast: (state, action: PayloadAction<string>) => {
      state.toasts = state.toasts.filter(toast => toast.id !== action.payload);
    },
    clearToasts: (state) => {
      state.toasts = [];
    },

    // Modal actions
    setProfilePictureModal: (state, action: PayloadAction<boolean>) => {
      state.modals.profilePictureModal = action.payload;
    },
    setSettingsModal: (state, action: PayloadAction<boolean>) => {
      state.modals.settingsModal = action.payload;
    },
    setConfirmDialog: (state, action: PayloadAction<{
      open: boolean;
      title?: string;
      description?: string;
      onConfirm?: () => void;
    }>) => {
      state.modals.confirmDialog = action.payload;
    },

    // Reset UI state (useful for logout)
    resetUIState: (state) => {
      state.toasts = [];
      state.modals = {
        profilePictureModal: false,
        settingsModal: false,
        confirmDialog: { open: false },
      };
      state.globalLoading = false;
      state.pageLoading = {};
    },
  },
});

// Action creators
export const {
  toggleSidebar,
  setSidebarCollapsed,
  setSidebarOpen,
  setTheme,
  setGlobalLoading,
  setPageLoading,
  addToast,
  removeToast,
  clearToasts,
  setProfilePictureModal,
  setSettingsModal,
  setConfirmDialog,
  resetUIState,
} = uiSlice.actions;

// Selectors
export const selectUI = (state: { ui: UIState }) => state.ui;
export const selectSidebarCollapsed = (state: { ui: UIState }) => state.ui.sidebarCollapsed;
export const selectSidebarOpen = (state: { ui: UIState }) => state.ui.sidebarOpen;
export const selectTheme = (state: { ui: UIState }) => state.ui.theme;
export const selectGlobalLoading = (state: { ui: UIState }) => state.ui.globalLoading;
export const selectToasts = (state: { ui: UIState }) => state.ui.toasts;
export const selectModals = (state: { ui: UIState }) => state.ui.modals;
export const selectPageLoading = (state: { ui: UIState }, page: string) => 
  state.ui.pageLoading[page] || false;

export default uiSlice.reducer;
