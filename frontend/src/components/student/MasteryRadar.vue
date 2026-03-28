<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ElMessage } from '@/ui/feedback'
import { useRouter } from 'vue-router'
import { buildRadarDimensions } from '../../utils/studentMastery.js'

const props = defineProps({
  rows: {
    type: Array,
    default: () => [],
  },
  referenceRows: {
    type: Array,
    default: () => [],
  },
  referenceLabel: {
    type: String,
    default: '参考曲线',
  },
  loading: {
    type: Boolean,
    default: false,
  },
  subjectMetaMap: {
    type: Object,
    default: () => ({}),
  },
})

const router = useRouter()
const radarRef = ref(null)
const explanationPanels = ref([])

const PRIMARY_SERIES_NAME = '我的掌握度'
let radarChart = null
let initEcharts = null
let echartsReadyPromise = null

async function ensureEchartsRuntime() {
  if (initEcharts) {
    return
  }
  if (!echartsReadyPromise) {
    echartsReadyPromise = import('../../utils/echarts/studentRuntime.js').then(({ ensureStudentEchartsRuntime }) => {
      initEcharts = ensureStudentEchartsRuntime()
    })
  }
  await echartsReadyPromise
}

const normalizedRows = computed(() => (Array.isArray(props.rows) ? props.rows : []))
const normalizedReferenceRows = computed(() => (Array.isArray(props.referenceRows) ? props.referenceRows : []))
const normalizedSubjectMetaMap = computed(() => (
  props.subjectMetaMap && typeof props.subjectMetaMap === 'object'
    ? props.subjectMetaMap
    : {}
))

const radarDimensions = computed(() =>
  buildRadarDimensions(normalizedRows.value, normalizedSubjectMetaMap.value),
)

const referenceRadarDimensions = computed(() =>
  buildRadarDimensions(normalizedReferenceRows.value, normalizedSubjectMetaMap.value),
)

const chartDimensions = computed(() =>
  radarDimensions.value.length ? radarDimensions.value : referenceRadarDimensions.value,
)

const hasRows = computed(() => radarDimensions.value.length > 0)
const hasReferenceRows = computed(() => referenceRadarDimensions.value.length > 0)
const hasAnySeries = computed(() => hasRows.value || hasReferenceRows.value)

const radarIndicators = computed(() =>
  chartDimensions.value.map((item) => ({
    name: item.label,
    max: 100,
  })),
)

function buildTooltipLines(seriesLabel, dimensions) {
  return [
    `<strong>${seriesLabel}</strong>`,
    ...dimensions.map((item) => `${item.label}：${item.mastery}%`),
  ].join('<br/>')
}

async function onRadarClick(params) {
  const clickedName = String(params?.name || '').trim().toUpperCase()
  if (!clickedName) {
    return
  }

  const targetDimension = chartDimensions.value.find(
    (item) => String(item?.label || '').trim().toUpperCase() === clickedName,
  )
  if (!targetDimension?.subjectCode) {
    return
  }

  await router.push({
    path: '/student/practice',
    query: {
      subjectCode: targetDimension.subjectCode,
    },
  })
  ElMessage.success(`已定位到 ${targetDimension.subjectCode} 科目练习。`)
}

function bindRadarEvents() {
  if (!radarChart) {
    return
  }
  radarChart.off('click', onRadarClick)
  radarChart.on('click', onRadarClick)
}

async function renderRadar() {
  await nextTick()
  if (!radarRef.value || props.loading) {
    return
  }

  await ensureEchartsRuntime()
  if (!radarChart) {
    radarChart = initEcharts(radarRef.value)
    bindRadarEvents()
  }

  if (!hasAnySeries.value) {
    radarChart.clear()
    radarChart.resize()
    return
  }

  const theme = getComputedStyle(document.documentElement)
  const resolveThemeColor = (primaryToken, fallbackToken = '') =>
    String(theme.getPropertyValue(primaryToken) || '').trim()
    || (String(fallbackToken || '').startsWith('--')
      ? String(theme.getPropertyValue(fallbackToken) || '').trim()
      : String(fallbackToken || '').trim())

  const primary = resolveThemeColor('--qb-primary-student', '--el-color-primary')
  const primarySoft = resolveThemeColor('--qb-primary-soft-bg', '--qb-bg-muted')
  const primaryBorder = resolveThemeColor('--qb-primary-soft-border', '--qb-border-muted')
  const warmLine = resolveThemeColor('--qb-chart-mid', '--qb-warning')
  const warmArea = resolveThemeColor('--qb-chart-mid-soft', '--qb-warning-soft-bg')
  const warmShadow = resolveThemeColor('--qb-chart-mid-shadow', 'rgba(245, 158, 11, 0.18)')
  const cardColor = resolveThemeColor('--qb-bg-card', '--qb-bg-subtle')
  const subtleText = resolveThemeColor('--qb-text-meta', '--qb-text-secondary')

  const series = []
  if (hasRows.value) {
    series.push({
      type: 'radar',
      name: PRIMARY_SERIES_NAME,
      symbol: 'circle',
      symbolSize: 10,
      data: [
        {
          value: radarDimensions.value.map((item) => item.mastery),
          name: PRIMARY_SERIES_NAME,
          areaStyle: {
            color: primarySoft,
          },
          lineStyle: {
            color: primary,
            width: 3,
            shadowBlur: 18,
            shadowColor: `${primary}2f`,
          },
          itemStyle: {
            color: primary,
            borderColor: cardColor,
            borderWidth: 2,
          },
        },
      ],
    })
  }

  if (hasReferenceRows.value) {
    series.push({
      type: 'radar',
      name: props.referenceLabel,
      symbol: 'diamond',
      symbolSize: 8,
      data: [
        {
          value: referenceRadarDimensions.value.map((item) => item.mastery),
          name: props.referenceLabel,
          areaStyle: {
            color: warmArea,
          },
          lineStyle: {
            color: warmLine,
            width: 2,
            type: 'dashed',
            shadowBlur: 12,
            shadowColor: warmShadow,
          },
          itemStyle: {
            color: warmLine,
            borderColor: cardColor,
            borderWidth: 2,
          },
        },
      ],
    })
  }

  radarChart.setOption({
    tooltip: {
      trigger: 'item',
      backgroundColor: resolveThemeColor('--qb-tooltip-bg', 'rgba(10, 18, 40, 0.88)'),
      borderWidth: 0,
      textStyle: {
        color: resolveThemeColor('--qb-text-inverse', '--qb-bg-card'),
      },
      formatter() {
        const blocks = []
        if (hasRows.value) {
          blocks.push(buildTooltipLines(PRIMARY_SERIES_NAME, radarDimensions.value))
        }
        if (hasReferenceRows.value) {
          blocks.push(buildTooltipLines(props.referenceLabel, referenceRadarDimensions.value))
        }
        return blocks.join('<br/><br/>')
      },
    },
    radar: {
      triggerEvent: true,
      indicator: radarIndicators.value,
      splitNumber: 5,
      center: ['50%', '52%'],
      radius: '72%',
      axisName: {
        color: resolveThemeColor('--qb-text-secondary-strong', '--qb-text-heading'),
        fontSize: 12,
        fontWeight: 700,
        backgroundColor: resolveThemeColor('--qb-surface-raised', 'rgba(255, 255, 255, 0.92)'),
        borderRadius: 999,
        padding: [6, 10],
      },
      splitLine: {
        lineStyle: {
          color: primaryBorder,
        },
      },
      splitArea: {
        areaStyle: {
          color: [resolveThemeColor('--qb-bg-muted', '--qb-bg-subtle'), primarySoft],
        },
      },
      axisLine: {
        lineStyle: {
          color: primaryBorder,
        },
      },
    },
    series,
    graphic: [
      {
        type: 'group',
        left: 'center',
        top: '7%',
        silent: true,
        children: [
          {
            type: 'text',
            style: {
              text: hasRows.value ? '个人 vs 参考' : props.referenceLabel,
              fill: subtleText,
              fontSize: 12,
              textAlign: 'center',
            },
          },
        ],
      },
    ],
  }, { notMerge: true })

  radarChart.resize()
}

function resizeRadar() {
  radarChart?.resize()
}

watch(
  () => [
    props.loading,
    radarDimensions.value.map((item) => item.mastery).join(','),
    referenceRadarDimensions.value.map((item) => item.mastery).join(','),
  ],
  () => {
    renderRadar()
  },
)

onMounted(() => {
  renderRadar()
  window.addEventListener('resize', resizeRadar)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeRadar)
  radarChart?.off('click', onRadarClick)
  radarChart?.dispose()
  radarChart = null
})
</script>

<template>
  <section class="mastery-radar-panel">
    <div class="radar-legend" v-if="hasAnySeries">
      <span class="legend-item legend-item--primary">{{ PRIMARY_SERIES_NAME }}</span>
      <span v-if="hasReferenceRows" class="legend-item legend-item--reference">{{ referenceLabel }}</span>
    </div>

    <div class="radar-surface" v-loading="loading">
      <el-empty
        v-if="!loading && !hasAnySeries"
        description="暂无掌握度数据，完成练习后将展示雷达画像。"
      />
      <div v-else class="radar-stage">
        <div ref="radarRef" class="mastery-radar" />
      </div>
    </div>

    <p class="interaction-tip">
      蓝色轮廓表示个人掌握度，橙色虚线表示参考曲线；点击任一科目标签即可直达对应科目练习。
    </p>

    <el-collapse v-model="explanationPanels" class="algorithm-collapse">
      <el-collapse-item name="algorithm" title="计算口径">
        <p class="formula-line">掌握度 = 正确率 × 0.6 + 速度分 × 0.2 + 训练频次 × 0.2</p>
        <p class="formula-block">$$掌握度 = 正确率 \times 0.6 + 速度分 \times 0.2 + 训练频次 \times 0.2$$</p>
      </el-collapse-item>
    </el-collapse>
  </section>
</template>

<style scoped>
.mastery-radar-panel {
  display: grid;
  gap: var(--qb-space-4);
  margin-top: var(--qb-space-4-5);
}

.radar-legend {
  display: flex;
  flex-wrap: wrap;
  gap: var(--qb-space-2-5);
}

.legend-item {
  display: inline-flex;
  align-items: center;
  gap: var(--qb-space-2);
  padding: var(--qb-space-2) var(--qb-space-3);
  border-radius: var(--qb-radius-pill);
  background: var(--qb-surface-glass-soft);
  color: var(--qb-text-secondary-strong);
  font-size: 12px;
  font-weight: 700;
}

.legend-item::before {
  width: 10px;
  height: 10px;
  border-radius: var(--qb-radius-pill);
  content: '';
}

.legend-item--primary::before {
  background: var(--qb-primary-student);
}

.legend-item--reference::before {
  background: var(--qb-chart-mid);
}

.radar-surface {
  border-radius: var(--qb-radius-2xl);
  background:
    radial-gradient(circle at top, color-mix(in srgb, var(--qb-primary-student) 10%, transparent), transparent 42%),
    linear-gradient(180deg, var(--qb-surface-strong), rgba(244, 247, 252, 1));
  padding: var(--qb-space-4-5);
  min-height: clamp(360px, 50vh, 520px);
  box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--qb-primary-student) 6%, transparent);
}

.radar-stage {
  width: min(100%, 640px);
  margin: 0 auto;
  aspect-ratio: 1 / 1;
}

.mastery-radar {
  width: 100%;
  height: 100%;
}

.interaction-tip {
  padding: var(--qb-space-3) var(--qb-space-3-5);
  border-radius: var(--qb-radius-md);
  background: color-mix(in srgb, var(--qb-primary-student) 5%, white 95%);
  color: var(--qb-text-meta);
  font-size: 12px;
}

.algorithm-collapse {
  border-radius: var(--qb-radius-md);
  background: var(--qb-surface-raised);
  overflow: hidden;
}

.formula-line,
.formula-block {
  margin: 0;
  color: var(--qb-text-subtle-7);
}

.formula-block {
  margin-top: 8px;
  font-family: var(--font-mono);
  white-space: nowrap;
  overflow-x: auto;
}

:deep(.el-loading-mask) {
  border-radius: var(--qb-radius-2xl);
}

:deep(.algorithm-collapse .el-collapse-item__header) {
  padding-inline: var(--qb-space-4);
  font-weight: 600;
  color: var(--qb-text-heading);
  background: color-mix(in srgb, var(--qb-primary-student) 3%, white 97%);
}

:deep(.algorithm-collapse .el-collapse-item__content) {
  padding-inline: var(--qb-space-4);
  padding-bottom: var(--qb-space-4);
}

@media (max-width: 768px) {
  .radar-surface {
    padding: var(--qb-space-3);
    min-height: 320px;
  }

  .radar-stage {
    width: 100%;
  }
}
</style>
