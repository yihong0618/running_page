module.exports = {
  env: {
    browser: true,
    es6: true,
  },
  extends: [
    'airbnb',
  ],
  globals: {
    Atomics: 'readonly',
    SharedArrayBuffer: 'readonly',
  },
  parser: 'babel-eslint',
  parserOptions: {
    sourceType: 'module',
    allowImportExportEverywhere: true
  },
  plugins: [
    'react',
  ],
  "rules": {
    "indent": [
      "error",
      2,
      {
        "ignoredNodes": [
          "TemplateLiteral"
        ]
      }
    ],
    "template-curly-spacing": [
      "off"
    ]
  },
};
