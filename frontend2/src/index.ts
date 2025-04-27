
// Ensure this is at the very top of your entry file (before other imports)
window.Huntarr = window.Huntarr || {}; // Ensure Huntarr is defined
window.Huntarr.urlBase = window.Huntarr.urlBase || '/';

import './polyfills';
import 'Styles/globals.module.css';
import './index.module.css';
import { bootstrap } from './bootstrap';

async function loadHuntarrConfig() {
  try {
    const initializeUrl = `${window.Huntarr.urlBase}/`;
    const response = await fetch(initializeUrl);
    if (response.ok) {
      const config = await response.json();
      Object.assign(window.Huntarr, config);
    } else {
      console.warn('initialize.json not found, using defaults.');
    }
  } catch (e) {
    console.warn('Failed to load initialize.json', e);
  }
}

await loadHuntarrConfig();

/* eslint-disable no-undef, @typescript-eslint/ban-ts-comment */
// @ts-ignore 2304
//__webpack_public_path__ = `${window.Huntarr.urlBase}/`;
/* eslint-enable no-undef, @typescript-eslint/ban-ts-comment */

const error = console.error;

// Monkey patch console.error to filter out some warnings from React
// TODO: Remove this after the great TypeScript migration

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function logError(...parameters: any[]) {
  const filter = parameters.find((parameter) => {
    return (
      typeof parameter === 'string' &&
      (parameter.includes(
        'Support for defaultProps will be removed from function components in a future major release'
      ) ||
        parameter.includes(
          'findDOMNode is deprecated and will be removed in the next major release'
        ))
    );
  });

  if (!filter) {
    error(...parameters);
  }
}

console.error = logError;

await bootstrap();