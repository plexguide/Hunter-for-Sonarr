import { combineReducers } from '@reduxjs/toolkit'; 
import actions from 'Store/Actions';

const defaultState: Record<string, any> = {};
const reducers: Record<string, any> = {};

actions.forEach((action) => {
  const { section, defaultState: sectionDefaultState, reducer } = action;

  // Set default state dynamically
  defaultState[section] = sectionDefaultState;

  // Set reducers dynamically
  reducers[section] = reducer; // Add slice reducer directly
});

export { defaultState };

export default function createReducers() {
  return combineReducers(reducers);
}
