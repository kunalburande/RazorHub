import { execSync } from 'node:child_process';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import { sentryVitePlugin } from '@sentry/vite-plugin';

import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

let gitHash = 'latest';
try {
  gitHash = execSync('git rev-parse --short HEAD').toString().trim();
} catch {
  gitHash = 'latest';
}

export default defineConfig({
  root: path.resolve(__dirname),
  define: { 'import.meta.env.VITE_APP_VERSION': JSON.stringify(gitHash) },
  build: { sourcemap: 'hidden' },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src/seller'),
    },
  },
  plugins: [
    react(),
    tailwindcss(),
    sentryVitePlugin({
      org: process.env.SENTRY_ORG,
      project: process.env.SENTRY_PROJECT,
      authToken: process.env.SENTRY_AUTH_TOKEN,
    }),
  ],
  server: {
    allowedHosts: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
