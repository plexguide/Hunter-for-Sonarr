import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'
import path from 'path'

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
    },
  },
});