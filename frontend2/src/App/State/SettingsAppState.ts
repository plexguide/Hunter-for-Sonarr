import UiSettings from 'typings/Settings/UiSettings';
import { AppSectionItemState } from './AppSectionState';  
  
  
  
  export type UiSettingsAppState = AppSectionItemState<UiSettings>;
  
  interface SettingsAppState {
    ui: UiSettingsAppState;
  }
  
  export default SettingsAppState;