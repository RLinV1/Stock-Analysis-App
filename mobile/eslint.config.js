const { defineConfig } = require('eslint/config');
const expoConfig = require('eslint-config-expo/flat');

module.exports = defineConfig([
  { ignores: ['dist/**', '.expo/**', '.expo-tmp/**', '.jest-cache/**'] },
  expoConfig,
]);
