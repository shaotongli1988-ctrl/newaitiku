<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from '@/ui/feedback'
import { onBeforeRouteLeave, useRoute, useRouter } from 'vue-router'
import { useUserStore } from '../../stores/userStore.js'
import { useSubjectContextStore } from '../../stores/subjectContextStore.js'
import {
  createStudentSession,
  fetchStudentDashboard,
  fetchStudentPracticeQuestionList,
  getStudentMockExamSession,
  getStudentSession,
  getStudentPaperReportDetail,
  knowledgeTreeV2,
  listStudentPaperQuestions,
  startStudentMockExam,
  submitLearningMethodQuestionPackFeedback,
  submitStudentExamTask,
  submitStudentPaper,
  submitStudentPaperQuestion,
  updateStudentSessionAnswer,
} from '../../api/services/questionBank'
import { useAiMarking } from '../../composables/useAiMarking'
import {
  buildContentLabelMaps,
  filterJointExamGroupOptions,
  filterSubjectCodeOptions,
  normalizeStudentDashboardDictionary,
  resolveContentLabel,
} from '../../utils/contentBaseline.js'
import { buildKnowledgeLevelTreeState, buildKnowledgeSelectorState } from '../../utils/knowledgeTree'
import {
  clearPracticePathQuery,
  clearPracticeTransientFocusQuery,
  normalizePracticePercent,
  normalizePracticeSubjectOptions,
  resolvePracticeSubjectCode,
  sanitizePracticeQuery,
} from '../../utils/practiceScope.js'
import {
  buildStudentPracticeRouteLocation,
  resolveStudentPracticeSourceDescriptor,
  STUDENT_PRACTICE_MODULE,
} from '../../utils/studentPracticeNavigation.js'
import {
  buildMockExamPreviewRows,
  isMockExamPreviewPaper,
  listMockExamPreviewQuestions,
} from '../../utils/studentMockExamPreview.js'
import { parseExtJson, questionDifficultyLabel, questionTypeLabel } from '../../utils/question.js'
import { saveLearningMethodFeedbackNotice } from '../../utils/learningMethodFeedbackNotice.js'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const subjectContextStore = useSubjectContextStore()

const scopeLabelMaps = computed(() => buildContentLabelMaps(userStore.availableExamCategories))
const practiceModule = computed(() => {
  const explicitModule = String(route.query.module || '').trim().toLowerCase()
  if (route.path.endsWith('/free') || explicitModule === STUDENT_PRACTICE_MODULE.FREE) {
    return STUDENT_PRACTICE_MODULE.FREE
  }
  if (route.path.endsWith('/mock') || explicitModule === STUDENT_PRACTICE_MODULE.MOCK) {
    return STUDENT_PRACTICE_MODULE.MOCK
  }
  return STUDENT_PRACTICE_MODULE.CHAPTER
})
const expectedPath = computed(() => String(route.path || '/student/practice/chapter').trim() || '/student/practice/chapter')
const isChapterModule = computed(() => practiceModule.value === STUDENT_PRACTICE_MODULE.CHAPTER)
const isFreeModule = computed(() => practiceModule.value === STUDENT_PRACTICE_MODULE.FREE)
const isMockModule = computed(() => practiceModule.value === STUDENT_PRACTICE_MODULE.MOCK)
const isImmersiveMode = computed(() => String(route.query.immersive || '').trim() === '1')

const practiceExamCategoryCode = computed(() =>
  String(route.query.examCategoryCode || userStore.examCategoryCode || '').trim(),
)
const practiceJointExamGroupCode = computed(() =>
  String(
    route.query.jointExamGroupCode
    || userStore.assignedJointGroupCode
    || userStore.jointExamGroupCode
    || '',
  ).trim(),
)
const practiceSubjectCode = computed(() =>
  String(route.query.subjectCode || subjectContextStore.currentSubjectCode || '').trim(),
)
const practiceChapterCode = computed(() => String(route.query.chapterCode || '').trim())
const practiceChapterName = computed(() => String(route.query.chapterName || '').trim())
const practicePointCode = computed(() => String(route.query.pointCode || '').trim())
const practicePointName = computed(() => String(route.query.pointName || '').trim())
const practiceKnowledgeId = computed(() => String(route.query.knowledgeId || '').trim())
const practiceKnowledgePathNodeId = computed(() => String(route.query.knowledgePathNodeId || '').trim())
const practicePathLabel = computed(() => String(route.query.pathLabel || '').trim())
const focusMode = computed(() => String(route.query.focusMode || '').trim())
const focusedQuestionId = computed(() => String(route.query.focusQuestionId || '').trim())
const practiceSource = computed(() => String(route.query.practiceSource || '').trim())
const practiceSourceLabel = computed(() => String(route.query.practiceSourceLabel || '').trim())
const learningMethodCode = computed(() => String(route.query.learningMethodCode || '').trim())
const learningMethodRecommendationId = computed(() => String(route.query.learningMethodRecommendationId || '').trim())
const learningMethodSessionId = computed(() => String(route.query.learningMethodSessionId || '').trim())

const adaptiveDimensionParam = computed(() => {
  const raw = route.query.adaptiveDimension
  const normalized = (Array.isArray(raw) ? raw[0] : raw || '').toString().trim()
  return normalized
})
const hasAdaptiveTrace = computed(() => Boolean(adaptiveDimensionParam.value))
const adaptiveQuestionIds = computed(() => {
  const raw = route.query.adaptiveQuestionIds
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
const adaptiveDimension = computed(() => {
  const normalized = adaptiveDimensionParam.value
    .toString()
    .trim()
    .replace(/^subject[-_]?/i, '')
    .replace(/[^a-zA-Z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .toUpperCase()
  if (normalized) {
    return normalized
  }
  return practiceSubjectCode.value || 'MATH'
})
const adaptiveMastery = computed(() => {
  const raw = route.query.adaptiveMastery
  const normalized = Number(Array.isArray(raw) ? raw[0] : raw)
  if (!Number.isFinite(normalized)) {
    return 0
  }
  return Math.max(0, Math.min(100, normalized))
})
const adaptiveTraceNotice = computed(() =>
  `🎯 智能强化：系统检测到您在 ${adaptiveDimension.value} 领域的掌握度仅为 ${adaptiveMastery.value.toFixed(2)}%，已为您精准匹配 ${adaptiveQuestionIds.value.length || 6} 道提分题。`,
)
const isRiskRepairMode = computed(() => focusMode.value === 'RISK_REPAIR')
const practiceSourceDescriptor = computed(() =>
  resolveStudentPracticeSourceDescriptor(practiceSource.value, practiceSourceLabel.value),
)
const practiceSourceAlertType = computed(() => {
  if (practiceSourceDescriptor.value.key === 'WRONG_BOOK') {
    return 'warning'
  }
  if (practiceSourceDescriptor.value.key === 'LEARNING_METHOD') {
    return 'success'
  }
  if (practiceSourceDescriptor.value.key === 'TASK') {
    return 'success'
  }
  if (practiceSourceDescriptor.value.key === 'HOME') {
    return 'success'
  }
  if (practiceSourceDescriptor.value.key === 'POINTS') {
    return 'info'
  }
  if (practiceSourceDescriptor.value.key === 'KNOWLEDGE') {
    return 'info'
  }
  return 'info'
})
const isLearningMethodRecommendationPractice = computed(() =>
  isFreeModule.value
  && practiceSourceDescriptor.value.key === 'LEARNING_METHOD'
  && Boolean(learningMethodCode.value)
  && Boolean(learningMethodRecommendationId.value)
  && adaptiveQuestionIds.value.length > 0,
)
const canBackToLearningMethods = computed(() =>
  isLearningMethodRecommendationPractice.value
  && Boolean(learningMethodCode.value)
  && Boolean(learningMethodRecommendationId.value),
)
const SESSION_STORAGE_KEY = 'current_session_id'
const MOCK_EXAM_DRAFT_PREFIX = 'student_mock_exam_draft:'

const pageLoading = ref(false)
const savingAnswer = ref(false)
const submittingPractice = ref(false)
const knowledgeTreeLoading = ref(false)
const baselineLoading = ref(false)

const dashboardPayload = ref({})
const subjectOptions = ref([])
const examCategoryOptions = ref([])
const jointExamGroupOptions = ref([])
const subjectCodeOptions = ref([])

const preciseKnowledgeOptions = ref([])
const selectedKnowledgePath = ref([])
const selectedL3NodeId = ref('')
const selectedL4NodeId = ref('')
const selectedL5NodeId = ref('')
const knowledgeSelectorState = ref(buildKnowledgeSelectorState({}))
const knowledgePathLabelMap = ref({})
const filterCollapsePanels = ref([])
const chapterCloudRef = ref(null)
const chapterCloudExpanded = ref(false)
const chapterCloudOverflow = ref(false)

const questionRows = ref([])
const questionTotal = ref(0)
const activeQuestionIndex = ref(0)
const selectedAnswers = reactive({})
const markedQuestions = reactive({})
const practiceRouteActive = ref(true)
const availablePaperRows = ref([])
const challengePointsState = ref({})
const usingMockExamPreview = ref(false)
const mockExamSession = ref(null)
const mockExamSubmitDialogVisible = ref(false)
const mockExamSubmittingPaper = ref(false)
const mockExamPaused = ref(false)
const mockExamRemainingSec = ref(0)
const mockExamLastReport = ref(null)
const studentMessageText = ref('')
const draftRestoreStamp = ref('')
const learningMethodAutoFeedbackSubmitting = ref(false)
const learningMethodAutoFeedbackStatus = ref('')
const learningMethodReturnLoading = ref(false)
let chapterCloudMeasureTimer = 0
let mockExamCountdownTimer = 0

const sessionState = reactive({
  sessionId: '',
  answeredCount: 0,
  elapsedSec: 0,
  updateTime: '',
  startedAtMs: 0,
})

const aiMarking = useAiMarking()

// 立即重置所有loading状态，防止转圈按钮卡死
savingAnswer.value = false
submittingPractice.value = false
mockExamSubmittingPaper.value = false
aiMarking.loading.value = false
aiMarking.stopPolling()

// 使用nextTick确保在DOM更新后再次重置，防止状态残留
nextTick(() => {
  savingAnswer.value = false
  submittingPractice.value = false
  mockExamSubmittingPaper.value = false
  aiMarking.loading.value = false
  aiMarking.stopPolling()
})

const knowledgeCascaderProps = {
  value: 'value',
  label: 'label',
  children: 'children',
  emitPath: true,
  checkStrictly: false,
}

function toText(value) {
  return String(value || '').trim()
}

function createAttemptId(prefix = 'attempt') {
  const randomUUID = globalThis.crypto && typeof globalThis.crypto.randomUUID === 'function'
    ? globalThis.crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(16).slice(2)}`
  return `${prefix}-${randomUUID}`
}

function currentElapsedSec() {
  if (isMockModule.value && activePaper.value?.paperId) {
    const totalSec = Number(activePaper.value?.durationMinutes || 0) * 60
    if (totalSec > 0) {
      return Math.max(0, totalSec - Number(mockExamRemainingSec.value || 0))
    }
  }
  const baseSec = Number(sessionState.elapsedSec || 0)
  const startedAtMs = Number(sessionState.startedAtMs || 0)
  if (!startedAtMs) {
    return baseSec
  }
  const delta = Math.max(0, Math.floor((Date.now() - startedAtMs) / 1000))
  return baseSec + delta
}

function clampElapsedSec(maxSec = 3600) {
  const normalizedMax = Math.max(0, Number(maxSec || 0))
  return Math.max(0, Math.min(normalizedMax, Number(currentElapsedSec() || 0)))
}

function optionLabel(optionItem) {
  const key = toText(optionItem?.key)
  const content = toText(optionItem?.content)
  if (key && content) {
    return `${key}. ${content}`
  }
  return key || content || '-'
}

function formatDuration(totalSec) {
  const normalized = Math.max(0, Number(totalSec || 0))
  const hours = Math.floor(normalized / 3600)
  const minutes = Math.floor((normalized % 3600) / 60)
  const seconds = normalized % 60

  if (hours > 0) {
    return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
  }

  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
}

function readSafeStorage(key) {
  if (typeof localStorage === 'undefined') {
    return ''
  }
  try {
    return String(localStorage.getItem(key) || '')
  } catch (error) {
    return ''
  }
}

function writeSafeStorage(key, value) {
  if (typeof localStorage === 'undefined') {
    return
  }
  try {
    localStorage.setItem(key, value)
  } catch (error) {
    // Ignore storage write failures and keep the exam flow usable.
  }
}

function removeSafeStorage(key) {
  if (typeof localStorage === 'undefined') {
    return
  }
  try {
    localStorage.removeItem(key)
  } catch (error) {
    // Ignore storage removal failures and keep the exam flow usable.
  }
}

function answerForAiMarking() {
  const currentAnswer = toText(currentSelectedAnswer.value)
  if (!currentAnswer) {
    return ''
  }
  const matchedOption = activeQuestionOptions.value.find(
    (optionItem) => toText(optionItem?.key) === currentAnswer,
  )
  if (!matchedOption) {
    return currentAnswer
  }
  return optionLabel(matchedOption)
}

const scopedExamCategoryOptions = computed(() => {
  const source = Array.isArray(examCategoryOptions.value) ? examCategoryOptions.value : []
  const assignedJointGroupCode = toText(userStore.assignedJointGroupCode)
  if (!assignedJointGroupCode) {
    return source
  }
  const matchedGroup = jointExamGroupOptions.value.find(
    (item) => toText(item?.jointExamGroupCode) === assignedJointGroupCode,
  )
  if (!matchedGroup?.examCategoryCode) {
    return source
  }
  return source.filter(
    (item) => toText(item?.examCategoryCode) === toText(matchedGroup.examCategoryCode),
  )
})

function resolveJointGroupOptions(examCategoryCode) {
  const assignedJointGroupCode = toText(userStore.assignedJointGroupCode)
  let options = filterJointExamGroupOptions(jointExamGroupOptions.value, examCategoryCode)
  if (assignedJointGroupCode) {
    options = options.filter(
      (item) => toText(item?.jointExamGroupCode) === assignedJointGroupCode,
    )
  }
  if (options.length) {
    return options
  }
  if (assignedJointGroupCode) {
    return [
      {
        jointExamGroupCode: assignedJointGroupCode,
        jointExamGroupName: resolveContentLabel(scopeLabelMaps.value.jointExamGroupNameMap, assignedJointGroupCode),
        examCategoryCode: toText(examCategoryCode),
      },
    ]
  }
  return []
}

function resolveSubjectScopeOptions(examCategoryCode, jointExamGroupCode) {
  const dictionarySource = Array.isArray(subjectCodeOptions.value) ? subjectCodeOptions.value : []
  const dashboardSource = Array.isArray(subjectOptions.value) ? subjectOptions.value : []
  const dashboardMetaMap = new Map(
    dashboardSource.map((item) => [
      toText(item?.subjectCode),
      {
        subjectCode: toText(item?.subjectCode),
        subjectId: toText(item?.subjectId),
        subjectName: toText(item?.subjectName || item?.subjectCode),
        subjectType: toText(item?.subjectType),
        answered: Number(item?.answered || 0),
        total: Number(item?.total || 0),
        accuracy: Number(item?.accuracy || 0),
      },
    ]),
  )

  const mergedRows = []
  const seen = new Set()

  const scopedDictionaryRows = filterSubjectCodeOptions(dictionarySource, examCategoryCode, jointExamGroupCode)
  scopedDictionaryRows.forEach((item) => {
    const subjectCode = toText(item?.subjectCode)
    if (!subjectCode || seen.has(subjectCode)) {
      return
    }
    seen.add(subjectCode)
    const dashboardMeta = dashboardMetaMap.get(subjectCode) || {}
    mergedRows.push({
      subjectCode,
      subjectId: toText(dashboardMeta.subjectId),
      subjectName: toText(dashboardMeta.subjectName || item?.subjectName || subjectCode),
      subjectType: toText(dashboardMeta.subjectType || item?.subjectType),
      examCategoryCode: toText(item?.examCategoryCode),
      jointExamGroupCode: toText(item?.jointExamGroupCode),
      answered: Number(dashboardMeta.answered || 0),
      total: Number(dashboardMeta.total || 0),
      accuracy: Number(dashboardMeta.accuracy || 0),
    })
  })

  dashboardSource.forEach((item) => {
    const subjectCode = toText(item?.subjectCode)
    if (!subjectCode || seen.has(subjectCode)) {
      return
    }
    if (scopedDictionaryRows.length) {
      return
    }
    seen.add(subjectCode)
    mergedRows.push({
      subjectCode,
      subjectId: toText(item?.subjectId),
      subjectName: toText(item?.subjectName || item?.subjectCode),
      subjectType: toText(item?.subjectType),
      examCategoryCode: toText(examCategoryCode),
      jointExamGroupCode: toText(jointExamGroupCode),
      answered: Number(item?.answered || 0),
      total: Number(item?.total || 0),
      accuracy: Number(item?.accuracy || 0),
    })
  })

  return mergedRows
}

const scopedJointExamGroupOptions = computed(() =>
  resolveJointGroupOptions(practiceExamCategoryCode.value),
)

const scopedSubjectOptions = computed(() =>
  resolveSubjectScopeOptions(practiceExamCategoryCode.value, practiceJointExamGroupCode.value),
)

const currentSubject = computed(() =>
  scopedSubjectOptions.value.find((item) => item.subjectCode === practiceSubjectCode.value)
  || subjectOptions.value.find((item) => item.subjectCode === practiceSubjectCode.value)
  || scopedSubjectOptions.value[0]
  || subjectOptions.value[0]
  || null,
)

const currentSubjectName = computed(() =>
  toText(currentSubject.value?.subjectName || currentSubject.value?.subjectCode || '当前科目'),
)

const currentSubjectProgress = computed(() => ({
  answered: Number(currentSubject.value?.answered || 0),
  total: Number(currentSubject.value?.total || 0),
  accuracy: normalizePracticePercent(currentSubject.value?.accuracy || 0),
}))

const mockPaperCards = computed(() => {
  if (mockExamSession.value?.paperId) {
    return [
      {
        paperId: toText(mockExamSession.value.paperId),
        paperName: toText(mockExamSession.value.paperName || '当前模拟卷'),
        durationMinutes: Number(mockExamSession.value.durationMinutes || 0),
        questionCount: Number(mockExamSession.value.questionCount || 0),
        totalScore: Number(mockExamSession.value.totalScore || 0),
        questionIds: [],
      },
    ]
  }
  const paperMap = new Map()
  availablePaperRows.value.forEach((row) => {
    const questionId = toText(row?.id)
    const ext = parseExtJson(row?.extJson)
    const bindings = Array.isArray(ext?.paperBindings) ? ext.paperBindings : []
    const binding = bindings[0] || {}
    const paperId = toText(binding?.paperId)
    if (!paperId) {
      return
    }
    const rowSubjectCode = toText(ext?.subjectCode)
    if (practiceSubjectCode.value && rowSubjectCode && rowSubjectCode !== practiceSubjectCode.value) {
      return
    }
    const card = paperMap.get(paperId) || {
      paperId,
      paperName: toText(binding?.paperName || paperId),
      durationMinutes: Number(binding?.durationMinutes || 0),
      questionCount: 0,
      totalScore: 0,
      questionIds: [],
    }
    card.questionCount += 1
    card.totalScore += Number(binding?.questionScore || 0)
    if (questionId) {
      card.questionIds.push(questionId)
    }
    paperMap.set(paperId, card)
  })
  return Array.from(paperMap.values()).sort((left, right) => {
    if (left.questionCount !== right.questionCount) {
      return right.questionCount - left.questionCount
    }
    return left.paperName.localeCompare(right.paperName, 'zh-Hans-CN')
  })
})

const selectedPaperId = computed(() => toText(route.query.paperId))
const recommendedPaper = computed(() => mockPaperCards.value[0] || null)
const activePaper = computed(() =>
  mockPaperCards.value.find((item) => item.paperId === selectedPaperId.value)
  || recommendedPaper.value
  || null,
)
const mockExamDraftStorageKey = computed(() => {
  const paperId = toText(activePaper.value?.paperId)
  return paperId ? `${MOCK_EXAM_DRAFT_PREFIX}${paperId}` : ''
})

const currentChallengePoints = computed(() => {
  const subjectCode = practiceSubjectCode.value
  const challengePayload = challengePointsState.value && typeof challengePointsState.value === 'object'
    ? challengePointsState.value
    : {}
  if (toText(challengePayload?.subjectCode) === subjectCode) {
    return challengePayload
  }
  const dashboardSubjects = Array.isArray(dashboardPayload.value?.challengePointSubjects)
    ? dashboardPayload.value.challengePointSubjects
    : Array.isArray(dashboardPayload.value?.studentState?.challengePointSubjects)
      ? dashboardPayload.value.studentState.challengePointSubjects
      : []
  return dashboardSubjects.find((item) => toText(item?.subjectCode) === subjectCode) || {
    subjectCode,
    total: 0,
    todayDelta: 0,
    correctSubmitCount: 0,
    todayCorrectSubmitCount: 0,
    rank: 0,
    awardUnlocked: false,
    awardProgress: 0,
    awardThreshold: 3000,
    scoreCap: 3000,
    levelName: '刷题青铜',
    nextLevelName: '刷题白银',
    pointsToNextLevel: 200,
  }
})

const challengeRuleHelperText = computed(() => {
  const nextLevelName = toText(currentChallengePoints.value?.nextLevelName)
  const pointsToNextLevel = Number(currentChallengePoints.value?.pointsToNextLevel || 0)
  if (nextLevelName) {
    return `每次答对都在累积稳定得分能力，再积 ${pointsToNextLevel} 分到 ${nextLevelName}。`
  }
  return '当前已到满阶段位，继续保持高频正确输出，才能把状态带进正式考试。'
})

function buildChallengePointToast(submitResult = {}) {
  const challengePoints = submitResult?.challengePoints && typeof submitResult.challengePoints === 'object'
    ? submitResult.challengePoints
    : currentChallengePoints.value
  const total = Number(submitResult?.challengePointTotal || challengePoints?.total || 0)
  const levelName = toText(challengePoints?.levelName || '刷题青铜')
  const nextLevelName = toText(challengePoints?.nextLevelName)
  const pointsToNextLevel = Number(challengePoints?.pointsToNextLevel || 0)
  const rank = Number(submitResult?.subjectRank || challengePoints?.rank || 0)
  const rankText = rank > 0 ? `，排名 #${rank}` : ''

  if (nextLevelName) {
    return `段位分 +${Number(submitResult?.challengePointDelta || 0)}，当前 ${total} 分，段位 ${levelName}${rankText}，再积 ${pointsToNextLevel} 分到 ${nextLevelName}。你在把这门课练成考场上能稳定拿分的状态。`
  }

  return `段位分 +${Number(submitResult?.challengePointDelta || 0)}，当前 ${total} 分，段位 ${levelName}${rankText}。当前已经满阶，继续保持这种正确输出，就是在稳住升本底盘。`
}


const activeQuestion = computed(() => questionRows.value[activeQuestionIndex.value] || null)
const activeQuestionId = computed(() => toText(activeQuestion.value?.id))
const isFocusedQuestionActive = computed(() =>
  Boolean(focusedQuestionId.value) && focusedQuestionId.value === activeQuestionId.value,
)
const riskRepairNotice = computed(() =>
  isRiskRepairMode.value && isFocusedQuestionActive.value
    ? '同组高风险题已自动聚焦，请优先完成这道题的补齐练习。'
    : '',
)

const activeQuestionExt = computed(() => parseExtJson(activeQuestion.value?.extJson))
const activeQuestionOptions = computed(() => {
  try {
    const parsed = JSON.parse(String(activeQuestion.value?.optionsJson || '[]'))
    return Array.isArray(parsed) ? parsed : []
  } catch (error) {
    return []
  }
})
const activeQuestionKnowledgeTags = computed(() => {
  const knowledgeTags = Array.isArray(activeQuestionExt.value?.knowledgeTags)
    ? activeQuestionExt.value.knowledgeTags
    : []
  return knowledgeTags.map((item) => toText(item)).filter((item) => item)
})
const activeQuestionTypeLabel = computed(() => questionTypeLabel(activeQuestion.value?.type))
const activeQuestionDifficulty = computed(() => {
  const difficulty = toText(activeQuestionExt.value?.difficulty)
  return difficulty ? questionDifficultyLabel(difficulty) : ''
})
const activeQuestionTimeLimit = computed(() =>
  Number(activeQuestionExt.value?.practiceConfig?.timeLimitSec || 0),
)

const answeredQuestionCount = computed(() =>
  Object.values(selectedAnswers).filter((answerItem) => toText(answerItem)).length,
)

const remainingQuestionCount = computed(() =>
  Math.max((questionRows.value.length || 0) - answeredQuestionCount.value, 0),
)

const workbenchProgressPercent = computed(() => {
  const total = Number(questionRows.value.length || 0)
  if (!total) {
    return 0
  }
  return Math.max(0, Math.min(100, Math.round((answeredQuestionCount.value / total) * 100)))
})

const questionPositionPercent = computed(() => {
  const total = Number(questionRows.value.length || 0)
  if (!total) {
    return 0
  }
  return Math.max(8, Math.min(100, Math.round(((activeQuestionIndex.value + 1) / total) * 100)))
})

const practiceElapsedLabel = computed(() => formatDuration(currentElapsedSec()))
const mockExamRemainingLabel = computed(() => formatDuration(mockExamRemainingSec.value))
const mockPreviewNotice = computed(() =>
  usingMockExamPreview.value
    ? '当前模拟考试内容为前端预览卷，仅用于看页面与交互感觉，不会写入正式模考记录。'
    : '',
)
const currentQuestionNumberLabel = computed(() => `Q${String(activeQuestionIndex.value + 1).padStart(2, '0')}`)
const unansweredQuestionRows = computed(() =>
  questionOutlineRows.value.filter((item) => !item.isAnswered),
)
const markedQuestionRows = computed(() =>
  questionOutlineRows.value.filter((item) => item.isMarked),
)
const mockExamPauseStatusLabel = computed(() =>
  mockExamPaused.value ? '暂停中' : '每次最多 10 分钟',
)
const mockExamPauseStatusType = computed(() => (mockExamPaused.value ? 'warning' : 'info'))
const isMockExamSubmitted = computed(() => Boolean(mockExamLastReport.value?.reportId))

const currentSelectedAnswer = computed({
  get() {
    return toText(selectedAnswers[activeQuestionId.value])
  },
  set(value) {
    selectedAnswers[activeQuestionId.value] = toText(value)
  },
})

const currentQuestionListLabel = computed(() => {
  if (isMockModule.value) {
    return activePaper.value
      ? `当前试卷：${activePaper.value.paperName}`
      : '当前试卷：点击开始考试后生成'
  }
  if (practicePathLabel.value) {
    return `当前定位：${practicePathLabel.value}`
  }
  if (practicePointCode.value) {
    return `当前考点：${practicePointName.value || practicePointCode.value}`
  }
  if (practiceChapterCode.value) {
    return `当前章节：${practiceChapterName.value || practiceChapterCode.value}`
  }
  return '当前题单：全量练习'
})

const practiceFilterNotice = computed(() => {
  const fragments = []
  if (practiceChapterName.value || practiceChapterCode.value) {
    fragments.push(`章节 ${practiceChapterName.value || practiceChapterCode.value}`)
  }
  if (practicePointName.value || practicePointCode.value) {
    fragments.push(`L5 ${practicePointName.value || practicePointCode.value}`)
  }
  return fragments.join(' / ')
})

const selectedPracticeChapterLabel = computed(() =>
  toText(practiceChapterName.value || practiceChapterCode.value || '全部章节'),
)

const selectedPracticePointLabel = computed(() =>
  toText(practicePointName.value || practicePointCode.value),
)

const selectedPracticeScopeLabel = computed(() => {
  const fragments = []
  if (selectedPracticeChapterLabel.value && selectedPracticeChapterLabel.value !== '全部章节') {
    fragments.push(selectedPracticeChapterLabel.value)
  }
  if (selectedPracticePointLabel.value) {
    fragments.push(`L5 ${selectedPracticePointLabel.value}`)
  }
  return `已选中：${fragments.length ? fragments.join(' - ') : '全量题单'}`
})

const practiceSourceNotice = computed(() => {
  if (!practiceSourceDescriptor.value.key && !practiceSourceLabel.value) {
    return ''
  }
  return `${practiceSourceDescriptor.value.title}：${practiceSourceDescriptor.value.description}`
})

const practiceHeroTitle = computed(() => {
  if (isMockModule.value) {
    return '模拟考试'
  }
  if (isFreeModule.value) {
    return '自由练习'
  }
  if (practiceSourceDescriptor.value.key === 'TASK') {
    return '任务练习台'
  }
  if (practiceSourceDescriptor.value.key === 'LEARNING_METHOD') {
    return '学习方法推荐练习'
  }
  if (practiceSourceDescriptor.value.key === 'HOME') {
    return '首页推荐练习'
  }
  if (practiceSourceDescriptor.value.key === 'POINTS') {
    return '积分冲刺练习'
  }
  if (practiceSourceDescriptor.value.key === 'WRONG_BOOK') {
    return '错题修复练习'
  }
  if (practiceSourceDescriptor.value.key === 'KNOWLEDGE') {
    return '知识点专项练习'
  }
  return '刷题升本'
})

const practiceHeroCopy = computed(() => {
  if (isMockModule.value) {
    return '按当前科目官方大纲即时组卷，点击开始考试后才会生成本次试卷。'
  }
  if (isFreeModule.value) {
    return '这里默认只保留答题主界面和积分反馈，不展示章节树、筛选折叠区和右侧提示卡。'
  }
  if (practiceSourceDescriptor.value.key === 'TASK') {
    return '这里承接今天的执行动作，首屏只保留当前题路、章节和题目推进，不再把范围信息堆满一整屏。'
  }
  if (practiceSourceDescriptor.value.key === 'LEARNING_METHOD') {
    return '你是从学习方法推荐题包进入的，建议先完成定向题，再回到方法页查看匹配反馈。'
  }
  if (practiceSourceDescriptor.value.key === 'HOME') {
    return '你是从学习首页直接进入的，这里承接首页推荐动作，适合先把最顺手的一组题做起来。'
  }
  if (practiceSourceDescriptor.value.key === 'POINTS') {
    return '你是从练习积分进入的，这一轮更适合保持答题节奏，把段位分和正确题次稳定往上推。'
  }
  if (practiceSourceDescriptor.value.key === 'WRONG_BOOK') {
    return '你是从错题修复进入的，这一轮不是泛化刷题，而是围绕已经暴露的问题快速闭环。'
  }
  if (practiceSourceDescriptor.value.key === 'KNOWLEDGE') {
    return '你是从知识路径定位进入的，当前练习应该围绕一个明确的章节或考点持续推进。'
  }
  return '把章节和 L5 考点收成一条清晰刷题路径，先定定位，再连续推进提分。'
})

const practiceHeroToneClass = computed(() => {
  if (isMockModule.value) {
    return 'practice-hero--knowledge'
  }
  if (isFreeModule.value) {
    return 'practice-hero--task'
  }
  if (practiceSourceDescriptor.value.key === 'TASK') {
    return 'practice-hero--task'
  }
  if (practiceSourceDescriptor.value.key === 'LEARNING_METHOD') {
    return 'practice-hero--knowledge'
  }
  if (practiceSourceDescriptor.value.key === 'HOME') {
    return 'practice-hero--task'
  }
  if (practiceSourceDescriptor.value.key === 'POINTS') {
    return 'practice-hero--knowledge'
  }
  if (practiceSourceDescriptor.value.key === 'WRONG_BOOK') {
    return 'practice-hero--repair'
  }
  if (practiceSourceDescriptor.value.key === 'KNOWLEDGE') {
    return 'practice-hero--knowledge'
  }
  return ''
})

const isTaskPracticeWorkbench = computed(() =>
  !isFreeModule.value && !isMockModule.value && practiceSourceDescriptor.value.key === 'TASK',
)

const practiceContextCards = computed(() => ([
  {
    label: '进入方式',
    value: isMockModule.value ? '模拟考试' : isFreeModule.value ? '自由练习' : (practiceSourceDescriptor.value.title || '刷题入口'),
    helper: isMockModule.value
      ? '点击开始考试后会即时生成一套当前科目的模拟卷'
      : isFreeModule.value
        ? '当前按科目或知识点自由出题'
        : (practiceSourceDescriptor.value.description || '所有去练入口都会统一落到这里'),
  },
  {
    label: '当前位置',
    value: currentQuestionListLabel.value.replace(/^当前(定位|考点|章节|范围)：/, ''),
    helper: practiceFilterNotice.value || '当前范围会跟随统一 query 协议变化',
  },
  {
    label: '当前主线',
    value: isMockModule.value
      ? (activePaper.value?.paperName || '先开始考试，再生成试卷')
      : isRiskRepairMode.value
      ? '优先修复高风险题'
      : (adaptiveQuestionIds.value.length ? `完成 ${adaptiveQuestionIds.value.length} 道定向题` : '沿当前路径持续推进'),
    helper: `${answeredQuestionCount.value} 题已答，剩余 ${Math.max((questionRows.length || 0) - answeredQuestionCount.value, 0)} 题`,
  },
]))

const isFilterCollapseExpanded = computed(() => filterCollapsePanels.value.includes('scope'))

const currentSubjectPracticeTree = computed(() => {
  const sourceRows = Array.isArray(dashboardPayload.value?.chapterPracticeTree)
    ? dashboardPayload.value.chapterPracticeTree
    : []
  const targetSubjectId = toText(currentSubject.value?.subjectId)
  const targetSubjectName = currentSubjectName.value
  return sourceRows.find((subjectRow) => {
    const rowSubjectId = toText(subjectRow?.subjectId)
    const rowSubjectName = toText(subjectRow?.subjectName)
    if (targetSubjectId && rowSubjectId && rowSubjectId === targetSubjectId) {
      return true
    }
    return targetSubjectName && rowSubjectName && rowSubjectName === targetSubjectName
  }) || null
})

const currentSubjectChapterMetaMap = computed(() => {
  const chapterRows = Array.isArray(currentSubjectPracticeTree.value?.chapters)
    ? currentSubjectPracticeTree.value.chapters
    : []
  return new Map(
    chapterRows
      .map((item) => [toText(item?.chapter), item])
      .filter(([label]) => Boolean(label)),
  )
})

const chapterFilterRows = computed(() => {
  const selectorState = knowledgeSelectorState.value || {}
  const graphIndex = selectorState?.graphIndex || {}
  const nodeMap = graphIndex?.nodeMap || {}
  const levelById = graphIndex?.levelById || {}
  const sortChildIds = typeof graphIndex?.sortChildIds === 'function'
    ? graphIndex.sortChildIds
    : (rows) => rows
  const chapterCodeMap = selectorState?.chapterCodeMap || {}
  const chapterIds = sortChildIds(
    Object.keys(nodeMap).filter((nodeId) => Number(levelById[nodeId] || 0) === 4),
  )

  return chapterIds.map((chapterId) => {
    const label = toText(nodeMap[chapterId]?.label || chapterId)
    const dashboardMeta = currentSubjectChapterMetaMap.value.get(label) || {}
    const hasUnlockState = typeof dashboardMeta?.isUnlocked === 'boolean'
    const isUnlocked = hasUnlockState ? Boolean(dashboardMeta?.isUnlocked || dashboardMeta?.isCurrent) : true
    return {
      id: chapterId,
      label,
      chapterCode: toText(chapterCodeMap[chapterId]),
      questionCount: Math.max(
        Number(nodeMap[chapterId]?.questionCount || 0),
        Number(dashboardMeta?.total || 0),
      ),
      accuracyPercent: normalizePracticePercent(dashboardMeta?.accuracyPercent ?? dashboardMeta?.accuracy ?? 0),
      statusLabel: toText(
        dashboardMeta?.statusLabel
        || (dashboardMeta?.isCurrent ? '正在闯关' : hasUnlockState && !isUnlocked ? '未解锁' : '已解锁'),
      ),
      isUnlocked,
      isCurrent: Boolean(dashboardMeta?.isCurrent),
      hasUnlockState,
      pathLabel: [currentSubjectName.value, label].filter((item) => item).join(' / '),
    }
  })
})

const unlockedChapterCount = computed(() =>
  chapterFilterRows.value.filter((item) => !item.hasUnlockState || item.isUnlocked).length,
)

const l5PointCount = computed(() => {
  const graphIndex = knowledgeSelectorState.value?.graphIndex || {}
  const levelById = graphIndex?.levelById || {}
  return Object.keys(levelById).filter((nodeId) => Number(levelById[nodeId] || 0) >= 5).length
})

const knowledgeLevelTabs = [
  { level: 3, label: 'L3', title: '模块层', description: '按总知识模块收题' },
  { level: 4, label: 'L4', title: '章节层', description: '按章节范围收题' },
  { level: 5, label: 'L5', title: '考点层', description: '按原子考点收题' },
]

const chapterKnowledgeLevelColumns = computed(() => {
  const selectorState = knowledgeSelectorState.value || {}
  const graphIndex = selectorState?.graphIndex || {}
  const nodeMap = graphIndex?.nodeMap || {}
  const levelById = graphIndex?.levelById || {}
  const sortChildIds = typeof graphIndex?.sortChildIds === 'function'
    ? graphIndex.sortChildIds
    : (rows) => rows
  const pathById = graphIndex?.pathById || {}
  const labelMap = selectorState?.labelMap || {}
  const chapterCodeMap = selectorState?.chapterCodeMap || {}
  const pointCodeMap = selectorState?.pointCodeMap || {}

  const l3Rows = sortChildIds(
    Object.keys(nodeMap).filter((nodeId) => Number(levelById[nodeId] || 0) === 3),
  )
  const l4Rows = sortChildIds(
    Object.keys(nodeMap).filter((nodeId) => Number(levelById[nodeId] || 0) === 4),
  ).filter((nodeId) => {
    if (!selectedL3NodeId.value) {
      return true
    }
    const pathIds = Array.isArray(pathById[nodeId]) ? pathById[nodeId] : [nodeId]
    return pathIds.includes(selectedL3NodeId.value)
  })
  const l5Rows = sortChildIds(
    Object.keys(nodeMap).filter((nodeId) => Number(levelById[nodeId] || 0) >= 5),
  ).filter((nodeId) => {
    const pathIds = Array.isArray(pathById[nodeId]) ? pathById[nodeId] : [nodeId]
    if (selectedL4NodeId.value) {
      return pathIds.includes(selectedL4NodeId.value)
    }
    if (selectedL3NodeId.value) {
      return pathIds.includes(selectedL3NodeId.value)
    }
    return true
  })
  const rowMap = {
    3: l3Rows,
    4: l4Rows,
    5: l5Rows,
  }

  return knowledgeLevelTabs.map((tab) => {
    const rows = (rowMap[tab.level] || []).map((nodeId) => {
      const pathIds = Array.isArray(pathById[nodeId]) ? pathById[nodeId] : [nodeId]
      const pathLabel = pathIds.map((pathNodeId) => toText(labelMap[pathNodeId] || nodeMap[pathNodeId]?.label || pathNodeId)).join(' / ')
      return {
        id: nodeId,
        level: Number(levelById[nodeId] || 0),
        label: toText(nodeMap[nodeId]?.label || nodeId),
        chapterCode: toText(chapterCodeMap[nodeId]),
        pointCode: toText(pointCodeMap[nodeId]),
        pathLabel,
        isActive:
          (Number(levelById[nodeId] || 0) === 3 && practiceKnowledgePathNodeId.value === nodeId)
          || (Number(levelById[nodeId] || 0) === 4 && practiceChapterCode.value && practiceChapterCode.value === toText(chapterCodeMap[nodeId]) && !practiceKnowledgeId.value)
          || (Number(levelById[nodeId] || 0) >= 5 && practiceKnowledgeId.value === nodeId),
      }
    })
    return {
      ...tab,
      rows,
    }
  })
})

const l3SelectOptions = computed(() =>
  (chapterKnowledgeLevelColumns.value.find((item) => item.level === 3)?.rows || []).map((item) => ({
    value: item.id,
    label: item.label,
  })),
)

const l4SelectOptions = computed(() =>
  (chapterKnowledgeLevelColumns.value.find((item) => item.level === 4)?.rows || []).map((item) => ({
    value: item.id,
    label: item.label,
  })),
)

const l5SelectOptions = computed(() =>
  (chapterKnowledgeLevelColumns.value.find((item) => item.level === 5)?.rows || []).map((item) => ({
    value: item.id,
    label: item.label,
  })),
)

const practiceSummaryCards = computed(() => {
  const sharedCards = [
    { label: '当前题量', value: Number(questionTotal.value || questionRows.value.length || 0), helper: isMockModule.value ? '试卷题量实时同步' : '筛选结果实时刷新' },
    {
      label: '刷题段位分',
      value: Number(currentChallengePoints.value?.total || 0),
      helper: currentChallengePoints.value?.nextLevelName
        ? `今日 +${Number(currentChallengePoints.value?.todayDelta || 0)} · ${toText(currentChallengePoints.value?.levelName || '刷题青铜')} · 再积 ${Number(currentChallengePoints.value?.pointsToNextLevel || 0)} 分到 ${toText(currentChallengePoints.value?.nextLevelName)}`
        : `今日 +${Number(currentChallengePoints.value?.todayDelta || 0)} · ${toText(currentChallengePoints.value?.levelName || '刷题青铜')} · 当前已满阶`,
    },
    {
      label: '累计答对题次',
      value: Number(currentChallengePoints.value?.correctSubmitCount || currentChallengePoints.value?.total || 0),
      helper: `今日 +${Number(currentChallengePoints.value?.todayCorrectSubmitCount || currentChallengePoints.value?.todayDelta || 0)}`,
    },
    { label: '科目排名', value: currentChallengePoints.value?.rank ? `#${currentChallengePoints.value.rank}` : '未上榜', helper: currentSubjectName.value },
    { label: '升本口径', value: '答对 1 题 = 1 分', helper: challengeRuleHelperText.value },
  ]
  if (isMockModule.value || isFreeModule.value) {
    return sharedCards
  }
  return [
    sharedCards[0],
    { label: 'L4 章节', value: Number(chapterFilterRows.value.length || 0), helper: `已解锁 ${unlockedChapterCount.value}` },
    { label: 'L5 考点', value: Number(l5PointCount.value || 0), helper: '支持直接搜索' },
    sharedCards[4],
  ]
})

const questionOutlineRows = computed(() =>
  questionRows.value.map((row, index) => ({
    id: toText(row?.id || `question-${index + 1}`),
    index,
    typeLabel: questionTypeLabel(row?.type),
    stem: toText(row?.stem),
    isAnswered: Boolean(toText(selectedAnswers[toText(row?.id)])),
    isMarked: Boolean(markedQuestions[toText(row?.id)]),
    knowledgeTags: (() => {
      const ext = parseExtJson(row?.extJson)
      const tags = Array.isArray(ext?.knowledgeTags) ? ext.knowledgeTags : []
      return tags.map((item) => toText(item)).filter((item) => item).slice(0, 2)
    })(),
  })),
)

const emptyDescription = computed(() => {
  if (!practiceSubjectCode.value && !scopedSubjectOptions.value.length) {
    return '当前账号下暂无可练习科目，请先补齐学生科目绑定或内容基线。'
  }
  if (isMockModule.value) {
    return '当前科目下暂无可参加的模拟卷，请切换科目或联系老师发布试卷。'
  }
  if (practiceKnowledgeId.value || practicePointCode.value) {
    return '该 L5 原子考点下暂未命中可练习题目，请尝试切换相邻章节或清空精准定位。'
  }
  if (practiceChapterCode.value) {
    return '该章节下暂未命中可练习题目，请尝试切换其他章节。'
  }
  return '当前筛选范围暂无可练习题目，请调整顶部筛选条件。'
})

function resolveKnowledgeFilterPathByRoute() {
  const selectorState = knowledgeSelectorState.value || {}
  const pathMap = selectorState?.pathMap || {}
  const pointCodeMap = selectorState?.pointCodeMap || {}

  if (practiceKnowledgeId.value && Array.isArray(pathMap[practiceKnowledgeId.value])) {
    return pathMap[practiceKnowledgeId.value]
  }

  const matchedPointEntry = Object.entries(pointCodeMap).find(
    ([, pointCode]) => toText(pointCode) === practicePointCode.value,
  )
  if (matchedPointEntry && Array.isArray(pathMap[matchedPointEntry[0]])) {
    return pathMap[matchedPointEntry[0]]
  }

  return []
}

function syncSelectedKnowledgePathFromRoute() {
  selectedKnowledgePath.value = resolveKnowledgeFilterPathByRoute()
  const selectorState = knowledgeSelectorState.value || {}
  const graphIndex = selectorState?.graphIndex || {}
  const levelById = graphIndex?.levelById || {}
  const pathById = graphIndex?.pathById || {}

  selectedL3NodeId.value = ''
  selectedL4NodeId.value = ''
  selectedL5NodeId.value = ''

  const targetNodeId = practiceKnowledgeId.value || practiceKnowledgePathNodeId.value
  const pathIds = targetNodeId && Array.isArray(pathById[targetNodeId]) ? pathById[targetNodeId] : []
  pathIds.forEach((pathNodeId) => {
    const level = Number(levelById[pathNodeId] || 0)
    if (level === 3) {
      selectedL3NodeId.value = pathNodeId
    } else if (level === 4) {
      selectedL4NodeId.value = pathNodeId
    } else if (level >= 5) {
      selectedL5NodeId.value = pathNodeId
    }
  })

  if (!selectedL4NodeId.value && practiceChapterCode.value) {
    const matchedL4 = chapterFilterRows.value.find((item) => item.chapterCode === practiceChapterCode.value)
    selectedL4NodeId.value = toText(matchedL4?.id)
  }

  if (practiceKnowledgeId.value) {
    selectedL5NodeId.value = practiceKnowledgeId.value
  }
}

function resetQuestionState() {
  activeQuestionIndex.value = 0
  Object.keys(selectedAnswers).forEach((questionId) => {
    delete selectedAnswers[questionId]
  })
  Object.keys(markedQuestions).forEach((questionId) => {
    delete markedQuestions[questionId]
  })
}

function buildMockExamDraftPayload() {
  const answers = {}
  const marks = {}
  questionRows.value.forEach((row) => {
    const questionId = toText(row?.id)
    if (!questionId) {
      return
    }
    const answer = toText(selectedAnswers[questionId])
    if (answer) {
      answers[questionId] = answer
    }
    if (markedQuestions[questionId]) {
      marks[questionId] = true
    }
  })
  return {
    paperId: toText(activePaper.value?.paperId),
    activeQuestionIndex: Number(activeQuestionIndex.value || 0),
    remainingSec: Number(mockExamRemainingSec.value || 0),
    paused: Boolean(mockExamPaused.value),
    answers,
    marks,
    updateTime: new Date().toISOString(),
  }
}

function persistMockExamDraft(force = false) {
  if (!isMockModule.value || !activePaper.value?.paperId || isMockExamSubmitted.value) {
    return
  }
  const storageKey = mockExamDraftStorageKey.value
  if (!storageKey) {
    return
  }
  if (!force && !questionRows.value.length) {
    return
  }
  writeSafeStorage(storageKey, JSON.stringify(buildMockExamDraftPayload()))
}

function clearMockExamDraft(paperId = toText(activePaper.value?.paperId)) {
  if (!paperId) {
    return
  }
  removeSafeStorage(`${MOCK_EXAM_DRAFT_PREFIX}${paperId}`)
}

function initializeMockExamCountdown() {
  const totalSec = Number(activePaper.value?.durationMinutes || 0) * 60
  mockExamRemainingSec.value = totalSec > 0 ? totalSec : 0
  mockExamPaused.value = false
}

function restoreMockExamDraft() {
  if (!isMockModule.value || !activePaper.value?.paperId || !questionRows.value.length) {
    return
  }
  const storageKey = mockExamDraftStorageKey.value
  if (!storageKey || draftRestoreStamp.value === storageKey) {
    return
  }

  initializeMockExamCountdown()
  const raw = readSafeStorage(storageKey)
  if (!raw) {
    draftRestoreStamp.value = storageKey
    return
  }

  try {
    const parsed = JSON.parse(raw)
    const answers = parsed?.answers && typeof parsed.answers === 'object' ? parsed.answers : {}
    const marks = parsed?.marks && typeof parsed.marks === 'object' ? parsed.marks : {}
    questionRows.value.forEach((row) => {
      const questionId = toText(row?.id)
      if (!questionId) {
        return
      }
      const answer = toText(answers[questionId])
      if (answer) {
        selectedAnswers[questionId] = answer
      }
      if (marks[questionId]) {
        markedQuestions[questionId] = true
      }
    })
    const remainingSec = Number(parsed?.remainingSec || 0)
    if (Number.isFinite(remainingSec) && remainingSec >= 0) {
      mockExamRemainingSec.value = remainingSec
    }
    mockExamPaused.value = Boolean(parsed?.paused)
    activeQuestionIndex.value = Math.max(0, Math.min(questionRows.value.length - 1, Number(parsed?.activeQuestionIndex || 0)))
  } catch (error) {
    initializeMockExamCountdown()
  }

  draftRestoreStamp.value = storageKey
}

function buildPaperAnswerPayload() {
  return questionRows.value
    .map((row) => {
      const questionId = toText(row?.id)
      return {
        questionId,
        answer: toText(selectedAnswers[questionId]),
        elapsedSec: clampElapsedSec(3600),
        marked: Boolean(markedQuestions[questionId]),
      }
    })
    .filter((item) => item.questionId && (item.answer || item.marked))
}

function buildPreviewPaperReport() {
  const submittedAt = new Date().toISOString()
  const questionResults = questionRows.value.map((row) => {
    const questionId = toText(row?.id)
    const answer = toText(selectedAnswers[questionId])
    const normalizedAnswer = answer.toUpperCase()
    const ext = parseExtJson(row?.extJson)
    const correctAnswer = toText(row?.answer).toUpperCase()
    const binding = Array.isArray(ext?.paperBindings) ? ext.paperBindings[0] || {} : {}
    const totalScore = Number(binding?.questionScore || 0)
    const isCorrect = Boolean(correctAnswer) && normalizedAnswer === correctAnswer
    return {
      questionId,
      type: toText(row?.type),
      stem: toText(row?.stem),
      optionsJson: toText(row?.optionsJson || '[]'),
      correctAnswer,
      analysis: toText(ext?.analysis || ''),
      answer,
      normalizedAnswer,
      isCorrect,
      isPendingAiMarking: false,
      marked: Boolean(markedQuestions[questionId]),
      elapsedSec: clampElapsedSec(3600),
      score: isCorrect ? totalScore : 0,
      totalScore,
    }
  })
  const score = questionResults.reduce((sum, item) => sum + Number(item.score || 0), 0)
  const totalScore = questionResults.reduce((sum, item) => sum + Number(item.totalScore || 0), 0)
  const wrongQuestionIds = questionResults.filter((item) => !item.isCorrect).map((item) => item.questionId)
  const markedCount = questionResults.filter((item) => item.marked).length
  const reportId = `paper-report-preview-${Date.now()}`

  return {
    reportId,
    paperId: toText(activePaper.value?.paperId),
    subjectId: practiceSubjectCode.value,
    score,
    totalScore,
    totalElapsedSec: Number(currentElapsedSec()),
    wrongQuestionIds,
    pendingSubjectiveTaskIds: [],
    pendingSubjectiveCount: 0,
    submittedAt,
    summary: {
      questionCount: questionResults.length,
      markedCount,
      correctCount: questionResults.length - wrongQuestionIds.length,
      wrongCount: wrongQuestionIds.length,
    },
    questionResults,
  }
}

async function submitMockPaperWithCheck({ autoSubmit = false } = {}) {
  if (!activePaper.value?.paperId || isMockExamSubmitted.value) {
    return
  }

  mockExamSubmitDialogVisible.value = false
  mockExamSubmittingPaper.value = true
  try {
    let report = null
    if (usingMockExamPreview.value && isMockExamPreviewPaper(activePaper.value.paperId)) {
      report = buildPreviewPaperReport()
    } else {
      const response = await submitStudentPaper(activePaper.value.paperId, {
        answers: buildPaperAnswerPayload(),
        totalElapsedSec: clampElapsedSec(14400),
      })
      const submitResult = response?.data || response || {}
      report = submitResult
      if (submitResult?.reportId) {
        try {
          const detail = await getStudentPaperReportDetail(submitResult.reportId)
          report = { ...submitResult, ...(detail?.data || detail || {}) }
        } catch (error) {
          report = submitResult
        }
      }
    }

    mockExamLastReport.value = report
    const assignmentId = toText(route.query.assignmentId)
    if (assignmentId && report?.reportId) {
      try {
        await submitStudentExamTask(assignmentId, {
          paperId: toText(report?.paperId),
          score: Number(report?.score || 0),
          totalScore: Number(report?.totalScore || 0),
          pendingSubjectiveCount: Number(report?.pendingSubjectiveCount || 0),
          submittedAt: toText(report?.submittedAt),
        })
      } catch (error) {
        ElMessage.warning('考试任务状态回写失败，但本次模考报告已生成。')
      }
    }
    studentMessageText.value = autoSubmit ? '系统已自动交卷，本次模考报告已生成。' : '模考已交卷，本次模考报告已生成。'
    mockExamPaused.value = false
    clearMockExamDraft()
    if (autoSubmit) {
      ElMessage.warning('倒计时已结束，系统已自动交卷。')
    } else {
      ElMessage.success('交卷成功，已生成本次模考报告。')
    }
  } catch (error) {
    ElMessage.error(toText(error?.response?.data?.message || error?.message || '模拟考试交卷失败'))
  } finally {
    mockExamSubmittingPaper.value = false
  }
}

function openMockSubmitCheck() {
  if (!isMockModule.value || !activePaper.value?.paperId || isMockExamSubmitted.value) {
    return
  }
  mockExamSubmitDialogVisible.value = true
}

function handleMarkedToggle(questionId, checked) {
  const normalizedQuestionId = toText(questionId)
  if (!normalizedQuestionId || isMockExamSubmitted.value) {
    return
  }
  if (checked) {
    markedQuestions[normalizedQuestionId] = true
  } else {
    delete markedQuestions[normalizedQuestionId]
  }
  persistMockExamDraft(true)
}

function toggleMockExamPause() {
  if (!isMockModule.value || !activePaper.value?.paperId || isMockExamSubmitted.value) {
    return
  }
  mockExamPaused.value = !mockExamPaused.value
  persistMockExamDraft(true)
}

async function initializeSession() {
  const localSessionId = toText(localStorage.getItem(SESSION_STORAGE_KEY))
  try {
    let sessionData
    if (localSessionId) {
      sessionData = await getStudentSession(localSessionId)
    } else {
      sessionData = await createStudentSession()
    }
    const normalizedSessionId = toText(sessionData?.sessionId || localSessionId || `session-${Date.now()}`)
    sessionState.sessionId = normalizedSessionId
    sessionState.answeredCount = Number(sessionData?.answeredCount || 0)
    sessionState.elapsedSec = Number(sessionData?.elapsedSec || 0)
    sessionState.updateTime = toText(sessionData?.updateTime)
    sessionState.startedAtMs = Date.now()
    localStorage.setItem(SESSION_STORAGE_KEY, normalizedSessionId)
  } catch (error) {
    const fallbackSession = await createStudentSession()
    sessionState.sessionId = toText(fallbackSession?.sessionId || `session-${Date.now()}`)
    sessionState.answeredCount = Number(fallbackSession?.answeredCount || 0)
    sessionState.elapsedSec = Number(fallbackSession?.elapsedSec || 0)
    sessionState.updateTime = toText(fallbackSession?.updateTime)
    sessionState.startedAtMs = Date.now()
    localStorage.setItem(SESSION_STORAGE_KEY, sessionState.sessionId)
  }
}

async function loadContentBaselineScope() {
  baselineLoading.value = true
  try {
    const normalized = normalizeStudentDashboardDictionary(dashboardPayload.value || {})
    examCategoryOptions.value = Array.isArray(normalized?.examCategoryOptions) ? normalized.examCategoryOptions : []
    jointExamGroupOptions.value = Array.isArray(normalized?.jointExamGroupOptions) ? normalized.jointExamGroupOptions : []
    subjectCodeOptions.value = Array.isArray(normalized?.subjectCodeOptions) ? normalized.subjectCodeOptions : []
  } catch (error) {
    examCategoryOptions.value = []
    jointExamGroupOptions.value = []
    subjectCodeOptions.value = []
  } finally {
    baselineLoading.value = false
  }
}

function buildScopeQueryWithFallback({
  examCategoryCode = '',
  jointExamGroupCode = '',
  subjectCode = '',
} = {}) {
  const fallbackExamCategoryCode = toText(examCategoryCode)
    || scopedExamCategoryOptions.value[0]?.examCategoryCode
    || toText(userStore.examCategoryCode)

  const availableJointGroups = resolveJointGroupOptions(fallbackExamCategoryCode)
  const fallbackJointExamGroupCode = availableJointGroups.find(
    (item) => item.jointExamGroupCode === toText(jointExamGroupCode),
  )?.jointExamGroupCode
    || availableJointGroups[0]?.jointExamGroupCode
    || ''

  const availableSubjects = resolveSubjectScopeOptions(
    fallbackExamCategoryCode,
    fallbackJointExamGroupCode,
  )
  const resolvedSubjectCode = resolvePracticeSubjectCode(subjectCode, availableSubjects)
  const fallbackSubjectCode = availableSubjects.find(
    (item) => item.subjectCode === resolvedSubjectCode,
  )?.subjectCode
    || availableSubjects[0]?.subjectCode
    || toText(subjectOptions.value[0]?.subjectCode)
    || ''

  return sanitizePracticeQuery({
    examCategoryCode: fallbackExamCategoryCode,
    jointExamGroupCode: fallbackJointExamGroupCode,
    subjectCode: fallbackSubjectCode,
  })
}

async function normalizeInitialPracticeQuery() {
  const rawExamCategoryCode = toText(route.query.examCategoryCode)
  const rawJointExamGroupCode = toText(route.query.jointExamGroupCode)
  const rawSubjectCode = toText(route.query.subjectCode || subjectContextStore.currentSubjectCode)
  const normalizedScope = buildScopeQueryWithFallback({
    examCategoryCode: rawExamCategoryCode,
    jointExamGroupCode: rawJointExamGroupCode,
    subjectCode: rawSubjectCode,
  })

  const nextQuery = sanitizePracticeQuery({
    ...route.query,
    ...normalizedScope,
    module: practiceModule.value,
    immersive: isFreeModule.value ? '1' : toText(route.query.immersive),
  })

  const scopeChanged =
    rawExamCategoryCode !== toText(normalizedScope.examCategoryCode)
    || rawJointExamGroupCode !== toText(normalizedScope.jointExamGroupCode)
    || rawSubjectCode !== toText(normalizedScope.subjectCode)

  if (scopeChanged) {
    Object.assign(nextQuery, clearPracticePathQuery(nextQuery))
  }

  if (
    toText(route.query.module) !== toText(nextQuery.module)
    || toText(route.query.immersive) !== toText(nextQuery.immersive)
    || rawExamCategoryCode !== toText(nextQuery.examCategoryCode)
    || rawJointExamGroupCode !== toText(nextQuery.jointExamGroupCode)
    || rawSubjectCode !== toText(nextQuery.subjectCode)
  ) {
    await router.replace({ path: expectedPath.value, query: nextQuery })
  }
}

async function loadKnowledgeFilterTree() {
  if (isMockModule.value || !practiceSubjectCode.value) {
    knowledgeSelectorState.value = buildKnowledgeSelectorState({})
    preciseKnowledgeOptions.value = []
    knowledgePathLabelMap.value = {}
    selectedKnowledgePath.value = []
    return
  }

  knowledgeTreeLoading.value = true
  try {
    const response = await knowledgeTreeV2({
      status: 'ENABLED',
      subjectCode: practiceSubjectCode.value,
    })
    const selectorState = buildKnowledgeSelectorState(response?.data || response || {})
    const preciseLevelTreeState = buildKnowledgeLevelTreeState(selectorState, {
      startLevel: 4,
      endLevel: 5,
    })
    knowledgeSelectorState.value = selectorState
    preciseKnowledgeOptions.value = Array.isArray(preciseLevelTreeState?.options)
      ? preciseLevelTreeState.options
      : []
    knowledgePathLabelMap.value = preciseLevelTreeState?.pathLabelMap || {}
    syncSelectedKnowledgePathFromRoute()
  } catch (error) {
    knowledgeSelectorState.value = buildKnowledgeSelectorState({})
    preciseKnowledgeOptions.value = []
    knowledgePathLabelMap.value = {}
    selectedKnowledgePath.value = []
    ElMessage.error(toText(error?.response?.data?.message || error?.message || '知识筛选树加载失败'))
  } finally {
    knowledgeTreeLoading.value = false
  }
}

async function collectQuestionRows(baseQuestionList, {
  pageSize = 20,
  maxPages = 1,
} = {}) {
  const collectedRows = []
  let page = 1
  let total = 0

  while (page <= maxPages) {
    const pageData = await baseQuestionList(page, pageSize)
    total = Number(pageData?.total || 0)
    const items = Array.isArray(pageData?.items) ? pageData.items : []
    collectedRows.push(...items)
    if (!items.length || collectedRows.length >= total || page >= maxPages) {
      break
    }
    page += 1
  }

  return {
    rows: collectedRows,
    total: total || collectedRows.length,
  }
}

async function loadQuestionRows() {
  if (isMockModule.value) {
    if (!activePaper.value?.paperId) {
      questionRows.value = []
      questionTotal.value = 0
      resetQuestionState()
      return
    }
    if (usingMockExamPreview.value && isMockExamPreviewPaper(activePaper.value.paperId)) {
      questionRows.value = listMockExamPreviewQuestions(activePaper.value.paperId, {
        subjectCode: practiceSubjectCode.value,
        subjectName: currentSubjectName.value,
      })
      questionTotal.value = Number(questionRows.value.length || 0)
      resetQuestionState()
      return
    }
    const paperPage = await listStudentPaperQuestions(activePaper.value.paperId, { page: 1, size: 200 })
    const paperData = paperPage?.data && typeof paperPage.data === 'object' && Array.isArray(paperPage.data.items)
      ? paperPage.data
      : paperPage
    questionRows.value = Array.isArray(paperData?.items) ? paperData.items : []
    questionTotal.value = Number(paperData?.total || questionRows.value.length || 0)
    resetQuestionState()
    return
  }

  const baseQuestionList = async (page = 1, size = 20) =>
    fetchStudentPracticeQuestionList({
      page,
      size,
      examCategoryCode: practiceExamCategoryCode.value,
      jointExamGroupCode: practiceJointExamGroupCode.value,
      subjectCode: practiceSubjectCode.value,
      knowledgeId: practiceKnowledgeId.value,
      knowledgePathNodeId: practiceKnowledgePathNodeId.value,
      chapterCode: practiceChapterCode.value,
      pointCode: practicePointCode.value,
      module: practiceModule.value,
    })

  const targetIds = adaptiveQuestionIds.value

  if (!targetIds.length) {
    const shouldExpandFetch = Boolean(practiceKnowledgeId.value || practicePointCode.value || practiceChapterCode.value)
    const pageData = await collectQuestionRows(baseQuestionList, {
      pageSize: shouldExpandFetch ? 60 : 20,
      maxPages: shouldExpandFetch ? 6 : 1,
    })
    questionRows.value = pageData.rows
    questionTotal.value = Number(pageData.total || pageData.rows.length || 0)
    resetQuestionState()
    return
  }

  const questionIdOrder = new Map(targetIds.map((questionId, index) => [questionId, index]))
  const collectedRows = new Map()
  const pageSize = Math.min(100, Math.max(20, targetIds.length * 5))
  let page = 1
  let total = 0

  while (page === 1 || ((page - 1) * pageSize) < total) {
    const pageData = await baseQuestionList(page, pageSize)
    total = Number(pageData?.total || 0)
    const items = Array.isArray(pageData?.items) ? pageData.items : []
    items.forEach((item) => {
      const questionId = toText(item?.id)
      if (!questionId || !questionIdOrder.has(questionId) || collectedRows.has(questionId)) {
        return
      }
      collectedRows.set(questionId, item)
    })
    if (collectedRows.size >= targetIds.length || page >= 6 || !items.length) {
      break
    }
    page += 1
  }

  const adaptiveRows = targetIds
    .map((questionId) => collectedRows.get(questionId))
    .filter((item) => item)

  if (!adaptiveRows.length) {
    const fallbackPage = await baseQuestionList(1, 20)
    questionRows.value = Array.isArray(fallbackPage?.items) ? fallbackPage.items : []
    questionTotal.value = Number(fallbackPage?.total || questionRows.value.length || 0)
    ElMessage.warning('强化题单未命中可练习题，已回退到常规题单。')
  } else {
    questionRows.value = adaptiveRows
    questionTotal.value = adaptiveRows.length
  }

  resetQuestionState()
}

async function loadMockPaperOptions() {
  if (!isMockModule.value) {
    availablePaperRows.value = []
    usingMockExamPreview.value = false
    mockExamSession.value = null
    return
  }
  const sessionId = toText(route.query.sessionId)
  const directPaperId = toText(route.query.paperId)
  const directPaperName = toText(route.query.paperName)
  if (!sessionId && directPaperId) {
    mockExamSession.value = {
      id: '',
      paperId: directPaperId,
      paperName: directPaperName || '指定模拟卷',
      questionCount: 0,
      totalScore: 0,
      durationMinutes: 0,
    }
    availablePaperRows.value = []
    usingMockExamPreview.value = false
    return
  }
  if (!sessionId) {
    availablePaperRows.value = []
    usingMockExamPreview.value = false
    mockExamSession.value = null
    return
  }
  try {
    const response = await getStudentMockExamSession(sessionId)
    const payload = response?.data || response || {}
    mockExamSession.value = payload
    availablePaperRows.value = []
    usingMockExamPreview.value = false
  } catch (error) {
    mockExamSession.value = null
    availablePaperRows.value = []
    usingMockExamPreview.value = false
  }
}

async function handleMockPaperChange(nextPaperId) {
  await replacePracticeScopeQuery({
    ...route.query,
    module: practiceModule.value,
    subjectCode: practiceSubjectCode.value,
    paperId: toText(nextPaperId),
    sessionId: toText(route.query.sessionId),
    immersive: '1',
  })
}

async function handleStartMockExam() {
  if (!practiceSubjectCode.value) {
    ElMessage.warning('请先选择当前考试科目。')
    return
  }
  pageLoading.value = true
  try {
    const response = await startStudentMockExam({
      subjectCode: practiceSubjectCode.value,
      examCategoryCode: practiceExamCategoryCode.value,
      jointExamGroupCode: practiceJointExamGroupCode.value,
    })
    const payload = response?.data || response || {}
    mockExamSession.value = payload
    await replacePracticeScopeQuery({
      ...route.query,
      module: practiceModule.value,
      subjectCode: practiceSubjectCode.value,
      paperId: toText(payload?.paperId),
      sessionId: toText(payload?.id),
      immersive: '1',
    })
    ElMessage.success('模拟考试已生成，开始作答吧。')
  } catch (error) {
    ElMessage.error(toText(error?.response?.data?.message || error?.message || '模拟考试生成失败'))
  } finally {
    pageLoading.value = false
  }
}

async function syncExamTaskSubmission(extraPayload = {}) {
  const assignmentId = toText(route.query.assignmentId)
  if (!assignmentId) {
    return
  }
  await submitStudentExamTask(assignmentId, extraPayload)
}

function resolveLearningMethodFeedbackProgress() {
  const targetQuestionIds = adaptiveQuestionIds.value.map((item) => toText(item)).filter(Boolean)
  if (!targetQuestionIds.length) {
    return {
      targetQuestionIds: [],
      completedQuestionIds: [],
      skippedQuestionIds: [],
    }
  }
  const completedQuestionIds = targetQuestionIds.filter((questionId) => Boolean(toText(selectedAnswers[questionId])))
  const completedIdSet = new Set(completedQuestionIds)
  const skippedQuestionIds = targetQuestionIds.filter((questionId) => !completedIdSet.has(questionId))
  return {
    targetQuestionIds,
    completedQuestionIds,
    skippedQuestionIds,
  }
}

async function maybeSubmitLearningMethodAutoFeedback({
  feedbackStatus = 'ACCEPTED',
  silent = false,
} = {}) {
  const normalizedFeedbackStatus = toText(feedbackStatus).toUpperCase()
  if (!isLearningMethodRecommendationPractice.value) {
    return false
  }
  if (learningMethodAutoFeedbackSubmitting.value) {
    return false
  }
  if (
    learningMethodAutoFeedbackStatus.value === 'ACCEPTED'
    || learningMethodAutoFeedbackStatus.value === normalizedFeedbackStatus
  ) {
    return false
  }

  const { targetQuestionIds, completedQuestionIds, skippedQuestionIds } = resolveLearningMethodFeedbackProgress()
  if (!targetQuestionIds.length) {
    return false
  }

  if (normalizedFeedbackStatus === 'ACCEPTED' && completedQuestionIds.length < targetQuestionIds.length) {
    return false
  }
  if (
    normalizedFeedbackStatus === 'PARTIAL'
    && (completedQuestionIds.length === 0 || completedQuestionIds.length >= targetQuestionIds.length)
  ) {
    return false
  }

  const feedbackNote = normalizedFeedbackStatus === 'PARTIAL'
    ? '学生在未完成全部推荐题时离开刷题页，系统自动回写部分匹配反馈。'
    : '学生在刷题页完成学习方法推荐题包，系统自动回写反馈。'

  learningMethodAutoFeedbackSubmitting.value = true
  try {
    await submitLearningMethodQuestionPackFeedback(learningMethodCode.value, {
      recommendationId: learningMethodRecommendationId.value,
      sessionId: learningMethodSessionId.value || sessionState.sessionId,
      feedbackStatus: normalizedFeedbackStatus,
      isHelpful: normalizedFeedbackStatus !== 'REJECTED',
      completedQuestionIds,
      skippedQuestionIds,
      note: feedbackNote,
    })
    learningMethodAutoFeedbackStatus.value = normalizedFeedbackStatus
    saveLearningMethodFeedbackNotice({
      feedbackStatus: normalizedFeedbackStatus,
      methodCode: learningMethodCode.value,
      recommendationId: learningMethodRecommendationId.value,
    })
    return true
  } catch (error) {
    if (!silent) {
      ElMessage.warning(toText(error?.response?.data?.message || error?.message || '学习方法反馈回写失败，可稍后在学习方法页手动反馈。'))
    }
    return false
  } finally {
    learningMethodAutoFeedbackSubmitting.value = false
  }
}

async function handleBackToLearningMethods() {
  if (!canBackToLearningMethods.value) {
    return
  }
  learningMethodReturnLoading.value = true
  try {
    await maybeSubmitLearningMethodAutoFeedback({
      feedbackStatus: 'PARTIAL',
      silent: true,
    })
    await router.push({
      path: '/student/question-bank/learning-methods',
      query: {
        fromPracticeReturn: '1',
        subjectCode: practiceSubjectCode.value,
        learningMethodCode: learningMethodCode.value,
        learningMethodRecommendationId: learningMethodRecommendationId.value,
        learningMethodSessionId: learningMethodSessionId.value || sessionState.sessionId,
      },
    })
  } catch (error) {
    ElMessage.error(toText(error?.message || '返回学习方法页失败，请稍后重试。'))
  } finally {
    learningMethodReturnLoading.value = false
  }
}

async function navigateToPracticeModule(nextModule) {
  const normalizedModule = toText(nextModule).toLowerCase()
  if (!normalizedModule || normalizedModule === practiceModule.value) {
    return
  }
  if (isLearningMethodRecommendationPractice.value) {
    await maybeSubmitLearningMethodAutoFeedback({ feedbackStatus: 'PARTIAL', silent: true })
  }
  const nextLocation = buildStudentPracticeRouteLocation({
    module: normalizedModule,
    subjectCode: practiceSubjectCode.value,
    knowledgeId: normalizedModule === STUDENT_PRACTICE_MODULE.MOCK ? '' : practiceKnowledgeId.value,
    chapterCode: normalizedModule === STUDENT_PRACTICE_MODULE.CHAPTER ? practiceChapterCode.value : '',
    chapterName: normalizedModule === STUDENT_PRACTICE_MODULE.CHAPTER ? practiceChapterName.value : '',
    pointCode: normalizedModule === STUDENT_PRACTICE_MODULE.CHAPTER ? practicePointCode.value : '',
    pointName: normalizedModule === STUDENT_PRACTICE_MODULE.CHAPTER ? practicePointName.value : '',
    pathLabel: normalizedModule === STUDENT_PRACTICE_MODULE.CHAPTER ? practicePathLabel.value : '',
    practiceSource: practiceSource.value,
    practiceSourceLabel: practiceSourceLabel.value,
    extraQuery: {
      immersive: normalizedModule === STUDENT_PRACTICE_MODULE.FREE ? '1' : '',
    },
  })
  await router.push(nextLocation)
}

async function persistAnswer(questionId, answerValue) {
  const normalizedAnswer = toText(answerValue)
  if (!questionId || !normalizedAnswer || !sessionState.sessionId) {
    return
  }
  savingAnswer.value = true
  try {
    const submitResult = await updateStudentSessionAnswer(
      sessionState.sessionId,
      questionId,
      {
        answer: normalizedAnswer,
        answeredCount: answeredQuestionCount.value,
        elapsedSec: currentElapsedSec(),
        sourceType: isFreeModule.value ? 'FREE_PRACTICE' : 'CHAPTER_CHALLENGE',
        assignmentId: toText(route.query.assignmentId),
        attemptKey: createAttemptId(isFreeModule.value ? 'free' : 'chapter'),
      },
    )
    sessionState.answeredCount = Number(submitResult?.answeredCount || answeredQuestionCount.value)
    sessionState.elapsedSec = Number(submitResult?.elapsedSec || currentElapsedSec())
    sessionState.updateTime = toText(submitResult?.updateTime)
    sessionState.startedAtMs = Date.now()
    if (submitResult?.challengePoints && typeof submitResult.challengePoints === 'object') {
      challengePointsState.value = submitResult.challengePoints
    }
    if (Number(submitResult?.challengePointDelta || 0) > 0) {
      ElMessage.success(buildChallengePointToast(submitResult))
    }
  } catch (error) {
    ElMessage.error(toText(error?.response?.data?.message || error?.message || '答案保存失败'))
  } finally {
    savingAnswer.value = false
  }
}

async function persistMockAnswer(questionId, answerValue) {
  const normalizedAnswer = toText(answerValue)
  if (!questionId || !normalizedAnswer || !activePaper.value?.paperId) {
    return
  }
  if (usingMockExamPreview.value && isMockExamPreviewPaper(activePaper.value.paperId)) {
    sessionState.answeredCount = answeredQuestionCount.value
    sessionState.elapsedSec = Number(currentElapsedSec())
    sessionState.updateTime = new Date().toISOString()
    sessionState.startedAtMs = Date.now()
    persistMockExamDraft(true)
    return
  }
  savingAnswer.value = true
  try {
    const response = await submitStudentPaperQuestion(activePaper.value.paperId, questionId, {
      answer: normalizedAnswer,
      elapsedSec: currentElapsedSec(),
      sourceType: 'MOCK_EXAM',
      attemptKey: createAttemptId('mock'),
    })
    const submitResult = response?.data || response || {}
    sessionState.answeredCount = answeredQuestionCount.value
    sessionState.elapsedSec = Number(currentElapsedSec())
    sessionState.updateTime = new Date().toISOString()
    sessionState.startedAtMs = Date.now()
    if (submitResult?.challengePoints && typeof submitResult.challengePoints === 'object') {
      challengePointsState.value = submitResult.challengePoints
    }
    if (Number(submitResult?.challengePointDelta || 0) > 0) {
      ElMessage.success(buildChallengePointToast(submitResult))
    } else {
      ElMessage.success(Boolean(submitResult?.isCorrect) ? '本题答对，已记录作答。' : '本题已记录，继续下一题。')
    }
    persistMockExamDraft(true)
  } catch (error) {
    ElMessage.error(toText(error?.response?.data?.message || error?.message || '模考答题保存失败'))
  } finally {
    savingAnswer.value = false
  }
}

async function onAnswerChange(nextValue) {
  if (isMockExamSubmitted.value) {
    return
  }
  selectedAnswers[activeQuestionId.value] = toText(nextValue)
  if (isMockModule.value) {
    persistMockExamDraft(true)
    await persistMockAnswer(activeQuestionId.value, nextValue)
    return
  }
  // 章节闯关和自由练习：只保存选择，不自动提交，等用户点击按钮再提交
}

function toPreviousQuestion() {
  activeQuestionIndex.value = Math.max(0, activeQuestionIndex.value - 1)
  resetLoadingStates()
  if (isMockModule.value) {
    persistMockExamDraft(true)
  }
}

function toNextQuestion() {
  activeQuestionIndex.value = Math.min(questionRows.value.length - 1, activeQuestionIndex.value + 1)
  resetLoadingStates()
  if (isMockModule.value) {
    persistMockExamDraft(true)
  }
}

function jumpToQuestion(index) {
  activeQuestionIndex.value = Math.max(0, Math.min(questionRows.value.length - 1, Number(index || 0)))
  resetLoadingStates()
  if (isMockModule.value) {
    persistMockExamDraft(true)
  }
}

async function submitCurrentPractice() {
  const questionId = activeQuestionId.value
  const answer = toText(currentSelectedAnswer.value)
  if (!questionId) {
    ElMessage.warning('当前没有可提交题目。')
    return
  }
  if (isMockModule.value && isMockExamSubmitted.value) {
    ElMessage.warning('本次模考已经交卷，请切换试卷后继续。')
    return
  }
  if (isMockModule.value && mockExamPaused.value) {
    ElMessage.warning('当前考试处于暂停中，请先继续作答。')
    return
  }
  if (!answer) {
    ElMessage.warning('请先选择答案。')
    return
  }
  submittingPractice.value = true
  try {
    if (isMockModule.value) {
      await persistMockAnswer(questionId, answer)
      ElMessage.success('当前模考答案已确认。')
      return
    }
    await persistAnswer(questionId, answer)
    if (isFreeModule.value) {
      const autoFeedbackSubmitted = await maybeSubmitLearningMethodAutoFeedback()
      ElMessage.success(
        autoFeedbackSubmitted
          ? '当前自由练习答案已确认，学习方法推荐反馈已自动回写。'
          : '当前自由练习答案已确认。',
      )
      return
    }
    if (toText(activeQuestion.value?.type) !== 'subjective') {
      ElMessage.success('练习已提交，任务状态已更新。')
      return
    }
    const markingTask = await aiMarking.submitMarking(questionId, answerForAiMarking(), {
      assignmentId: toText(route.query.assignmentId),
    })
    await syncExamTaskSubmission({
      questionId,
      score: 0,
      totalScore: 100,
      pendingSubjectiveCount: 1,
      submittedAt: new Date().toISOString(),
      aiMarkingTaskId: toText(markingTask?.id || markingTask?.taskId),
    })
    if (isRiskRepairMode.value && isFocusedQuestionActive.value) {
      ElMessage.success('高风险题已提交，正在带你返回错题中心查看本题修复状态。')
      await router.push({
        path: '/student/question-bank/repair',
        query: {
          subjectCode: practiceSubjectCode.value,
          chapterCode: practiceChapterCode.value,
          chapterName: practiceChapterName.value,
          pointCode: practicePointCode.value,
          pointName: practicePointName.value || practicePointCode.value,
          knowledgeId: practiceKnowledgeId.value,
          knowledgePathNodeId: practiceKnowledgePathNodeId.value,
          pathLabel: practicePathLabel.value,
          focusQuestionId: questionId,
          focusSource: 'RISK_REPAIR',
        },
      })
      return
    }
    ElMessage.success('练习已提交，AI 批改任务已启动。')
  } catch (error) {
    ElMessage.error(toText(error?.response?.data?.message || error?.message || '提交练习失败'))
  } finally {
    submittingPractice.value = false
  }
}

async function replacePracticeScopeQuery(nextQuery) {
  if (practiceRouteActive.value && route.path === expectedPath.value) {
    await router.replace({
      path: expectedPath.value,
      query: sanitizePracticeQuery(nextQuery),
    })
  }
}

async function handleExamCategoryChange(nextExamCategoryCode) {
  const normalizedScope = buildScopeQueryWithFallback({
    examCategoryCode: nextExamCategoryCode,
    jointExamGroupCode: '',
    subjectCode: '',
  })
  let nextQuery = { ...route.query, ...normalizedScope }
  nextQuery = clearPracticePathQuery(nextQuery)
  nextQuery = clearPracticeTransientFocusQuery(nextQuery)
  await replacePracticeScopeQuery(nextQuery)
}

async function handleJointGroupChange(nextJointExamGroupCode) {
  const normalizedScope = buildScopeQueryWithFallback({
    examCategoryCode: practiceExamCategoryCode.value,
    jointExamGroupCode: nextJointExamGroupCode,
    subjectCode: '',
  })
  let nextQuery = { ...route.query, ...normalizedScope }
  nextQuery = clearPracticePathQuery(nextQuery)
  nextQuery = clearPracticeTransientFocusQuery(nextQuery)
  await replacePracticeScopeQuery(nextQuery)
}

async function handleKnowledgeLevelSelect(levelRow) {
  const level = Number(levelRow?.level || 0)
  let nextQuery = {
    ...route.query,
    examCategoryCode: practiceExamCategoryCode.value,
    jointExamGroupCode: practiceJointExamGroupCode.value,
    subjectCode: practiceSubjectCode.value,
  }
  nextQuery = clearPracticeTransientFocusQuery(nextQuery)
  nextQuery = clearPracticePathQuery(nextQuery)
  delete nextQuery.knowledgePathNodeId

  if (!levelRow?.id) {
    await replacePracticeScopeQuery(nextQuery)
    return
  }

  if (level === 3) {
    nextQuery.knowledgePathNodeId = toText(levelRow.id)
    nextQuery.pathLabel = toText(levelRow.pathLabel)
  } else if (level === 4) {
    nextQuery.knowledgePathNodeId = toText(levelRow.id)
    nextQuery.chapterCode = toText(levelRow.chapterCode)
    nextQuery.chapterName = toText(levelRow.label)
    nextQuery.pathLabel = toText(levelRow.pathLabel)
  } else {
    nextQuery.knowledgePathNodeId = toText(levelRow.id)
    nextQuery.knowledgeId = toText(levelRow.id)
    nextQuery.pointCode = toText(levelRow.pointCode)
    nextQuery.pointName = toText(levelRow.label)
    nextQuery.pathLabel = toText(levelRow.pathLabel)
  }

  await replacePracticeScopeQuery(nextQuery)
}

async function handleL3Select(nextNodeId) {
  selectedL3NodeId.value = toText(nextNodeId)
  selectedL4NodeId.value = ''
  selectedL5NodeId.value = ''
  const target = chapterKnowledgeLevelColumns.value.find((item) => item.level === 3)?.rows.find((item) => item.id === selectedL3NodeId.value)
  if (!target) {
    await handleKnowledgeLevelSelect(null)
    return
  }
  await handleKnowledgeLevelSelect(target)
}

async function handleL4Select(nextNodeId) {
  selectedL4NodeId.value = toText(nextNodeId)
  selectedL5NodeId.value = ''
  const target = chapterKnowledgeLevelColumns.value.find((item) => item.level === 4)?.rows.find((item) => item.id === selectedL4NodeId.value)
  if (!target) {
    const l3Target = chapterKnowledgeLevelColumns.value.find((item) => item.level === 3)?.rows.find((item) => item.id === selectedL3NodeId.value)
    await handleKnowledgeLevelSelect(l3Target || null)
    return
  }
  await handleKnowledgeLevelSelect(target)
}

async function handleL5Select(nextNodeId) {
  selectedL5NodeId.value = toText(nextNodeId)
  const target = chapterKnowledgeLevelColumns.value.find((item) => item.level === 5)?.rows.find((item) => item.id === selectedL5NodeId.value)
  if (!target) {
    const l4Target = chapterKnowledgeLevelColumns.value.find((item) => item.level === 4)?.rows.find((item) => item.id === selectedL4NodeId.value)
    await handleKnowledgeLevelSelect(l4Target || null)
    return
  }
  await handleKnowledgeLevelSelect(target)
}

async function handleKnowledgePathChange(nextPath) {
  const normalizedPath = Array.isArray(nextPath)
    ? nextPath.map((item) => toText(item)).filter((item) => item)
    : []
  const selectorState = knowledgeSelectorState.value || {}
  const graphIndex = selectorState?.graphIndex || {}
  const levelById = graphIndex?.levelById || {}
  const labelMap = selectorState?.labelMap || {}
  const chapterCodeMap = selectorState?.chapterCodeMap || {}
  const pointCodeMap = selectorState?.pointCodeMap || {}

  let nextQuery = {
    ...route.query,
    examCategoryCode: practiceExamCategoryCode.value,
    jointExamGroupCode: practiceJointExamGroupCode.value,
    subjectCode: practiceSubjectCode.value,
  }

  selectedKnowledgePath.value = normalizedPath
  nextQuery = clearPracticeTransientFocusQuery(nextQuery)
  nextQuery = clearPracticePathQuery(nextQuery)

  if (!normalizedPath.length) {
    await replacePracticeScopeQuery(nextQuery)
    return
  }

  const selectedId = normalizedPath[normalizedPath.length - 1]
  const selectedLevel = Number(levelById[selectedId] || 0)
  const chapterId = normalizedPath.find((item) => Number(levelById[item] || 0) === 4) || ''
  const pathLabel = toText(
    knowledgePathLabelMap.value[selectedId]
    || normalizedPath.map((item) => toText(labelMap[item] || item)).join(' / '),
  )

  if (chapterId) {
    nextQuery.chapterCode = toText(chapterCodeMap[chapterId])
    nextQuery.chapterName = toText(labelMap[chapterId] || chapterId)
  }

  if (selectedLevel >= 5) {
    nextQuery.knowledgePathNodeId = selectedId
    nextQuery.knowledgeId = selectedId
    nextQuery.pointCode = toText(pointCodeMap[selectedId])
    nextQuery.pointName = toText(labelMap[selectedId] || selectedId)
  }

  nextQuery.pathLabel = pathLabel
  await replacePracticeScopeQuery(nextQuery)
}

async function handleResetFilters() {
  const normalizedScope = buildScopeQueryWithFallback({
    examCategoryCode: practiceExamCategoryCode.value,
    jointExamGroupCode: practiceJointExamGroupCode.value,
    subjectCode: practiceSubjectCode.value,
  })
  let nextQuery = { ...route.query, ...normalizedScope }
  nextQuery = clearPracticePathQuery(nextQuery)
  nextQuery = clearPracticeTransientFocusQuery(nextQuery)
  await replacePracticeScopeQuery(nextQuery)
}

function measureChapterCloudOverflow() {
  if (typeof window === 'undefined') {
    return
  }

  nextTick(() => {
    const chapterCloudElement = chapterCloudRef.value
    if (!chapterCloudElement || !isFilterCollapseExpanded.value) {
      chapterCloudOverflow.value = false
      return
    }

    const collapsedHeight = Number.parseFloat(
      window.getComputedStyle(chapterCloudElement).getPropertyValue('--chapter-cloud-collapsed-height'),
    ) || 132

    chapterCloudOverflow.value = chapterCloudElement.scrollHeight > (collapsedHeight + 2)
    if (!chapterCloudOverflow.value) {
      chapterCloudExpanded.value = false
    }
  })
}

function scheduleChapterCloudMeasure(delay = 0) {
  if (typeof window === 'undefined') {
    return
  }

  window.clearTimeout(chapterCloudMeasureTimer)
  chapterCloudMeasureTimer = window.setTimeout(() => {
    measureChapterCloudOverflow()
  }, delay)
}

function toggleChapterCloud() {
  chapterCloudExpanded.value = !chapterCloudExpanded.value
}

async function initializePage() {
  pageLoading.value = true
  try {
    const dashboard = await fetchStudentDashboard()
    dashboardPayload.value = dashboard || {}
    subjectOptions.value = normalizePracticeSubjectOptions(dashboard)
    subjectContextStore.setSubjectOptions(subjectOptions.value, practiceSubjectCode.value)
    challengePointsState.value = {}
    await loadContentBaselineScope()
    await normalizeInitialPracticeQuery()
    await initializeSession()
    await Promise.all([
      loadKnowledgeFilterTree(),
      loadMockPaperOptions(),
    ])
    await loadQuestionRows()
  } finally {
    pageLoading.value = false
  }
}

function installMockExamE2EHooks() {
  if (typeof window === 'undefined') {
    return
  }
  window.__questionBankStudentE2E = {
    forceCountdown(nextSec = 0) {
      mockExamPaused.value = false
      mockExamRemainingSec.value = Math.max(0, Number(nextSec || 0))
      persistMockExamDraft(true)
    },
    resumeExam() {
      mockExamPaused.value = false
      persistMockExamDraft(true)
    },
    getState() {
      return {
        remainingSec: Number(mockExamRemainingSec.value || 0),
        paused: Boolean(mockExamPaused.value),
        answeredCount: Number(answeredQuestionCount.value || 0),
        reportId: toText(mockExamLastReport.value?.reportId),
      }
    },
  }
}

function startMockExamCountdown() {
  if (typeof window === 'undefined') {
    return
  }
  window.clearInterval(mockExamCountdownTimer)
  mockExamCountdownTimer = window.setInterval(() => {
    if (!isMockModule.value || !activePaper.value?.paperId || mockExamPaused.value || isMockExamSubmitted.value) {
      return
    }
    if (mockExamRemainingSec.value <= 0) {
      return
    }
    mockExamRemainingSec.value -= 1
    if (mockExamRemainingSec.value % 5 === 0) {
      persistMockExamDraft()
    }
  }, 1000)
}

function resetLoadingStates() {
  // 重置所有loading相关状态，确保按钮不会一直转圈
  savingAnswer.value = false
  submittingPractice.value = false
  mockExamSubmittingPaper.value = false
  aiMarking.loading.value = false
  aiMarking.stopPolling()
}

onMounted(() => {
  practiceRouteActive.value = true
  resetLoadingStates()
  initializePage()
  installMockExamE2EHooks()
  startMockExamCountdown()
  if (typeof window !== 'undefined') {
    window.addEventListener('resize', measureChapterCloudOverflow)
  }
})

onBeforeRouteLeave(() => {
  void maybeSubmitLearningMethodAutoFeedback({ feedbackStatus: 'PARTIAL', silent: true })
  practiceRouteActive.value = false
})

onBeforeUnmount(() => {
  void maybeSubmitLearningMethodAutoFeedback({ feedbackStatus: 'PARTIAL', silent: true })
  practiceRouteActive.value = false
  if (typeof window !== 'undefined') {
    window.removeEventListener('resize', measureChapterCloudOverflow)
    window.clearTimeout(chapterCloudMeasureTimer)
    window.clearInterval(mockExamCountdownTimer)
    if (window.__questionBankStudentE2E) {
      delete window.__questionBankStudentE2E
    }
  }
})

watch(
  () => route.path,
  () => {
    practiceRouteActive.value = true
    resetLoadingStates()
  },
)

watch(
  () => activeQuestionIndex.value,
  () => {
    // 切换题目时重置所有loading状态，确保按钮不会一直转圈
    resetLoadingStates()
  },
)

watch(
  () => [learningMethodRecommendationId.value, learningMethodCode.value, practiceSourceDescriptor.value.key],
  () => {
    learningMethodAutoFeedbackStatus.value = ''
  },
)

watch(
  () => practiceSubjectCode.value,
  async (nextSubjectCode, previousSubjectCode) => {
    if (nextSubjectCode === previousSubjectCode) {
      return
    }
    await loadKnowledgeFilterTree()
    await loadMockPaperOptions()
  },
)

watch(
  chapterFilterRows,
  () => {
    chapterCloudExpanded.value = false
    scheduleChapterCloudMeasure(isFilterCollapseExpanded.value ? 280 : 0)
  },
  { deep: true },
)

watch(
  () => filterCollapsePanels.value.slice(),
  (nextPanels) => {
    if (!nextPanels.includes('scope')) {
      chapterCloudExpanded.value = false
      chapterCloudOverflow.value = false
      return
    }
    scheduleChapterCloudMeasure(280)
  },
  { deep: true },
)

watch(
  () => [
    practiceModule.value,
    practiceExamCategoryCode.value,
    practiceJointExamGroupCode.value,
    practiceSubjectCode.value,
    practiceChapterCode.value,
    practicePointCode.value,
    practiceKnowledgeId.value,
    selectedPaperId.value,
    adaptiveQuestionIds.value.join(','),
  ],
  async (
    [
      nextModule,
      nextExamCategoryCode,
      nextJointExamGroupCode,
      nextSubjectCode,
      nextChapterCode,
      nextPointCode,
      nextKnowledgeId,
      nextPaperId,
      nextAdaptiveIds,
    ],
    [
      previousModule,
      previousExamCategoryCode,
      previousJointExamGroupCode,
      previousSubjectCode,
      previousChapterCode,
      previousPointCode,
      previousKnowledgeId,
      previousPaperId,
      previousAdaptiveIds,
    ],
  ) => {
    if (
      nextModule === previousModule
      && nextExamCategoryCode === previousExamCategoryCode
      && nextJointExamGroupCode === previousJointExamGroupCode
      && nextSubjectCode === previousSubjectCode
      && nextChapterCode === previousChapterCode
      && nextPointCode === previousPointCode
      && nextKnowledgeId === previousKnowledgeId
      && nextPaperId === previousPaperId
      && nextAdaptiveIds === previousAdaptiveIds
    ) {
      return
    }
    syncSelectedKnowledgePathFromRoute()
    if (nextModule === STUDENT_PRACTICE_MODULE.MOCK && nextSubjectCode !== previousSubjectCode) {
      await loadMockPaperOptions()
    }
    await loadQuestionRows()
  },
)

watch(
  () => [toText(activePaper.value?.paperId), questionRows.value.length],
  ([nextPaperId, questionCount], [previousPaperId]) => {
    if (!isMockModule.value) {
      return
    }
    if (nextPaperId && nextPaperId !== previousPaperId) {
      mockExamLastReport.value = null
      studentMessageText.value = ''
      draftRestoreStamp.value = ''
      initializeMockExamCountdown()
    }
    if (nextPaperId && questionCount > 0) {
      restoreMockExamDraft()
    }
  },
)

watch(
  () => mockExamRemainingSec.value,
  async (nextRemainingSec, previousRemainingSec) => {
    if (!isMockModule.value || isMockExamSubmitted.value) {
      return
    }
    if (nextRemainingSec <= 0 && Number(previousRemainingSec || 0) > 0) {
      mockExamRemainingSec.value = 0
      await submitMockPaperWithCheck({ autoSubmit: true })
    }
  },
)
</script>

<template>
  <section class="practice-shell" v-loading="pageLoading">
    <section v-if="isChapterModule" class="chapter-compact-strip">
      <div class="chapter-compact-strip__head">
        <div>
          <span class="compact-eyebrow">章节闯关</span>
          <strong>{{ currentQuestionListLabel }}</strong>
        </div>
        <div class="chapter-compact-strip__actions">
          <el-tag round>已答 {{ sessionState.answeredCount }}</el-tag>
          <el-tag round type="warning">段位分 {{ Number(currentChallengePoints.total || 0) }}</el-tag>
          <el-tag v-if="currentChallengePoints.rank" round type="danger">排名 #{{ Number(currentChallengePoints.rank || 0) }}</el-tag>
          <el-button plain @click="handleResetFilters">重置路径</el-button>
        </div>
      </div>
      <div class="chapter-compact-strip__selectors">
        <div class="knowledge-level-select-row">
          <el-select
            :model-value="selectedL3NodeId"
            class="knowledge-level-select"
            clearable
            filterable
            placeholder="选择 L3 模块"
            @change="handleL3Select"
          >
            <el-option
              v-for="item in l3SelectOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
          <el-select
            :model-value="selectedL4NodeId"
            class="knowledge-level-select"
            clearable
            filterable
            placeholder="选择 L4 章节"
            @change="handleL4Select"
          >
            <el-option
              v-for="item in l4SelectOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
          <el-select
            :model-value="selectedL5NodeId"
            class="knowledge-level-select"
            clearable
            filterable
            placeholder="选择 L5 考点"
            @change="handleL5Select"
          >
            <el-option
              v-for="item in l5SelectOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </div>
      </div>
    </section>

    <section v-if="isMockModule && !isImmersiveMode" class="mock-paper-deck">
      <div class="mock-paper-deck__header">
        <div>
          <h4>开始考试后即时组卷</h4>
          <p>系统会按当前科目的官方大纲自动生成本次试卷，避免提前占用无效考卷。</p>
        </div>
      </div>
      <div v-if="activePaper?.paperId" class="mock-paper-grid">
        <button
          v-for="paperItem in mockPaperCards"
          :key="paperItem.paperId"
          type="button"
          :class="['mock-paper-card', { 'mock-paper-card--active': activePaper?.paperId === paperItem.paperId }]"
          @click="handleMockPaperChange(paperItem.paperId)"
        >
          <span>{{ paperItem.paperName }}</span>
          <strong>{{ paperItem.questionCount }} 题</strong>
          <small>{{ paperItem.durationMinutes || 0 }} 分钟 · 总分 {{ paperItem.totalScore || 0 }}</small>
        </button>
      </div>
      <div v-else class="mock-paper-empty">
        <p>点击开始考试后，系统会按大纲权重即时生成本次模拟卷。</p>
        <el-button type="primary" @click="handleStartMockExam">开始考试</el-button>
      </div>
    </section>

    <el-alert
      v-if="isMockModule && mockPreviewNotice"
      class="practice-source-alert"
      effect="light"
      :closable="false"
      :title="mockPreviewNotice"
      type="warning"
      show-icon
    />

    <el-alert
      v-if="isChapterModule && practiceSourceNotice"
      class="practice-source-alert"
      effect="light"
      :closable="false"
      :title="practiceSourceNotice"
      :type="practiceSourceAlertType"
      show-icon
    />
    <el-alert
      v-if="isChapterModule && hasAdaptiveTrace"
      class="adaptive-trace-alert"
      effect="light"
      :closable="false"
      :title="adaptiveTraceNotice"
      show-icon
    />
    <el-alert
      v-if="isChapterModule && riskRepairNotice"
      class="risk-repair-alert"
      effect="light"
      :closable="false"
      :title="riskRepairNotice"
      type="error"
      show-icon
    />
    <section
      v-if="canBackToLearningMethods"
      class="learning-method-return-strip"
    >
      <span>已完成本轮后可返回学习方法页，查看推荐反馈与历史定位。</span>
      <el-button
        size="small"
        type="primary"
        plain
        :loading="learningMethodReturnLoading"
        @click="handleBackToLearningMethods"
      >
        返回学习方法页
      </el-button>
    </section>

    <section
      v-if="isMockModule && activePaper?.paperId"
      class="paper-command-strip"
    >
      <div class="paper-command-strip__status">
        <article class="paper-status-card paper-status-card--serial">
          <span>当前题号</span>
          <strong>{{ currentQuestionNumberLabel }}</strong>
          <small>切题时会同步更新</small>
        </article>
        <article id="paper-countdown" class="paper-status-card paper-status-card--countdown">
          <span>倒计时</span>
          <strong>{{ mockExamRemainingLabel }}</strong>
          <small>{{ activePaper?.durationMinutes || 0 }} 分钟整卷限时</small>
        </article>
        <article id="paper-pause-state" class="paper-status-card">
          <span>考试状态</span>
          <strong>{{ mockExamPauseStatusLabel }}</strong>
          <small>{{ mockExamPaused ? '已暂停计时，请尽快返回作答。' : '每次最多 10 分钟，可随时返回作答。' }}</small>
        </article>
      </div>
      <div class="paper-command-strip__actions">
        <el-button
          id="pause-paper-button"
          plain
          :disabled="isMockExamSubmitted"
          @click="toggleMockExamPause"
        >
          {{ mockExamPaused ? '继续作答' : '暂停考试' }}
        </el-button>
        <el-button
          id="submit-paper-button"
          type="danger"
          plain
          :disabled="isMockExamSubmitted || mockExamSubmittingPaper"
          @click="openMockSubmitCheck"
        >
          交卷检查
        </el-button>
      </div>
    </section>

    <section
      v-if="isMockModule && questionOutlineRows.length"
      id="paper-question-list"
      class="paper-question-list"
    >
      <article
        v-for="item in questionOutlineRows"
        :key="`paper-card-${item.id}`"
        :class="[
          'paper-card',
          { 'paper-card--active': activeQuestionIndex === item.index },
          { 'paper-card--answered': item.isAnswered },
          { 'paper-card--marked': item.isMarked },
        ]"
      >
        <button
          type="button"
          class="paper-card__jump"
          @click="jumpToQuestion(item.index)"
        >
          <strong>Q{{ String(item.index + 1).padStart(2, '0') }}</strong>
          <span>{{ item.isAnswered ? '已作答' : '未作答' }}</span>
        </button>
        <label class="paper-card__mark" :for="`paper-mark-${item.id}`">
          <input
            :id="`paper-mark-${item.id}`"
            :checked="item.isMarked"
            :disabled="isMockExamSubmitted"
            :data-marked-field="item.id"
            type="checkbox"
            @click.stop
            @change="handleMarkedToggle(item.id, $event.target.checked)"
          >
          <span>标记待查</span>
        </label>
      </article>
    </section>

    <section
      v-if="studentMessageText"
      id="student-message"
      class="student-message-banner"
    >
      <el-alert
        :title="studentMessageText"
        :type="isMockExamSubmitted ? 'success' : 'info'"
        :closable="false"
        show-icon
      />
    </section>

    <el-card
      v-if="mockExamLastReport"
      id="paper-report"
      class="paper-report-card"
      shadow="never"
    >
      <template #header>
        <div class="paper-report-card__header">
          <div>
            <span class="practice-eyebrow">模考报告</span>
            <h4>本次模考已完成</h4>
          </div>
          <el-tag type="success" round>{{ mockExamLastReport?.reportId || 'report-pending' }}</el-tag>
        </div>
      </template>
      <div class="paper-report-grid">
        <article>
          <span>得分</span>
          <strong>{{ Number(mockExamLastReport?.score || 0) }}/{{ Number(mockExamLastReport?.totalScore || 0) }}</strong>
        </article>
        <article>
          <span>用时</span>
          <strong>{{ formatDuration(Number(mockExamLastReport?.totalElapsedSec || 0)) }}</strong>
        </article>
        <article>
          <span>错题数</span>
          <strong>{{ Array.isArray(mockExamLastReport?.wrongQuestionIds) ? mockExamLastReport.wrongQuestionIds.length : Number(mockExamLastReport?.summary?.wrongCount || 0) }}</strong>
        </article>
        <article>
          <span>标记待查</span>
          <strong>{{ Number(mockExamLastReport?.summary?.markedCount || 0) }}</strong>
        </article>
      </div>
    </el-card>

    <el-empty
      v-if="!activeQuestion"
      class="practice-empty"
      :description="emptyDescription"
    />

    <section v-else class="practice-workbench" :class="{ 'practice-workbench--immersive': isImmersiveMode }">
      <div class="practice-main-column practice-main-column--solo">
        <el-card class="practice-card" shadow="never">
          <template #header>
            <div class="panel-header">
              <div>
                <h4>第 {{ activeQuestionIndex + 1 }} / {{ questionRows.length }} 题</h4>
                <p>{{ currentQuestionListLabel }}</p>
              </div>
              <div class="question-head-tags">
                <el-tag round effect="dark">{{ activeQuestionTypeLabel }}</el-tag>
                <el-tag v-if="activeQuestionDifficulty" round type="warning">{{ activeQuestionDifficulty }}</el-tag>
                <el-tag v-if="activeQuestionTimeLimit" round type="danger">{{ activeQuestionTimeLimit }}s</el-tag>
                <el-tag v-if="isMockModule" round type="danger">已用时 {{ practiceElapsedLabel }}</el-tag>
                <el-tag v-if="isMockModule && activePaper?.paperName" round type="info">{{ activePaper.paperName }}</el-tag>
              </div>
            </div>
          </template>

          <section v-if="isMockModule" class="question-serial-banner">
            <span>当前作答题号</span>
            <strong>{{ currentQuestionNumberLabel }}</strong>
            <small>{{ activeQuestionTypeLabel }}</small>
          </section>

          <section class="question-progress-strip">
            <div class="question-progress-strip__head">
              <div>
                <span>当前推进</span>
                <strong>{{ answeredQuestionCount }}/{{ questionRows.length || 0 }} 已作答</strong>
              </div>
              <small>剩余 {{ remainingQuestionCount }} 题</small>
            </div>
            <div class="question-progress-strip__track" aria-hidden="true">
              <span :style="{ width: `${workbenchProgressPercent}%` }" />
            </div>
          </section>

          <section class="question-jump-strip">
            <button
              v-for="item in questionOutlineRows"
              :key="item.id"
              type="button"
              :class="['question-jump-pill', { 'question-jump-pill--active': activeQuestionIndex === item.index }]"
              @click="jumpToQuestion(item.index)"
            >
              Q{{ item.index + 1 }}
            </button>
          </section>

          <header class="question-header" :class="{ 'question-header--focused': isFocusedQuestionActive }">
            <span v-if="isMockModule" class="question-header__serial">{{ currentQuestionNumberLabel }}</span>
            <p class="question-body">{{ activeQuestion.stem }}</p>
            <div v-if="activeQuestionKnowledgeTags.length" class="question-knowledge-tags">
              <el-tag
                v-for="tag in activeQuestionKnowledgeTags"
                :key="`${activeQuestionId}-${tag}`"
                effect="plain"
                round
              >
                {{ tag }}
              </el-tag>
            </div>
          </header>

          <el-radio-group
            v-model="currentSelectedAnswer"
            class="option-list"
            :disabled="mockExamPaused || isMockExamSubmitted"
            @change="onAnswerChange"
          >
            <el-radio
              v-for="(optionItem, optionIndex) in activeQuestionOptions"
              :key="`${activeQuestionId}-${optionIndex}`"
              :label="toText(optionItem?.key)"
              size="large"
              border
              class="option-card"
            >
              {{ optionLabel(optionItem) }}
            </el-radio>
          </el-radio-group>

          <div class="practice-actions">
            <el-button :disabled="activeQuestionIndex <= 0" @click="toPreviousQuestion">上一题</el-button>
            <el-button :disabled="activeQuestionIndex >= questionRows.length - 1" @click="toNextQuestion">下一题</el-button>
            <el-button
              type="primary"
              class="submit-practice-btn"
              :disabled="
                mockExamPaused || 
                isMockExamSubmitted || 
                (isChapterModule && activeQuestionIndex < questionRows.length - 1)
              "
              @click="submitCurrentPractice"
            >
              {{ isChapterModule ? '提交并 AI 批改' : '确认本题' }}
            </el-button>
            <el-button
              v-if="isMockModule"
              type="danger"
              plain
              :disabled="mockExamPaused || isMockExamSubmitted || mockExamSubmittingPaper"
              @click="openMockSubmitCheck"
            >
              交卷检查
            </el-button>
          </div>
        </el-card>
      </div>
    </section>

    <el-dialog
      v-model="mockExamSubmitDialogVisible"
      width="560px"
      :show-close="false"
    >
      <section id="paper-submit-check-modal" class="paper-submit-check-modal">
        <div class="paper-submit-check-modal__head">
          <div>
            <span class="practice-eyebrow">交卷前检查</span>
            <h4>确认提交 {{ activePaper?.paperName || '当前模拟卷' }}</h4>
          </div>
          <div class="paper-submit-check-modal__metrics">
            <el-tag round type="warning">未作答 {{ unansweredQuestionRows.length }}</el-tag>
            <el-tag round type="danger">已标记待查 {{ markedQuestionRows.length }}</el-tag>
          </div>
        </div>
        <div id="paper-submit-check-list" class="paper-submit-check-list">
          <article
            v-for="item in questionOutlineRows.filter((row) => !row.isAnswered || row.isMarked)"
            :key="`paper-submit-${item.id}`"
            class="paper-card"
          >
            <div class="paper-card__summary">
              <strong>Q{{ String(item.index + 1).padStart(2, '0') }}</strong>
              <span>{{ item.isAnswered ? '已作答' : '未作答' }}</span>
            </div>
            <small>{{ item.isMarked ? '已标记待查' : '建议先确认是否需要补答' }}</small>
          </article>
          <p
            v-if="!questionOutlineRows.some((row) => !row.isAnswered || row.isMarked)"
            class="paper-submit-check-list__empty"
          >
            当前试卷题目均已完成且没有待查标记，可以直接交卷。
          </p>
        </div>
        <div class="paper-submit-check-modal__actions">
          <el-button id="back-to-answer-button" @click="mockExamSubmitDialogVisible = false">返回作答</el-button>
          <el-button
            type="danger"
            :loading="mockExamSubmittingPaper"
            @click="submitMockPaperWithCheck()"
          >
            确认交卷
          </el-button>
        </div>
      </section>
    </el-dialog>

  </section>
</template>

<style scoped>
.practice-shell {
  display: grid;
  gap: 20px;
}

.practice-shell > * {
  min-width: 0;
}

.practice-workbench,
.practice-empty {
  order: 2;
}

.filter-deck {
  order: 3;
}

.context-atlas {
  order: 4;
}

.practice-source-alert,
.adaptive-trace-alert,
.risk-repair-alert {
  order: 1;
}

.learning-method-return-strip {
  order: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 10px 12px;
  border: 1px solid rgba(37, 99, 235, 0.24);
  border-radius: 12px;
  background: rgba(239, 246, 255, 0.9);
  color: var(--qb-text-secondary);
  font-size: 13px;
}

.challenge-strip,
.practice-module-strip,
.mock-paper-deck {
  order: 1;
}

.practice-hero {
  position: relative;
  display: grid;
  gap: 18px;
  padding: 24px;
  border-radius: 30px;
  border: 1px solid color-mix(in srgb, var(--qb-info) 24%, white 76%);
  background:
    radial-gradient(circle at 86% 14%, rgba(59, 130, 246, 0.2), transparent 22%),
    radial-gradient(circle at 16% 16%, rgba(125, 211, 252, 0.18), transparent 20%),
    linear-gradient(145deg, rgba(255, 255, 255, 0.98), rgba(239, 246, 255, 0.95));
  box-shadow: 0 30px 72px rgba(15, 23, 42, 0.08);
}

.practice-hero--task {
  background:
    radial-gradient(circle at 86% 18%, rgba(16, 185, 129, 0.16), transparent 24%),
    radial-gradient(circle at 16% 18%, rgba(37, 99, 235, 0.18), transparent 22%),
    linear-gradient(145deg, rgba(255, 255, 255, 0.98), rgba(236, 253, 245, 0.98));
}

.practice-hero--repair {
  border-color: color-mix(in srgb, var(--qb-danger-400) 30%, white 70%);
  background:
    radial-gradient(circle at 86% 18%, rgba(251, 113, 133, 0.16), transparent 24%),
    radial-gradient(circle at 16% 18%, rgba(251, 191, 36, 0.16), transparent 20%),
    linear-gradient(145deg, rgba(255, 255, 255, 0.98), rgba(255, 241, 242, 0.98));
}

.practice-hero--knowledge {
  background:
    radial-gradient(circle at 86% 18%, rgba(14, 165, 233, 0.16), transparent 24%),
    radial-gradient(circle at 16% 18%, rgba(99, 102, 241, 0.16), transparent 20%),
    linear-gradient(145deg, rgba(255, 255, 255, 0.98), rgba(238, 242, 255, 0.98));
}

.practice-module-strip {
  display: grid;
  gap: 14px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.practice-module-card {
  display: grid;
  gap: 6px;
  padding: 16px 18px;
  text-align: left;
  border-radius: 20px;
  border: 1px solid rgba(191, 219, 254, 0.56);
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 18px 36px rgba(15, 23, 42, 0.06);
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}

.practice-module-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 24px 44px rgba(37, 99, 235, 0.1);
}

.practice-module-card--active {
  border-color: rgba(37, 99, 235, 0.54);
  background: linear-gradient(145deg, rgba(239, 246, 255, 0.98), rgba(255, 255, 255, 0.98));
}

.practice-module-card span,
.practice-module-card small {
  color: var(--qb-text-meta);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.practice-module-card strong {
  color: var(--qb-text-heading);
  font-size: 18px;
  line-height: 1.4;
}

.challenge-strip {
  display: grid;
  gap: 14px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.challenge-strip__card,
.mock-paper-card {
  display: grid;
  gap: 6px;
  padding: 16px 18px;
  border-radius: 20px;
  border: 1px solid rgba(191, 219, 254, 0.56);
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 18px 36px rgba(15, 23, 42, 0.06);
}

.challenge-strip__card span,
.mock-paper-card span,
.mock-paper-card small {
  color: var(--qb-text-meta);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.challenge-strip__card strong,
.mock-paper-card strong {
  font-size: 20px;
  color: var(--qb-text-heading);
}

.mock-paper-deck {
  display: grid;
  gap: 14px;
}

.chapter-compact-strip,
.paper-mode-strip {
  display: grid;
  gap: 12px;
  padding: 16px 18px;
  border-radius: 24px;
  border: 1px solid color-mix(in srgb, var(--qb-primary-student) 14%, white 86%);
  background:
    radial-gradient(circle at top right, color-mix(in srgb, var(--qb-primary-student) 12%, transparent), transparent 30%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(246, 250, 255, 0.96));
  box-shadow: 0 18px 34px rgba(15, 23, 42, 0.06);
}

.chapter-compact-strip__head,
.paper-mode-strip {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.chapter-compact-strip__actions,
.paper-mode-strip__actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.chapter-compact-strip__selectors {
  display: grid;
  gap: 14px;
}

.knowledge-level-select-row {
  display: grid;
  gap: 10px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.knowledge-level-select :deep(.el-select__wrapper) {
  min-height: 40px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: inset 0 0 0 1px rgba(191, 219, 254, 0.68);
}

.compact-eyebrow {
  display: block;
  color: var(--qb-primary-student);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.mock-paper-deck__header h4,
.mock-paper-deck__header p {
  margin: 0;
}

.mock-paper-deck__header p {
  margin-top: 4px;
  color: var(--qb-text-copy);
}

.mock-paper-grid {
  display: grid;
  gap: 14px;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}

.mock-paper-empty {
  display: grid;
  gap: 12px;
  justify-items: start;
  padding: 20px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.78);
}

.mock-paper-empty p {
  margin: 0;
  color: var(--qb-text-copy);
}

.mock-paper-card {
  text-align: left;
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}

.mock-paper-card--active {
  border-color: rgba(37, 99, 235, 0.54);
  transform: translateY(-1px);
  box-shadow: 0 24px 44px rgba(37, 99, 235, 0.12);
}

.context-atlas {
  display: grid;
  gap: 16px;
  grid-template-columns: minmax(0, 1.2fr) repeat(3, minmax(0, 1fr));
}

.context-atlas__hero,
.context-atlas__card {
  border-radius: 24px;
  border: 1px solid rgba(191, 219, 254, 0.66);
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 20px 40px rgba(15, 23, 42, 0.06);
}

.context-atlas__hero {
  display: grid;
  gap: 10px;
  padding: 20px 22px;
  background:
    radial-gradient(circle at top right, rgba(59, 130, 246, 0.16), transparent 36%),
    linear-gradient(145deg, rgba(239, 246, 255, 0.96), rgba(255, 255, 255, 0.98));
}

.context-atlas__eyebrow,
.context-atlas__card span,
.context-atlas__card small {
  color: var(--qb-text-meta);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.05em;
}

.context-atlas__hero strong,
.context-atlas__card strong {
  color: var(--qb-text-heading);
  font-size: 18px;
  line-height: 1.45;
}

.context-atlas__hero p {
  margin: 0;
  color: var(--qb-text-copy);
  font-size: 13px;
  line-height: 1.75;
}

.context-atlas__card {
  display: grid;
  gap: 8px;
  padding: 18px 20px;
}

.hero-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
}

.hero-action-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.hero-copy {
  display: grid;
  gap: 0;
}

.hero-copy h3,
.hero-copy p {
  margin: 0;
}

.hero-eyebrow {
  display: inline-flex;
  width: fit-content;
  margin-bottom: 10px;
  padding: 7px 12px;
  border-radius: var(--qb-radius-pill);
  background: rgba(15, 23, 42, 0.94);
  color: rgba(239, 246, 255, 0.96);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.hero-copy h3 {
  font-size: clamp(28px, 3vw, 34px);
  line-height: 1.06;
  color: var(--qb-text-heading);
}

.hero-copy p {
  margin-top: 12px;
  max-width: 64ch;
  color: var(--qb-text-subtle-3);
  font-size: 14px;
  line-height: 1.7;
}

.hero-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 18px;
}

.hero-stats {
  display: grid;
  gap: 14px;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
}

.hero-stat-card {
  display: grid;
  gap: 8px;
  padding: 16px;
  border-radius: 22px;
  border: 1px solid rgba(191, 219, 254, 0.76);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.82), rgba(248, 250, 252, 0.9));
  backdrop-filter: blur(10px);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.7);
}

.hero-stat-card span,
.hero-stat-card small,
.hero-spotlight-card span,
.hero-spotlight-card small,
.rhythm-metrics span {
  color: var(--qb-text-subtle-4);
}

.hero-stat-card strong {
  font-size: 24px;
  color: var(--qb-text-heading);
}

.hero-spotlight-card,
.practice-rhythm-card {
  display: grid;
  gap: 10px;
  padding: 18px;
  border-radius: 24px;
  border: 1px solid rgba(96, 165, 250, 0.22);
  background:
    radial-gradient(circle at top right, rgba(191, 219, 254, 0.18), transparent 34%),
    linear-gradient(145deg, rgba(19, 63, 137, 0.98), rgba(37, 99, 235, 0.9));
  color: white;
  box-shadow: 0 22px 44px rgba(26, 86, 219, 0.2);
}

.hero-spotlight-card strong,
.practice-rhythm-card strong {
  font-size: 28px;
  color: white;
}

.hero-spotlight-card small,
.hero-spotlight-card span {
  color: rgba(219, 234, 254, 0.92);
}

.hero-spotlight-progress {
  position: relative;
  height: 8px;
  border-radius: 999px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.18);
}

.hero-spotlight-progress span {
  position: absolute;
  inset: 0 auto 0 0;
  border-radius: inherit;
  background: linear-gradient(90deg, rgba(196, 181, 253, 0.9), rgba(255, 255, 255, 0.96));
}

.filter-deck,
.practice-card,
.question-outline-card,
.ai-progress-card,
.practice-rhythm-card {
  border-radius: 24px;
  border: 1px solid var(--qb-border-soft);
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.05);
}

.filter-deck {
  padding: 18px;
  background:
    linear-gradient(180deg, rgba(248, 250, 252, 0.98), rgba(255, 255, 255, 0.96));
}

.filter-deck__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.filter-deck__header h4,
.filter-deck__header p {
  margin: 0;
}

.filter-deck__header p {
  margin-top: 8px;
  color: var(--qb-text-subtle-3);
  line-height: 1.7;
}

.filter-section {
  display: grid;
  gap: 10px;
  margin-top: 18px;
}

.filter-section__headline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.filter-section__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.filter-section--split {
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 18px;
}

.filter-section__label {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: var(--qb-text-subtle-4);
  text-transform: uppercase;
}

.filter-section__label--emphasis {
  font-size: 13px;
  color: var(--qb-text-heading);
}

.filter-search-card {
  display: grid;
  gap: 12px;
  margin-top: 18px;
  padding: 18px;
  border-radius: var(--qb-radius-xl);
  border: 1px solid color-mix(in srgb, var(--qb-info) 20%, white 80%);
  background:
    radial-gradient(circle at top right, rgba(14, 165, 233, 0.12), transparent 42%),
    linear-gradient(145deg, rgba(240, 249, 255, 0.95), var(--qb-surface-strong));
}

.filter-search-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.filter-pill-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.filter-pill {
  min-width: 132px;
  padding: var(--qb-space-3) var(--qb-space-3-5);
  border-radius: var(--qb-radius-lg);
  border: 1px solid var(--qb-border-strong);
  background: var(--qb-bg-card);
  color: var(--qb-text-heading);
  text-align: left;
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease, background 0.18s ease;
}

.filter-pill strong,
.filter-pill small {
  display: block;
}

.filter-pill strong {
  font-size: 14px;
  line-height: 1.4;
}

.filter-pill small {
  margin-top: 4px;
  color: var(--qb-text-subtle-4);
}

.filter-pill:hover:not(:disabled) {
  transform: translateY(-1px);
  border-color: color-mix(in srgb, var(--qb-info) 34%, white 66%);
  box-shadow: 0 10px 22px color-mix(in srgb, var(--qb-info) 12%, transparent);
}

.filter-pill.is-active {
  border-color: color-mix(in srgb, var(--qb-info) 34%, white 66%);
  background: linear-gradient(145deg, color-mix(in srgb, var(--qb-info) 10%, white 90%), var(--qb-surface-solid));
  box-shadow: 0 12px 24px color-mix(in srgb, var(--qb-info) 14%, transparent);
}

.filter-pill.is-active small {
  color: var(--el-color-primary);
}

.filter-pill.is-locked,
.filter-pill:disabled {
  cursor: not-allowed;
  opacity: 0.5;
  box-shadow: none;
}

.filter-pill--compact {
  min-width: 180px;
}

.filter-pill--ghost {
  border-style: dashed;
}

.filter-cascader-wrap {
  display: grid;
  gap: 8px;
}

.precision-cascader {
  width: 100%;
}

.precision-cascader--featured :deep(.el-input__wrapper) {
  min-height: 54px;
  padding: 0 16px;
  border-radius: var(--qb-radius-lg);
  box-shadow: 0 0 0 1px color-mix(in srgb, var(--qb-info) 18%, transparent);
}

.precision-cascader--featured :deep(.el-input__inner) {
  font-size: 15px;
  font-weight: 600;
}

.filter-tip {
  margin: 0;
  color: var(--qb-text-subtle-4);
  font-size: 13px;
}

.filter-tip--featured {
  font-size: 14px;
  line-height: 1.7;
}

.practice-filter-collapse {
  margin-top: 18px;
  border-top: none;
}

.practice-filter-collapse :deep(.el-collapse-item__wrap) {
  border-bottom: none;
}

.practice-filter-collapse :deep(.el-collapse-item__header) {
  height: auto;
  padding: 0;
  border-bottom: none;
  background: transparent;
  line-height: 1.4;
}

.practice-filter-collapse :deep(.el-collapse-item__content) {
  padding: 0;
}

.filter-collapse-title {
  display: flex;
  width: 100%;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 18px 0 8px;
}

.filter-collapse-title__copy {
  display: grid;
  gap: 6px;
}

.filter-collapse-title__copy p,
.filter-collapse-title__copy strong {
  margin: 0;
}

.filter-collapse-title__copy strong {
  font-size: 16px;
  color: var(--qb-text-heading);
}

.filter-collapse-title__copy p {
  color: var(--qb-text-subtle-4);
}

.filter-collapse-title__eyebrow {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: var(--el-color-primary);
}

.filter-collapse-title__meta {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}

.filter-collapse-body {
  padding: 8px 0 4px;
}

.chapter-capsule-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.chapter-capsule-grid--ghost {
  --chapter-cloud-collapsed-height: 124px;
  overflow: hidden;
  transition: max-height 0.22s ease;
}

.chapter-capsule-grid--ghost.is-collapsed {
  max-height: var(--chapter-cloud-collapsed-height);
}

.chapter-capsule {
  display: grid;
  gap: 4px;
  min-width: 148px;
  padding: 12px 16px;
  border-radius: var(--qb-radius-lg);
  border: 1px solid color-mix(in srgb, var(--qb-border-glass) 88%, white 12%);
  background: linear-gradient(145deg, var(--qb-surface-solid), rgba(248, 250, 252, 0.96));
  text-align: left;
  cursor: pointer;
  transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease, background 0.18s ease;
}

.chapter-capsule:hover:not(:disabled) {
  transform: translateY(-1px);
  border-color: color-mix(in srgb, var(--qb-primary-student) 28%, white 72%);
  box-shadow: 0 10px 20px color-mix(in srgb, var(--qb-primary-student) 10%, transparent);
}

.chapter-capsule--ghost {
  background: transparent;
  border-color: color-mix(in srgb, var(--qb-info) 28%, white 72%);
  box-shadow: none;
}

.chapter-capsule__title {
  font-weight: 700;
  color: var(--qb-text-heading);
}

.chapter-capsule__meta {
  font-size: 12px;
  color: var(--qb-text-subtle-4);
}

.chapter-capsule.is-active {
  border-color: color-mix(in srgb, var(--qb-primary-student) 32%, white 68%);
  background: linear-gradient(145deg, color-mix(in srgb, var(--qb-primary-student) 10%, white 90%), rgba(239, 246, 255, 0.98));
}

.chapter-capsule.is-current {
  box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--qb-success) 24%, transparent);
}

.chapter-capsule.is-disabled,
.chapter-capsule:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.chapter-cloud {
  display: grid;
  gap: 10px;
}

.chapter-cloud__actions {
  display: flex;
  justify-content: center;
}

.adaptive-trace-alert {
  border-color: var(--el-color-primary);
  background: var(--qb-primary-soft-bg);
}

.adaptive-trace-alert :deep(.el-alert__icon),
.adaptive-trace-alert :deep(.el-alert__title) {
  color: var(--el-color-primary);
}

.risk-repair-alert {
  border-color: var(--qb-danger);
  background: var(--qb-surface-soft-danger);
}

.risk-repair-alert :deep(.el-alert__icon),
.risk-repair-alert :deep(.el-alert__title) {
  color: var(--qb-danger);
}

.practice-workbench {
  display: grid;
  gap: 20px;
  align-items: start;
}

.practice-outline-column,
.practice-side-column {
  min-width: 0;
}

.practice-main-column {
  display: grid;
  gap: 20px;
  min-width: 0;
}

.practice-main-column--solo {
  grid-column: 1 / -1;
}

.practice-workbench--immersive {
  grid-template-columns: minmax(0, 1fr);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.panel-header--compact h4 {
  font-size: 16px;
}

.panel-header h4,
.panel-header p {
  margin: 0;
}

.panel-header p {
  margin-top: 4px;
  color: var(--qb-text-subtle-4);
}

.question-outline-list {
  display: grid;
  gap: 10px;
  max-height: calc(100vh - 220px);
  overflow: auto;
  padding-right: 6px;
}

.question-outline-card {
  background: rgba(255, 255, 255, 0.94);
}

.question-outline-item {
  display: grid;
  gap: 6px;
  padding: 12px;
  border-radius: 18px;
  border: 1px solid var(--qb-border-glass);
  background: var(--qb-surface-raised);
  text-align: left;
  cursor: pointer;
  transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
}

.question-outline-item:hover {
  transform: translateY(-1px);
  border-color: color-mix(in srgb, var(--qb-info) 28%, white 72%);
  box-shadow: 0 10px 18px color-mix(in srgb, var(--qb-info) 8%, transparent);
}

.question-outline-item.is-active {
  border-color: color-mix(in srgb, var(--qb-info) 34%, white 66%);
  background: linear-gradient(145deg, rgba(240, 249, 255, 0.98), var(--qb-surface-strong));
}

.question-outline-item__head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.question-outline-item__index {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: var(--qb-text-subtle-4);
  text-transform: uppercase;
}

.question-outline-item strong {
  color: var(--qb-text-heading);
}

.question-outline-item p {
  margin: 0;
  color: var(--qb-text-subtle-4);
  font-size: 13px;
  line-height: 1.6;
  display: -webkit-box;
  overflow: hidden;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.question-outline-item__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.practice-card {
  background:
    radial-gradient(circle at top right, rgba(219, 234, 254, 0.3), transparent 30%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 252, 0.98));
}

.practice-eyebrow {
  display: inline-flex;
  width: fit-content;
  color: var(--qb-primary-student);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.paper-command-strip,
.paper-question-list,
.student-message-banner,
.paper-report-card {
  order: 1;
}

.paper-command-strip {
  display: grid;
  gap: 14px;
  padding: 18px 20px;
  border-radius: 24px;
  border: 1px solid rgba(248, 113, 113, 0.18);
  background:
    radial-gradient(circle at top right, rgba(248, 113, 113, 0.14), transparent 28%),
    linear-gradient(145deg, rgba(255, 251, 235, 0.96), rgba(255, 255, 255, 0.98));
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.06);
}

.paper-command-strip__status,
.paper-report-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
}

.paper-command-strip__actions,
.paper-submit-check-modal__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: flex-end;
}

.paper-status-card,
.paper-report-grid article {
  display: grid;
  gap: 6px;
  padding: 14px 16px;
  border-radius: 18px;
  border: 1px solid rgba(226, 232, 240, 0.92);
  background: rgba(255, 255, 255, 0.92);
}

.paper-status-card span,
.paper-report-grid article span,
.paper-status-card small {
  color: var(--qb-text-subtle-4);
  font-size: 12px;
}

.paper-status-card strong,
.paper-report-grid article strong {
  color: var(--qb-text-heading);
  font-size: 22px;
}

.paper-question-list {
  display: grid;
  gap: 10px;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
}

.paper-card {
  display: grid;
  gap: 10px;
  padding: 14px;
  border-radius: 18px;
  border: 1px solid rgba(226, 232, 240, 0.94);
  background: rgba(255, 255, 255, 0.94);
}

.paper-card--active {
  border-color: rgba(37, 99, 235, 0.42);
  box-shadow: 0 16px 30px rgba(37, 99, 235, 0.1);
}

.paper-card--marked {
  border-color: rgba(249, 115, 22, 0.32);
}

.paper-card__jump,
.paper-card__summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  background: none;
  border: 0;
  padding: 0;
  text-align: left;
}

.paper-card__jump {
  cursor: pointer;
}

.paper-card__jump strong,
.paper-card__summary strong {
  color: var(--qb-text-heading);
  font-size: 16px;
}

.paper-card__jump span,
.paper-card__summary span,
.paper-card small {
  color: var(--qb-text-subtle-4);
  font-size: 12px;
}

.paper-card__mark {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: var(--qb-text-copy);
  font-size: 13px;
}

.paper-report-card__header,
.paper-submit-check-modal__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.paper-report-card__header h4,
.paper-submit-check-modal__head h4 {
  margin: 4px 0 0;
  color: var(--qb-text-heading);
}

.paper-submit-check-modal {
  display: grid;
  gap: 18px;
}

.paper-submit-check-modal__metrics {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.paper-submit-check-list {
  display: grid;
  gap: 10px;
}

.paper-submit-check-list__empty {
  margin: 0;
  color: var(--qb-text-subtle-4);
  font-size: 14px;
  line-height: 1.7;
}

.question-serial-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 18px;
  padding: 12px 16px;
  border-radius: 18px;
  border: 1px solid rgba(191, 219, 254, 0.72);
  background: rgba(239, 246, 255, 0.9);
}

.question-serial-banner span,
.question-serial-banner small {
  color: var(--qb-text-subtle-4);
  font-size: 12px;
}

.question-serial-banner strong,
.question-header__serial {
  color: var(--qb-primary-student);
  font-weight: 800;
}

.question-jump-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
}

.question-jump-pill {
  min-width: 56px;
  padding: 10px 14px;
  border-radius: 999px;
  border: 1px solid rgba(191, 219, 254, 0.76);
  background: rgba(255, 255, 255, 0.94);
  color: var(--qb-text-copy);
  cursor: pointer;
}

.question-jump-pill--active {
  border-color: rgba(37, 99, 235, 0.5);
  background: rgba(219, 234, 254, 0.96);
  color: var(--qb-primary-student);
}

.question-progress-strip {
  display: grid;
  gap: 12px;
  margin-bottom: 18px;
  padding: 16px 18px;
  border-radius: 20px;
  border: 1px solid rgba(191, 219, 254, 0.72);
  background:
    linear-gradient(135deg, rgba(239, 246, 255, 0.95), rgba(255, 255, 255, 0.92));
}

.question-progress-strip__head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12px;
}

.question-progress-strip__head div {
  display: grid;
  gap: 4px;
}

.question-progress-strip__head span,
.question-progress-strip__head small {
  color: var(--qb-text-subtle-4);
  font-size: 12px;
}

.question-progress-strip__head strong {
  color: var(--qb-text-heading);
  font-size: 16px;
}

.question-progress-strip__track {
  position: relative;
  height: 8px;
  overflow: hidden;
  border-radius: 999px;
  background: rgba(191, 219, 254, 0.42);
}

.question-progress-strip__track span {
  position: absolute;
  inset: 0 auto 0 0;
  border-radius: inherit;
  background: linear-gradient(90deg, rgba(14, 165, 233, 0.88), rgba(37, 99, 235, 0.96));
}

.question-header {
  display: grid;
  gap: 14px;
  padding: 18px;
  border-radius: var(--qb-radius-lg);
  background: linear-gradient(145deg, rgba(248, 250, 252, 0.96), var(--qb-surface-strong));
  transition: box-shadow 0.18s ease, border-color 0.18s ease, background 0.18s ease;
}

.question-header__serial {
  display: inline-flex;
  width: fit-content;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(219, 234, 254, 0.96);
  font-size: 12px;
  letter-spacing: 0.08em;
}

.question-header--focused {
  border: 1px solid color-mix(in srgb, var(--qb-danger) 28%, white 72%);
  background: var(--qb-gradient-danger-card);
  box-shadow: var(--qb-shadow-danger);
}

.question-body {
  margin: 0;
  font-size: 18px;
  line-height: 1.75;
  color: var(--qb-text-heading);
}

.question-knowledge-tags,
.question-head-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.option-list {
  display: grid;
  gap: 12px;
  margin-top: 18px;
}

.option-card {
  margin-right: 0;
  width: 100%;
  min-height: 58px;
  align-items: center;
}

.option-card :deep(.el-radio__label) {
  white-space: normal;
  line-height: 1.7;
}

.practice-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 20px;
  padding-top: 18px;
  border-top: 1px solid rgba(226, 232, 240, 0.92);
}

/* 修改提交按钮的hover效果，避免变白导致字看不清 */
.practice-actions :deep(.submit-practice-btn.el-button--primary:hover) {
  background-color: #e5e7eb !important;
  border-color: #e5e7eb !important;
  color: #1f2937 !important;
}

.practice-actions :deep(.submit-practice-btn.el-button--primary:not(:disabled):hover) {
  background-color: #e5e7eb !important;
  border-color: #e5e7eb !important;
  color: #1f2937 !important;
}

.practice-actions :deep(.submit-practice-btn.el-button--primary:focus-visible) {
  background-color: #e5e7eb !important;
  border-color: #e5e7eb !important;
  color: #1f2937 !important;
}

.ai-progress-card p {
  margin: 10px 0 0;
  color: var(--qb-text-subtle-4);
}

.practice-side-column {
  display: grid;
  gap: 16px;
}

.practice-focus-card,
.ai-progress-card,
.practice-rhythm-card {
  border-radius: 24px;
  border: 1px solid var(--qb-border-soft);
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.05);
}

.practice-focus-card {
  display: grid;
  gap: 14px;
  padding: 20px;
  background:
    radial-gradient(circle at top right, rgba(96, 165, 250, 0.18), transparent 34%),
    linear-gradient(160deg, rgba(255, 255, 255, 0.98), rgba(239, 246, 255, 0.96));
}

.practice-focus-card__header {
  display: grid;
  gap: 4px;
}

.practice-focus-card__header span,
.practice-focus-card small,
.status-list span {
  color: var(--qb-text-subtle-4);
  font-size: 12px;
}

.practice-focus-card__header strong {
  color: var(--qb-text-heading);
  font-size: 22px;
}

.practice-focus-card p {
  margin: 0;
  color: var(--qb-text-copy);
  line-height: 1.7;
}

.practice-focus-card__meta {
  display: grid;
  gap: 10px;
}

.practice-focus-card__meta div {
  display: grid;
  gap: 4px;
  padding: 12px 14px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(219, 234, 254, 0.88);
}

.practice-focus-card__meta span {
  color: var(--qb-text-subtle-4);
  font-size: 11px;
  letter-spacing: 0.04em;
}

.practice-focus-card__meta strong {
  color: var(--qb-text-heading);
  font-size: 15px;
}

.practice-focus-card__progress {
  margin-top: 2px;
}

.status-list {
  display: grid;
  gap: 10px;
  margin-top: 14px;
}

.status-list p {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin: 0;
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(248, 250, 252, 0.92);
  border: 1px solid rgba(226, 232, 240, 0.9);
}

.status-list strong {
  color: var(--qb-text-heading);
  font-size: 13px;
  text-align: right;
}

.practice-rhythm-card {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(241, 245, 255, 0.96));
  color: var(--qb-text-heading);
  box-shadow: 0 14px 36px rgba(15, 23, 42, 0.05);
}

.practice-rhythm-card strong {
  color: var(--qb-text-heading);
  font-size: 18px;
}

.rhythm-metrics {
  display: grid;
  gap: 10px;
}

.rhythm-metrics div {
  display: grid;
  gap: 4px;
  padding: 14px;
  border-radius: 18px;
  background: linear-gradient(145deg, rgba(248, 250, 252, 0.96), rgba(255, 255, 255, 0.96));
  border: 1px solid rgba(226, 232, 240, 0.92);
}

.error-text {
  color: var(--qb-danger-accent);
}

.practice-empty {
  border-radius: 22px;
  border: 1px dashed color-mix(in srgb, var(--qb-border-glass) 80%, transparent);
  background: rgba(255, 255, 255, 0.86);
}

@media (min-width: 1100px) {
  .practice-hero {
    grid-template-columns: minmax(0, 1.28fr) minmax(340px, 0.92fr);
    align-items: stretch;
  }

  .context-atlas {
    grid-template-columns: minmax(0, 1.2fr) repeat(3, minmax(0, 1fr));
  }

  .practice-workbench {
    grid-template-columns: minmax(260px, 0.72fr) minmax(0, 1.46fr) minmax(280px, 0.82fr);
    align-items: start;
  }

  .question-outline-card {
    position: sticky;
    top: 126px;
  }

  .practice-side-column {
    position: sticky;
    top: 126px;
  }
}

@media (max-width: 768px) {
  .practice-module-strip,
  .challenge-strip {
    grid-template-columns: 1fr;
  }

  .knowledge-level-select-row {
    grid-template-columns: 1fr;
  }

  .chapter-compact-strip__head,
  .paper-mode-strip,
  .chapter-compact-strip__actions,
  .paper-mode-strip__actions {
    flex-direction: column;
    align-items: flex-start;
  }

  .context-atlas,
  .practice-hero,
  .filter-deck {
    padding: 16px;
  }

  .context-atlas {
    grid-template-columns: 1fr;
  }

  .hero-copy h3 {
    font-size: 26px;
  }

  .chapter-capsule,
  .filter-pill {
    width: 100%;
  }

  .panel-header,
  .filter-deck__header,
  .filter-search-card__header,
  .filter-collapse-title,
  .hero-heading {
    flex-direction: column;
  }

  .question-progress-strip__head,
  .status-list p {
    flex-direction: column;
    align-items: flex-start;
  }

  .paper-command-strip__actions,
  .paper-submit-check-modal__actions,
  .paper-submit-check-modal__head {
    flex-direction: column;
    align-items: flex-start;
  }

  .paper-question-list,
  .paper-command-strip__status,
  .paper-report-grid {
    grid-template-columns: 1fr;
  }

  .filter-collapse-title__meta {
    justify-content: flex-start;
  }
}

@media (prefers-reduced-motion: reduce) {
}
</style>
