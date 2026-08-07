import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { yandexMetrika } from './metrika'

export default defineConfig({
    plugins: [vue(), yandexMetrika()],
    server: {
        proxy: {
            '/api': 'http://127.0.0.1:8080',
        },
    },
})
