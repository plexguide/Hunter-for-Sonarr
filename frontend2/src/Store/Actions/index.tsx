import userReducer from './Creators/Reducers/userReducer'; // your user slice
import themeReducer from './Creators/Reducers/themeReducer'; // your theme slice

const actions = [
  {
    section: 'user',
    defaultState: { isAuthenticated: false, username: null },
    reducer: userReducer.reducer, // Using the .reducer here to get the slice reducer
  },
  {
    section: 'theme',
    defaultState: { currentTheme: 'light' },
    reducer: themeReducer.reducer, // Using the .reducer here to get the slice reducer
  },
  // Add more actions as necessary
];

export default actions;
