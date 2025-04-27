import { defineConfig } from 'tsup';

export default defineConfig({
  entry: ['src/index.ts'],
  format: ['cjs', 'esm'],
  dts: true,
  minify: true,
  external: ['react', 'react-dom', 'react-router-dom', '@terrafusion/ui'],
  sourcemap: true,
  clean: true,
});