<script setup>
import { computed, defineAsyncComponent, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { ElMessage } from '@/ui/feedback'
import { fetchContentBaseline } from '../../api/services/questionBank'

const KnowledgeGraph = defineAsyncComponent(() => import('../../components/KnowledgeGraph.vue'))
const loading = ref(false)
const distributionRows = ref([])
const barRef = ref(null)
const pieRef = ref(null)
let barChart = null
let pieChart = null
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

const totalCategoryCount = computed(() => distributionRows.value.length)
const totalGroupCount = computed(() =>
  distributionRows.value.reduce((sum, row) => sum + Number(row.jointExamGroupCount || 0), 0),
)
const totalSubjectCount = computed(() =>
  distributionRows.value.reduce((sum, row) => sum + Number(row.subjectCount || 0), 0),
)

function normalizeDistributionRows(baselinePayload) {
  const examCategories = Array.isArray(baselinePayload?.examCategories) ? baselinePayload.examCategories : []
  const normalizedRows = examCategories.map((categoryItem) => {
    const jointExamGroups = Array.isArray(categoryItem?.jointExamGroups) ? categoryItem.jointExamGroups : []
    let subjectCount = 0
    let questionCount = 0
    jointExamGroups.forEach((groupItem) => {
      const subjects = Array.isArray(groupItem?.subjects) ? groupItem.subjects : []
      subjectCount += subjects.length
      questionCount += Number(groupItem?.questionCount || 0)
    })
    return {
      examCategoryCode: String(categoryItem?.examCategoryCode || ''),
      examCategoryName: String(categoryItem?.examCategoryName || categoryItem?.examCategoryCode || '-'),
      jointExamGroupCount: jointExamGroups.length,
      subjectCount,
      questionCount,
    }
  })
  return normalizedRows
    .sort((leftRow, rightRow) => Number(rightRow.questionCount || 0) - Number(leftRow.questionCount || 0))
    .slice(0, 10)
}

function resizeCharts() {
  barChart?.resize()
  pieChart?.resize()
}

function renderBarChart() {
  if (!barRef.value) {
    return
  }
  if (!barChart) {
    barChart = initEcharts(barRef.value)
  }
  barChart.setOption({
    tooltip: {
      trigger: 'axis',
    },
    grid: {
      left: 36,
      right: 20,
      top: 18,
      bottom: 48,
    },
    xAxis: {
      type: 'category',
      axisLine: {
        show: false,
      },
      axisTick: {
        show: false,
      },
      axisLabel: {
        interval: 0,
        rotate: 24,
      },
      data: distributionRows.value.map((row) => row.examCategoryName),
    },
    yAxis: {
      type: 'value',
      axisLine: {
        show: false,
      },
      axisTick: {
        show: false,
      },
      nameTextStyle: {
        color: 'transparent',
      },
      name: '题量',
    },
    series: [
      {
        name: '题量',
        type: 'bar',
        barMaxWidth: 28,
        data: distributionRows.value.map((row) => Number(row.questionCount || 0)),
        itemStyle: {
          color: 'var(--el-color-primary)',
        },
      },
    ],
  })
}

function renderPieChart() {
  if (!pieRef.value) {
    return
  }
  if (!pieChart) {
    pieChart = initEcharts(pieRef.value)
  }
  pieChart.setOption({
    tooltip: {
      trigger: 'item',
    },
    legend: {
      bottom: 0,
      type: 'scroll',
    },
    series: [
      {
        name: '学科门类题量占比',
        type: 'pie',
        radius: ['42%', '68%'],
        center: ['50%', '42%'],
        data: distributionRows.value.map((row) => ({
          name: row.examCategoryName,
          value: Number(row.questionCount || 0),
        })),
      },
    ],
  })
}

async function renderCharts() {
  await nextTick()
  await ensureEchartsRuntime()
  renderBarChart()
  renderPieChart()
  resizeCharts()
}

async function loadDistribution() {
  loading.value = true
  try {
    const baselinePayload = await fetchContentBaseline({ forceRefresh: true })
    distributionRows.value = normalizeDistributionRows(baselinePayload)
    await renderCharts()
  } catch (error) {
    ElMessage.error(String(error?.response?.data?.message || error?.message || '内容体系数据加载失败'))
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadDistribution()
  window.addEventListener('resize', resizeCharts)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeCharts)
  barChart?.dispose()
  pieChart?.dispose()
  barChart = null
  pieChart = null
})

</script>

<template>
  <section class="content-system-shell" v-loading="loading">
    <header class="page-header">
      <h3>内容体系字典</h3>
      <p>按题量统计展示学科门类分布（Top 10）。</p>
    </header>

    <section class="summary-grid">
      <article class="summary-card">
        <span>学科门类数量</span>
        <strong>{{ totalCategoryCount }}</strong>
      </article>
      <article class="summary-card">
        <span>联考组数量</span>
        <strong>{{ totalGroupCount }}</strong>
      </article>
      <article class="summary-card">
        <span>科目数量</span>
        <strong>{{ totalSubjectCount }}</strong>
      </article>
    </section>

    <section class="charts-grid">
      <article class="chart-card">
        <h4>学科门类题量柱状图</h4>
        <div ref="barRef" class="chart-body" />
      </article>
      <article class="chart-card">
        <h4>学科门类题量占比</h4>
        <div ref="pieRef" class="chart-body" />
      </article>
    </section>

    <el-table :data="distributionRows" border>
      <el-table-column prop="examCategoryName" label="学科门类" min-width="160" />
      <el-table-column prop="jointExamGroupCount" label="联考组数" width="120" />
      <el-table-column prop="subjectCount" label="科目数" width="120" />
      <el-table-column prop="questionCount" label="题量" width="120" />
    </el-table>

    <section class="graph-entry">
      <header class="graph-entry-header">
        <h4>知识星系交互入口</h4>
        <p>教师模式默认只看 L1-L3 骨架，点击章节后再展开 L4-L5 细节；进入关系编辑模式后才显示前置依赖线。</p>
      </header>
      <KnowledgeGraph mode="teacher" />
    </section>
  </section>
</template>

<style scoped>
.content-system-shell {
  display: grid;
  gap: 12px;
}

.page-header h3,
.page-header p {
  margin: 0;
}

.page-header p {
  margin-top: 6px;
  color: var(--qb-text-subtle-7);
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.summary-card {
  border: 1px solid var(--qb-primary-soft-border);
  border-radius: 12px;
  background: var(--qb-primary-soft-bg);
  padding: 12px;
  display: grid;
  gap: 8px;
}

.summary-card strong {
  font-size: 24px;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.chart-card {
  border: 1px solid var(--qb-primary-soft-border);
  border-radius: 12px;
  background: var(--qb-bg-card);
  padding: 12px;
}

.chart-card h4 {
  margin: 0;
}

.chart-body {
  width: 100%;
  height: 320px;
}

.graph-entry {
  display: grid;
  gap: 10px;
}

.graph-entry-header h4,
.graph-entry-header p {
  margin: 0;
}

.graph-entry-header p {
  margin-top: 6px;
  color: var(--qb-text-subtle-7);
}

@media (max-width: 980px) {
  .summary-grid,
  .charts-grid {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
