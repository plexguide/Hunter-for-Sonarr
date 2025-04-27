import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'
import path from 'path'

// Helper function to resolve file paths
function resolvePath(path: string) {
  return new URL(path, import.meta.url).pathname;
}


export default defineConfig({
  plugins: [react()],
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