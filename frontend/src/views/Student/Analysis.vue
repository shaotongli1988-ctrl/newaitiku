<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ElMessage } from '@/ui/feedback'
import { useRoute, useRouter } from 'vue-router'
import { useSubjectContextStore } from '../../stores/subjectContextStore.js'
import { fetchStudentDashboard } from '../../api/services/student.js'
import { knowledgeTreeV2 } from '../../api/services/questionBank.js'
import { buildKnowledgeSelectorState } from '../../utils/knowledgeTree.js'
import {
  buildStudentGalaxyModel,
  buildStudentGalaxySunburstData,
  classifyGalaxyMasteryBand,
} from '../../utils/studentAnalysisGalaxy.js'
import {
  buildStudentPracticeRouteLocation,
  STUDENT_PRACTICE_SOURCE,
} from '../../utils/studentPracticeNavigation.js'

const DEFAULT_SUBJECT_CODE = 'POLITICS'
const DEFAULT_SUBJECT_NAME = '政治'

const route = useRoute()
const router = useRouter()
const subjectContextStore = useSubjectContextStore()
const chartRef = ref(null)
const loading = ref(true)
const treeLoading = ref(false)
const subjectOptions = ref([])
const selectedSubjectCode = ref(DEFAULT_SUBJECT_CODE)
const loadedSubjectCode = ref('')
const activeChapterId = ref('')
const expandedChapterId = ref('')
const hoveredSectorId = ref('')
const pinnedSectorId = ref('')
const rankingExpanded = ref(false)
const galaxyExpanded = ref(false)
const currentTreePayload = ref(buildKnowledgeSelectorState({}))
let sunburstChart = null
let initEcharts = null
let echartsReadyPromise = null

function unwrapData(response) {
  if (response && typeof response === 'object' && 'data' in response) {
    return response.data
  }
  return response
}

function normalizeString(value) {
  return String(Array.isArray(value) ? value[0] : value || '').trim()
}

function normalizePercent(value) {
  const numericValue = Number(value || 0)
  if (!Number.isFinite(numericValue)) {
    return 0
  }
  const normalized = numericValue > 1 ? numericValue : numericValue * 100
  return Math.max(0, Math.min(100, Math.round(normalized)))
}

function normalizeSubjectOptions(payload) {
  const coreSubjects = Array.isArray(payload?.coreSubjects) ? payload.coreSubjects : []
  return coreSubjects
    .map((item) => ({
      subjectId: String(item?.subjectId || '').trim(),
      subjectCode: String(item?.subjectCode || '').trim(),
      subjectName: String(item?.subjectName || item?.subjectCode || '').trim(),
      answered: Number(item?.progress?.answered || 0),
      total: Number(item?.progress?.total || 0),
      accuracy: Number(item?.progress?.accuracy || 0),
    }))
    .filter((item) => Boolean(item.subjectCode))
}

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

function resolveThemeColor(theme, token, fallback) {
  const direct = String(theme.getPropertyValue(token) || '').trim()
  if (direct) {
    return direct
  }
  if (String(fallback || '').startsWith('--')) {
    return String(theme.getPropertyValue(fallback) || '').trim()
  }
  return fallback
}

function createGalaxyColorResolver() {
  const theme = getComputedStyle(document.documentElement)
  const palette = {
    subject: resolveThemeColor(theme, '--qb-primary-student', '--el-color-primary'),
    unpracticed: resolveThemeColor(theme, '--qb-chart-neutral', '--qb-chart-neutral'),
    weak: resolveThemeColor(theme, '--qb-chart-risk', '--qb-chart-risk'),
    fuzzy: resolveThemeColor(theme, '--qb-chart-mid', '--qb-chart-mid'),
    strong: resolveThemeColor(theme, '--qb-chart-good', '--qb-chart-good'),
  }
  return (mastery, explicitBand = '') => {
    const band = explicitBand || classifyGalaxyMasteryBand(mastery)
    if (band === 'subject') {
      return palette.subject
    }
    return palette[band] || palette.unpracticed
  }
}

const requestedSubjectCode = computed(() => (
  normalizeString(route.query.subjectCode || subjectContextStore.currentSubjectCode || DEFAULT_SUBJECT_CODE)
))
const requestedSubjectId = computed(() => normalizeString(route.query.subjectId))

const subjectMetaMap = computed(() =>
  Object.fromEntries(subjectOptions.value.map((item) => [item.subjectCode, item])),
)

const galaxyModel = computed(() => buildStudentGalaxyModel(currentTreePayload.value))

const currentSubjectMeta = computed(() => subjectMetaMap.value[selectedSubjectCode.value] || null)

const currentSubjectName = computed(() =>
  currentSubjectMeta.value?.subjectName
  || galaxyModel.value.subjectRootLabel
  || (selectedSubjectCode.value === DEFAULT_SUBJECT_CODE ? DEFAULT_SUBJECT_NAME : selectedSubjectCode.value)
  || '当前科目',
)

const chapterSummary = computed(() => galaxyModel.value.chapterCount || 0)
const pointSummary = computed(() => galaxyModel.value.pointCount || 0)
const renderedNodeCount = computed(() => galaxyModel.value.renderedNodeCount || 0)
const averageMastery = computed(() => galaxyModel.value.averageMastery || 0)
const totalWrongCount = computed(() => galaxyModel.value.wrongCount || 0)
const weakPointSummary = computed(() => galaxyModel.value.weakPointCount || 0)
const unpracticedSummary = computed(() => galaxyModel.value.unpracticedPointCount || 0)
const strongPointSummary = computed(() => galaxyModel.value.strongPointCount || 0)

const activeChapter = computed(() =>
  galaxyModel.value.chapterRows.find((item) => item.id === activeChapterId.value) || null,
)
const showChapterDetail = computed(() => Boolean(activeChapter.value))
const currentSubjectAccuracy = computed(() => normalizePercent(currentSubjectMeta.value?.accuracy || 0))
const currentSubjectAnswered = computed(() => Number(currentSubjectMeta.value?.answered || 0))
const currentSubjectTotal = computed(() => Number(currentSubjectMeta.value?.total || 0))
const currentSubjectCompletion = computed(() => {
  const total = currentSubjectTotal.value
  if (!total) {
    return 0
  }
  return Math.max(0, Math.min(100, Math.round((currentSubjectAnswered.value / total) * 100)))
})

const showGalaxyEmpty = computed(() =>
  !loading.value && !treeLoading.value && chapterSummary.value === 0 && pointSummary.value === 0,
)

const galaxyEmptyDescription = computed(() => (
  `当前还没有可用的 ${currentSubjectName.value} 诊断结果，先做一轮练习后，这里会自动给出薄弱点和优先建议。`
))

const stageHeading = computed(() => (
  showChapterDetail.value
    ? `${activeChapter.value?.label || ''} · 章节定位`
    : `${currentSubjectName.value} · 全科定位`
))

const stageDescription = computed(() => (
  showChapterDetail.value
    ? '上方结果已经切到本章，这里继续帮你定位本章的知识分布和考点路径。'
    : '上方先看结果，下方再用图谱补充全科分布和路径定位。'
))

const masteryCompass = computed(() => {
  if (averageMastery.value > 85) {
    return {
      tone: 'good',
      label: '基础稳定',
      description: '整体掌握度已经进入稳定区，建议保持章节练习节奏。',
    }
  }
  if (averageMastery.value >= 60) {
    return {
      tone: 'mid',
      label: '继续巩固',
      description: '结构已经成型，优先把模糊项逐个击穿，避免反复失分。',
    }
  }
  if (averageMastery.value > 0) {
    return {
      tone: 'risk',
      label: '优先补强',
      description: '当前仍有明显断层，建议优先处理最薄弱的章节和考点。',
    }
  }
  return {
    tone: 'neutral',
    label: '待形成画像',
    description: '还没有形成稳定画像，先做一轮练习，系统再给更具体的诊断建议。',
  }
})

function resolveMasteryPresentation(masteryBand = '', masteryScore = 0) {
  if (masteryBand === 'strong') {
    return {
      tone: 'good',
      label: '基础稳定',
      badge: '保持即可',
    }
  }
  if (masteryBand === 'fuzzy') {
    return {
      tone: 'mid',
      label: '需继续巩固',
      badge: '继续巩固',
    }
  }
  if (masteryBand === 'weak') {
    return {
      tone: 'risk',
      label: '需优先补强',
      badge: masteryScore <= 45 ? '优先处理' : '重点补强',
    }
  }
  return {
    tone: 'neutral',
    label: masteryScore > 0 ? '待继续练习' : '待形成画像',
    badge: '先做练习',
  }
}

function buildPriorityReason(point = {}) {
  if (Number(point.wrongCount || 0) >= 3) {
    return {
      label: '先止住失分',
      description: '这个考点已经连续出错，先补起来最能减少重复失分。',
      nextStep: '建议先做错因回练，再补一轮同类题。',
    }
  }
  if (Number(point.questionCount || 0) >= 6) {
    return {
      label: '练了还不稳',
      description: '题目覆盖已经不低，但掌握度还没站稳，适合集中巩固。',
      nextStep: '建议连续完成 2 组专项，把手感拉稳。',
    }
  }
  if (Number(point.masteryScore || 0) <= 55) {
    return {
      label: '提分窗口大',
      description: '当前掌握度偏低，集中练一轮通常更容易看到明显提升。',
      nextStep: '建议先把基础题做顺，再追求速度。',
    }
  }
  return {
    label: '再压一轮',
    description: '已经有一定基础，再做一轮巩固更容易把状态拉稳。',
    nextStep: '建议做一组短练，及时把模糊点补齐。',
  }
}

function computeRecommendedPracticeCount(point = {}) {
  const practiceCount = Math.round((100 - Number(point.masteryScore || 0)) / 8) + Number(point.wrongCount || 0) + 4
  return Math.max(6, Math.min(14, practiceCount))
}

function buildChapterPointRows(chapter = {}) {
  return (Array.isArray(chapter.points) ? chapter.points : [])
    .map((point) => {
      const presentation = resolveMasteryPresentation(point.masteryBand, point.masteryScore)
      const priorityReason = buildPriorityReason(point)
      const displayLabel = String(point.displayLabel || point.shortLabel || point.label || '').trim() || String(point.label || '').trim()
      const fullLabel = String(point.fullLabel || point.label || displayLabel).trim() || displayLabel
      return {
        ...point,
        chapterLabel: chapter.label,
        chapterDisplayLabel: String(chapter.displayLabel || chapter.label || '').trim() || String(chapter.label || '').trim(),
        displayLabel,
        fullLabel,
        displayPathLabel: String(point.displayPathLabel || point.pathLabel || displayLabel).trim(),
        fullPathLabel: String(point.pathLabel || point.displayPathLabel || displayLabel).trim(),
        ...presentation,
        reasonLabel: priorityReason.label,
        reasonDescription: priorityReason.description,
        nextStepLabel: priorityReason.nextStep,
        recommendedPracticeCount: computeRecommendedPracticeCount(point),
        primaryActionLabel: Number(point.masteryScore || 0) <= 50 ? '开始专项补强' : '开始这一组练习',
        secondaryActionLabel: '看知识定位',
        priorityScore: ((100 - Number(point.masteryScore || 0)) * 2)
          + (Number(point.wrongCount || 0) * 12)
          + (Math.min(Number(point.questionCount || 0), 10) * 3),
      }
    })
    .sort((left, right) => {
      if (left.priorityScore !== right.priorityScore) {
        return right.priorityScore - left.priorityScore
      }
      return left.masteryScore - right.masteryScore
    })
}

function buildChapterGuidance(chapter = {}) {
  if (Number(chapter.weakPointCount || 0) >= 4) {
    return {
      insightLabel: '先补这一章',
      insightDescription: '这一章薄弱点更集中，优先处理通常最能带动整体提升。',
      nextStepLabel: '先点进本章，把前 3 个薄弱点依次做完。',
    }
  }
  if (Number(chapter.unpracticedPointCount || 0) >= 3) {
    return {
      insightLabel: '先把画像补齐',
      insightDescription: '这一章还存在不少未练习考点，先补数据才能给出更稳的诊断。',
      nextStepLabel: '先做一轮基础练习，把未覆盖考点点亮。',
    }
  }
  if (Number(chapter.masteryScore || 0) <= 60) {
    return {
      insightLabel: '值得先攻克',
      insightDescription: '这一章掌握度偏低，但提升空间明显，适合尽快进入专项练习。',
      nextStepLabel: '建议先做基础题，再回看错因定位。',
    }
  }
  return {
    insightLabel: '继续稳一稳',
    insightDescription: '这一章基础已经有了，再补一轮能更快把状态拉稳。',
    nextStepLabel: '点进本章做一组短练，把模糊点压实。',
  }
}

const chapterOverviewRows = computed(() => (
  galaxyModel.value.chapterRows
    .map((chapter) => {
      const presentation = resolveMasteryPresentation(chapter.masteryBand, chapter.masteryScore)
      const guidance = buildChapterGuidance(chapter)
      return {
        ...chapter,
        ...presentation,
        ...guidance,
        summaryText: `${chapter.pointCount} 个考点 · ${chapter.weakPointCount} 个待补强`,
        summaryCompact: `待补强 ${chapter.weakPointCount} · 未练习 ${chapter.unpracticedPointCount}`,
        actionHint: activeChapterId.value === chapter.id ? '当前已切到本章' : '点击查看本章诊断',
      }
    })
    .sort((left, right) => {
      if (left.masteryScore !== right.masteryScore) {
        return left.masteryScore - right.masteryScore
      }
      return right.weakPointCount - left.weakPointCount
    })
))

const moduleOverviewHighlights = computed(() => chapterOverviewRows.value.slice(0, 2))

const scopedPointRows = computed(() => {
  const sourceChapters = showChapterDetail.value && activeChapter.value
    ? [activeChapter.value]
    : galaxyModel.value.chapterRows

  return sourceChapters
    .flatMap((chapter) => buildChapterPointRows(chapter))
    .sort((left, right) => {
      if (left.priorityScore !== right.priorityScore) {
        return right.priorityScore - left.priorityScore
      }
      return left.masteryScore - right.masteryScore
    })
})

const weakRankingRows = computed(() => scopedPointRows.value.slice(0, 5))
const priorityActionRows = computed(() => scopedPointRows.value.slice(0, 3))
const rankingLeadPoint = computed(() => weakRankingRows.value[0] || null)
const chapterCollapseRows = computed(() => (
  chapterOverviewRows.value.map((chapter) => {
    const pointRows = buildChapterPointRows(chapter)
    return {
      ...chapter,
      priorityPoints: pointRows.slice(0, 3),
      estimatedPracticeTotal: pointRows.slice(0, 3).reduce((sum, item) => sum + Number(item.recommendedPracticeCount || 0), 0),
    }
  })
))

const rankingTitle = computed(() => (
  showChapterDetail.value
    ? `${activeChapter.value?.label || ''} · 本章先补这几项`
    : '当前最需要先补的薄弱点'
))

const rankingDescription = computed(() => (
  showChapterDetail.value
    ? '已切到当前章节，建议先处理下面这 5 个最拖分的考点。'
    : '按掌握度、错频和练习覆盖综合排序，先补最拖分、也最值得补的点。'
))

const rankingCollapsedSummary = computed(() => {
  const leadPoint = rankingLeadPoint.value
  if (!leadPoint) {
    return '当前还没有足够的练习数据，先做一轮专项后这里会自动生成薄弱点排行。'
  }
  return `当前最该先补「${leadPoint.displayLabel || leadPoint.label}」，其后还有 ${Math.max(0, weakRankingRows.value.length - 1)} 个高优先级薄弱点。`
})

const overviewSummaryText = computed(() => {
  const chapterNames = chapterOverviewRows.value
    .slice(0, 2)
    .map((item) => item.label)
    .filter(Boolean)
  if (!chapterNames.length) {
    return '先完成一轮练习，系统会自动给出更清晰的章节优先顺序。'
  }
  return `先看 ${chapterNames.join('、')} 的整体情况，再进入下方优先攻克逐项处理。`
})

const heroRecommendationText = computed(() => {
  const actionNames = priorityActionRows.value
    .map((item) => item.displayLabel || item.label)
    .filter(Boolean)
  if (!actionNames.length) {
    return '先完成一轮练习，诊断页会自动生成优先攻克建议。'
  }
  return `先补 ${actionNames.join('、')}，通常能更快看到提分变化。`
})

const analysisBridgeCopy = computed(() => {
  const actionNames = priorityActionRows.value
    .slice(0, 2)
    .map((item) => item.displayLabel || item.label)
    .filter(Boolean)
  if (!actionNames.length) {
    return '诊断不是终点，它是在先帮你找准提分方向。开始练习后，这里会继续告诉你哪些点补起来最能带动积分和考试得分。'
  }
  return `诊断不是终点，而是在帮你决定下一轮分该往哪里拿。优先补 ${actionNames.join('、')}，通常更容易把薄弱点转成稳定正确输出，段位分涨得更快，升本时也更容易把会做的题真正拿下。`
})

function buildPracticeRouteLocation(meta = {}) {
  const basePayload = {
    subjectCode: selectedSubjectCode.value || DEFAULT_SUBJECT_CODE,
    pathLabel: String(meta.pathLabel || meta.label || currentSubjectName.value || '').trim(),
    practiceSource: STUDENT_PRACTICE_SOURCE.KNOWLEDGE,
    practiceSourceLabel: '知识点专项进入',
  }
  const level = Number(meta.level || 0)
  if (level >= 5) {
    return buildStudentPracticeRouteLocation({
      ...basePayload,
      knowledgeId: String(meta.id || ''),
      chapterCode: String(meta.chapterCode || ''),
      chapterName: String(meta.chapterName || ''),
      pointCode: String(meta.pointCode || ''),
      pointName: String(meta.label || ''),
    })
  }
  if (level === 4) {
    return buildStudentPracticeRouteLocation({
      ...basePayload,
      chapterCode: String(meta.chapterCode || ''),
      chapterName: String(meta.label || ''),
    })
  }
  if (level === 1) {
    return buildStudentPracticeRouteLocation(basePayload)
  }
  return null
}

function buildQuestionBankRouteLocation(meta = {}) {
  const nextQuery = {
    subjectCode: selectedSubjectCode.value || DEFAULT_SUBJECT_CODE,
  }
  const level = Number(meta.level || 0)
  const normalizedPathLabel = String(meta.pathLabel || meta.label || currentSubjectName.value || '').trim()
  if (normalizedPathLabel) {
    nextQuery.pathLabel = normalizedPathLabel
  }
  if (level >= 5) {
    nextQuery.knowledgeId = String(meta.id || '').trim()
    nextQuery.chapterCode = String(meta.chapterCode || '').trim()
    nextQuery.chapterName = String(meta.chapterName || '').trim()
    nextQuery.pointCode = String(meta.pointCode || '').trim()
    nextQuery.pointName = String(meta.label || '').trim()
  } else if (level === 4) {
    nextQuery.chapterCode = String(meta.chapterCode || '').trim()
    nextQuery.chapterName = String(meta.label || '').trim()
  }
  return {
    path: '/student/question-bank/repair',
    query: nextQuery,
  }
}

async function pushPractice(meta = {}) {
  const nextLocation = buildPracticeRouteLocation(meta)
  if (!nextLocation) {
    return
  }
  await router.push(nextLocation)
}

async function openQuestionBank(meta = {}) {
  await router.push(buildQuestionBankRouteLocation(meta))
}

async function openChallengePoints() {
  await router.push({
    path: '/student/analysis/points',
    query: {
      ...route.query,
      subjectCode: selectedSubjectCode.value || DEFAULT_SUBJECT_CODE,
    },
  })
}

async function handleEmptyPracticeStart() {
  await pushPractice({
    level: 1,
    subjectCode: selectedSubjectCode.value,
    label: currentSubjectName.value,
  })
}

async function focusSubjectOverview() {
  galaxyExpanded.value = true
  pinnedSectorId.value = String(galaxyModel.value.subjectRootId || selectedSubjectCode.value || DEFAULT_SUBJECT_CODE).trim()
  hoveredSectorId.value = ''
  await resetChapterDrill()
}

async function focusChapterOverview(chapter = {}) {
  const normalizedChapter = createFocusNode({
    ...chapter,
    chapterCode: chapter.chapterCode,
    chapterName: chapter.label,
    level: 4,
    pathLabel: chapter.pathLabel || chapter.label,
  })
  if (!normalizedChapter) {
    return
  }
  galaxyExpanded.value = true
  pinnedSectorId.value = normalizedChapter.id
  hoveredSectorId.value = ''
  await handleChapterDrill(normalizedChapter.id)
}

async function handleChapterCollapseChange(nextValue) {
  const normalizedChapterId = String(Array.isArray(nextValue) ? nextValue[0] || '' : nextValue || '').trim()
  if (!normalizedChapterId) {
    await resetChapterDrill()
    return
  }
  const matchedChapter = chapterCollapseRows.value.find((item) => item.id === normalizedChapterId)
  if (!matchedChapter) {
    return
  }
  await focusChapterOverview(matchedChapter)
}

async function focusKnowledgePoint(point = {}) {
  const normalizedPoint = createFocusNode({
    ...point,
    chapterName: point.chapterLabel || point.chapterName || '',
    pathLabel: point.pathLabel || point.label,
  })
  if (!normalizedPoint) {
    return
  }
  galaxyExpanded.value = true
  pinnedSectorId.value = normalizedPoint.id
  hoveredSectorId.value = ''
  if (normalizedPoint.chapterId && normalizedPoint.chapterId !== activeChapterId.value) {
    activeChapterId.value = normalizedPoint.chapterId
    await renderSunburst()
  }
}

function focusChartNode(targetNodeId) {
  const normalizedTargetNodeId = String(targetNodeId || '').trim()
  if (!sunburstChart || !normalizedTargetNodeId) {
    return
  }
  sunburstChart.dispatchAction({
    type: 'sunburstRootToNode',
    seriesIndex: 0,
    targetNodeId: normalizedTargetNodeId,
  })
}

function createFocusNode(meta = {}) {
  const mastery = normalizePercent(meta.mastery || meta.masteryScore || 0)
  const normalizedMeta = {
    id: String(meta.id || '').trim(),
    label: String(meta.label || '').trim(),
    fullLabel: String(meta.fullLabel || meta.label || '').trim(),
    pathLabel: String(meta.displayPathLabel || meta.pathLabel || meta.label || '').trim(),
    fullPathLabel: String(meta.fullPathLabel || meta.pathLabel || meta.displayPathLabel || meta.label || '').trim(),
    level: Number(meta.level || 0),
    masteryScore: mastery,
    masteryBand: String(meta.masteryBand || classifyGalaxyMasteryBand(Number(meta.mastery || mastery / 100))).trim(),
    wrongCount: Math.max(0, Number(meta.wrongCount || 0)),
    questionCount: Math.max(0, Number(meta.questionCount || 0)),
    chapterId: String(meta.chapterId || '').trim(),
    chapterCode: String(meta.chapterCode || '').trim(),
    chapterName: String(meta.chapterName || '').trim(),
    pointCode: String(meta.pointCode || '').trim(),
  }

  if (!normalizedMeta.id) {
    return null
  }

  const typeLabel = normalizedMeta.level >= 5 ? '考点' : normalizedMeta.level === 4 ? '章节' : '科目'
  const ringLabel = normalizedMeta.level >= 5 ? '外环' : normalizedMeta.level === 4 ? '内环' : '中心'

  return {
    ...normalizedMeta,
    typeLabel,
    ringLabel,
    pathSegments: normalizedMeta.pathLabel
      ? normalizedMeta.pathLabel.split('/').map((item) => String(item || '').trim()).filter(Boolean)
      : [normalizedMeta.label],
    practiceRouteLocation: buildPracticeRouteLocation(normalizedMeta),
  }
}

const focusNodeMap = computed(() => {
  const nodeMap = {}
  const subjectId = String(galaxyModel.value.subjectRootId || selectedSubjectCode.value || DEFAULT_SUBJECT_CODE).trim()
  const subjectNode = createFocusNode({
    id: subjectId,
    label: currentSubjectName.value,
    pathLabel: currentSubjectName.value,
    level: 1,
    mastery: galaxyModel.value.averageMasteryValue || 0,
    masteryBand: 'subject',
    wrongCount: galaxyModel.value.wrongCount || 0,
    questionCount: galaxyModel.value.chapterRows.reduce((sum, item) => sum + Number(item.questionCount || 0), 0),
  })

  if (subjectNode) {
    nodeMap[subjectNode.id] = subjectNode
  }

  galaxyModel.value.chapterRows.forEach((chapter) => {
    const chapterNode = createFocusNode({
      id: chapter.id,
      label: chapter.label,
      pathLabel: chapter.pathLabel,
      level: 4,
      mastery: chapter.mastery,
      masteryBand: chapter.masteryBand,
      wrongCount: chapter.wrongCount,
      questionCount: chapter.questionCount,
      chapterCode: chapter.chapterCode,
      chapterName: chapter.label,
    })
    if (chapterNode) {
      nodeMap[chapterNode.id] = chapterNode
    }

    chapter.points.forEach((point) => {
      const pointNode = createFocusNode({
        id: point.id,
        label: point.label,
        pathLabel: point.pathLabel,
        level: point.level,
        mastery: point.mastery,
        masteryBand: point.masteryBand,
        wrongCount: point.wrongCount,
        questionCount: point.questionCount,
        chapterId: chapter.id,
        chapterCode: point.chapterCode,
        chapterName: chapter.label,
        pointCode: point.pointCode,
      })
      if (pointNode) {
        nodeMap[pointNode.id] = pointNode
      }
    })
  })

  return nodeMap
})

const activeFocusNode = computed(() => {
  const focusId = String(hoveredSectorId.value || pinnedSectorId.value || '').trim()
  return focusNodeMap.value[focusId] || null
})

const hasFocusNode = computed(() => Boolean(activeFocusNode.value))
const focusCardMode = computed(() => (hoveredSectorId.value ? '悬停预览' : '已锁定'))
const focusEmptyCopy = computed(() => (
  showChapterDetail.value
    ? '先点上方的薄弱点或优先攻克卡片，这里就会显示本章对应的定位和练习入口。'
    : '先点章节卡、薄弱点排行或图谱节点，这里就会显示对应路径和下一步入口。'
))

const detailSummary = computed(() => {
  const node = activeFocusNode.value
  if (!node) {
    return ''
  }
  if (node.level >= 5) {
    return '这个考点已经定位好了，可以直接查看路径并开始专项练习。'
  }
  if (node.level === 4) {
    return '这一章已经和上方总览联动，继续下钻就能看到本章最值得先补的考点。'
  }
  return '全科层只负责给出整体定位，真正的优先级已经收敛到上方总览和行动卡。'
})
const galaxyPreviewSummary = computed(() => {
  if (hasFocusNode.value) {
    return `当前已定位到「${activeFocusNode.value.label}」，展开图谱可以查看完整路径和关联分布。`
  }
  if (showChapterDetail.value && activeChapter.value) {
    return `当前聚焦「${activeChapter.value.label}」，需要看本章在整科中的位置时再展开图谱。`
  }
  return `当前可定位 ${renderedNodeCount.value} 个节点；图谱先收起，需要时再展开查看章节和考点分布。`
})

const canPracticeFocusedNode = computed(() => Boolean(activeFocusNode.value?.practiceRouteLocation))
const canDrillFocusedChapter = computed(() => (
  activeFocusNode.value?.level === 4 && activeFocusNode.value?.id !== activeChapterId.value
))

async function handleChapterDrill(chapterId) {
  const normalizedChapterId = String(chapterId || '').trim()
  if (!normalizedChapterId || normalizedChapterId === activeChapterId.value) {
    return
  }
  activeChapterId.value = normalizedChapterId
  await renderSunburst()
}

async function resetChapterDrill() {
  if (!activeChapterId.value) {
    return
  }
  activeChapterId.value = ''
  await renderSunburst()
}

function handleChartHover(meta = {}) {
  const normalizedId = String(meta.id || '').trim()
  hoveredSectorId.value = normalizedId
}

function handleChartPin(meta = {}) {
  const normalizedId = String(meta.id || '').trim()
  if (!normalizedId) {
    return
  }
  pinnedSectorId.value = normalizedId
}

async function syncChartInteraction(meta = {}, { pin = false } = {}) {
  const normalizedMeta = createFocusNode(meta)
  if (!normalizedMeta) {
    return
  }
  handleChartHover(normalizedMeta)
  if (pin) {
    handleChartPin(normalizedMeta)
  }
  if (!pin) {
    return
  }
  if (normalizedMeta.level === 4) {
    await handleChapterDrill(normalizedMeta.id)
    return
  }
  if (normalizedMeta.level === 1) {
    await resetChapterDrill()
  }
}

async function renderSunburst() {
  await nextTick()
  if (!chartRef.value) {
    return
  }
  await ensureEchartsRuntime()

  if (!sunburstChart) {
    sunburstChart = initEcharts(chartRef.value)
    sunburstChart.on('mouseover', (params) => {
      const meta = params?.data?.meta || {}
      handleChartHover(meta)
    })
    sunburstChart.on('mouseout', () => {
      hoveredSectorId.value = ''
    })
    sunburstChart.on('globalout', () => {
      hoveredSectorId.value = ''
    })
    sunburstChart.on('click', async (params) => {
      const meta = params?.data?.meta || {}
      await syncChartInteraction(meta, { pin: true })
    })
  }

  const colorResolver = createGalaxyColorResolver()
  const seriesData = buildStudentGalaxySunburstData(
    {
      ...galaxyModel.value,
      subjectCode: selectedSubjectCode.value,
      subjectName: currentSubjectName.value,
    },
    colorResolver,
  )

  if (!seriesData[0]?.children?.length) {
    sunburstChart.clear()
    return
  }

  const theme = getComputedStyle(document.documentElement)
  const textHeading = resolveThemeColor(theme, '--qb-text-heading', '--qb-text-main')
  const textSubtle = resolveThemeColor(theme, '--qb-text-meta', '--qb-text-secondary')
  const cardBg = resolveThemeColor(theme, '--qb-bg-card', '--qb-bg-subtle')
  const focusGlow = resolveThemeColor(theme, '--qb-primary-student', '--el-color-primary')
  const showLeafLabels = showChapterDetail.value

  sunburstChart.setOption({
    tooltip: {
      trigger: 'item',
      formatter(params) {
        const meta = params?.data?.meta || {}
        const mastery = normalizePercent(meta.mastery || 0)
        return [
          String(meta.label || params?.name || ''),
          ...(String(meta.fullLabel || '').trim() && String(meta.fullLabel || '').trim() !== String(meta.label || '').trim()
            ? [`全称：${String(meta.fullLabel || '').trim()}`]
            : []),
          `路径：${String(meta.fullPathLabel || meta.pathLabel || meta.label || '')}`,
          `掌握度：${mastery}%`,
          `错误频次：${Math.max(0, Number(meta.wrongCount || 0))}`,
        ].join('<br>')
      },
    },
    series: [
      {
        type: 'sunburst',
        radius: ['0%', '92%'],
        center: ['50%', '52%'],
        sort: null,
        nodeClick: false,
        minAngle: 2,
        animationDuration: 420,
        animationDurationUpdate: 320,
        itemStyle: {
          borderColor: cardBg,
          borderWidth: 2,
        },
        label: {
          color: textHeading,
          overflow: 'truncate',
        },
        emphasis: {
          focus: 'ancestor',
          label: {
            show: true,
            color: textHeading,
            fontSize: 12,
            fontWeight: 700,
          },
          itemStyle: {
            shadowBlur: 22,
            shadowColor: `${focusGlow}30`,
          },
        },
        blur: {
          itemStyle: {
            opacity: 0.16,
          },
        },
        levels: [
          {},
          {
            r0: '0%',
            r: '24%',
            label: {
              show: true,
              rotate: 0,
              fontSize: 16,
              fontWeight: 700,
              align: 'center',
            },
            itemStyle: {
              borderWidth: 0,
            },
          },
          {
            r0: '24%',
            r: '58%',
            label: {
              show: true,
              rotate: 'tangential',
              fontSize: 11,
              fontWeight: 600,
              minAngle: 18,
              overflow: 'truncate',
            },
            itemStyle: {
              borderWidth: 2,
              borderColor: cardBg,
            },
          },
          {
            r0: '58%',
            r: '92%',
            label: {
              show: showLeafLabels,
              rotate: 'radial',
              fontSize: 10,
              color: textSubtle,
              minAngle: showLeafLabels ? 7 : 180,
            },
            itemStyle: {
              borderWidth: 1,
              borderColor: cardBg,
            },
          },
        ],
        data: seriesData,
      },
    ],
  }, { notMerge: true })

  await nextTick()
  if (showChapterDetail.value && activeChapterId.value) {
    focusChartNode(activeChapterId.value)
  } else {
    focusChartNode(galaxyModel.value.subjectRootId || selectedSubjectCode.value || DEFAULT_SUBJECT_CODE)
  }

  sunburstChart.resize()
}

async function syncRouteSubject(subjectCode, subjectId = '') {
  const normalizedSubjectCode = String(subjectCode || '').trim()
  const normalizedSubjectId = String(subjectId || '').trim()
  if (!normalizedSubjectCode) {
    return
  }
  if (
    normalizedSubjectCode === requestedSubjectCode.value
    && normalizedSubjectId === requestedSubjectId.value
  ) {
    return
  }
  await router.replace({
    path: route.path,
    query: {
      ...route.query,
      subjectCode: normalizedSubjectCode,
      subjectId: normalizedSubjectId,
    },
  })
}

async function loadKnowledgeTree(subjectCode, subjectId = '') {
  const normalizedSubjectCode = String(subjectCode || '').trim() || DEFAULT_SUBJECT_CODE
  const normalizedSubjectId = String(subjectId || '').trim()
  treeLoading.value = true

  try {
    const response = await knowledgeTreeV2({
      status: 'ENABLED',
      subject_code: normalizedSubjectCode,
      subject_id: normalizedSubjectId,
    })
    currentTreePayload.value = buildKnowledgeSelectorState(unwrapData(response) || {})
    selectedSubjectCode.value = normalizedSubjectCode
    subjectContextStore.setCurrentSubjectCode(normalizedSubjectCode)
    loadedSubjectCode.value = normalizedSubjectCode
    activeChapterId.value = ''
    hoveredSectorId.value = ''
    pinnedSectorId.value = ''
    await renderSunburst()
  } catch (error) {
    currentTreePayload.value = buildKnowledgeSelectorState({})
    loadedSubjectCode.value = ''
    activeChapterId.value = ''
    hoveredSectorId.value = ''
    pinnedSectorId.value = ''
    await renderSunburst()
    ElMessage.error(error?.response?.data?.message || error?.message || '知识诊断加载失败')
  } finally {
    treeLoading.value = false
  }
}

async function loadDashboardContext() {
  try {
    const payload = await fetchStudentDashboard()
    const rows = normalizeSubjectOptions(payload)
    const fallbackSubjectName = galaxyModel.value.subjectRootLabel || currentSubjectName.value || DEFAULT_SUBJECT_NAME
    if (selectedSubjectCode.value && !rows.some((item) => item.subjectCode === selectedSubjectCode.value)) {
      rows.unshift({
        subjectId: requestedSubjectId.value,
        subjectCode: selectedSubjectCode.value,
        subjectName: fallbackSubjectName,
        answered: 0,
        total: 0,
        accuracy: 0,
      })
    }
    subjectOptions.value = rows
    subjectContextStore.setSubjectOptions(rows, selectedSubjectCode.value)
    await syncRouteSubject(
      selectedSubjectCode.value,
      String(subjectMetaMap.value[selectedSubjectCode.value]?.subjectId || requestedSubjectId.value || '').trim(),
    )
  } catch (_error) {
    if (selectedSubjectCode.value) {
      subjectOptions.value = [
        {
          subjectId: requestedSubjectId.value,
          subjectCode: selectedSubjectCode.value,
          subjectName: galaxyModel.value.subjectRootLabel || DEFAULT_SUBJECT_NAME,
          answered: 0,
          total: 0,
          accuracy: 0,
        },
      ]
      subjectContextStore.setSubjectOptions(subjectOptions.value, selectedSubjectCode.value)
    }
  }
}

function resizeChart() {
  sunburstChart?.resize()
}

watch(
  () => requestedSubjectCode.value,
  async (nextSubjectCode, previousSubjectCode) => {
    const normalizedSubjectCode = String(nextSubjectCode || DEFAULT_SUBJECT_CODE).trim()
    if (
      !normalizedSubjectCode
      || normalizedSubjectCode === previousSubjectCode
      || normalizedSubjectCode === loadedSubjectCode.value
    ) {
      return
    }
    selectedSubjectCode.value = normalizedSubjectCode
    await loadKnowledgeTree(
      normalizedSubjectCode,
      requestedSubjectId.value || String(subjectMetaMap.value[normalizedSubjectCode]?.subjectId || '').trim(),
    )
    await loadDashboardContext()
  },
)

watch(
  () => galaxyModel.value.chapterRows.map((item) => item.id).join(','),
  async () => {
    if (activeChapterId.value && !activeChapter.value) {
      activeChapterId.value = ''
      await renderSunburst()
    }
    if (pinnedSectorId.value && !focusNodeMap.value[pinnedSectorId.value]) {
      pinnedSectorId.value = ''
    }
    if (hoveredSectorId.value && !focusNodeMap.value[hoveredSectorId.value]) {
      hoveredSectorId.value = ''
    }
  },
)

watch(
  () => activeChapterId.value,
  (nextChapterId) => {
    expandedChapterId.value = String(nextChapterId || '').trim()
    if (String(nextChapterId || '').trim()) {
      galaxyExpanded.value = true
    }
  },
)

watch(
  () => hasFocusNode.value,
  (nextValue) => {
    if (nextValue) {
      galaxyExpanded.value = true
    }
  },
)

watch(
  () => galaxyExpanded.value,
  async (nextValue) => {
    if (nextValue) {
      await renderSunburst()
    }
  },
)

onMounted(async () => {
  loading.value = true
  const initialSubjectCode = requestedSubjectCode.value || DEFAULT_SUBJECT_CODE
  selectedSubjectCode.value = initialSubjectCode
  await loadKnowledgeTree(initialSubjectCode, requestedSubjectId.value)
  await loadDashboardContext()
  loading.value = false
  window.addEventListener('resize', resizeChart)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeChart)
  sunburstChart?.dispose()
  sunburstChart = null
})
</script>

<template>
  <section class="analysis-page">
    <header class="hero-card hero-card--compact">
      <div class="hero-main-row">
        <div class="hero-copy-block">
          <div class="hero-kicker-row">
            <p class="eyebrow">知识诊断</p>
            <span class="board-pill" :class="`board-pill--${masteryCompass.tone}`">{{ masteryCompass.label }}</span>
          </div>
          <div class="hero-title-inline">
            <h3>知识结构与薄弱点诊断</h3>
            <p class="hero-copy">{{ heroRecommendationText }}</p>
          </div>
        </div>
        <div class="hero-compact-score">
          <small>综合掌握</small>
          <strong>{{ averageMastery }}%</strong>
        </div>
      </div>

      <div class="hero-summary-strip">
        <article class="hero-summary-chip">
          <span>当前科目</span>
          <strong>{{ currentSubjectName }}</strong>
        </article>
        <article class="hero-summary-chip">
          <span>练习进度</span>
          <strong>{{ currentSubjectCompletion }}%</strong>
        </article>
        <article class="hero-summary-chip">
          <span>待补强</span>
          <strong>{{ weakPointSummary }}</strong>
        </article>
        <article class="hero-summary-chip">
          <span>章节 / 考点</span>
          <strong>{{ chapterSummary }} / {{ pointSummary }}</strong>
        </article>
      </div>

      <div class="hero-bridge-card">
        <strong>诊断结果只有转成下一轮动作，才会变成真正的分数</strong>
        <p>{{ analysisBridgeCopy }}</p>
      </div>

      <div class="hero-summary-actions">
        <el-button type="primary" plain @click="openChallengePoints">看刷题段位</el-button>
        <el-button plain @click="openQuestionBank({ level: 1, label: currentSubjectName })">去错题中心处理题目</el-button>
      </div>
    </header>

    <div class="analysis-shell" v-loading="loading || treeLoading">
      <section v-if="showGalaxyEmpty" class="summary-card summary-card--empty">
        <el-empty :description="galaxyEmptyDescription" />
        <div class="analysis-empty-panel__actions">
          <el-button type="primary" plain @click="handleEmptyPracticeStart">先去做一轮练习</el-button>
        </div>
      </section>

      <template v-else>
        <section class="module-overview-card">
          <div class="section-head">
            <div class="section-head-copy">
              <p class="section-eyebrow">模块总览</p>
              <h4>{{ currentSubjectName }} · 当前章节主线</h4>
              <p>{{ overviewSummaryText }}</p>
            </div>
            <div class="module-overview-actions">
              <el-button v-if="showChapterDetail" plain @click="focusSubjectOverview">回到全科视角</el-button>
              <el-button plain @click="openQuestionBank({ level: 1, label: currentSubjectName })">去错题中心</el-button>
            </div>
          </div>

          <div class="summary-stat-strip summary-stat-strip--compact">
            <div>
              <small>平均掌握</small>
              <strong>{{ averageMastery }}%</strong>
            </div>
            <div>
              <small>薄弱项</small>
              <strong>{{ weakPointSummary }}</strong>
            </div>
            <div>
              <small>未练习</small>
              <strong>{{ unpracticedSummary }}</strong>
            </div>
            <div>
              <small>高掌握</small>
              <strong>{{ strongPointSummary }}</strong>
            </div>
          </div>

        </section>

        <section class="galaxy-board">
          <div class="galaxy-board__head">
            <div class="galaxy-board__copy">
              <p class="section-eyebrow">辅助定位</p>
              <h4>{{ stageHeading }}</h4>
              <p>{{ galaxyPreviewSummary }}</p>
            </div>
            <button
              type="button"
              class="galaxy-toggle"
              :aria-expanded="String(galaxyExpanded)"
              @click="galaxyExpanded = !galaxyExpanded"
            >
              <span>{{ galaxyExpanded ? '收起图谱' : '展开图谱' }}</span>
              <span :class="['galaxy-toggle__chevron', { 'galaxy-toggle__chevron--expanded': galaxyExpanded }]">⌄</span>
            </button>
          </div>

          <transition name="galaxy-collapse">
            <div v-if="galaxyExpanded" class="galaxy-layout">
              <section class="galaxy-card galaxy-card--chart">
                <div class="chart-toolbar">
                  <div class="chart-toolbar-row">
                    <span class="chart-toolbar-label">图层说明</span>
                    <div class="ring-guide">
                      <span class="ring-chip ring-chip--subject">中心 / 科目</span>
                      <span class="ring-chip">L4 / 章节</span>
                      <span class="ring-chip">L5 / 考点</span>
                    </div>
                  </div>
                  <div class="legend legend--inline">
                    <span class="legend-chip legend-neutral">未练习</span>
                    <span class="legend-chip legend-risk">需补强</span>
                    <span class="legend-chip legend-mid">需巩固</span>
                    <span class="legend-chip legend-good">基础稳定</span>
                  </div>
                </div>

                <div class="stage-shell">
                  <div ref="chartRef" class="chart-stage" />
                </div>
              </section>

              <aside class="galaxy-aside">
                <article class="aside-card detail-card">
                  <div class="aside-head">
                    <span class="aside-label">定位详情</span>
                    <span v-if="hasFocusNode" class="focus-mode">{{ focusCardMode }}</span>
                  </div>

                  <template v-if="hasFocusNode">
                    <div class="detail-title-row">
                      <div class="detail-title-copy">
                        <strong>{{ activeFocusNode.label }}</strong>
                        <p v-if="activeFocusNode.fullLabel && activeFocusNode.fullLabel !== activeFocusNode.label" class="detail-full-label">
                          {{ activeFocusNode.fullLabel }}
                        </p>
                        <p>{{ detailSummary }}</p>
                      </div>
                      <span class="detail-level-chip">{{ activeFocusNode.ringLabel }} · {{ activeFocusNode.typeLabel }}</span>
                    </div>

                    <div class="detail-path">
                      <span class="path-label">完整路径</span>
                      <div class="path-chip-row">
                        <span
                          v-for="segment in activeFocusNode.pathSegments"
                          :key="segment"
                          class="path-chip"
                        >
                          {{ segment }}
                        </span>
                      </div>
                    </div>

                    <dl class="detail-metrics">
                      <div>
                        <dt>掌握度</dt>
                        <dd>{{ activeFocusNode.masteryScore }}%</dd>
                      </div>
                      <div>
                        <dt>错误频次</dt>
                        <dd>{{ activeFocusNode.wrongCount }}</dd>
                      </div>
                      <div>
                        <dt>关联题量</dt>
                        <dd>{{ activeFocusNode.questionCount }}</dd>
                      </div>
                      <div>
                        <dt>层级</dt>
                        <dd>L{{ activeFocusNode.level }}</dd>
                      </div>
                    </dl>

                    <div class="detail-actions">
                      <el-button
                        v-if="canPracticeFocusedNode"
                        type="primary"
                        @click="pushPractice(activeFocusNode)"
                      >
                        专项练习
                      </el-button>
                      <el-button plain @click="openQuestionBank(activeFocusNode || {})">
                        去错题中心
                      </el-button>
                      <el-button
                        v-if="canDrillFocusedChapter"
                        plain
                        @click="handleChapterDrill(activeFocusNode.id)"
                      >
                        切到本章视角
                      </el-button>
                      <el-button
                        v-if="showChapterDetail"
                        plain
                        @click="focusSubjectOverview"
                      >
                        回到全科视角
                      </el-button>
                    </div>
                  </template>

                  <div v-else class="detail-empty">
                    <strong>先选一个点看看</strong>
                    <p>{{ focusEmptyCopy }}</p>
                  </div>
                </article>
              </aside>
            </div>
          </transition>
        </section>
      </template>
    </div>
  </section>
</template>

<style scoped>
.analysis-page {
  display: grid;
  gap: var(--qb-space-4);
  --galaxy-surface: linear-gradient(180deg, var(--qb-surface-strong), rgba(242, 247, 255, 0.96));
  --galaxy-border: color-mix(in srgb, var(--qb-primary-student) 14%, white);
  --galaxy-shadow: 0 28px 72px rgba(15, 23, 42, 0.08);
  --galaxy-neutral: var(--qb-chart-neutral);
  --galaxy-risk: var(--qb-chart-risk);
  --galaxy-mid: var(--qb-chart-mid);
  --galaxy-good: var(--qb-chart-good);
}

.hero-card {
  display: grid;
  gap: var(--qb-space-3);
  padding: var(--qb-space-4-5);
  border-radius: var(--qb-student-card-radius-strong);
  background:
    radial-gradient(circle at top left, color-mix(in srgb, var(--qb-info) 24%, transparent), transparent 34%),
    radial-gradient(circle at 85% 20%, color-mix(in srgb, var(--qb-primary-student) 18%, transparent), transparent 24%),
    linear-gradient(135deg, rgba(235, 243, 255, 0.96) 0%, rgba(240, 249, 255, 0.98) 62%, rgba(247, 250, 255, 0.98) 100%);
  border: 1px solid var(--galaxy-border);
  box-shadow: var(--qb-student-card-shadow-strong);
}

.hero-card--compact {
  align-items: start;
}

.hero-main-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--qb-space-3);
}

.hero-copy-block {
  display: grid;
  gap: var(--qb-space-2);
  min-width: 0;
}

.hero-kicker-row {
  display: flex;
  align-items: center;
  gap: var(--qb-space-2);
  flex-wrap: wrap;
}

.hero-title-inline {
  display: grid;
  gap: 6px;
}

.eyebrow {
  display: inline-flex;
  width: fit-content;
  margin: 0 0 6px;
  padding: 6px 10px;
  border-radius: var(--qb-radius-pill);
  background: var(--qb-student-kicker-bg);
  color: var(--qb-student-kicker-text);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.hero-card h3 {
  margin: 0;
  font-size: 24px;
}

.hero-copy {
  margin: 0;
  color: var(--qb-text-meta);
  line-height: 1.6;
}

.hero-compact-score {
  display: grid;
  gap: 4px;
  min-width: 120px;
  justify-items: end;
  padding: 10px 12px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid var(--qb-border-glass);
}

.hero-compact-score small {
  color: var(--qb-text-meta);
  font-size: 12px;
}

.hero-compact-score strong {
  color: var(--qb-primary-student);
  font-size: 26px;
  line-height: 1;
}

.hero-summary-strip {
  display: grid;
  gap: var(--qb-space-2);
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.hero-summary-chip {
  display: grid;
  gap: 4px;
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.74);
  border: 1px solid var(--qb-border-glass);
}

.hero-summary-chip span {
  color: var(--qb-text-meta);
  font-size: 12px;
}

.hero-summary-chip strong {
  color: var(--qb-text-heading);
  font-size: 16px;
}

.hero-bridge-card {
  display: grid;
  gap: 8px;
  padding: 16px 18px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid var(--qb-border-glass);
}

.hero-bridge-card strong,
.hero-bridge-card p {
  margin: 0;
}

.hero-bridge-card p {
  color: var(--qb-text-copy);
  line-height: 1.7;
}

.hero-summary-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--qb-space-2);
  flex-wrap: wrap;
}

.hero-summary-actions :deep(.el-button) {
  margin-left: 0;
}

.analysis-empty-panel {
  display: grid;
  gap: 12px;
}

.analysis-empty-panel__actions {
  display: flex;
  justify-content: center;
  gap: 10px;
  flex-wrap: wrap;
}

.analysis-shell {
  display: grid;
  gap: var(--qb-space-4);
}

.action-zone {
  display: grid;
  gap: var(--qb-space-4);
}

.summary-card,
.priority-section {
  display: grid;
  gap: var(--qb-space-4);
  padding: var(--qb-space-5);
  border-radius: 28px;
  border: 1px solid var(--qb-border-glass);
  box-shadow: 0 16px 36px rgba(15, 23, 42, 0.06);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.97), rgba(241, 246, 255, 0.95));
}

.summary-card--ranking {
  align-content: start;
  background:
    linear-gradient(180deg, rgba(251, 253, 255, 0.98), rgba(238, 244, 255, 0.94));
}

.summary-card--empty {
  justify-items: center;
}

.section-head {
  display: flex;
  justify-content: space-between;
  gap: var(--qb-space-3);
  align-items: flex-start;
}

.section-head-copy {
  display: grid;
  gap: 8px;
}

.section-head h4 {
  margin: 0;
  font-size: 24px;
  color: var(--qb-text-heading);
  line-height: 1.25;
}

.section-head p {
  margin: 0;
  color: var(--qb-text-meta);
  line-height: 1.65;
}

.summary-stat-strip {
  display: grid;
  gap: var(--qb-space-3);
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
}

.summary-stat-strip--compact {
  gap: var(--qb-space-2);
}

.summary-stat-strip div {
  display: grid;
  gap: 4px;
  padding: 14px 16px;
  border-radius: var(--qb-radius-lg);
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid var(--qb-border-glass);
}

.summary-stat-strip small {
  color: var(--qb-text-meta);
}

.summary-stat-strip strong {
  color: var(--qb-text-heading);
  font-size: 20px;
}

.module-overview-card,
.chapter-collapse-section,
.priority-section {
  display: grid;
  gap: var(--qb-space-3);
  padding: var(--qb-space-4-5);
  border-radius: 28px;
  border: 1px solid var(--qb-border-glass);
  box-shadow: 0 16px 36px rgba(15, 23, 42, 0.06);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.97), rgba(241, 246, 255, 0.95));
}

.module-overview-card {
  background:
    radial-gradient(circle at 12% 18%, rgba(47, 84, 235, 0.08), transparent 28%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.99), rgba(239, 246, 255, 0.96));
}

.module-overview-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--qb-space-2-5);
  align-items: flex-start;
  justify-content: flex-end;
}

.module-overview-layout {
  display: grid;
  gap: var(--qb-space-3);
}

.module-highlight-card,
.chapter-panel-summary,
.chapter-panel-list {
  border-radius: 24px;
  border: 1px solid var(--qb-border-glass);
  background: rgba(255, 255, 255, 0.88);
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.05);
}

.chapter-point-row {
  width: 100%;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--qb-space-3);
  padding: 14px 16px;
  border-radius: 18px;
  border: 1px solid var(--qb-border-glass);
  background: rgba(255, 255, 255, 0.78);
  cursor: pointer;
  text-align: left;
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}

.chapter-point-row:hover {
  transform: translateY(-1px);
  box-shadow: 0 14px 28px rgba(15, 23, 42, 0.08);
}

.chapter-point-copy strong {
  color: var(--qb-text-heading);
  font-weight: 700;
}

.chapter-point-copy p {
  color: var(--qb-text-meta);
  line-height: 1.6;
}

.module-highlight-grid {
  display: grid;
  gap: var(--qb-space-2);
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.module-highlight-card {
  display: grid;
  gap: var(--qb-space-2);
  padding: 16px;
  cursor: pointer;
  text-align: left;
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}

.module-highlight-card__main,
.module-highlight-card__meta,
.module-highlight-card__action {
  display: grid;
  gap: 4px;
}

.module-highlight-card__summary {
  margin: 0;
  color: var(--qb-text-meta);
  font-size: 12px;
  line-height: 1.55;
}

.module-highlight-card__meta span,
.module-highlight-card__action span {
  color: var(--qb-text-meta);
  font-size: 12px;
}

.module-highlight-card__meta strong,
.module-highlight-card__action strong {
  color: var(--qb-text-heading);
  font-size: 13px;
  line-height: 1.5;
}

.module-highlight-card__action {
  padding-top: 6px;
  border-top: 1px dashed color-mix(in srgb, var(--qb-border-glass) 72%, white 28%);
}

.module-highlight-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 16px 30px rgba(15, 23, 42, 0.08);
}

.module-highlight-card--risk {
  border-color: color-mix(in srgb, var(--qb-danger) 18%, white);
}

.module-highlight-card--mid {
  border-color: color-mix(in srgb, var(--qb-warning) 18%, white);
}

.module-highlight-card--good {
  border-color: color-mix(in srgb, var(--qb-success) 18%, white);
}

.chapter-collapse-section {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(244, 248, 255, 0.96));
}

.chapter-collapse {
  display: grid;
  gap: var(--qb-space-3);
}

.chapter-collapse-title {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--qb-space-3);
  width: 100%;
  padding-right: var(--qb-space-3);
}

.chapter-collapse-title-main,
.chapter-collapse-title-side,
.chapter-collapse-state,
.chapter-panel-head,
.chapter-point-copy,
.chapter-point-meta {
  display: grid;
  gap: 6px;
}

.chapter-collapse-title-main strong,
.chapter-panel-head strong {
  color: var(--qb-text-heading);
  font-size: 18px;
}

.chapter-collapse-title-main p,
.chapter-point-copy p {
  margin: 0;
  color: var(--qb-text-meta);
  line-height: 1.6;
}

.chapter-collapse-title--active .chapter-collapse-title-main p {
  color: var(--qb-text-secondary-strong);
}

.chapter-collapse-title-side {
  justify-items: end;
}

.chapter-collapse-state {
  justify-items: end;
}

.chapter-collapse-metrics {
  display: flex;
  gap: var(--qb-space-2);
  flex-wrap: wrap;
  justify-content: flex-end;
}

.chapter-current-badge,
.chapter-collapse-metrics span,
.chapter-point-meta span {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: var(--qb-radius-pill);
  background: color-mix(in srgb, var(--qb-primary-soft-bg) 72%, white 28%);
  color: var(--qb-primary-student);
  font-size: 11px;
  font-weight: 600;
}

.chapter-current-badge {
  background: color-mix(in srgb, var(--qb-primary-student) 16%, white);
  color: var(--qb-text-info-ink);
  border: 1px solid color-mix(in srgb, var(--qb-primary-student) 28%, white);
}

.chapter-panel-grid {
  display: grid;
  gap: var(--qb-space-3);
  grid-template-columns: minmax(280px, 0.95fr) minmax(0, 1.05fr);
  padding-top: var(--qb-space-2);
}

.chapter-panel-summary,
.chapter-panel-list {
  display: grid;
  gap: var(--qb-space-2-5);
  padding: 18px;
}

.chapter-panel-stats {
  display: grid;
  gap: var(--qb-space-2-5);
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.chapter-panel-stats div {
  display: grid;
  gap: 4px;
  padding: 12px;
  border-radius: var(--qb-radius-md);
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid var(--qb-border-glass);
}

.chapter-panel-stats small {
  color: var(--qb-text-meta);
}

.chapter-panel-stats strong,
.chapter-point-meta strong {
  color: var(--qb-text-heading);
  font-size: 18px;
}

.chapter-panel-points {
  display: grid;
  gap: var(--qb-space-2-5);
}

.chapter-panel-summary-line {
  display: grid;
  gap: 4px;
  padding: 10px 12px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.76);
  border: 1px solid var(--qb-border-glass);
}

.chapter-panel-summary-line span {
  color: var(--qb-text-meta);
  font-size: 12px;
}

.chapter-panel-summary-line strong {
  color: var(--qb-text-heading);
  font-size: 14px;
  line-height: 1.55;
}

.chapter-panel-summary-line--action {
  background: color-mix(in srgb, var(--qb-primary-soft-bg) 58%, white 42%);
}

.chapter-point-meta {
  justify-items: end;
  min-width: 84px;
}

:deep(.chapter-collapse .el-collapse) {
  border: none;
}

:deep(.chapter-collapse .el-collapse-item) {
  border: 1px solid var(--qb-border-glass);
  border-radius: 24px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.82);
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.05);
}

:deep(.chapter-collapse .chapter-collapse-item--active) {
  border-color: color-mix(in srgb, var(--qb-primary-student) 28%, white);
  background: linear-gradient(180deg, rgba(247, 251, 255, 0.98), rgba(234, 243, 255, 0.94));
  box-shadow: 0 16px 32px rgba(47, 84, 235, 0.10);
}

:deep(.chapter-collapse .el-collapse-item__header) {
  min-height: 82px;
  padding: 16px 20px;
  border: none;
  background: transparent;
  line-height: normal;
}

:deep(.chapter-collapse .el-collapse-item__wrap) {
  border: none;
  background: transparent;
}

:deep(.chapter-collapse .el-collapse-item__content) {
  padding: 0 20px 20px;
}

.chapter-grid {
  display: grid;
  gap: var(--qb-space-3);
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.chapter-card,
.ranking-row {
  width: 100%;
  border: 1px solid var(--qb-border-glass);
  background: rgba(255, 255, 255, 0.86);
  cursor: pointer;
  text-align: left;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

.chapter-card:hover,
.ranking-row:hover {
  transform: translateY(-1px);
  box-shadow: 0 14px 28px rgba(15, 23, 42, 0.08);
}

.chapter-card {
  display: grid;
  gap: var(--qb-space-3);
  padding: 18px;
  border-radius: 22px;
}

.chapter-card--active {
  border-color: color-mix(in srgb, var(--qb-primary-student) 28%, white);
  box-shadow: 0 18px 30px rgba(47, 84, 235, 0.12);
}

.chapter-card-head,
.ranking-title-row,
.priority-card-head {
  display: flex;
  justify-content: space-between;
  gap: var(--qb-space-2-5);
  align-items: flex-start;
}

.chapter-card-head strong,
.ranking-title-row strong,
.priority-card strong {
  color: var(--qb-text-heading);
}

.chapter-card-head strong,
.priority-card strong {
  font-size: 20px;
  line-height: 1.3;
}

.chapter-card p,
.priority-card p {
  margin: 0;
  color: var(--qb-text-secondary);
  line-height: 1.65;
}

.chapter-card-summary,
.priority-card-summary {
  color: var(--qb-text-meta);
}

.chapter-card-insight,
.chapter-card-next-step {
  display: grid;
  gap: 6px;
  padding: 12px 14px;
  border-radius: 16px;
  background: color-mix(in srgb, var(--qb-primary-soft-bg) 58%, white 42%);
  border: 1px solid color-mix(in srgb, var(--qb-primary-student) 10%, white 90%);
}

.chapter-card-insight span,
.chapter-card-next-step span {
  color: var(--qb-text-meta);
  font-size: 12px;
}

.chapter-card-insight strong,
.chapter-card-next-step strong {
  font-size: 14px;
  line-height: 1.6;
  color: var(--qb-text-heading);
}

.chapter-card-badge,
.priority-rank {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 28px;
  padding: 0 12px;
  border-radius: var(--qb-radius-pill);
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
}

.chapter-card-badge--good {
  background: color-mix(in srgb, var(--qb-success) 14%, white);
  color: var(--qb-text-success-strong);
}

.chapter-card-badge--mid {
  background: color-mix(in srgb, var(--qb-warning) 14%, white);
  color: var(--qb-text-warning-strong);
}

.chapter-card-badge--risk {
  background: color-mix(in srgb, var(--qb-danger) 12%, white);
  color: var(--qb-text-danger-strong);
}

.chapter-card-badge--neutral {
  background: var(--qb-bg-muted);
  color: var(--qb-text-meta);
}

.chapter-card-progress,
.ranking-bar {
  position: relative;
  height: 10px;
  border-radius: var(--qb-radius-pill);
  background: var(--qb-bg-muted);
  overflow: hidden;
}

.chapter-card-progress span,
.ranking-bar span {
  position: absolute;
  inset: 0 auto 0 0;
  border-radius: inherit;
  background: linear-gradient(90deg, var(--qb-primary-student), color-mix(in srgb, var(--qb-primary-student) 52%, white 48%));
}

.chapter-card-foot {
  display: flex;
  justify-content: space-between;
  gap: var(--qb-space-2);
  flex-wrap: wrap;
  color: var(--qb-text-meta);
  font-size: 12px;
}

.ranking-list,
.priority-grid {
  display: grid;
  gap: var(--qb-space-3);
}

.ranking-toggle {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border: 1px solid var(--qb-border-glass);
  border-radius: var(--qb-radius-pill);
  background: rgba(255, 255, 255, 0.82);
  color: var(--qb-text-secondary-strong);
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: background-color 0.18s ease, border-color 0.18s ease, transform 0.18s ease;
}

.ranking-toggle:hover {
  background: rgba(255, 255, 255, 0.96);
  border-color: color-mix(in srgb, var(--qb-primary-student) 18%, white);
  transform: translateY(-1px);
}

.ranking-toggle__chevron {
  display: inline-flex;
  transition: transform 0.18s ease;
}

.ranking-toggle__chevron--expanded {
  transform: rotate(180deg);
}

.ranking-collapsed {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--qb-space-3);
  padding: 16px 18px;
  border-radius: 20px;
  border: 1px solid var(--qb-border-glass);
  background: rgba(255, 255, 255, 0.82);
}

.ranking-collapsed__copy {
  display: grid;
  gap: 6px;
  min-width: 0;
}

.ranking-collapsed__copy strong,
.ranking-collapsed__copy p {
  margin: 0;
}

.ranking-collapsed__copy strong {
  color: var(--qb-text-heading);
  font-size: 15px;
  line-height: 1.6;
}

.ranking-collapsed__copy p {
  color: var(--qb-text-meta);
  font-size: 12px;
  line-height: 1.6;
}

.ranking-collapsed__action {
  flex-shrink: 0;
  padding: 10px 14px;
  border: 1px solid color-mix(in srgb, var(--qb-primary-student) 14%, white);
  border-radius: 16px;
  background: color-mix(in srgb, var(--qb-primary-soft-bg) 62%, white 38%);
  color: var(--qb-primary-student);
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease, background-color 0.18s ease;
}

.ranking-collapsed__action:hover {
  transform: translateY(-1px);
  box-shadow: 0 12px 24px rgba(47, 84, 235, 0.12);
}

.ranking-collapse-enter-active,
.ranking-collapse-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
  transform-origin: top center;
}

.ranking-collapse-enter-from,
.ranking-collapse-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

.ranking-row {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: var(--qb-space-3);
  align-items: center;
  padding: 16px 18px;
  border-radius: 20px;
}

.ranking-index {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: var(--qb-primary-soft-bg);
  color: var(--qb-primary-student);
  font-weight: 700;
}

.ranking-main {
  display: grid;
  gap: 10px;
  min-width: 0;
}

.ranking-title-row span {
  color: var(--qb-text-meta);
  font-size: 12px;
}

.ranking-metrics {
  display: grid;
  gap: 4px;
  justify-items: end;
}

.ranking-metrics strong {
  color: var(--qb-text-heading);
  font-size: 20px;
}

.ranking-metrics small {
  color: var(--qb-text-meta);
}

.ranking-reason {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: var(--qb-radius-pill);
  background: color-mix(in srgb, var(--qb-primary-soft-bg) 72%, white 28%);
  color: var(--qb-primary-student);
  font-size: 11px;
  font-weight: 600;
}

.priority-section {
  background:
    radial-gradient(circle at 12% 18%, rgba(47, 84, 235, 0.08), transparent 28%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(240, 246, 255, 0.96));
}

.priority-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.priority-card {
  display: grid;
  gap: var(--qb-space-3);
  padding: 20px;
  border-radius: 24px;
  border: 1px solid var(--qb-border-glass);
  background: rgba(255, 255, 255, 0.88);
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.05);
  position: relative;
  overflow: hidden;
}

.priority-card::before {
  content: '';
  position: absolute;
  inset: 0 0 auto 0;
  height: 4px;
  background: linear-gradient(90deg, var(--qb-primary-student), color-mix(in srgb, var(--qb-primary-student) 36%, white 64%));
}

.priority-card--risk {
  border-color: color-mix(in srgb, var(--qb-danger) 18%, white);
}

.priority-card--mid {
  border-color: color-mix(in srgb, var(--qb-warning) 18%, white);
}

.priority-card--good {
  border-color: color-mix(in srgb, var(--qb-success) 18%, white);
}

.priority-card--neutral {
  border-color: var(--qb-border-muted);
}

.priority-rank {
  background: var(--qb-primary-soft-bg);
  color: var(--qb-primary-student);
}

.priority-metrics {
  display: grid;
  gap: var(--qb-space-2);
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin: 0;
}

.priority-metrics div {
  display: grid;
  gap: 4px;
  padding: 12px;
  border-radius: var(--qb-radius-md);
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid var(--qb-border-glass);
}

.priority-metrics dt {
  font-size: 12px;
  color: var(--qb-text-meta);
}

.priority-metrics dd {
  margin: 0;
  color: var(--qb-text-heading);
  font-weight: 700;
}

.priority-hint {
  min-height: 44px;
  color: var(--qb-text-secondary);
}

.priority-next-step {
  display: grid;
  gap: 6px;
  padding: 14px 16px;
  border-radius: 16px;
  background: color-mix(in srgb, var(--qb-primary-soft-bg) 62%, white 38%);
  border: 1px solid color-mix(in srgb, var(--qb-primary-student) 10%, white 90%);
}

.priority-next-step span {
  color: var(--qb-text-meta);
  font-size: 12px;
}

.priority-next-step strong {
  font-size: 14px;
  line-height: 1.6;
}

.priority-actions {
  display: flex;
  gap: var(--qb-space-2-5);
  flex-wrap: wrap;
}

.galaxy-board {
  display: grid;
  gap: var(--qb-space-3);
  padding: var(--qb-space-4-5);
  border-radius: var(--qb-radius-2xl);
  background:
    radial-gradient(circle at 18% 22%, rgba(59, 130, 246, 0.06), transparent 24%),
    radial-gradient(circle at 70% 46%, rgba(56, 189, 248, 0.05), transparent 28%),
    linear-gradient(180deg, rgba(250, 252, 255, 0.98) 0%, rgba(242, 247, 255, 0.96) 100%);
  border: 1px solid color-mix(in srgb, var(--qb-border-glass) 72%, white 28%);
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.04);
}

.galaxy-board__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--qb-space-3);
}

.galaxy-board__copy {
  display: grid;
  gap: 6px;
  min-width: 0;
}

.section-eyebrow {
  margin: 0;
  font-size: 11px;
  letter-spacing: 0.04em;
  color: var(--qb-text-meta);
}

.galaxy-board__copy h4 {
  margin: 0;
  font-size: 22px;
}

.galaxy-board__copy p {
  margin: 0;
  color: var(--qb-text-meta);
  line-height: 1.65;
}

.galaxy-toggle {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border: 1px solid var(--qb-border-glass);
  border-radius: var(--qb-radius-pill);
  background: rgba(255, 255, 255, 0.82);
  color: var(--qb-text-secondary-strong);
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: background-color 0.18s ease, border-color 0.18s ease, transform 0.18s ease;
}

.galaxy-toggle:hover {
  background: rgba(255, 255, 255, 0.96);
  border-color: color-mix(in srgb, var(--qb-primary-student) 18%, white);
  transform: translateY(-1px);
}

.galaxy-toggle__chevron {
  display: inline-flex;
  transition: transform 0.18s ease;
}

.galaxy-toggle__chevron--expanded {
  transform: rotate(180deg);
}

.board-pill {
  display: inline-flex;
  align-items: center;
  padding: var(--qb-space-2) var(--qb-space-3);
  border-radius: var(--qb-radius-pill);
  background: var(--qb-surface-glass-soft);
  border: 1px solid var(--qb-border-glass);
  color: var(--qb-text-secondary-strong);
  font-size: 12px;
  font-weight: 600;
}

.board-pill--good,
.overview-pill--good {
  background: color-mix(in srgb, var(--galaxy-good) 14%, white);
  border-color: color-mix(in srgb, var(--galaxy-good) 26%, white);
}

.board-pill--mid,
.overview-pill--mid {
  background: color-mix(in srgb, var(--galaxy-mid) 15%, white);
  border-color: color-mix(in srgb, var(--galaxy-mid) 28%, white);
}

.board-pill--risk,
.overview-pill--risk {
  background: color-mix(in srgb, var(--galaxy-risk) 14%, white);
  border-color: color-mix(in srgb, var(--galaxy-risk) 26%, white);
}

.board-pill--neutral,
.overview-pill--neutral {
  background: color-mix(in srgb, var(--galaxy-neutral) 24%, white);
  border-color: color-mix(in srgb, var(--galaxy-neutral) 48%, white);
}

.galaxy-layout {
  display: grid;
  gap: var(--qb-space-4-5);
  grid-template-columns: minmax(0, 1fr) minmax(300px, 340px);
  align-items: start;
}

.galaxy-collapse-enter-active,
.galaxy-collapse-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
  transform-origin: top center;
}

.galaxy-collapse-enter-from,
.galaxy-collapse-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

.galaxy-card,
.aside-card {
  border-radius: 28px;
  background: var(--galaxy-surface);
  border: 1px solid var(--qb-border-glass);
  box-shadow: 0 16px 36px rgba(15, 23, 42, 0.06);
}

.galaxy-card {
  display: grid;
  gap: var(--qb-space-3);
  padding: var(--qb-space-4-5);
}

.galaxy-card--chart {
  min-width: 0;
  position: relative;
  overflow: hidden;
  background:
    radial-gradient(circle at center, rgba(59, 130, 246, 0.12), transparent 26%),
    linear-gradient(180deg, rgba(250, 252, 255, 0.98), rgba(234, 243, 255, 0.96));
}

.chart-toolbar {
  display: grid;
  gap: var(--qb-space-2);
}

.chart-toolbar-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--qb-space-3);
  flex-wrap: wrap;
}

.chart-toolbar-label {
  color: var(--qb-text-meta);
  font-size: 12px;
  font-weight: 700;
}

.ring-guide,
.legend--inline {
  display: flex;
  gap: var(--qb-space-2);
  flex-wrap: wrap;
}

.ring-chip,
.legend-chip,
.detail-level-chip,
.focus-mode,
.overview-pill,
.path-chip {
  display: inline-flex;
  align-items: center;
  gap: var(--qb-space-2);
  padding: var(--qb-space-2) var(--qb-space-3);
  border-radius: var(--qb-radius-pill);
  font-size: 12px;
  border: 1px solid var(--qb-border-glass);
  background: var(--qb-surface-glass-soft);
}

.ring-chip {
  color: var(--qb-text-secondary-strong);
  font-weight: 600;
}

.ring-chip--subject {
  border-color: color-mix(in srgb, var(--qb-primary-student) 24%, white);
}

.legend-neutral {
  color: var(--qb-text-neutral-ink);
  background: color-mix(in srgb, var(--galaxy-neutral) 24%, white);
}

.legend-risk {
  color: var(--qb-text-danger-strong);
  background: color-mix(in srgb, var(--galaxy-risk) 16%, white);
}

.legend-mid {
  color: var(--qb-text-warning-strong);
  background: color-mix(in srgb, var(--galaxy-mid) 16%, white);
}

.legend-good {
  color: var(--qb-text-success-strong);
  background: color-mix(in srgb, var(--galaxy-good) 18%, white);
}

.stage-shell,
.chart-stage {
  min-height: clamp(360px, 48vw, 520px);
}

.chart-stage {
  width: 100%;
}

.stage-shell {
  position: relative;
  overflow: hidden;
  border-radius: 24px;
  background:
    radial-gradient(circle at center, rgba(59, 130, 246, 0.12), transparent 30%),
    linear-gradient(180deg, rgba(243, 248, 255, 0.8), rgba(230, 240, 255, 0.42));
}

.stage-shell::before,
.stage-shell::after {
  content: '';
  position: absolute;
  border-radius: 999px;
  border: 1px solid rgba(148, 163, 184, 0.16);
  pointer-events: none;
}

.stage-shell::before {
  inset: 14% 16%;
}

.stage-shell::after {
  inset: 28% 30%;
}

.galaxy-aside {
  display: grid;
  gap: var(--qb-space-3);
  align-content: start;
}

.aside-card {
  display: grid;
  gap: var(--qb-space-3);
  padding: var(--qb-space-4-5);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(241, 246, 255, 0.94));
}

.aside-head {
  display: flex;
  justify-content: space-between;
  gap: var(--qb-space-2-5);
  align-items: center;
}

.aside-label {
  font-size: 12px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--qb-text-meta);
}

.focus-mode,
.detail-level-chip,
.overview-pill {
  color: var(--qb-text-secondary-strong);
  font-weight: 600;
}

.detail-card {
  gap: var(--qb-space-4);
}

.detail-title-row {
  display: flex;
  justify-content: space-between;
  gap: var(--qb-space-3);
  align-items: flex-start;
}

.detail-title-copy {
  display: grid;
  gap: 6px;
}

.detail-title-copy strong,
.detail-empty strong {
  font-size: 20px;
  color: var(--qb-text-heading);
}

.detail-title-copy p,
.detail-empty p {
  margin: 0;
  color: var(--qb-text-meta);
  line-height: 1.65;
}

.detail-path {
  display: grid;
  gap: var(--qb-space-2);
}

.path-label {
  font-size: 12px;
  color: var(--qb-text-meta);
}

.path-chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: var(--qb-space-2);
}

.path-chip {
  color: var(--qb-text-secondary-strong);
}

.detail-metrics,
.focus-stats {
  display: grid;
  gap: var(--qb-space-2-5);
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin: 0;
}

.detail-metrics div,
.focus-stats div {
  display: grid;
  gap: var(--qb-space-1);
  padding: var(--qb-space-3);
  border-radius: var(--qb-radius-md);
  background: rgba(255, 255, 255, 0.72);
}

.detail-metrics dt,
.focus-stats dt {
  font-size: 12px;
  color: var(--qb-text-meta);
}

.detail-metrics dd,
.focus-stats dd {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: var(--qb-text-heading);
}

.detail-actions {
  display: flex;
  gap: var(--qb-space-2-5);
  flex-wrap: wrap;
}

.detail-empty {
  display: grid;
  gap: var(--qb-space-2);
  min-height: 160px;
  align-content: center;
  justify-items: start;
}

@media (max-width: 1180px) {
  .module-overview-layout,
  .module-highlight-grid,
  .chapter-panel-grid,
  .priority-grid,
  .galaxy-layout {
    grid-template-columns: 1fr;
  }

  .chart-stage,
  .stage-shell {
    min-height: clamp(340px, 54vw, 460px);
  }
}

@media (max-width: 960px) {
  .hero-main-row,
  .galaxy-board__head {
    display: grid;
  }

  .section-head,
  .chapter-collapse-title,
  .chapter-card-head,
  .ranking-row,
  .priority-card-head {
    display: grid;
  }

  .ranking-collapsed {
    display: grid;
  }

  .ranking-collapsed__action,
  .ranking-toggle {
    justify-content: center;
  }

  .summary-stat-strip,
  .chapter-panel-stats,
  .priority-metrics,
  .hero-summary-strip {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .chapter-grid {
    grid-template-columns: 1fr;
  }

}

@media (max-width: 640px) {
  .analysis-page {
    gap: var(--qb-space-3-5);
  }

  .hero-card,
  .summary-card,
  .priority-section,
  .galaxy-board,
  .galaxy-card,
  .aside-card {
    padding: var(--qb-space-4);
  }

  .summary-stat-strip,
  .chapter-panel-stats,
  .priority-metrics,
  .detail-metrics,
  .focus-stats,
  .hero-summary-strip {
    grid-template-columns: 1fr;
  }

  .module-overview-actions,
  .chapter-collapse-metrics,
  .priority-actions {
    justify-content: stretch;
  }

  .detail-title-row {
    display: grid;
  }

  .chart-stage,
  .stage-shell {
    min-height: 320px;
  }

  .analysis-empty-panel__actions {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
