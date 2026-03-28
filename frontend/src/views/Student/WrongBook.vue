<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ElMessage } from '@/ui/feedback'
import { useRoute, useRouter } from 'vue-router'
import QuestionBankActionGroup from '../../components/student/QuestionBankActionGroup.vue'
import QuestionBankCardActions from '../../components/student/QuestionBankCardActions.vue'
import QuestionBankFilterPanel from '../../components/student/QuestionBankFilterPanel.vue'
import QuestionBankPageHeader from '../../components/student/QuestionBankPageHeader.vue'
import QuestionBankResultSection from '../../components/student/QuestionBankResultSection.vue'
import { useStudentQuestionBankKnowledge } from '../../composables/student-question-bank/useStudentQuestionBankKnowledge.js'
import { useStudentQuestionBankNavigation } from '../../composables/student-question-bank/useStudentQuestionBankNavigation.js'
import { useStudentQuestionBankScope } from '../../composables/student-question-bank/useStudentQuestionBankScope.js'
import { useRequest } from '../../composables/useRequest.js'
import { useSubjectContextStore } from '../../stores/subjectContextStore.js'
import {
  archiveHarvestedWrongBook,
  exportWrongBookWord,
  generatePersonalizedWrongBookPaper,
  getStudentErrorBookSummary,
  knowledgeTreeV2,
  listStudentPaperQuestions,
  listSimilarWrongBookQuestions,
  listWrongBookQuestions,
  reviewWrongBookQuestion,
} from '../../api/services/questionBank'
import { questionTypeLabel } from '../../utils/question'
import { buildWrongBookQuestionMeta } from '../../utils/studentQuestionBankMeta'
import {
  buildWrongBookAiTutorPlan,
  buildWrongBookBreadcrumbTrail,
  computeWrongBookPriorityAlertCount,
  resolveWrongBookPracticeSuggestionCount,
} from '../../utils/wrongBookDiagnostics'

const route = useRoute()
const router = useRouter()
const subjectContextStore = useSubjectContextStore()

const reviewingId = ref('')
const similarLoadingId = ref('')
const focusedRepairTagVisible = ref(true)
const focusedRepairHistoryDismissed = ref(false)
const aiDrawerVisible = ref(false)
const isAiDrawerMode = ref(typeof window !== 'undefined' ? window.innerWidth < 1200 : false)
const AI_PANEL_BREAKPOINT = 1200
let focusedRepairTagTimer = 0

const rows = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const pageSizeOptions = [20, 50, 100]
const summaryErrorMessage = ref('')
const tableErrorMessage = ref('')
const summaryData = ref({
  selectedSubjectCode: '',
  subjectRows: [],
  questionInsights: [],
  currentSubject: {},
})
const selectedQuestionIds = ref([])
const expandedRowKeys = ref([])
const similarQuestionsMap = ref({})
const harvestedPanels = ref([])
const latestAiPaper = ref({
  paperId: '',
  questionIds: [],
  previewRows: [],
  total: 0,
})

const {
  subjectCode,
  chapterName,
  chapterCode,
  pointCode,
  pointName,
  knowledgeId,
  knowledgePathNodeId,
  pathLabel,
  effectiveSubjectCode,
  buildScopeFilters,
} = useStudentQuestionBankScope({
  route,
  currentSubjectCode: computed(() => subjectContextStore.currentSubjectCode),
})
const focusQuestionId = computed(() => String(route.query.focusQuestionId || '').trim())
const focusSource = computed(() => String(route.query.focusSource || '').trim())
const autoGeneratePaper = computed(() => String(route.query.autoGeneratePaper || '').trim() === '1')
const focusedRepairHistorySessionKey = computed(() =>
  focusQuestionId.value ? `wrong-book:focused-repair-dismissed:${focusQuestionId.value}` : '',
)

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
  loadErrorMessage: '错题中心知识树加载失败',
})

const { openKnowledgeDiagnosis, jumpToWrongBookPractice } = useStudentQuestionBankNavigation({
  router,
  effectiveSubjectCode,
  buildAnalysisQuery: () => {
    const query = {}
    if (effectiveSubjectCode.value) {
      query.subjectCode = effectiveSubjectCode.value
    }
    if (chapterCode.value) {
      query.chapterCode = chapterCode.value
      query.chapterName = chapterName.value
    }
    if (pointCode.value) {
      query.pointCode = pointCode.value
      query.pointName = pointName.value
    }
    if (knowledgeId.value) {
      query.knowledgeId = knowledgeId.value
    }
    if (knowledgePathNodeId.value) {
      query.knowledgePathNodeId = knowledgePathNodeId.value
    }
    if (pathLabel.value) {
      query.pathLabel = pathLabel.value
    }
    return query
  },
})

const knowledgeCascaderProps = {
  value: 'value',
  label: 'label',
  children: 'children',
  emitPath: true,
  checkStrictly: true,
}

const pageBusy = computed(() => tableLoading.value || summaryLoading.value)
const filteredQuestionInsights = computed(() => Array.isArray(summaryData.value.questionInsights) ? summaryData.value.questionInsights : [])
const totalActiveQuestionCount = computed(() =>
  filteredQuestionInsights.value.filter((item) => String(item?.reviewStatusKey || '').trim() !== 'mastered').length,
)
const totalHarvestedQuestionCount = computed(() =>
  filteredQuestionInsights.value.filter((item) => String(item?.reviewStatusKey || '').trim() === 'mastered').length,
)
const shouldRenderResultBody = computed(() => Boolean(tableErrorMessage.value) || total.value > 0)
const shouldShowPagination = computed(() => !tableErrorMessage.value && total.value > pageSize.value)
const subjectRows = computed(() => Array.isArray(summaryData.value.subjectRows) ? summaryData.value.subjectRows : [])
const currentSubject = computed(() => {
  const selectedCode = effectiveSubjectCode.value
  if (selectedCode) {
    const matched = subjectRows.value.find((item) => String(item?.subjectCode || '').trim() === selectedCode)
    if (matched) {
      return matched
    }
  }
  return summaryData.value.currentSubject && typeof summaryData.value.currentSubject === 'object'
    ? summaryData.value.currentSubject
    : {}
})
const insightMap = computed(() =>
  Object.fromEntries(
    (Array.isArray(summaryData.value.questionInsights) ? summaryData.value.questionInsights : [])
      .map((item) => [String(item?.questionId || '').trim(), item])
      .filter(([questionId]) => questionId),
  ),
)
const currentPracticeSuggestion = computed(() => currentSubject.value?.aiSuggestions?.practiceSuggestion || {})
const currentRepairSuggestions = computed(() => {
  const rows = currentSubject.value?.aiSuggestions?.repairSuggestions
  return Array.isArray(rows) ? rows : []
})
const currentReviewWarnings = computed(() => {
  const rows = currentSubject.value?.aiSuggestions?.reviewWarnings
  return Array.isArray(rows) ? rows : []
})
const currentChapterInducerSuggestions = computed(() => {
  const rows = currentSubject.value?.chapterInducerSuggestions
  return Array.isArray(rows) ? rows : []
})
const currentSubjectName = computed(() => currentSubject.value?.subjectName || effectiveSubjectCode.value || '当前科目')
const practiceSuggestionCount = computed(() => resolveWrongBookPracticeSuggestionCount(currentPracticeSuggestion.value))
const benchmarkAlertRows = computed(() =>
  activeRows.value
    .filter((row) => row._meta.benchmarkTagType === 'danger')
    .slice(0, 3),
)
const priorityAlertCount = computed(() => computeWrongBookPriorityAlertCount({
  benchmarkAlertRows: benchmarkAlertRows.value,
  reviewWarnings: currentReviewWarnings.value,
  repairSuggestions: currentRepairSuggestions.value,
}))
const missionSummaryText = computed(() => {
  if (currentRepairSuggestions.value.length) {
    return currentRepairSuggestions.value[0]?.message || '先处理底层逻辑错误，再做短链巩固，把最容易重复丢的分先追回来。'
  }
  if (currentReviewWarnings.value.length) {
    return '先消化遗忘预警题，再回到原章节做短链复盘，避免同一类分在练习和考试里反复丢。'
  }
  if (practiceSuggestionCount.value > 0) {
    return '先做推荐修复题，再回到同章节完成一轮巩固，把错过的分一点点收回来。'
  }
  return '先用筛选缩小范围，再从当前页挑一组错题开始处理，先追回最容易重复丢掉的分。'
})
const wrongBookBridgeCopy = computed(() => {
  if (practiceSuggestionCount.value > 0) {
    return `错题中心不是仓库，而是在帮你回收会反复丢掉的分。当前有 ${practiceSuggestionCount.value} 组优先修复建议，先把这些题修顺，后面的积分增长和考场稳定性通常都会更明显。`
  }
  return '错题中心不是仓库，而是在帮你回收会反复丢掉的分。每修掉一题，后续练习和正式考试里就少一次重复失分，段位分也更容易稳步往上走。'
})
const focusedQuestionRow = computed(() =>
  normalizedRows.value.find((row) => String(row?.id || '').trim() === focusQuestionId.value) || null,
)
const focusedRepairResultLabel = computed(() => {
  if (focusSource.value !== 'RISK_REPAIR' || !focusedQuestionRow.value?._meta?.reviewStatusLabel) {
    return ''
  }
  return `修复结果：${focusedQuestionRow.value._meta.reviewStatusLabel}`
})
const visibleFocusedRepairResultLabel = computed(() =>
  focusedRepairTagVisible.value ? focusedRepairResultLabel.value : '',
)
const subtleFocusedRepairResultLabel = computed(() =>
  !focusedRepairTagVisible.value && !focusedRepairHistoryDismissed.value && focusedRepairResultLabel.value
    ? `最近修复：${focusedQuestionRow.value?._meta?.reviewStatusLabel || ''}`
    : '',
)
const focusedRepairResultType = computed(() => {
  const reviewStatusKey = String(focusedQuestionRow.value?._meta?.reviewStatusKey || '').trim()
  if (reviewStatusKey === 'mastered') {
    return 'success'
  }
  if (reviewStatusKey === 'familiar') {
    return 'warning'
  }
  return 'danger'
})

const filterSummary = computed(() => {
  if (visibleFocusedRepairResultLabel.value) {
    return `当前修复题已回到错题中心，${visibleFocusedRepairResultLabel.value}`
  }
  if (pathLabel.value) {
    return `当前按 2026 标签路径修复：${pathLabel.value}`
  }
  if (pointCode.value) {
    return `当前聚焦考点：${pointName.value || pointCode.value}`
  }
  if (chapterCode.value) {
    return `当前聚焦章节：${chapterName.value || chapterCode.value}`
  }
  if (effectiveSubjectCode.value) {
    return `当前科目：${currentSubject.value?.subjectName || effectiveSubjectCode.value}`
  }
  return '展示当前账号下全部错题中心题目，优先处理具体题目与回顾动作。'
})

const aiPaperPreviewRows = computed(() =>
  Array.isArray(latestAiPaper.value?.previewRows) ? latestAiPaper.value.previewRows : [],
)
const listMetaText = computed(() => {
  if (tableErrorMessage.value) {
    return '错题记录加载失败，请重试。'
  }
  const start = total.value > 0 ? ((currentPage.value - 1) * pageSize.value) + 1 : 0
  const end = total.value > 0 ? Math.min(currentPage.value * pageSize.value, total.value) : 0
  return `当前页待处理 ${activeRows.value.length} 题 · 第 ${start}-${end} / ${total.value} 题 · 已勾选 ${selectedQuestionIds.value.length} 题`
})
const listEmptyDescription = computed(() => {
  if (total.value > 0) {
    return '当前页没有待处理错题，请切换页码继续查看。'
  }
  if (normalizedRows.value.length) {
    return '当前错题均已斩获，已自动折叠到下方温故知新区。'
  }
  return '当前筛选条件下暂无错题记录。'
})
const activeRowIds = computed(() =>
  activeRows.value.map((row) => String(row?.id || '').trim()).filter((item) => item),
)
const selectedActiveCount = computed(() =>
  activeRowIds.value.filter((questionId) => selectedQuestionIds.value.includes(questionId)).length,
)
const allActiveRowsSelected = computed(() =>
  activeRowIds.value.length > 0 && selectedActiveCount.value === activeRowIds.value.length,
)

function syncAiDrawerMode() {
  if (typeof window === 'undefined') {
    return
  }
  isAiDrawerMode.value = window.innerWidth < AI_PANEL_BREAKPOINT
  if (!isAiDrawerMode.value) {
    aiDrawerVisible.value = false
  }
}

function resolveQuestionMeta(row) {
  return buildWrongBookQuestionMeta(row, {
    knowledgeSemanticMap: knowledgeSemanticMap.value,
    insightMap: insightMap.value,
    similarQuestionsMap: similarQuestionsMap.value,
    currentRepairSuggestions: currentRepairSuggestions.value,
    currentChapterInducerSuggestions: currentChapterInducerSuggestions.value,
    buildWrongBookBreadcrumbTrail,
    buildWrongBookAiTutorPlan,
  })
}

const normalizedRows = computed(() =>
  rows.value.map((row) => ({
    ...row,
    _meta: resolveQuestionMeta(row),
  })),
)
const activeRows = computed(() =>
  normalizedRows.value.filter((row) => row._meta.reviewStatusKey !== 'mastered'),
)
const harvestedRows = computed(() =>
  normalizedRows.value.filter((row) => row._meta.reviewStatusKey === 'mastered'),
)

async function syncFocusedQuestionIntoView() {
  if (!focusQuestionId.value) {
    return
  }
  const targetRow = normalizedRows.value.find((item) => String(item?.id || '').trim() === focusQuestionId.value)
  if (!targetRow) {
    return
  }
  if (targetRow._meta.reviewStatusKey === 'mastered') {
    harvestedPanels.value = ['harvested']
  } else {
    expandedRowKeys.value = Array.from(new Set([...expandedRowKeys.value, focusQuestionId.value]))
  }
  await nextTick()
  const focusedRow = document.querySelector('.focused-error-row')
  if (focusedRow && typeof focusedRow.scrollIntoView === 'function') {
    focusedRow.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }
}

function scheduleFocusedRepairTagFade() {
  if (focusedRepairTagTimer) {
    window.clearTimeout(focusedRepairTagTimer)
    focusedRepairTagTimer = 0
  }
  if (!focusedRepairResultLabel.value) {
    focusedRepairTagVisible.value = false
    focusedRepairHistoryDismissed.value = false
    return
  }
  focusedRepairTagVisible.value = true
  if (focusedRepairHistorySessionKey.value) {
    focusedRepairHistoryDismissed.value = window.sessionStorage.getItem(focusedRepairHistorySessionKey.value) === '1'
  } else {
    focusedRepairHistoryDismissed.value = false
  }
  focusedRepairTagTimer = window.setTimeout(() => {
    focusedRepairTagVisible.value = false
  }, 4500)
}

function dismissFocusedRepairHistory() {
  focusedRepairHistoryDismissed.value = true
  if (focusedRepairHistorySessionKey.value) {
    window.sessionStorage.setItem(focusedRepairHistorySessionKey.value, '1')
  }
}

async function openChallengePoints() {
  await router.push({
    path: '/student/analysis/points',
    query: {
      ...route.query,
      subjectCode: effectiveSubjectCode.value,
    },
  })
}

async function syncSubjectRouteIfNeeded(nextSubjectCode) {
  const normalizedSubjectCode = String(nextSubjectCode || '').trim()
  if (!normalizedSubjectCode || normalizedSubjectCode === subjectCode.value) {
    return
  }
  await router.replace({
    path: route.path,
    query: {
      ...route.query,
      subjectCode: normalizedSubjectCode,
    },
  })
}

const {
  loading: summaryLoading,
  run: loadCenterSummary,
} = useRequest(
  async () => {
    const response = await getStudentErrorBookSummary(buildScopeFilters())
    const data = response?.data && typeof response.data === 'object' ? response.data : response || {}
    summaryErrorMessage.value = ''
    summaryData.value = {
      selectedSubjectCode: String(data?.selectedSubjectCode || '').trim(),
      subjectRows: Array.isArray(data?.subjectRows) ? data.subjectRows : [],
      questionInsights: Array.isArray(data?.questionInsights) ? data.questionInsights : [],
      currentSubject: data?.currentSubject && typeof data.currentSubject === 'object' ? data.currentSubject : {},
    }
    subjectContextStore.setSubjectOptions(
      summaryData.value.subjectRows,
      String(data?.selectedSubjectCode || subjectCode.value || '').trim(),
    )
    await syncSubjectRouteIfNeeded(String(data?.selectedSubjectCode || '').trim())
    return data
  },
  {
    onError(error) {
      summaryErrorMessage.value = String(error?.response?.data?.message || error?.message || '错题中心汇总加载失败')
      summaryData.value = {
        selectedSubjectCode: '',
        subjectRows: [],
        questionInsights: [],
        currentSubject: {},
      }
      ElMessage.error(summaryErrorMessage.value)
    },
  },
)

const {
  loading: tableLoading,
  run: loadWrongBookRows,
} = useRequest(
  async () => {
    const response = await listWrongBookQuestions(buildScopeFilters({
      page: currentPage.value,
      size: pageSize.value,
    }))
    const data = response?.data && typeof response.data === 'object' ? response.data : response || {}
    rows.value = Array.isArray(data?.items) ? data.items : []
    total.value = Number(data?.total || rows.value.length || 0)
    tableErrorMessage.value = ''
    selectedQuestionIds.value = []
    await syncFocusedQuestionIntoView()
    return data
  },
  {
    onError(error) {
      rows.value = []
      total.value = 0
      tableErrorMessage.value = String(error?.response?.data?.message || error?.message || '错题记录加载失败')
      ElMessage.error(tableErrorMessage.value)
    },
  },
)

async function resetWrongBookFilters() {
  const nextQuery = {}
  if (effectiveSubjectCode.value) {
    nextQuery.subjectCode = effectiveSubjectCode.value
  }
  await router.replace({ path: route.path, query: nextQuery })
}

async function handlePageChange(page) {
  currentPage.value = Math.max(1, Number(page || 1))
  await loadWrongBookRows()
}

async function handlePageSizeChange(size) {
  pageSize.value = Number(size || 20)
  currentPage.value = 1
  await loadWrongBookRows()
}

function isQuestionSelected(questionId) {
  const normalizedQuestionId = String(questionId || '').trim()
  return selectedQuestionIds.value.includes(normalizedQuestionId)
}

function handleQuestionToggle(questionId, checked) {
  const normalizedQuestionId = String(questionId || '').trim()
  if (!normalizedQuestionId) {
    return
  }
  if (checked) {
    selectedQuestionIds.value = Array.from(new Set([...selectedQuestionIds.value, normalizedQuestionId]))
    return
  }
  selectedQuestionIds.value = selectedQuestionIds.value.filter((item) => item !== normalizedQuestionId)
}

function handleToggleSelectAllCurrentPage() {
  if (allActiveRowsSelected.value) {
    selectedQuestionIds.value = selectedQuestionIds.value.filter((item) => !activeRowIds.value.includes(item))
    return
  }
  selectedQuestionIds.value = Array.from(new Set([...selectedQuestionIds.value, ...activeRowIds.value]))
}

function clearSelectedQuestions() {
  selectedQuestionIds.value = []
}

function isQuestionDetailsOpen(questionId) {
  return expandedRowKeys.value.includes(String(questionId || '').trim())
}

function toggleQuestionDetails(questionId) {
  const normalizedQuestionId = String(questionId || '').trim()
  if (!normalizedQuestionId) {
    return
  }
  expandedRowKeys.value = expandedRowKeys.value.includes(normalizedQuestionId)
    ? expandedRowKeys.value.filter((item) => item !== normalizedQuestionId)
    : [...expandedRowKeys.value, normalizedQuestionId]
}

const { loading: exporting, run: exportWordRequest } = useRequest(
  async () => {
    const response = await exportWrongBookWord({
      subjectCode: effectiveSubjectCode.value,
      questionIds: selectedQuestionIds.value,
    })
    const data = response?.data && typeof response.data === 'object' ? response.data : response || {}
    downloadBase64File(data?.fileName, data?.mediaType, data?.contentBase64)
    ElMessage.success(`已生成 ${Number(data?.questionCount || 0)} 题的线下提分卷。`)
    return data
  },
  {
    onError(error) {
      ElMessage.error(error?.response?.data?.message || error?.message || 'Word 导出失败')
    },
  },
)

const { loading: archiving, run: archiveHarvestedRequest } = useRequest(
  async () => {
    const response = await archiveHarvestedWrongBook({
      questionIds: harvestedRows.value.map((item) => String(item.id || '').trim()).filter((item) => item),
      subjectCode: effectiveSubjectCode.value,
    })
    const data = response?.data && typeof response.data === 'object' ? response.data : response || {}
    ElMessage.success(`已归档 ${Number(data?.archivedCount || 0)} 道已斩获题。`)
    await Promise.all([loadCenterSummary(), loadWrongBookRows()])
    return data
  },
  {
    onError(error) {
      ElMessage.error(error?.response?.data?.message || error?.message || '归档失败')
    },
  },
)

const { loading: generatingAiPaper, run: generateAiExclusivePaperRequest } = useRequest(
  async ({ silent = false } = {}) => {
    const response = await generatePersonalizedWrongBookPaper(buildScopeFilters())
    const data = response?.data && typeof response.data === 'object' ? response.data : response || {}
    const paperId = String(data?.paperId || '').trim()
    const questionIds = Array.isArray(data?.questionIds)
      ? data.questionIds.map((item) => String(item || '').trim()).filter((item) => item)
      : []
    await loadAiPaperPreview(paperId, questionIds)
    if (!silent) {
      ElMessage.success(`错题修复卷已生成，共 ${questionIds.length || latestAiPaper.value.total || 0} 题。`)
    }
    return data
  },
  {
    async onError(error) {
      ElMessage.error(String(error?.response?.data?.message || error?.message || '错题修复卷生成失败'))
    },
    async onFinally() {
      await consumeAutoGeneratePaperQuery()
    },
  },
)

const { run: reviewRequest } = useRequest(
  async (questionId) => {
    await reviewWrongBookQuestion(questionId)
    ElMessage.success('已记录本次回顾。')
    await Promise.all([loadCenterSummary(), loadWrongBookRows()])
  },
  {
    onError(error) {
      ElMessage.error(error?.response?.data?.message || error?.message || '错题回顾提交失败')
    },
    onFinally() {
      reviewingId.value = ''
    },
  },
)

const { run: loadSimilarRequest } = useRequest(
  async (questionId) => {
    const response = await listSimilarWrongBookQuestions(questionId)
    const data = response?.data && typeof response.data === 'object' ? response.data : response || {}
    similarQuestionsMap.value = {
      ...similarQuestionsMap.value,
      [questionId]: Array.isArray(data?.items) ? data.items : [],
    }
    expandedRowKeys.value = Array.from(new Set([...expandedRowKeys.value, questionId]))
    return data
  },
  {
    onError(error) {
      ElMessage.error(error?.response?.data?.message || error?.message || '类似题加载失败')
    },
    onFinally() {
      similarLoadingId.value = ''
    },
  },
)

async function handleReview(row) {
  const questionId = String(row?.id || '').trim()
  if (!questionId || reviewingId.value) {
    return
  }
  reviewingId.value = questionId
  await reviewRequest(questionId)
}

async function handleLoadSimilar(row) {
  const questionId = String(row?.id || '').trim()
  if (!questionId || similarLoadingId.value) {
    return
  }
  similarLoadingId.value = questionId
  await loadSimilarRequest(questionId)
}

async function handlePracticeWeakest() {
  const questionIds = Array.isArray(currentPracticeSuggestion.value?.questionIds)
    ? currentPracticeSuggestion.value.questionIds.map((item) => String(item || '').trim()).filter((item) => item)
    : []
  if (!questionIds.length) {
    ElMessage.warning('当前科目暂无可进入的消灭错题题单。')
    return
  }
  await jumpToWrongBookPractice({
    subjectCode: effectiveSubjectCode.value,
    knowledgeId: knowledgeId.value,
    knowledgePathNodeId: knowledgePathNodeId.value,
    chapterCode: chapterCode.value,
    chapterName: chapterName.value,
    pointCode: pointCode.value,
    pointName: pointName.value,
    pathLabel: pathLabel.value,
    questionIds,
    adaptiveDimension: effectiveSubjectCode.value || 'ERROR_BOOK',
    adaptiveMastery: Math.round(Number(currentPracticeSuggestion.value?.lowestMastery || 0) * 100),
  })
}

async function handlePracticeRisk(row) {
  const questionId = String(row?.id || '').trim()
  if (!questionId) {
    ElMessage.warning('当前高风险题暂不可进入练习。')
    return
  }
  await jumpToWrongBookPractice({
    subjectCode: effectiveSubjectCode.value,
    knowledgeId: knowledgeId.value,
    knowledgePathNodeId: knowledgePathNodeId.value,
    chapterCode: chapterCode.value,
    chapterName: chapterName.value,
    pointCode: pointCode.value,
    pointName: pointName.value,
    pathLabel: pathLabel.value,
    row,
    questionIds: [questionId],
    adaptiveDimension: row?._meta?.pointCode || row?._meta?.pointName || effectiveSubjectCode.value || 'ERROR_BOOK',
    adaptiveMastery: Number(row?._meta?.masteryScore || 0),
    focusMode: 'RISK_REPAIR',
    focusQuestionId: questionId,
  })
}

async function handlePracticeSimilar(row) {
  const questionId = String(row?.id || '').trim()
  const similarRows = Array.isArray(similarQuestionsMap.value[questionId]) ? similarQuestionsMap.value[questionId] : []
  const questionIds = similarRows.map((item) => String(item?.id || '').trim()).filter((item) => item)
  if (!questionIds.length) {
    ElMessage.warning('当前暂无可练的类似题。')
    return
  }
  await jumpToWrongBookPractice({
    subjectCode: effectiveSubjectCode.value,
    knowledgeId: knowledgeId.value,
    knowledgePathNodeId: knowledgePathNodeId.value,
    chapterCode: chapterCode.value,
    chapterName: chapterName.value,
    pointCode: pointCode.value,
    pointName: pointName.value,
    pathLabel: pathLabel.value,
    row,
    questionIds,
    adaptiveDimension: row?._meta?.pointCode || row?._meta?.pointName || effectiveSubjectCode.value || 'ERROR_BOOK',
    adaptiveMastery: Number(row?._meta?.masteryScore || 0),
  })
}

function downloadBase64File(fileName, mediaType, contentBase64) {
  const binary = window.atob(String(contentBase64 || ''))
  const bytes = new Uint8Array(binary.length)
  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index)
  }
  const blob = new Blob([bytes], { type: mediaType || 'application/octet-stream' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = fileName || 'wrong-book.docx'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

async function handleExportWord() {
  if (!selectedQuestionIds.value.length) {
    ElMessage.warning('请先勾选要打印的错题。')
    return
  }
  await exportWordRequest()
}

async function handleArchiveHarvested() {
  if (!harvestedRows.value.length) {
    ElMessage.warning('当前没有可归档的已斩获题目。')
    return
  }
  await archiveHarvestedRequest()
}

async function loadAiPaperPreview(paperId, fallbackQuestionIds = []) {
  if (!String(paperId || '').trim()) {
    latestAiPaper.value = {
      paperId: '',
      questionIds: [],
      previewRows: [],
      total: 0,
    }
    return
  }
  const response = await listStudentPaperQuestions(paperId, { page: 1, size: 6 })
  const data = response?.data && typeof response.data === 'object' ? response.data : response || {}
  const previewRows = Array.isArray(data?.items) ? data.items : []
  latestAiPaper.value = {
    paperId: String(paperId || '').trim(),
    questionIds: Array.isArray(fallbackQuestionIds)
      ? fallbackQuestionIds.map((item) => String(item || '').trim()).filter((item) => item)
      : [],
    previewRows,
    total: Number(data?.total || previewRows.length || 0),
  }
}

async function consumeAutoGeneratePaperQuery() {
  if (!autoGeneratePaper.value) {
    return
  }
  const nextQuery = { ...route.query }
  delete nextQuery.autoGeneratePaper
  await router.replace({
    path: route.path,
    query: nextQuery,
  })
}

async function generateAiExclusivePaper({ silent = false } = {}) {
  if (generatingAiPaper.value) {
    return
  }
  await generateAiExclusivePaperRequest({ silent })
}

onMounted(async () => {
  syncAiDrawerMode()
  window.addEventListener('resize', syncAiDrawerMode)
  await loadCenterSummary()
  await Promise.all([loadKnowledgeTree(), loadWrongBookRows()])
  if (autoGeneratePaper.value) {
    await generateAiExclusivePaper({ silent: true })
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', syncAiDrawerMode)
  if (focusedRepairTagTimer) {
    window.clearTimeout(focusedRepairTagTimer)
  }
})

watch(
  () => effectiveSubjectCode.value,
  async (nextSubjectCode, previousSubjectCode) => {
    if (nextSubjectCode === previousSubjectCode) {
      return
    }
    selectedKnowledgePath.value = []
    selectedQuestionIds.value = []
    similarQuestionsMap.value = {}
    expandedRowKeys.value = []
    currentPage.value = 1
    await Promise.all([loadCenterSummary(), loadKnowledgeTree(), loadWrongBookRows()])
  },
)

watch(
  () => focusedRepairResultLabel.value,
  () => {
    scheduleFocusedRepairTagFade()
  },
  { immediate: true },
)

watch(
  () => focusQuestionId.value,
  () => {
    if (!focusedRepairHistorySessionKey.value) {
      focusedRepairHistoryDismissed.value = false
      return
    }
    focusedRepairHistoryDismissed.value = window.sessionStorage.getItem(focusedRepairHistorySessionKey.value) === '1'
  },
  { immediate: true },
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
    currentPage.value = 1
    await Promise.all([loadCenterSummary(), loadWrongBookRows()])
  },
)

watch(
  () => autoGeneratePaper.value,
  async (enabled) => {
    if (!enabled) {
      return
    }
    await generateAiExclusivePaper({ silent: true })
  },
)
</script>

<template>
  <section class="error-book-center" v-loading="pageBusy">
    <QuestionBankPageHeader
      eyebrow="我的题库"
      title="错题中心"
      :description="filterSummary"
    >
      <template #actions>
        <QuestionBankActionGroup>
          <el-button
            plain
            :loading="exporting"
            :disabled="!selectedQuestionIds.length"
            @click="handleExportWord"
          >
            打印错题集
          </el-button>
        </QuestionBankActionGroup>
      </template>
    </QuestionBankPageHeader>

    <el-alert
      v-if="summaryErrorMessage"
      class="page-alert"
      type="error"
      :title="summaryErrorMessage"
      show-icon
      :closable="false"
    />

    <section class="mission-scope-grid">
      <div class="mission-main-column">
        <article class="mission-panel">
          <div class="mission-panel-copy">
            <span class="mission-panel-tag">AI 修复中心</span>
            <div class="mission-panel-kicker-row">
              <span class="mission-panel-subject">{{ currentSubjectName }}</span>
              <span class="mission-panel-filter">{{ filterSummary }}</span>
            </div>
            <h4>{{ currentSubjectName }}</h4>
            <p>{{ missionSummaryText }}</p>
            <p class="mission-panel-bridge">{{ wrongBookBridgeCopy }}</p>
          </div>
          <div class="mission-stat-grid">
            <article class="mission-stat-card">
              <span>待修复</span>
              <strong>{{ totalActiveQuestionCount }}</strong>
              <small>当前筛选范围内待处理题数</small>
            </article>
            <article class="mission-stat-card">
              <span>推荐修复</span>
              <strong>{{ practiceSuggestionCount }}</strong>
              <small>{{ practiceSuggestionCount ? '优先处理掌握度最低的题单' : '当前暂无直接推荐题单' }}</small>
            </article>
            <article class="mission-stat-card">
              <span>重点提醒</span>
              <strong>{{ priorityAlertCount }}</strong>
              <small>同组差距、遗忘预警与修复建议合计</small>
            </article>
          </div>
          <QuestionBankActionGroup class="mission-panel-actions">
            <el-button type="primary" :disabled="!practiceSuggestionCount" @click="handlePracticeWeakest">
              开始修复
            </el-button>
            <el-button plain @click="openChallengePoints">
              看刷题段位
            </el-button>
            <el-button plain :loading="generatingAiPaper" @click="generateAiExclusivePaper()">
              生成错题修复卷
            </el-button>
          </QuestionBankActionGroup>
        </article>

        <section class="mission-support-grid">
          <article class="ai-card mission-support-card">
            <div class="ai-card-head">
              <strong>完整分析</strong>
              <span>{{ currentReviewWarnings.length }} 条回顾提醒</span>
            </div>
            <p class="ai-copy">
              章节结构、热点分布和完整薄弱点统一放到知识诊断页，这里聚焦具体题目处理。
            </p>
            <el-button plain @click="openKnowledgeDiagnosis">
              去知识诊断看完整分析
            </el-button>
          </article>

          <article class="ai-card mission-support-card">
            <div class="ai-card-head">
              <strong>遗忘预警</strong>
              <span>{{ currentReviewWarnings.length }} 条</span>
            </div>
            <el-empty v-if="!currentReviewWarnings.length" :image-size="72" description="当前没有超过 72 小时未回顾的高频错题。" />
            <div v-else class="warning-list">
              <div v-for="item in currentReviewWarnings" :key="item.questionId" class="warning-item">
                <strong>{{ item.pointName }}</strong>
                <p>{{ item.overdueHours }} 小时未回顾，累计错 {{ item.wrongCount }} 次。</p>
              </div>
            </div>
          </article>
        </section>
      </div>

      <aside class="scope-column">
        <QuestionBankFilterPanel
          class="filter-card scope-card scope-card--tool"
          kicker="精准筛选"
          title="2026 五级标签筛选"
          :description="`从 L3 到 L5 精准定位错题归因，当前共 ${total} 题。`"
        >
          <el-cascader
            v-model="selectedKnowledgePath"
            class="knowledge-cascader"
            :options="knowledgeFilterOptions"
            :props="knowledgeCascaderProps"
            :loading="knowledgeTreeLoading"
            clearable
            filterable
            collapse-tags
            collapse-tags-tooltip
            placeholder="选择 L3 / L4 / L5 知识路径"
            @change="handleKnowledgePathChange"
          />
        </QuestionBankFilterPanel>

        <article class="ai-card support-card scope-card scope-card--result scope-combined-card">
          <section class="scope-combined-section">
            <div class="ai-card-head">
              <strong>错题修复卷</strong>
              <span>{{ latestAiPaper.paperId ? `${latestAiPaper.total || aiPaperPreviewRows.length} 题` : '待生成' }}</span>
            </div>
            <p class="ai-copy">
              基于当前错题和薄弱知识点，自动生成一套围绕修复闭环的巩固卷。
            </p>
            <p v-if="latestAiPaper.paperId" class="paper-preview-meta">
              试卷编号：{{ latestAiPaper.paperId }}
            </p>
            <el-empty
              v-if="!aiPaperPreviewRows.length && !generatingAiPaper"
              :image-size="92"
              description="生成后会在这里预览前 6 道题。"
            />
            <div v-else class="paper-preview-list">
              <article v-for="item in aiPaperPreviewRows" :key="item.id" class="paper-preview-item">
                <strong>{{ questionTypeLabel(item.type) }}</strong>
                <p>{{ item.stem || '-' }}</p>
              </article>
            </div>
          </section>

          <section class="scope-combined-section">
            <div class="ai-card-head">
              <strong>修复提示</strong>
              <span>{{ currentRepairSuggestions.length }} 条</span>
            </div>
            <el-empty v-if="!currentRepairSuggestions.length" :image-size="72" description="当前没有触发底层逻辑错误规则。" />
            <div v-else class="ai-list">
              <div v-for="item in currentRepairSuggestions.slice(0, 2)" :key="item.knowledgeId || item.pointCode" class="ai-list-item">
                <strong>{{ item.pointName }}</strong>
                <p>{{ item.message }}</p>
              </div>
            </div>
          </section>
        </article>
      </aside>
    </section>

    <QuestionBankResultSection
      class="stream-head"
      kicker="题目列表"
      title="详细错题库"
      description="每道题都带完整路径、风险信号和 AI 助教建议。"
      :meta-text="listMetaText"
      :has-items="shouldRenderResultBody"
      :empty-description="listEmptyDescription"
    >
      <template #emptyActions>
        <QuestionBankActionGroup compact>
          <el-button plain @click="resetWrongBookFilters">清空筛选</el-button>
          <el-button type="primary" plain :disabled="!practiceSuggestionCount" @click="handlePracticeWeakest">去做一轮修复</el-button>
        </QuestionBankActionGroup>
      </template>
      <div v-if="tableErrorMessage" class="result-error-card">
        <el-result
          icon="error"
          title="错题记录加载失败"
          :sub-title="tableErrorMessage"
        >
          <template #extra>
            <QuestionBankActionGroup compact>
              <el-button plain @click="resetWrongBookFilters">清空筛选</el-button>
              <el-button type="primary" @click="loadWrongBookRows">重新加载</el-button>
            </QuestionBankActionGroup>
          </template>
        </el-result>
      </div>
      <section v-else class="diagnosis-card-grid">
          <div v-if="activeRows.length" class="batch-toolbar">
            <div class="batch-toolbar-copy">
              <strong>批量处理</strong>
              <span>当前页 {{ activeRows.length }} 题，已选 {{ selectedActiveCount }} 题。</span>
            </div>
            <QuestionBankCardActions class="batch-toolbar-actions" :stacked-on-mobile="false">
              <el-button plain @click="handleToggleSelectAllCurrentPage">
                {{ allActiveRowsSelected ? '取消全选当前页' : '全选当前页' }}
              </el-button>
              <el-button plain :disabled="!selectedQuestionIds.length" @click="clearSelectedQuestions">
                清空勾选
              </el-button>
              <el-button
                type="primary"
                plain
                :disabled="!selectedQuestionIds.length"
                :loading="exporting"
                @click="handleExportWord"
              >
                批量打印已选题
              </el-button>
            </QuestionBankCardActions>
          </div>
          <div v-if="!activeRows.length" class="result-empty-card">
            <el-empty description="当前页没有待处理错题，请切换页码继续查看。" />
          </div>
          <article
            v-for="row in activeRows"
            :key="row.id"
            class="diagnosis-card"
            :class="{ 'focused-error-row': row.id === focusQuestionId }"
          >
            <header class="diagnosis-card-head">
              <div class="card-head-main">
                <el-checkbox
                  :model-value="isQuestionSelected(row.id)"
                  @change="(checked) => handleQuestionToggle(row.id, checked)"
                />
              </div>

              <div class="diagnosis-signals">
                <el-tag effect="plain">{{ questionTypeLabel(row.type) }}</el-tag>
                <el-tag
                  :type="row._meta.reviewStatusKey === 'familiar' ? 'warning' : 'danger'"
                  effect="light"
                >
                  {{ row._meta.reviewStatusLabel }}
                </el-tag>
                <el-tag
                  :type="row._meta.masteryScore < 40 ? 'danger' : row._meta.masteryScore < 70 ? 'warning' : 'success'"
                  effect="light"
                >
                  掌握度 {{ row._meta.masteryScore }}%
                </el-tag>
                <el-tag v-if="row._meta.isOverdue72h" type="warning" effect="plain">
                  72h 未回顾
                </el-tag>
                <el-tag
                  v-if="row.id === focusQuestionId && visibleFocusedRepairResultLabel"
                  :type="focusedRepairResultType"
                  effect="dark"
                >
                  {{ visibleFocusedRepairResultLabel }}
                </el-tag>
                <el-tag
                  v-if="row.id === focusQuestionId && subtleFocusedRepairResultLabel"
                  type="info"
                  effect="plain"
                  closable
                  @close="dismissFocusedRepairHistory"
                >
                  {{ subtleFocusedRepairResultLabel }}
                </el-tag>
                <el-tag v-if="row.id === focusQuestionId" type="warning" effect="dark">
                  当前修复题
                </el-tag>
              </div>
            </header>

            <div class="diagnosis-card-body">
              <section class="diagnosis-main">
                <div class="question-meta-strip">
                  <span class="chapter-pill">{{ row._meta.chapterLabel }}</span>
                  <button
                    v-if="row._meta.showBenchmarkRiskBadge"
                    type="button"
                    class="risk-crest"
                    @click="handlePracticeRisk(row)"
                  >
                    {{ row._meta.benchmarkRiskBadgeText }}
                  </button>
                </div>
                <p class="question-stem question-body">{{ row.stem }}</p>
                <p v-if="row._meta.semanticTagLine" class="question-path-copy">{{ row._meta.semanticTagLine }}</p>

                <div class="diagnostic-metrics">
                  <article class="diag-metric">
                    <span>诊断定位</span>
                    <strong>{{ row._meta.pointCode || row._meta.pointName }}</strong>
                    <small>{{ row._meta.benchmarkStatusText }}</small>
                  </article>
                  <article class="diag-metric">
                    <span>错题次数</span>
                    <strong>{{ row._meta.wrongCount }}</strong>
                    <small>最近交卷 {{ row._meta.submittedAt }}</small>
                  </article>
                  <article class="diag-metric">
                    <span>对标均值</span>
                    <strong>{{ Math.round(row._meta.jointGroupAverageAccuracy * 100) }}%</strong>
                    <small>错后再正确率 {{ Math.round(row._meta.reviewAccuracyRate * 100) }}%</small>
                  </article>
                </div>
              </section>

              <aside class="card-ai-panel card-ai-panel--secondary">
                <div class="card-ai-head">
                  <strong>AI 助教建议</strong>
                  <span class="card-ai-priority">{{ row._meta.aiTutorPlan.priorityLabel }}</span>
                </div>
                <p class="card-ai-title">{{ row._meta.aiTutorPlan.diagnosisTitle }}</p>
                <p class="card-ai-copy">{{ row._meta.aiTutorPlan.recommendation }}</p>
                <div class="card-ai-meta">
                  <p><strong>L4 建议：</strong>{{ row._meta.aiTutorPlan.chapterAction }}</p>
                  <p><strong>优先动作：</strong>{{ row._meta.aiTutorPlan.actionLabel }}</p>
                </div>
              </aside>
            </div>

            <footer class="diagnosis-card-footer">
              <QuestionBankCardActions class="row-actions">
                <el-button
                  type="primary"
                  plain
                  :loading="reviewingId === row.id"
                  @click="handleReview(row)"
                >
                  完成回顾
                </el-button>
                <el-button
                  plain
                  :loading="similarLoadingId === row.id"
                  @click="handleLoadSimilar(row)"
                >
                  举一反三
                </el-button>
                <el-button plain @click="toggleQuestionDetails(row.id)">
                  {{ isQuestionDetailsOpen(row.id) ? '收起详情' : '展开详情' }}
                </el-button>
              </QuestionBankCardActions>
            </footer>

            <transition name="detail-fade">
              <section v-if="isQuestionDetailsOpen(row.id)" class="detail-panel">
                <div class="detail-copy">
                  <p><strong>知识路径：</strong>{{ row._meta.semanticPath || row._meta.chapterPointPath }}</p>
                  <p><strong>题型：</strong>{{ questionTypeLabel(row.type) }}</p>
                  <p><strong>我的最近答案：</strong>{{ row._meta.lastAnswer || '-' }}</p>
                  <p><strong>累计作答：</strong>{{ row._meta.submitCount }} 次，答对 {{ row._meta.correctCount }} 次</p>
                  <p><strong>最近作答耗时：</strong>{{ row._meta.answerDurationSec ? `${row._meta.answerDurationSec} 秒` : '-' }}</p>
                  <p><strong>答案：</strong>{{ row.answer || '-' }}</p>
                  <p><strong>解析：</strong>{{ row._meta.analysis }}</p>
                  <p><strong>错误诱因：</strong>{{ row._meta.errorInducerLabel }}</p>
                  <p><strong>最近错因：</strong>{{ row._meta.lastReasonLabel || '-' }}</p>
                  <p><strong>回顾记录：</strong>{{ row._meta.reviewCount }} 次</p>
                  <p><strong>错后再练：</strong>{{ row._meta.postWrongCorrectCount }} / {{ row._meta.postWrongAttemptCount }}</p>
                  <p><strong>最近回顾：</strong>{{ row._meta.reviewedAt }}</p>
                </div>

                <div class="detail-similar">
                  <div class="detail-head">
                    <strong>类似题推荐</strong>
                    <el-button
                      size="small"
                      plain
                      :disabled="!row._meta.similarQuestions.length"
                      @click="handlePracticeSimilar(row)"
                    >
                      {{ `去练这 ${row._meta.similarQuestions.length} 题` }}
                    </el-button>
                  </div>
                  <el-empty
                    v-if="!row._meta.similarQuestions.length"
                    description="点击“举一反三”后展示同 point_code 的 3 道新题。"
                  />
                  <div v-else class="similar-list">
                    <article
                      v-for="item in row._meta.similarQuestions"
                      :key="item.id"
                      class="similar-card"
                    >
                      <strong>{{ questionTypeLabel(item.type) }}</strong>
                      <p>{{ item.stem }}</p>
                    </article>
                  </div>
                </div>
              </section>
            </transition>
          </article>
          <div v-if="shouldShowPagination" class="pagination-bar">
            <el-pagination
              background
              layout="total, sizes, prev, pager, next"
              :current-page="currentPage"
              :page-size="pageSize"
              :page-sizes="pageSizeOptions"
              :total="total"
              @current-change="handlePageChange"
              @size-change="handlePageSizeChange"
            />
          </div>
      </section>
    </QuestionBankResultSection>

    <el-collapse v-if="harvestedRows.length" v-model="harvestedPanels" class="harvested-collapse">
      <el-collapse-item :title="`温故知新：已斩获 ${harvestedRows.length} 题（默认折叠）`" name="harvested">
        <QuestionBankCardActions class="harvested-actions" :stacked-on-mobile="false">
          <el-button plain size="small" :loading="archiving" @click="handleArchiveHarvested">
            一键归档已斩获
          </el-button>
        </QuestionBankCardActions>
        <div class="harvested-list">
          <article
            v-for="row in harvestedRows"
            :key="row.id"
            class="harvested-card"
            :class="{ 'focused-error-row': row.id === focusQuestionId }"
          >
            <div class="harvested-copy">
              <strong>{{ row.stem }}</strong>
              <small>{{ row._meta.chapterPointPath }}</small>
            </div>
            <div class="status-tags">
              <el-tag type="success" effect="light">{{ row._meta.reviewStatusLabel }}</el-tag>
              <el-tag :type="row._meta.benchmarkTagType" effect="light">{{ row._meta.benchmarkStatusText }}</el-tag>
            </div>
          </article>
        </div>
      </el-collapse-item>
    </el-collapse>

    <section v-if="benchmarkAlertRows.length" class="insight-grid insight-grid--single">
      <article class="ai-card insight-card alert-card">
        <div class="ai-card-head">
          <strong>同组差距预警</strong>
          <span>{{ benchmarkAlertRows.length }} 题</span>
        </div>
        <div class="warning-list">
          <div v-for="item in benchmarkAlertRows" :key="item.id" class="warning-item">
            <div class="warning-item-head">
              <strong>{{ item._meta.pointName }}</strong>
              <button
                v-if="item._meta.showBenchmarkRiskBadge"
                type="button"
                class="risk-crest"
                @click="handlePracticeRisk(item)"
              >
                {{ item._meta.benchmarkRiskBadgeText }}
              </button>
            </div>
            <p>个人 {{ item._meta.masteryScore }}%，同组均值 {{ Math.round(item._meta.jointGroupAverageAccuracy * 100) }}%。{{ item._meta.benchmarkStatusText }}</p>
          </div>
        </div>
      </article>
    </section>
  </section>
</template>

<style scoped>
.error-book-center {
  display: grid;
  gap: var(--qb-space-4);
  --wb-surface-radius: 24px;
  --wb-surface-border: rgba(223, 229, 239, 0.92);
  --wb-surface-shadow: 0 18px 40px rgba(15, 23, 42, 0.06);
  --wb-surface-shadow-hover: 0 24px 52px rgba(15, 23, 42, 0.1);
  --wb-muted-surface: linear-gradient(145deg, rgba(255, 255, 255, 0.99), rgba(249, 250, 252, 0.97));
  --wb-accent-border: color-mix(in srgb, var(--qb-primary-student) 12%, white 88%);
  --wb-soft-blue: linear-gradient(145deg, rgba(255, 255, 255, 0.99), rgba(242, 247, 255, 0.95));
  --wb-soft-rose: linear-gradient(145deg, rgba(255, 255, 255, 0.99), rgba(255, 245, 245, 0.96));
}

.page-alert {
  border-radius: 20px;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--qb-space-4);
  padding: var(--qb-space-5) var(--qb-space-5-5);
  border-radius: 28px;
  background:
    radial-gradient(circle at top left, rgba(59, 130, 246, 0.16), transparent 42%),
    linear-gradient(135deg, rgba(239, 246, 255, 0.98), rgba(255, 255, 255, 0.96));
  border: 1px solid color-mix(in srgb, var(--qb-primary-student) 14%, white);
  box-shadow: 0 24px 56px rgba(15, 23, 42, 0.08);
}

.eyebrow {
  margin: 0 0 8px;
  font-size: 12px;
  letter-spacing: 0.14em;
  color: var(--qb-primary-student);
}

.page-header h3,
.page-copy,
.filter-copy h4,
.filter-copy p,
.panel-head h4,
.panel-head p,
.stream-head h4,
.stream-head p,
.board-copy,
.card-ai-copy,
.card-ai-title {
  margin: 0;
}

.page-header h3 {
  font-size: 28px;
  line-height: 1.1;
}

.page-copy {
  margin-top: 8px;
  color: var(--qb-text-meta);
}

.header-actions,
.row-actions,
.diagnosis-signals,
.stream-stats,
.coverage-foot,
.status-tags {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.panel-head p,
.filter-copy p,
.stream-head p {
  margin-top: 6px;
  color: var(--qb-text-subtle-8);
}

.sidebar-title-row,
.board-head,
.diagnosis-card-head,
.diagnosis-card-footer,
.detail-head,
.ai-card-head,
.warning-item-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.main-panel {
  display: grid;
  gap: var(--qb-space-3-5);
}

.mission-panel,
.filter-card,
.stream-head,
.diagnosis-card,
.harvested-card,
.ai-card {
  border-radius: var(--wb-surface-radius);
  border: 1px solid var(--wb-surface-border);
  background: var(--wb-muted-surface);
  box-shadow: var(--wb-surface-shadow);
}

.filter-card,
.stream-head,
.diagnosis-card,
.harvested-card {
  border-radius: var(--wb-surface-radius);
}

.filter-card {
  display: grid;
  gap: var(--qb-space-3);
  padding: var(--qb-space-4);
  background: var(--wb-soft-blue);
  border-color: var(--wb-accent-border);
}

.knowledge-cascader {
  width: 100%;
}

.mission-scope-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.28fr) minmax(320px, 0.9fr);
  gap: var(--qb-space-3);
  align-items: start;
}

.mission-main-column {
  display: grid;
  gap: var(--qb-space-3);
}

.mission-support-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--qb-space-3);
}

.mission-support-card {
  min-height: 100%;
}

.mission-panel {
  display: grid;
  gap: var(--qb-space-3);
  padding: var(--qb-space-4);
  color: var(--qb-text-heading);
  background:
    radial-gradient(circle at 86% 16%, rgba(147, 197, 253, 0.18), transparent 24%),
    linear-gradient(132deg, rgba(239, 246, 255, 0.96), rgba(255, 255, 255, 0.98));
  border-color: var(--wb-accent-border);
  box-shadow: 0 16px 34px rgba(37, 99, 235, 0.1);
  position: relative;
  overflow: hidden;
}

.mission-panel-copy {
  display: grid;
  gap: var(--qb-space-3);
}

.mission-panel-kicker-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.mission-panel-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: fit-content;
  min-height: 30px;
  padding: 0 var(--qb-space-3);
  border-radius: var(--qb-radius-pill);
  background: var(--qb-primary-soft-bg);
  border: 1px solid var(--qb-border-primary-soft);
  color: var(--qb-text-info-ink);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.mission-panel-subject,
.mission-panel-filter {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 var(--qb-space-3);
  border-radius: var(--qb-radius-pill);
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid rgba(191, 219, 254, 0.62);
  color: var(--qb-text-copy);
  font-size: 12px;
}

.mission-panel-filter {
  max-width: min(100%, 44ch);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.mission-panel h4,
.mission-panel p {
  margin: 0;
}

.mission-panel h4 {
  font-size: 26px;
  line-height: 1.12;
  color: var(--qb-text-heading);
}

.mission-panel p {
  color: var(--qb-text-copy);
  line-height: 1.62;
  max-width: 56ch;
}

.mission-panel-bridge {
  color: var(--qb-text-heading);
}

.mission-panel::after {
  content: '';
  position: absolute;
  right: -36px;
  bottom: -40px;
  width: 180px;
  height: 180px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(147, 197, 253, 0.22), transparent 70%);
  pointer-events: none;
}

.mission-panel-actions,
.scope-column {
  display: grid;
  gap: var(--qb-space-3);
}

.mission-panel-actions {
  display: flex;
  gap: var(--qb-space-3);
  flex-wrap: wrap;
}

.mission-stat-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--qb-space-3);
}

.mission-stat-card {
  display: grid;
  gap: 6px;
  padding: 16px;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(191, 219, 254, 0.6);
}

.mission-stat-card span,
.mission-stat-card p,
.mission-stat-card small {
  margin: 0;
  color: var(--qb-text-copy);
}

.mission-stat-card strong {
  font-size: 24px;
  line-height: 1.15;
  color: var(--qb-text-heading);
}

.mission-stat-card small {
  line-height: 1.5;
}

.scope-column,
.insight-grid {
  display: grid;
  gap: var(--qb-space-3);
}

.scope-column {
  align-content: start;
}

.scope-card--tool {
  box-shadow: 0 16px 30px rgba(59, 130, 246, 0.08);
}

.scope-card--result {
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.99), rgba(244, 248, 255, 0.96));
}

.scope-combined-card {
  gap: var(--qb-space-2);
}

.scope-combined-section {
  display: grid;
  gap: var(--qb-space-3);
}

.scope-combined-section + .scope-combined-section {
  padding-top: var(--qb-space-2);
  border-top: 1px dashed rgba(148, 163, 184, 0.24);
}

.scope-card--hint {
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.99), rgba(249, 250, 252, 0.96));
  border-color: rgba(226, 232, 240, 0.88);
}

@media (min-width: 961px) {
  .scope-column {
    position: sticky;
    top: 24px;
  }
}

.insight-grid {
  grid-template-columns: 1fr;
}

.insight-grid--single {
  grid-template-columns: 1fr;
}

.insight-card {
  min-height: 100%;
}

.insight-card--entry {
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.99), rgba(241, 247, 255, 0.96));
}

.stream-head h4 {
  margin: 0;
  font-size: 18px;
}

.card-ai-priority,
.chapter-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 28px;
  padding: 0 var(--qb-space-3);
  border-radius: var(--qb-radius-pill);
  background: var(--qb-surface-soft-success);
  color: var(--qb-success);
  font-size: 12px;
  font-weight: 700;
}

.stream-stats span,
.diag-metric small,
.harvested-copy small {
  color: var(--qb-text-subtle-8);
}

.hotspot-list,
.hotspot-item,
.diagnosis-card-grid,
.diagnosis-card,
.diagnosis-main,
.diagnostic-metrics,
.diag-metric,
.card-ai-panel,
.card-ai-meta,
.detail-panel,
.detail-copy,
.detail-similar,
.similar-list,
.paper-preview-list,
.paper-preview-item,
.ai-list,
.warning-list,
.harvested-list {
  display: grid;
  gap: var(--qb-space-5);
}

.hotspot-item {
  grid-template-columns: auto 1fr;
  align-items: start;
  gap: 12px;
}

.hotspot-rank {
  min-width: 34px;
  height: 34px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--qb-radius-sm);
  background: color-mix(in srgb, var(--qb-warning) 14%, white 86%);
  color: var(--qb-text-warning-ink);
  font-weight: 700;
}

.hotspot-copy {
  display: grid;
  gap: 4px;
}

.stream-head {
  padding: var(--qb-space-4) var(--qb-space-4-5);
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.99), rgba(245, 248, 255, 0.97));
}

.stream-stats span {
  padding: var(--qb-space-2) var(--qb-space-3);
  border-radius: var(--qb-radius-pill);
  background: rgba(241, 245, 249, 0.9);
  font-size: 13px;
}

.diagnosis-card-grid {
  gap: var(--qb-space-5);
}

.result-error-card {
  padding: var(--qb-space-3);
  border: 1px dashed color-mix(in srgb, var(--qb-danger) 24%, white 76%);
  border-radius: 24px;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.98), rgba(254, 242, 242, 0.98));
}

.result-empty-card {
  padding: var(--qb-space-2);
  border-radius: 24px;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 252, 0.98));
}

.batch-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--qb-space-3);
  padding: var(--qb-space-3-5);
  border-radius: 20px;
  border: 1px solid rgba(217, 228, 243, 0.92);
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.99), rgba(240, 246, 255, 0.95));
}

.batch-toolbar-copy {
  display: grid;
  gap: 4px;
}

.batch-toolbar-copy strong,
.batch-toolbar-copy span,
.question-path-copy {
  margin: 0;
}

.batch-toolbar-copy span {
  color: var(--qb-text-subtle-8);
}

.batch-toolbar-actions {
  justify-content: flex-end;
}

.pagination-bar {
  display: flex;
  justify-content: flex-end;
  padding-top: var(--qb-space-2);
}

.diagnosis-card {
  padding: var(--qb-space-6);
  gap: var(--qb-space-5);
  transition: transform 0.16s ease, box-shadow 0.16s ease, border-color 0.16s ease;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.99), rgba(247, 250, 255, 0.97));
}

.diagnosis-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--wb-surface-shadow-hover);
  border-color: color-mix(in srgb, var(--qb-primary-student) 18%, white 82%);
}

.focused-error-row {
  border-color: color-mix(in srgb, var(--qb-warning) 38%, white 62%);
  box-shadow: 0 16px 32px color-mix(in srgb, var(--qb-warning) 14%, transparent);
  background: linear-gradient(145deg, rgba(255, 251, 235, 0.98), rgba(255, 255, 255, 0.98));
}

.card-head-main {
  min-width: 0;
  flex: 1;
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.diagnosis-card-body {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(280px, 340px);
  gap: 16px;
  align-items: start;
}

.question-meta-strip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
}

.chapter-pill {
  background: var(--qb-surface-soft-primary);
  color: var(--qb-text-info-ink);
}

.question-stem {
  margin: 0;
  color: var(--qb-text-heading);
  font-size: 16px;
  line-height: 1.72;
  font-weight: 600;
}

.question-path-copy {
  color: var(--qb-text-subtle-8);
  font-size: 12px;
  line-height: 1.6;
  padding-bottom: 4px;
}

.diagnostic-metrics {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.diag-metric {
  gap: 6px;
  padding: var(--qb-space-3);
  border-radius: 16px;
  background: linear-gradient(145deg, rgba(248, 250, 252, 0.98), rgba(255, 255, 255, 0.98));
  border: 1px solid rgba(226, 232, 240, 0.84);
}

.diag-metric span,
.card-ai-meta p,
.detail-copy p,
.paper-preview-item p,
.ai-copy,
.ai-list-item p,
.warning-item p,
.similar-card p {
  margin: 0;
}

.diag-metric span {
  color: var(--qb-text-subtle-8);
  font-size: 12px;
}

.diag-metric strong,
.card-ai-title {
  color: var(--qb-text-heading);
  font-size: 16px;
}

.card-ai-panel {
  gap: var(--qb-space-3);
  padding: var(--qb-space-3-5);
  border-radius: var(--qb-radius-md);
  background:
    radial-gradient(circle at top right, rgba(96, 165, 250, 0.08), transparent 34%),
    linear-gradient(145deg, rgba(255, 255, 255, 0.99), rgba(248, 250, 255, 0.98));
  border: 1px solid rgba(217, 228, 243, 0.9);
  align-self: stretch;
}

.card-ai-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.card-ai-copy,
.card-ai-meta p,
.detail-copy p,
.paper-preview-item p,
.ai-list-item p,
.warning-item p,
.similar-card p {
  color: var(--qb-text-subtle-8);
  line-height: 1.65;
}

.risk-crest {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 var(--qb-space-3);
  border-radius: var(--qb-radius-pill);
  background: var(--qb-gradient-danger-fill);
  color: var(--qb-bg-card);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.04em;
  box-shadow: var(--qb-shadow-danger);
  border: 0;
  cursor: pointer;
  transition: transform 0.16s ease, box-shadow 0.16s ease;
}

.risk-crest:hover {
  transform: translateY(-1px);
  box-shadow: var(--qb-shadow-danger-strong);
}

.row-actions :deep(.el-button) {
  margin-left: 0;
}

.detail-panel {
  grid-template-columns: 1.1fr 1fr;
  gap: var(--qb-space-4);
  padding-top: var(--qb-space-3);
  border-top: 1px dashed rgba(148, 163, 184, 0.26);
}

.detail-copy,
.detail-similar {
  padding: var(--qb-space-3-5);
  border-radius: 22px;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 252, 0.98));
  border: 1px solid rgba(226, 232, 240, 0.76);
}

.similar-card,
.paper-preview-item,
.harvested-card {
  padding: var(--qb-space-3-5);
  border-radius: 24px;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 252, 0.98));
  border: 1px solid var(--qb-border-soft);
}

.ai-card {
  display: grid;
  gap: var(--qb-space-3);
  padding: var(--qb-space-4);
  border-radius: 24px;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.99), rgba(247, 250, 255, 0.97));
}

.support-card {
  min-height: 100%;
}

.harvested-actions {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 10px;
}

.harvested-list {
  gap: var(--qb-space-3);
}

.harvested-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--qb-space-3-5);
}

.harvested-copy {
  display: grid;
  gap: 4px;
}

.alert-card {
  border-color: color-mix(in srgb, var(--qb-danger) 25%, white 75%);
  background: var(--wb-soft-rose);
}

.ai-list-item,
.warning-item {
  display: grid;
  gap: 4px;
  padding: 10px 0;
  border-top: 1px dashed rgba(148, 163, 184, 0.2);
}

.ai-list-item:first-child,
.warning-item:first-child {
  padding-top: 0;
  border-top: 0;
}

.paper-preview-meta {
  margin: 0;
  color: var(--qb-text-subtle-8);
}

.detail-fade-enter-active,
.detail-fade-leave-active {
  transition: all 0.18s ease;
}

.detail-fade-enter-from,
.detail-fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

@media (max-width: 1320px) {
  .mission-scope-grid {
    grid-template-columns: 1fr;
  }

  .scope-column {
    position: static;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    align-items: start;
  }

}

@media (max-width: 1180px) {
  .mission-stat-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .mission-support-grid {
    grid-template-columns: 1fr;
  }

  .diagnosis-card-body,
  .detail-panel {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 960px) {
  .page-header {
    flex-direction: column;
  }

  .diagnosis-card-head,
  .diagnosis-card-footer,
  .harvested-card,
  .pagination-bar,
  .batch-toolbar {
    flex-direction: column;
  }

  .mission-scope-grid,
  .mission-support-grid,
  .scope-column,
  .mission-stat-grid,
  .insight-grid,
  .diagnosis-card-body,
  .diagnostic-metrics,
  .detail-panel {
    grid-template-columns: 1fr;
  }

  .mission-panel-kicker-row {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
