<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import StudentSubjectDrawer from '../../components/student/StudentSubjectDrawer.vue'
import StudentHeroBanner from '../../components/student/StudentHeroBanner.vue'
import { fetchAnalyticsSummary, fetchStudentDashboard } from '../../api/services/student.js'
import { knowledgeTreeV2 } from '../../api/services/questionBank.js'
import { useUserStore } from '../../stores/userStore.js'
import { useSubjectContextStore } from '../../stores/subjectContextStore.js'
import { buildContentLabelMaps, resolveContentLabel } from '../../utils/contentBaseline.js'
import { buildKnowledgeGraphIndex } from '../../utils/knowledgeTree.js'
import { buildSubjectMetaById, computeSubjectMastery, normalizeMasteryScore } from '../../utils/studentMastery.js'
import {
  buildStudentPracticeRouteLocation,
  STUDENT_PRACTICE_MODULE,
  STUDENT_PRACTICE_SOURCE,
} from '../../utils/studentPracticeNavigation.js'
import {
  buildFocusedUrgentKnowledgeSuggestion,
  buildReferenceMastery,
  buildTodayExecutionRecommendation,
  clampPercent,
  derivePredictedScore,
  resolveDailyMotivationalQuote,
  normalizeKnowledgeMastery,
} from '../../utils/studentHomeViewModel.js'

const route = useRoute()
const userStore = useUserStore()
const subjectContextStore = useSubjectContextStore()
const router = useRouter()

const loading = ref(true)
const masteryRows = ref([])
const dashboardPayload = ref({})
const baselinePayload = ref({})
const subjectKnowledgeMetrics = ref([])
const subjectInsightsRetrying = ref(false)
const subjectInsightLoadError = ref('')
const subjectDrawerVisible = ref(false)
const activeSubjectCode = ref('')
let subjectInsightBatchToken = 0
let subjectInsightBackgroundTimer = 0

function resolveSubjectAccent(subjectCode, index = 0) {
  const normalizedCode = String(subjectCode || '').trim().toUpperCase()
  if (normalizedCode.includes('POLIT') || normalizedCode.includes('政治')) {
    return 'var(--qb-subject-politics)'
  }
  if (normalizedCode.includes('ENGLISH') || normalizedCode.includes('英语')) {
    return 'var(--qb-subject-english)'
  }
  if (normalizedCode.includes('MATH') || normalizedCode.includes('数学') || normalizedCode.includes('高数')) {
    return 'var(--qb-subject-math)'
  }
  if (normalizedCode.includes('CHINESE') || normalizedCode.includes('语文')) {
    return 'var(--qb-subject-chinese)'
  }
  if (normalizedCode.includes('COMPUTER') || normalizedCode.includes('计算机')) {
    return 'var(--qb-subject-computer)'
  }
  const fallbackPalette = [
    'var(--qb-subject-fallback-1)',
    'var(--qb-subject-fallback-2)',
    'var(--qb-subject-fallback-3)',
    'var(--qb-subject-fallback-4)',
    'var(--qb-subject-fallback-5)',
    'var(--qb-subject-fallback-6)',
  ]
  return fallbackPalette[index % fallbackPalette.length]
}

function buildHomeFallbackPayload() {
  const fallbackSubjectRows = (Array.isArray(subjectContextStore.subjectOptions) ? subjectContextStore.subjectOptions : [])
    .map((item) => ({
      subjectCode: String(item?.subjectCode || '').trim(),
      subjectId: String(item?.subjectId || item?.subjectCode || '').trim(),
      subjectName: String(item?.subjectName || item?.subjectCode || '').trim(),
      subjectType: String(item?.subjectType || '').trim(),
      progress: {
        answered: 0,
        total: 0,
        accuracy: 0,
      },
    }))
    .filter((item) => Boolean(item.subjectCode))

  const availableExamCategories = Array.isArray(userStore.availableExamCategories)
    ? userStore.availableExamCategories
    : []
  const scopeMaps = buildContentLabelMaps(availableExamCategories)
  const examCategoryCode = String(userStore.examCategoryCode || '').trim()
  const jointExamGroupCode = String(userStore.assignedJointGroupCode || userStore.jointExamGroupCode || '').trim()

  return {
    examCategoryCode,
    jointExamGroupCode,
    examCategoryName: resolveContentLabel(scopeMaps.examCategoryNameMap, examCategoryCode, ''),
    jointExamGroupName: resolveContentLabel(scopeMaps.jointExamGroupNameMap, jointExamGroupCode, ''),
    availableExamCategories,
    coreSubjects: fallbackSubjectRows,
    points: 0,
    title: '备考新星',
    streakDays: 0,
    dailyTasks: [],
    aiQuota: {
      dailyLimit: 0,
      usedCount: 0,
    },
    challengePointSubjects: [],
    recentPointsLedger: [],
    unlockedTitles: [],
    personalBankCount: 0,
    messageUnreadCount: 0,
    examSession: {},
    studentState: {
      checkInDone: false,
      streakDays: 0,
      dailyTasks: [],
      challengePointSubjects: [],
    },
    chapterPracticeTree: [],
  }
}

function applyDashboardPayload(dashboard) {
  const fallbackPayload = buildHomeFallbackPayload()
  const normalizedDashboard = dashboard && typeof dashboard === 'object' ? dashboard : {}
  const availableExamCategories = Array.isArray(normalizedDashboard.availableExamCategories) && normalizedDashboard.availableExamCategories.length
    ? normalizedDashboard.availableExamCategories
    : fallbackPayload.availableExamCategories
  const coreSubjects = Array.isArray(normalizedDashboard.coreSubjects) && normalizedDashboard.coreSubjects.length
    ? normalizedDashboard.coreSubjects
    : fallbackPayload.coreSubjects

  dashboardPayload.value = {
    ...fallbackPayload,
    ...normalizedDashboard,
    availableExamCategories,
    coreSubjects,
    dailyTasks: Array.isArray(normalizedDashboard.dailyTasks) ? normalizedDashboard.dailyTasks : fallbackPayload.dailyTasks,
    challengePointSubjects: Array.isArray(normalizedDashboard.challengePointSubjects)
      ? normalizedDashboard.challengePointSubjects
      : fallbackPayload.challengePointSubjects,
    recentPointsLedger: Array.isArray(normalizedDashboard.recentPointsLedger)
      ? normalizedDashboard.recentPointsLedger
      : fallbackPayload.recentPointsLedger,
    unlockedTitles: Array.isArray(normalizedDashboard.unlockedTitles)
      ? normalizedDashboard.unlockedTitles
      : fallbackPayload.unlockedTitles,
    chapterPracticeTree: Array.isArray(normalizedDashboard.chapterPracticeTree)
      ? normalizedDashboard.chapterPracticeTree
      : fallbackPayload.chapterPracticeTree,
    studentState: {
      ...fallbackPayload.studentState,
      ...(normalizedDashboard.studentState && typeof normalizedDashboard.studentState === 'object'
        ? normalizedDashboard.studentState
        : {}),
    },
    aiQuota: {
      ...fallbackPayload.aiQuota,
      ...(normalizedDashboard.aiQuota && typeof normalizedDashboard.aiQuota === 'object'
        ? normalizedDashboard.aiQuota
        : {}),
    },
    examSession: normalizedDashboard.examSession && typeof normalizedDashboard.examSession === 'object'
      ? normalizedDashboard.examSession
      : fallbackPayload.examSession,
  }

  baselinePayload.value = {
    examCategories: Array.isArray(availableExamCategories) ? availableExamCategories : [],
  }

  if (coreSubjects.length) {
    subjectContextStore.setSubjectOptions(
      { coreSubjects },
      String(route.query.subjectCode || subjectContextStore.currentSubjectCode || activeSubjectCode.value || '').trim(),
    )
  }
}

const scopeLabelMaps = computed(() => buildContentLabelMaps(
  Array.isArray(baselinePayload.value?.examCategories) && baselinePayload.value.examCategories.length
    ? baselinePayload.value
    : userStore.availableExamCategories,
))

const referenceGroupLabel = computed(() => {
  const jointExamGroupCode = String(
    userStore.assignedJointGroupCode || userStore.jointExamGroupCode || dashboardPayload.value?.jointExamGroupCode || '',
  ).trim()
  return resolveContentLabel(scopeLabelMaps.value.jointExamGroupNameMap, jointExamGroupCode, '当前专业组')
})

const currentDateLabel = computed(() => (
  new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  }).format(new Date())
))

const allowedSubjectCodes = computed(() => {
  const jointExamGroupCode = String(userStore.assignedJointGroupCode || userStore.jointExamGroupCode || '').trim()
  const examCategories = Array.isArray(baselinePayload.value?.examCategories) ? baselinePayload.value.examCategories : []
  const codes = new Set()

  examCategories.forEach((examCategoryItem) => {
    const jointExamGroups = Array.isArray(examCategoryItem?.jointExamGroups) ? examCategoryItem.jointExamGroups : []
    jointExamGroups.forEach((groupItem) => {
      if (jointExamGroupCode && String(groupItem?.jointExamGroupCode || '').trim() !== jointExamGroupCode) {
        return
      }
      const subjects = Array.isArray(groupItem?.subjects) ? groupItem.subjects : []
      subjects.forEach((subjectItem) => {
        const subjectCode = String(subjectItem?.subjectCode || '').trim()
        if (subjectCode) {
          codes.add(subjectCode)
        }
      })
    })
  })

  return codes
})

const scopedCoreSubjects = computed(() => {
  const coreSubjects = Array.isArray(dashboardPayload.value?.coreSubjects) ? dashboardPayload.value.coreSubjects : []
  if (!allowedSubjectCodes.value.size) {
    return coreSubjects
  }
  return coreSubjects.filter((item) => allowedSubjectCodes.value.has(String(item?.subjectCode || '').trim()))
})

const scopedSubjectMetaById = computed(() => buildSubjectMetaById(scopedCoreSubjects.value))

const masteryRowsBySubjectId = computed(() => (
  new Map(
    masteryRows.value.map((row) => [String(row?.subjectId || '').trim(), row]).filter(([subjectId]) => Boolean(subjectId)),
  )
))

const scopedMasteryRows = computed(() => {
  const allowedSubjectIds = new Set(
    scopedCoreSubjects.value.map((item) => String(item?.subjectId || '').trim()).filter(Boolean),
  )
  if (!allowedSubjectIds.size) {
    return masteryRows.value
  }
  return masteryRows.value.filter((row) => allowedSubjectIds.has(String(row?.subjectId || '').trim()))
})

const hasPersonalMastery = computed(() => scopedMasteryRows.value.length > 0)

const masteryOverview = computed(() => {
  if (!scopedMasteryRows.value.length) {
    return {
      averageMastery: 0,
      averageAccuracy: 0,
      averageSpeed: 0,
      averageFrequency: 0,
    }
  }

  const subjectCount = scopedMasteryRows.value.length
  const totals = scopedMasteryRows.value.reduce(
    (accumulator, row) => ({
      averageMastery: accumulator.averageMastery + computeSubjectMastery(row),
      averageAccuracy: accumulator.averageAccuracy + normalizeMasteryScore(row?.accuracy),
      averageSpeed: accumulator.averageSpeed + normalizeMasteryScore(row?.speed),
      averageFrequency: accumulator.averageFrequency + normalizeMasteryScore(row?.frequency),
    }),
    {
      averageMastery: 0,
      averageAccuracy: 0,
      averageSpeed: 0,
      averageFrequency: 0,
    },
  )

  return {
    averageMastery: Math.round(totals.averageMastery / subjectCount),
    averageAccuracy: Math.round(totals.averageAccuracy / subjectCount),
    averageSpeed: Math.round(totals.averageSpeed / subjectCount),
    averageFrequency: Math.round(totals.averageFrequency / subjectCount),
  }
})

const subjectKnowledgeMetricsMap = computed(() => (
  Object.fromEntries(subjectKnowledgeMetrics.value.map((item) => [item.subjectCode, item]))
))

const readySubjectKnowledgeMetrics = computed(() => (
  subjectKnowledgeMetrics.value.filter((item) => String(item?.status || 'ready').trim() === 'ready')
))

const subjectKnowledgeMetricErrorCount = computed(() => (
  subjectKnowledgeMetrics.value.filter((item) => String(item?.status || '').trim() === 'error').length
))

const subjectKnowledgeMetricLoadingCount = computed(() => (
  subjectKnowledgeMetrics.value.filter((item) => String(item?.status || '').trim() === 'loading').length
))

const subjectKnowledgeMetricIdleCount = computed(() => (
  subjectKnowledgeMetrics.value.filter((item) => ['idle', 'queued', ''].includes(String(item?.status || '').trim())).length
))

const overallCoverage = computed(() => {
  const total = readySubjectKnowledgeMetrics.value.reduce((sum, item) => sum + Number(item?.l5Total || 0), 0)
  const covered = readySubjectKnowledgeMetrics.value.reduce((sum, item) => sum + Number(item?.l5Covered || 0), 0)
  const percent = total ? Math.round((covered / total) * 100) : 0
  const targetSubjectCount = subjectKnowledgeMetrics.value.length
  const readySubjectCount = readySubjectKnowledgeMetrics.value.length
  const pendingSubjectCount = subjectKnowledgeMetricLoadingCount.value + subjectKnowledgeMetricIdleCount.value
  const status = targetSubjectCount === 0
    ? 'empty'
    : pendingSubjectCount > 0
      ? 'syncing'
      : readySubjectCount > 0
        ? (subjectKnowledgeMetricErrorCount.value > 0 ? 'partial' : 'ready')
        : (subjectKnowledgeMetricErrorCount.value > 0 ? 'unavailable' : 'empty')
  return {
    total,
    covered,
    percent,
    status,
    targetSubjectCount,
    readySubjectCount,
    pendingSubjectCount,
    failedSubjectCount: subjectKnowledgeMetricErrorCount.value,
  }
})

const subjectInsightNotice = computed(() => {
  if (!subjectInsightLoadError.value) {
    return null
  }
  if (overallCoverage.value.status === 'partial') {
    return {
      tone: 'warning',
      title: '部分科目学情摘要暂未同步',
      description: subjectInsightLoadError.value,
    }
  }
  return {
    tone: 'error',
    title: '首页学情摘要暂不可用',
    description: subjectInsightLoadError.value,
  }
})

const predictedScore = computed(() => {
  const backendScore = Number(
    dashboardPayload.value?.predictedScore
    || dashboardPayload.value?.predictionScore
    || dashboardPayload.value?.forecastScore
    || 0,
  )

  return derivePredictedScore({
    backendScore,
    hasPersonalMastery: hasPersonalMastery.value,
    averageMastery: masteryOverview.value.averageMastery,
    averageAccuracy: masteryOverview.value.averageAccuracy,
    coveragePercent: overallCoverage.value.status === 'ready' ? overallCoverage.value.percent : 0,
  })
})

const predictedScoreBand = computed(() => {
  if (predictedScore.value >= 250) {
    return {
      label: '冲刺区',
      description: '基本盘稳定，接下来把时间留给高权重薄弱点和解题速度。',
      tone: 'strong',
    }
  }
  if (predictedScore.value >= 220) {
    return {
      label: '提升区',
      description: '当前最适合集中补强 L5 断点，覆盖率和正确率会一起抬升。',
      tone: 'steady',
    }
  }
  return {
    label: '补基区',
    description: '先把基础考点打穿，再逐步拉速度，分数会更稳地向上走。',
    tone: 'focus',
  }
})

const dailyTaskRows = computed(() => {
  const studentStateTasks = dashboardPayload.value?.studentState?.dailyTasks
  if (Array.isArray(studentStateTasks)) {
    return studentStateTasks
  }
  return Array.isArray(dashboardPayload.value?.dailyTasks) ? dashboardPayload.value?.dailyTasks : []
})

const completedDailyTaskCount = computed(() =>
  dailyTaskRows.value.filter((taskItem) => Boolean(taskItem?.isDone)).length,
)

const totalDailyTaskCount = computed(() => dailyTaskRows.value.length)
const nextDailyTask = computed(() =>
  dailyTaskRows.value.find((taskItem) => !taskItem?.isDone) || dailyTaskRows.value[0] || null,
)

const checkInDone = computed(() => Boolean(dashboardPayload.value?.studentState?.checkInDone))

const streakDays = computed(() =>
  Number(dashboardPayload.value?.studentState?.streakDays || dashboardPayload.value?.streakDays || 0),
)

const chapterPracticeTree = computed(() => {
  const sourceRows = Array.isArray(dashboardPayload.value?.chapterPracticeTree)
    ? dashboardPayload.value.chapterPracticeTree
    : []
  const subjectMetaMap = new Map(
    scopedCoreSubjects.value.map((item) => [
      String(item?.subjectId || '').trim(),
      {
        subjectCode: String(item?.subjectCode || '').trim(),
        subjectName: String(item?.subjectName || item?.subjectCode || '').trim(),
      },
    ]),
  )

  return sourceRows
    .map((subjectRow) => {
      const subjectId = String(subjectRow?.subjectId || '').trim()
      const subjectMeta = subjectMetaMap.get(subjectId) || {}
      return {
        ...subjectRow,
        subjectId,
        subjectCode: String(subjectMeta.subjectCode || '').trim(),
        subjectName: String(subjectMeta.subjectName || subjectRow?.subjectName || subjectId).trim(),
      }
    })
    .filter((subjectRow) => {
      if (!allowedSubjectCodes.value.size) {
        return true
      }
      const subjectCode = String(subjectRow?.subjectCode || '').trim()
      return !subjectCode || allowedSubjectCodes.value.has(subjectCode)
    })
})

const chapterTargetsBySubjectCode = computed(() => (
  Object.fromEntries(
    chapterPracticeTree.value
      .map((subjectRow) => {
        const chapters = Array.isArray(subjectRow?.chapters) ? subjectRow.chapters : []
        const targetChapter = chapters.find((item) => item?.isCurrent)
          || chapters.find((item) => item?.isUnlocked)
          || chapters[0]
        if (!targetChapter) {
          return null
        }
        return [
          String(subjectRow?.subjectCode || '').trim(),
          {
            subjectCode: String(subjectRow?.subjectCode || '').trim(),
            subjectName: String(subjectRow?.subjectName || subjectRow?.subjectCode || '').trim(),
            chapterName: String(targetChapter?.chapter || '').trim(),
            chapterCount: Number(subjectRow?.chapterCount || chapters.length || 0),
            unlockedChapterCount: Number(
              subjectRow?.unlockedChapterCount
              || chapters.filter((item) => item?.isUnlocked).length
              || 0,
            ),
            statusLabel: String(targetChapter?.statusLabel || '').trim(),
          },
        ]
      })
      .filter(Boolean),
  )
))

const subjectCards = computed(() => (
  scopedCoreSubjects.value.map((subjectItem, index) => {
    const subjectCode = String(subjectItem?.subjectCode || '').trim()
    const subjectId = String(subjectItem?.subjectId || '').trim()
    const masteryRow = masteryRowsBySubjectId.value.get(subjectId)
    const insight = subjectKnowledgeMetricsMap.value[subjectCode] || {}
    const insightStatus = String(insight?.status || '').trim() || 'empty'
    const hasInsight = insightStatus === 'ready'
    const isLoadingInsight = insightStatus === 'loading'
    const isIdleInsight = insightStatus === 'idle' || insightStatus === 'queued' || insightStatus === 'empty'
    const mastery = masteryRow ? computeSubjectMastery(masteryRow) : 0
    const label = String(subjectItem?.subjectName || subjectCode || `科目 ${index + 1}`).trim()
    const coverage = hasInsight ? clampPercent(insight?.coverage || 0) : null
    const weakNodes = hasInsight
      ? (Array.isArray(insight?.weakNodes) ? insight.weakNodes : []).map((nodeItem) => ({
        ...nodeItem,
        subjectCode,
        subjectName: label,
      }))
      : []
    return {
      subjectCode,
      subjectId,
      subjectName: label,
      mastery,
      coverage,
      l5Total: Number(insight?.l5Total || 0),
      l5Covered: Number(insight?.l5Covered || 0),
      badge: label.replace(/\s+/g, '').slice(0, 2) || `${index + 1}`,
      accent: resolveSubjectAccent(subjectCode, index),
      weakNodes,
      hasInsight,
      insightStatus,
      coverageLabel: hasInsight
        ? `${coverage}% 覆盖`
        : (isLoadingInsight ? '学情摘要同步中' : (isIdleInsight ? '待同步学情摘要' : '学情摘要暂不可用')),
      insightSummary: hasInsight
        ? (weakNodes[0]?.label
          ? `优先补 ${weakNodes[0].label}`
          : `已覆盖 ${Number(insight?.l5Covered || 0)}/${Number(insight?.l5Total || 0)} 个考点`)
        : (isLoadingInsight ? '正在补齐这门科目的覆盖率和薄弱点。' : (isIdleInsight ? '点击后优先同步这门科目的学情摘要。' : '知识树同步失败，请稍后重试')),
      chapterTarget: chapterTargetsBySubjectCode.value[subjectCode] || null,
    }
  })
))

const activeSubjectCard = computed(() => (
  subjectCards.value.find((item) => item.subjectCode === activeSubjectCode.value) || subjectCards.value[0] || null
))

const currentFocusSubjectCode = computed(() => (
  String(route.query.subjectCode || subjectContextStore.currentSubjectCode || activeSubjectCode.value || '').trim()
))

const currentFocusSubject = computed(() => (
  subjectCards.value.find((item) => item.subjectCode === currentFocusSubjectCode.value) || activeSubjectCard.value || null
))

const effectiveCurrentFocusSubjectCode = computed(() => (
  String(currentFocusSubject.value?.subjectCode || currentFocusSubjectCode.value || '').trim()
))

const referenceRadarRows = computed(() => {
  if (hasPersonalMastery.value) {
    return []
  }

  return scopedCoreSubjects.value.map((subjectItem, index) => {
    const subjectCode = String(subjectItem?.subjectCode || '').trim()
    const subjectId = String(subjectItem?.subjectId || subjectCode || `subject-${index}`).trim()
    const insight = subjectKnowledgeMetricsMap.value[subjectCode] || {}
    const referenceMastery = clampPercent(
      Number(insight?.averageMastery || 0) > 0
        ? Math.min(76, Number(insight.averageMastery || 0) + 8)
        : buildReferenceMastery(subjectItem, index),
    )
    const normalized = referenceMastery / 100
    return {
      subjectId,
      subjectCode,
      accuracy: normalized,
      speed: normalized,
      frequency: normalized,
    }
  })
})

const weakKnowledgeCandidates = computed(() => (
  readySubjectKnowledgeMetrics.value
    .flatMap((subjectItem) => (Array.isArray(subjectItem?.weakNodes) ? subjectItem.weakNodes : []).map((nodeItem) => ({
      ...nodeItem,
      subjectCode: subjectItem.subjectCode,
      subjectName: subjectItem.subjectName,
      subjectCoverage: subjectItem.coverage,
    })))
    .sort((left, right) => {
      if (left.mastery !== right.mastery) {
        return left.mastery - right.mastery
      }
      if (left.questionCount !== right.questionCount) {
        return right.questionCount - left.questionCount
      }
      return String(left.label || '').localeCompare(String(right.label || ''), 'zh-Hans-CN')
    })
))

const currentFocusUrgentKnowledgeSuggestion = computed(() => buildFocusedUrgentKnowledgeSuggestion({
  weakKnowledgeCandidates: weakKnowledgeCandidates.value,
  currentSubjectCode: effectiveCurrentFocusSubjectCode.value,
  referenceGroupLabel: referenceGroupLabel.value,
}))

const currentFocusChapterTarget = computed(() => {
  const subjectCode = effectiveCurrentFocusSubjectCode.value
  if (!subjectCode) {
    return null
  }
  return chapterTargetsBySubjectCode.value[subjectCode] || null
})

const todayExecutionRecommendation = computed(() => buildTodayExecutionRecommendation({
  checkInDone: checkInDone.value,
  streakDays: streakDays.value,
  nextDailyTask: nextDailyTask.value,
  urgentKnowledgeSuggestion: currentFocusUrgentKnowledgeSuggestion.value,
  dailyCompletionPercent: totalDailyTaskCount.value
    ? Math.round((completedDailyTaskCount.value / totalDailyTaskCount.value) * 100)
    : 0,
  currentSubjectName: currentFocusSubject.value?.subjectName || currentFocusChapterTarget.value?.subjectName || '当前科目',
}))

const todayNorthStarQuote = computed(() => {
  return resolveDailyMotivationalQuote(new Date())
})

const todayNorthStarTitle = computed(() => {
  return todayExecutionRecommendation.value.title
})

const todayNorthStarCopy = computed(() => {
  return todayExecutionRecommendation.value.description
})

const todayTaskEntryValue = computed(() => {
  const taskName = String(nextDailyTask.value?.taskName || '').trim()
  const actionLabel = String(
    todayExecutionRecommendation.value.actionLabel || nextDailyTask.value?.actionLabel || '',
  ).trim()

  return taskName || actionLabel || '查看今日安排'
})

const todayTaskEntryHelper = computed(() => {
  const description = String(todayExecutionRecommendation.value.description || '').trim()
  if (description) {
    return `今天需要做什么：${description}`
  }

  const actionLabel = String(nextDailyTask.value?.actionLabel || '').trim()
  if (actionLabel) {
    return `今天需要做什么：${actionLabel}`
  }

  const taskName = String(nextDailyTask.value?.taskName || '').trim()
  if (taskName) {
    return `今天需要做什么：完成「${taskName}」`
  }

  return '今天需要做什么：进入任务区查看今天的安排'
})

const onboardingSnapshot = computed(() => {
  const raw = dashboardPayload.value?.onboarding
  return raw && typeof raw === 'object' ? raw : {}
})

const subscriptionActive = computed(() => Boolean(onboardingSnapshot.value?.subscriptionActive))

const onboardingQuickDiagnosisCompleted = computed(() => (
  Boolean(onboardingSnapshot.value?.quickDiagnosisCompleted)
))

const homeSubscriptionCard = computed(() => {
  if (subscriptionActive.value) {
    return {
      tone: 'active',
      badge: '权益已生效',
      title: 'AI 提分权益已开通',
      description: '你已处于订阅生效状态，建议直接进入今日任务，把开通价值转成稳定提分输出。',
      detail: '订阅状态 ACTIVE · 可以直接使用 AI 提分能力',
      primaryActionLabel: '进入今日任务',
      secondaryActionLabel: '查看权益状态',
      primaryAction: 'tasks',
      secondaryAction: 'subscriptionStatus',
    }
  }
  if (onboardingQuickDiagnosisCompleted.value) {
    return {
      tone: 'pending',
      badge: '待完成开通',
      title: '快诊已完成，还差一步开通',
      description: '你已拿到诊断建议，建议现在完成兑换或模拟支付，确保首日学习链路不断档。',
      detail: '当前未开通订阅权益 · 建议立即进入开通页',
      primaryActionLabel: '去开通权益',
      secondaryActionLabel: '重做快诊',
      primaryAction: 'checkout',
      secondaryAction: 'diagnosis',
    }
  }
  return {
    tone: 'guide',
    badge: '首登引导',
    title: '先完成 AI 快诊再开通',
    description: '建议先做 3-5 题快诊，系统会给出当前短板和开通建议，然后再进入权益开通。',
    detail: '当前尚未完成快诊 · 建议先进入引导页',
    primaryActionLabel: '去做快诊',
    secondaryActionLabel: '去开通页',
    primaryAction: 'diagnosis',
    secondaryAction: 'checkout',
  }
})

const recommendedPracticeModuleTitle = computed(() => {
  const moduleKey = resolveRecommendedPracticeModuleKey()
  if (moduleKey === STUDENT_PRACTICE_MODULE.MOCK) {
    return '模拟考试'
  }
  if (moduleKey === STUDENT_PRACTICE_MODULE.FREE) {
    return '自由练习'
  }
  return '章节闯关'
})

const overviewPulseCards = computed(() => ([
  {
    label: '当前科目',
    value: currentFocusSubject.value?.subjectName || '跟随全局切换',
    helper: currentFocusSubject.value
      ? currentFocusSubject.value.coverageLabel
      : '切换科目后自动同步',
  },
  {
    label: '学习连续达成',
    value: `${streakDays.value} 天`,
    helper: checkInDone.value ? '今日已完成打卡' : '待完成今日打卡',
  },
  {
    label: '今日执行',
    value: todayTaskEntryValue.value,
    helper: checkInDone.value
      ? `优先从「${recommendedPracticeModuleTitle.value}」进入，${todayTaskEntryHelper.value.replace(/^今天需要做什么：/, '')}`
      : todayTaskEntryHelper.value,
  },
  {
    label: 'AI权益',
    value: subscriptionActive.value ? '已开通' : '未开通',
    helper: subscriptionActive.value
      ? '当前可直接使用提分权益'
      : (onboardingQuickDiagnosisCompleted.value ? '快诊已完成，建议立即开通' : '建议先完成快诊再开通'),
  },
]))

const currentFocusChallengePoints = computed(() => {
  const rows = Array.isArray(dashboardPayload.value?.challengePointSubjects)
    ? dashboardPayload.value.challengePointSubjects
    : Array.isArray(dashboardPayload.value?.studentState?.challengePointSubjects)
      ? dashboardPayload.value.studentState.challengePointSubjects
      : []
  return rows.find((item) => String(item?.subjectCode || '').trim() === effectiveCurrentFocusSubjectCode.value) || {
    total: 0,
    todayDelta: 0,
    correctSubmitCount: 0,
    todayCorrectSubmitCount: 0,
    rank: 0,
    awardUnlocked: false,
    awardProgress: 0,
    awardThreshold: 3000,
    scoreCap: 3000,
    cappedTotal: 0,
    scorePercent: 0,
    levelName: '刷题青铜',
    nextLevelName: '刷题白银',
    pointsToNextLevel: 200,
    isTopLevel: false,
  }
})

const homeChallengeSummaryCopy = computed(() => {
  const challengePoints = currentFocusChallengePoints.value || {}
  const total = Number(challengePoints.total || 0)
  const correctSubmitCount = Number(challengePoints.correctSubmitCount || total || 0)
  const levelName = String(challengePoints.levelName || '刷题青铜').trim() || '刷题青铜'
  const nextLevelName = String(challengePoints.nextLevelName || '').trim()
  const pointsToNextLevel = Number(challengePoints.pointsToNextLevel || 0)

  if (nextLevelName) {
    return `当前累计段位分 ${total}，累计答对题次 ${correctSubmitCount}。这不是装饰分，而是在记录你把题真正做对了多少次。再积 ${pointsToNextLevel} 分到「${nextLevelName}」，说明你正在把这门课从“会一点”练成“考试能稳定拿分”。`
  }

  return `当前累计段位分 ${total}，累计答对题次 ${correctSubmitCount}。你已经来到「${levelName}」满阶，这代表这门课已经形成了高密度的稳定正确输出，接下来更关键的是把这种状态一直带到考场。`
})

const homeChallengeMomentumCopy = computed(() => {
  const challengePoints = currentFocusChallengePoints.value || {}
  if (Number(challengePoints.rank || 0) > 0) {
    return `当前同科目排名 #${Number(challengePoints.rank || 0)}，段位已到「${String(challengePoints.levelName || '刷题青铜').trim() || '刷题青铜'}」。`
  }
  if (String(challengePoints.nextLevelName || '').trim()) {
    return `当前段位是「${String(challengePoints.levelName || '刷题青铜').trim() || '刷题青铜'}」，建议从「${recommendedPracticeModuleTitle.value}」继续刷题冲分，先把下一段位拿下来。`
  }
  return `当前段位已封顶，建议继续从「${recommendedPracticeModuleTitle.value}」保持节奏，把高段位转成稳定的升本得分能力。`
})

function resolveRecommendedPracticeModuleKey() {
  const taskSignals = [
    String(nextDailyTask.value?.taskName || '').trim(),
    String(nextDailyTask.value?.actionLabel || '').trim(),
    String(todayExecutionRecommendation.value?.actionLabel || '').trim(),
    String(todayExecutionRecommendation.value?.title || '').trim(),
  ].join(' ')

  if (taskSignals.includes('模拟考试')) {
    return STUDENT_PRACTICE_MODULE.MOCK
  }
  if (taskSignals.includes('自由练习')) {
    return STUDENT_PRACTICE_MODULE.FREE
  }
  if (taskSignals.includes('章节闯关')) {
    return STUDENT_PRACTICE_MODULE.CHAPTER
  }
  if (todayExecutionRecommendation.value?.kind === 'weakness') {
    return STUDENT_PRACTICE_MODULE.FREE
  }
  if (predictedScoreBand.value.label === '冲刺区') {
    return STUDENT_PRACTICE_MODULE.MOCK
  }
  if (predictedScoreBand.value.label === '提升区') {
    return STUDENT_PRACTICE_MODULE.FREE
  }
  return STUDENT_PRACTICE_MODULE.CHAPTER
}

const practiceModuleQuickActions = computed(() => {
  const recommendedKey = resolveRecommendedPracticeModuleKey()
  return [
    {
      key: STUDENT_PRACTICE_MODULE.CHAPTER,
      title: '章节闯关',
      description: currentFocusChapterTarget.value?.chapterName
        ? `从「${currentFocusChapterTarget.value.chapterName}」继续推进，最适合沿当前主线把基础打透。`
        : '按章节解锁推进，适合沿着当前主线稳步过章。',
    },
    {
      key: STUDENT_PRACTICE_MODULE.FREE,
      title: '自由练习',
      description: currentFocusUrgentKnowledgeSuggestion.value?.target?.label
        ? `围绕「${currentFocusUrgentKnowledgeSuggestion.value.target.label}」快速连刷，适合补弱和二次巩固。`
        : '只保留答题主界面，适合围绕当前科目快速连续刷题。',
    },
    {
      key: STUDENT_PRACTICE_MODULE.MOCK,
      title: '模拟考试',
      description: predictedScoreBand.value.label === '冲刺区'
        ? '整卷演练和时间控制都在这里，适合考前做完整校验。'
        : '推荐试卷与手动选卷并存，需要整卷查漏时可以直接进入。',
    },
  ].map((item) => {
    const isRecommended = item.key === recommendedKey
    return {
      ...item,
      isRecommended,
      badge: isRecommended ? '今日优先' : '',
      ctaLabel: isRecommended ? '优先进入' : '立即进入',
    }
  })
})

const weaknessFocusCard = computed(() => {
  const suggestion = currentFocusUrgentKnowledgeSuggestion.value || {}
  const target = suggestion?.target && typeof suggestion.target === 'object' ? suggestion.target : null

  if (!target) {
    return {
      tone: 'empty',
      kicker: '今日弱项',
      badge: '先做一轮',
      title: '先刷一轮，再出弱项',
      description: '先刷，刷完回来这里直接告诉你补哪块。',
      detail: `当前先按 ${referenceGroupLabel.value} 给总览。`,
      actionLabel: '现在去刷',
      subjectCode: currentFocusSubject.value?.subjectCode || '',
      target: null,
    }
  }

  const mastery = clampPercent(target.mastery || 0)
  const questionCount = Math.max(0, Number(target.questionCount || 0))
  const subjectName = target.subjectName || currentFocusSubject.value?.subjectName || '当前科目'
  const targetLabel = target.label || '这块内容'
  const isRisk = suggestion.tone === 'risk'

  return {
    tone: suggestion.tone || 'steady',
    kicker: '今日弱项',
    badge: isRisk ? '先补这里' : '顺手拉高',
    title: `${subjectName} · ${targetLabel}`,
    description: isRisk
      ? '先补这块，现在就做一轮针对题。'
      : '这块还能涨，顺手再刷一轮。',
    detail: `${mastery}% 掌握度 · ${questionCount} 题关联`,
    actionLabel: isRisk ? '现在去补' : '现在去刷',
    subjectCode: String(target.subjectCode || currentFocusSubject.value?.subjectCode || '').trim(),
    target,
  }
})

const todayPriorityCard = computed(() => {
  const recommendation = todayExecutionRecommendation.value || {}
  const kind = String(recommendation.kind || 'empty').trim() || 'empty'
  const taskName = String(recommendation.task?.taskName || '').trim()
  const weaknessLabel = String(recommendation.target?.label || '').trim()
  const badgeMap = {
    checkIn: '先打卡',
    task: '先完成',
    weakness: '先补弱',
    empty: '保持节奏',
  }

  const titleMap = {
    checkIn: '先打卡，再开练',
    task: taskName ? `先做「${taskName}」` : '先做今日任务',
    weakness: weaknessLabel ? `先补「${weaknessLabel}」` : '先补当前弱项',
    empty: '继续刷，别停手',
  }
  const descriptionMap = {
    checkIn: '先把今天开起来。',
    task: '先做这一项，做完再看下一步。',
    weakness: '先把最拖分的这块拉回来。',
    empty: '没有更急的项，直接继续刷。',
  }

  return {
    tone: kind === 'weakness' ? 'risk' : (kind === 'checkIn' ? 'steady' : 'task'),
    kicker: '今天最该完成的事',
    badge: badgeMap[kind] || '现在去做',
    title: titleMap[kind] || '先打开今天的主线动作',
    description: descriptionMap[kind] || '先把最明确的一步做完。',
    detail: String(recommendation.helper || todayTaskEntryHelper.value).trim(),
    actionLabel: kind === 'empty'
      ? '继续去刷'
      : (kind === 'weakness'
        ? '现在去补'
        : (kind === 'checkIn' ? '现在去打卡' : '现在去做')),
    kind,
    target: recommendation.target || null,
  }
})

function dailyTaskProgress(task) {
  const completed = Number(task?.completed || 0)
  const target = Math.max(0, Number(task?.target || 0))
  const percent = target > 0 ? Math.round(Math.min(100, (completed / target) * 100)) : 0
  return {
    completed,
    target,
    percent,
  }
}

function clearSubjectInsightBackgroundTimer() {
  if (subjectInsightBackgroundTimer) {
    window.clearTimeout(subjectInsightBackgroundTimer)
    subjectInsightBackgroundTimer = 0
  }
}

function normalizeInsightSubjects(subjectRows = []) {
  return (Array.isArray(subjectRows) ? subjectRows : [])
    .map((item) => ({
      subjectId: String(item?.subjectId || '').trim(),
      subjectCode: String(item?.subjectCode || '').trim(),
      subjectName: String(item?.subjectName || item?.subjectCode || '').trim(),
    }))
    .filter((item) => Boolean(item.subjectCode))
}

function buildSubjectInsightPlaceholder(subjectItem = {}, status = 'idle') {
  return {
    subjectId: String(subjectItem?.subjectId || '').trim(),
    subjectCode: String(subjectItem?.subjectCode || '').trim(),
    subjectName: String(subjectItem?.subjectName || subjectItem?.subjectCode || '').trim(),
    status,
    l5Total: 0,
    l5Covered: 0,
    averageMastery: 0,
    coverage: 0,
    weakNodes: [],
    errorMessage: '',
  }
}

function mergeSubjectInsightMetric(metric = {}) {
  const subjectCode = String(metric?.subjectCode || '').trim()
  if (!subjectCode) {
    return
  }
  const currentRows = Array.isArray(subjectKnowledgeMetrics.value) ? subjectKnowledgeMetrics.value : []
  const nextRows = currentRows.slice()
  const targetIndex = nextRows.findIndex((item) => String(item?.subjectCode || '').trim() === subjectCode)
  if (targetIndex >= 0) {
    nextRows[targetIndex] = { ...nextRows[targetIndex], ...metric }
  } else {
    nextRows.push(metric)
  }
  subjectKnowledgeMetrics.value = nextRows
}

function refreshSubjectInsightLoadError() {
  const rows = Array.isArray(subjectKnowledgeMetrics.value) ? subjectKnowledgeMetrics.value : []
  const failedRows = rows.filter((item) => item.status === 'error')
  if (!failedRows.length) {
    subjectInsightLoadError.value = ''
    return
  }
  const readyRows = rows.filter((item) => item.status === 'ready')
  subjectInsightLoadError.value = !readyRows.length
    ? '知识树摘要接口暂时不可用，首页先保留预测分和任务主线。'
    : `${failedRows.length} 门科目的知识树摘要暂未同步，覆盖率和弱项建议先按已成功科目展示。`
}

async function fetchSubjectInsightMetric(subjectItem = {}) {
  try {
    const response = await knowledgeTreeV2({
      status: 'ENABLED',
      subject_code: subjectItem.subjectCode,
    })
    const payload = response?.data || response || {}
    const graphIndex = buildKnowledgeGraphIndex(payload)
    const nodeMap = graphIndex?.nodeMap || {}
    const levelById = graphIndex?.levelById || {}
    const l5Nodes = Object.keys(nodeMap)
      .filter((nodeId) => Number(levelById[nodeId] || 0) >= 5 && String(nodeId || '').trim())
      .map((nodeId) => {
        const nodeItem = nodeMap[nodeId] || {}
        return {
          id: String(nodeId || '').trim(),
          label: String(nodeItem?.label || nodeId).trim(),
          mastery: normalizeKnowledgeMastery(nodeItem?.mastery || 0),
          questionCount: Number(nodeItem?.questionCount || 0),
        }
      })

    const l5Total = l5Nodes.length
    const l5Covered = l5Nodes.filter((nodeItem) => nodeItem.mastery > 0).length
    const averageMastery = l5Total
      ? Math.round(l5Nodes.reduce((sum, nodeItem) => sum + nodeItem.mastery, 0) / l5Total)
      : 0

    return {
      ...subjectItem,
      status: 'ready',
      l5Total,
      l5Covered,
      averageMastery,
      coverage: l5Total ? Math.round((l5Covered / l5Total) * 100) : 0,
      weakNodes: l5Nodes
        .sort((left, right) => {
          if (left.mastery !== right.mastery) {
            return left.mastery - right.mastery
          }
          if (left.questionCount !== right.questionCount) {
            return right.questionCount - left.questionCount
          }
          return left.label.localeCompare(right.label, 'zh-Hans-CN')
        })
        .slice(0, 3),
      errorMessage: '',
    }
  } catch (error) {
    return {
      ...subjectItem,
      status: 'error',
      l5Total: 0,
      l5Covered: 0,
      averageMastery: 0,
      coverage: 0,
      weakNodes: [],
      errorMessage: String(error?.response?.data?.message || error?.message || '知识树摘要加载失败'),
    }
  }
}

async function ensureSubjectInsightReady(subjectCode, { force = false } = {}) {
  const normalizedSubjectCode = String(subjectCode || '').trim()
  if (!normalizedSubjectCode) {
    return
  }
  const subjectItem = normalizeInsightSubjects(scopedCoreSubjects.value)
    .find((item) => item.subjectCode === normalizedSubjectCode)
  if (!subjectItem) {
    return
  }
  const currentMetric = subjectKnowledgeMetricsMap.value[normalizedSubjectCode] || {}
  const currentStatus = String(currentMetric?.status || '').trim()
  if (!force && (currentStatus === 'ready' || currentStatus === 'loading')) {
    return
  }
  mergeSubjectInsightMetric({
    ...buildSubjectInsightPlaceholder(subjectItem, 'loading'),
    ...currentMetric,
    status: 'loading',
    errorMessage: '',
  })
  const nextMetric = await fetchSubjectInsightMetric(subjectItem)
  mergeSubjectInsightMetric(nextMetric)
  refreshSubjectInsightLoadError()
}

async function loadKnowledgeInsights(subjectRows = [], { prioritySubjectCode = '', force = false } = {}) {
  const normalizedSubjects = normalizeInsightSubjects(subjectRows)

  clearSubjectInsightBackgroundTimer()
  subjectInsightBatchToken += 1
  const currentBatchToken = subjectInsightBatchToken

  if (!normalizedSubjects.length) {
    subjectKnowledgeMetrics.value = []
    subjectInsightLoadError.value = ''
    return
  }

  const currentMetricMap = new Map(
    (Array.isArray(subjectKnowledgeMetrics.value) ? subjectKnowledgeMetrics.value : [])
      .map((item) => [String(item?.subjectCode || '').trim(), item]),
  )
  const prioritizedSubjectCode = String(prioritySubjectCode || '').trim()
  subjectKnowledgeMetrics.value = normalizedSubjects.map((subjectItem) => {
    const currentMetric = currentMetricMap.get(subjectItem.subjectCode)
    const shouldKeepReady = !force && String(currentMetric?.status || '').trim() === 'ready'
    if (shouldKeepReady) {
      return { ...buildSubjectInsightPlaceholder(subjectItem, 'ready'), ...currentMetric }
    }
    return {
      ...buildSubjectInsightPlaceholder(
        subjectItem,
        subjectItem.subjectCode === prioritizedSubjectCode ? 'loading' : 'idle',
      ),
      ...(force ? {} : currentMetric),
      status: subjectItem.subjectCode === prioritizedSubjectCode ? 'loading' : 'idle',
      errorMessage: '',
    }
  })
  refreshSubjectInsightLoadError()

  const orderedSubjects = normalizedSubjects.slice().sort((left, right) => {
    if (left.subjectCode === prioritizedSubjectCode) {
      return -1
    }
    if (right.subjectCode === prioritizedSubjectCode) {
      return 1
    }
    return 0
  })

  const loadSequentially = async () => {
    for (let index = 0; index < orderedSubjects.length; index += 1) {
      if (currentBatchToken !== subjectInsightBatchToken) {
        return
      }
      const subjectItem = orderedSubjects[index]
      const currentMetric = subjectKnowledgeMetricsMap.value[subjectItem.subjectCode] || {}
      const currentStatus = String(currentMetric?.status || '').trim()
      if (!force && currentStatus === 'ready') {
        continue
      }
      mergeSubjectInsightMetric({
        ...buildSubjectInsightPlaceholder(subjectItem, 'loading'),
        ...currentMetric,
        status: 'loading',
        errorMessage: '',
      })
      const nextMetric = await fetchSubjectInsightMetric(subjectItem)
      if (currentBatchToken !== subjectInsightBatchToken) {
        return
      }
      mergeSubjectInsightMetric(nextMetric)
      refreshSubjectInsightLoadError()
      if (index < orderedSubjects.length - 1) {
        await new Promise((resolve) => {
          subjectInsightBackgroundTimer = window.setTimeout(resolve, 120)
        })
      }
    }
  }

  void loadSequentially()
}

async function loadHomeContext() {
  loading.value = true
  try {
    const summaryFilters = {
      examCategoryCode: userStore.examCategoryCode,
      jointExamGroupCode: userStore.jointExamGroupCode,
    }
    if (String(userStore.userId || '').trim()) {
      summaryFilters.studentUserId = userStore.userId
    }

    const [dashboardResult, summaryResult] = await Promise.allSettled([
      fetchStudentDashboard(),
      fetchAnalyticsSummary(summaryFilters),
    ])

    if (dashboardResult.status === 'fulfilled') {
      applyDashboardPayload(dashboardResult.value)
    } else {
      if (!subjectContextStore.subjectOptions.length) {
        await subjectContextStore.ensureStudentSubjectContext({ force: true })
      }
      applyDashboardPayload({})
    }

    const summary = summaryResult.status === 'fulfilled' ? summaryResult.value : {}
    const sourceRows = Array.isArray(summary?.mastery) ? summary.mastery : []
    const currentUserId = String(userStore.userId || '').trim()
    const userRows = sourceRows.filter((row) => String(row?.studentUserId || '').trim() === currentUserId)
    masteryRows.value = userRows.length ? userRows : sourceRows

    if (summaryResult.status !== 'fulfilled') {
      subjectKnowledgeMetrics.value = []
    }

    const initialSubjectCode = String(
      route.query.subjectCode
      || subjectContextStore.currentSubjectCode
      || activeSubjectCode.value
      || scopedCoreSubjects.value[0]?.subjectCode
      || '',
    ).trim()
    if (initialSubjectCode) {
      activeSubjectCode.value = initialSubjectCode
    }
  } catch (error) {
    if (!subjectContextStore.subjectOptions.length) {
      await subjectContextStore.ensureStudentSubjectContext({ force: true })
    }
    applyDashboardPayload({})
    masteryRows.value = []
    subjectKnowledgeMetrics.value = []
  } finally {
    loading.value = false
  }

  if (scopedCoreSubjects.value.length) {
    await loadKnowledgeInsights(scopedCoreSubjects.value, {
      prioritySubjectCode: String(currentFocusSubjectCode.value || scopedCoreSubjects.value[0]?.subjectCode || '').trim(),
    })
  }
}

async function retrySubjectInsights() {
  if (subjectInsightsRetrying.value) {
    return
  }
  subjectInsightsRetrying.value = true
  try {
    await loadKnowledgeInsights(scopedCoreSubjects.value, {
      prioritySubjectCode: String(currentFocusSubjectCode.value || scopedCoreSubjects.value[0]?.subjectCode || '').trim(),
      force: true,
    })
  } finally {
    subjectInsightsRetrying.value = false
  }
}

async function navigateToDailyTasks(subjectItem = currentFocusSubject.value) {
  await router.push({
    path: '/student/analysis/tasks',
    query: subjectItem?.subjectCode ? { subjectCode: subjectItem.subjectCode } : {},
  })
}

async function navigateToChallengePoints(subjectItem = currentFocusSubject.value) {
  await router.push({
    path: '/student/analysis/points',
    query: subjectItem?.subjectCode ? { subjectCode: subjectItem.subjectCode } : {},
  })
}

async function navigateToPracticeModule(module, subjectItem = currentFocusSubject.value) {
  await router.push(buildStudentPracticeRouteLocation({
    module,
    subjectCode: subjectItem?.subjectCode || currentFocusSubjectCode.value,
    practiceSource: STUDENT_PRACTICE_SOURCE.HOME,
    practiceSourceLabel: '学习首页进入',
  }))
}

async function handlePracticeModuleQuickAction(moduleKey) {
  await navigateToPracticeModule(moduleKey, currentFocusSubject.value)
}

async function navigateToMessages() {
  await router.push('/messages')
}

async function navigateToOnboardingDiagnosis() {
  await router.push('/student/onboarding/diagnosis')
}

async function navigateToSubscriptionCheckout() {
  await router.push('/student/subscription/checkout')
}

async function navigateToSubscriptionStatus() {
  await router.push({
    path: '/student/subscription/success',
    query: {
      source: 'status',
    },
  })
}

async function handleSubscriptionCardAction(action) {
  const normalizedAction = String(action || '').trim()
  if (normalizedAction === 'tasks') {
    await navigateToDailyTasks(currentFocusSubject.value)
    return
  }
  if (normalizedAction === 'subscriptionStatus') {
    await navigateToSubscriptionStatus()
    return
  }
  if (normalizedAction === 'checkout') {
    await navigateToSubscriptionCheckout()
    return
  }
  await navigateToOnboardingDiagnosis()
}

function resolveSubjectCardByCode(subjectCode = '') {
  const normalizedSubjectCode = String(subjectCode || '').trim()
  if (!normalizedSubjectCode) {
    return currentFocusSubject.value || activeSubjectCard.value || null
  }
  return subjectCards.value.find((item) => item.subjectCode === normalizedSubjectCode) || currentFocusSubject.value || activeSubjectCard.value || null
}

async function navigateToWeaknessFocus(target = weaknessFocusCard.value.target) {
  const targetSubject = resolveSubjectCardByCode(target?.subjectCode || weaknessFocusCard.value.subjectCode)
  if (target) {
    await navigateToPracticeModule(STUDENT_PRACTICE_MODULE.FREE, targetSubject)
    return
  }
  await navigateToSubjectAnalysis(targetSubject)
}

async function handleTodayPriorityPrimaryAction() {
  if (todayPriorityCard.value.kind === 'weakness') {
    await navigateToWeaknessFocus(todayPriorityCard.value.target)
    return
  }
  if (todayPriorityCard.value.kind === 'empty') {
    await navigateToPracticeModule(resolveRecommendedPracticeModuleKey(), currentFocusSubject.value)
    return
  }
  await navigateToDailyTasks(currentFocusSubject.value)
}

function handleSubjectCardClick(subjectItem) {
  activeSubjectCode.value = String(subjectItem?.subjectCode || '').trim()
  subjectDrawerVisible.value = true
  void ensureSubjectInsightReady(activeSubjectCode.value)
}

async function navigateToSubjectAnalysis(subjectItem = activeSubjectCard.value) {
  const subjectCode = String(subjectItem?.subjectCode || '').trim()
  if (!subjectCode) {
    return
  }
  subjectDrawerVisible.value = false
  await router.push({
    path: '/student/analysis/overview',
    query: {
      subjectCode,
    },
  })
}

async function handleSubjectTaskDecision(subjectItem = activeSubjectCard.value) {
  await navigateToDailyTasks(subjectItem || activeSubjectCard.value)
}

async function handleAssistantPrimaryAction() {
  await navigateToDailyTasks(currentFocusSubject.value)
}

onMounted(async () => {
  await loadHomeContext()
})

onBeforeUnmount(() => {
  clearSubjectInsightBackgroundTimer()
  subjectInsightBatchToken += 1
})

watch(
  () => currentFocusSubjectCode.value,
  (nextSubjectCode) => {
    const normalizedSubjectCode = String(nextSubjectCode || '').trim()
    if (!normalizedSubjectCode) {
      return
    }
    activeSubjectCode.value = normalizedSubjectCode
    if (loading.value) {
      return
    }
    void ensureSubjectInsightReady(normalizedSubjectCode)
  },
  { immediate: true },
)

</script>

<template>
  <section class="home-shell">
    <header class="page-head">
      <div class="page-copy">
        <span class="page-kicker">今日概览</span>
        <div class="page-title-row">
          <h3>学习首页</h3>
          <p class="page-title-note">把注意力集中在预测分、弱项和今天最该完成的事。</p>
        </div>
      </div>

      <div class="date-pill">{{ currentDateLabel }}</div>
    </header>

    <template v-if="loading">
      <section class="hero-skeleton">
        <el-skeleton animated>
          <template #template>
            <el-skeleton-item variant="text" class="skeleton-line skeleton-line--short" />
            <el-skeleton-item variant="h1" class="skeleton-line skeleton-line--title" />
            <el-skeleton-item variant="rect" class="skeleton-block skeleton-block--hero" />
          </template>
        </el-skeleton>
      </section>

      <section class="focus-grid">
        <article v-for="index in 2" :key="`focus-skeleton-${index}`" class="focus-card diagnosis-skeleton">
          <el-skeleton animated>
            <template #template>
              <el-skeleton-item variant="text" class="skeleton-line skeleton-line--short" />
              <el-skeleton-item variant="rect" class="skeleton-block" />
            </template>
          </el-skeleton>
        </article>
      </section>

      <section class="subject-section diagnosis-skeleton">
        <el-skeleton animated>
          <template #template>
            <el-skeleton-item variant="text" class="skeleton-line skeleton-line--short" />
            <div class="subject-skeleton-grid">
              <el-skeleton-item v-for="index in 6" :key="`subject-skeleton-${index}`" variant="rect" class="subject-skeleton-card" />
            </div>
          </template>
        </el-skeleton>
      </section>
    </template>

    <template v-else>
      <section
        v-if="subjectInsightNotice"
        :class="['home-inline-alert', `home-inline-alert--${subjectInsightNotice.tone}`]"
      >
        <div class="home-inline-alert__copy">
          <strong>{{ subjectInsightNotice.title }}</strong>
          <p>{{ subjectInsightNotice.description }}</p>
        </div>
        <el-button
          size="small"
          plain
          :loading="subjectInsightsRetrying"
          @click="retrySubjectInsights"
        >
          重试学情摘要
        </el-button>
      </section>

      <section :class="['subscription-status-panel', `subscription-status-panel--${homeSubscriptionCard.tone}`]">
        <div class="subscription-status-panel__copy">
          <span class="subscription-status-panel__badge">{{ homeSubscriptionCard.badge }}</span>
          <h4>{{ homeSubscriptionCard.title }}</h4>
          <p>{{ homeSubscriptionCard.description }}</p>
          <small>{{ homeSubscriptionCard.detail }}</small>
        </div>
        <div class="subscription-status-panel__actions">
          <el-button
            type="primary"
            size="small"
            @click="handleSubscriptionCardAction(homeSubscriptionCard.primaryAction)"
          >
            {{ homeSubscriptionCard.primaryActionLabel }}
          </el-button>
          <el-button
            plain
            size="small"
            @click="handleSubscriptionCardAction(homeSubscriptionCard.secondaryAction)"
          >
            {{ homeSubscriptionCard.secondaryActionLabel }}
          </el-button>
        </div>
      </section>

      <section class="overview-grid">
        <article class="decision-atlas__hero decision-atlas__hero--compact">
          <div class="decision-atlas__copy">
            <div class="decision-atlas__eyebrow-row">
              <span class="decision-atlas__eyebrow">今日主线</span>
              <span class="decision-atlas__quote">{{ todayNorthStarQuote }}</span>
            </div>
            <h4>{{ todayNorthStarTitle }}</h4>
            <p>{{ todayNorthStarCopy }}</p>
          </div>

          <div class="decision-atlas__focus-grid">
            <article :class="['decision-focus-card', `decision-focus-card--${weaknessFocusCard.tone}`]">
              <div class="decision-focus-card__head">
                <span class="decision-focus-card__kicker">{{ weaknessFocusCard.kicker }}</span>
                <span class="decision-focus-card__badge">{{ weaknessFocusCard.badge }}</span>
              </div>
              <strong>{{ weaknessFocusCard.title }}</strong>
              <p>{{ weaknessFocusCard.description }}</p>
              <small>{{ weaknessFocusCard.detail }}</small>
              <el-button
                size="small"
                plain
                :class="[
                  'decision-focus-card__action',
                  'decision-focus-card__action--support',
                  `decision-focus-card__action--${weaknessFocusCard.tone}`,
                ]"
                @click="navigateToWeaknessFocus()"
              >
                {{ weaknessFocusCard.actionLabel }}
              </el-button>
            </article>

            <article :class="['decision-focus-card', `decision-focus-card--${todayPriorityCard.tone}`]">
              <div class="decision-focus-card__head">
                <span class="decision-focus-card__kicker">{{ todayPriorityCard.kicker }}</span>
                <span class="decision-focus-card__badge">{{ todayPriorityCard.badge }}</span>
              </div>
              <strong>{{ todayPriorityCard.title }}</strong>
              <p>{{ todayPriorityCard.description }}</p>
              <small>{{ todayPriorityCard.detail }}</small>
              <el-button
                size="small"
                type="primary"
                :class="[
                  'decision-focus-card__action',
                  'decision-focus-card__action--primary',
                  `decision-focus-card__action--${todayPriorityCard.tone}`,
                ]"
                @click="handleTodayPriorityPrimaryAction"
              >
                {{ todayPriorityCard.actionLabel }}
              </el-button>
            </article>
          </div>

          <div class="overview-pulse-grid">
            <article
              v-for="item in overviewPulseCards"
              :key="item.label"
              class="overview-pulse"
            >
              <span>{{ item.label }}</span>
              <strong>{{ item.value }}</strong>
              <small>{{ item.helper }}</small>
            </article>
          </div>
          <div class="panel-actions">
            <el-button size="small" type="primary" @click="navigateToDailyTasks(currentFocusSubject)">进入今日任务</el-button>
            <el-button size="small" plain @click="navigateToSubjectAnalysis(currentFocusSubject)">看知识诊断</el-button>
            <el-button size="small" plain @click="navigateToChallengePoints(currentFocusSubject)">看刷题段位</el-button>
            <el-button size="small" plain @click="navigateToMessages">消息中心</el-button>
          </div>
        </article>

        <StudentHeroBanner
          :predicted-score="predictedScore"
          :predicted-score-band="predictedScoreBand"
          :mastery-overview="masteryOverview"
          :overall-coverage="overallCoverage"
          :reference-group-label="referenceGroupLabel"
          :subject-count="subjectCards.length"
          :completed-daily-task-count="completedDailyTaskCount"
          :total-daily-task-count="totalDailyTaskCount"
          :practice-modules="practiceModuleQuickActions"
          @select-module="handlePracticeModuleQuickAction"
        />
      </section>

      <section class="task-center-panel">
        <div class="task-center-layout">
          <article class="points-summary-card">
            <div class="points-summary-card__head">
              <div>
                <span class="panel-kicker">刷题段位主模块</span>
                <h4>刷题段位已经提到首页主位</h4>
              </div>
              <span class="points-summary-card__badge">{{ currentFocusSubject?.subjectName || '当前科目' }}</span>
            </div>

            <p class="points-summary-card__copy">
              {{ homeChallengeSummaryCopy }}
              {{ homeChallengeMomentumCopy }}
            </p>

            <div class="points-summary-card__stats">
              <article class="points-summary-card__stat">
                <span>累计段位分</span>
                <strong>{{ Number(currentFocusChallengePoints.total || 0) }}</strong>
                <small>今日 +{{ Number(currentFocusChallengePoints.todayDelta || 0) }}</small>
              </article>
              <article class="points-summary-card__stat">
                <span>累计答对题次</span>
                <strong>{{ Number(currentFocusChallengePoints.correctSubmitCount || currentFocusChallengePoints.total || 0) }}</strong>
                <small>今日 +{{ Number(currentFocusChallengePoints.todayCorrectSubmitCount || currentFocusChallengePoints.todayDelta || 0) }}</small>
              </article>
              <article class="points-summary-card__stat">
                <span>当前段位</span>
                <strong>{{ currentFocusChallengePoints.levelName || '刷题青铜' }}</strong>
                <small>
                  {{ currentFocusChallengePoints.nextLevelName
                    ? `再积 ${Number(currentFocusChallengePoints.pointsToNextLevel || 0)} 分到 ${currentFocusChallengePoints.nextLevelName}`
                    : `已到 ${Number(currentFocusChallengePoints.scoreCap || 3000)} 分满阶` }}
                </small>
              </article>
            </div>

            <div class="points-summary-card__actions">
              <el-button type="primary" @click="navigateToChallengePoints(currentFocusSubject)">进入刷题段位</el-button>
              <el-button plain @click="navigateToPracticeModule(resolveRecommendedPracticeModuleKey(), currentFocusSubject)">继续冲分</el-button>
              <el-button plain @click="navigateToDailyTasks(currentFocusSubject)">查看今日任务</el-button>
            </div>
          </article>

          <section class="subject-section subject-section--compact task-center-subjects">
            <div class="section-head">
              <div>
                <span class="panel-kicker">科目速览</span>
                <h4>切换后全页同步</h4>
              </div>
              <span class="section-meta">{{ subjectCards.length }} 门</span>
            </div>

            <div class="subject-grid subject-grid--rail">
              <button
                v-for="subjectItem in subjectCards"
                :key="subjectItem.subjectCode"
                :class="['subject-card', { 'subject-card--active': subjectItem.subjectCode === currentFocusSubjectCode }]"
                type="button"
                :style="{ '--subject-accent': subjectItem.accent }"
                @click="handleSubjectCardClick(subjectItem)"
              >
                <div class="subject-card__head">
                  <span class="subject-icon">{{ subjectItem.badge }}</span>
                  <div>
                    <strong>{{ subjectItem.subjectName }}</strong>
                    <p>{{ subjectItem.coverageLabel }}</p>
                  </div>
                </div>
                <div class="subject-track" aria-hidden="true">
                  <div
                    class="subject-fill"
                    :class="{ 'subject-fill--unavailable': !subjectItem.hasInsight }"
                    :style="{ width: `${subjectItem.hasInsight ? subjectItem.coverage : 100}%` }"
                  />
                </div>
                <span class="subject-card__meta">{{ subjectItem.insightSummary }}</span>
              </button>
            </div>
          </section>
        </div>
      </section>

      <StudentSubjectDrawer
        v-model="subjectDrawerVisible"
        :subject="activeSubjectCard"
        @analyze="navigateToSubjectAnalysis"
        @tasks="handleSubjectTaskDecision"
      />
    </template>
  </section>
</template>

<style scoped>
.home-shell {
  display: grid;
  gap: var(--qb-space-4);
}

.overview-grid {
  display: grid;
  gap: var(--qb-space-3);
  grid-template-columns: minmax(360px, 1.02fr) minmax(320px, 0.98fr);
}

.home-inline-alert {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 14px 16px;
  border-radius: 16px;
  border: 1px solid transparent;
}

.home-inline-alert--warning {
  background: var(--qb-surface-soft-warning);
  border-color: color-mix(in srgb, var(--qb-warning) 26%, white 74%);
}

.home-inline-alert--error {
  background: var(--qb-surface-soft-danger);
  border-color: color-mix(in srgb, var(--qb-danger) 24%, white 76%);
}

.home-inline-alert__copy,
.home-inline-alert__copy p {
  margin: 0;
}

.home-inline-alert__copy {
  display: grid;
  gap: 4px;
}

.home-inline-alert__copy strong {
  color: var(--qb-text-heading);
  font-size: 14px;
}

.home-inline-alert__copy p {
  color: var(--qb-text-copy);
  font-size: 12px;
  line-height: 1.6;
}

.subscription-status-panel {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 16px 18px;
  border-radius: 18px;
  border: 1px solid rgba(0, 0, 0, 0.06);
}

.subscription-status-panel--active {
  background: linear-gradient(
    120deg,
    var(--qb-surface-soft-success) 0%,
    var(--qb-bg-card) 100%
  );
}

.subscription-status-panel--pending {
  background: linear-gradient(
    120deg,
    var(--qb-surface-soft-warning) 0%,
    var(--qb-bg-card) 100%
  );
}

.subscription-status-panel--guide {
  background: linear-gradient(
    120deg,
    var(--qb-surface-soft-info) 0%,
    var(--qb-bg-card) 100%
  );
}

.subscription-status-panel__copy {
  display: grid;
  gap: 6px;
}

.subscription-status-panel__copy h4,
.subscription-status-panel__copy p,
.subscription-status-panel__copy small {
  margin: 0;
}

.subscription-status-panel__copy h4 {
  color: var(--qb-text-heading);
  font-size: 16px;
}

.subscription-status-panel__copy p {
  color: var(--qb-text-copy);
  font-size: 13px;
  line-height: 1.6;
}

.subscription-status-panel__copy small {
  color: var(--qb-text-subtle);
  font-size: 12px;
  line-height: 1.5;
}

.subscription-status-panel__badge {
  display: inline-flex;
  width: fit-content;
  padding: 5px 10px;
  border-radius: 999px;
  background: var(--qb-bg-card);
  color: var(--qb-text-heading);
  font-size: 11px;
  font-weight: 700;
  border: 1px solid rgba(0, 0, 0, 0.06);
}

.subscription-status-panel__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.decision-atlas__hero {
  position: relative;
  overflow: hidden;
  border-radius: 28px;
  border: 1px solid rgba(191, 219, 254, 0.78);
  box-shadow: 0 22px 54px rgba(15, 23, 42, 0.08);
}

.decision-atlas__hero {
  display: grid;
  gap: var(--qb-space-3);
  padding: 22px;
  background:
    radial-gradient(circle at top right, rgba(59, 130, 246, 0.2), transparent 24%),
    radial-gradient(circle at 12% 18%, rgba(14, 165, 233, 0.14), transparent 20%),
    linear-gradient(145deg, rgba(255, 255, 255, 0.98), rgba(239, 246, 255, 0.98));
}

.decision-atlas__hero--compact {
  min-height: 100%;
  padding: 20px;
}

.decision-atlas__copy h4,
.decision-atlas__copy p {
  margin: 0;
}

.decision-atlas__eyebrow-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
}

.decision-atlas__eyebrow {
  display: inline-flex;
  width: fit-content;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.92);
  color: var(--qb-text-inverse);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
}

.decision-atlas__quote {
  color: var(--qb-text-subtle-3);
  font-size: 13px;
  font-weight: 700;
  line-height: 1.4;
}

.decision-atlas__copy h4 {
  margin-top: 12px;
  color: var(--qb-text-heading);
  font-size: clamp(24px, 2.5vw, 34px);
  line-height: 1.18;
  max-width: 100%;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.decision-atlas__copy p {
  margin-top: 10px;
  max-width: 62ch;
  color: var(--qb-text-copy);
  font-size: 13px;
  line-height: 1.7;
}

.decision-atlas__focus-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.decision-focus-card {
  display: grid;
  gap: 10px;
  padding: 14px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.76);
  backdrop-filter: blur(10px);
  box-shadow: inset 0 0 0 1px rgba(191, 219, 254, 0.5);
}

.decision-focus-card--risk {
  background:
    radial-gradient(circle at top right, rgba(248, 113, 113, 0.12), transparent 32%),
    rgba(255, 255, 255, 0.82);
  box-shadow: inset 0 0 0 1px rgba(251, 191, 36, 0.34);
}

.decision-focus-card--steady {
  background:
    radial-gradient(circle at top right, rgba(250, 204, 21, 0.12), transparent 28%),
    rgba(255, 255, 255, 0.82);
}

.decision-focus-card--task {
  background:
    radial-gradient(circle at top right, rgba(14, 165, 233, 0.12), transparent 28%),
    rgba(255, 255, 255, 0.82);
}

.decision-focus-card--empty {
  background:
    radial-gradient(circle at top right, rgba(148, 163, 184, 0.12), transparent 28%),
    rgba(255, 255, 255, 0.82);
}

.decision-focus-card__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.decision-focus-card__kicker,
.decision-focus-card__badge,
.decision-focus-card p,
.decision-focus-card small {
  margin: 0;
}

.decision-focus-card__kicker {
  color: var(--qb-text-subtle-4);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.04em;
}

.decision-focus-card__badge {
  display: inline-flex;
  align-items: center;
  padding: 5px 8px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.08);
  color: var(--qb-text-heading);
  font-size: 10px;
  font-weight: 700;
  white-space: nowrap;
}

.decision-focus-card strong {
  color: var(--qb-text-heading);
  font-size: 16px;
  line-height: 1.45;
}

.decision-focus-card p {
  color: var(--qb-text-copy);
  font-size: 12px;
  line-height: 1.65;
}

.decision-focus-card small {
  color: var(--qb-text-meta);
  font-size: 11px;
  line-height: 1.6;
}

.decision-focus-card__action {
  width: fit-content;
  min-width: 120px;
  font-weight: 700;
  transition:
    transform 0.18s ease,
    box-shadow 0.18s ease,
    border-color 0.18s ease,
    background 0.18s ease;
}

.decision-focus-card__action:hover,
.decision-focus-card__action:focus-visible {
  transform: translateY(-1px);
}

.decision-focus-card__action--primary {
  border: none;
  box-shadow: 0 14px 26px rgba(37, 99, 235, 0.18);
}

.decision-focus-card__action--primary.decision-focus-card__action--task {
  background: linear-gradient(135deg, rgba(14, 165, 233, 0.96), rgba(37, 99, 235, 0.96));
}

.decision-focus-card__action--primary.decision-focus-card__action--steady {
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.96), rgba(249, 115, 22, 0.96));
  box-shadow: 0 14px 26px rgba(245, 158, 11, 0.22);
}

.decision-focus-card__action--primary.decision-focus-card__action--risk {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.96), rgba(249, 115, 22, 0.96));
  box-shadow: 0 14px 26px rgba(239, 68, 68, 0.22);
}

.decision-focus-card__action--primary.decision-focus-card__action--empty {
  background: linear-gradient(135deg, rgba(71, 85, 105, 0.96), rgba(15, 23, 42, 0.96));
  box-shadow: 0 14px 26px rgba(15, 23, 42, 0.18);
}

.decision-focus-card__action--support {
  background: rgba(255, 255, 255, 0.88);
}

.decision-focus-card__action--support.decision-focus-card__action--risk {
  border-color: rgba(249, 115, 22, 0.38);
  color: rgb(194, 65, 12);
  box-shadow: 0 10px 20px rgba(249, 115, 22, 0.12);
}

.decision-focus-card__action--support.decision-focus-card__action--steady {
  border-color: rgba(245, 158, 11, 0.34);
  color: rgb(180, 83, 9);
  box-shadow: 0 10px 20px rgba(245, 158, 11, 0.1);
}

.decision-focus-card__action--support.decision-focus-card__action--task {
  border-color: rgba(37, 99, 235, 0.3);
  color: rgb(29, 78, 216);
  box-shadow: 0 10px 20px rgba(37, 99, 235, 0.1);
}

.decision-focus-card__action--support.decision-focus-card__action--empty {
  border-color: rgba(100, 116, 139, 0.28);
  color: rgb(51, 65, 85);
  box-shadow: 0 10px 20px rgba(100, 116, 139, 0.1);
}

.overview-pulse-grid {
  display: grid;
  gap: 10px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.overview-pulse {
  display: grid;
  gap: 6px;
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(12px);
  box-shadow: inset 0 0 0 1px rgba(191, 219, 254, 0.55);
}

.overview-pulse span,
.overview-pulse small {
  color: var(--qb-text-meta);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.overview-pulse strong {
  color: var(--qb-text-heading);
  font-size: 16px;
  line-height: 1.45;
}

.page-copy,
.page-copy h3,
.page-copy p,
.section-head h4,
.assistant-priority p,
.task-progress-hero p,
.task-item p {
  margin: 0;
}

.page-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--qb-space-4-5);
}

.page-kicker,
.panel-kicker {
  display: inline-flex;
  align-items: center;
  padding: 6px var(--qb-space-2-5);
  border-radius: var(--qb-radius-pill);
  background: var(--qb-student-kicker-bg);
  color: var(--qb-student-kicker-text);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.page-copy h3 {
  margin-top: 10px;
  font-size: clamp(24px, 2.6vw, 30px);
  line-height: 1.15;
  color: var(--qb-text-heading);
}

.page-title-row {
  display: flex;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 10px;
}

.page-title-note {
  margin-top: 10px;
  color: var(--qb-text-copy);
  font-size: 12px;
}

.page-copy p {
  margin-top: var(--qb-space-2);
  color: var(--qb-text-copy);
  font-size: 12px;
}

.page-copy .page-title-note {
  margin-top: 10px;
}

.date-pill {
  display: inline-flex;
  align-items: center;
  padding: 8px 12px;
  border-radius: var(--qb-radius-pill);
  background: rgba(219, 234, 254, 0.66);
  color: var(--qb-primary-student);
  font-size: 12px;
  font-weight: 700;
}

.focus-grid {
  display: grid;
  gap: var(--qb-space-5);
  grid-template-columns: minmax(0, 0.95fr) minmax(0, 1.25fr);
  align-items: start;
}

.focus-card,
.subject-section,
.hero-skeleton {
  position: relative;
  overflow: hidden;
  border-radius: var(--qb-student-card-radius);
  background: var(--qb-surface-strong);
  box-shadow: var(--qb-student-card-shadow);
}

.focus-card,
.subject-section,
.hero-skeleton,
.diagnosis-skeleton {
  padding: var(--qb-space-6);
}

.task-center-panel {
  display: grid;
  gap: var(--qb-space-3);
}

.task-center-layout {
  display: grid;
  gap: var(--qb-space-3);
  grid-template-columns: minmax(360px, 1.02fr) minmax(320px, 0.98fr);
  align-items: stretch;
}

.task-center-subjects {
  min-height: 100%;
}

.points-summary-card {
  display: grid;
  gap: var(--qb-space-4);
  padding: var(--qb-space-6);
  border-radius: 28px;
  background:
    radial-gradient(circle at top right, rgba(47, 84, 235, 0.14), transparent 38%),
    radial-gradient(circle at 10% 16%, rgba(245, 158, 11, 0.12), transparent 24%),
    linear-gradient(140deg, rgba(255, 255, 255, 0.98), rgba(255, 251, 235, 0.94));
  box-shadow: var(--qb-shadow-card);
}

.points-summary-card__head,
.points-summary-card__actions,
.points-summary-card__stats {
  display: flex;
  gap: var(--qb-space-3);
}

.points-summary-card__head {
  align-items: flex-start;
  justify-content: space-between;
}

.points-summary-card__head h4,
.points-summary-card__copy,
.points-summary-card__stat {
  margin: 0;
}

.points-summary-card__copy {
  color: var(--qb-color-text-secondary);
}

.points-summary-card__badge {
  padding: 8px 14px;
  border-radius: 999px;
  background: rgba(245, 158, 11, 0.14);
  color: var(--qb-text-warning-ink);
  font-size: 0.86rem;
  font-weight: 600;
}

.points-summary-card__stats {
  flex-wrap: wrap;
}

.points-summary-card__stat {
  display: grid;
  gap: 6px;
  flex: 1 1 180px;
  min-width: 0;
  padding: var(--qb-space-4);
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.78);
}

.points-summary-card__stat span,
.points-summary-card__stat small {
  color: var(--qb-color-text-secondary);
}

.points-summary-card__stat strong {
  color: var(--qb-color-text-strong);
  font-size: 1.05rem;
}

.points-summary-card__actions {
  flex-wrap: wrap;
}

.focus-side {
  display: grid;
  gap: var(--qb-space-5);
}

.radar-panel {
  min-height: 100%;
}

.section-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--qb-space-3-5);
}

.section-head h4 {
  margin-top: var(--qb-space-2-5);
  color: var(--qb-text-heading);
  font-size: 18px;
  line-height: 1.3;
}

.section-head--compact h4 {
  font-size: 17px;
}

.section-meta,
.task-summary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 44px;
  padding: var(--qb-space-2) var(--qb-space-3);
  border-radius: var(--qb-radius-pill);
  background: var(--qb-surface-soft-primary);
  color: var(--qb-primary-student);
  font-size: 12px;
  font-weight: 700;
}

.assistant-panel,
.task-panel {
  display: grid;
  gap: var(--qb-space-4-5);
}

.assistant-priority {
  display: grid;
  gap: var(--qb-space-3);
  padding: var(--qb-space-4-5);
  border-radius: var(--qb-radius-xl);
}

.assistant-priority--risk {
  background: var(--qb-surface-soft-danger);
}

.assistant-priority--steady {
  background: var(--qb-surface-soft-warning);
}

.assistant-priority--empty {
  background: var(--qb-surface-soft-neutral);
}

.assistant-tag {
  width: fit-content;
  padding: 7px var(--qb-space-3);
  border-radius: var(--qb-radius-pill);
  background: var(--qb-surface-ink-soft);
  color: var(--qb-text-secondary-strong);
  font-size: 12px;
  font-weight: 700;
}

.assistant-priority strong {
  color: var(--qb-text-heading);
  font-size: 18px;
  line-height: 1.55;
}

.assistant-priority p {
  color: var(--qb-text-copy);
  font-size: 13px;
  line-height: 1.7;
}

.task-progress-hero {
  padding: var(--qb-space-4) var(--qb-space-4-5);
  border-radius: var(--qb-radius-lg);
  background: var(--qb-gradient-primary-panel);
}

.task-progress-hero strong {
  color: var(--qb-text-heading);
  font-size: 18px;
}

.task-progress-hero p {
  margin-top: 8px;
  color: var(--qb-text-copy);
  font-size: 13px;
  line-height: 1.7;
}

.task-summary-strip {
  display: grid;
  gap: var(--qb-space-3);
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.task-summary-chip {
  display: grid;
  gap: 8px;
  padding: var(--qb-space-3-5) var(--qb-space-4);
  border-radius: var(--qb-radius-lg);
  background: var(--qb-surface-raised);
}

.task-summary-chip span {
  color: var(--qb-text-meta);
  font-size: 12px;
  font-weight: 600;
}

.task-summary-chip strong {
  color: var(--qb-text-heading);
  font-size: 15px;
  line-height: 1.5;
}

.task-list {
  display: grid;
  gap: var(--qb-space-3);
}

.task-item {
  display: grid;
  gap: var(--qb-space-2-5);
  padding: var(--qb-space-3-5) var(--qb-space-4);
  border-radius: var(--qb-radius-lg);
  background: var(--qb-surface-raised);
}

.task-item-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--qb-space-3);
}

.task-item strong {
  color: var(--qb-text-heading);
  font-size: 14px;
}

.task-item p {
  margin-top: 4px;
  color: var(--qb-text-meta);
  font-size: 12px;
}

.task-state {
  display: inline-flex;
  align-items: center;
  padding: 6px var(--qb-space-2-5);
  border-radius: var(--qb-radius-pill);
  background: var(--qb-surface-soft-warning);
  color: var(--qb-text-warning-ink);
  font-size: 11px;
  font-weight: 700;
  white-space: nowrap;
}

.task-state--done {
  background: var(--qb-surface-soft-success);
  color: var(--qb-text-success-ink);
}

.task-track,
.subject-track {
  width: 100%;
  overflow: hidden;
  border-radius: var(--qb-radius-pill);
  background: var(--qb-track-soft);
}

.task-track {
  height: 8px;
}

.subject-track {
  height: 6px;
}

.task-fill {
  height: 100%;
  border-radius: inherit;
  background: var(--qb-gradient-primary-fill);
}

.panel-actions {
  display: flex;
  gap: var(--qb-space-3);
  flex-wrap: wrap;
}

.panel-actions--compact {
  margin-top: var(--qb-space-3);
}

.subject-section {
  display: grid;
  gap: var(--qb-space-4-5);
}

.subject-section--compact {
  gap: var(--qb-space-3);
}

.subject-grid {
  display: grid;
  gap: var(--qb-space-4);
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.subject-grid--compact {
  gap: 10px;
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.subject-grid--rail {
  gap: 10px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.subject-card {
  display: grid;
  gap: 8px;
  padding: 14px;
  border: none;
  border-radius: 16px;
  background: var(--qb-surface-strong);
  box-shadow: inset 0 0 0 1px rgba(0, 21, 41, 0.05);
  cursor: pointer;
  text-align: left;
  transition:
    transform 0.18s ease,
    box-shadow 0.18s ease;
}

.subject-card:hover,
.subject-card:focus-visible {
  transform: translateY(-2px);
  box-shadow:
    inset 0 0 0 1px color-mix(in srgb, var(--subject-accent) 20%, white 80%),
    var(--qb-shadow-panel);
  outline: none;
}

.subject-card--active {
  box-shadow:
    inset 0 0 0 1px color-mix(in srgb, var(--subject-accent) 26%, white 74%),
    0 16px 36px color-mix(in srgb, var(--subject-accent) 12%, rgba(15, 23, 42, 0.08) 88%);
}

.subject-icon {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border-radius: var(--qb-radius-md);
  background: var(--subject-accent);
  color: var(--qb-text-inverse);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.05em;
}

.subject-card__head {
  display: flex;
  align-items: center;
  gap: 10px;
}

.subject-card__head p,
.subject-card__meta {
  margin: 0;
  color: var(--qb-text-copy);
  font-size: 12px;
  line-height: 1.6;
}

.subject-card strong {
  color: var(--qb-text-heading);
  font-size: 14px;
  line-height: 1.4;
}

.subject-fill {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, var(--subject-accent), color-mix(in srgb, var(--subject-accent) 68%, white 32%));
}

.subject-fill--unavailable {
  background: linear-gradient(90deg, color-mix(in srgb, var(--qb-border-muted) 92%, white 8%), var(--qb-border-muted));
}

.skeleton-line {
  width: 100%;
  height: 14px;
  margin-bottom: var(--qb-space-3);
}

.skeleton-line--short {
  width: 34%;
}

.skeleton-line--title {
  width: 48%;
  height: 42px;
}

.skeleton-block {
  width: 100%;
  height: 240px;
  border-radius: var(--qb-radius-lg);
}

.skeleton-block--hero {
  height: 280px;
  margin-top: var(--qb-space-4);
}

.subject-skeleton-grid {
  display: grid;
  gap: var(--qb-space-4);
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.subject-skeleton-card {
  width: 100%;
  height: 132px;
  border-radius: var(--qb-radius-xl);
}

@media (max-width: 1100px) {
  .overview-grid,
  .focus-grid,
  .task-center-layout,
  .subject-grid,
  .task-summary-strip,
  .subject-skeleton-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 900px) {
  .subject-grid,
  .subject-skeleton-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .home-shell {
    gap: var(--qb-space-4-5);
  }

  .home-inline-alert {
    flex-direction: column;
    align-items: flex-start;
  }

  .subscription-status-panel {
    flex-direction: column;
    align-items: flex-start;
  }

  .subscription-status-panel__actions {
    width: 100%;
  }

  .points-summary-card__head {
    flex-direction: column;
  }

  .page-head {
    flex-direction: column;
    align-items: flex-start;
  }

  .page-title-row {
    align-items: flex-start;
  }

  .page-copy .page-title-note {
    margin-top: 0;
  }

  .date-pill {
    align-self: flex-start;
  }

  .focus-card,
  .subject-section,
  .hero-skeleton,
  .diagnosis-skeleton {
    padding: var(--qb-space-4-5);
    border-radius: var(--qb-radius-xl);
  }

  .overview-pulse-grid {
    grid-template-columns: 1fr;
  }

  .decision-atlas__focus-grid {
    grid-template-columns: 1fr;
  }

  .decision-focus-card__head {
    align-items: flex-start;
    flex-direction: column;
  }

  .panel-actions {
    flex-direction: column;
  }

  .subject-grid,
  .subject-skeleton-grid {
    grid-template-columns: 1fr;
  }

  .subject-grid--rail {
    grid-template-columns: 1fr;
  }
}
</style>
