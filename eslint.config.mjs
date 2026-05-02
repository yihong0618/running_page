import eslintReact from '@eslint-react/eslint-plugin';
import js from '@eslint/js';
import tsParser from '@typescript-eslint/parser';
import tsPlugin from '@typescript-eslint/eslint-plugin';
import globals from 'globals';
import reactHooks from 'eslint-plugin-react-hooks';

const reactRecommended = eslintReact.configs['recommended-typescript'];
const reactRulesAsWarnings = Object.fromEntries(
  Object.entries(reactRecommended.rules).map(([rule, config]) => {
    if (Array.isArray(config)) {
      return [rule, ['warn', ...config.slice(1)]];
    }
    return [rule, 'warn'];
  })
);

export default [
  {
    ignores: [
      '**/node_modules/',
      '**/dist/',
      '**/pyproject.toml',
      '**/LICENSE',
      '**/*lock.*',
      '**/*.html',
      '**/*.md',
      '**/*.css',
      '**/*.svg',
      '**/*.png',
      '**/*.jpg',
      '**/*.ico',
      '**/*.lock',
      '**/*.min.js',
    ],
  },
  js.configs.recommended,
  {
    files: ['**/*.{js,jsx,ts,tsx}'],
    languageOptions: {
      parser: tsParser,
      globals: {
        ...globals.browser,
      },
      ecmaVersion: 'latest',
      sourceType: 'module',
      parserOptions: {
        ecmaFeatures: {
          jsx: true,
        },
      },
    },
    plugins: {
      ...reactRecommended.plugins,
      ...reactHooks.configs.flat.recommended.plugins,
      '@typescript-eslint': tsPlugin,
    },
    settings: reactRecommended.settings,
    rules: {
      ...reactRulesAsWarnings,
      ...reactHooks.configs.flat.recommended.rules,
      'react-hooks/set-state-in-effect': 'warn',
      'react-hooks/static-components': 'warn',
      'no-unused-vars': 'off',
      '@typescript-eslint/no-unused-vars': [
        'warn',
        {
          argsIgnorePattern: '^_',
          varsIgnorePattern: '^_',
          caughtErrorsIgnorePattern: '^_',
          destructuredArrayIgnorePattern: '^_',
          ignoreRestSiblings: true,
        },
      ],
    },
  },
];
