<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ElMessage } from '@/ui/feedback'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '../../stores/userStore.js'
import {
  exportTeacherErrorBookWord,
  exportTeacherErrorBookClassPackage,
  exportTeacherErrorBookClassReport,
  getTeacherErrorBookClassOverview,
  getTeacherErrorBookSummary,
  knowledgeTreeV2,
  listMyClasses,
  listTeacherErrorBookQuestions,
  listTeacherErrorBookStudents,
  listTeacherSimilarWrongBookQuestions,
} from '../../api/services/questionBank'
import { buildContentLabelMaps, resolveContentLabel } from '../../utils/contentBaseline.js'
import { parseExtJson, questionTypeLabel } from '../../utils/question'
import {
  buildKnowledgeLevelTreeState,
  buildKnowledgeSelectorState,
  buildKnowledgeSemanticMap,
} from '../../utils/knowledgeTree'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const tableRef = ref(null)
const summaryLoading = ref(false)
const tableLoading = ref(false)
const studentLoading = ref(false)
const classLoading = ref(false)
const knowledgeTreeLoading = ref(false)
const similarLoadingId = ref('')
const exporting = ref(false)
const aiDrawerVisible = ref(false)
const isAiDrawerMode = ref(typeof window !== 'undefined' ? window.innerWidth < 1200 : false)
const AI_PANEL_BREAKPOINT = 1200

const classOptions = ref([])
const studentOptions = ref([])
const rows = ref([])
const total = ref(0)
const summaryData = ref({
  studentMeta: {},
  selectedSubjectCodes: [],
  subjectRows: [],
  questionInsights: [],
  currentSubject: {},
})
const classOverview = ref({
  classMeta: {},
  summaryCards: {},
  topChapters: [],
  topStudents: [],
})
const selectedQuestionIds = ref([])
const batchStudentUserIds = ref([])
const expandedRowKeys = ref([])
const similarQuestionsMap = ref({})
const knowledgeFilterOptions = ref([])
const selectedKnowledgePath = ref([])
const knowledgeSelectorState = ref(buildKnowledgeSelectorState({}))
const knowledgeSemanticMap = ref({})
const topStudentSortMode = ref('risk')

const selectedClassId = computed(() => String(route.query.classId || '').trim())
const selectedStudentUserId = computed(() => String(route.query.studentUserId || '').trim())
const selectedSubjectCodes = computed(() => {
  const raw = route.query.subjectCodes || route.query.subjectCode || ''
  const normalizedRaw = Array.isArray(raw) ? raw.join(',') : String(raw || '')
  return Array.from(
    new Set(
      normalizedRaw
        .split(',')
        .map((item) => String(item || '').trim())
        .filter((item) => item),
    ),
  )
})
const singleSubjectCode = computed(() => (selectedSubjectCodes.value.length === 1 ? selectedSubjectCodes.value[0] : ''))
const chapterName = computed(() => String(route.query.chapterName || '').trim())
const chapterCode = computed(() => String(route.query.chapterCode || '').trim())
const pointCode = computed(() => String(route.query.pointCode || '').trim())
const pointName = computed(() => String(route.query.pointName || '').trim())
const knowledgeId = computed(() => String(route.query.knowledgeId || '').trim())
const knowledgePathNodeId = computed(() => String(route.query.knowledgePathNodeId || '').trim())
const pathLabel = computed(() => String(route.query.pathLabel || '').trim())

const knowledgeCascaderProps = {
  value: 'value',
  label: 'label',
  children: 'children',
  emitPath: true,
  checkStrictly: true,
}

const pageBusy = computed(() => summaryLoading.value || tableLoading.value || studentLoading.value || classLoading.value)
const subjectRows = computed(() => Array.isArray(summaryData.value.subjectRows) ? summaryData.value.subjectRows : [])
const currentStudentMeta = computed(() =>
  summaryData.value.studentMeta && typeof summaryData.value.studentMeta === 'object'
    ? summaryData.value.studentMeta
    : {},
)
const scopeLabelMaps = computed(() => buildContentLabelMaps(userStore.availableExamCategories))
const currentStudentScopeText = computed(() => ({
  examCategoryName: resolveContentLabel(
    scopeLabelMaps.value.examCategoryNameMap,
    currentStudentMeta.value?.examCategoryCode,
  ),
  jointExamGroupName: resolveContentLabel(
    scopeLabelMaps.value.jointExamGroupNameMap,
    currentStudentMeta.value?.jointExamGroupCode,
  ),
}))
const currentSubject = computed(() =>
  summaryData.value.currentSubject && typeof summaryData.value.currentSubject === 'object'
    ? summaryData.value.currentSubject
    : {},
)
const classMeta = computed(() =>
  classOverview.value.classMeta && typeof classOverview.value.classMeta === 'object'
    ? classOverview.value.classMeta
    : {},
)
const classSummaryCards = computed(() => {
  const cards = classOverview.value.summaryCards && typeof classOverview.value.summaryCards === 'object'
    ? classOverview.value.summaryCards
    : {}
  return [
    { label: '班级学生数', value: Number(cards.studentCount || 0), helper: '当前教师可见学生范围' },
    { label: '有错题学生', value: Number(cards.analyzedStudentCount || 0), helper: '当前筛选科目下有错题记录的学生' },
    { label: '平均练习积分', value: Number(cards.averagePracticePoints || 0).toFixed(1), helper: `${Number(cards.practicePointStudentCount || 0)} 名学生已有积分记录` },
    { label: '平均覆盖率', value: `${Math.round(Number(cards.averageCoverageRate || 0) * 100)}%`, helper: '班级知识覆盖均值' },
    { label: '平均正确率', value: `${Math.round(Number(cards.averageAccuracy || 0) * 100)}%`, helper: '班级学情正确率均值' },
    { label: '风险学生数', value: Number(cards.atRiskStudentCount || 0), helper: '掌握度低或错题偏高的学生' },
    { label: '遗忘预警题', value: Number(cards.overdueQuestionCount || 0), helper: '超过 72 小时未回顾的高频错题' },
  ]
})
const sortedTopStudents = computed(() => {
  const rows = Array.isArray(classOverview.value?.topStudents) ? classOverview.value.topStudents.slice() : []
  if (topStudentSortMode.value === 'points') {
    return rows.sort((left, right) => (
      Number(right?.practicePointTotal || 0) - Number(left?.practicePointTotal || 0)
      || Number(right?.practicePointTodayDelta || 0) - Number(left?.practicePointTodayDelta || 0)
      || Number(right?.wrongCount || 0) - Number(left?.wrongCount || 0)
      || String(left?.studentUserId || '').localeCompare(String(right?.studentUserId || ''))
    ))
  }
  return rows.sort((left, right) => (
    Number(right?.wrongCount || 0) - Number(left?.wrongCount || 0)
    || Number(left?.lowestMastery || 0) - Number(right?.lowestMastery || 0)
    || Number(right?.practicePointTotal || 0) - Number(left?.practicePointTotal || 0)
    || String(left?.studentUserId || '').localeCompare(String(right?.studentUserId || ''))
  ))
})
const currentRepairSuggestions = computed(() => {
  const rows = currentSubject.value?.aiSuggestions?.repairSuggestions
  return Array.isArray(rows) ? rows : []
})
const currentReviewWarnings = computed(() => {
  const rows = currentSubject.value?.aiSuggestions?.reviewWarnings
  return Array.isArray(rows) ? rows : []
})
const insightMap = computed(() =>
  Object.fromEntries(
    (Array.isArray(summaryData.value.questionInsights) ? summaryData.value.questionInsights : [])
      .map((item) => [String(item?.questionId || '').trim(), item])
      .filter(([questionId]) => questionId),
  ),
)

const filterSummary = computed(() => {
  const className = String(classMeta.value?.className || selectedClassId.value || '').trim()
  const studentName = String(currentStudentMeta.value?.studentName || selectedStudentUserId.value || '').trim()
  const subjectSummary = selectedSubjectCodes.value.length
    ? selectedSubjectCodes.value.length === 1
      ? `${subjectRows.value.find((item) => item.subjectCode === selectedSubjectCodes.value[0])?.subjectName || selectedSubjectCodes.value[0]}`
      : `已选 ${selectedSubjectCodes.value.length} 科`
    : '全部科目'

  if (studentName) {
    return `当前教师视角正在分析 ${studentName} 的 ${subjectSummary} 学情修复中心。`
  }
  if (className) {
    return `当前教师视角正在查看 ${className} 的 ${subjectSummary} 班级总览。`
  }
  return '请选择班级或学生后查看学情修复中心。'
})

const studentDashboardCards = computed(() => {
  const chapters = Array.isArray(currentSubject.value?.topChapters) ? currentSubject.value.topChapters : []
  const coverageRate = Number(currentSubject.value?.knowledgeCoverageRate || 0)
  const analyticsOverview = currentSubject.value?.analyticsOverview || {}
  const practicePoints = currentSubject.value?.practicePoints && typeof currentSubject.value.practicePoints === 'object'
    ? currentSubject.value.practicePoints
    : (currentStudentMeta.value?.practicePoints && typeof currentStudentMeta.value.practicePoints === 'object'
      ? currentStudentMeta.value.practicePoints
      : {})
  return [
    {
      label: '练习积分',
      value: Number(practicePoints?.total || 0),
      helper: Number(practicePoints?.rank || 0) > 0
        ? `今日 +${Number(practicePoints?.todayDelta || 0)} / 排名 #${Number(practicePoints.rank || 0)}`
        : `今日 +${Number(practicePoints?.todayDelta || 0)} / ${Number(practicePoints?.selectedSubjectCount || 1)} 科范围`,
    },
    {
      label: '知识覆盖率',
      value: `${Math.round(coverageRate * 100)}%`,
      helper: `${Number(currentSubject.value?.practicedPointCount || 0)} / ${Number(currentSubject.value?.totalPointCount || 0)} 个考点已练习`,
    },
    {
      label: '重灾区章节',
      value: chapters.length ? chapters.map((item) => String(item?.chapterName || item?.chapterCode || '-')).join(' / ') : '暂无',
      helper: chapters.length ? chapters.map((item) => `${item.chapterName || item.chapterCode}: ${item.wrongCount}题`).join('；') : '当前没有高频错题章节',
    },
    {
      label: '遗忘曲线预警',
      value: `${currentReviewWarnings.value.length} 题`,
      helper: currentReviewWarnings.value.length
        ? '超过 72 小时未回顾的高频错题，建议提醒学生优先回看。'
        : '当前没有超过 72 小时的高频遗忘项。',
    },
    {
      label: '学情成绩概览',
      value: `${Math.round(Number(analyticsOverview.averageAccuracy || 0) * 100)}%`,
      helper: `${Number(analyticsOverview.answerCount || 0)} 次作答 / 平均 ${Number(analyticsOverview.averageAnswerDurationSec || 0).toFixed(1)} 秒`,
    },
  ]
})

const currentPracticePointSummary = computed(() => {
  const practicePoints = currentSubject.value?.practicePoints && typeof currentSubject.value.practicePoints === 'object'
    ? currentSubject.value.practicePoints
    : (currentStudentMeta.value?.practicePoints && typeof currentStudentMeta.value.practicePoints === 'object'
      ? currentStudentMeta.value.practicePoints
      : {})
  return {
    total: Number(practicePoints?.total || 0),
    todayDelta: Number(practicePoints?.todayDelta || 0),
    rank: Number(practicePoints?.rank || 0),
    awardUnlocked: Boolean(practicePoints?.awardUnlocked),
    awardProgress: Number(practicePoints?.awardProgress || 0),
    awardThreshold: Number(practicePoints?.awardThreshold || 10000),
    scoreCap: Number(practicePoints?.scoreCap || practicePoints?.awardThreshold || 10000),
    cappedTotal: Number(practicePoints?.cappedTotal || 0),
    scorePercent: Number(practicePoints?.scorePercent || 0),
    levelName: String(practicePoints?.levelName || '倔强青铜'),
    nextLevelName: String(practicePoints?.nextLevelName || ''),
    pointsToNextLevel: Number(practicePoints?.pointsToNextLevel || 0),
    isTopLevel: Boolean(practicePoints?.isTopLevel),
    selectedSubjectCount: Number(practicePoints?.selectedSubjectCount || (selectedSubjectCodes.value.length || 1)),
  }
})

const practicePointSpotlightCards = computed(() => [
  {
    label: '今日新增',
    value: `${currentPracticePointSummary.value.todayDelta}`,
    helper: '今日首次答对带来的练习积分变化',
  },
  {
    label: '科目排名',
    value: currentPracticePointSummary.value.rank ? `#${currentPracticePointSummary.value.rank}` : '多科汇总',
    helper: currentPracticePointSummary.value.rank
      ? '单科模式下展示全站同科目排名'
      : `当前按 ${currentPracticePointSummary.value.selectedSubjectCount} 科汇总，不展示统一排名`,
  },
  {
    label: '当前段位',
    value: currentPracticePointSummary.value.levelName,
    helper: currentPracticePointSummary.value.nextLevelName
      ? `再积 ${currentPracticePointSummary.value.pointsToNextLevel} 分到 ${currentPracticePointSummary.value.nextLevelName}`
      : `已到 ${currentPracticePointSummary.value.scoreCap} 分满阶`,
  },
])

const practicePointSpotlightText = computed(() => {
  if (currentPracticePointSummary.value.rank) {
    return `当前学生累计练习积分 ${currentPracticePointSummary.value.total} 分，今日新增 ${currentPracticePointSummary.value.todayDelta} 分，当前段位 ${currentPracticePointSummary.value.levelName}，单科排名 #${currentPracticePointSummary.value.rank}。`
  }
  return `当前学生累计练习积分 ${currentPracticePointSummary.value.total} 分，今日新增 ${currentPracticePointSummary.value.todayDelta} 分，当前段位 ${currentPracticePointSummary.value.levelName}；当前按 ${currentPracticePointSummary.value.selectedSubjectCount} 科汇总观察积分表现。`
})

function formatDateTime(value) {
  const normalized = String(value || '').trim()
  if (!normalized) {
    return '-'
  }
  return normalized.replace('T', ' ').replace('Z', '')
}

function resolveKnowledgeFilterPathByRoute() {
  const selectorState = knowledgeSelectorState.value || {}
  const pathMap = selectorState?.pathMap || {}
  const chapterCodeMap = selectorState?.chapterCodeMap || {}
  const pointCodeMap = selectorState?.pointCodeMap || {}
  const targetNodeId = knowledgePathNodeId.value || knowledgeId.value
  if (targetNodeId && Array.isArray(pathMap[targetNodeId])) {
    return pathMap[targetNodeId]
  }
  const matchedPointEntry = Object.entries(pointCodeMap).find(([, value]) => String(value || '').trim() === pointCode.value)
  if (matchedPointEntry && Array.isArray(pathMap[matchedPointEntry[0]])) {
    return pathMap[matchedPointEntry[0]]
  }
  const matchedChapterEntry = Object.entries(chapterCodeMap).find(([, value]) => String(value || '').trim() === chapterCode.value)
  if (matchedChapterEntry && Array.isArray(pathMap[matchedChapterEntry[0]])) {
    return pathMap[matchedChapterEntry[0]]
  }
  return []
}

function syncSelectedKnowledgePathFromRoute() {
  selectedKnowledgePath.value = resolveKnowledgeFilterPathByRoute()
}

function resolveQuestionMeta(row) {
  const extJson = parseExtJson(row?.extJson)
  const rowKnowledgeId = String(row?.knowledgeId || '').trim()
  const semantic = knowledgeSemanticMap.value[rowKnowledgeId] || {}
  const insight = insightMap.value[String(row?.id || '').trim()] || {}
  const semanticTrail = Array.isArray(semantic?.semanticTrail) ? semantic.semanticTrail : []
  const semanticTagLine = semanticTrail.map((item) => `${item.levelLabel} ${item.label}`).join(' / ')
  return {
    chapter: String(extJson?.chapter || '').trim() || String(insight?.chapterName || '').trim() || '-',
    chapterCode: String(extJson?.chapter_code || '').trim() || String(insight?.chapterCode || '').trim(),
    pointCode: String(extJson?.point_code || '').trim() || String(insight?.pointCode || '').trim(),
    pointName: String(insight?.pointName || '').trim() || rowKnowledgeId || '-',
    analysis: String(extJson?.analysis || '').trim() || '-',
    semanticPath: String(semantic?.fullPathLabel || '').trim(),
    semanticTagLine,
    currentLevelLabel: String(semantic?.levelLabel || '').trim(),
    masteryScore: Number(insight?.masteryScore || 0),
    wrongCount: Number(insight?.wrongCount || 0),
    submittedAt: formatDateTime(insight?.submittedAt),
    reviewedAt: formatDateTime(insight?.reviewedAt),
    isOverdue72h: Boolean(insight?.isOverdue72h),
    similarQuestions: Array.isArray(similarQuestionsMap.value[String(row?.id || '').trim()])
      ? similarQuestionsMap.value[String(row?.id || '').trim()]
      : [],
  }
}

const normalizedRows = computed(() =>
  rows.value.map((row) => ({
    ...row,
    _meta: resolveQuestionMeta(row),
  })),
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

function buildBaseQuery() {
  return {
    classId: selectedClassId.value,
    studentUserId: selectedStudentUserId.value,
    subjectCodes: selectedSubjectCodes.value.join(','),
  }
}

async function replaceTeacherQuery(patch = {}, { resetKnowledgePath = false } = {}) {
  const nextQuery = {
    ...route.query,
    ...patch,
  }
  if (resetKnowledgePath) {
    delete nextQuery.knowledgePathNodeId
    delete nextQuery.knowledgeId
    delete nextQuery.chapterCode
    delete nextQuery.chapterName
    delete nextQuery.pointCode
    delete nextQuery.pointName
    delete nextQuery.pathLabel
  }
  Object.keys(nextQuery).forEach((key) => {
    const value = nextQuery[key]
    if (value === '' || value === undefined || value === null) {
      delete nextQuery[key]
    }
  })
  await router.replace({ path: route.path, query: nextQuery })
}

async function loadClasses() {
  classLoading.value = true
  try {
    const response = await listMyClasses()
    const data = response?.data && typeof response.data === 'object' ? response.data : response || []
    classOptions.value = Array.isArray(data) ? data : []
    if (!selectedClassId.value && classOptions.value.length) {
      await replaceTeacherQuery({ classId: classOptions.value[0].classId || classOptions.value[0].class_id || classOptions.value[0].value || '' }, { resetKnowledgePath: true })
    }
  } catch (error) {
    classOptions.value = []
    ElMessage.error(error?.response?.data?.message || error?.message || '班级列表加载失败')
  } finally {
    classLoading.value = false
  }
}

async function loadTeacherStudents() {
  studentLoading.value = true
  try {
    const response = await listTeacherErrorBookStudents()
    const data = response?.data && typeof response.data === 'object' ? response.data : response || []
    let nextStudents = Array.isArray(data) ? data : []
    if (selectedClassId.value) {
      nextStudents = nextStudents.filter((item) => String(item?.classId || '').trim() === selectedClassId.value)
    }
    studentOptions.value = nextStudents
    if (selectedStudentUserId.value && !nextStudents.find((item) => String(item.studentUserId) === selectedStudentUserId.value)) {
      await replaceTeacherQuery({ studentUserId: '' }, { resetKnowledgePath: true })
      return
    }
    if (!selectedStudentUserId.value && nextStudents.length) {
      await replaceTeacherQuery({ studentUserId: nextStudents[0].studentUserId }, { resetKnowledgePath: true })
    }
  } catch (error) {
    studentOptions.value = []
    ElMessage.error(error?.response?.data?.message || error?.message || '教师学生列表加载失败')
  } finally {
    studentLoading.value = false
  }
}

async function loadClassOverview() {
  if (!selectedClassId.value) {
    classOverview.value = { classMeta: {}, summaryCards: {}, topChapters: [], topStudents: [] }
    return
  }
  try {
    const response = await getTeacherErrorBookClassOverview({
      classId: selectedClassId.value,
      subjectCodes: selectedSubjectCodes.value.join(','),
    })
    const data = response?.data && typeof response.data === 'object' ? response.data : response || {}
    classOverview.value = {
      classMeta: data?.classMeta && typeof data.classMeta === 'object' ? data.classMeta : {},
      summaryCards: data?.summaryCards && typeof data.summaryCards === 'object' ? data.summaryCards : {},
      topChapters: Array.isArray(data?.topChapters) ? data.topChapters : [],
      topStudents: Array.isArray(data?.topStudents) ? data.topStudents : [],
    }
  } catch (error) {
    classOverview.value = { classMeta: {}, summaryCards: {}, topChapters: [], topStudents: [] }
    ElMessage.error(error?.response?.data?.message || error?.message || '班级总览加载失败')
  }
}

async function loadCenterSummary() {
  if (!selectedStudentUserId.value) {
    summaryData.value = { studentMeta: {}, selectedSubjectCodes: [], subjectRows: [], questionInsights: [], currentSubject: {} }
    return
  }
  summaryLoading.value = true
  try {
    const response = await getTeacherErrorBookSummary(buildBaseQuery())
    const data = response?.data && typeof response.data === 'object' ? response.data : response || {}
    summaryData.value = {
      studentMeta: data?.studentMeta && typeof data.studentMeta === 'object' ? data.studentMeta : {},
      selectedSubjectCodes: Array.isArray(data?.selectedSubjectCodes) ? data.selectedSubjectCodes : [],
      subjectRows: Array.isArray(data?.subjectRows) ? data.subjectRows : [],
      questionInsights: Array.isArray(data?.questionInsights) ? data.questionInsights : [],
      currentSubject: data?.currentSubject && typeof data.currentSubject === 'object' ? data.currentSubject : {},
    }
  } catch (error) {
    summaryData.value = { studentMeta: {}, selectedSubjectCodes: [], subjectRows: [], questionInsights: [], currentSubject: {} }
    ElMessage.error(error?.response?.data?.message || error?.message || '教师学情修复中心汇总加载失败')
  } finally {
    summaryLoading.value = false
  }
}

async function loadKnowledgeTree() {
  if (!singleSubjectCode.value) {
    knowledgeSelectorState.value = buildKnowledgeSelectorState({})
    knowledgeFilterOptions.value = []
    knowledgeSemanticMap.value = {}
    selectedKnowledgePath.value = []
    return
  }
  knowledgeTreeLoading.value = true
  try {
    const response = await knowledgeTreeV2({
      status: 'ENABLED',
      subject_code: singleSubjectCode.value,
    })
    const selectorState = buildKnowledgeSelectorState(response?.data || response || {})
    const levelTreeState = buildKnowledgeLevelTreeState(selectorState, { startLevel: 3, endLevel: 5 })
    knowledgeSelectorState.value = selectorState
    knowledgeFilterOptions.value = Array.isArray(levelTreeState?.options) ? levelTreeState.options : []
    knowledgeSemanticMap.value = buildKnowledgeSemanticMap(selectorState)
    syncSelectedKnowledgePathFromRoute()
  } catch (error) {
    knowledgeSelectorState.value = buildKnowledgeSelectorState({})
    knowledgeFilterOptions.value = []
    knowledgeSemanticMap.value = {}
    selectedKnowledgePath.value = []
    ElMessage.error(error?.response?.data?.message || error?.message || '教师知识树加载失败')
  } finally {
    knowledgeTreeLoading.value = false
  }
}

async function loadWrongBookRows() {
  if (!selectedStudentUserId.value) {
    rows.value = []
    total.value = 0
    return
  }
  tableLoading.value = true
  try {
    const response = await listTeacherErrorBookQuestions({
      ...buildBaseQuery(),
      page: 1,
      size: 200,
      knowledgePathNodeId: knowledgePathNodeId.value,
      chapterCode: chapterCode.value,
      pointCode: pointCode.value,
      knowledgeId: knowledgeId.value,
    })
    const data = response?.data && typeof response.data === 'object' ? response.data : response || {}
    rows.value = Array.isArray(data?.items) ? data.items : []
    total.value = Number(data?.total || rows.value.length || 0)
    selectedQuestionIds.value = []
  } catch (error) {
    rows.value = []
    total.value = 0
    ElMessage.error(error?.response?.data?.message || error?.message || '教师错题明细加载失败')
  } finally {
    tableLoading.value = false
  }
}

async function handleClassChange(nextClassId) {
  await replaceTeacherQuery(
    {
      classId: String(nextClassId || '').trim(),
      studentUserId: '',
      subjectCodes: '',
      subjectCode: '',
    },
    { resetKnowledgePath: true },
  )
}

async function handleStudentChange(nextStudentUserId) {
  await replaceTeacherQuery(
    {
      studentUserId: String(nextStudentUserId || '').trim(),
      subjectCodes: '',
      subjectCode: '',
    },
    { resetKnowledgePath: true },
  )
}

async function handleSubjectToggle(subjectCode) {
  const normalizedSubjectCode = String(subjectCode || '').trim()
  if (!normalizedSubjectCode) return
  const nextCodes = [...selectedSubjectCodes.value]
  const matchedIndex = nextCodes.indexOf(normalizedSubjectCode)
  if (matchedIndex >= 0) nextCodes.splice(matchedIndex, 1)
  else nextCodes.push(normalizedSubjectCode)
  await replaceTeacherQuery(
    {
      subjectCodes: nextCodes.join(','),
      subjectCode: nextCodes.length === 1 ? nextCodes[0] : '',
    },
    { resetKnowledgePath: true },
  )
}

async function handleAllSubjects() {
  await replaceTeacherQuery(
    {
      subjectCodes: '',
      subjectCode: '',
    },
    { resetKnowledgePath: true },
  )
}

async function handleKnowledgePathChange(nextPath) {
  const normalizedPath = Array.isArray(nextPath) ? nextPath.map((item) => String(item || '').trim()).filter((item) => item) : []
  const selectorState = knowledgeSelectorState.value || {}
  const graphIndex = selectorState?.graphIndex || {}
  const levelById = graphIndex?.levelById || {}
  const labelMap = selectorState?.labelMap || {}
  const chapterCodeMap = selectorState?.chapterCodeMap || {}
  const pointCodeMap = selectorState?.pointCodeMap || {}
  const semanticMap = knowledgeSemanticMap.value || {}
  const nextQuery = { ...route.query }
  selectedKnowledgePath.value = normalizedPath
  delete nextQuery.knowledgePathNodeId
  delete nextQuery.knowledgeId
  delete nextQuery.chapterCode
  delete nextQuery.chapterName
  delete nextQuery.pointCode
  delete nextQuery.pointName
  delete nextQuery.pathLabel
  if (!normalizedPath.length) {
    await router.replace({ path: route.path, query: nextQuery })
    return
  }
  const selectedId = normalizedPath[normalizedPath.length - 1]
  const selectedLevel = Number(levelById[selectedId] || 0)
  const semantic = semanticMap[selectedId] || {}
  const semanticTrail = Array.isArray(semantic?.semanticTrail) ? semantic.semanticTrail : []
  const chapterNode = semanticTrail.find((item) => Number(item.level || 0) === 4) || {}
  nextQuery.knowledgePathNodeId = selectedId
  nextQuery.pathLabel = String(
    semantic?.fullPathLabel
    || semanticTrail.map((item) => item.label).join(' / ')
    || normalizedPath.map((item) => String(labelMap[item] || item)).join(' / '),
  )
  if (selectedLevel >= 5) {
    nextQuery.knowledgeId = selectedId
    nextQuery.pointCode = String(pointCodeMap[selectedId] || '')
    nextQuery.pointName = String(labelMap[selectedId] || selectedId)
    if (chapterNode?.id) {
      nextQuery.chapterCode = String(chapterCodeMap[chapterNode.id] || '')
      nextQuery.chapterName = String(chapterNode.label || chapterNode.id)
    }
  } else if (selectedLevel === 4) {
    nextQuery.chapterCode = String(chapterCodeMap[selectedId] || '')
    nextQuery.chapterName = String(labelMap[selectedId] || selectedId)
  }
  await router.replace({ path: route.path, query: nextQuery })
}

function handleSelectionChange(selection) {
  selectedQuestionIds.value = Array.isArray(selection)
    ? selection.map((item) => String(item?.id || '').trim()).filter((item) => item)
    : []
}

async function handleLoadSimilar(row) {
  const questionId = String(row?.id || '').trim()
  if (!questionId || !selectedStudentUserId.value || similarLoadingId.value) return
  similarLoadingId.value = questionId
  try {
    const response = await listTeacherSimilarWrongBookQuestions(questionId, {
      studentUserId: selectedStudentUserId.value,
    })
    const data = response?.data && typeof response.data === 'object' ? response.data : response || {}
    similarQuestionsMap.value = {
      ...similarQuestionsMap.value,
      [questionId]: Array.isArray(data?.items) ? data.items : [],
    }
    expandedRowKeys.value = Array.from(new Set([...expandedRowKeys.value, questionId]))
    if (tableRef.value?.toggleRowExpansion) {
      tableRef.value.toggleRowExpansion(row, true)
    }
  } catch (error) {
    ElMessage.error(error?.response?.data?.message || error?.message || '教师类似题加载失败')
  } finally {
    similarLoadingId.value = ''
  }
}

function downloadBase64File(fileName, mediaType, contentBase64) {
  const binary = window.atob(String(contentBase64 || ''))
  const bytes = new Uint8Array(binary.length)
  for (let index = 0; index < binary.length; index += 1) bytes[index] = binary.charCodeAt(index)
  const blob = new Blob([bytes], { type: mediaType || 'application/octet-stream' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = fileName || 'teacher-error-book.docx'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

async function handleExportWord() {
  if (!selectedStudentUserId.value) {
    ElMessage.warning('请先选择学生。')
    return
  }
  exporting.value = true
  try {
    const exportQuestionIds = selectedQuestionIds.value.length
      ? selectedQuestionIds.value
      : normalizedRows.value.map((item) => String(item?.id || '').trim()).filter((item) => item)
    const response = await exportTeacherErrorBookWord({
      studentUserId: selectedStudentUserId.value,
      subjectCodes: selectedSubjectCodes.value.join(','),
      questionIds: exportQuestionIds,
    })
    const data = response?.data && typeof response.data === 'object' ? response.data : response || {}
    downloadBase64File(data?.fileName, data?.mediaType, data?.contentBase64)
    ElMessage.success(`已生成教师分析卷，共 ${Number(data?.questionCount || 0)} 题。`)
  } catch (error) {
    ElMessage.error(error?.response?.data?.message || error?.message || '教师导出失败')
  } finally {
    exporting.value = false
  }
}

async function handleBatchExport() {
  if (!batchStudentUserIds.value.length) {
    ElMessage.warning('请先勾选要批量导出的学生。')
    return
  }
  exporting.value = true
  try {
    const response = await exportTeacherErrorBookWord({
      studentUserIds: batchStudentUserIds.value,
      subjectCodes: selectedSubjectCodes.value.join(','),
    })
    const data = response?.data && typeof response.data === 'object' ? response.data : response || {}
    downloadBase64File(data?.fileName, data?.mediaType, data?.contentBase64)
    ElMessage.success(`已批量生成 ${Array.isArray(data?.items) ? data.items.length : 0} 份教师分析卷。`)
  } catch (error) {
    ElMessage.error(error?.response?.data?.message || error?.message || '批量导出失败')
  } finally {
    exporting.value = false
  }
}

async function handleClassReportExport() {
  if (!selectedClassId.value) {
    ElMessage.warning('请先选择班级。')
    return
  }
  exporting.value = true
  try {
    const response = await exportTeacherErrorBookClassReport({
      classId: selectedClassId.value,
      subjectCodes: selectedSubjectCodes.value.join(','),
    })
    const data = response?.data && typeof response.data === 'object' ? response.data : response || {}
    downloadBase64File(data?.fileName, data?.mediaType, data?.contentBase64)
    ElMessage.success('班级汇总总报告已开始下载。')
  } catch (error) {
    ElMessage.error(error?.response?.data?.message || error?.message || '班级总报告导出失败')
  } finally {
    exporting.value = false
  }
}

async function handleClassPackageExport() {
  if (!selectedClassId.value) {
    ElMessage.warning('请先选择班级。')
    return
  }
  exporting.value = true
  try {
    const response = await exportTeacherErrorBookClassPackage({
      classId: selectedClassId.value,
      subjectCodes: selectedSubjectCodes.value.join(','),
    })
    const data = response?.data && typeof response.data === 'object' ? response.data : response || {}
    downloadBase64File(data?.fileName, data?.mediaType, data?.contentBase64)
    ElMessage.success(`已生成全班分析包，共 ${Array.isArray(data?.items) ? data.items.length : 0} 份学生报告。`)
  } catch (error) {
    ElMessage.error(error?.response?.data?.message || error?.message || '全班分析包导出失败')
  } finally {
    exporting.value = false
  }
}

onMounted(async () => {
  syncAiDrawerMode()
  window.addEventListener('resize', syncAiDrawerMode)
  await loadClasses()
  await loadTeacherStudents()
  await Promise.all([loadClassOverview(), loadCenterSummary(), loadKnowledgeTree(), loadWrongBookRows()])
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', syncAiDrawerMode)
})

watch(
  () => selectedClassId.value,
  async (nextClassId, previousClassId) => {
    if (nextClassId === previousClassId) return
    batchStudentUserIds.value = []
    await Promise.all([loadTeacherStudents(), loadClassOverview()])
  },
)

watch(
  () => selectedStudentUserId.value,
  async (nextStudentUserId, previousStudentUserId) => {
    if (nextStudentUserId === previousStudentUserId) return
    selectedQuestionIds.value = []
    similarQuestionsMap.value = {}
    expandedRowKeys.value = []
    await Promise.all([loadCenterSummary(), loadKnowledgeTree(), loadWrongBookRows()])
  },
)

watch(
  () => selectedSubjectCodes.value.join(','),
  async (nextValue, previousValue) => {
    if (nextValue === previousValue) return
    selectedKnowledgePath.value = []
    similarQuestionsMap.value = {}
    expandedRowKeys.value = []
    await Promise.all([loadClassOverview(), loadCenterSummary(), loadKnowledgeTree(), loadWrongBookRows()])
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
    await loadWrongBookRows()
  },
)
</script>

<template>
  <section class="error-book-center" v-loading="pageBusy">
    <header class="page-header">
      <div>
        <p class="eyebrow">教师智能学情修复中心</p>
        <h3>学生学情、成绩与班级总览</h3>
        <p class="page-copy">{{ filterSummary }}</p>
      </div>
      <div class="header-actions">
        <el-button v-if="isAiDrawerMode" plain @click="aiDrawerVisible = true">
          AI 建议
        </el-button>
        <el-button
          type="primary"
          :loading="exporting"
          :disabled="!selectedStudentUserId"
          @click="handleExportWord"
        >
          下载教师分析卷
        </el-button>
      </div>
    </header>

    <section class="teacher-toolbar">
      <el-select
        :model-value="selectedClassId"
        class="toolbar-select"
        clearable
        placeholder="选择班级"
        @update:model-value="handleClassChange"
      >
        <el-option
          v-for="classItem in classOptions"
          :key="classItem.classId || classItem.class_id || classItem.value"
          :label="`${classItem.className || classItem.class_name || classItem.label}（${classItem.studentCount || 0}人）`"
          :value="classItem.classId || classItem.class_id || classItem.value"
        />
      </el-select>

      <el-select
        :model-value="selectedStudentUserId"
        class="toolbar-select"
        filterable
        clearable
        placeholder="选择学生"
        @update:model-value="handleStudentChange"
      >
        <el-option
          v-for="student in studentOptions"
          :key="student.studentUserId"
          :label="`${student.studentName}（${student.studentUserId}）`"
          :value="student.studentUserId"
        />
      </el-select>

      <div class="student-meta" v-if="selectedStudentUserId">
        <span>{{ currentStudentMeta.studentName || selectedStudentUserId }}</span>
        <small>{{ currentStudentMeta.vocationalMajor || '-' }} / {{ currentStudentMeta.prepStage || '-' }}</small>
      </div>
    </section>

    <section class="class-overview">
      <div class="section-head">
        <h4>班级维度总览</h4>
        <p>{{ classMeta.className || selectedClassId || '当前班级' }} / 学生 {{ classMeta.studentCount || 0 }} 人</p>
      </div>
      <div class="class-actions">
        <el-button plain :loading="exporting" :disabled="!selectedClassId" @click="handleClassReportExport">
          下载班级总报告
        </el-button>
        <el-button type="primary" :loading="exporting" :disabled="!selectedClassId" @click="handleClassPackageExport">
          一键生成全班分析包
        </el-button>
      </div>
      <div class="class-cards">
        <article v-for="card in classSummaryCards" :key="card.label" class="metric-card">
          <p>{{ card.label }}</p>
          <strong>{{ card.value }}</strong>
          <span>{{ card.helper }}</span>
        </article>
      </div>
      <div class="class-panels">
        <article class="class-panel">
          <div class="class-panel__head">
            <h5>重点学生</h5>
            <div class="sort-toggle">
              <button
                type="button"
                :class="['sort-toggle__button', { 'sort-toggle__button--active': topStudentSortMode === 'risk' }]"
                @click="topStudentSortMode = 'risk'"
              >
                风险优先
              </button>
              <button
                type="button"
                :class="['sort-toggle__button', { 'sort-toggle__button--active': topStudentSortMode === 'points' }]"
                @click="topStudentSortMode = 'points'"
              >
                积分优先
              </button>
            </div>
          </div>
          <el-empty v-if="!sortedTopStudents.length" description="暂无班级学生学情数据" />
          <div v-else class="simple-list">
            <div v-for="item in sortedTopStudents" :key="item.studentUserId" class="simple-row">
              <strong>{{ item.studentName }}</strong>
              <span>积分 {{ Number(item.practicePointTotal || 0) }} / 今日 +{{ Number(item.practicePointTodayDelta || 0) }} / 错 {{ item.wrongCount }} 题</span>
            </div>
          </div>
        </article>
      </div>
    </section>

    <section class="batch-export">
      <div class="section-head">
        <h4>批量导出</h4>
        <p>勾选多个学生后，可批量生成教师分析卷压缩包。</p>
      </div>
      <el-select
        v-model="batchStudentUserIds"
        multiple
        filterable
        clearable
        collapse-tags
        collapse-tags-tooltip
        class="batch-select"
        placeholder="选择多个学生批量导出"
      >
        <el-option
          v-for="student in studentOptions"
          :key="student.studentUserId"
          :label="`${student.studentName}（${student.studentUserId}）`"
          :value="student.studentUserId"
        />
      </el-select>
      <el-button plain :loading="exporting" :disabled="!batchStudentUserIds.length" @click="handleBatchExport">
        批量生成分析卷
      </el-button>
    </section>

    <section class="center-layout">
      <aside class="subject-sidebar">
        <div class="sidebar-head">
          <h4>科目联合分析</h4>
          <p>支持单科聚焦，也支持多科联合分析。</p>
        </div>
        <button
          type="button"
          class="subject-chip"
          :class="{ active: !selectedSubjectCodes.length }"
          @click="handleAllSubjects"
        >
          <span class="subject-chip-head">
            <strong>全部科目</strong>
            <em>{{ subjectRows.reduce((sum, item) => sum + Number(item.redDotCount || 0), 0) }}</em>
          </span>
          <small>查看全部学情修复数据</small>
        </button>
        <button
          v-for="subject in subjectRows"
          :key="subject.subjectCode"
          type="button"
          class="subject-chip"
          :class="{ active: selectedSubjectCodes.includes(subject.subjectCode) }"
          @click="handleSubjectToggle(subject.subjectCode)"
        >
          <span class="subject-chip-head">
            <strong>{{ subject.subjectName || subject.subjectCode }}</strong>
            <em>{{ subject.redDotCount }}</em>
          </span>
          <small>覆盖 {{ Math.round(Number(subject.knowledgeCoverageRate || 0) * 100) }}%</small>
        </button>
      </aside>

      <main class="main-panel">
        <section class="filter-card">
          <div class="filter-copy">
            <h4>2026 五级标签筛选</h4>
            <p v-if="singleSubjectCode">当前单科模式支持从 L3 到 L5 下钻，教师可直接定位错因路径。</p>
            <p v-else>多科模式下不启用单树筛选，请先在左侧切成单科再做 L3-L5 定位。</p>
          </div>
          <el-cascader
            v-if="singleSubjectCode"
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
          <el-alert
            v-else
            type="info"
            :closable="false"
            title="多科联合分析中，请先单选一个科目后再启用知识树路径筛选。"
          />
        </section>

        <section class="practice-point-spotlight">
          <div class="practice-point-spotlight__head">
            <div>
              <p class="practice-point-spotlight__eyebrow">练习积分观察</p>
              <h4>{{ currentStudentMeta.studentName || selectedStudentUserId || '当前学生' }}</h4>
              <p>{{ practicePointSpotlightText }}</p>
            </div>
            <div class="practice-point-spotlight__total">
              <span>累计练习积分</span>
              <strong>{{ currentPracticePointSummary.total }}</strong>
            </div>
          </div>
          <div class="practice-point-spotlight__grid">
            <article v-for="card in practicePointSpotlightCards" :key="card.label" class="practice-point-spotlight__card">
              <span>{{ card.label }}</span>
              <strong>{{ card.value }}</strong>
              <small>{{ card.helper }}</small>
            </article>
          </div>
        </section>

        <section class="dashboard-cards">
          <article v-for="card in studentDashboardCards" :key="card.label" class="metric-card">
            <p>{{ card.label }}</p>
            <strong>{{ card.value }}</strong>
            <span>{{ card.helper }}</span>
          </article>
        </section>

        <el-empty v-if="!normalizedRows.length && !tableLoading" description="当前筛选条件下暂无学生错题记录。" />

        <el-table
          v-else
          ref="tableRef"
          :data="normalizedRows"
          border
          row-key="id"
          :expand-row-keys="expandedRowKeys"
          @selection-change="handleSelectionChange"
        >
          <el-table-column type="selection" width="48" />
          <el-table-column prop="stem" label="题干" min-width="280" show-overflow-tooltip />
          <el-table-column label="5 级标签路径" min-width="260">
            <template #default="scope">
              <div class="path-block">
                <strong>{{ scope.row._meta.semanticPath || '-' }}</strong>
                <small>{{ scope.row._meta.semanticTagLine || scope.row._meta.currentLevelLabel || '-' }}</small>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="诊断定位" min-width="200">
            <template #default="scope">
              <div class="meta-block">
                <span>{{ scope.row._meta.chapter }}</span>
                <small>{{ scope.row._meta.pointCode || '-' }}</small>
                <strong>掌握度 {{ scope.row._meta.masteryScore }}%</strong>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="150">
            <template #default="scope">
              <div class="status-tags">
                <el-tag
                  :type="scope.row._meta.masteryScore < 40 ? 'danger' : scope.row._meta.masteryScore < 70 ? 'warning' : 'success'"
                  effect="light"
                >
                  {{ scope.row._meta.masteryScore }}%
                </el-tag>
                <el-tag v-if="scope.row._meta.isOverdue72h" type="warning" effect="plain">
                  72h 未回顾
                </el-tag>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="错题次数" width="96">
            <template #default="scope">
              {{ scope.row._meta.wrongCount }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="130" fixed="right">
            <template #default="scope">
              <el-button
                plain
                :loading="similarLoadingId === scope.row.id"
                @click="handleLoadSimilar(scope.row)"
              >
                查看类似题
              </el-button>
            </template>
          </el-table-column>
          <el-table-column type="expand">
            <template #default="scope">
              <div class="detail-panel">
                <div class="detail-copy">
                  <p><strong>题型：</strong>{{ questionTypeLabel(scope.row.type) }}</p>
                  <p><strong>答案：</strong>{{ scope.row.answer || '-' }}</p>
                  <p><strong>解析：</strong>{{ scope.row._meta.analysis }}</p>
                  <p><strong>最近交卷：</strong>{{ scope.row._meta.submittedAt }}</p>
                  <p><strong>最近回顾：</strong>{{ scope.row._meta.reviewedAt }}</p>
                </div>

                <div class="detail-similar">
                  <div class="detail-head">
                    <strong>类似题参考</strong>
                  </div>
                  <el-empty
                    v-if="!scope.row._meta.similarQuestions.length"
                    description="点击“查看类似题”后展示同 point_code 的题目。"
                  />
                  <div v-else class="similar-list">
                    <article
                      v-for="item in scope.row._meta.similarQuestions"
                      :key="item.id"
                      class="similar-card"
                    >
                      <strong>{{ questionTypeLabel(item.type) }}</strong>
                      <p>{{ item.stem }}</p>
                    </article>
                  </div>
                </div>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </main>

      <aside v-if="!isAiDrawerMode" class="ai-panel">
        <div class="panel-head">
          <h4>教师侧 AI 建议</h4>
          <p>复用学生端修复规则，转成教师干预视角。</p>
        </div>

        <article class="ai-card">
          <div class="ai-card-head">
            <strong>补短建议</strong>
            <span>{{ currentRepairSuggestions.length }} 条</span>
          </div>
          <el-empty v-if="!currentRepairSuggestions.length" description="当前没有触发底层逻辑错误规则。" />
          <div v-else class="ai-list">
            <div v-for="item in currentRepairSuggestions" :key="item.knowledgeId || item.pointCode" class="ai-list-item">
              <strong>{{ item.pointName }}</strong>
              <p>{{ item.message }}</p>
            </div>
          </div>
        </article>

        <article class="ai-card">
          <div class="ai-card-head">
            <strong>遗忘预警</strong>
            <span>{{ currentReviewWarnings.length }} 条</span>
          </div>
          <el-empty v-if="!currentReviewWarnings.length" description="当前没有超过 72 小时未回顾的高频错题。" />
          <div v-else class="warning-list">
            <div v-for="item in currentReviewWarnings" :key="item.questionId" class="warning-item">
              <strong>{{ item.pointName }}</strong>
              <p>{{ item.overdueHours }} 小时未回顾，累计错 {{ item.wrongCount }} 次。</p>
            </div>
          </div>
        </article>

        <article class="ai-card">
          <div class="ai-card-head">
            <strong>学生画像</strong>
            <span>{{ currentStudentMeta.studentName || '-' }}</span>
          </div>
          <p class="ai-copy">学科门类：{{ currentStudentScopeText.examCategoryName }}</p>
          <p class="ai-copy">专业组：{{ currentStudentScopeText.jointExamGroupName }}</p>
          <p class="ai-copy">专业方向：{{ currentStudentMeta.vocationalMajor || '-' }}</p>
          <p class="ai-copy">备考阶段：{{ currentStudentMeta.prepStage || '-' }}</p>
        </article>
      </aside>
    </section>

    <el-drawer
      v-model="aiDrawerVisible"
      class="ai-drawer"
      direction="ttb"
      size="72vh"
      title="教师侧 AI 建议"
    >
      <section class="ai-panel ai-panel--drawer">
        <div class="panel-head">
          <h4>教师侧 AI 建议</h4>
          <p>复用学生端修复规则，转成教师干预视角。</p>
        </div>

        <article class="ai-card">
          <div class="ai-card-head">
            <strong>补短建议</strong>
            <span>{{ currentRepairSuggestions.length }} 条</span>
          </div>
          <el-empty v-if="!currentRepairSuggestions.length" description="当前没有触发底层逻辑错误规则。" />
          <div v-else class="ai-list">
            <div v-for="item in currentRepairSuggestions" :key="item.knowledgeId || item.pointCode" class="ai-list-item">
              <strong>{{ item.pointName }}</strong>
              <p>{{ item.message }}</p>
            </div>
          </div>
        </article>

        <article class="ai-card">
          <div class="ai-card-head">
            <strong>遗忘预警</strong>
            <span>{{ currentReviewWarnings.length }} 条</span>
          </div>
          <el-empty v-if="!currentReviewWarnings.length" description="当前没有超过 72 小时未回顾的高频错题。" />
          <div v-else class="warning-list">
            <div v-for="item in currentReviewWarnings" :key="item.questionId" class="warning-item">
              <strong>{{ item.pointName }}</strong>
              <p>{{ item.overdueHours }} 小时未回顾，累计错 {{ item.wrongCount }} 次。</p>
            </div>
          </div>
        </article>

        <article class="ai-card">
          <div class="ai-card-head">
            <strong>学生画像</strong>
            <span>{{ currentStudentMeta.studentName || '-' }}</span>
          </div>
          <p class="ai-copy">学科门类：{{ currentStudentScopeText.examCategoryName }}</p>
          <p class="ai-copy">专业组：{{ currentStudentScopeText.jointExamGroupName }}</p>
          <p class="ai-copy">专业方向：{{ currentStudentMeta.vocationalMajor || '-' }}</p>
          <p class="ai-copy">备考阶段：{{ currentStudentMeta.prepStage || '-' }}</p>
        </article>
      </section>
    </el-drawer>
  </section>
</template>

<style scoped>
.error-book-center {
  display: grid;
  gap: 16px;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 18px 20px;
  border-radius: 20px;
  background:
    radial-gradient(circle at top left, rgba(15, 118, 110, 0.16), transparent 42%),
    linear-gradient(145deg, rgba(255, 255, 255, 0.98), rgba(240, 253, 250, 0.92));
  border: 1px solid rgba(13, 148, 136, 0.18);
  box-shadow: 0 14px 32px rgba(15, 23, 42, 0.08);
}

.eyebrow {
  margin: 0 0 8px;
  font-size: 12px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--qb-success);
}

.page-header h3,
.page-copy,
.sidebar-head h4,
.sidebar-head p,
.filter-copy h4,
.filter-copy p,
.panel-head h4,
.panel-head p,
.student-meta span,
.student-meta small,
.section-head h4,
.section-head p {
  margin: 0;
}

.page-header h3 {
  font-size: 28px;
  line-height: 1.1;
}

.page-copy {
  margin-top: 8px;
  color: var(--qb-text-subtle-8);
}

.header-actions,
.teacher-toolbar {
  display: flex;
  gap: 12px;
  align-items: center;
}

.header-actions {
  flex-wrap: wrap;
}

.teacher-toolbar,
.class-overview,
.batch-export {
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid rgba(148, 163, 184, 0.18);
}

.teacher-toolbar {
  flex-wrap: wrap;
}

.toolbar-select,
.batch-select {
  width: min(420px, 100%);
}

.student-meta {
  display: grid;
  gap: 4px;
}

.student-meta small {
  color: var(--qb-text-subtle-8);
}

.section-head {
  display: grid;
  gap: 6px;
  margin-bottom: 12px;
}

.class-cards {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 12px;
}

.class-panels {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-top: 12px;
}

.class-actions {
  display: flex;
  gap: 10px;
  margin-bottom: 12px;
}

.class-panel {
  padding: 14px;
  border-radius: 16px;
  background: linear-gradient(145deg, rgba(255,255,255,0.98), rgba(248,250,252,0.98));
  border: 1px solid rgba(148,163,184,0.16);
}

.class-panel__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.class-panel__head h5 {
  margin: 0;
}

.sort-toggle {
  display: inline-flex;
  gap: 6px;
  padding: 4px;
  border-radius: 999px;
  background: rgba(241, 245, 249, 0.96);
}

.sort-toggle__button {
  padding: 6px 10px;
  border-radius: 999px;
  border: 0;
  background: transparent;
  color: var(--qb-text-subtle-8);
  font-size: 12px;
  font-weight: 700;
}

.sort-toggle__button--active {
  background: rgba(255, 255, 255, 0.98);
  color: var(--qb-text-heading);
  box-shadow: 0 6px 12px rgba(15, 23, 42, 0.08);
}

.simple-list {
  display: grid;
  gap: 8px;
}

.simple-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.center-layout {
  display: grid;
  grid-template-columns: 240px minmax(0, 1fr) 320px;
  gap: 16px;
  align-items: start;
}

.subject-sidebar,
.ai-panel {
  display: grid;
  gap: 12px;
  padding: 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid rgba(148, 163, 184, 0.18);
  box-shadow: 0 12px 24px rgba(15, 23, 42, 0.05);
}

.subject-sidebar {
  position: sticky;
  top: 0;
}

.sidebar-head p,
.panel-head p,
.filter-copy p,
.ai-copy {
  margin-top: 6px;
  color: var(--qb-text-subtle-8);
}

.subject-chip {
  width: 100%;
  display: grid;
  gap: 6px;
  padding: 12px 14px;
  border-radius: 14px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.96), rgba(248, 250, 252, 0.98));
  text-align: left;
  cursor: pointer;
  transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
}

.subject-chip:hover,
.subject-chip.active {
  transform: translateY(-1px);
  border-color: rgba(15, 118, 110, 0.35);
  box-shadow: 0 12px 22px rgba(15, 118, 110, 0.12);
}

.subject-chip-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.subject-chip-head em {
  min-width: 26px;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(239, 68, 68, 0.12);
  color: var(--qb-danger);
  font-style: normal;
  text-align: center;
}

.main-panel {
  display: grid;
  gap: 14px;
}

.filter-card {
  display: grid;
  gap: 12px;
  padding: 16px;
  border-radius: 18px;
  background: linear-gradient(135deg, rgba(236, 253, 245, 0.96), rgba(239, 246, 255, 0.96));
  border: 1px solid rgba(15, 118, 110, 0.14);
}

.knowledge-cascader {
  width: 100%;
}

.practice-point-spotlight {
  display: grid;
  gap: 16px;
  padding: 18px 20px;
  border-radius: 24px;
  background:
    radial-gradient(circle at top right, rgba(245, 158, 11, 0.16), transparent 34%),
    linear-gradient(135deg, rgba(255, 251, 235, 0.98), rgba(255, 255, 255, 0.96));
  border: 1px solid rgba(245, 158, 11, 0.22);
  box-shadow: 0 18px 34px rgba(15, 23, 42, 0.05);
}

.practice-point-spotlight__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
}

.practice-point-spotlight__head h4,
.practice-point-spotlight__head p {
  margin: 0;
}

.practice-point-spotlight__head h4 {
  color: var(--qb-text-heading);
  font-size: 22px;
}

.practice-point-spotlight__head p {
  margin-top: 8px;
  color: var(--qb-text-meta);
  line-height: 1.6;
}

.practice-point-spotlight__eyebrow {
  margin: 0 0 6px;
  color: var(--qb-text-warning-ink);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.practice-point-spotlight__total {
  min-width: 180px;
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.84);
  box-shadow: inset 0 0 0 1px rgba(251, 191, 36, 0.24);
  text-align: right;
}

.practice-point-spotlight__total span,
.practice-point-spotlight__card span,
.practice-point-spotlight__card small {
  color: var(--qb-text-meta);
  font-size: 12px;
}

.practice-point-spotlight__total strong {
  display: block;
  margin-top: 8px;
  color: var(--qb-text-warning-strong);
  font-size: 34px;
  line-height: 1;
}

.practice-point-spotlight__grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.practice-point-spotlight__card {
  display: grid;
  gap: 6px;
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.82);
  box-shadow: inset 0 0 0 1px rgba(251, 191, 36, 0.18);
}

.practice-point-spotlight__card strong {
  color: var(--qb-text-heading);
  font-size: 24px;
  line-height: 1.2;
}

.practice-point-spotlight__card small {
  line-height: 1.5;
}

.dashboard-cards {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.metric-card {
  display: grid;
  gap: 8px;
  padding: 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid rgba(148, 163, 184, 0.16);
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.05);
}

.metric-card p,
.metric-card strong,
.metric-card span,
.path-block strong,
.path-block small,
.meta-block span,
.meta-block small,
.meta-block strong,
.ai-copy {
  margin: 0;
}

.metric-card strong {
  font-size: 20px;
}

.metric-card span {
  color: var(--qb-text-subtle-8);
  line-height: 1.5;
}

.path-block,
.meta-block,
.status-tags,
.detail-panel,
.detail-copy,
.detail-similar,
.similar-list,
.ai-list,
.warning-list {
  display: grid;
  gap: 8px;
}

.path-block small,
.meta-block small {
  color: var(--qb-text-subtle-8);
}

.meta-block strong {
  color: var(--qb-success);
}

.detail-panel {
  grid-template-columns: 1.2fr 1fr;
  gap: 16px;
  padding: 8px 4px;
}

.detail-copy p {
  margin: 0;
  line-height: 1.7;
}

.detail-head,
.ai-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.similar-card,
.ai-card {
  display: grid;
  gap: 10px;
  padding: 14px;
  border-radius: 16px;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 252, 0.98));
  border: 1px solid rgba(148, 163, 184, 0.16);
}

.similar-card p,
.ai-list-item p,
.warning-item p {
  margin: 0;
  color: var(--qb-text-subtle-8);
  line-height: 1.6;
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

.ai-panel--drawer {
  height: 100%;
  overflow: auto;
}

.ai-drawer :deep(.el-drawer__header) {
  margin-bottom: 0;
}

.ai-drawer :deep(.el-drawer__body) {
  padding-top: 8px;
}

@media (max-width: 1199px) {
  .center-layout {
    grid-template-columns: 220px minmax(0, 1fr);
  }
  .practice-point-spotlight__head {
    flex-direction: column;
  }
  .practice-point-spotlight__total {
    width: 100%;
    text-align: left;
  }
  .class-cards {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 960px) {
  .page-header,
  .teacher-toolbar {
    flex-direction: column;
    align-items: stretch;
  }
  .class-panel__head {
    flex-direction: column;
    align-items: flex-start;
  }
  .center-layout,
  .class-panels,
  .practice-point-spotlight__grid,
  .dashboard-cards,
  .detail-panel,
  .class-cards {
    grid-template-columns: 1fr;
  }
  .subject-sidebar {
    position: static;
  }
}
</style>
