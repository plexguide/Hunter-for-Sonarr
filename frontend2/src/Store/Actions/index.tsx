import * as media from 'Store/Actions/mediaActions';  // Correct for named exports
import * as mediaIndex from './mediaIndexActions';  // Correct for named exports
import * as app from './appActions';


const actions = [
  media,
  mediaIndex,
  app
  // Add more actions as necessary
];

export default actions;
