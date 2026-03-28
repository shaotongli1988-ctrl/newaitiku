<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from '@/ui/feedback'
import { useRoute, useRouter } from 'vue-router'
import { resolveApiErrorMessage } from '../../api/request'
import {
  completeStudentPersonalBankReviewPlanQuestion,
  getStudentPersonalBankReviewPlan,
  knowledgeTreeV2,
  listStudentPersonalBankQuestions,
  listStudentPersonalBankReviewPlans,
  restoreArchivedWrongBook,
  startStudentPersonalBankReviewPlan,
  studentPersonalBankExport,
  studentPersonalBankSummary,
} from '../../api/services/questionBank'
import QuestionBankActionGroup from '../../components/student/QuestionBankActionGroup.vue'
import QuestionBankCardActions from '../../components/student/QuestionBankCardActions.vue'
import QuestionBankEmptyState from '../../components/student/QuestionBankEmptyState.vue'
import QuestionBankFilterPanel from '../../components/student/QuestionBankFilterPanel.vue'
import QuestionBankPageHeader from '../../components/student/QuestionBankPageHeader.vue'
import QuestionBankResultSection from '../../components/student/QuestionBankResultSection.vue'
import QuestionBankSectionHeader from '../../components/student/QuestionBankSectionHeader.vue'
import { useStudentQuestionBankKnowledge } from '../../composables/student-question-bank/useStudentQuestionBankKnowledge.js'
import { useStudentQuestionBankNavigation } from '../../composables/student-question-bank/useStudentQuestionBankNavigation.js'
import { useStudentQuestionBankScope } from '../../composables/student-question-bank/useStudentQuestionBankScope.js'
import { useRequest } from '../../composables/useRequest.js'
import { useSubjectContextStore } from '../../stores/subjectContextStore.js'
import { questionTypeLabel } from '../../utils/question'
import {
  buildPersonalBankQuestionMeta,
  formatQuestionBankDateTime,
} from '../../utils/studentQuestionBankMeta'

const DEFAULT_PAGE_SIZE = 20
const PAGE_SIZE_OPTIONS = [20, 50, 100]

const route = useRoute()
const router = useRouter()
const subjectContextStore = useSubjectContextStore()

const rows = ref([])
const total = ref(0)
const exporting = ref(false)
const questionGridRef = ref(null)
const exportFormat = ref('csv')
const keywordSearch = ref('')
const reviewPlans = ref([])
const activeReviewPlanId = ref('')
const activeReviewPlanDetail = ref(null)
const planActionBusy = ref(false)
const summaryData = ref({
  totalCount: 0,
  answeredCount: 0,
  accuracy: '0%',
  unansweredCount: 0,
  recentCollectedAt: '',
  archivedCount: 0,
  archivedLast7DaysCount: 0,
  archivedLast30DaysCount: 0,
  archivedEarlierCount: 0,
  subjectRankings: [],
  reviewPlan: [],
  recommendedPlanKey: '',
})

const {
  chapterName,
  chapterCode,
  pointCode,
  pointName,
  knowledgeId,
  knowledgePathNodeId,
  pathLabel,
  effectiveSubjectCode,
  buildScopeFilters,
  buildAnalysisQuery,
} = useStudentQuestionBankScope({
  route,
  currentSubjectCode: computed(() => subjectContextStore.currentSubjectCode),
})

const keywordQuery = computed(() => String(route.query.keyword || '').trim())
const archiveWindow = computed(() => String(route.query.archiveWindow || '').trim().toUpperCase())
const currentPage = computed(() => normalizePositiveInt(route.query.page, 1))
const currentPageSize = computed(() => {
  const normalized = normalizePositiveInt(route.query.size, DEFAULT_PAGE_SIZE)
  return PAGE_SIZE_OPTIONS.includes(normalized) ? normalized : DEFAULT_PAGE_SIZE
})
const selectedSubjectLabel = computed(() => {
  const subjectOptions = Array.isArray(subjectContextStore.subjectOptions) ? subjectContextStore.subjectOptions : []
  const matched = subjectOptions.find((item) => String(item?.subjectCode || '').trim() === effectiveSubjectCode.value)
  return String(matched?.subjectName || effectiveSubjectCode.value || '').trim()
})

const {
  knowledgeTreeLoading,
  knowledgeFilterOptions,
  selectedKnowledgePath,
  knowledgeSelectorState,
  knowledgeSemanticMap,
  loadKnowledgeTree,
  handleKnowledgePathChange,
  syncSelectedKnowledgePathFromRoute,
} = useStudentQuestionBankKnowledge({
  route,
  router,
  effectiveSubjectCode,
  knowledgePathNodeId,
  knowledgeId,
  chapterCode,
  pointCode,
  fetchKnowledgeTree: knowledgeTreeV2,
  loadErrorMessage: '沉淀题库知识树加载失败',
})

const { openKnowledgeDiagnosis, jumpToKnowledgePractice } = useStudentQuestionBankNavigation({
  router,
  effectiveSubjectCode,
  buildAnalysisQuery,
})

const knowledgeCascaderProps = {
  value: 'value',
  label: 'label',
  children: 'children',
  emitPath: true,
  checkStrictly: true,
}

const archiveWindowOptions = [
  { label: '全部题目', value: '' },
  { label: '全部已归档', value: 'ARCHIVED' },
  { label: '近 7 天归档', value: 'LAST_7_DAYS' },
  { label: '近 30 天归档', value: 'LAST_30_DAYS' },
  { label: '30 天前归档', value: 'EARLIER' },
]

const reviewPlanRows = computed(() => Array.isArray(reviewPlans.value) ? reviewPlans.value : [])
const summaryReviewPlanRows = computed(() => Array.isArray(summaryData.value.reviewPlan) ? summaryData.value.reviewPlan : [])
const visibleReviewPlanRows = computed(() =>
  reviewPlanRows.value
    .map((plan) => {
      const planId = String(plan?.planId || '').trim()
      const planKey = String(plan?.planKey || '').trim()
      const scopedPlan = summaryReviewPlanRows.value.find((item) => (
        String(item?.planId || '').trim() === planId
          || (planKey && String(item?.planKey || '').trim() === planKey)
      ))
      if (!scopedPlan) {
        return {
          ...plan,
          questionCount: 0,
          questionIds: [],
          completedCount: 0,
        }
      }
      return {
        ...plan,
        ...scopedPlan,
        startedAt: String(plan?.startedAt || scopedPlan?.startedAt || '').trim(),
        completedAt: String(plan?.completedAt || scopedPlan?.completedAt || '').trim(),
        lastExecutedAt: String(plan?.lastExecutedAt || scopedPlan?.lastExecutedAt || '').trim(),
        actionLabel: String(plan?.actionLabel || scopedPlan?.actionLabel || '').trim(),
      }
    })
    .filter((plan) => Number(plan?.questionCount || 0) > 0 || String(plan?.planId || '').trim() === activeReviewPlanId.value)
    .sort((left, right) => {
      const leftIsRecommended = String(left?.planKey || '').trim() === summaryData.value.recommendedPlanKey
      const rightIsRecommended = String(right?.planKey || '').trim() === summaryData.value.recommendedPlanKey
      if (leftIsRecommended !== rightIsRecommended) {
        return leftIsRecommended ? -1 : 1
      }
      const leftRank = reviewPlanStatusRank(left?.status)
      const rightRank = reviewPlanStatusRank(right?.status)
      if (leftRank !== rightRank) {
        return leftRank - rightRank
      }
      const leftQuestionCount = Number(left?.questionCount || 0)
      const rightQuestionCount = Number(right?.questionCount || 0)
      if (leftQuestionCount !== rightQuestionCount) {
        return rightQuestionCount - leftQuestionCount
      }
      return String(left?.planName || '').localeCompare(String(right?.planName || ''), 'zh-Hans-CN')
    }),
)
const activeReviewPlan = computed(() =>
  visibleReviewPlanRows.value.find((item) => String(item?.planId || '').trim() === activeReviewPlanId.value)
  || reviewPlanRows.value.find((item) => String(item?.planId || '').trim() === activeReviewPlanId.value)
  || null,
)
const activeReviewPlanScopedQuestionIds = computed(() => (
  Array.isArray(activeReviewPlan.value?.questionIds)
    ? activeReviewPlan.value.questionIds.map((item) => String(item || '').trim()).filter((item) => item)
    : []
))
const activeReviewPlanItems = computed(() => {
  const items = Array.isArray(activeReviewPlanDetail.value?.items) ? activeReviewPlanDetail.value.items : []
  if (!activeReviewPlanScopedQuestionIds.value.length) {
    return items
  }
  const scopedQuestionIdSet = new Set(activeReviewPlanScopedQuestionIds.value)
  return items.filter((item) => scopedQuestionIdSet.has(String(item?.questionId || '').trim()))
})
const activeReviewPlanItemMap = computed(() => {
  const map = {}
  activeReviewPlanItems.value.forEach((item) => {
    const questionId = String(item?.questionId || '').trim()
    if (questionId) {
      map[questionId] = item
    }
  })
  return map
})
const activeReviewQuestionIds = computed(() => (
  activeReviewPlanItems.value.length
    ? activeReviewPlanItems.value.map((item) => String(item?.questionId || '').trim()).filter((item) => item)
    : activeReviewPlanScopedQuestionIds.value
))
const activeArchiveWindowLabel = computed(() =>
  archiveWindowOptions.find((item) => item.value === archiveWindow.value)?.label || '',
)
const hasActiveReviewPlan = computed(() => Boolean(activeReviewPlanId.value && activeReviewPlan.value))
const pageBusy = computed(() => loading.value || summaryLoading.value || reviewPlansLoading.value || reviewPlanDetailLoading.value || exporting.value || planActionBusy.value)

const activeFilterTags = computed(() => {
  const tags = []
  if (keywordQuery.value) {
    tags.push({ label: '关键词', value: keywordQuery.value })
  }
  if (pathLabel.value) {
    tags.push({ label: '知识路径', value: pathLabel.value })
  }
  if (archiveWindow.value) {
    tags.push({ label: '归档范围', value: activeArchiveWindowLabel.value || archiveWindow.value })
  }
  if (activeReviewPlan.value?.planName) {
    tags.push({ label: '复习计划', value: activeReviewPlan.value.planName })
  }
  return tags
})

const headerDescription = computed(() => {
  if (activeReviewPlan.value?.planName) {
    return `当前按复习计划“${activeReviewPlan.value.planName}”查看结果，支持继续按关键词和知识路径缩小范围。把这批题反复练顺，更容易把已经会做的分稳定留在卷面上。`
  }
  if (keywordQuery.value) {
    return `当前按关键词“${keywordQuery.value}”检索沉淀题库，可继续叠加知识路径和归档范围。`
  }
  if (activeArchiveWindowLabel.value) {
    return `当前按归档范围筛选：${activeArchiveWindowLabel.value}`
  }
  if (pathLabel.value) {
    return `当前按知识路径筛选：${pathLabel.value}`
  }
  if (pointCode.value) {
    return `当前按考点聚焦：${pointName.value || pointCode.value}`
  }
  if (chapterCode.value) {
    return `当前按章节聚焦：${chapterName.value || chapterCode.value}`
  }
  if (selectedSubjectLabel.value) {
    return `当前按科目聚焦：${selectedSubjectLabel.value}`
  }
  return '支持关键词、知识路径、归档范围和复习计划联动筛选，把已经做过的题重新组织成可反复提分的资产池。'
})

const personalBankBridgeCopy = computed(() => {
  if (hasActiveReviewPlan.value) {
    return `沉淀题库不是简单归档区，而是在帮你把已经做过的题重新组织成“能反复回收分数”的资产池。当前切到正式计划后，持续把这批题练顺，更容易让段位分和考场稳定性一起上来。`
  }
  if (activeArchiveWindowLabel.value) {
    return `当前重点看的是“${activeArchiveWindowLabel.value}”。这些题已经被你做过一轮，再回练的价值在于把偶然做对变成稳定做对，让后续积分增长和升本得分都更扎实。`
  }
  return '沉淀题库不是仓库，它的价值在于把做过的题重新组织成可反复回练、持续回收分数的资产。练习积分想涨得稳，最后还是要靠这些已经碰过的题目被真正练成熟。'
})

const personalBankMomentumCopy = computed(() => {
  if (activeReviewPlan.value?.planName) {
    return `先把计划“${activeReviewPlan.value.planName}”里的题吃透，再去刷下一轮新题，通常更容易把会做的题稳定成卷面分。`
  }
  if (selectedSubjectLabel.value) {
    return `先在 ${selectedSubjectLabel.value} 里把高频归档题练顺，再去刷题冲分，段位分通常会涨得更稳。`
  }
  return '先把沉淀题库里的高频题练顺，再去刷题冲分，段位分通常会涨得更稳。'
})

const normalizedRows = computed(() =>
  (Array.isArray(rows.value) ? rows.value : []).map((row) => ({
    ...row,
    _meta: buildPersonalBankQuestionMeta(row, { knowledgeSemanticMap: knowledgeSemanticMap.value }),
  })),
)

const archivedHarvestedRows = computed(() =>
  normalizedRows.value.filter((row) => row._meta.isArchived),
)
const shouldHighlightArchivedRows = computed(() => Boolean(archiveWindow.value))
const activeReviewPlanCompletedCount = computed(() => Number(activeReviewPlan.value?.completedCount || 0))
const activeReviewPlanQuestionCount = computed(() => Number(activeReviewPlan.value?.questionCount || 0))
const activeReviewPlanPendingCount = computed(() =>
  Math.max(0, activeReviewPlanQuestionCount.value - activeReviewPlanCompletedCount.value),
)
const activeReviewPlanProgressText = computed(() => {
  if (!hasActiveReviewPlan.value) {
    return ''
  }
  return `已完成 ${activeReviewPlanCompletedCount.value} / ${activeReviewPlanQuestionCount.value} 题`
})
const activeReviewPlanTimelineText = computed(() => {
  if (!hasActiveReviewPlan.value) {
    return ''
  }
  const segments = [
    activeReviewPlan.value?.startedAt ? `开始于 ${formatQuestionBankDateTime(activeReviewPlan.value.startedAt)}` : '',
    activeReviewPlan.value?.lastExecutedAt ? `最近执行 ${formatQuestionBankDateTime(activeReviewPlan.value.lastExecutedAt)}` : '',
    activeReviewPlan.value?.completedAt ? `完成于 ${formatQuestionBankDateTime(activeReviewPlan.value.completedAt)}` : '',
  ].filter((item) => item)
  return segments.join(' · ')
})
const reviewPlanSectionDescription = computed(() => {
  if (hasActiveReviewPlan.value) {
    return `当前已切入正式复习计划“${activeReviewPlan.value?.planName || ''}”，筛选、汇总和结果会基于同一题目范围同步更新。`
  }
  return '正式复习计划不再是汇总里的临时建议分组，点击后会切到可执行、可追踪的计划视角。'
})
const resultSectionDescription = computed(() => (
  hasActiveReviewPlan.value
    ? `当前结果已收敛到计划“${activeReviewPlan.value?.planName || ''}”命中的题目，可直接回练并记录计划完成。把这批题练熟，更容易把会做的题稳定成考试得分。`
    : '列表优先展示当前筛选条件下可直接回练、恢复和导出的题目。这里更像提分资产池，而不只是归档列表。'
))

const summaryCards = computed(() => [
  { label: '沉淀题数', value: Number(summaryData.value.totalCount || 0) },
  { label: '已作答', value: Number(summaryData.value.answeredCount || 0) },
  { label: '正确率', value: String(summaryData.value.accuracy || '0%') },
  { label: '未作答', value: Number(summaryData.value.unansweredCount || 0) },
  {
    label: '全部已归档',
    value: Number(summaryData.value.archivedCount || 0),
    interactive: true,
    isActive: archiveWindow.value === 'ARCHIVED',
    actionValue: 'ARCHIVED',
    helper: '查看全部已斩获归档题',
  },
  {
    label: '近 7 天归档',
    value: Number(summaryData.value.archivedLast7DaysCount || 0),
    interactive: true,
    isActive: archiveWindow.value === 'LAST_7_DAYS',
    actionValue: 'LAST_7_DAYS',
    helper: '优先回看最新归档题',
  },
  {
    label: '近 30 天归档',
    value: Number(summaryData.value.archivedLast30DaysCount || 0),
    interactive: true,
    isActive: archiveWindow.value === 'LAST_30_DAYS',
    actionValue: 'LAST_30_DAYS',
    helper: '适合做阶段性回收',
  },
  {
    label: '30 天前归档',
    value: Number(summaryData.value.archivedEarlierCount || 0),
    interactive: true,
    isActive: archiveWindow.value === 'EARLIER',
    actionValue: 'EARLIER',
    helper: '适合做长尾盘点',
  },
])

const listMetaText = computed(() => {
  if (listErrorMessage.value) {
    return ''
  }
  const pageLabel = `第 ${currentPage.value} / ${Math.max(1, Math.ceil(Number(total.value || 0) / currentPageSize.value))} 页`
  return `共 ${Number(total.value || 0)} 条结果 · ${pageLabel}`
})

const resultSummary = computed(() => {
  const base = activeReviewPlan.value?.planName
    ? `当前计划“${activeReviewPlan.value.planName}”命中 ${Number(total.value || 0)} 道题`
    : `当前共找到 ${Number(total.value || 0)} 道题`
  const recentCollectedAt = formatQuestionBankDateTime(summaryData.value.recentCollectedAt)
  if (recentCollectedAt !== '-') {
    return `${base} · 最近收藏 ${recentCollectedAt}`
  }
  return base
})

const questionEmptyDescription = computed(() => {
  if (activeReviewPlan.value?.planName) {
    return `复习计划“${activeReviewPlan.value.planName}”在当前筛选条件下暂无题目。`
  }
  if (keywordQuery.value) {
    return `没有找到与“${keywordQuery.value}”相关的题目。`
  }
  if (pathLabel.value) {
    return '当前知识路径下暂无沉淀题库题目。'
  }
  if (archiveWindow.value) {
    return '当前归档范围下暂无沉淀题库题目。'
  }
  return '当前筛选条件下暂无沉淀题库题目。'
})

function normalizePositiveInt(value, fallback) {
  const numeric = Number(value)
  if (!Number.isFinite(numeric) || numeric < 1) {
    return fallback
  }
  return Math.floor(numeric)
}

function normalizeAccuracy(value) {
  const numericValue = Number(value || 0)
  if (!Number.isFinite(numericValue)) {
    return '0%'
  }
  if (numericValue <= 1) {
    return `${Math.round(numericValue * 100)}%`
  }
  return `${Math.round(numericValue)}%`
}

function resolveErrorCardMessage(error, fallback) {
  return resolveApiErrorMessage(error, fallback)
}

function planStatusLabel(status) {
  const normalized = String(status || '').trim().toUpperCase()
  if (normalized === 'COMPLETED') {
    return '已完成'
  }
  if (normalized === 'IN_PROGRESS') {
    return '进行中'
  }
  return '待开始'
}

function reviewPlanStatusRank(status) {
  const normalized = String(status || '').trim().toUpperCase()
  if (normalized === 'IN_PROGRESS') {
    return 0
  }
  if (normalized === 'PENDING') {
    return 1
  }
  if (normalized === 'COMPLETED') {
    return 2
  }
  return 3
}

function planStatusTagType(status) {
  const normalized = String(status || '').trim().toUpperCase()
  if (normalized === 'COMPLETED') {
    return 'success'
  }
  if (normalized === 'IN_PROGRESS') {
    return 'primary'
  }
  return 'info'
}

function resolvePlanPrimaryActionLabel(plan) {
  const normalizedStatus = String(plan?.status || '').trim().toUpperCase()
  if (normalizedStatus === 'IN_PROGRESS') {
    return '继续执行'
  }
  if (normalizedStatus === 'COMPLETED') {
    return '查看计划'
  }
  return String(plan?.actionLabel || '').trim() || '开始执行'
}

function planQuestionStatusLabel(status) {
  return String(status || '').trim().toUpperCase() === 'COMPLETED' ? '本题已完成' : '待完成'
}

function planQuestionStatusType(status) {
  return String(status || '').trim().toUpperCase() === 'COMPLETED' ? 'success' : 'warning'
}

function getActiveReviewPlanItem(questionId) {
  return activeReviewPlanItemMap.value[String(questionId || '').trim()] || null
}

function isActiveReviewPlanQuestionCompleted(questionId) {
  return String(getActiveReviewPlanItem(questionId)?.status || '').trim().toUpperCase() === 'COMPLETED'
}

function canRestoreArchivedRow(row) {
  return Boolean(row?._meta?.isArchived)
}

function filterKnowledgeNode(node, keyword) {
  const normalizedKeyword = String(keyword || '').trim().toLowerCase()
  if (!normalizedKeyword) {
    return true
  }
  const semanticPath = String(knowledgeSemanticMap.value[node?.value]?.fullPathLabel || '').trim().toLowerCase()
  const chapterCodeLabel = String(knowledgeSelectorState.value?.chapterCodeMap?.[node?.value] || '').trim().toLowerCase()
  const pointCodeLabel = String(knowledgeSelectorState.value?.pointCodeMap?.[node?.value] || '').trim().toLowerCase()
  const currentLabel = String(node?.label || '').trim().toLowerCase()
  return [semanticPath, chapterCodeLabel, pointCodeLabel, currentLabel].some((item) => item.includes(normalizedKeyword))
}

function buildSummaryFilters() {
  const filters = buildScopeFilters({
    keyword: keywordQuery.value,
    archiveWindow: archiveWindow.value,
  })
  if (hasActiveReviewPlan.value && activeReviewQuestionIds.value.length) {
    filters.questionIds = activeReviewQuestionIds.value.join(',')
  }
  return filters
}

function buildReviewPlanFilters() {
  return buildScopeFilters({
    keyword: keywordQuery.value,
    archiveWindow: archiveWindow.value,
  })
}

function buildListFilters() {
  const filters = buildScopeFilters({
    keyword: keywordQuery.value,
    archiveWindow: archiveWindow.value,
    page: currentPage.value,
    size: currentPageSize.value,
  })
  if (activeReviewQuestionIds.value.length) {
    filters.questionIds = activeReviewQuestionIds.value.join(',')
  }
  return filters
}

function buildExportFilters() {
  const filters = buildScopeFilters({
    keyword: keywordQuery.value,
    archiveWindow: archiveWindow.value,
    format: exportFormat.value,
  })
  if (activeReviewQuestionIds.value.length) {
    filters.questionIds = activeReviewQuestionIds.value.join(',')
  }
  return filters
}

async function updateRouteQuery(patch, { resetPage = false } = {}) {
  const nextQuery = { ...route.query }
  Object.entries(patch || {}).forEach(([key, value]) => {
    const normalized = String(value ?? '').trim()
    if (value === null || value === undefined || normalized === '') {
      delete nextQuery[key]
      return
    }
    nextQuery[key] = normalized
  })
  if (resetPage) {
    delete nextQuery.page
  }
  await router.replace({ path: route.path, query: nextQuery })
}

function syncKeywordSearchFromRoute() {
  keywordSearch.value = keywordQuery.value
}

function downloadTextFile(fileName, mediaType, content) {
  const blob = new Blob([String(content || '')], { type: mediaType || 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = fileName
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

function resolveExportFileName(format) {
  const subjectLabel = selectedSubjectLabel.value || effectiveSubjectCode.value || '沉淀题库'
  const suffix = String(format || 'csv').trim().toLowerCase() === 'pdf' ? 'pdf' : 'csv'
  return `${subjectLabel}-沉淀题库.${suffix}`
}

function resolveExportMediaType(format) {
  return String(format || 'csv').trim().toLowerCase() === 'pdf'
    ? 'application/pdf'
    : 'text/csv;charset=utf-8'
}

async function scrollToResults() {
  const target = questionGridRef.value
  if (target && typeof target.scrollIntoView === 'function') {
    target.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

const {
  loading: summaryLoading,
  error: summaryError,
  run: loadSummary,
} = useRequest(
  async () => {
    const payload = await studentPersonalBankSummary(buildSummaryFilters())
    const data = payload?.data && typeof payload.data === 'object' ? payload.data : payload || {}
    summaryData.value = {
      totalCount: Number(data?.totalCount || 0),
      answeredCount: Number(data?.answeredCount || 0),
      accuracy: normalizeAccuracy(data?.accuracy),
      unansweredCount: Number(data?.unansweredCount || 0),
      recentCollectedAt: String(data?.recentCollectedAt || '').trim(),
      archivedCount: Number(data?.archivedCount || 0),
      archivedLast7DaysCount: Number(data?.archivedLast7DaysCount || 0),
      archivedLast30DaysCount: Number(data?.archivedLast30DaysCount || 0),
      archivedEarlierCount: Number(data?.archivedEarlierCount || 0),
      subjectRankings: Array.isArray(data?.subjectRankings) ? data.subjectRankings : [],
      reviewPlan: Array.isArray(data?.reviewPlan) ? data.reviewPlan : [],
      recommendedPlanKey: String(data?.recommendedPlanKey || '').trim(),
    }
    return data
  },
  {
    onError(error) {
      summaryData.value = {
        totalCount: 0,
        answeredCount: 0,
        accuracy: '0%',
        unansweredCount: 0,
        recentCollectedAt: '',
        archivedCount: 0,
        archivedLast7DaysCount: 0,
        archivedLast30DaysCount: 0,
        archivedEarlierCount: 0,
        subjectRankings: [],
        reviewPlan: [],
        recommendedPlanKey: '',
      }
      ElMessage.error(resolveErrorCardMessage(error, '沉淀题库汇总加载失败'))
    },
  },
)

const {
  loading: reviewPlansLoading,
  error: reviewPlansError,
  run: loadReviewPlans,
} = useRequest(
  async () => {
    const payload = await listStudentPersonalBankReviewPlans(buildReviewPlanFilters())
    const data = Array.isArray(payload?.data) ? payload.data : Array.isArray(payload) ? payload : []
    reviewPlans.value = data
    if (activeReviewPlanId.value && !data.some((item) => String(item?.planId || '').trim() === activeReviewPlanId.value)) {
      activeReviewPlanId.value = ''
      activeReviewPlanDetail.value = null
    }
    return data
  },
  {
    onError(error) {
      reviewPlans.value = []
      activeReviewPlanId.value = ''
      activeReviewPlanDetail.value = null
      ElMessage.error(resolveErrorCardMessage(error, '复习计划加载失败'))
    },
  },
)

const {
  loading: reviewPlanDetailLoading,
  error: reviewPlanDetailError,
  run: loadReviewPlanDetail,
} = useRequest(
  async (planId) => {
    const normalizedPlanId = String(planId || '').trim()
    if (!normalizedPlanId) {
      activeReviewPlanDetail.value = null
      return null
    }
    const payload = await getStudentPersonalBankReviewPlan(normalizedPlanId, buildReviewPlanFilters())
    const data = payload?.data && typeof payload.data === 'object' ? payload.data : payload || null
    activeReviewPlanDetail.value = data
    return data
  },
  {
    onError(error) {
      activeReviewPlanDetail.value = null
      ElMessage.error(resolveErrorCardMessage(error, '复习计划详情加载失败'))
    },
  },
)

const {
  loading,
  error: listError,
  run: loadRows,
} = useRequest(
  async () => {
    if (hasActiveReviewPlan.value && !activeReviewQuestionIds.value.length) {
      rows.value = []
      total.value = 0
      return { items: [], total: 0 }
    }
    const payload = await listStudentPersonalBankQuestions(buildListFilters())
    const data = payload?.data && typeof payload.data === 'object' ? payload.data : payload || {}
    rows.value = Array.isArray(data?.items) ? data.items : []
    total.value = Number(data?.total || 0)
    return data
  },
  {
    onError(error) {
      rows.value = []
      total.value = 0
      ElMessage.error(resolveErrorCardMessage(error, '沉淀题库列表加载失败'))
    },
  },
)

const summaryErrorMessage = computed(() => (
  summaryError.value ? resolveErrorCardMessage(summaryError.value, '沉淀题库汇总加载失败') : ''
))
const reviewPlansErrorMessage = computed(() => (
  reviewPlansError.value ? resolveErrorCardMessage(reviewPlansError.value, '复习计划加载失败') : ''
))
const reviewPlanDetailErrorMessage = computed(() => (
  reviewPlanDetailError.value ? resolveErrorCardMessage(reviewPlanDetailError.value, '复习计划详情加载失败') : ''
))
const listErrorMessage = computed(() => (
  listError.value ? resolveErrorCardMessage(listError.value, '沉淀题库列表加载失败') : ''
))

async function refreshPageData({ includeSummary = true, includeKnowledge = false, includeReviewPlans = true } = {}) {
  const preloads = []
  if (includeKnowledge) {
    preloads.push(loadKnowledgeTree())
  }
  if (includeReviewPlans) {
    await loadReviewPlans()
  }
  if (includeSummary) {
    await loadSummary()
  }
  if (preloads.length) {
    await Promise.all(preloads)
  }
  if (activeReviewPlanId.value) {
    await loadReviewPlanDetail(activeReviewPlanId.value)
  }
  await loadRows()
}

async function handleArchiveWindowChange(nextWindow) {
  await updateRouteQuery({ archiveWindow: String(nextWindow || '').trim().toUpperCase() }, { resetPage: true })
}

async function handleKeywordSearch() {
  await updateRouteQuery({ keyword: keywordSearch.value.trim() }, { resetPage: true })
}

async function handleKeywordClear() {
  keywordSearch.value = ''
  await updateRouteQuery({ keyword: '' }, { resetPage: true })
}

async function handleKnowledgePathFilterChange(nextPath) {
  await handleKnowledgePathChange(nextPath)
  if (currentPage.value !== 1) {
    await updateRouteQuery({ page: '1' })
  }
}

async function handlePageChange(nextPage) {
  await updateRouteQuery({ page: String(nextPage || 1) })
  await scrollToResults()
}

async function handlePageSizeChange(nextSize) {
  await updateRouteQuery({ size: String(nextSize || DEFAULT_PAGE_SIZE), page: '1' })
}

async function resetPersonalBankFilters() {
  keywordSearch.value = ''
  activeReviewPlanId.value = ''
  activeReviewPlanDetail.value = null
  const nextQuery = {}
  if (effectiveSubjectCode.value) {
    nextQuery.subjectCode = effectiveSubjectCode.value
  }
  await router.replace({ path: route.path, query: nextQuery })
}

async function handleSummaryCardClick(card) {
  if (!card?.interactive) {
    return
  }
  if (card.isActive) {
    await handleArchiveWindowChange('')
    return
  }
  await handleArchiveWindowChange(card.actionValue)
}

async function applyReviewPlan(plan) {
  const planId = String(plan?.planId || '').trim()
  if (!planId) {
    return
  }
  const shouldStart = String(plan?.status || '').trim().toUpperCase() === 'PENDING'
  try {
    planActionBusy.value = true
    if (shouldStart) {
      await startStudentPersonalBankReviewPlan(planId, buildReviewPlanFilters())
      ElMessage.success('复习计划已开始执行。')
      await loadReviewPlans()
      await loadSummary()
    }
    activeReviewPlanId.value = planId
    await loadReviewPlanDetail(planId)
    await loadSummary()
  } catch (error) {
    ElMessage.error(resolveErrorCardMessage(error, shouldStart ? '开始复习计划失败' : '复习计划加载失败'))
    return
  } finally {
    planActionBusy.value = false
  }
  if (currentPage.value !== 1) {
    await updateRouteQuery({ page: '1' })
    return
  }
  await loadRows()
}

async function clearReviewPlan() {
  if (!activeReviewPlanId.value) {
    return
  }
  activeReviewPlanId.value = ''
  activeReviewPlanDetail.value = null
  await loadSummary()
  if (currentPage.value !== 1) {
    await updateRouteQuery({ page: '1' })
    return
  }
  await loadRows()
}

async function completeReviewPlanQuestion(row) {
  const planId = String(activeReviewPlan.value?.planId || '').trim()
  const questionId = String(row?.id || '').trim()
  if (!planId || !questionId) {
    return
  }
  try {
    planActionBusy.value = true
    await completeStudentPersonalBankReviewPlanQuestion(planId, questionId, buildReviewPlanFilters())
    ElMessage.success('已记录本题复习完成。')
    await loadReviewPlans()
    await loadSummary()
    await loadReviewPlanDetail(planId)
    await loadRows()
  } catch (error) {
    ElMessage.error(resolveErrorCardMessage(error, '记录复习完成失败'))
  } finally {
    planActionBusy.value = false
  }
}

async function jumpToPractice(row) {
  await jumpToKnowledgePractice(row)
}

async function openChallengePoints() {
  const subjectCode = String(effectiveSubjectCode.value || '').trim()
  await router.push({
    path: '/student/analysis/points',
    query: subjectCode ? { subjectCode } : {},
  })
}

async function restoreHarvested(row) {
  const questionId = String(row?.id || '').trim()
  if (!questionId) {
    return
  }
  try {
    await ElMessageBox.confirm('该题将恢复到错题中心，便于重新加入修错流程。', '确认恢复', {
      type: 'warning',
      confirmButtonText: '确认恢复',
      cancelButtonText: '取消',
    })
    const response = await restoreArchivedWrongBook({ questionIds: [questionId] })
    const data = response?.data && typeof response.data === 'object' ? response.data : response || {}
    ElMessage.success(`已恢复 ${Number(data?.restoredCount || 0)} 道题到错题中心。`)
    await refreshPageData({ includeSummary: true, includeKnowledge: false })
  } catch (error) {
    const normalizedError = String(error || '')
    if (normalizedError.includes('cancel') || normalizedError.includes('close')) {
      return
    }
    ElMessage.error(resolveErrorCardMessage(error, '恢复失败'))
  }
}

async function restoreCurrentHarvested() {
  const questionIds = archivedHarvestedRows.value.map((row) => String(row?.id || '').trim()).filter((item) => item)
  if (!questionIds.length) {
    ElMessage.warning('当前结果中没有可恢复的已斩获题。')
    return
  }
  try {
    await ElMessageBox.confirm(
      `将恢复当前结果中命中的 ${questionIds.length} 道已斩获题到错题中心。`,
      '确认批量恢复',
      {
        type: 'warning',
        confirmButtonText: '确认恢复',
        cancelButtonText: '取消',
      },
    )
    const response = await restoreArchivedWrongBook({ questionIds })
    const data = response?.data && typeof response.data === 'object' ? response.data : response || {}
    ElMessage.success(`已批量恢复 ${Number(data?.restoredCount || 0)} 道题到错题中心。`)
    await refreshPageData({ includeSummary: true, includeKnowledge: false })
  } catch (error) {
    const normalizedError = String(error || '')
    if (normalizedError.includes('cancel') || normalizedError.includes('close')) {
      return
    }
    ElMessage.error(resolveErrorCardMessage(error, '批量恢复失败'))
  }
}

async function handleExportCurrentResult() {
  try {
    exporting.value = true
    const payload = await studentPersonalBankExport(buildExportFilters())
    const data = payload?.data && typeof payload.data === 'object' ? payload.data : payload || {}
    const format = String(data?.format || exportFormat.value || 'csv').trim().toLowerCase()
    downloadTextFile(resolveExportFileName(format), resolveExportMediaType(format), data?.content || '')
    ElMessage.success(`已导出当前结果（${format.toUpperCase()}）。`)
  } catch (error) {
    ElMessage.error(resolveErrorCardMessage(error, '沉淀题库导出失败'))
  } finally {
    exporting.value = false
  }
}

onMounted(async () => {
  syncKeywordSearchFromRoute()
  await refreshPageData({ includeSummary: true, includeKnowledge: true })
})

watch(
  () => keywordQuery.value,
  () => {
    syncKeywordSearchFromRoute()
  },
)

watch(
  () => effectiveSubjectCode.value,
  async (nextSubjectCode, previousSubjectCode) => {
    if (nextSubjectCode === previousSubjectCode) {
      return
    }
    activeReviewPlanId.value = ''
    activeReviewPlanDetail.value = null
    await refreshPageData({ includeSummary: true, includeKnowledge: true })
  },
)

watch(
  () => [chapterCode.value, pointCode.value, knowledgeId.value, knowledgePathNodeId.value],
  async ([nextChapterCode, nextPointCode, nextKnowledgeId, nextPathNodeId], [previousChapterCode, previousPointCode, previousKnowledgeId, previousPathNodeId]) => {
    if (
      nextChapterCode === previousChapterCode
      && nextPointCode === previousPointCode
      && nextKnowledgeId === previousKnowledgeId
      && nextPathNodeId === previousPathNodeId
    ) {
      return
    }
    syncSelectedKnowledgePathFromRoute()
    await refreshPageData({ includeSummary: true, includeKnowledge: false })
  },
)

watch(
  () => [archiveWindow.value, keywordQuery.value],
  async ([nextArchiveWindow, nextKeyword], [previousArchiveWindow, previousKeyword]) => {
    if (nextArchiveWindow === previousArchiveWindow && nextKeyword === previousKeyword) {
      return
    }
    await refreshPageData({ includeSummary: true, includeKnowledge: false })
    await scrollToResults()
  },
)

watch(
  () => [currentPage.value, currentPageSize.value],
  async ([nextPage, nextPageSize], [previousPage, previousPageSize]) => {
    if (nextPage === previousPage && nextPageSize === previousPageSize) {
      return
    }
    await loadRows()
  },
)
</script>

<template>
  <section class="personal-bank-page" v-loading="pageBusy">
    <section class="page-header-card">
      <QuestionBankPageHeader
        eyebrow="我的题库"
        title="沉淀题库"
        :description="headerDescription"
      >
        <template #meta>
          <el-tag class="header-total-tag" effect="dark" type="primary">
            当前结果 {{ total }}
          </el-tag>
        </template>
        <template #actions>
          <QuestionBankActionGroup>
            <el-button plain @click="openKnowledgeDiagnosis">去知识诊断</el-button>
            <el-button plain @click="openChallengePoints">看刷题段位</el-button>
            <el-button v-if="hasActiveReviewPlan" plain @click="clearReviewPlan">清除复习计划</el-button>
            <el-select v-model="exportFormat" class="export-format-select" placeholder="导出格式">
              <el-option label="CSV" value="csv" />
              <el-option label="PDF" value="pdf" />
            </el-select>
            <el-button type="primary" :loading="exporting" @click="handleExportCurrentResult">
              导出当前结果
            </el-button>
          </QuestionBankActionGroup>
        </template>
      </QuestionBankPageHeader>

      <div class="header-tags">
        <template v-if="activeFilterTags.length">
          <span
            v-for="tag in activeFilterTags"
            :key="`${tag.label}-${tag.value}`"
            class="header-tag"
          >
            <strong>{{ tag.label }}</strong>
            <span>{{ tag.value }}</span>
          </span>
        </template>
        <span v-else class="header-tag header-tag--muted">当前未叠加额外筛选，展示全库结果。</span>
      </div>

      <div class="bank-bridge-card">
        <strong>沉淀题库要解决的，不是“存下来”，而是“把会做的题练成稳定得分”</strong>
        <p>{{ personalBankBridgeCopy }}</p>
        <p class="bank-bridge-card__momentum">{{ personalBankMomentumCopy }}</p>
      </div>
    </section>

    <QuestionBankFilterPanel
      class="filter-card"
      kicker="精准搜索"
      title="先找题，再进入复习"
      description="关键词、归档范围和知识路径统一走同一套筛选条件，列表、汇总和导出结果保持一致，让回练和提分动作始终落在同一批题上。"
    >
      <template #caption>
        <span class="panel-caption">{{ resultSummary }}</span>
      </template>

      <div class="filter-grid">
        <el-input
          v-model="keywordSearch"
          class="search-input"
          clearable
          placeholder="输入题干关键词 / 解析 / 章节 / 原子考点"
          @clear="handleKeywordClear"
          @keyup.enter="handleKeywordSearch"
        />

        <el-select
          :model-value="archiveWindow"
          class="archive-select"
          placeholder="选择归档范围"
          @change="handleArchiveWindowChange"
        >
          <el-option
            v-for="item in archiveWindowOptions"
            :key="item.value || 'ALL'"
            :label="item.label"
            :value="item.value"
          />
        </el-select>

        <el-cascader
          v-model="selectedKnowledgePath"
          class="knowledge-cascader"
          :options="knowledgeFilterOptions"
          :props="knowledgeCascaderProps"
          :loading="knowledgeTreeLoading"
          :filter-method="filterKnowledgeNode"
          clearable
          filterable
          collapse-tags
          collapse-tags-tooltip
          placeholder="选择 L3 / L4 / L5 知识路径"
          @change="handleKnowledgePathFilterChange"
        />
      </div>

      <QuestionBankActionGroup class="filter-actions" compact>
        <el-button type="primary" @click="handleKeywordSearch">开始搜索</el-button>
        <el-button plain @click="resetPersonalBankFilters">清空筛选</el-button>
      </QuestionBankActionGroup>
    </QuestionBankFilterPanel>

    <section class="review-plan-section">
      <QuestionBankSectionHeader
        kicker="正式复习计划"
        title="复习计划"
        :description="reviewPlanSectionDescription"
      >
        <template #actions>
          <QuestionBankActionGroup compact>
            <el-button v-if="hasActiveReviewPlan" plain @click="clearReviewPlan">查看全部结果</el-button>
          </QuestionBankActionGroup>
        </template>
      </QuestionBankSectionHeader>

      <div v-if="reviewPlansErrorMessage" class="state-card state-card--error">
        <el-alert
          :title="reviewPlansErrorMessage"
          type="error"
          :closable="false"
          show-icon
        />
        <QuestionBankActionGroup compact>
          <el-button type="primary" @click="loadReviewPlans">重试计划</el-button>
        </QuestionBankActionGroup>
      </div>

      <QuestionBankEmptyState
        v-else-if="!visibleReviewPlanRows.length"
        description="当前暂无可执行复习计划。"
      />

      <template v-else>
        <section v-if="hasActiveReviewPlan" class="active-plan-card">
          <div class="active-plan-card__head">
            <div class="active-plan-card__copy">
              <div class="active-plan-card__title">
                <h5>{{ activeReviewPlan?.planName }}</h5>
                <el-tag effect="light" :type="planStatusTagType(activeReviewPlan?.status)">
                  {{ planStatusLabel(activeReviewPlan?.status) }}
                </el-tag>
              </div>
              <p>{{ activeReviewPlan?.description || '当前计划已经切到正式执行态，可直接在结果区逐题完成。' }}</p>
            </div>
            <div class="active-plan-card__meta">
              <strong>{{ activeReviewPlanProgressText }}</strong>
              <span>{{ activeReviewPlanPendingCount }} 题待完成</span>
            </div>
          </div>
          <p v-if="activeReviewPlanTimelineText" class="active-plan-card__timeline">{{ activeReviewPlanTimelineText }}</p>
          <div v-if="reviewPlanDetailErrorMessage" class="state-card state-card--error">
            <el-alert
              :title="reviewPlanDetailErrorMessage"
              type="error"
              :closable="false"
              show-icon
            />
            <QuestionBankActionGroup compact>
              <el-button type="primary" @click="loadReviewPlanDetail(activeReviewPlanId)">重试计划详情</el-button>
            </QuestionBankActionGroup>
          </div>
        </section>

        <div class="plan-grid">
        <article
          v-for="plan in visibleReviewPlanRows"
          :key="plan.planKey"
          class="plan-card"
          :class="{ active: activeReviewPlanId === plan.planId }"
        >
            <div class="plan-card__title">
              <h5>{{ plan.planName }}</h5>
              <el-tag effect="light" :type="planStatusTagType(plan.status)">{{ planStatusLabel(plan.status) }}</el-tag>
            </div>
            <p>{{ plan.description }}</p>
            <div class="plan-card__metrics">
              <span>题量 {{ Number(plan.questionCount || 0) }}</span>
              <span>已完成 {{ Number(plan.completedCount || 0) }}</span>
            </div>
            <div class="plan-card__timeline">
              <span v-if="plan.startedAt">开始于 {{ formatQuestionBankDateTime(plan.startedAt) }}</span>
              <span v-else>尚未开始</span>
            </div>
            <el-button
              type="primary"
              plain
              :disabled="!Number(plan.questionCount || 0) && activeReviewPlanId !== plan.planId"
              @click="applyReviewPlan(plan)"
            >
              {{ resolvePlanPrimaryActionLabel(plan) }}
            </el-button>
        </article>
        </div>
      </template>
    </section>

    <section class="summary-section">
      <QuestionBankSectionHeader
        kicker="汇总统计"
        title="当前筛选口径汇总"
        description="汇总卡与列表、导出复用同一套后端筛选条件，不再只基于当前页做临时统计。"
      />

      <div v-if="summaryErrorMessage" class="state-card state-card--error">
        <el-alert
          :title="summaryErrorMessage"
          type="error"
          :closable="false"
          show-icon
        />
        <QuestionBankActionGroup compact>
          <el-button type="primary" @click="loadSummary">重试汇总</el-button>
        </QuestionBankActionGroup>
      </div>

      <div v-else class="summary-grid">
        <article
          v-for="item in summaryCards"
          :key="item.label"
          class="summary-card"
          :class="{ 'summary-card--interactive': item.interactive, 'summary-card--active': item.isActive }"
          :role="item.interactive ? 'button' : undefined"
          :tabindex="item.interactive ? 0 : undefined"
          @click="handleSummaryCardClick(item)"
          @keyup.enter="handleSummaryCardClick(item)"
        >
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
          <small v-if="item.helper" class="summary-helper">{{ item.helper }}</small>
        </article>
      </div>
    </section>

    <QuestionBankResultSection
      kicker="题目列表"
      title="沉淀题库结果"
      :description="resultSectionDescription"
      :meta-text="listMetaText"
      :has-items="Boolean(normalizedRows.length) || Boolean(listErrorMessage)"
      :empty-description="questionEmptyDescription"
    >
      <template #actions>
        <QuestionBankActionGroup compact>
          <el-button
            v-if="archivedHarvestedRows.length"
            plain
            @click="restoreCurrentHarvested"
          >
            恢复当前结果中的已斩获题
          </el-button>
          <el-button v-if="hasActiveReviewPlan" plain @click="clearReviewPlan">查看全部结果</el-button>
        </QuestionBankActionGroup>
      </template>

      <template #emptyActions>
        <QuestionBankActionGroup compact>
          <el-button plain @click="resetPersonalBankFilters">清空筛选</el-button>
          <el-button plain @click="openKnowledgeDiagnosis">去知识诊断</el-button>
        </QuestionBankActionGroup>
      </template>

      <div v-if="listErrorMessage" class="state-card state-card--error">
        <el-alert
          :title="listErrorMessage"
          type="error"
          :closable="false"
          show-icon
        />
        <QuestionBankActionGroup compact>
          <el-button type="primary" @click="loadRows">重试列表</el-button>
          <el-button plain @click="resetPersonalBankFilters">清空筛选</el-button>
        </QuestionBankActionGroup>
      </div>

      <template v-else>
        <section ref="questionGridRef" class="question-grid">
          <article
            v-for="(row, index) in normalizedRows"
            :key="row.id"
            class="question-card"
            :class="{ 'question-card--highlighted': shouldHighlightArchivedRows && row._meta.isArchived }"
          >
            <div class="question-head">
              <div class="question-heading">
                <span class="question-order">
                  NO. {{ ((currentPage - 1) * currentPageSize) + index + 1 }}
                </span>
                <strong class="question-body">{{ row.stem }}</strong>
              </div>
              <el-tag effect="dark" type="primary">{{ questionTypeLabel(row.type) }}</el-tag>
            </div>

            <div class="question-path">
              <span class="question-level">{{ row._meta.level3Label || 'L3 未归类' }}</span>
              <span class="question-meta">{{ row._meta.semanticPath || '-' }}</span>
            </div>

            <p class="question-meta">
              {{ row._meta.chapterLabel || row._meta.chapter || '-' }} / {{ row._meta.pointCode || row._meta.pointLabel || '-' }}
            </p>
            <p v-if="row._meta.collectedAt !== '-'" class="question-meta">
              <strong>进入时间：</strong>{{ row._meta.collectedAt }}
            </p>
            <p v-if="row._meta.archivedAt !== '-'" class="question-meta">
              <strong>归档时间：</strong>{{ row._meta.archivedAt }}
            </p>
            <p class="question-answer"><strong>答案：</strong>{{ row.answer || '-' }}</p>
            <p class="question-analysis"><strong>解析：</strong>{{ row._meta.analysis || '-' }}</p>

            <div class="inline-tags">
              <el-tag
                v-if="row._meta.sourceLabel"
                effect="light"
                type="success"
              >
                {{ row._meta.sourceLabel }}
              </el-tag>
              <el-tag
                v-if="hasActiveReviewPlan && getActiveReviewPlanItem(row.id)"
                effect="light"
                :type="planQuestionStatusType(getActiveReviewPlanItem(row.id)?.status)"
              >
                {{ planQuestionStatusLabel(getActiveReviewPlanItem(row.id)?.status) }}
              </el-tag>
              <el-tag
                v-for="stateLabel in row._meta.stateLabels"
                :key="`${row.id}-${stateLabel}`"
                effect="light"
                type="info"
              >
                {{ stateLabel }}
              </el-tag>
              <el-tag
                v-for="reason in row._meta.reasons"
                :key="`${row.id}-${reason}`"
                effect="light"
                type="warning"
              >
                {{ reason }}
              </el-tag>
              <span v-if="!row._meta.reasons.length && !row._meta.stateLabels.length" class="question-meta">暂无错因标签</span>
            </div>

            <QuestionBankCardActions class="inline-actions">
              <el-button type="primary" @click="jumpToPractice(row)">去练这题</el-button>
              <el-button
                v-if="hasActiveReviewPlan && getActiveReviewPlanItem(row.id) && !isActiveReviewPlanQuestionCompleted(row.id)"
                plain
                @click="completeReviewPlanQuestion(row)"
              >
                记录计划完成
              </el-button>
              <el-button
                v-if="canRestoreArchivedRow(row)"
                plain
                @click="restoreHarvested(row)"
              >
                恢复到错题中心
              </el-button>
            </QuestionBankCardActions>
          </article>
        </section>

        <div v-if="total > currentPageSize" class="pagination-wrap">
          <el-pagination
            background
            layout="total, sizes, prev, pager, next"
            :current-page="currentPage"
            :page-size="currentPageSize"
            :page-sizes="PAGE_SIZE_OPTIONS"
            :total="total"
            @current-change="handlePageChange"
            @size-change="handlePageSizeChange"
          />
        </div>
      </template>
    </QuestionBankResultSection>
  </section>
</template>

<style scoped>
.personal-bank-page {
  display: grid;
  gap: var(--qb-space-4-5);
}

.page-header-card,
.filter-card,
.review-plan-section,
.summary-section {
  border: 1px solid var(--qb-border-primary-soft);
  border-radius: 24px;
  background: var(--qb-surface-strong);
  box-shadow: var(--qb-shadow-soft);
  padding: 24px;
}

.header-total-tag {
  border-radius: var(--qb-radius-pill);
  padding-inline: 14px;
  height: 34px;
}

.export-format-select {
  width: 128px;
}

.header-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 18px;
}

.bank-bridge-card {
  display: grid;
  gap: 8px;
  margin-top: 18px;
  padding: 16px 18px;
  border-radius: 20px;
  background: linear-gradient(135deg, rgba(219, 234, 254, 0.62), rgba(255, 255, 255, 0.96));
  border: 1px solid color-mix(in srgb, var(--qb-primary-student) 24%, white 76%);
}

.bank-bridge-card strong,
.bank-bridge-card p {
  margin: 0;
}

.bank-bridge-card p {
  color: var(--qb-text-copy);
  line-height: 1.72;
}

.bank-bridge-card__momentum {
  color: var(--qb-text-info-ink);
}

.header-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border-radius: var(--qb-radius-pill);
  background: var(--qb-primary-soft-bg);
  color: var(--qb-text-heading);
}

.header-tag strong {
  color: var(--qb-primary-student);
}

.header-tag--muted {
  color: var(--qb-text-copy);
}

.filter-grid {
  display: grid;
  gap: 14px;
  grid-template-columns: minmax(0, 1.4fr) minmax(180px, 0.7fr) minmax(260px, 1fr);
}

.filter-actions {
  margin-top: 18px;
}

.panel-caption,
.summary-helper,
.question-meta,
.question-answer,
.question-analysis,
.plan-card p {
  color: var(--qb-text-copy);
}

.state-card {
  display: grid;
  gap: 14px;
  padding: 18px;
  border-radius: 20px;
  background: var(--qb-surface-soft-danger);
  border: 1px solid var(--qb-border-danger-soft);
}

.question-grid {
  display: grid;
  gap: 16px;
}

.question-card {
  display: grid;
  gap: 14px;
  padding: 20px;
  border-radius: 22px;
  border: 1px solid var(--qb-border-soft);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 252, 0.95));
  box-shadow: 0 14px 30px rgba(15, 23, 42, 0.06);
}

.question-card--highlighted {
  border-color: color-mix(in srgb, var(--qb-primary-student) 40%, white 60%);
  box-shadow: 0 18px 32px rgba(37, 99, 235, 0.14);
}

.question-head,
.question-heading,
.question-path,
.inline-tags {
  display: flex;
  gap: 10px;
}

.question-head {
  align-items: flex-start;
  justify-content: space-between;
}

.question-heading {
  flex: 1;
  min-width: 0;
  flex-direction: column;
}

.question-order {
  display: inline-flex;
  align-items: center;
  width: fit-content;
  padding: 4px 10px;
  border-radius: var(--qb-radius-pill);
  background: var(--qb-primary-soft-bg);
  color: var(--qb-primary-student);
  font-size: 12px;
  font-weight: 700;
}

.question-body {
  color: var(--qb-text-heading);
  line-height: 1.7;
}

.question-path,
.inline-tags {
  flex-wrap: wrap;
}

.question-level {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: var(--qb-radius-pill);
  background: var(--qb-surface-soft-info);
  color: var(--qb-text-info-ink);
  font-size: 12px;
  font-weight: 700;
}

.inline-actions {
  margin-top: 4px;
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}

.plan-grid,
.summary-grid {
  display: grid;
  gap: 14px;
  margin-top: 18px;
}

.active-plan-card {
  display: grid;
  gap: 12px;
  margin-top: 18px;
  padding: 20px;
  border-radius: 22px;
  border: 1px solid color-mix(in srgb, var(--qb-primary-student) 36%, white 64%);
  background: linear-gradient(135deg, rgba(219, 234, 254, 0.72), rgba(255, 255, 255, 0.96));
}

.active-plan-card__head,
.active-plan-card__title,
.active-plan-card__meta,
.plan-card__title,
.plan-card__metrics,
.plan-card__timeline {
  display: flex;
  gap: 10px;
}

.active-plan-card__head {
  align-items: flex-start;
  justify-content: space-between;
}

.active-plan-card__copy,
.active-plan-card__meta {
  display: grid;
  gap: 6px;
}

.active-plan-card__copy h5,
.active-plan-card__copy p,
.plan-card h5,
.plan-card p {
  margin: 0;
}

.active-plan-card__title,
.plan-card__title {
  align-items: center;
  flex-wrap: wrap;
}

.active-plan-card__meta {
  justify-items: end;
  text-align: right;
}

.active-plan-card__meta strong {
  font-size: 22px;
  color: var(--qb-text-heading);
}

.active-plan-card__timeline,
.plan-card__timeline {
  color: var(--qb-text-copy);
  font-size: 13px;
}

.plan-grid {
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}

.plan-card,
.summary-card {
  display: grid;
  gap: 8px;
  padding: 18px;
  border-radius: 22px;
  border: 1px solid var(--qb-border-soft);
  background: var(--qb-surface-strong);
}

.plan-card h5,
.plan-card p {
  margin: 0;
}

.plan-card__metrics,
.plan-card__timeline {
  flex-wrap: wrap;
  color: var(--qb-text-copy);
  font-size: 13px;
}

.plan-card.active {
  border-color: var(--qb-primary-student);
  box-shadow: 0 14px 28px rgba(37, 99, 235, 0.16);
}

.summary-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.summary-card span {
  color: var(--qb-text-copy);
}

.summary-card strong {
  color: var(--qb-text-heading);
  font-size: 28px;
}

.summary-card--interactive {
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

.summary-card--interactive:hover,
.summary-card--active {
  transform: translateY(-2px);
  border-color: var(--qb-primary-student);
  box-shadow: 0 14px 30px rgba(37, 99, 235, 0.14);
}

@media (max-width: 1080px) {
  .filter-grid,
  .summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .page-header-card,
  .filter-card,
  .review-plan-section,
  .summary-section {
    padding: 18px;
  }

  .filter-grid,
  .summary-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .question-head {
    flex-direction: column;
  }

  .active-plan-card__head {
    flex-direction: column;
  }

  .active-plan-card__meta {
    justify-items: start;
    text-align: left;
  }

  .pagination-wrap {
    justify-content: center;
  }

  .export-format-select {
    width: 100%;
  }
}
</style>
