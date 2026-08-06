<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { fetchInterestingObjects, type InterestingObject } from '../api'
import { useSelectionStore } from '../stores/selection'
import { classLabel } from '../labels'

const selection = useSelectionStore()
const rows = ref<InterestingObject[]>([])

onMounted(async () => {
    rows.value = await fetchInterestingObjects()
})
</script>

<template>
    <section>
        <h2 title="Objects with many observations and the largest brightness change (max - min magnitude). Click to see the light curve">
            <span class="star">★</span>
            Interesting
        </h2>
        <div class="scroll">
            <div
                v-for="row in rows"
                :key="row.object_id"
                class="row"
                :class="{ selected: row.object_id === selection.objectId }"
                :title="`${classLabel(row.classification).full}, ${row.n_events} events`"
                @click="selection.select(row.object_id)"
            >
                <span class="object">{{ row.object_id }}</span>
                <span class="amp">{{ row.amplitude.toFixed(2) }}<small>m</small></span>
            </div>
        </div>
    </section>
</template>

<style lang="sass" scoped>
h2
    cursor: help

.star
    color: #e8c74a

.scroll
    max-height: 260px
    overflow-y: auto

.row
    display: flex
    justify-content: space-between
    align-items: baseline
    padding: 4px 6px
    border-radius: 4px
    cursor: pointer

    &:hover
        background: #26262a

    &.selected
        background: #2e3a4d

.object
    color: #7aa2d6

.amp
    color: #d4d4d6
    font-variant-numeric: tabular-nums

    small
        color: #929296
        margin-left: 2px
</style>
