<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { Chart } from 'chart.js/auto'
import { fetchDailyStats } from '../api'
import { classLabel } from '../labels'

const PALETTE = ['#7aa2d6', '#d6a96c', '#84bf9a', '#c98ca8', '#a08cc9', '#c9c98c']
const GRID = '#2b2b2f'

const canvas = ref<HTMLCanvasElement>()

onMounted(async () => {
    const rows = await fetchDailyStats(30)
    const days = [...new Set(rows.map(r => r.day))].sort()
    const classes = [...new Set(rows.map(r => r.classification))]
    const datasets = classes.map((cls, i) => ({
        label: classLabel(cls).short,
        backgroundColor: PALETTE[i % PALETTE.length],
        data: days.map(day =>
            rows.find(r => r.day === day && r.classification === cls)?.cnt ?? 0
        ),
    }))
    new Chart(canvas.value!, {
        type: 'bar',
        data: { labels: days, datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                tooltip: {
                    callbacks: {
                        footer: items =>
                            items.map(i => classLabel(classes[i.datasetIndex]).full).join('\n'),
                    },
                },
            },
            scales: {
                x: { stacked: true, grid: { color: GRID } },
                y: { stacked: true, grid: { color: GRID } },
            },
        },
    })
})
</script>

<template>
    <section>
        <h2 title="Number of alerts stored per day, stacked by classification">
            Alerts per day
        </h2>
        <div class="chart-box">
            <canvas ref="canvas"></canvas>
        </div>
    </section>
</template>

<style lang="sass" scoped>
h2
    cursor: help

.chart-box
    position: relative
    height: 260px
</style>
