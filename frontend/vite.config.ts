import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import { fileURLToPath } from 'url';
import { dirname, resolve } from 'path';
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0'
  },
  test: {
    environment: 'jsdom',
    alias: {
      leaflet: resolve(__dirname, 'src/__mocks__/leaflet.ts')
    }
  }
});
