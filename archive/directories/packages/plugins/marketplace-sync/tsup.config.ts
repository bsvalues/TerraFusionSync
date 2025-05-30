import { defineConfig } from 'tsup';

export default defineConfig({
  entry: ['src/index.ts'],
  clean: true,
  dts: true,
  format: ['cjs', 'esm'],
  external: ['react', 'react-dom', 'react-router-dom', '@terrafusion/ui'],
});