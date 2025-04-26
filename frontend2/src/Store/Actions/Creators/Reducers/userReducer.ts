// src/Store/Actions/Creators/Reducers/userReducer.ts

import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { AppState } from 'App/State/AppState';

const initialState: AppState['user'] = {
  isAuthenticated: false,
  username: null,
};

const userSlice = createSlice({
  name: 'user',
  initialState,
  reducers: {
    login: (state, action: PayloadAction<string>) => {
      state.isAuthenticated = true;
      state.username = action.payload;
    },
    logout: (state) => {
      state.isAuthenticated = false;
      state.username = null;
    },
  },
});

export const { login, logout } = userSlice.actions;
export default userSlice.reducer;
