import { copyFileSync, existsSync } from 'node:fs';
import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';

export default defineConfig({
  base: '/StatsWiki/',
  plugins: [
    vue(),
    {
      name: 'spa-404',
      closeBundle() {
        const index = 'dist/index.html';
        if (existsSync(index)) copyFileSync(index, 'dist/404.html');
      },
    },
  ],
});
