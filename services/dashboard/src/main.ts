import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import './styles/main.sass'

createApp(App).use(createPinia()).mount('#app')
