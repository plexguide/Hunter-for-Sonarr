import { createRoot } from 'react-dom/client';
import createAppStore from 'Store/createAppStore.ts';
import App from './App/App';


export async function bootstrap() {
  const store = createAppStore();
  const container = document.getElementById('root');

  const root = createRoot(container!); // createRoot(container!) if you use TypeScript
  root.render(<App store={store} />);
}