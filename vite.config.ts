import process from 'node:process';
import path from 'node:path';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import yaml from '@modyfi/vite-plugin-yaml';
import svgr from 'vite-plugin-svgr';

const colorClassMapping: { [key: string]: string } = {
  '#1a1a1a': 'svg-color-bg',
  '#222': 'svg-color-bg',
  '#444': 'svg-color-inactive-cell',
  '#4dd2ff': 'svg-color-active-cell',
  '#fff': 'svg-color-text',
  '#e1ed5e': 'svg-color-text',
};

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    yaml(),
    svgr({
      include: ['**/*.svg'],
      svgrOptions: {
        exportType: 'named',
        namedExport: 'ReactComponent',
        plugins: ['@svgr/plugin-svgo', '@svgr/plugin-jsx'],
        svgoConfig: {
          floatPrecision: 2,
          plugins: [
            {
              name: 'preset-default',
              params: {
                overrides: {
                  removeTitle: false,
                  removeViewBox: false,
                },
              },
            },
            {
              name: 'addClassesByFillColor',
              fn: () => {
                return {
                  element: {
                    enter: (node: {
                      attributes: {
                        fill?: string;
                        stroke?: string;
                        class?: string;
                      };
                    }) => {
                      const fillColor = node.attributes.fill;
                      if (fillColor) {
                        const lowerCaseFill = fillColor.toLowerCase();
                        if (colorClassMapping[lowerCaseFill]) {
                          node.attributes.class =
                            colorClassMapping[lowerCaseFill];
                        }
                      }
                      const strokeColor = node.attributes.stroke;
                      if (strokeColor) {
                        const lowerCaseStroke = strokeColor.toLowerCase();
                        if (colorClassMapping[lowerCaseStroke]) {
                          const existingClass = node.attributes.class || '';
                          const newClass = colorClassMapping[lowerCaseStroke];
                          if (!existingClass.includes(newClass)) {
                            node.attributes.class =
                              `${existingClass} ${newClass}`.trim();
                          }
                        }
                      }
                    },
                  },
                };
              },
            },
          ],
        },
      },
    }),
  ],
  base: process.env.PATH_PREFIX ? `${process.env.PATH_PREFIX}/` : '/',
  define: {
    'import.meta.env.VERCEL': JSON.stringify(process.env.VERCEL),
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@config': path.resolve(__dirname, 'config.yml'),
      '@core': path.resolve(__dirname, './src/core'),
      '@themes': path.resolve(__dirname, './src/themes'),
      '@assets': path.resolve(__dirname, './assets'),
    },
  },
  build: {
    manifest: true,
    modulePreload: false,
    outDir: './dist',
  },
});
