import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ command }) => ({
  plugins: [react()],
  // Base path for GitHub Pages: /simulon/
  base: command === 'build' ? '/simulon/' : '/',
  server: {
    proxy: {
      '/simulate': 'http://localhost:8000',
    },
  },
}));
