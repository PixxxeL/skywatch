import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useSelectionStore = defineStore('selection', () => {
    const objectId = ref<string | null>(null)

    function select(id: string) {
        objectId.value = id
    }

    return { objectId, select }
})
