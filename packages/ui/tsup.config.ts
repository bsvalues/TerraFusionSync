import { defineConfig } from 'tsup';

export default defineConfig({
  entry: ['src/index.ts'],
  format: ['cjs', 'esm'],
  dts: true,
  minify: true,
  external: ['react', 'react-dom'],
  sourcemap: true,
  clean: true,
});