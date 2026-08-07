<script setup lang="ts">
import DailyChart from './components/DailyChart.vue'
import TopObjects from './components/TopObjects.vue'
import ClassCounts from './components/ClassCounts.vue'
import LatestAlerts from './components/LatestAlerts.vue'
import ObjectCurve from './components/ObjectCurve.vue'
import { usePollStore } from './stores/settings'

const POLL_OPTIONS = [
    { value: 5000, label: '5 s' },
    { value: 10000, label: '10 s' },
    { value: 30000, label: '30 s' },
    { value: 60000, label: '1 min' },
    { value: 0, label: 'off' },
]

const poll = usePollStore()
</script>

<template>
    <header class="header">
        <h1>SkyWatch</h1>
        <span class="sub">ZTF transient alerts via Fink</span>
        <label class="poll" title="How often the alerts table refreshes">
            refresh
            <select v-model.number="poll.intervalMs">
                <option v-for="o in POLL_OPTIONS" :key="o.value" :value="o.value">
                    {{ o.label }}
                </option>
            </select>
        </label>
    </header>
    <main class="grid">
        <DailyChart class="panel" />
        <ClassCounts class="panel" />
        <TopObjects class="panel" />
        <ObjectCurve class="panel" />
        <LatestAlerts class="panel wide" />
    </main>
</template>

<style lang="sass" scoped>
.header
    display: flex
    flex-wrap: wrap
    align-items: baseline
    gap: 12px
    padding: 18px 24px 6px

    h1
        margin: 0
        font-size: 22px

    .sub
        color: #929296
        flex: 1

    .poll
        color: #929296
        display: flex
        align-items: center
        gap: 6px

    @media (max-width: 640px)
        gap: 6px 12px
        padding: 14px 16px 4px

        .sub
            flex: 1 1 100%
            order: 3

.grid
    display: grid
    grid-template-columns: 3fr 1fr 1fr 3fr
    gap: 16px
    padding: 16px 24px 24px

    .wide
        grid-column: span 4

    @media (max-width: 1024px)
        grid-template-columns: 1fr 1fr

        .wide
            grid-column: span 2

    @media (max-width: 640px)
        grid-template-columns: 1fr
        gap: 12px
        padding: 12px 12px 16px

        .wide
            grid-column: span 1
</style>
