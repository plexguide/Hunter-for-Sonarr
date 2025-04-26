// src/types/AppState.ts
import SettingsAppState from './SettingsAppState';

export interface AppState {
    user: {
      isAuthenticated: boolean;
      username: string | null;
    };
    theme: {
      currentTheme: string; // e.g. 'light' or 'dark'
    };
    settings: SettingsAppState;
    // Add more sections of your state here
  }
  
export default AppState;