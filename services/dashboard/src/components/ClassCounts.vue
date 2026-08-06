<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { Chart } from 'chart.js/auto'
import { fetchClassCounts } from '../api'
import { classLabel } from '../labels'

const PALETTE = ['#7aa2d6', '#d6a96c', '#84bf9a', '#c98ca8', '#a08cc9', '#c9c98c']
const GRID = '#2b2b2f'

const canvas = ref<HTMLCanvasElement>()

onMounted(async () => {
    const rows = await fetchClassCounts()
    new Chart(canvas.value!, {
        type: 'bar',
        data: {
            labels: rows.map(r => classLabel(r.classification).short),
            datasets: [{
                data: rows.map(r => r.cnt),
                backgroundColor: rows.map((_, i) => PALETTE[i % PALETTE.length]),
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        footer: items =>
                            items.map(i => classLabel(rows[i.dataIndex].classification).full).join('\n'),
                    },
                },
            },
            scales: {
                x: { grid: { display: false } },
                y: { grid: { color: GRID } },
            },
        },
    })
})
</script>

<template>
    <section>
        <h2 title="Total number of unique alerts per classification">
            By class
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
