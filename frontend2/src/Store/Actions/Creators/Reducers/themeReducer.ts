// src/redux/themeReducer.ts

import { createSlice } from '@reduxjs/toolkit';
import { AppState } from 'App/State/AppState';

const initialState: AppState['theme'] = {
  currentTheme: 'light',
};

const themeSlice = createSlice({
  name: 'theme',
  initialState,
  reducers: {
    toggleTheme: (state) => {
      state.currentTheme = state.currentTheme === 'light' ? 'dark' : 'light';
    },
  },
});

export const { toggleTheme } = themeSlice.actions;
export default themeSlice.reducer;
