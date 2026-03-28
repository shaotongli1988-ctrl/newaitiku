<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps({
  summary: {
    type: Object,
    default: () => ({}),
  },
})

const radarRef = ref(null)
const scatterRef = ref(null)
let radarChart = null
let scatterChart = null
let initEcharts = null
let echartsReadyPromise = null

async function ensureEchartsRuntime() {
  if (initEcharts) {
    return
  }
  if (!echartsReadyPromise) {
    echartsReadyPromise = import('../../utils/echarts/teacherRuntime.js').then(({ ensureTeacherEchartsRuntime }) => {
      initEcharts = ensureTeacherEchartsRuntime()
    })
  }
  await echartsReadyPromise
}

const radarRows = computed(() => {
  const weakKnowledgeTags = Array.isArray(props.summary?.weakKnowledgeTags)
    ? props.summary.weakKnowledgeTags
    : []
  const topRows = weakKnowledgeTags.slice(0, 6)
  if (!topRows.length) {
    return []
  }
  const maxWrongCount = Math.max(...topRows.map((row) => Number(row?.wrongCount || 0)), 1)
  return topRows.map((row) => {
    const wrongCount = Number(row?.wrongCount || 0)
    return {
      name: String(row?.knowledgeTag || '-'),
      value: Math.max(8, Math.round(((maxWrongCount - wrongCount) / maxWrongCount) * 100)),
    }
  })
})

const scatterRows = computed(() => {
  const rankingRows = Array.isArray(props.summary?.studentRankings) ? props.summary.studentRankings : []
  const lowActivityRows = Array.isArray(props.summary?.lowActivityStudents)
    ? props.summary.lowActivityStudents
    : []
  const activityMap = new Map(
    lowActivityRows.map((row) => [String(row?.studentUserId || ''), Number(row?.activityCount || 0)]),
  )
  return rankingRows.map((row) => {
    const studentUserId = String(row?.studentUserId || '')
    const mastery = Number(row?.averageMastery || 0)
    const activity = activityMap.has(studentUserId) ? activityMap.get(studentUserId) : 8
    const riskLevel = mastery < 0.6 || Number(activity || 0) <= 3 ? '高风险' : '平稳'
    return {
      studentUserId,
      mastery: Math.round(mastery * 100),
      activity: Number(activity || 0),
      riskLevel,
    }
  })
})

function renderRadarChart() {
  if (!radarRef.value) {
    return
  }
  if (!radarChart) {
    radarChart = initEcharts(radarRef.value)
  }

  const rows = radarRows.value
  radarChart.setOption({
    tooltip: {
      trigger: 'item',
    },
    radar: {
      indicator: rows.map((row) => ({
        name: row.name,
        max: 100,
      })),
      splitNumber: 4,
      axisName: {
        color: 'var(--qb-text-strong)',
      },
      splitLine: {
        lineStyle: {
          color: 'rgba(148, 163, 184, 0.4)',
        },
      },
    },
    series: [
      {
        type: 'radar',
        data: [
          {
            value: rows.map((row) => row.value),
            name: '知识点覆盖率',
            areaStyle: {
              color: 'rgba(14, 165, 233, 0.2)',
            },
            lineStyle: {
              color: 'var(--el-color-primary)',
            },
            itemStyle: {
              color: 'var(--el-color-primary)',
            },
          },
        ],
      },
    ],
  })
}

function renderScatterChart() {
  if (!scatterRef.value) {
    return
  }
  if (!scatterChart) {
    scatterChart = initEcharts(scatterRef.value)
  }

  const rows = scatterRows.value
  scatterChart.setOption({
    tooltip: {
      trigger: 'item',
      formatter(params) {
        const row = params?.data?.raw || {}
        return `${row.studentUserId}<br/>掌握度: ${row.mastery}%<br/>活跃度: ${row.activity}`
      },
    },
    xAxis: {
      type: 'value',
      min: 0,
      max: 100,
      name: '掌握度评分',
    },
    yAxis: {
      type: 'value',
      min: 0,
      name: '活跃次数',
    },
    series: [
      {
        type: 'scatter',
        symbolSize(item) {
          return Math.max(12, Math.min(32, Number(item[2] || 12)))
        },
        data: rows.map((row) => ({
          value: [row.mastery, row.activity, row.activity * 2 + 8],
          raw: row,
          itemStyle: {
            color: row.riskLevel === '高风险' ? 'var(--qb-danger-strong)' : 'var(--el-color-primary)',
          },
        })),
      },
    ],
  })
}

function resizeCharts() {
  radarChart?.resize()
  scatterChart?.resize()
}

async function renderCharts() {
  await nextTick()
  await ensureEchartsRuntime()
  renderRadarChart()
  renderScatterChart()
  resizeCharts()
}

watch(
  () => props.summary,
  () => {
    renderCharts()
  },
  { deep: true },
)

onMounted(() => {
  renderCharts()
  window.addEventListener('resize', resizeCharts)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeCharts)
  radarChart?.dispose()
  scatterChart?.dispose()
  radarChart = null
  scatterChart = null
})
</script>

<template>
  <section class="charts-grid">
    <article class="chart-card">
      <header>
        <h3>知识点覆盖率雷达图</h3>
      </header>
      <div ref="radarRef" class="chart-body" />
    </article>

    <article class="chart-card">
      <header>
        <h3>风险学生分布散点图</h3>
      </header>
      <div ref="scatterRef" class="chart-body" />
    </article>
  </section>
</template>

<style scoped>
.charts-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.chart-card {
  border-radius: 12px;
  border: 1px solid var(--qb-primary-soft-border);
  background: linear-gradient(180deg, var(--qb-bg-card), var(--qb-primary-soft-bg));
  padding: 12px;
}

.chart-card h3 {
  margin: 0;
  font-size: 15px;
  color: var(--qb-text-heading);
}

.chart-body {
  width: 100%;
  height: 320px;
}

@media (max-width: 980px) {
  .charts-grid {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
