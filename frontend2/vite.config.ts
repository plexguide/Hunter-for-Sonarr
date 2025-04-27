import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'
import tsconfigPaths from 'vite-tsconfig-paths';
import path from 'path'


export default defineConfig({
  plugins: [
    react(),
    tsconfigPaths(),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      Utilities: path.resolve(__dirname, 'src/Utilities'),
      Components: path.resolve(__dirname, 'src/Components'),
      Settings: path.resolve(__dirname, 'src/Settings'),
      Store: path.resolve(__dirname, 'src/Store'),
      App: path.resolve(__dirname, 'src/App'),
      Helpers: path.resolve(__dirname, 'src/Helpers'),
      Styles: path.resolve(__dirname, 'src/Styles'),
      Media: path.resolve(__dirname, 'src/Media'),
    },
  },
  css: {
    modules: {
      scopeBehaviour: 'local', // Make ALL .css files behave like CSS modules
    },
  },
});