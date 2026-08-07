<script setup lang="ts">
import { onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { fetchClassCounts, fetchLatestAlerts, type Alert } from '../api'
import { useSelectionStore } from '../stores/selection'
import { usePollStore } from '../stores/settings'
import { classLabel, FILTER_LABELS } from '../labels'

const LIMITS = [25, 50, 100, 200, 500]

const selection = useSelectionStore()
const poll = usePollStore()
const rows = ref<Alert[]>([])
const classes = ref<string[]>([])
const filters = reactive({
    limit: 50,
    classification: '',
    dateFrom: '',
    dateTo: '',
})
let timer = 0

async function refresh() {
    rows.value = await fetchLatestAlerts(filters)
}

function restartTimer() {
    window.clearInterval(timer)
    if (poll.intervalMs > 0) {
        timer = window.setInterval(refresh, poll.intervalMs)
    }
}

watch(filters, refresh)
watch(() => poll.intervalMs, restartTimer)

onMounted(async () => {
    refresh()
    restartTimer()
    classes.value = (await fetchClassCounts()).map(r => r.classification)
})

onUnmounted(() => {
    window.clearInterval(timer)
})
</script>

<template>
    <section>
        <div class="toolbar">
            <h2>Latest alerts</h2>
            <label>
                class
                <select v-model="filters.classification">
                    <option value="">all</option>
                    <option v-for="cls in classes" :key="cls" :value="cls">
                        {{ classLabel(cls).short }}
                    </option>
                </select>
            </label>
            <label>
                from
                <input v-model="filters.dateFrom" type="date">
            </label>
            <label>
                to
                <input v-model="filters.dateTo" type="date">
            </label>
            <label>
                limit
                <select v-model.number="filters.limit">
                    <option v-for="l in LIMITS" :key="l" :value="l">{{ l }}</option>
                </select>
            </label>
        </div>
        <div class="scroll">
            <table>
                <thead>
                    <tr>
                        <th title="ZTF object identifier; click a row to see its light curve">object</th>
                        <th title="Observation time, UTC">time (UTC)</th>
                        <th title="Right ascension, degrees (sky coordinate, like longitude)">ra</th>
                        <th title="Declination, degrees (sky coordinate, like latitude)">dec</th>
                        <th title="PSF magnitude: brightness, lower = brighter">mag</th>
                        <th title="Photometric band: g = green filter, r = red filter">filter</th>
                        <th title="Classification (from the Fink topic name)">class</th>
                        <th title="Classifier confidence, 0..1 (0 = not scored)">score</th>
                    </tr>
                </thead>
                <tbody>
                    <tr
                        v-for="row in rows"
                        :key="row.object_id + row.event_ts"
                        :class="{ selected: row.object_id === selection.objectId }"
                        @click="selection.select(row.object_id)"
                    >
                        <td class="object">{{ row.object_id }}</td>
                        <td>{{ row.event_ts.slice(0, 19) }}</td>
                        <td>{{ row.ra.toFixed(4) }}</td>
                        <td>{{ row.dec.toFixed(4) }}</td>
                        <td>{{ row.magpsf.toFixed(2) }}</td>
                        <td :title="FILTER_LABELS[row.fid]?.full">
                            {{ FILTER_LABELS[row.fid]?.short ?? row.fid }}
                        </td>
                        <td :title="classLabel(row.classification).full">
                            {{ classLabel(row.classification).short }}
                        </td>
                        <td>{{ row.class_score.toFixed(2) }}</td>
                    </tr>
                </tbody>
            </table>
            <p v-if="!rows.length" class="empty">No alerts match the filters</p>
        </div>
    </section>
</template>

<style lang="sass" scoped>
.toolbar
    display: flex
    flex-wrap: wrap
    align-items: center
    gap: 16px
    margin-bottom: 12px

    h2
        margin: 0
        flex: 1

    label
        color: #929296
        display: flex
        align-items: center
        gap: 6px

    @media (max-width: 640px)
        gap: 10px 12px

        h2
            flex: 1 1 100%

.scroll
    max-height: 340px
    overflow: auto
    -webkit-overflow-scrolling: touch

tbody tr
    cursor: pointer

    &.selected
        background: #2e3a4d

.object
    color: #7aa2d6

.empty
    color: #929296
    text-align: center
    margin: 16px 0
</style>
