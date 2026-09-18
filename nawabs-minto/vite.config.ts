import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { VitePWA } from 'vite-plugin-pwa'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    VitePWA({
      registerType: 'autoUpdate',
      // Scoped to the driver app — the owner dashboard is a plain responsive web app.
      scope: '/driver/',
      includeAssets: ['icons/icon.svg'],
      manifest: {
        id: '/driver/',
        name: "Nawab's Minto — Driver",
        short_name: 'Nawab Driver',
        description: 'Delivery driver app for Nawab\'s Minto',
        start_url: '/driver/home',
        scope: '/driver/',
        display: 'standalone',
        background_color: '#fdf8ef',
        theme_color: '#6e1717',
        icons: [
          { src: '/icons/icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: '/icons/icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'any maskable' },
        ],
      },
      workbox: {
        navigateFallback: '/driver/home',
        navigateFallbackAllowlist: [/^\/driver/],
      },
    }),
  ],
  resolve: {
    alias: {
      '@': new URL('./src', import.meta.url).pathname,
    },
  },
})
