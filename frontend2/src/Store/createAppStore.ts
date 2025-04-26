import { configureStore } from '@reduxjs/toolkit';
import createReducers, { defaultState } from 'Store/Actions/createReducers';

function createAppStore() {
  const appStore = configureStore({
    reducer: createReducers(),
    preloadedState: defaultState,
  });

  return appStore;
}

export default createAppStore;
