<script setup lang="ts">
import { onUnmounted, ref, watch } from 'vue'
import { Chart } from 'chart.js/auto'
import { fetchObjectHistory } from '../api'
import { useSelectionStore } from '../stores/selection'
import { FILTER_LABELS } from '../labels'

const FILTER_COLORS: Record<number, string> = { 1: '#84bf9a', 2: '#c98c8c' }
const GRID = '#2b2b2f'

const selection = useSelectionStore()
const canvas = ref<HTMLCanvasElement>()
let chart: Chart | null = null

watch(() => selection.objectId, async objectId => {
    if (!objectId) {
        return
    }
    const points = await fetchObjectHistory(objectId)
    const datasets = Object.entries(FILTER_LABELS).map(([fid, label]) => ({
        label: label.short,
        borderColor: FILTER_COLORS[Number(fid)],
        backgroundColor: FILTER_COLORS[Number(fid)],
        showLine: true,
        data: points
            .filter(p => p.fid === Number(fid))
            .map(p => ({ x: p.event_ts.slice(0, 16), y: p.magpsf })),
    })).filter(ds => ds.data.length)
    chart?.destroy()
    chart = new Chart(canvas.value!, {
        type: 'scatter',
        data: { datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                tooltip: {
                    callbacks: {
                        footer: items =>
                            items.map(i => FILTER_LABELS[i.dataset.label === 'g' ? 1 : 2].full).join('\n'),
                    },
                },
            },
            scales: {
                x: { type: 'category', grid: { color: GRID } },
                y: {
                    reverse: true,
                    title: { display: true, text: 'magpsf' },
                    grid: { color: GRID },
                },
            },
        },
    })
})

onUnmounted(() => {
    chart?.destroy()
})
</script>

<template>
    <section>
        <h2 title="Brightness history of the selected object. Magnitude scale is inverted: lower value = brighter. g/r are ZTF photometric bands (green/red filters)">
            Light curve
            <span v-if="selection.objectId" class="object">{{ selection.objectId }}</span>
        </h2>
        <div class="chart-box">
            <canvas v-show="selection.objectId" ref="canvas"></canvas>
            <p v-if="!selection.objectId" class="hint">
                Click an object in the alerts table
            </p>
        </div>
    </section>
</template>

<style lang="sass" scoped>
h2
    cursor: help

.object
    color: #7aa2d6
    margin-left: 8px

.chart-box
    position: relative
    height: 260px

.hint
    color: #929296
    text-align: center
    padding-top: 100px
    margin: 0
</style>
