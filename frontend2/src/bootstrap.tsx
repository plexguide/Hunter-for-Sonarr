import React from 'react';
import { createRoot } from 'react-dom/client';
import createAppStore from 'Store/createAppStore';
import App from './App/App';


export async function bootstrap() {
  const store = createAppStore();
  const container = document.getElementById('root');
  console.log(container);
  if (!container) throw new Error('Root element not found');

  const root = createRoot(container!); 
  root.render(<App store={store} />);
}