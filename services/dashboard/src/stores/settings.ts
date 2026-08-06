import { defineStore } from 'pinia'
import { ref } from 'vue'

export const usePollStore = defineStore('poll', () => {
    const intervalMs = ref(10000)

    return { intervalMs }
})
