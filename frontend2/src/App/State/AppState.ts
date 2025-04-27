// src/types/AppState.ts
import ModelBase from 'App/ModelBase';
import SettingsAppState from './SettingsAppState';
import { FilterBuilderTypes } from 'Helpers/Props/filterBuilderTypes';
import { DateFilterValue, FilterType } from 'Helpers/Props/filterTypes';
import MessagesAppState from './MessageAppState';


export interface FilterBuilderPropOption {
  id: string;
  name: string;
}

export interface FilterBuilderPropOption {
  id: string;
  name: string;
}

export interface FilterBuilderProp<T> {
  name: string;
  label: string | (() => string);
  type: FilterBuilderTypes;
  valueType?: string;
  optionsSelector?: (items: T[]) => FilterBuilderPropOption[];
}

export interface PropertyFilter {
  key: string;
  value: string | string[] | number[] | boolean[] | DateFilterValue;
  type: FilterType;
}

export interface Filter {
  key: string;
  label: string | (() => string);
  filters: PropertyFilter[];
}

export interface CustomFilter extends ModelBase {
  type: string;
  label: string;
  filters: PropertyFilter[];
}

export interface AppSectionState {
  isUpdated: boolean;
  isConnected: boolean;
  isDisconnected: boolean;
  isReconnecting: boolean;
  isRestarting: boolean;
  isSidebarVisible: boolean;
  version: string;
  prevVersion?: string;
  dimensions: {
    isSmallScreen: boolean;
    isLargeScreen: boolean;
    width: number;
    height: number;
  };
  translations: {
    error?: Error;
    isPopulated: boolean;
  };
  messages: MessagesAppState;
}


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