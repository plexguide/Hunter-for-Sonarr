import userReducer from './Creators/Reducers/userReducer'; // your user slice
import themeReducer from './Creators/Reducers/themeReducer'; // your theme slice
import * as media from 'Store/Actions/mediaActions';  // Correct for named exports
import * as mediaIndex from './mediaIndexActions';  // Correct for named exports


const actions = [
  {
    section: 'user',
    defaultState: { isAuthenticated: false, username: null },
    reducer: userReducer, // Using the .reducer here to get the slice reducer
  },
  {
    section: 'theme',
    defaultState: { currentTheme: 'light' },
    reducer: themeReducer, // Using the .reducer here to get the slice reducer
  },
  media,
  mediaIndex
  // Add more actions as necessary
];

export default actions;
