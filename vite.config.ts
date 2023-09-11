import process from 'node:process';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import viteTsconfigPaths from 'vite-tsconfig-paths';
import svgrPlugin from 'vite-plugin-svgr';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(), viteTsconfigPaths(), svgrPlugin()],
  base: process.env.PATH_PREFIX || '/',
  build: {
    manifest: true,
    outDir: './dist', // for user easy to use, vercel use default dir -> dist
  },
});
