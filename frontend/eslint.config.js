import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{js,jsx}'],
    extends: [
      js.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      // `__APP_VERSION__` est posé par Vite (`define`, cf. vite.config.js) : il vaut la version
      // de package.json au moment de la construction. Sans cette ligne, ESLint le voit comme une
      // variable inventée — c'est un global du même ordre que ceux du navigateur.
      globals: { ...globals.browser, __APP_VERSION__: 'readonly' },
      parserOptions: { ecmaFeatures: { jsx: true } },
    },
  },
])
