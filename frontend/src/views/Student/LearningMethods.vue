<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { ElMessage } from '@/ui/feedback'
import { useRoute, useRouter } from 'vue-router'
import {
  completeLearningMethodSession,
  fetchLearningMethodDetail,
  fetchLearningMethodList,
  fetchLearningMethodQuestionPackRecommendation,
  fetchLearningMethodQuestionPackRecommendationHistory,
  startLearningMethodSession,
  submitLearningMethodQuestionPackFeedback,
} from '../../api/services/questionBank.js'
import { useSubjectContextStore } from '../../stores/subjectContextStore.js'
import {
  buildStudentPracticeRouteLocation,
  STUDENT_PRACTICE_MODULE,
  STUDENT_PRACTICE_SOURCE,
} from '../../utils/studentPracticeNavigation.js'
import { consumeAllLearningMethodFeedbackNotices } from '../../utils/learningMethodFeedbackNotice.js'
import {
  LEARNING_METHOD_RECOMMENDATION_STRATEGY_SOURCE,
  learningMethodRecommendationStrategySourceLabel,
  loadPersistedLearningMethodRecommendationStrategy,
  normalizeLearningMethodRecommendationStrategyCode,
  normalizeLearningMethodRecommendationStrategySource,
  recommendationStrategyCodeByPracticeStrategy,
  resolveLearningMethodRecommendationStrategyFromPayload,
  resolveLearningMethodRecommendationStrategySourceFromPayload,
  savePersistedLearningMethodRecommendationStrategy,
} from '../../utils/learningMethodStrategy.js'
import {
  computeLearningMethodSourceInsights,
  summarizeLearningMethodSourceInsights,
} from '../../utils/learningMethodSourceInsights.js'

const route = useRoute()
const router = useRouter()
const subjectContextStore = useSubjectContextStore()

const loading = ref(false)
const listError = ref('')
const methodItems = ref([])
const selectedCode = ref('')
const detailLoading = ref(false)
const detailError = ref('')
const detailPayload = ref(null)
const actionLoadingCode = ref('')

const recommendationLoading = ref(false)
const recommendationError = ref('')
const recommendationPayload = ref(null)
const feedbackLoading = ref(false)
const feedbackStatus = ref('')

const recommendationHistoryLoading = ref(false)
const recommendationHistoryError = ref('')
const recommendationHistoryItems = ref([])
const historyPracticeLoadingRecommendationId = ref('')
const recentFeedbackNotices = ref([])
const returnSummaryHandledRecommendationId = ref('')
const RECENT_AUTO_FEEDBACK_HIGHLIGHT_MS = 8000
let recentAutoFeedbackHighlightTimer = 0

const RECOMMENDATION_STRATEGY_PRESETS = {
  FOUNDATION: {
    code: 'FOUNDATION',
    label: '基础巩固',
    difficultyPreference: 'easy',
    practiceStrategy: 'FOUNDATION_REINFORCE',
    questionCount: 10,
    tagType: 'warning',
  },
  BALANCED: {
    code: 'BALANCED',
    label: '均衡进阶',
    difficultyPreference: 'medium',
    practiceStrategy: 'BALANCED_ADVANCE',
    questionCount: 12,
    tagType: 'info',
  },
  SPRINT: {
    code: 'SPRINT',
    label: '冲刺突破',
    difficultyPreference: 'hard',
    practiceStrategy: 'SPRINT_BREAKTHROUGH',
    questionCount: 15,
    tagType: 'success',
  },
}

const selectedRecommendationStrategyCode = ref('BALANCED')
const selectedRecommendationStrategySource = ref(LEARNING_METHOD_RECOMMENDATION_STRATEGY_SOURCE.DEFAULT)

const currentSubjectCode = computed(() => String(subjectContextStore.currentSubjectCode || '').trim())
const selectedMethod = computed(() => (
  methodItems.value.find((item) => String(item?.methodCode || '').trim() === selectedCode.value) || null
))
const selectedProgress = computed(() => {
  const progress = detailPayload.value?.progress
  return progress && typeof progress === 'object' ? progress : {}
})
const currentSessionId = computed(() => String(selectedProgress.value?.extJson?.currentSession?.sessionId || '').trim())
const currentRecommendationId = computed(() => String(recommendationPayload.value?.recommendationId || '').trim())
const focusedHistoryMethodCode = computed(() =>
  String(route.query.learningMethodCode || '').trim().toUpperCase(),
)
const focusedHistoryRecommendationId = computed(() =>
  String(route.query.learningMethodRecommendationId || '').trim(),
)
const focusedHistorySessionId = computed(() =>
  String(route.query.learningMethodSessionId || '').trim(),
)
const isReturnFromPractice = computed(() =>
  String(route.query.fromPracticeReturn || '').trim() === '1',
)

function normalizeMethodList(payload) {
  const source = payload && typeof payload === 'object' ? payload : {}
  const rows = Array.isArray(source.items) ? source.items : []
  return rows
    .map((item) => {
      const progress = item?.progress && typeof item.progress === 'object' ? item.progress : {}
      return {
        methodCode: String(item?.methodCode || '').trim(),
        methodName: String(item?.methodName || '').trim(),
        oneLineIntro: String(item?.oneLineIntro || '').trim(),
        difficultyLevel: String(item?.difficultyLevel || 'L1').trim() || 'L1',
        estimatedMinutes: Number(item?.estimatedMinutes || 0),
        status: String(item?.status || 'ACTIVE').trim(),
        sort: Number(item?.sort || 0),
        progress: {
          status: String(progress?.status || 'NOT_STARTED').trim(),
          startCount: Number(progress?.startCount || 0),
          completeCount: Number(progress?.completeCount || 0),
          lastAccuracy: Number(progress?.lastAccuracy || 0),
          lastPracticedAt: String(progress?.lastPracticedAt || '').trim(),
        },
      }
    })
    .filter((item) => Boolean(item.methodCode))
    .sort((left, right) => left.sort - right.sort)
}

function normalizeRecommendationHistory(payload) {
  const source = payload && typeof payload === 'object' ? payload : {}
  const rows = Array.isArray(source.items) ? source.items : []
  const normalizeQuestionIdList = (value) => {
    const sourceRows = Array.isArray(value) ? value : []
    return Array.from(new Set(sourceRows.map((questionId) => String(questionId || '').trim()).filter(Boolean)))
  }
  return rows.map((item) => {
    const extJson = item?.extJson && typeof item.extJson === 'object' ? item.extJson : {}
    const practiceStrategy = String(item?.practiceStrategy || extJson.practiceStrategy || '').trim().toUpperCase()
    const recommendationStrategyCode = normalizeLearningMethodRecommendationStrategyCode(
      item?.recommendationStrategyCode
      || extJson.recommendationStrategyCode
      || recommendationStrategyCodeByPracticeStrategy(practiceStrategy, ''),
      '',
    )
    const recommendationStrategySource = normalizeLearningMethodRecommendationStrategySource(
      item?.recommendationStrategySource
      || extJson.strategySource,
      LEARNING_METHOD_RECOMMENDATION_STRATEGY_SOURCE.DEFAULT,
    )
    return {
      recommendationId: String(item?.recommendationId || '').trim(),
      sessionId: String(item?.sessionId || '').trim(),
      questionCount: Number(item?.questionCount || 0),
      questionIds: normalizeQuestionIdList(item?.questionIds),
      completedQuestionIds: normalizeQuestionIdList(item?.completedQuestionIds),
      skippedQuestionIds: normalizeQuestionIdList(item?.skippedQuestionIds),
      feedbackStatus: String(item?.feedbackStatus || 'PENDING').trim().toUpperCase() || 'PENDING',
      recommendedAt: String(item?.recommendedAt || '').trim(),
      feedbackAt: String(item?.feedbackAt || '').trim(),
      averageScore: Number(item?.averageScore || 0),
      studentProfileFitAverage: Number(item?.studentProfileFitAverage || 0),
      practiceStrategy,
      recommendationStrategyCode,
      recommendationStrategySource,
      studentProfile: normalizeRecommendationStudentProfile(item?.studentProfile),
      reasonTags: Array.isArray(item?.reasonTags) ? item.reasonTags.map((tag) => String(tag || '').trim()).filter(Boolean) : [],
      isRecentAutoFeedback: false,
      isFocusedByReturn: false,
    }
  }).filter((item) => Boolean(item.recommendationId))
}

function applyRecentFeedbackNoticeToHistory(rows, methodCode) {
  const historyRows = Array.isArray(rows) ? rows : []
  const notices = Array.isArray(recentFeedbackNotices.value)
    ? recentFeedbackNotices.value
    : []
  if (!notices.length) {
    return historyRows
  }
  const normalizedMethodCode = String(methodCode || '').trim().toUpperCase()
  let nextRows = historyRows
  const remainingNotices = []

  notices.forEach((notice) => {
    const noticeMethodCode = String(notice?.methodCode || '').trim().toUpperCase()
    if (noticeMethodCode && normalizedMethodCode && noticeMethodCode !== normalizedMethodCode) {
      remainingNotices.push(notice)
      return
    }
    const noticeRecommendationId = String(notice?.recommendationId || '').trim()
    const noticeFeedbackStatus = String(notice?.feedbackStatus || '').trim().toUpperCase()
    if (!noticeRecommendationId || !noticeFeedbackStatus) {
      return
    }

    let matched = false
    nextRows = nextRows.map((item) => {
      if (String(item?.recommendationId || '').trim() !== noticeRecommendationId) {
        return item
      }
      matched = true
      return {
        ...item,
        feedbackStatus: noticeFeedbackStatus,
        feedbackAt: String(notice?.updateTime || item.feedbackAt || '').trim(),
        isRecentAutoFeedback: true,
      }
    })

    if (!matched) {
      remainingNotices.push(notice)
    }
  })

  recentFeedbackNotices.value = remainingNotices
  return nextRows
}

function recommendationHistoryItemDomId(recommendationId) {
  const normalizedId = String(recommendationId || '').trim().replace(/[^a-zA-Z0-9_-]/g, '-')
  return `learning-method-recommendation-${normalizedId || 'unknown'}`
}

function applyRecommendationHistoryFocus(rows, recommendationId) {
  const targetRecommendationId = String(recommendationId || '').trim()
  if (!targetRecommendationId) {
    return rows.map((item) => ({
      ...item,
      isFocusedByReturn: false,
    }))
  }
  return rows.map((item) => ({
    ...item,
    isFocusedByReturn: String(item?.recommendationId || '').trim() === targetRecommendationId,
  }))
}

function recommendationHistoryFocusClass(item) {
  return item?.isFocusedByReturn ? 'recommendation-history-item--focus-return' : ''
}

function scrollToRecommendationHistoryItem(recommendationId) {
  const targetRecommendationId = String(recommendationId || '').trim()
  if (!targetRecommendationId || typeof window === 'undefined') {
    return
  }
  nextTick(() => {
    const element = document.getElementById(recommendationHistoryItemDomId(targetRecommendationId))
    if (!element || typeof element.scrollIntoView !== 'function') {
      return
    }
    element.scrollIntoView({
      behavior: 'smooth',
      block: 'center',
    })
  })
}

function clearRecentAutoFeedbackHighlight() {
  recommendationHistoryItems.value = recommendationHistoryItems.value.map((item) => ({
    ...item,
    isRecentAutoFeedback: false,
    isFocusedByReturn: false,
  }))
  if (typeof window !== 'undefined') {
    window.clearTimeout(recentAutoFeedbackHighlightTimer)
  }
  recentAutoFeedbackHighlightTimer = 0
}

function scheduleRecentAutoFeedbackHighlightReset() {
  if (typeof window === 'undefined') {
    return
  }
  const hasTransientHighlight = recommendationHistoryItems.value.some(
    (item) => item.isRecentAutoFeedback || item.isFocusedByReturn,
  )
  window.clearTimeout(recentAutoFeedbackHighlightTimer)
  recentAutoFeedbackHighlightTimer = 0
  if (!hasTransientHighlight) {
    return
  }
  recentAutoFeedbackHighlightTimer = window.setTimeout(() => {
    clearRecentAutoFeedbackHighlight()
  }, RECENT_AUTO_FEEDBACK_HIGHLIGHT_MS)
}

function statusTagType(status) {
  const normalizedStatus = String(status || '').trim().toUpperCase()
  if (normalizedStatus === 'COMPLETED') return 'success'
  if (normalizedStatus === 'IN_PROGRESS') return 'warning'
  return 'info'
}

function statusLabel(status) {
  const normalizedStatus = String(status || '').trim().toUpperCase()
  if (normalizedStatus === 'COMPLETED') return '已完成'
  if (normalizedStatus === 'IN_PROGRESS') return '进行中'
  return '未开始'
}

function feedbackStatusLabel(status) {
  const normalizedStatus = String(status || '').trim().toUpperCase()
  if (normalizedStatus === 'ACCEPTED') return '已采纳'
  if (normalizedStatus === 'PARTIAL') return '部分匹配'
  if (normalizedStatus === 'REJECTED') return '不匹配'
  if (normalizedStatus === 'COMPLETED') return '已完成'
  return '待反馈'
}

function feedbackStatusTagType(status) {
  const normalizedStatus = String(status || '').trim().toUpperCase()
  if (normalizedStatus === 'ACCEPTED' || normalizedStatus === 'COMPLETED') return 'success'
  if (normalizedStatus === 'PARTIAL') return 'warning'
  if (normalizedStatus === 'REJECTED') return 'danger'
  return 'info'
}

function recentAutoFeedbackTagType(status) {
  const normalizedStatus = String(status || '').trim().toUpperCase()
  if (normalizedStatus === 'PARTIAL') return 'warning'
  if (normalizedStatus === 'REJECTED') return 'danger'
  return 'success'
}

function recentAutoFeedbackTagLabel(status) {
  const normalizedStatus = String(status || '').trim().toUpperCase()
  if (normalizedStatus === 'ACCEPTED') return '刚刚回写：匹配很好'
  if (normalizedStatus === 'PARTIAL') return '刚刚回写：部分匹配'
  if (normalizedStatus === 'REJECTED') return '刚刚回写：不够匹配'
  return '刚刚回写'
}

function recentAutoFeedbackItemClass(item) {
  if (!item?.isRecentAutoFeedback) {
    return ''
  }
  const normalizedStatus = String(item?.feedbackStatus || '').trim().toUpperCase()
  if (normalizedStatus === 'PARTIAL') {
    return 'recommendation-history-item--recent-partial'
  }
  if (normalizedStatus === 'REJECTED') {
    return 'recommendation-history-item--recent-rejected'
  }
  return 'recommendation-history-item--recent-accepted'
}

function formatAccuracy(value) {
  const numeric = Number(value || 0)
  if (!Number.isFinite(numeric) || numeric <= 0) {
    return '0%'
  }
  const percent = numeric > 1 ? numeric : numeric * 100
  return `${Math.max(0, Math.min(100, Math.round(percent)))}%`
}

function formatScore(value) {
  const numeric = Number(value || 0)
  if (!Number.isFinite(numeric) || numeric <= 0) {
    return '0.00'
  }
  return numeric.toFixed(2)
}

function normalizeRecommendationStudentProfile(payload) {
  const source = payload && typeof payload === 'object' ? payload : {}
  const tags = Array.isArray(source.tags)
    ? Array.from(new Set(source.tags.map((tag) => String(tag || '').trim()).filter(Boolean)))
    : []
  const questionTypeWeights = source.questionTypeWeights && typeof source.questionTypeWeights === 'object'
    ? source.questionTypeWeights
    : {}
  return {
    tags,
    difficultyPreference: String(source.difficultyPreference || '').trim().toLowerCase(),
    questionTypeWeights,
  }
}

const recommendationStudentProfile = computed(() =>
  normalizeRecommendationStudentProfile(recommendationPayload.value?.scoreSummary?.studentProfile),
)

function recommendationTagLabel(tag) {
  const normalizedTag = String(tag || '').trim().toLowerCase()
  const labelMap = {
    concept: '概念理解',
    calculation: '计算推导',
    application: '应用场景',
    memory: '记忆巩固',
    review: '错因复盘',
    speed: '提速训练',
  }
  return labelMap[normalizedTag] || normalizedTag || '--'
}

function recommendationReasonTagLabel(tag) {
  const normalizedTag = String(tag || '').trim().toLowerCase()
  const labelMap = {
    method_fit: '方法匹配',
    weakness_hit: '薄弱点命中',
    difficulty_aligned: '难度对齐',
    fresh_question: '新题优先',
    profile_fit: '画像匹配',
    balanced_mix: '均衡混合',
  }
  return labelMap[normalizedTag] || normalizedTag || '--'
}

function recommendationReasonTagType(tag) {
  const normalizedTag = String(tag || '').trim().toLowerCase()
  if (normalizedTag === 'profile_fit' || normalizedTag === 'method_fit') return 'success'
  if (normalizedTag === 'weakness_hit' || normalizedTag === 'difficulty_aligned') return 'warning'
  return 'info'
}

function recommendationDifficultyPreferenceLabel(value) {
  const normalizedValue = String(value || '').trim().toLowerCase()
  if (normalizedValue === 'easy') return '基础巩固'
  if (normalizedValue === 'hard') return '冲刺突破'
  return '均衡进阶'
}

function recommendationQuestionTypeLabel(value) {
  const normalizedValue = String(value || '').trim().toLowerCase()
  const labelMap = {
    single_choice: '单选题',
    multiple_choice: '多选题',
    judge: '判断题',
    subjective: '主观题',
  }
  return labelMap[normalizedValue] || value || '--'
}

function recommendationQuestionTypeWeightSummary(profile) {
  const weights = profile?.questionTypeWeights && typeof profile.questionTypeWeights === 'object'
    ? profile.questionTypeWeights
    : {}
  const rows = Object.entries(weights)
    .map(([questionType, weight]) => ({
      questionType: recommendationQuestionTypeLabel(questionType),
      weight: Number(weight || 0),
    }))
    .filter((item) => item.weight > 0)
    .sort((left, right) => right.weight - left.weight)
  if (!rows.length) {
    return '--'
  }
  return rows.slice(0, 2).map((item) => `${item.questionType} ${Math.round(item.weight * 100)}%`).join('、')
}

function recommendationStrategyPresetByCode(value) {
  const normalizedCode = normalizeLearningMethodRecommendationStrategyCode(value)
  return RECOMMENDATION_STRATEGY_PRESETS[normalizedCode]
}

function recommendationStrategyLabel(strategyCode) {
  const normalizedCode = normalizeLearningMethodRecommendationStrategyCode(strategyCode, '')
  if (!normalizedCode) {
    return '--'
  }
  return recommendationStrategyPresetByCode(normalizedCode)?.label || '--'
}

function recommendationStrategySourceLabel(source) {
  return learningMethodRecommendationStrategySourceLabel(source)
}

const recommendationStrategyOptions = computed(() =>
  Object.values(RECOMMENDATION_STRATEGY_PRESETS),
)

const recommendationPayloadStrategyCode = computed(() =>
  resolveLearningMethodRecommendationStrategyFromPayload(recommendationPayload.value, ''),
)

const recommendationPayloadStrategySource = computed(() =>
  resolveLearningMethodRecommendationStrategySourceFromPayload(recommendationPayload.value, ''),
)

const activeRecommendationStrategyCode = computed(() =>
  normalizeLearningMethodRecommendationStrategyCode(
    recommendationPayloadStrategyCode.value || selectedRecommendationStrategyCode.value,
    selectedRecommendationStrategyCode.value,
  ),
)

const activeRecommendationStrategyPreset = computed(() =>
  recommendationStrategyPresetByCode(activeRecommendationStrategyCode.value),
)

const activeRecommendationStrategySource = computed(() =>
  normalizeLearningMethodRecommendationStrategySource(
    recommendationPayloadStrategySource.value || selectedRecommendationStrategySource.value,
    selectedRecommendationStrategySource.value,
  ),
)

const selectedRecommendationStrategySourceLabel = computed(() =>
  learningMethodRecommendationStrategySourceLabel(activeRecommendationStrategySource.value),
)

function parseDateTimestamp(value) {
  const normalizedValue = String(value || '').trim()
  if (!normalizedValue) {
    return 0
  }
  const date = new Date(normalizedValue)
  if (Number.isNaN(date.getTime())) {
    return 0
  }
  return date.getTime()
}

function formatTrendDate(value) {
  const timestamp = parseDateTimestamp(value)
  if (!timestamp) {
    return '--'
  }
  const date = new Date(timestamp)
  return date.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
}

function normalizeProfileFit(value) {
  const numeric = Number(value || 0)
  if (!Number.isFinite(numeric) || numeric <= 0) {
    return 0
  }
  return Math.max(0, Math.min(1, numeric > 1 ? numeric / 100 : numeric))
}

const recommendationTrendThresholds = [0.6, 0.75, 0.85]

const recommendationHistoryProfileTrend = computed(() => {
  const rows = Array.isArray(recommendationHistoryItems.value) ? recommendationHistoryItems.value : []
  const points = rows.map((item, index) => ({
    key: `${item.recommendationId}-${index}`,
    recommendationId: String(item?.recommendationId || '').trim(),
    recommendedAt: String(item?.recommendedAt || '').trim(),
    fit: normalizeProfileFit(item?.studentProfileFitAverage),
    timestamp: parseDateTimestamp(item?.recommendedAt),
  }))
  if (!points.length) {
    return {
      points: [],
      startFit: 0,
      endFit: 0,
      deltaFit: 0,
    }
  }
  points.sort((left, right) => {
    const leftTime = Number(left.timestamp || 0)
    const rightTime = Number(right.timestamp || 0)
    if (leftTime !== rightTime) {
      return leftTime - rightTime
    }
    return String(left.recommendationId || '').localeCompare(String(right.recommendationId || ''))
  })
  const startFit = Number(points[0]?.fit || 0)
  const endFit = Number(points[points.length - 1]?.fit || 0)
  return {
    points: points.slice(-8),
    startFit,
    endFit,
    deltaFit: endFit - startFit,
  }
})

const trendSwitchSuggestion = computed(() =>
  recommendationTrendSwitchSuggestion(recommendationHistoryProfileTrend.value),
)

const recommendationHistorySourceInsights = computed(() =>
  computeLearningMethodSourceInsights(recommendationHistoryItems.value),
)

const recommendationHistorySourceSummary = computed(() =>
  summarizeLearningMethodSourceInsights(recommendationHistorySourceInsights.value),
)

function recommendationTrendSummaryText(trendPayload) {
  const trend = trendPayload && typeof trendPayload === 'object' ? trendPayload : {}
  const points = Array.isArray(trend.points) ? trend.points : []
  if (points.length < 2) {
    return '历史数据不足 2 次，趋势将在后续推荐中自动更新。'
  }
  const delta = Number(trend.deltaFit || 0)
  if (delta >= 0.05) {
    return `匹配趋势上升 ${Math.round(delta * 100)}%，最近推荐与当前画像更贴合。`
  }
  if (delta <= -0.05) {
    return `匹配趋势下降 ${Math.round(Math.abs(delta) * 100)}%，建议复核题型偏好后再继续推荐。`
  }
  return '匹配趋势整体稳定，建议继续保持当前学习节奏。'
}

function trendBarStyle(fitValue) {
  const ratio = Math.max(0, Math.min(1, Number(fitValue || 0)))
  return {
    width: `${Math.round(ratio * 100)}%`,
  }
}

function trendThresholdStyle(threshold) {
  const ratio = Math.max(0, Math.min(1, Number(threshold || 0)))
  return {
    left: `${Math.round(ratio * 100)}%`,
  }
}

function sourceInsightBarStyle(value) {
  const ratio = Math.max(0, Math.min(1, Number(value || 0)))
  return {
    width: `${Math.round(ratio * 100)}%`,
  }
}

function sourceInsightRecommendedStrategyLabel(insight) {
  const normalizedInsight = insight && typeof insight === 'object' ? insight : {}
  const strategyCode = normalizeLearningMethodRecommendationStrategyCode(
    normalizedInsight.recommendedStrategyCode,
    '',
  )
  if (!strategyCode) {
    return recommendationStrategyLabel(selectedRecommendationStrategyCode.value)
  }
  return recommendationStrategyLabel(strategyCode)
}

function recommendationTrendSwitchSuggestion(trendPayload) {
  const trend = trendPayload && typeof trendPayload === 'object' ? trendPayload : {}
  const points = Array.isArray(trend.points) ? trend.points : []
  if (points.length < 2) {
    return {
      type: 'info',
      strategyCode: 'BALANCED',
      title: '策略建议：继续收集样本',
      detail: '推荐历史不足，先保持均衡进阶策略并继续完成 2-3 次题包。',
    }
  }
  const endFit = Number(trend.endFit || 0)
  const deltaFit = Number(trend.deltaFit || 0)
  if (endFit >= 0.85 && deltaFit >= 0.05) {
    return {
      type: 'success',
      strategyCode: 'SPRINT',
      title: '策略建议：切到冲刺突破',
      detail: '画像匹配已进入高位且趋势向上，可提高主观题与综合应用题占比。',
    }
  }
  if (endFit < 0.6 || deltaFit <= -0.08) {
    return {
      type: 'warning',
      strategyCode: 'FOUNDATION',
      title: '策略建议：回到基础巩固',
      detail: '当前匹配度偏低或下降明显，建议先强化概念与记忆题型。',
    }
  }
  return {
    type: 'info',
    strategyCode: 'BALANCED',
    title: '策略建议：保持均衡进阶',
    detail: '匹配度处于中位区间，建议维持当前题型结构并观察后续趋势。',
  }
}

function formatDateTime(value) {
  const normalized = String(value || '').trim()
  if (!normalized) {
    return '--'
  }
  const date = new Date(normalized)
  if (Number.isNaN(date.getTime())) {
    return normalized
  }
  return date.toLocaleString('zh-CN', { hour12: false })
}

function returnSummaryMessageType(feedbackStatus) {
  const normalizedStatus = String(feedbackStatus || '').trim().toUpperCase()
  if (normalizedStatus === 'ACCEPTED') {
    return 'success'
  }
  if (normalizedStatus === 'PARTIAL') {
    return 'warning'
  }
  if (normalizedStatus === 'REJECTED') {
    return 'warning'
  }
  return 'info'
}

function showPracticeReturnSummary(historyItem) {
  const item = historyItem && typeof historyItem === 'object' ? historyItem : {}
  const totalQuestionCount = Math.max(
    Number(item.questionCount || 0),
    Array.isArray(item.questionIds) ? item.questionIds.length : 0,
  )
  const completedCount = Array.isArray(item.completedQuestionIds) ? item.completedQuestionIds.length : 0
  const remainingCount = Math.max(totalQuestionCount - completedCount, 0)
  const statusText = feedbackStatusLabel(item.feedbackStatus)
  const message = `本轮已回到学习方法页：共 ${totalQuestionCount} 题，已完成 ${completedCount} 题，剩余 ${remainingCount} 题，当前状态 ${statusText}。`
  const type = returnSummaryMessageType(item.feedbackStatus)
  if (type === 'success') {
    ElMessage.success(message)
    return
  }
  if (type === 'warning') {
    ElMessage.warning(message)
    return
  }
  ElMessage.info(message)
}

async function clearPracticeReturnFlag() {
  if (!isReturnFromPractice.value) {
    return
  }
  const nextQuery = { ...(route.query || {}) }
  delete nextQuery.fromPracticeReturn
  try {
    await router.replace({
      path: route.path,
      query: nextQuery,
    })
  } catch (error) {
    // Ignore query cleanup failure and keep the page usable.
  }
}

function recommendationQuestions(payload) {
  const rows = Array.isArray(payload?.questions) ? payload.questions : []
  return rows.map((item) => ({
    questionId: String(item?.questionId || '').trim(),
    type: String(item?.type || '').trim(),
    difficulty: String(item?.difficulty || '').trim(),
    score: Number(item?.score || 0),
    reasonTags: Array.isArray(item?.reasonTags) ? item.reasonTags : [],
    scoreBreakdown: item?.scoreBreakdown && typeof item.scoreBreakdown === 'object' ? item.scoreBreakdown : {},
  })).filter((item) => Boolean(item.questionId))
}

const recommendationQuestionIds = computed(() =>
  recommendationQuestions(recommendationPayload.value)
    .map((item) => item.questionId)
    .filter(Boolean),
)

const canNavigateToRecommendationPractice = computed(() =>
  recommendationQuestionIds.value.length > 0 && !recommendationLoading.value,
)

function normalizeAdaptiveMastery(value) {
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) {
    return ''
  }
  const percentValue = numeric <= 1 ? numeric * 100 : numeric
  return String(Math.max(0, Math.min(100, Number(percentValue.toFixed(2)))))
}

async function handleNavigateToRecommendationPractice() {
  const subjectCode = currentSubjectCode.value
  if (!subjectCode) {
    ElMessage.warning('当前未选择学科，请先选择学科后再去做题。')
    return
  }
  if (!recommendationQuestionIds.value.length) {
    ElMessage.warning('当前推荐题包暂无可练题目，请先生成推荐题包。')
    return
  }

  const methodCode = String(selectedCode.value || recommendationPayload.value?.methodCode || '').trim()
  const adaptiveMastery = normalizeAdaptiveMastery(recommendationPayload.value?.scoreSummary?.averageScore)
  const nextLocation = buildStudentPracticeRouteLocation({
    module: STUDENT_PRACTICE_MODULE.FREE,
    subjectCode,
    adaptiveQuestionIds: recommendationQuestionIds.value,
    adaptiveDimension: methodCode || subjectCode,
    adaptiveMastery,
    practiceSource: STUDENT_PRACTICE_SOURCE.LEARNING_METHOD,
    practiceSourceLabel: '学习方法推荐题包',
    extraQuery: {
      immersive: '1',
      learningMethodCode: methodCode,
      learningMethodRecommendationId: String(recommendationPayload.value?.recommendationId || '').trim(),
      learningMethodSessionId: String(recommendationPayload.value?.sessionId || currentSessionId.value || '').trim(),
    },
  })

  try {
    await router.push(nextLocation)
  } catch (error) {
    ElMessage.error(String(error?.message || '跳转刷题页失败，请稍后重试。'))
  }
}

function resolveHistoryRemainingQuestionIds(item) {
  const questionIds = Array.isArray(item?.questionIds)
    ? item.questionIds.map((questionId) => String(questionId || '').trim()).filter(Boolean)
    : []
  if (!questionIds.length) {
    return []
  }
  const completedQuestionIdSet = new Set(
    (Array.isArray(item?.completedQuestionIds) ? item.completedQuestionIds : [])
      .map((questionId) => String(questionId || '').trim())
      .filter(Boolean),
  )
  if (!completedQuestionIdSet.size) {
    return questionIds
  }
  const remainingQuestionIds = questionIds.filter((questionId) => !completedQuestionIdSet.has(questionId))
  return remainingQuestionIds
}

function historyRemainingQuestionCount(item) {
  return resolveHistoryRemainingQuestionIds(item).length
}

function isContinueHistoryFeedbackStatus(status) {
  const normalizedFeedbackStatus = String(status || '').trim().toUpperCase()
  return normalizedFeedbackStatus === 'PARTIAL' || normalizedFeedbackStatus === 'PENDING'
}

function canContinueHistoryRecommendation(item) {
  if (!isContinueHistoryFeedbackStatus(item?.feedbackStatus)) {
    return false
  }
  return historyRemainingQuestionCount(item) > 0
}

function continueHistoryRecommendationButtonLabel(item) {
  const normalizedFeedbackStatus = String(item?.feedbackStatus || '').trim().toUpperCase()
  if (normalizedFeedbackStatus === 'PARTIAL') {
    return '继续完成剩余题目'
  }
  return '去完成推荐题目'
}

async function handleContinueHistoryRecommendation(item) {
  const subjectCode = currentSubjectCode.value
  if (!subjectCode) {
    ElMessage.warning('当前未选择学科，请先选择学科后再去做题。')
    return
  }
  const remainingQuestionIds = resolveHistoryRemainingQuestionIds(item)
  if (!remainingQuestionIds.length) {
    ElMessage.warning('该推荐题包暂无可继续题目，请重新生成题包。')
    return
  }

  const recommendationId = String(item?.recommendationId || '').trim()
  historyPracticeLoadingRecommendationId.value = recommendationId
  const methodCode = String(selectedCode.value || detailPayload.value?.method?.methodCode || '').trim()
  const adaptiveMastery = normalizeAdaptiveMastery(item?.averageScore)
  const practiceSourceLabel = String(item?.feedbackStatus || '').trim().toUpperCase() === 'PARTIAL'
    ? '学习方法推荐题包（继续）'
    : '学习方法推荐题包'
  const nextLocation = buildStudentPracticeRouteLocation({
    module: STUDENT_PRACTICE_MODULE.FREE,
    subjectCode,
    adaptiveQuestionIds: remainingQuestionIds,
    adaptiveDimension: methodCode || subjectCode,
    adaptiveMastery,
    practiceSource: STUDENT_PRACTICE_SOURCE.LEARNING_METHOD,
    practiceSourceLabel,
    extraQuery: {
      immersive: '1',
      learningMethodCode: methodCode,
      learningMethodRecommendationId: recommendationId,
      learningMethodSessionId: String(item?.sessionId || currentSessionId.value || '').trim(),
    },
  })

  try {
    await router.push(nextLocation)
  } catch (error) {
    ElMessage.error(String(error?.message || '跳转刷题页失败，请稍后重试。'))
  } finally {
    historyPracticeLoadingRecommendationId.value = ''
  }
}

async function fetchMethods({ keepSelected = true } = {}) {
  loading.value = true
  listError.value = ''
  try {
    const payload = await fetchLearningMethodList({ status: 'ACTIVE' })
    methodItems.value = normalizeMethodList(payload)
    if (!methodItems.value.length) {
      selectedCode.value = ''
      detailPayload.value = null
      detailError.value = ''
      recommendationPayload.value = null
      recommendationHistoryItems.value = []
      return
    }

    const preferredCodeFromRoute = focusedHistoryMethodCode.value
    const fallbackCode = String(methodItems.value[0]?.methodCode || '').trim()
    const candidateCode = keepSelected && selectedCode.value
      ? selectedCode.value
      : preferredCodeFromRoute || fallbackCode

    if (candidateCode && methodItems.value.some((item) => item.methodCode === candidateCode)) {
      await selectMethod(candidateCode)
      return
    }

    selectedCode.value = ''
    detailPayload.value = null
  } catch (error) {
    listError.value = String(error?.response?.data?.message || error?.message || '学习方法列表加载失败，请稍后重试。')
  } finally {
    loading.value = false
  }
}

async function fetchRecommendationHistory(methodCode, { silent = false } = {}) {
  const normalizedCode = String(methodCode || '').trim()
  if (!normalizedCode) {
    recommendationHistoryItems.value = []
    return
  }

  if (!silent) {
    recommendationHistoryLoading.value = true
  }
  recommendationHistoryError.value = ''
  try {
    const payload = await fetchLearningMethodQuestionPackRecommendationHistory(normalizedCode, { limit: 10 })
    const normalizedItems = normalizeRecommendationHistory(payload)
    recommendationHistoryItems.value = applyRecentFeedbackNoticeToHistory(normalizedItems, normalizedCode)
    const focusRecommendationIdFromRoute = focusedHistoryRecommendationId.value
    const focusSessionIdFromRoute = focusedHistorySessionId.value
    const recentAutoFeedbackRecommendationId = String(
      recommendationHistoryItems.value.find((item) => item.isRecentAutoFeedback)?.recommendationId || '',
    ).trim()
    const focusRecommendationId = focusRecommendationIdFromRoute || recentAutoFeedbackRecommendationId
    recommendationHistoryItems.value = applyRecommendationHistoryFocus(
      recommendationHistoryItems.value,
      focusRecommendationId,
    )
    if (focusRecommendationId) {
      scrollToRecommendationHistoryItem(focusRecommendationId)
    }
    if (
      isReturnFromPractice.value
      && returnSummaryHandledRecommendationId.value !== (
        focusRecommendationId
        || (focusSessionIdFromRoute ? `session:${focusSessionIdFromRoute}` : '__return_from_practice__')
      )
    ) {
      const returnSummaryKey = focusRecommendationId
        || (focusSessionIdFromRoute ? `session:${focusSessionIdFromRoute}` : '__return_from_practice__')
      let returnSummaryItem = recommendationHistoryItems.value.find(
        (item) => String(item?.recommendationId || '').trim() === focusRecommendationId,
      )
      if (!returnSummaryItem && focusSessionIdFromRoute) {
        returnSummaryItem = recommendationHistoryItems.value.find(
          (item) => String(item?.sessionId || '').trim() === focusSessionIdFromRoute,
        )
      }
      if (returnSummaryItem) {
        showPracticeReturnSummary(returnSummaryItem)
      } else {
        ElMessage.info('已返回学习方法页，推荐历史同步中，请稍后查看本轮完成情况。')
      }
      returnSummaryHandledRecommendationId.value = returnSummaryKey
      void clearPracticeReturnFlag()
    }
    scheduleRecentAutoFeedbackHighlightReset()
    const activeRecommendationId = String(recommendationPayload.value?.recommendationId || '').trim()
    const activeHistoryItem = recommendationHistoryItems.value.find(
      (item) => String(item?.recommendationId || '').trim() === activeRecommendationId,
    )
    if (activeHistoryItem && recommendationPayload.value && typeof recommendationPayload.value === 'object') {
      recommendationPayload.value = {
        ...recommendationPayload.value,
        recommendationLog: {
          ...(recommendationPayload.value.recommendationLog || {}),
          feedbackStatus: activeHistoryItem.feedbackStatus || recommendationPayload.value?.recommendationLog?.feedbackStatus || 'PENDING',
          feedbackAt: activeHistoryItem.feedbackAt || recommendationPayload.value?.recommendationLog?.feedbackAt || '',
        },
      }
    }
  } catch (error) {
    recommendationHistoryItems.value = []
    recommendationHistoryError.value = String(error?.response?.data?.message || error?.message || '推荐历史加载失败，请稍后重试。')
  } finally {
    recommendationHistoryLoading.value = false
  }
}

async function selectMethod(methodCode) {
  const normalizedCode = String(methodCode || '').trim()
  if (!normalizedCode) {
    return
  }
  selectedCode.value = normalizedCode
  restoreRecommendationStrategyState(normalizedCode)
  detailLoading.value = true
  detailError.value = ''
  recommendationError.value = ''
  recommendationPayload.value = null
  try {
    detailPayload.value = await fetchLearningMethodDetail(normalizedCode)
    await fetchRecommendationHistory(normalizedCode, { silent: true })
  } catch (error) {
    detailPayload.value = null
    detailError.value = String(error?.response?.data?.message || error?.message || '学习方法详情加载失败，请稍后重试。')
  } finally {
    detailLoading.value = false
  }
}

async function handleStart(methodCode) {
  const normalizedCode = String(methodCode || '').trim()
  if (!normalizedCode) {
    return
  }

  actionLoadingCode.value = `start:${normalizedCode}`
  try {
    await startLearningMethodSession(normalizedCode, {
      sourceType: 'LEARNING_METHOD_PAGE',
      practiceStrategy: 'DEFAULT',
      subjectCode: currentSubjectCode.value,
    })
    ElMessage.success('已开始练习，建议按步骤完成一轮。')
    await Promise.all([
      selectMethod(normalizedCode),
      fetchMethods({ keepSelected: true }),
    ])
  } catch (error) {
    ElMessage.error(String(error?.response?.data?.message || error?.message || '启动学习方法失败，请重试。'))
  } finally {
    actionLoadingCode.value = ''
  }
}

async function handleComplete(methodCode) {
  const normalizedCode = String(methodCode || '').trim()
  if (!normalizedCode) {
    return
  }

  const fallbackSessionId = `learning-method-session-${Date.now()}`
  actionLoadingCode.value = `complete:${normalizedCode}`
  try {
    await completeLearningMethodSession(normalizedCode, {
      sessionId: currentSessionId.value || fallbackSessionId,
      accuracy: Number(selectedProgress.value?.lastAccuracy || 0),
      durationSec: 0,
      reviewSummary: '学生在学习方法页标记本次学习完成。',
    })
    ElMessage.success('已标记完成，本次学习进度已更新。')
    await Promise.all([
      selectMethod(normalizedCode),
      fetchMethods({ keepSelected: true }),
    ])
  } catch (error) {
    ElMessage.error(String(error?.response?.data?.message || error?.message || '提交完成失败，请稍后重试。'))
  } finally {
    actionLoadingCode.value = ''
  }
}

function recommendationRequestPayloadByStrategy(strategyCode, strategySource) {
  const preset = recommendationStrategyPresetByCode(strategyCode)
  return {
    questionCount: Number(preset.questionCount || 12),
    subjectCode: currentSubjectCode.value,
    sourceType: 'LEARNING_METHOD_PAGE',
    sessionId: currentSessionId.value,
    difficultyPreference: String(preset.difficultyPreference || '').trim(),
    practiceStrategy: String(preset.practiceStrategy || '').trim(),
    strategySource: normalizeLearningMethodRecommendationStrategySource(
      strategySource,
      LEARNING_METHOD_RECOMMENDATION_STRATEGY_SOURCE.DEFAULT,
    ),
  }
}

async function syncRecommendationStrategyQuery(methodCode, strategyCode, strategySource) {
  const normalizedMethodCode = String(methodCode || '').trim().toUpperCase()
  if (!normalizedMethodCode) {
    return
  }
  const normalizedStrategyCode = normalizeLearningMethodRecommendationStrategyCode(strategyCode, '')
  if (!normalizedStrategyCode) {
    return
  }
  const normalizedStrategySource = normalizeLearningMethodRecommendationStrategySource(
    strategySource,
    LEARNING_METHOD_RECOMMENDATION_STRATEGY_SOURCE.DEFAULT,
  )
  const currentMethodCode = String(route.query.learningMethodCode || '').trim().toUpperCase()
  const currentStrategyCode = normalizeLearningMethodRecommendationStrategyCode(
    route.query.recommendationStrategy,
    '',
  )
  const currentStrategySource = normalizeLearningMethodRecommendationStrategySource(
    route.query.recommendationStrategySource,
    '',
  )
  if (
    currentMethodCode === normalizedMethodCode
    && currentStrategyCode === normalizedStrategyCode
    && currentStrategySource === normalizedStrategySource
  ) {
    return
  }

  const nextQuery = {
    ...(route.query || {}),
    learningMethodCode: normalizedMethodCode,
    recommendationStrategy: normalizedStrategyCode,
    recommendationStrategySource: normalizedStrategySource,
  }
  try {
    await router.replace({
      path: route.path,
      query: nextQuery,
    })
  } catch (error) {
    // Ignore query sync failures and keep the page usable.
  }
}

function applyRecommendationStrategyState(
  methodCode,
  strategyCode,
  {
    source = LEARNING_METHOD_RECOMMENDATION_STRATEGY_SOURCE.DEFAULT,
    persist = true,
    syncQuery = true,
  } = {},
) {
  const normalizedMethodCode = String(methodCode || '').trim().toUpperCase()
  const normalizedStrategyCode = normalizeLearningMethodRecommendationStrategyCode(
    strategyCode,
    selectedRecommendationStrategyCode.value,
  )
  const normalizedStrategySource = normalizeLearningMethodRecommendationStrategySource(
    source,
    LEARNING_METHOD_RECOMMENDATION_STRATEGY_SOURCE.DEFAULT,
  )

  selectedRecommendationStrategyCode.value = normalizedStrategyCode
  selectedRecommendationStrategySource.value = normalizedStrategySource

  if (persist && normalizedMethodCode) {
    savePersistedLearningMethodRecommendationStrategy({
      subjectCode: currentSubjectCode.value,
      methodCode: normalizedMethodCode,
      strategyCode: normalizedStrategyCode,
      source: normalizedStrategySource,
    })
  }
  if (syncQuery && normalizedMethodCode) {
    void syncRecommendationStrategyQuery(
      normalizedMethodCode,
      normalizedStrategyCode,
      normalizedStrategySource,
    )
  }
}

function restoreRecommendationStrategyState(methodCode) {
  const normalizedMethodCode = String(methodCode || '').trim().toUpperCase()
  if (!normalizedMethodCode) {
    return
  }
  const queryMethodCode = String(route.query.learningMethodCode || '').trim().toUpperCase()
  const queryStrategyCode = normalizeLearningMethodRecommendationStrategyCode(
    route.query.recommendationStrategy,
    '',
  )
  if (queryStrategyCode && (!queryMethodCode || queryMethodCode === normalizedMethodCode)) {
    applyRecommendationStrategyState(normalizedMethodCode, queryStrategyCode, {
      source: normalizeLearningMethodRecommendationStrategySource(
        route.query.recommendationStrategySource,
        LEARNING_METHOD_RECOMMENDATION_STRATEGY_SOURCE.DEFAULT,
      ),
      persist: true,
      syncQuery: true,
    })
    return
  }

  const persistedStrategy = loadPersistedLearningMethodRecommendationStrategy({
    subjectCode: currentSubjectCode.value,
    methodCode: normalizedMethodCode,
  })
  if (persistedStrategy?.strategyCode) {
    applyRecommendationStrategyState(normalizedMethodCode, persistedStrategy.strategyCode, {
      source: persistedStrategy.source,
      persist: false,
      syncQuery: true,
    })
    return
  }

  applyRecommendationStrategyState(normalizedMethodCode, 'BALANCED', {
    source: LEARNING_METHOD_RECOMMENDATION_STRATEGY_SOURCE.DEFAULT,
    persist: false,
    syncQuery: true,
  })
}

async function handleRecommendQuestionPack(methodCode, options = {}) {
  const normalizedCode = String(methodCode || '').trim()
  if (!normalizedCode) {
    return
  }
  const strategyCode = normalizeLearningMethodRecommendationStrategyCode(
    options?.strategyCode,
    selectedRecommendationStrategyCode.value,
  )
  const strategySource = normalizeLearningMethodRecommendationStrategySource(
    options?.strategySource,
    selectedRecommendationStrategySource.value,
  )
  applyRecommendationStrategyState(normalizedCode, strategyCode, {
    source: strategySource,
    persist: true,
    syncQuery: true,
  })
  const requestPayload = recommendationRequestPayloadByStrategy(strategyCode, strategySource)

  recommendationLoading.value = true
  recommendationError.value = ''
  recommendationPayload.value = null
  try {
    recommendationPayload.value = await fetchLearningMethodQuestionPackRecommendation(normalizedCode, requestPayload)
    const payloadStrategyCode = resolveLearningMethodRecommendationStrategyFromPayload(recommendationPayload.value, '')
    const payloadStrategySource = resolveLearningMethodRecommendationStrategySourceFromPayload(
      recommendationPayload.value,
      strategySource,
    )
    if (payloadStrategyCode) {
      applyRecommendationStrategyState(normalizedCode, payloadStrategyCode, {
        source: payloadStrategySource,
        persist: true,
        syncQuery: true,
      })
    }
    ElMessage.success('已生成推荐题包，请先做一轮再反馈效果。')
    await fetchRecommendationHistory(normalizedCode)
  } catch (error) {
    recommendationPayload.value = null
    recommendationError.value = String(error?.response?.data?.message || error?.message || '推荐题包生成失败，请稍后重试。')
    ElMessage.error(recommendationError.value)
  } finally {
    recommendationLoading.value = false
  }
}

function handleSelectRecommendationStrategy(strategyCode) {
  applyRecommendationStrategyState(selectedCode.value, strategyCode, {
    source: LEARNING_METHOD_RECOMMENDATION_STRATEGY_SOURCE.MANUAL,
    persist: true,
    syncQuery: true,
  })
}

async function handleRunRecommendationByCurrentStrategy() {
  const normalizedCode = String(selectedCode.value || '').trim()
  if (!normalizedCode) {
    ElMessage.warning('请先选择学习方法后再切换推荐策略。')
    return
  }
  await handleRecommendQuestionPack(normalizedCode, {
    strategyCode: selectedRecommendationStrategyCode.value,
    strategySource: selectedRecommendationStrategySource.value,
  })
}

async function handleRunRecommendationBySourceInsight(insight) {
  const normalizedCode = String(selectedCode.value || '').trim()
  if (!normalizedCode) {
    ElMessage.warning('请先选择学习方法后再按来源执行。')
    return
  }
  const normalizedInsight = insight && typeof insight === 'object' ? insight : {}
  const strategyCode = normalizeLearningMethodRecommendationStrategyCode(
    normalizedInsight.recommendedStrategyCode,
    selectedRecommendationStrategyCode.value,
  )
  const strategySource = normalizeLearningMethodRecommendationStrategySource(
    normalizedInsight.source,
    selectedRecommendationStrategySource.value,
  )
  await handleRecommendQuestionPack(normalizedCode, {
    strategyCode,
    strategySource,
  })
}

function handleResetRecommendationStrategyToDefault() {
  const normalizedCode = String(selectedCode.value || '').trim()
  if (!normalizedCode) {
    ElMessage.warning('请先选择学习方法后再恢复默认策略。')
    return
  }
  applyRecommendationStrategyState(normalizedCode, 'BALANCED', {
    source: LEARNING_METHOD_RECOMMENDATION_STRATEGY_SOURCE.DEFAULT,
    persist: true,
    syncQuery: true,
  })
  ElMessage.success('已恢复系统默认策略，下一轮可直接重算题包。')
}

async function handleApplySuggestedRecommendationStrategy() {
  const normalizedCode = String(selectedCode.value || '').trim()
  if (!normalizedCode) {
    ElMessage.warning('请先选择学习方法后再执行策略建议。')
    return
  }
  const suggestion = trendSwitchSuggestion.value || {}
  const suggestedStrategyCode = normalizeLearningMethodRecommendationStrategyCode(
    suggestion.strategyCode,
    selectedRecommendationStrategyCode.value,
  )
  await handleRecommendQuestionPack(normalizedCode, {
    strategyCode: suggestedStrategyCode,
    strategySource: LEARNING_METHOD_RECOMMENDATION_STRATEGY_SOURCE.SUGGESTED,
  })
}

async function handleRecommendationFeedback(status) {
  const normalizedCode = String(selectedCode.value || '').trim()
  if (!normalizedCode || !currentRecommendationId.value) {
    return
  }

  feedbackLoading.value = true
  feedbackStatus.value = String(status || '').trim().toUpperCase()
  try {
    const response = await submitLearningMethodQuestionPackFeedback(normalizedCode, {
      recommendationId: currentRecommendationId.value,
      sessionId: String(recommendationPayload.value?.sessionId || currentSessionId.value || '').trim(),
      feedbackStatus: feedbackStatus.value,
      isHelpful: feedbackStatus.value !== 'REJECTED',
      note: feedbackStatus.value === 'REJECTED'
        ? '学生反馈题包与当前学习状态不匹配。'
        : '学生已在学习方法页提交推荐反馈。',
    })
    if (recommendationPayload.value && typeof recommendationPayload.value === 'object') {
      recommendationPayload.value = {
        ...recommendationPayload.value,
        recommendationLog: {
          ...(recommendationPayload.value.recommendationLog || {}),
          feedbackStatus: response?.feedbackStatus || feedbackStatus.value,
          feedbackAt: response?.feedbackAt || '',
        },
      }
    }
    ElMessage.success('推荐反馈已提交，系统会用于后续匹配优化。')
    await Promise.all([
      selectMethod(normalizedCode),
      fetchRecommendationHistory(normalizedCode),
    ])
  } catch (error) {
    ElMessage.error(String(error?.response?.data?.message || error?.message || '提交推荐反馈失败，请稍后重试。'))
  } finally {
    feedbackLoading.value = false
    feedbackStatus.value = ''
  }
}

onMounted(() => {
  recentFeedbackNotices.value = consumeAllLearningMethodFeedbackNotices()
  const noticeCount = recentFeedbackNotices.value.length
  if (noticeCount > 1) {
    ElMessage.success(`系统已同步 ${noticeCount} 条推荐题包反馈回写结果。`)
  } else if (noticeCount === 1) {
    const onlyStatus = String(recentFeedbackNotices.value[0]?.feedbackStatus || '').trim().toUpperCase()
    if (onlyStatus === 'ACCEPTED') {
      ElMessage.success('系统已自动记录推荐题包“匹配很好”反馈。')
    } else if (onlyStatus === 'PARTIAL') {
      ElMessage.info('系统已记录本次推荐题包“部分匹配”反馈。')
    } else if (onlyStatus === 'REJECTED') {
      ElMessage.warning('系统已记录本次推荐题包“不够匹配”反馈。')
    }
  }
  fetchMethods({ keepSelected: false })
})

onBeforeUnmount(() => {
  if (typeof window !== 'undefined') {
    window.clearTimeout(recentAutoFeedbackHighlightTimer)
  }
  recentAutoFeedbackHighlightTimer = 0
})
</script>

<template>
  <section class="learning-method-page" v-loading="loading">
    <header class="learning-method-page__header">
      <div>
        <p class="learning-method-page__eyebrow">学习方法</p>
        <h2>方法先行，再做训练</h2>
        <p>
          先选一个方法，理解适用场景与步骤，再进入练习。把“会做题”升级成“会学习”，提分会更稳定。
        </p>
      </div>
      <el-button :loading="loading" plain @click="fetchMethods({ keepSelected: true })">刷新列表</el-button>
    </header>

    <el-alert
      v-if="listError"
      :title="listError"
      type="error"
      show-icon
      :closable="false"
      class="learning-method-page__alert"
    />

    <el-empty
      v-else-if="!methodItems.length"
      description="当前暂无可用学习方法，请联系管理员配置。"
      class="learning-method-page__empty"
    />

    <div v-else class="learning-method-page__content">
      <aside class="method-list-panel">
        <button
          v-for="item in methodItems"
          :key="item.methodCode"
          type="button"
          class="method-list-item"
          :class="{ 'method-list-item--active': item.methodCode === selectedCode }"
          @click="selectMethod(item.methodCode)"
        >
          <div class="method-list-item__header">
            <strong>{{ item.methodName || item.methodCode }}</strong>
            <el-tag size="small" :type="statusTagType(item.progress.status)">
              {{ statusLabel(item.progress.status) }}
            </el-tag>
          </div>
          <p>{{ item.oneLineIntro || '暂无方法简介。' }}</p>
          <div class="method-list-item__meta">
            <span>{{ item.difficultyLevel }}</span>
            <span>约 {{ item.estimatedMinutes || 0 }} 分钟</span>
            <span>完成 {{ item.progress.completeCount }} 次</span>
          </div>
        </button>
      </aside>

      <section class="method-detail-panel" v-loading="detailLoading">
        <el-alert
          v-if="detailError"
          :title="detailError"
          type="error"
          show-icon
          :closable="false"
        />

        <template v-else-if="detailPayload?.method">
          <header class="method-detail-panel__header">
            <div>
              <h3>{{ detailPayload.method.methodName || selectedMethod?.methodName || selectedCode }}</h3>
              <p>{{ detailPayload.method.oneLineIntro || selectedMethod?.oneLineIntro || '暂无简介' }}</p>
            </div>
            <div class="method-detail-panel__actions">
              <el-button
                type="primary"
                :loading="actionLoadingCode === `start:${selectedCode}`"
                @click="handleStart(selectedCode)"
              >
                开始练习
              </el-button>
              <el-button
                :loading="actionLoadingCode === `complete:${selectedCode}`"
                @click="handleComplete(selectedCode)"
              >
                标记完成
              </el-button>
              <el-button
                type="success"
                plain
                :loading="recommendationLoading"
                @click="handleRecommendQuestionPack(selectedCode)"
              >
                智能推荐题包
              </el-button>
            </div>
          </header>

          <div class="method-detail-panel__stats">
            <article>
              <span>当前状态</span>
              <strong>{{ statusLabel(selectedProgress.status) }}</strong>
            </article>
            <article>
              <span>开始次数</span>
              <strong>{{ Number(selectedProgress.startCount || 0) }}</strong>
            </article>
            <article>
              <span>完成次数</span>
              <strong>{{ Number(selectedProgress.completeCount || 0) }}</strong>
            </article>
            <article>
              <span>最近正确率</span>
              <strong>{{ formatAccuracy(selectedProgress.lastAccuracy) }}</strong>
            </article>
          </div>

          <div class="method-detail-panel__section">
            <h4>适用场景</h4>
            <ul>
              <li v-for="(row, index) in (detailPayload.method.useWhen || [])" :key="`use-when-${index}`">{{ row }}</li>
            </ul>
            <p v-if="!(detailPayload.method.useWhen || []).length" class="method-detail-panel__placeholder">暂无适用场景说明。</p>
          </div>

          <div class="method-detail-panel__section">
            <h4>执行步骤</h4>
            <ol>
              <li v-for="(step, index) in (detailPayload.method.steps || [])" :key="`step-${index}`">{{ step }}</li>
            </ol>
            <p v-if="!(detailPayload.method.steps || []).length" class="method-detail-panel__placeholder">暂无步骤配置。</p>
          </div>

          <div class="method-detail-panel__section">
            <h4>常见误区</h4>
            <ul>
              <li v-for="(row, index) in (detailPayload.method.commonMistakes || [])" :key="`mistake-${index}`">{{ row }}</li>
            </ul>
            <p v-if="!(detailPayload.method.commonMistakes || []).length" class="method-detail-panel__placeholder">暂无误区提示。</p>
          </div>

          <div class="method-detail-panel__section">
            <h4>推荐题包</h4>
            <el-alert
              v-if="recommendationError"
              :title="recommendationError"
              type="error"
              show-icon
              :closable="false"
            />
            <template v-else-if="recommendationPayload?.recommendationId">
              <div class="recommendation-summary">
                <div>
                  <strong>推荐单号：{{ recommendationPayload.recommendationId }}</strong>
                  <p>
                    共 {{ Number(recommendationPayload.questionCount || 0) }} 题，平均匹配分 {{ formatScore(recommendationPayload?.scoreSummary?.averageScore) }}
                  </p>
                  <p>
                    画像难度偏好：{{ recommendationDifficultyPreferenceLabel(recommendationStudentProfile.difficultyPreference) }}，推荐题型：{{ recommendationQuestionTypeWeightSummary(recommendationStudentProfile) }}
                  </p>
                  <p>
                    当前切换策略：{{ activeRecommendationStrategyPreset.label }}（{{ selectedRecommendationStrategySourceLabel }}）
                  </p>
                </div>
                <div class="recommendation-summary__actions">
                  <el-tag :type="feedbackStatusTagType(recommendationPayload?.recommendationLog?.feedbackStatus)">
                    {{ feedbackStatusLabel(recommendationPayload?.recommendationLog?.feedbackStatus) }}
                  </el-tag>
                  <el-button
                    size="small"
                    type="primary"
                    :disabled="!canNavigateToRecommendationPractice"
                    @click="handleNavigateToRecommendationPractice"
                  >
                    去做题
                  </el-button>
                </div>
              </div>

              <div v-if="recommendationStudentProfile.tags.length" class="recommendation-profile-summary">
                <span>本次画像标签</span>
                <div class="recommendation-profile-summary__tags">
                  <el-tag
                    v-for="tag in recommendationStudentProfile.tags"
                    :key="`profile-${tag}`"
                    size="small"
                    type="success"
                    effect="light"
                  >
                    {{ recommendationTagLabel(tag) }}
                  </el-tag>
                </div>
              </div>

              <div class="recommendation-strategy-switch">
                <span>下一轮推荐策略（来源：{{ selectedRecommendationStrategySourceLabel }}）</span>
                <div class="recommendation-strategy-switch__actions">
                  <el-button
                    v-for="strategy in recommendationStrategyOptions"
                    :key="`strategy-switch-${strategy.code}`"
                    size="small"
                    :type="selectedRecommendationStrategyCode === strategy.code ? 'primary' : 'default'"
                    :plain="selectedRecommendationStrategyCode !== strategy.code"
                    @click="handleSelectRecommendationStrategy(strategy.code)"
                  >
                    {{ strategy.label }}
                  </el-button>
                  <el-button
                    size="small"
                    type="success"
                    plain
                    :loading="recommendationLoading"
                    @click="handleRunRecommendationByCurrentStrategy"
                  >
                    按当前策略重算题包
                  </el-button>
                  <el-button
                    size="small"
                    plain
                    @click="handleResetRecommendationStrategyToDefault"
                  >
                    恢复系统默认
                  </el-button>
                </div>
              </div>

              <div class="recommendation-feedback-actions">
                <el-button
                  size="small"
                  type="success"
                  :loading="feedbackLoading && feedbackStatus === 'ACCEPTED'"
                  @click="handleRecommendationFeedback('ACCEPTED')"
                >
                  匹配很好
                </el-button>
                <el-button
                  size="small"
                  type="warning"
                  :loading="feedbackLoading && feedbackStatus === 'PARTIAL'"
                  @click="handleRecommendationFeedback('PARTIAL')"
                >
                  部分匹配
                </el-button>
                <el-button
                  size="small"
                  type="danger"
                  plain
                  :loading="feedbackLoading && feedbackStatus === 'REJECTED'"
                  @click="handleRecommendationFeedback('REJECTED')"
                >
                  不够匹配
                </el-button>
              </div>

              <ul class="recommendation-question-list">
                <li v-for="question in recommendationQuestions(recommendationPayload)" :key="question.questionId" class="recommendation-question-card">
                  <div class="recommendation-question-card__header">
                    <strong>{{ question.questionId }}</strong>
                    <span>匹配分 {{ formatScore(question.score) }}</span>
                  </div>
                  <div class="recommendation-question-card__meta">
                    <span>题型 {{ recommendationQuestionTypeLabel(question.type) }}</span>
                    <span>难度 {{ question.difficulty || '--' }}</span>
                    <span>画像匹配 {{ formatAccuracy(question.scoreBreakdown?.studentProfileFit) }}</span>
                  </div>
                  <div class="recommendation-question-card__tags">
                    <el-tag
                      v-for="tag in question.reasonTags"
                      :key="`${question.questionId}-${tag}`"
                      size="small"
                      :type="recommendationReasonTagType(tag)"
                      effect="plain"
                    >
                      {{ recommendationReasonTagLabel(tag) }}
                    </el-tag>
                  </div>
                </li>
              </ul>
            </template>
            <p v-else class="method-detail-panel__placeholder">点击“智能推荐题包”后会展示题目匹配结果，并可直接反馈效果。</p>
          </div>

          <div class="method-detail-panel__section">
            <h4>推荐历史</h4>
            <el-alert
              v-if="recommendationHistoryError"
              :title="recommendationHistoryError"
              type="warning"
              show-icon
              :closable="false"
            />
            <div v-loading="recommendationHistoryLoading">
              <section
                v-if="recommendationHistorySourceInsights.length"
                class="recommendation-history-source-insights"
              >
                <header class="recommendation-history-source-insights__header">
                  <strong>策略来源效果对比</strong>
                  <span>{{ recommendationHistorySourceSummary }}</span>
                </header>
                <ul class="recommendation-history-source-insights__list">
                  <li
                    v-for="insight in recommendationHistorySourceInsights"
                    :key="`source-insight-${insight.source}`"
                    class="recommendation-history-source-insights__item"
                  >
                    <div class="recommendation-history-source-insights__item-header">
                      <strong>{{ recommendationStrategySourceLabel(insight.source) }}</strong>
                      <span>{{ insight.sampleCount }} 次</span>
                    </div>
                    <div class="recommendation-history-source-insights__bar-track">
                      <div class="recommendation-history-source-insights__bar-fill" :style="sourceInsightBarStyle(insight.averageFit)"></div>
                    </div>
                    <div class="recommendation-history-source-insights__meta">
                      <span>画像匹配 {{ formatAccuracy(insight.averageFit) }}</span>
                      <span>平均分 {{ formatScore(insight.averageScore) }}</span>
                      <span>有效反馈通过率 {{ formatAccuracy(insight.acceptedRate) }}</span>
                      <span>推荐策略 {{ sourceInsightRecommendedStrategyLabel(insight) }}</span>
                    </div>
                    <div class="recommendation-history-source-insights__actions">
                      <el-button
                        size="small"
                        type="primary"
                        plain
                        :loading="recommendationLoading"
                        @click="handleRunRecommendationBySourceInsight(insight)"
                      >
                        按此来源执行
                      </el-button>
                    </div>
                  </li>
                </ul>
              </section>
              <section
                v-if="recommendationHistoryProfileTrend.points.length"
                class="recommendation-history-trend"
              >
                <header class="recommendation-history-trend__header">
                  <strong>画像匹配变化趋势</strong>
                  <span>
                    近 {{ recommendationHistoryProfileTrend.points.length }} 次：{{ recommendationTrendSummaryText(recommendationHistoryProfileTrend) }}
                  </span>
                </header>
                <div class="recommendation-history-trend__strategy">
                  <el-tag size="small" :type="trendSwitchSuggestion.type">
                    {{ trendSwitchSuggestion.title }}
                  </el-tag>
                  <span>{{ trendSwitchSuggestion.detail }}</span>
                  <el-button
                    size="small"
                    type="primary"
                    plain
                    :loading="recommendationLoading"
                    @click="handleApplySuggestedRecommendationStrategy"
                  >
                    按建议执行下一轮
                  </el-button>
                </div>
                <div class="recommendation-history-trend__thresholds">
                  <span
                    v-for="threshold in recommendationTrendThresholds"
                    :key="`trend-threshold-${threshold}`"
                  >
                    阈值 {{ Math.round(threshold * 100) }}%
                  </span>
                </div>
                <ul class="recommendation-history-trend__list">
                  <li
                    v-for="point in recommendationHistoryProfileTrend.points"
                    :key="point.key"
                    class="recommendation-history-trend__item"
                  >
                    <span class="recommendation-history-trend__date">{{ formatTrendDate(point.recommendedAt) }}</span>
                    <div class="recommendation-history-trend__bar-track">
                      <span
                        v-for="threshold in recommendationTrendThresholds"
                        :key="`${point.key}-threshold-${threshold}`"
                        class="recommendation-history-trend__threshold-line"
                        :style="trendThresholdStyle(threshold)"
                      ></span>
                      <div class="recommendation-history-trend__bar-fill" :style="trendBarStyle(point.fit)"></div>
                    </div>
                    <span class="recommendation-history-trend__value">{{ formatAccuracy(point.fit) }}</span>
                  </li>
                </ul>
              </section>
              <el-empty
                v-if="!recommendationHistoryItems.length"
                description="暂无推荐历史，先生成一次智能推荐题包。"
              />
              <ul v-else class="recommendation-history-list">
                <li
                  v-for="item in recommendationHistoryItems"
                  :key="item.recommendationId"
                  class="recommendation-history-item"
                  :id="recommendationHistoryItemDomId(item.recommendationId)"
                  :class="[
                    { 'recommendation-history-item--recent': item.isRecentAutoFeedback },
                    recentAutoFeedbackItemClass(item),
                    recommendationHistoryFocusClass(item),
                  ]"
                >
                  <div class="recommendation-history-item__header">
                    <strong>{{ item.recommendationId }}</strong>
                    <div class="recommendation-history-item__header-tags">
                      <el-tag
                        v-if="item.isRecentAutoFeedback"
                        size="small"
                        :type="recentAutoFeedbackTagType(item.feedbackStatus)"
                        effect="dark"
                      >
                        {{ recentAutoFeedbackTagLabel(item.feedbackStatus) }}
                      </el-tag>
                      <el-tag size="small" :type="feedbackStatusTagType(item.feedbackStatus)">
                        {{ feedbackStatusLabel(item.feedbackStatus) }}
                      </el-tag>
                    </div>
                  </div>
                  <div class="recommendation-history-item__meta">
                    <span>题量 {{ item.questionCount }}</span>
                    <span>平均分 {{ formatScore(item.averageScore) }}</span>
                    <span>执行策略 {{ recommendationStrategyLabel(item.recommendationStrategyCode) }}</span>
                    <span>策略来源 {{ recommendationStrategySourceLabel(item.recommendationStrategySource) }}</span>
                    <span>画像匹配 {{ formatAccuracy(item.studentProfileFitAverage) }}</span>
                    <span>画像偏好 {{ recommendationDifficultyPreferenceLabel(item.studentProfile?.difficultyPreference) }}</span>
                    <span>推荐时间 {{ formatDateTime(item.recommendedAt) }}</span>
                    <span v-if="canContinueHistoryRecommendation(item)">剩余 {{ historyRemainingQuestionCount(item) }} 题</span>
                  </div>
                  <div v-if="item.studentProfile?.tags?.length" class="recommendation-history-item__profile">
                    <span>画像标签</span>
                    <div class="recommendation-profile-summary__tags">
                      <el-tag
                        v-for="tag in item.studentProfile.tags"
                        :key="`${item.recommendationId}-profile-${tag}`"
                        size="small"
                        type="success"
                        effect="light"
                      >
                        {{ recommendationTagLabel(tag) }}
                      </el-tag>
                    </div>
                  </div>
                  <div v-if="canContinueHistoryRecommendation(item)" class="recommendation-history-item__actions">
                    <el-button
                      size="small"
                      type="primary"
                      plain
                      :loading="historyPracticeLoadingRecommendationId === item.recommendationId"
                      @click="handleContinueHistoryRecommendation(item)"
                    >
                      {{ continueHistoryRecommendationButtonLabel(item) }}
                    </el-button>
                  </div>
                  <div class="recommendation-history-item__tags">
                    <el-tag
                      v-for="tag in item.reasonTags"
                      :key="`${item.recommendationId}-${tag}`"
                      size="small"
                      :type="recommendationReasonTagType(tag)"
                      effect="plain"
                    >
                      {{ recommendationReasonTagLabel(tag) }}
                    </el-tag>
                  </div>
                </li>
              </ul>
            </div>
          </div>
        </template>
      </section>
    </div>
  </section>
</template>

<style scoped>
.learning-method-page {
  display: grid;
  gap: 16px;
}

.learning-method-page__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 20px;
  border: 1px solid var(--qb-border-light);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.94);
}

.learning-method-page__eyebrow {
  margin: 0;
  font-size: 12px;
  color: var(--qb-text-meta);
}

.learning-method-page__header h2 {
  margin: 8px 0;
  color: var(--qb-text-primary);
}

.learning-method-page__header p {
  margin: 0;
  color: var(--qb-text-secondary);
  line-height: 1.65;
}

.learning-method-page__alert,
.learning-method-page__empty {
  background: rgba(255, 255, 255, 0.9);
  border-radius: 12px;
}

.learning-method-page__content {
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
  gap: 16px;
}

.method-list-panel,
.method-detail-panel {
  border: 1px solid var(--qb-border-light);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.95);
  padding: 14px;
}

.method-list-panel {
  display: grid;
  gap: 10px;
  align-content: start;
  max-height: 72vh;
  overflow: auto;
}

.method-list-item {
  display: grid;
  gap: 8px;
  text-align: left;
  border: 1px solid var(--qb-border-light);
  border-radius: 12px;
  background: var(--qb-bg-card);
  padding: 12px;
  cursor: pointer;
}

.method-list-item--active {
  border-color: rgba(47, 84, 235, 0.52);
  box-shadow: 0 8px 24px rgba(47, 84, 235, 0.12);
}

.method-list-item__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.method-list-item__header strong {
  color: var(--qb-text-primary);
}

.method-list-item p {
  margin: 0;
  color: var(--qb-text-secondary);
  line-height: 1.55;
  font-size: 13px;
}

.method-list-item__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  font-size: 12px;
  color: var(--qb-text-meta);
}

.method-detail-panel {
  display: grid;
  gap: 14px;
  min-height: 420px;
}

.method-detail-panel__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.method-detail-panel__header h3 {
  margin: 0;
  color: var(--qb-text-primary);
}

.method-detail-panel__header p {
  margin: 8px 0 0;
  color: var(--qb-text-secondary);
  line-height: 1.6;
}

.method-detail-panel__actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.method-detail-panel__stats {
  display: grid;
  gap: 10px;
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.method-detail-panel__stats article {
  border: 1px solid var(--qb-border-light);
  border-radius: 10px;
  padding: 10px;
  background: rgba(240, 244, 255, 0.45);
  display: grid;
  gap: 4px;
}

.method-detail-panel__stats span {
  color: var(--qb-text-meta);
  font-size: 12px;
}

.method-detail-panel__stats strong {
  color: var(--qb-text-primary);
  font-size: 16px;
}

.method-detail-panel__section {
  display: grid;
  gap: 8px;
}

.method-detail-panel__section h4 {
  margin: 0;
  color: var(--qb-text-primary);
}

.method-detail-panel__section ul,
.method-detail-panel__section ol {
  margin: 0;
  padding-left: 18px;
  color: var(--qb-text-secondary);
  line-height: 1.65;
}

.method-detail-panel__placeholder {
  margin: 0;
  color: var(--qb-text-meta);
  font-size: 13px;
}

.recommendation-summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border: 1px solid var(--qb-border-light);
  border-radius: 10px;
  background: rgba(241, 250, 241, 0.72);
}

.recommendation-summary p {
  margin: 6px 0 0;
  color: var(--qb-text-secondary);
  font-size: 13px;
}

.recommendation-summary__actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  flex-wrap: wrap;
}

.recommendation-feedback-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.recommendation-profile-summary {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  color: var(--qb-text-secondary);
  font-size: 13px;
}

.recommendation-profile-summary__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.recommendation-strategy-switch {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  color: var(--qb-text-secondary);
  font-size: 13px;
}

.recommendation-strategy-switch__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.recommendation-history-source-insights {
  border: 1px solid var(--qb-border-light);
  border-radius: 10px;
  padding: 10px;
  background: rgba(240, 247, 255, 0.8);
  display: grid;
  gap: 10px;
  margin-bottom: 12px;
}

.recommendation-history-source-insights__header {
  display: grid;
  gap: 4px;
}

.recommendation-history-source-insights__header strong {
  color: var(--qb-text-primary);
  font-size: 14px;
}

.recommendation-history-source-insights__header span {
  color: var(--qb-text-secondary);
  font-size: 12px;
  line-height: 1.5;
}

.recommendation-history-source-insights__list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 8px;
}

.recommendation-history-source-insights__item {
  padding: 10px;
  border-radius: 10px;
  border: 1px solid var(--qb-border-light);
  background: rgba(255, 255, 255, 0.9);
  display: grid;
  gap: 8px;
}

.recommendation-history-source-insights__item-header {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  color: var(--qb-text-primary);
  font-size: 13px;
}

.recommendation-history-source-insights__bar-track {
  position: relative;
  height: 8px;
  border-radius: 999px;
  background: rgba(31, 45, 61, 0.12);
  overflow: hidden;
}

.recommendation-history-source-insights__bar-fill {
  position: relative;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(
    90deg,
    var(--qb-color-success, rgba(38, 208, 124, 1)) 0%,
    var(--qb-color-primary, rgba(47, 84, 235, 1)) 100%
  );
}

.recommendation-history-source-insights__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  font-size: 12px;
  color: var(--qb-text-meta);
}

.recommendation-history-source-insights__actions {
  display: flex;
  justify-content: flex-end;
}

.recommendation-history-trend {
  border: 1px solid var(--qb-border-light);
  border-radius: 10px;
  padding: 10px;
  background: rgba(240, 247, 255, 0.8);
  display: grid;
  gap: 10px;
}

.recommendation-history-trend__header {
  display: grid;
  gap: 4px;
}

.recommendation-history-trend__header strong {
  color: var(--qb-text-primary);
  font-size: 14px;
}

.recommendation-history-trend__header span {
  color: var(--qb-text-secondary);
  font-size: 12px;
  line-height: 1.5;
}

.recommendation-history-trend__strategy {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.recommendation-history-trend__strategy span {
  color: var(--qb-text-secondary);
  font-size: 12px;
  line-height: 1.5;
}

.recommendation-history-trend__thresholds {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.recommendation-history-trend__thresholds span {
  font-size: 12px;
  color: var(--qb-text-meta);
}

.recommendation-history-trend__list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 8px;
}

.recommendation-history-trend__item {
  display: grid;
  grid-template-columns: 60px 1fr 56px;
  align-items: center;
  gap: 8px;
}

.recommendation-history-trend__date,
.recommendation-history-trend__value {
  color: var(--qb-text-meta);
  font-size: 12px;
}

.recommendation-history-trend__value {
  text-align: right;
}

.recommendation-history-trend__bar-track {
  position: relative;
  height: 8px;
  border-radius: 999px;
  background: rgba(31, 45, 61, 0.12);
  overflow: hidden;
}

.recommendation-history-trend__threshold-line {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 1px;
  background: var(--qb-border-color, rgba(31, 45, 61, 0.28));
  transform: translateX(-0.5px);
  pointer-events: none;
}

.recommendation-history-trend__bar-fill {
  position: relative;
  z-index: 1;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(
    90deg,
    var(--qb-color-info, rgba(88, 166, 255, 1)) 0%,
    var(--qb-color-primary, rgba(47, 84, 235, 1)) 100%
  );
}

.recommendation-question-list,
.recommendation-history-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 10px;
}

.recommendation-question-card,
.recommendation-history-item {
  border: 1px solid var(--qb-border-light);
  border-radius: 10px;
  padding: 10px;
  background: rgba(248, 250, 255, 0.9);
  display: grid;
  gap: 8px;
  transition: border-color 0.45s ease, box-shadow 0.45s ease, background-color 0.45s ease;
}

.recommendation-question-card__header,
.recommendation-history-item__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.recommendation-history-item__header-tags {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.recommendation-history-item--recent {
  transform: translateY(-1px);
}

.recommendation-history-item--focus-return {
  border-color: rgba(47, 84, 235, 0.56);
  box-shadow: 0 8px 20px rgba(47, 84, 235, 0.16);
  background: rgba(236, 242, 255, 0.9);
}

.recommendation-history-item--recent-accepted {
  border-color: rgba(24, 160, 88, 0.55);
  box-shadow: 0 8px 20px rgba(24, 160, 88, 0.14);
  background: rgba(236, 250, 240, 0.88);
}

.recommendation-history-item--recent-partial {
  border-color: rgba(230, 162, 60, 0.55);
  box-shadow: 0 8px 20px rgba(230, 162, 60, 0.16);
  background: rgba(255, 245, 225, 0.92);
}

.recommendation-history-item--recent-rejected {
  border-color: rgba(245, 108, 108, 0.55);
  box-shadow: 0 8px 20px rgba(245, 108, 108, 0.16);
  background: rgba(255, 236, 236, 0.9);
}

.recommendation-question-card__meta,
.recommendation-history-item__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  color: var(--qb-text-meta);
  font-size: 12px;
}

.recommendation-history-item__actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.recommendation-history-item__profile {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  color: var(--qb-text-secondary);
  font-size: 13px;
}

.recommendation-question-card__tags,
.recommendation-history-item__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

@media (max-width: 1200px) {
  .learning-method-page__content {
    grid-template-columns: 1fr;
  }

  .method-list-panel {
    max-height: none;
  }

  .method-detail-panel__stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .learning-method-page__header {
    flex-direction: column;
  }

  .method-detail-panel__header {
    flex-direction: column;
  }

  .method-detail-panel__stats {
    grid-template-columns: 1fr;
  }

  .recommendation-summary {
    flex-direction: column;
    align-items: flex-start;
  }

  .recommendation-summary__actions {
    justify-content: flex-start;
  }
}
</style>
