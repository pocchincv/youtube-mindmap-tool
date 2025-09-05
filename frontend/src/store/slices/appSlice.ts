import { createSlice, type PayloadAction } from '@reduxjs/toolkit';
import type { YouTubeVideo, MindMap, AppState } from '../../types';

const initialState: AppState = {
  currentVideo: null,
  currentMindMap: null,
  isLoading: false,
  error: null,
  sidebarCollapsed: false,
  theme: 'light',
};

const appSlice = createSlice({
  name: 'app',
  initialState,
  reducers: {
    setCurrentVideo: (state, action: PayloadAction<YouTubeVideo | null>) => {
      state.currentVideo = action.payload;
    },
    setCurrentMindMap: (state, action: PayloadAction<MindMap | null>) => {
      state.currentMindMap = action.payload;
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
      if (action.payload) {
        state.error = null;
      }
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
      if (action.payload) {
        state.isLoading = false;
      }
    },
    toggleSidebar: (state) => {
      state.sidebarCollapsed = !state.sidebarCollapsed;
    },
    setSidebarCollapsed: (state, action: PayloadAction<boolean>) => {
      state.sidebarCollapsed = action.payload;
    },
    toggleTheme: (state) => {
      state.theme = state.theme === 'light' ? 'dark' : 'light';
    },
    setTheme: (state, action: PayloadAction<'light' | 'dark'>) => {
      state.theme = action.payload;
    },
    clearError: (state) => {
      state.error = null;
    },
    resetApp: () => initialState,
  },
});

export const {
  setCurrentVideo,
  setCurrentMindMap,
  setLoading,
  setError,
  toggleSidebar,
  setSidebarCollapsed,
  toggleTheme,
  setTheme,
  clearError,
  resetApp,
} = appSlice.actions;

export default appSlice.reducer;