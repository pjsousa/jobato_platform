import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import { loadEnv } from 'vite'

const parseAllowedHosts = (value?: string) =>
  value
    ?.split(',')
    .map((host) => host.trim())
    .filter(Boolean) ?? []

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const allowedHosts = parseAllowedHosts(env.VITE_ALLOWED_HOSTS)

  return {
    plugins: [react()],
    ...(allowedHosts.length > 0 ? { server: { allowedHosts } } : {}),
    test: {
      environment: 'jsdom',
      setupFiles: './src/test-setup.ts',
      css: true,
      globals: true,
    },
  }
})
