import { combineReducers } from '@reduxjs/toolkit'; 
import actions from 'Store/Actions';

const defaultState = {};
const reducers = {};

actions.forEach((action) => {
  const section = action.section;

  defaultState[section] = action.defaultState;
  reducers[section] = action.reducers;
});

export { defaultState };

export default function createReducers() {
  return combineReducers(reducers);
}
