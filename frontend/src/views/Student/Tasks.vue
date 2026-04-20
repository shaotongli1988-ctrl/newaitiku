<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage } from '@/ui/feedback'
import { useRoute, useRouter } from 'vue-router'
import { fetchStudentDashboard, fetchTaskList } from '../../api/services/student'
import { knowledgeTreeV2, studentCheckIn } from '../../api/services/questionBank'
import { useUserStore } from '../../stores/userStore'
import { useSubjectContextStore } from '../../stores/subjectContextStore.js'
import {
  buildStudentChapterPracticePathLabel,
  buildStudentPracticeRouteLocation,
  STUDENT_PRACTICE_SOURCE,
} from '../../utils/studentPracticeNavigation.js'
import {
  buildDailyTaskScopeCopy,
  buildTaskOverviewCards,
  buildTaskRecordHeading,
  buildTaskRecordScopeCopy,
  buildTaskStatusMeta,
  buildTaskSummaryFootnote,
  buildTasksErrorState,
  buildTasksExecutionScopeNote,
  buildWeakPointScopeCopy,
  normalizeTaskRecord,
} from '../../utils/studentTasksCopy.js'
import { buildKnowledgeGraphIndex } from '../../utils/knowledgeTree.js'
import { buildTodayExecutionRecommendation } from '../../utils/studentHomeViewModel.js'

const props = defineProps({
  embedded: {
    type: Boolean,
    default: false,
  },
})

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const subjectContextStore = useSubjectContextStore()

const dashboardLoading = ref(false)
const loading = ref(false)
const graphLoading = ref(false)
const taskRows = ref([])
const taskListMeta = ref({ page: 1, size: 20, total: 0 })
const dashboardPayload = ref({})
const aiQuota = ref({ dailyLimit: 0, usedCount: 0 })
const graphPayloadBySubject = ref({})
const checkInSubmitting = ref(false)
const taskListError = ref('')
const dashboardError = ref('')
const graphError = ref('')

function normalizeSubjectOptions(payload) {
  const coreSubjects = Array.isArray(payload?.coreSubjects) ? payload.coreSubjects : []
  return coreSubjects
    .map((item) => ({
      subjectCode: String(item?.subjectCode || '').trim(),
      subjectId: String(item?.subjectId || '').trim(),
      subjectName: String(item?.subjectName || item?.subjectCode || '').trim(),
    }))
    .filter((item) => Boolean(item.subjectCode))
}

function normalizeMastery(value) {
  const numericValue = Number(value || 0)
  if (!Number.isFinite(numericValue)) {
    return 0
  }
  return Math.max(0, Math.min(1, numericValue))
}

const currentSubjectCode = computed(() => String(route.query.subjectCode || subjectContextStore.currentSubjectCode || '').trim())
const subjectOptions = computed(() => subjectContextStore.subjectOptions)
const recentTaskCount = computed(() => taskRows.value.length)
const runningCount = computed(() => taskRows.value.filter((item) => String(item?.status || '').trim().toUpperCase() === 'RUNNING').length)
const failedCount = computed(() => taskRows.value.filter((item) => String(item?.status || '').trim().toUpperCase() === 'FAILED').length)
const completedCount = computed(() => (
  taskRows.value.filter((item) => ['SUCCESS', 'DONE', 'COMPLETED', 'FINISHED'].includes(String(item?.status || '').trim().toUpperCase())).length
))
const dailyTaskRows = computed(() => {
  const studentStateTasks = dashboardPayload.value?.studentState?.dailyTasks
  if (Array.isArray(studentStateTasks)) {
    return studentStateTasks
  }
  return Array.isArray(dashboardPayload.value?.dailyTasks) ? dashboardPayload.value.dailyTasks : []
})
const completedDailyTaskCount = computed(() =>
  dailyTaskRows.value.filter((item) => Boolean(item?.isDone)).length,
)
const totalDailyTaskCount = computed(() => dailyTaskRows.value.length)
const checkInDone = computed(() => Boolean(dashboardPayload.value?.studentState?.checkInDone))
const streakDays = computed(() =>
  Number(dashboardPayload.value?.studentState?.streakDays || dashboardPayload.value?.streakDays || 0),
)
const studentPoints = computed(() =>
  Number(dashboardPayload.value?.studentState?.points || dashboardPayload.value?.points || 0),
)
const nextDailyTask = computed(() =>
  dailyTaskRows.value.find((item) => !item?.isDone) || dailyTaskRows.value[0] || null,
)
const hasSubjectOptions = computed(() => subjectOptions.value.length > 0)
const hasTaskRows = computed(() => Array.isArray(taskRows.value) && taskRows.value.length > 0)
const hasTaskListError = computed(() => Boolean(String(taskListError.value || '').trim()))
const hasDashboardError = computed(() => Boolean(String(dashboardError.value || '').trim()))
const hasGraphError = computed(() => Boolean(String(graphError.value || '').trim()))
const currentGraphPayload = computed(() => {
  const currentPayload = graphPayloadBySubject.value[currentSubjectCode.value]
  if (currentPayload) {
    return currentPayload
  }
  const firstPayload = Object.values(graphPayloadBySubject.value || {})[0]
  return firstPayload && typeof firstPayload === 'object' ? firstPayload : { nodes: [], links: [] }
})
const graphNodes = computed(() => (Array.isArray(currentGraphPayload.value?.nodes) ? currentGraphPayload.value.nodes : []))
const normalizedGraphLevelById = computed(() => {
  const graphIndex = buildKnowledgeGraphIndex(currentGraphPayload.value || {})
  return graphIndex?.levelById || {}
})
const renderedNodeCount = computed(() => graphNodes.value.length)
const l5GraphNodes = computed(() => (
  graphNodes.value.filter((item) => Number(normalizedGraphLevelById.value[String(item?.id || '').trim()] || 0) >= 5)
))
const hasGraphNodes = computed(() => l5GraphNodes.value.length > 0)
const currentSubjectLabel = computed(() => {
  const matched = subjectOptions.value.find((item) => String(item?.subjectCode || '').trim() === currentSubjectCode.value)
  return String(matched?.subjectName || currentSubjectCode.value || '未选择科目').trim()
})
const currentSubjectChallengePoints = computed(() => {
  const rows = Array.isArray(dashboardPayload.value?.challengePointSubjects)
    ? dashboardPayload.value.challengePointSubjects
    : Array.isArray(dashboardPayload.value?.studentState?.challengePointSubjects)
      ? dashboardPayload.value.studentState.challengePointSubjects
      : []
  return rows.find((item) => String(item?.subjectCode || '').trim() === currentSubjectCode.value) || {
    total: 0,
    todayDelta: 0,
    correctSubmitCount: 0,
    rank: 0,
    levelName: '刷题青铜',
    nextLevelName: '刷题白银',
    pointsToNextLevel: 200,
    scoreCap: 3000,
    isTopLevel: false,
  }
})
const weakL5Count = computed(() =>
  l5GraphNodes.value.filter((item) => normalizeMastery(item?.mastery) < 0.6).length,
)
const uncoveredL5Count = computed(() =>
  l5GraphNodes.value.filter((item) => normalizeMastery(item?.mastery) <= 0).length,
)
const dailyCompletionPercent = computed(() => {
  const total = Number(totalDailyTaskCount.value || 0)
  if (!total) {
    return 0
  }
  return Math.max(0, Math.min(100, Math.round((completedDailyTaskCount.value / total) * 100)))
})
const graphCoveragePercent = computed(() => {
  const total = l5GraphNodes.value.length
  if (!total) {
    return 0
  }
  const covered = l5GraphNodes.value.filter((item) => normalizeMastery(item?.mastery) > 0).length
  return Math.max(0, Math.min(100, Math.round((covered / total) * 100)))
})
const quotaRemaining = computed(() => Math.max(0, Number(aiQuota.value?.dailyLimit || 0) - Number(aiQuota.value?.usedCount || 0)))
const studentDisplayName = computed(() => {
  const raw = String(
    dashboardPayload.value?.studentState?.displayName
    || dashboardPayload.value?.studentState?.studentName
    || dashboardPayload.value?.studentName
    || userStore.userId
    || '学习同学',
  ).trim()
  if (!raw) {
    return '学习同学'
  }
  if (/^(student|user|test)[-_]/i.test(raw)) {
    return '学习同学'
  }
  return raw.includes('同学') ? raw : `${raw}同学`
})
const weakestNodeRows = computed(() => {
  const rows = []
  for (const subjectItem of subjectOptions.value) {
    const subjectCode = String(subjectItem?.subjectCode || '').trim()
    const subjectName = String(subjectItem?.subjectName || subjectCode || '').trim()
    const payload = graphPayloadBySubject.value[subjectCode] || { nodes: [], links: [] }
    const graphIndex = buildKnowledgeGraphIndex(payload || {})
    const levelById = graphIndex?.levelById || {}
    const nodes = Array.isArray(payload?.nodes) ? payload.nodes : []
    for (const item of nodes) {
      const nodeId = String(item?.id || '').trim()
      if (Number(levelById[nodeId] || 0) < 5) {
        continue
      }
      rows.push({
        id: nodeId,
        subjectCode,
        subjectName,
        label: String(item?.label || item?.name || item?.id || '').trim(),
        mastery: Math.round(normalizeMastery(item?.mastery) * 100),
        questionCount: Number(item?.questionCount || 0),
      })
    }
  }
  return rows
    .filter((item) => Number(item.mastery || 0) < 60)
    .sort((left, right) => {
      if (left.mastery !== right.mastery) {
        return left.mastery - right.mastery
      }
      return right.questionCount - left.questionCount
    })
    .slice(0, 6)
})
const localUrgentKnowledgeSuggestion = computed(() => {
  const target = weakestNodeRows.value[0] || null
  if (!target) {
    return {
      tone: 'empty',
      title: '暂无紧急弱项',
      message: '',
      detail: '',
      actionLabel: '查看诊断总览',
      target: null,
    }
  }
  const subjectName = String(target?.subjectName || currentSubjectLabel.value || '当前科目').trim()
  const urgent = Number(target.mastery || 0) < 60
  return {
    tone: urgent ? 'risk' : 'steady',
    title: urgent ? '最紧急补短板' : '下一步提分点',
    message: `${subjectName}：${target.label} 当前掌握度 ${target.mastery}%，建议优先做一轮针对性补强。`,
    detail: `掌握度 ${target.mastery}% · 关联题量 ${target.questionCount}`,
    actionLabel: urgent ? '去补弱项' : '继续巩固',
    target: {
      ...target,
      subjectName,
    },
  }
})
const todayExecutionRecommendation = computed(() => buildTodayExecutionRecommendation({
  checkInDone: checkInDone.value,
  streakDays: streakDays.value,
  nextDailyTask: nextDailyTask.value,
  urgentKnowledgeSuggestion: localUrgentKnowledgeSuggestion.value,
  dailyCompletionPercent: dailyCompletionPercent.value,
  currentSubjectName: currentSubjectLabel.value,
}))
const embeddedDailyTaskRows = computed(() => (
  props.embedded ? dailyTaskRows.value.slice(0, 3) : dailyTaskRows.value
))
const embeddedWeakNodeRows = computed(() => (
  props.embedded ? weakestNodeRows.value.slice(0, 2) : weakestNodeRows.value
))
const pageHeading = computed(() => (props.embedded ? '首页任务摘要' : '知识诊断今日任务'))
const pageDescription = computed(() => (
  props.embedded
    ? '首页只保留诊断驱动的任务摘要，完整执行清单已收进知识诊断。'
    : '这里把诊断结论转成今天能直接开做的动作，让今天的执行结果能继续沉淀成段位分和更稳的升本得分能力。'
))
const executionBadgeLabel = computed(() => (props.embedded ? '首页摘要' : '知识诊断 · 今日任务'))
const executionHeadline = computed(() => {
  return todayExecutionRecommendation.value.title
})
const executionSupportCopy = computed(() => {
  const baseCopy = todayExecutionRecommendation.value.description
    || (props.embedded
      ? '首页把今天最关键的一步前置提醒给你。'
      : '知识诊断今日任务已经接管今天的执行闭环。')
  if (props.embedded) {
    return baseCopy
  }
  if (String(currentSubjectChallengePoints.value?.nextLevelName || '').trim()) {
    return `${baseCopy} 当前科目再积 ${Number(currentSubjectChallengePoints.value?.pointsToNextLevel || 0)} 分到 ${String(currentSubjectChallengePoints.value?.nextLevelName || '').trim()}，今天这轮任务就是最适合拿这部分分的入口。`
  }
  return `${baseCopy} 当前科目段位已到高阶，更重要的是把今天的执行结果继续稳成考场上的真实得分。`
})
const executionScopeNote = computed(() => (
  buildTasksExecutionScopeNote(currentSubjectLabel.value)
))
const executionPulseCards = computed(() => ([
  {
    label: '待补弱项',
    value: `${weakL5Count.value} 个`,
    helper: uncoveredL5Count.value > 0 ? `${uncoveredL5Count.value} 个节点尚未覆盖` : '当前路径已形成可执行清单',
  },
  {
    label: '执行进度',
    value: `${dailyCompletionPercent.value}%`,
    helper: `${completedDailyTaskCount.value}/${totalDailyTaskCount.value || 0} 已完成`,
  },
  {
    label: '下一步',
    value: todayExecutionRecommendation.value.actionLabel || (checkInDone.value ? '查看完整任务清单' : '先完成今日打卡'),
    helper: todayExecutionRecommendation.value.helper || (props.embedded ? '首页只保留摘要，完整动作统一去知识诊断二级页' : '当前页是诊断之后的唯一执行页'),
  },
  {
    label: '当前段位',
    value: String(currentSubjectChallengePoints.value?.levelName || '刷题青铜'),
    helper: String(currentSubjectChallengePoints.value?.nextLevelName || '').trim()
      ? `再积 ${Number(currentSubjectChallengePoints.value?.pointsToNextLevel || 0)} 分到 ${String(currentSubjectChallengePoints.value?.nextLevelName || '').trim()}`
      : `已到 ${Number(currentSubjectChallengePoints.value?.scoreCap || 3000)} 分满阶`,
  },
]))
const taskChallengeBridgeCopy = computed(() => {
  if (String(currentSubjectChallengePoints.value?.nextLevelName || '').trim()) {
    return `今天的任务不是额外负担，而是在帮你把分数刷到下一段位。先把今日任务做完，再去刷题升本，通常更容易把正确输出稳定下来。`
  }
  return '今天的任务不是额外负担，而是在帮你把高段位继续稳住。把今天该做的动作按顺序跑完，后面更容易把状态带进正式考试。'
})
const overviewCards = computed(() => buildTaskOverviewCards({
  recentTaskCount: recentTaskCount.value,
  runningCount: runningCount.value,
  failedCount: failedCount.value,
  completedCount: completedCount.value,
}))
const taskSummaryFootnote = computed(() => {
  return buildTaskSummaryFootnote(recentTaskCount.value, taskListMeta.value?.total || 0)
})
const taskRecordHeading = computed(() => buildTaskRecordHeading(failedCount.value))
const secondaryInsightTitle = computed(() => (
  hasTaskRows.value ? '次级诊断摘要' : '补充信息'
))
const dailyTaskScopeCopy = computed(() => (
  buildDailyTaskScopeCopy()
))
const taskRecordScopeCopy = computed(() => (
  buildTaskRecordScopeCopy()
))
const weakPointScopeCopy = computed(() => (
  buildWeakPointScopeCopy(currentSubjectLabel.value)
))
const dashboardErrorState = computed(() => buildTasksErrorState('dashboard', dashboardError.value))
const taskListErrorState = computed(() => buildTasksErrorState('taskList', taskListError.value))
const graphSummaryErrorState = computed(() => buildTasksErrorState('graphSummary', graphError.value))
const weakPointErrorState = computed(() => buildTasksErrorState('weakPoint', graphError.value))
const failedTaskRows = computed(() =>
  normalizedTaskRows.value.filter((item) => item.statusTone === 'danger').slice(0, 3),
)
const recentExecutionRows = computed(() =>
  normalizedTaskRows.value.filter((item) => item.statusTone !== 'danger').slice(0, 3),
)
const insightsExpanded = ref([])
const chapterChallengeTarget = computed(() => {
  const chapterTree = Array.isArray(dashboardPayload.value?.chapterPracticeTree)
    ? dashboardPayload.value.chapterPracticeTree
    : []
  const subjectMetaById = new Map(
    subjectOptions.value.map((item) => [
      String(item?.subjectId || '').trim(),
      {
        subjectCode: String(item?.subjectCode || '').trim(),
        subjectName: String(item?.subjectName || item?.subjectCode || '').trim(),
      },
    ]),
  )
  for (const subjectRow of chapterTree) {
    const subjectId = String(subjectRow?.subjectId || '').trim()
    const subjectMeta = subjectMetaById.get(subjectId) || {}
    const chapters = Array.isArray(subjectRow?.chapters) ? subjectRow.chapters : []
    const targetChapter = chapters.find((item) => item?.isCurrent)
      || chapters.find((item) => item?.isUnlocked)
      || chapters[0]
    if (!targetChapter) {
      continue
    }
    return {
      subjectCode: String(subjectMeta.subjectCode || '').trim(),
      subjectName: String(subjectMeta.subjectName || subjectRow?.subjectName || '').trim(),
      chapterName: String(targetChapter?.chapter || '').trim(),
    }
  }
  return null
})

const normalizedTaskRows = computed(() => (
  taskRows.value.map((item, index) => normalizeTaskRecord(item, index))
))

const featuredTaskRows = computed(() => {
  const actionableRows = normalizedTaskRows.value.filter((item) => item.statusTone !== 'success')
  if (actionableRows.length) {
    return actionableRows.slice(0, 4)
  }
  return normalizedTaskRows.value.slice(0, 4)
})

const recentTaskRows = computed(() => normalizedTaskRows.value.slice(0, 6))

async function loadTaskRows() {
  loading.value = true
  taskListError.value = ''
  try {
    const payload = await fetchTaskList({ page: 1, size: 20 })
    taskRows.value = Array.isArray(payload?.items) ? payload.items : []
    taskListMeta.value = {
      page: Math.max(1, Number(payload?.page || 1)),
      size: Math.max(1, Number(payload?.size || 20)),
      total: Math.max(0, Number(payload?.total || 0)),
    }
    aiQuota.value = payload?.aiQuota || { dailyLimit: 0, usedCount: 0 }
  } catch (error) {
    taskRows.value = []
    taskListMeta.value = { page: 1, size: 20, total: 0 }
    aiQuota.value = { dailyLimit: 0, usedCount: 0 }
    taskListError.value = String(error?.response?.data?.message || error?.message || '任务流水加载失败')
    ElMessage.error(taskListError.value)
  } finally {
    loading.value = false
  }
}

async function loadDashboardSnapshot() {
  dashboardLoading.value = true
  dashboardError.value = ''
  try {
    const dashboard = await fetchStudentDashboard()
    dashboardPayload.value = dashboard || {}
    subjectContextStore.setSubjectOptions(normalizeSubjectOptions(dashboard), currentSubjectCode.value)
  } catch (error) {
    dashboardPayload.value = {}
    dashboardError.value = String(error?.response?.data?.message || error?.message || '今日任务数据加载失败')
    ElMessage.error(dashboardError.value)
  } finally {
    dashboardLoading.value = false
  }
}

async function loadWeakKnowledgeSnapshot() {
  const subjectRows = subjectOptions.value.filter((item) => String(item?.subjectCode || '').trim())
  if (!subjectRows.length && !currentSubjectCode.value) {
    graphPayloadBySubject.value = {}
    graphError.value = ''
    return
  }
  graphLoading.value = true
  graphError.value = ''
  try {
    const targetSubjects = subjectRows.length
      ? subjectRows
      : [{ subjectCode: currentSubjectCode.value, subjectName: currentSubjectLabel.value }]
    const nextGraphPayloadBySubject = {}
    const failedSubjects = []
    await Promise.all(targetSubjects.map(async (subjectItem) => {
      const subjectCode = String(subjectItem?.subjectCode || '').trim()
      if (!subjectCode) {
        return
      }
      try {
        const response = await knowledgeTreeV2({
          status: 'ENABLED',
          subjectCode: subjectCode,
        })
        const payload = response?.data || response || {}
        nextGraphPayloadBySubject[subjectCode] = {
          nodes: Array.isArray(payload?.nodes) ? payload.nodes : [],
          links: Array.isArray(payload?.links) ? payload.links : [],
        }
      } catch (_error) {
        failedSubjects.push(subjectCode)
      }
    }))
    graphPayloadBySubject.value = nextGraphPayloadBySubject
    if (failedSubjects.length && failedSubjects.length === targetSubjects.length) {
      graphError.value = '全部科目弱项摘要加载失败'
    } else if (failedSubjects.length) {
      graphError.value = `部分科目弱项摘要加载失败：${failedSubjects.join('、')}`
    }
  } catch (error) {
    graphPayloadBySubject.value = {}
    graphError.value = String(error?.response?.data?.message || error?.message || '全部科目弱项摘要加载失败')
    ElMessage.error(graphError.value)
  } finally {
    graphLoading.value = false
  }
}

async function refreshTasksPageData() {
  await loadDashboardSnapshot()
  await Promise.all([loadTaskRows(), loadWeakKnowledgeSnapshot()])
}

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

function parseActionQuery(actionQuery) {
  if (actionQuery && typeof actionQuery === 'object' && !Array.isArray(actionQuery)) {
    return Object.fromEntries(
      Object.entries(actionQuery)
        .map(([key, value]) => [String(key || '').trim(), String(value ?? '').trim()])
        .filter(([key, value]) => key && value),
    )
  }
  const query = {}
  const params = new URLSearchParams(String(actionQuery || ''))
  params.forEach((value, key) => {
    if (key) {
      query[key] = value
    }
  })
  return query
}

async function navigateToAnalysis() {
  await router.push({
    path: '/student/analysis/overview',
    query: currentSubjectCode.value ? { subjectCode: currentSubjectCode.value } : {},
  })
}

async function navigateToChallengePoints() {
  await router.push({
    path: '/student/analysis/points',
    query: currentSubjectCode.value ? { subjectCode: currentSubjectCode.value } : {},
  })
}

async function navigateToPractice() {
  await router.push(buildStudentPracticeRouteLocation({
    subjectCode: currentSubjectCode.value,
    practiceSource: STUDENT_PRACTICE_SOURCE.TASK,
    practiceSourceLabel: props.embedded ? '学习首页任务摘要进入' : '知识诊断今日任务进入',
  }))
}

async function handleWeakNodePractice(item) {
  await router.push(buildStudentPracticeRouteLocation({
    subjectCode: item?.subjectCode || currentSubjectCode.value,
    knowledgeId: item?.id || '',
    pathLabel: [item?.subjectName || '', item?.label || ''].filter((row) => row).join(' / '),
    practiceSource: STUDENT_PRACTICE_SOURCE.TASK,
    practiceSourceLabel: props.embedded ? '学习首页任务摘要进入' : '知识诊断今日任务进入',
  }))
}

async function handleDailyTaskAction(task) {
  const taskKey = String(task?.taskKey || '').trim()
  const actionPath = String(task?.actionPath || '/student/practice/chapter').trim() || '/student/practice/chapter'
  const nextQuery = parseActionQuery(task?.actionQuery)
  if (actionPath.startsWith('/student/practice') && currentSubjectCode.value && !nextQuery.subjectCode) {
    nextQuery.subjectCode = currentSubjectCode.value
  }
  if (actionPath === '/student/question-bank/repair' && currentSubjectCode.value && !nextQuery.subjectCode) {
    nextQuery.subjectCode = currentSubjectCode.value
  }
  if (actionPath.startsWith('/student/practice')) {
    const target = chapterChallengeTarget.value
    const inferredModule = actionPath.endsWith('/free')
      ? STUDENT_PRACTICE_MODULE.FREE
      : actionPath.endsWith('/mock')
        ? STUDENT_PRACTICE_MODULE.MOCK
        : actionPath.endsWith('/tasks')
          ? STUDENT_PRACTICE_MODULE.TASKS
          : STUDENT_PRACTICE_MODULE.CHAPTER
    await router.push(buildStudentPracticeRouteLocation({
      module: nextQuery.module || inferredModule,
      subjectCode: nextQuery.subjectCode || target?.subjectCode || currentSubjectCode.value,
      knowledgePathNodeId: nextQuery.knowledgePathNodeId || '',
      knowledgeId: nextQuery.knowledgeId || '',
      chapterCode: nextQuery.chapterCode || '',
      chapterName: nextQuery.chapterName || '',
      pointCode: nextQuery.pointCode || '',
      pointName: nextQuery.pointName || '',
      pathLabel: nextQuery.pathLabel
        || (taskKey === 'practiceReward' ? buildStudentChapterPracticePathLabel(target || {}) : '')
        || String(task?.taskName || task?.actionLabel || '').trim(),
      adaptiveQuestionIds: nextQuery.adaptiveQuestionIds || '',
      adaptiveDimension: nextQuery.adaptiveDimension || '',
      adaptiveMastery: nextQuery.adaptiveMastery || '',
      focusMode: nextQuery.focusMode || '',
      focusQuestionId: nextQuery.focusQuestionId || '',
      practiceSource: nextQuery.practiceSource || STUDENT_PRACTICE_SOURCE.TASK,
      practiceSourceLabel: nextQuery.practiceSourceLabel || String(task?.taskName || task?.actionLabel || '任务进入').trim() || '任务进入',
      extraQuery: nextQuery,
    }))
    return
  }
  await router.push({
    path: actionPath,
    query: nextQuery,
  })
}

async function handleTaskRecordAction(task) {
  if (task?.hasExplicitAction || String(task?.actionPath || '').trim() || String(task?.taskKey || '').trim()) {
    await handleDailyTaskAction(task)
    return
  }
  if (String(task?.status || '').trim().toUpperCase() === 'FAILED' && nextDailyTask.value) {
    await handleDailyTaskAction(nextDailyTask.value)
    return
  }
  await navigateToAnalysis()
}

async function handleCheckIn() {
  if (checkInDone.value || checkInSubmitting.value) {
    if (checkInDone.value) {
      ElMessage.success('今日已经打卡完成啦。')
    }
    return
  }
  checkInSubmitting.value = true
  try {
    const response = await studentCheckIn()
    const data = response?.data && typeof response.data === 'object' ? response.data : response || {}
    ElMessage.success(`打卡成功，当前积分 ${Number(data?.points || 0)}，连续打卡 ${Number(data?.streakDays || 0)} 天。`)
    await loadDashboardSnapshot()
  } catch (error) {
    ElMessage.error(String(error?.response?.data?.message || error?.message || '打卡失败'))
  } finally {
    checkInSubmitting.value = false
  }
}

async function handlePrimaryExecutionAction() {
  const recommendation = todayExecutionRecommendation.value
  if (recommendation.kind === 'checkIn') {
    await handleCheckIn()
    return
  }
  if (recommendation.kind === 'task' && recommendation.task) {
    await handleDailyTaskAction(recommendation.task)
    return
  }
  if (recommendation.kind === 'weakness' && recommendation.target) {
    await handleWeakNodePractice(recommendation.target)
    return
  }
  await navigateToPractice()
}

onMounted(async () => {
  await refreshTasksPageData()
})

watch(
  () => currentSubjectCode.value,
  async (nextSubjectCode, previousSubjectCode) => {
    if (!nextSubjectCode || nextSubjectCode === previousSubjectCode) {
      return
    }
    await refreshTasksPageData()
  },
)
</script>

<template>
  <section :class="['tasks-shell', { 'tasks-shell--embedded': embedded }]" v-loading="loading">
    <header v-if="!embedded" class="page-header">
      <div>
        <h3>{{ pageHeading }}</h3>
        <p>{{ pageDescription }}</p>
      </div>
    </header>

    <template v-if="embedded">
      <section class="feature-card daily-card daily-card--merged" v-loading="dashboardLoading">
        <div class="card-header">
          <div>
            <span class="section-kicker">今日执行</span>
            <h4>{{ todayExecutionRecommendation.title }}</h4>
          </div>
          <el-button size="small" type="primary" plain :disabled="!hasSubjectOptions" @click="navigateToAnalysis">查看诊断总览</el-button>
        </div>
        <p class="embedded-copy embedded-copy--strong">{{ todayExecutionRecommendation.description }}</p>

        <article class="embedded-recommendation">
          <div class="embedded-recommendation__copy">
            <span class="embedded-recommendation__label">当前推荐动作</span>
            <strong>{{ todayExecutionRecommendation.actionLabel }}</strong>
            <p>{{ todayExecutionRecommendation.helper }}</p>
          </div>
          <div class="embedded-recommendation__actions">
            <el-button
              size="small"
              type="primary"
              :loading="todayExecutionRecommendation.kind === 'checkIn' && checkInSubmitting"
              @click="handlePrimaryExecutionAction"
            >
              {{ todayExecutionRecommendation.actionLabel }}
            </el-button>
            <el-button size="small" plain @click="navigateToChallengePoints">看刷题段位</el-button>
            <el-button size="small" plain @click="navigateToPractice">刷题升本</el-button>
          </div>
        </article>

        <div v-if="!dailyTaskRows.length && !dashboardLoading" class="student-empty-panel">
          <el-empty description="当前还没有生成今日任务，请先完善学习档案。" />
          <div class="student-empty-panel__actions">
            <el-button plain :disabled="!hasSubjectOptions" @click="navigateToAnalysis">查看诊断总览</el-button>
            <el-button type="primary" plain @click="navigateToPractice">去刷题升本</el-button>
          </div>
        </div>
        <div v-else class="embedded-task-summary">
          <div class="embedded-task-summary__head">
            <span>今日任务速览</span>
            <strong>{{ completedDailyTaskCount }}/{{ totalDailyTaskCount || 0 }} 已完成</strong>
          </div>
          <div class="embedded-task-checklist">
            <article v-for="task in embeddedDailyTaskRows" :key="task.taskKey" class="embedded-task-checklist__item">
              <div>
                <strong>{{ task.taskName }}</strong>
                <p>{{ dailyTaskProgress(task).completed }}/{{ dailyTaskProgress(task).target }} · {{ task.actionLabel || '继续完成任务' }}</p>
              </div>
              <el-tag size="small" :type="task.isDone ? 'success' : 'warning'" effect="light">
                {{ task.isDone ? '已完成' : '进行中' }}
              </el-tag>
            </article>
          </div>
        </div>
        <p v-if="dailyTaskRows.length > embeddedDailyTaskRows.length" class="embedded-meta-note">
          其余 {{ dailyTaskRows.length - embeddedDailyTaskRows.length }} 项继续在知识诊断今日任务中展开。
        </p>

      </section>
    </template>

    <template v-else>
      <section class="execution-banner">
        <article class="execution-banner__hero">
          <div class="execution-banner__copy">
            <span class="execution-badge">{{ executionBadgeLabel }}</span>
            <h4>{{ executionHeadline }}</h4>
            <p>{{ executionSupportCopy }}</p>
            <div class="execution-bridge-card">
              <strong>先把今天该做的动作跑通，再去冲段位，分通常涨得更稳</strong>
              <p>{{ taskChallengeBridgeCopy }}</p>
            </div>
            <small class="scope-note">{{ executionScopeNote }}</small>
          </div>
          <div class="execution-banner__actions">
            <el-button
              type="primary"
              :loading="todayExecutionRecommendation.kind === 'checkIn' && checkInSubmitting"
              @click="handlePrimaryExecutionAction"
            >
              {{ todayExecutionRecommendation.actionLabel }}
            </el-button>
            <el-button plain @click="navigateToChallengePoints">看刷题段位</el-button>
            <el-button plain :disabled="!hasSubjectOptions" @click="navigateToAnalysis">回诊断总览</el-button>
          </div>
        </article>

        <div class="execution-banner__grid">
          <article
            v-for="item in executionPulseCards"
            :key="item.label"
            class="execution-pulse-card"
          >
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
            <small>{{ item.helper }}</small>
          </article>
        </div>
      </section>

      <section class="tasks-layout">
        <div class="tasks-main">
          <section class="feature-card daily-card" v-loading="dashboardLoading">
            <div class="card-header">
              <div>
                <span class="section-kicker">今日任务</span>
                <h4>{{ completedDailyTaskCount }}/{{ totalDailyTaskCount || 0 }} 已完成</h4>
                <p>{{ dailyTaskScopeCopy }}</p>
              </div>
              <div class="card-header__actions">
                <el-button plain :loading="dashboardLoading" @click="refreshTasksPageData">重新加载</el-button>
                <el-button type="primary" plain :disabled="!hasSubjectOptions" @click="navigateToAnalysis">查看诊断总览</el-button>
              </div>
            </div>
            <div v-if="hasDashboardError && !dashboardLoading" class="student-status-panel student-status-panel--error">
              <strong>{{ dashboardErrorState.title }}</strong>
              <p>{{ dashboardErrorState.message }}</p>
              <div class="student-empty-panel__actions">
                <el-button type="primary" @click="refreshTasksPageData">重新加载</el-button>
                <el-button plain :disabled="!hasSubjectOptions" @click="navigateToAnalysis">查看诊断总览</el-button>
              </div>
            </div>
            <div v-else-if="!dailyTaskRows.length && !dashboardLoading" class="student-empty-panel">
              <el-empty description="当前还没有生成今日任务，请先完善学习档案。" />
              <div class="student-empty-panel__actions">
                <el-button plain :disabled="!hasSubjectOptions" @click="navigateToAnalysis">查看诊断总览</el-button>
                <el-button type="primary" plain @click="navigateToPractice">去刷题升本</el-button>
              </div>
            </div>
            <div v-else class="daily-task-list">
              <article v-for="task in dailyTaskRows" :key="task.taskKey" class="daily-task-item">
                <div class="daily-task-head">
                  <div>
                    <strong>{{ task.taskName }}</strong>
                    <p>{{ task.actionLabel || '继续完成任务' }}</p>
                  </div>
                  <el-tag :type="task.isDone ? 'success' : 'warning'" effect="light">
                    {{ task.isDone ? '已完成' : '进行中' }}
                  </el-tag>
                </div>
                <div class="hero-progress hero-progress--thin" aria-hidden="true">
                  <span :style="{ width: `${dailyTaskProgress(task).percent}%` }" />
                </div>
                <div class="daily-task-foot">
                  <span>{{ dailyTaskProgress(task).completed }}/{{ dailyTaskProgress(task).target }}</span>
                  <el-button size="small" plain @click="handleDailyTaskAction(task)">
                    {{ task.isDone ? '再次进入' : (task.actionLabel || '去完成') }}
                  </el-button>
                </div>
              </article>
            </div>
            <p v-if="nextDailyTask" class="daily-note">当前推荐：{{ nextDailyTask.taskName }}</p>
          </section>

          <section v-if="failedTaskRows.length" class="feature-card recovery-card">
              <div class="card-header">
                <div>
                  <span class="section-kicker">待恢复任务</span>
                  <h4>先恢复这里</h4>
                  <p>失败或中断的任务单独列出，优先恢复后再继续今天的主线。</p>
                </div>
              </div>
              <div class="task-record-list">
                <article
                  v-for="item in failedTaskRows"
                  :key="`failed-${item.recordId}`"
                  class="task-record-card task-record-card--danger"
                >
                  <div class="task-record-card__head">
                    <div>
                      <strong>{{ item.title }}</strong>
                      <p>{{ item.summary }}</p>
                    </div>
                    <el-tag type="danger" effect="light">
                      {{ item.statusLabel }}
                    </el-tag>
                  </div>
                  <div class="hero-progress hero-progress--thin" aria-hidden="true">
                    <span :style="{ width: `${item.progressValue}%` }" />
                  </div>
                  <div class="task-record-card__foot">
                    <span>更新时间 {{ item.helper }}</span>
                    <el-button size="small" plain @click="handleTaskRecordAction(item)">
                      {{ item.actionLabel }}
                    </el-button>
                  </div>
                </article>
              </div>
          </section>

          <section class="feature-card task-stream-card">
            <div class="card-header">
              <div>
                <span class="section-kicker">最近执行</span>
                <h4>刚刚完成</h4>
                <p>{{ taskSummaryFootnote }}</p>
                <p>{{ taskRecordScopeCopy }}</p>
              </div>
              <el-button :loading="loading" @click="loadTaskRows">刷新</el-button>
            </div>
            <div v-if="hasTaskListError && !loading" class="student-status-panel student-status-panel--error">
              <strong>{{ taskListErrorState.title }}</strong>
              <p>{{ taskListErrorState.message }}</p>
              <div class="student-empty-panel__actions">
                <el-button type="primary" @click="loadTaskRows">重新加载</el-button>
                <el-button plain :disabled="!hasSubjectOptions" @click="navigateToAnalysis">回诊断总览</el-button>
              </div>
            </div>
            <div v-else-if="!hasTaskRows" class="student-empty-panel">
              <el-empty description="当前还没有任务记录，先去完成今天的打卡或练习。" />
              <div class="student-empty-panel__actions">
                <el-button plain @click="handleCheckIn">{{ checkInDone ? '今日已打卡' : '先完成打卡' }}</el-button>
                <el-button type="primary" plain @click="navigateToPractice">去刷题升本</el-button>
              </div>
            </div>
            <template v-else-if="recentExecutionRows.length">
              <div class="task-record-list">
                <article
                  v-for="item in recentExecutionRows"
                  :key="item.recordId"
                  :class="['task-record-card', `task-record-card--${item.statusTone}`]"
                >
                  <div class="task-record-card__head">
                    <div>
                      <strong>{{ item.title }}</strong>
                      <p>{{ item.summary }}</p>
                    </div>
                    <el-tag
                      :type="item.statusTone === 'danger' ? 'danger' : item.statusTone === 'success' ? 'success' : item.statusTone === 'info' ? 'primary' : 'info'"
                      effect="light"
                    >
                      {{ item.statusLabel }}
                    </el-tag>
                  </div>
                  <div class="hero-progress hero-progress--thin" aria-hidden="true">
                    <span :style="{ width: `${item.progressValue}%` }" />
                  </div>
                  <div class="task-record-card__foot">
                    <span>更新时间 {{ item.helper }}</span>
                    <el-button size="small" plain @click="handleTaskRecordAction(item)">
                      {{ item.actionLabel }}
                    </el-button>
                  </div>
                </article>
              </div>
            </template>
          </section>

          <el-collapse v-model="insightsExpanded" class="secondary-insights">
            <el-collapse-item name="more-insights">
              <template #title>
                <div class="secondary-insights__title">
                  <span class="section-kicker">更多诊断信息</span>
                  <strong>{{ secondaryInsightTitle }}</strong>
                </div>
              </template>

              <section class="summary-grid">
                <article
                  v-for="item in overviewCards"
                  :key="item.label"
                  class="summary-card"
                  :class="item.tone ? `summary-card--${item.tone}` : ''"
                >
                  <span>{{ item.label }}</span>
                  <strong>{{ item.value }}</strong>
                  <small>{{ item.helper }}</small>
                </article>
              </section>

              <section class="hero-grid">
                <article class="hero-card hero-card--coverage" v-loading="graphLoading">
                  <template v-if="hasGraphError && !graphLoading">
                    <div class="student-status-panel student-status-panel--error">
                      <strong>{{ graphSummaryErrorState.title }}</strong>
                      <p>{{ graphSummaryErrorState.message }}</p>
                      <div class="student-empty-panel__actions">
                        <el-button type="primary" @click="loadWeakKnowledgeSnapshot">重新加载</el-button>
                        <el-button plain :disabled="!hasSubjectOptions" @click="navigateToAnalysis">查看诊断总览</el-button>
                      </div>
                    </div>
                  </template>
                  <template v-else>
                    <span class="hero-label">路径覆盖率</span>
                    <div class="hero-value-row">
                      <strong>{{ graphCoveragePercent }}</strong>
                      <em>%</em>
                    </div>
                    <div class="hero-progress" aria-hidden="true">
                      <span :style="{ width: `${graphCoveragePercent}%` }" />
                    </div>
                    <p v-if="hasGraphNodes">当前路径已点亮 {{ renderedNodeCount }} 个节点，覆盖 {{ l5GraphNodes.length }} 个 L5 考点。</p>
                    <p v-else>当前路径画像还不够完整，可先去刷题升本积累更多诊断数据。</p>
                  </template>
                </article>

                <article class="hero-card hero-card--quota">
                  <span class="hero-label">AI 剩余配额</span>
                  <strong>{{ quotaRemaining }}</strong>
                  <p>今日已使用 {{ Number(aiQuota.usedCount || 0) }} / {{ Number(aiQuota.dailyLimit || 0) }}</p>
                </article>
              </section>
            </el-collapse-item>
          </el-collapse>
        </div>

        <aside class="tasks-rail">
          <article class="profile-card profile-card--compact" v-loading="dashboardLoading">
            <div class="card-header">
              <div>
                <span class="section-kicker">今日进度</span>
                <h4>今天推进到这里</h4>
                <p>{{ studentDisplayName }} · 连续备考 {{ streakDays }} 天</p>
              </div>
            </div>
            <div class="profile-progress">
              <div class="profile-progress__head">
                <span>今日任务进度</span>
                <strong>{{ dailyCompletionPercent }}%</strong>
              </div>
              <div class="hero-progress" aria-hidden="true">
                <span :style="{ width: `${dailyCompletionPercent}%` }" />
              </div>
              <small>{{ completedDailyTaskCount }}/{{ totalDailyTaskCount || 0 }} 已完成</small>
            </div>

            <el-button
              type="primary"
              class="profile-action"
              :loading="checkInSubmitting"
              :disabled="checkInDone"
              @click="handleCheckIn"
            >
              {{ checkInDone ? '今日已打卡' : '打卡领取积分' }}
            </el-button>
          </article>

          <article class="profile-card challenge-card" v-loading="dashboardLoading">
            <div class="card-header">
              <div>
                <span class="section-kicker">刷题段位</span>
                <h4>{{ currentSubjectLabel }} · {{ String(currentSubjectChallengePoints.levelName || '刷题青铜') }}</h4>
                <p>任务做完后的下一步，就是把今天的执行结果继续转成稳定段位分。</p>
              </div>
            </div>
            <div class="profile-progress">
              <div class="profile-progress__head">
                <span>累计段位分</span>
                <strong>{{ Number(currentSubjectChallengePoints.total || 0) }}</strong>
              </div>
              <small>
                {{ String(currentSubjectChallengePoints.nextLevelName || '').trim()
                  ? `再积 ${Number(currentSubjectChallengePoints.pointsToNextLevel || 0)} 分到 ${String(currentSubjectChallengePoints.nextLevelName || '').trim()}`
                  : `已到 ${Number(currentSubjectChallengePoints.scoreCap || 3000)} 分满阶` }}
              </small>
            </div>
            <el-button type="primary" plain class="profile-action" @click="navigateToChallengePoints">
              看刷题段位
            </el-button>
          </article>

          <article class="feature-card weak-card" v-loading="graphLoading">
            <div class="card-header">
              <div>
                <span class="section-kicker">今日弱项提醒</span>
                <h4>全部科目都要看</h4>
                <p>{{ weakPointScopeCopy }}</p>
              </div>
            </div>
            <div v-if="hasGraphError && !graphLoading" class="student-status-panel student-status-panel--error">
              <strong>{{ weakPointErrorState.title }}</strong>
              <p>{{ weakPointErrorState.message }}</p>
              <div class="student-empty-panel__actions">
                <el-button type="primary" @click="loadWeakKnowledgeSnapshot">重新加载</el-button>
                <el-button plain :disabled="!hasSubjectOptions" @click="navigateToAnalysis">查看诊断总览</el-button>
              </div>
            </div>
            <div v-else-if="!weakestNodeRows.length" class="student-empty-panel student-empty-panel--compact">
              <el-empty description="当前还没有可提示的薄弱节点。" />
              <div class="student-empty-panel__actions">
                <el-button plain :disabled="!hasSubjectOptions" @click="navigateToAnalysis">查看诊断总览</el-button>
              </div>
            </div>
            <div v-else class="weak-list">
              <button
                v-for="item in weakestNodeRows"
                :key="item.id"
                type="button"
                class="weak-item"
                @click="handleWeakNodePractice(item)"
              >
                <div>
                  <strong>{{ item.subjectName }} · {{ item.label }}</strong>
                  <p>掌握度 {{ item.mastery }}% · 关联题量 {{ item.questionCount }}</p>
                </div>
                <span>去补弱项</span>
              </button>
            </div>
            <div class="panel-actions panel-actions--tight">
              <el-button type="primary" plain :disabled="!hasSubjectOptions" @click="navigateToAnalysis">查看诊断总览</el-button>
            </div>
          </article>
        </aside>
      </section>
    </template>

  </section>
</template>

<style scoped>
.tasks-shell {
  display: grid;
  gap: 20px;
}

.tasks-shell--embedded {
  gap: 0;
}

.tasks-shell--embedded .feature-card {
  min-height: 100%;
  padding: 20px;
  border-radius: var(--qb-student-card-radius);
}

.tasks-shell--embedded .card-header h4 {
  font-size: 17px;
  line-height: 1.3;
}

.tasks-shell--embedded .daily-card,
.tasks-shell--embedded .weak-card {
  display: grid;
  align-content: start;
  gap: var(--qb-space-3);
}

.daily-card--merged {
  display: grid;
  gap: var(--qb-space-3);
}

.execution-banner {
  display: grid;
  gap: 16px;
}

.execution-banner__hero,
.execution-pulse-card {
  border-radius: 28px;
  border: 1px solid rgba(191, 219, 254, 0.65);
  box-shadow: 0 24px 54px rgba(15, 23, 42, 0.08);
}

.execution-banner__hero {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  padding: 26px 28px;
  background:
    radial-gradient(circle at top right, rgba(251, 191, 36, 0.14), transparent 22%),
    radial-gradient(circle at 15% 18%, rgba(59, 130, 246, 0.18), transparent 18%),
    linear-gradient(145deg, rgba(255, 255, 255, 0.98), rgba(239, 246, 255, 0.98));
}

.execution-banner__copy h4,
.execution-banner__copy p {
  margin: 0;
}

.execution-badge {
  display: inline-flex;
  width: fit-content;
  padding: 7px 12px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.92);
  color: var(--qb-text-inverse);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
}

.execution-banner__copy h4 {
  margin-top: 14px;
  color: var(--qb-text-heading);
  font-size: clamp(28px, 3vw, 38px);
  line-height: 1.15;
  max-width: 16ch;
}

.execution-banner__copy p {
  margin-top: 12px;
  max-width: 64ch;
  color: var(--qb-text-copy);
  font-size: 14px;
  line-height: 1.8;
}

.execution-bridge-card {
  display: grid;
  gap: 8px;
  margin-top: 14px;
  padding: 14px 16px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.74);
  border: 1px solid rgba(191, 219, 254, 0.72);
}

.execution-bridge-card strong,
.execution-bridge-card p {
  margin: 0;
}

.execution-bridge-card p {
  color: var(--qb-text-copy);
  line-height: 1.7;
}

.scope-note {
  display: inline-flex;
  width: fit-content;
  margin-top: 12px;
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.72);
  color: var(--qb-text-subtle-4);
  font-size: 12px;
  line-height: 1.5;
  box-shadow: inset 0 0 0 1px rgba(191, 219, 254, 0.88);
}

.execution-banner__actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.execution-banner__grid {
  display: grid;
  gap: 14px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.execution-pulse-card {
  display: grid;
  gap: 8px;
  padding: 18px 20px;
  background: rgba(255, 255, 255, 0.96);
}

.execution-pulse-card span,
.execution-pulse-card small {
  color: var(--qb-text-meta);
  font-size: 12px;
  font-weight: 600;
}

.execution-pulse-card strong {
  color: var(--qb-text-heading);
  font-size: 18px;
  line-height: 1.45;
}

.page-header,
.card-header,
.daily-task-head,
.daily-task-foot,
.profile-progress__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.page-header h3,
.page-header p,
.card-header h4,
.card-header p,
.daily-note,
.weak-item p,
.profile-card p {
  margin: 0;
}

.page-header p {
  margin-top: 6px;
  color: var(--qb-text-copy);
}

.card-header__actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.tasks-layout {
  display: grid;
  gap: 20px;
  grid-template-columns: minmax(0, 1.6fr) minmax(300px, 0.9fr);
  align-items: start;
}

.tasks-main,
.tasks-rail {
  display: grid;
  gap: 20px;
}

.hero-grid {
  display: grid;
  gap: 20px;
  grid-template-columns: minmax(0, 1.35fr) minmax(240px, 0.72fr);
}

.hero-card,
.feature-card,
.profile-card,
.summary-card {
  border-radius: var(--qb-student-card-radius);
  border: var(--qb-student-card-border);
  background: var(--qb-surface-strong);
  box-shadow: var(--qb-student-card-shadow);
}

.hero-card,
.feature-card,
.profile-card {
  padding: 24px;
}

.challenge-card {
  display: grid;
  gap: 16px;
}

.hero-card--coverage {
  display: grid;
  gap: 18px;
}

.hero-card--quota {
  display: grid;
  gap: 18px;
  color: var(--qb-text-inverse);
  background: var(--qb-gradient-brand);
  border-color: transparent;
}

.hero-label,
.section-kicker {
  color: var(--qb-text-subtle-4);
  font-size: 12px;
  font-weight: 700;
}

.section-kicker {
  display: inline-flex;
  align-items: center;
  width: fit-content;
  padding: 6px 10px;
  border-radius: var(--qb-radius-pill);
  background: var(--qb-student-kicker-bg);
  color: var(--qb-student-kicker-text);
  letter-spacing: 0.04em;
}

.hero-card--quota .hero-label,
.hero-card--quota p {
  color: rgba(255, 255, 255, 0.82);
}

.hero-value-row {
  display: flex;
  align-items: flex-end;
  gap: 4px;
}

.hero-value-row strong {
  color: var(--qb-primary-student);
  font-size: 54px;
  line-height: 0.95;
  font-family: var(--font-display);
}

.hero-value-row em {
  color: var(--qb-primary-student);
  font-style: normal;
  font-size: 22px;
  font-weight: 700;
}

.hero-card--quota strong {
  font-size: 42px;
  line-height: 1;
  font-family: var(--font-display);
}

.hero-progress {
  width: 100%;
  height: 8px;
  border-radius: 999px;
  overflow: hidden;
  background: rgba(148, 163, 184, 0.18);
}

.hero-progress span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: var(--qb-gradient-primary-fill);
}

.hero-progress--thin {
  height: 6px;
}

.summary-grid {
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.summary-card {
  display: grid;
  gap: 8px;
  padding: 20px;
}

.summary-card span {
  color: var(--qb-text-subtle-4);
  font-size: 12px;
  font-weight: 700;
}

.summary-card strong {
  color: var(--qb-text-heading);
  font-size: 32px;
  line-height: 1;
  font-family: var(--font-display);
}

.summary-card small {
  color: var(--qb-text-copy);
  font-size: 12px;
  line-height: 1.6;
}

.summary-card--info strong {
  color: var(--qb-text-success-ink);
}

.summary-card--danger strong {
  color: var(--qb-danger-600);
}

.summary-card--success strong {
  color: var(--qb-success-600);
}

.graph-card h4,
.task-stream-card h4,
.selector-card h4,
.weak-card h4,
.daily-card h4,
.card-header h4 {
  margin-top: 6px;
  color: var(--qb-text-heading);
  font-size: 20px;
}

.graph-stage {
  height: 420px;
}

.graph-stage--dark {
  margin-top: 20px;
  border-radius: 20px;
  overflow: hidden;
  background:
    radial-gradient(circle at 50% 50%, rgba(37, 99, 235, 0.16), transparent 48%),
    linear-gradient(180deg, var(--qb-tooltip-bg), rgba(15, 23, 42, 0.96));
}

.profile-card {
  display: grid;
  gap: 18px;
  justify-items: center;
}

.profile-avatar {
  display: grid;
  place-items: center;
  width: 84px;
  height: 84px;
  border-radius: 999px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(219, 234, 254, 0.96));
  color: var(--qb-primary-student);
  font-size: 28px;
  font-weight: 800;
  box-shadow: inset 0 0 0 4px rgba(191, 219, 254, 0.92);
}

.profile-card strong {
  color: var(--qb-text-heading);
  font-size: 28px;
  line-height: 1;
  font-family: var(--font-display);
}

.profile-card p {
  color: var(--qb-text-copy);
  font-size: 13px;
}

.profile-metrics {
  display: grid;
  gap: 12px;
  width: 100%;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.profile-metrics article {
  display: grid;
  gap: 6px;
  padding: 14px;
  border-radius: 16px;
  background: rgba(248, 250, 252, 0.96);
  text-align: center;
}

.profile-metrics span,
.profile-progress small {
  color: var(--qb-text-subtle-4);
  font-size: 12px;
}

.profile-metrics strong {
  font-size: 22px;
}

.profile-progress {
  display: grid;
  gap: 10px;
  width: 100%;
}

.profile-progress__head strong {
  font-size: 16px;
}

.profile-action {
  width: 100%;
}

.subject-select {
  width: 100%;
}

.weak-list,
.daily-task-list {
  display: grid;
  gap: 12px;
  margin-top: 18px;
}

.tasks-shell--embedded .weak-list,
.tasks-shell--embedded .daily-task-list {
  gap: 10px;
  margin-top: 0;
}

.task-record-list,
.task-timeline {
  display: grid;
  gap: 12px;
  margin-top: 18px;
}

.weak-item,
.daily-task-item {
  display: grid;
  gap: 10px;
  padding: 16px;
  border-radius: 18px;
  border: 1px solid rgba(219, 234, 254, 0.96);
  background: rgba(248, 250, 252, 0.96);
}

.tasks-shell--embedded .weak-item,
.tasks-shell--embedded .daily-task-item {
  gap: 8px;
  padding: 14px;
  border-radius: 16px;
}

.weak-item {
  width: 100%;
  text-align: left;
  cursor: pointer;
}

.weak-item strong,
.daily-task-item strong {
  color: var(--qb-text-heading);
  font-size: 15px;
}

.weak-item p,
.daily-task-item p,
.daily-note {
  color: var(--qb-text-copy);
  font-size: 12px;
  line-height: 1.7;
}

.task-record-card {
  display: grid;
  gap: 12px;
  padding: 18px;
  border-radius: 18px;
  border: 1px solid var(--qb-border-soft);
  background: var(--qb-surface-solid);
}

.task-record-card__head,
.task-record-card__foot,
.task-timeline__item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.task-record-card__head strong,
.task-timeline__content strong {
  color: var(--qb-text-heading);
  font-size: 15px;
}

.task-record-card__head p,
.task-record-card__foot span,
.task-timeline__content p {
  margin: 0;
  color: var(--qb-text-copy);
  font-size: 12px;
  line-height: 1.7;
}

.task-record-card--danger {
  border-color: var(--qb-border-danger-soft);
  background: var(--qb-surface-soft-danger);
}

.task-record-card--success {
  border-color: var(--qb-border-success-soft);
  background: var(--qb-surface-soft-success);
}

.task-record-card--info {
  border-color: var(--qb-border-primary-soft);
  background: var(--qb-surface-soft-info);
}

.secondary-insights {
  display: grid;
  gap: 18px;
}

.secondary-insights :deep(.el-collapse) {
  border: none;
}

.secondary-insights :deep(.el-collapse-item__header) {
  align-items: center;
  min-height: auto;
  padding: 0;
  border: none;
  background: transparent;
}

.secondary-insights :deep(.el-collapse-item__wrap) {
  border: none;
  background: transparent;
}

.secondary-insights :deep(.el-collapse-item__content) {
  display: grid;
  gap: 18px;
  padding-bottom: 0;
}

.secondary-insights__title {
  display: grid;
  gap: 8px;
}

.task-timeline {
  padding-top: 8px;
  border-top: 1px solid var(--qb-border-soft);
}

.task-timeline__item {
  justify-content: flex-start;
}

.task-timeline__dot {
  flex: none;
  width: 10px;
  height: 10px;
  margin-top: 6px;
  border-radius: 999px;
  background: var(--qb-track-strong);
}

.task-timeline__dot--danger {
  background: var(--qb-danger-600);
}

.task-timeline__dot--success {
  background: var(--qb-success-600);
}

.task-timeline__dot--info {
  background: var(--qb-primary-student);
}

.task-timeline__content {
  display: grid;
  gap: 2px;
}

.student-empty-panel {
  display: grid;
  gap: 10px;
  padding: 8px 0 4px;
}

.student-status-panel {
  display: grid;
  gap: 10px;
  padding: 16px;
  border-radius: 18px;
  border: 1px solid var(--qb-border-soft);
  background: rgba(248, 250, 252, 0.96);
}

.student-status-panel strong {
  color: var(--qb-text-heading);
  font-size: 15px;
}

.student-status-panel p {
  margin: 0;
  color: var(--qb-text-copy);
  font-size: 12px;
  line-height: 1.7;
}

.student-status-panel--error {
  border-color: var(--qb-border-danger-soft);
  background: var(--qb-surface-soft-danger);
}

.student-empty-panel--compact {
  padding-top: 0;
}

.student-empty-panel__actions {
  display: flex;
  justify-content: center;
  gap: 10px;
  flex-wrap: wrap;
}

.weak-item span {
  color: var(--qb-primary-student);
  font-size: 12px;
  font-weight: 700;
}

.embedded-copy {
  margin: 0;
  color: var(--qb-text-copy);
  font-size: 12px;
  line-height: 1.7;
}

.embedded-copy--strong {
  font-size: 13px;
}

.embedded-recommendation,
.embedded-task-summary {
  padding: 16px;
  border-radius: 18px;
  border: 1px solid rgba(191, 219, 254, 0.72);
  background:
    radial-gradient(circle at top right, rgba(251, 191, 36, 0.12), transparent 32%),
    linear-gradient(145deg, rgba(255, 255, 255, 0.98), rgba(239, 246, 255, 0.92));
}

.embedded-recommendation {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.embedded-recommendation__copy,
.embedded-task-summary,
.embedded-task-checklist {
  display: grid;
  gap: 10px;
}

.embedded-recommendation__label,
.embedded-task-summary__head span {
  color: var(--qb-text-subtle-4);
  font-size: 12px;
  font-weight: 700;
}

.embedded-recommendation__copy strong,
.embedded-task-summary__head strong,
.embedded-task-checklist__item strong {
  color: var(--qb-text-heading);
}

.embedded-recommendation__copy strong {
  font-size: 18px;
  line-height: 1.4;
}

.embedded-recommendation__copy p,
.embedded-task-checklist__item p {
  margin: 0;
  color: var(--qb-text-copy);
  font-size: 12px;
  line-height: 1.7;
}

.embedded-recommendation__actions,
.embedded-task-summary__head,
.embedded-task-checklist__item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.embedded-recommendation__actions {
  flex-wrap: wrap;
}

.embedded-task-checklist__item {
  padding-top: 10px;
  border-top: 1px solid rgba(226, 232, 240, 0.92);
}

.embedded-task-checklist__item:first-child {
  padding-top: 0;
  border-top: none;
}

.embedded-suggestions {
  display: grid;
  gap: var(--qb-space-3);
  padding-top: var(--qb-space-3);
  border-top: 1px solid rgba(226, 232, 240, 0.92);
}

.embedded-meta-note {
  margin: 10px 0 0;
  color: var(--qb-text-subtle-4);
  font-size: 12px;
  line-height: 1.6;
}

.embedded-actions {
  display: flex;
  gap: 10px;
  margin-top: 14px;
  flex-wrap: wrap;
}

@media (max-width: 1180px) {
  .tasks-layout,
  .hero-grid {
    grid-template-columns: 1fr;
  }

  .execution-banner__hero {
    flex-direction: column;
  }

  .execution-banner__grid,
  .summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .embedded-actions,
  .embedded-recommendation,
  .embedded-recommendation__actions,
  .embedded-task-summary__head,
  .embedded-task-checklist__item,
  .execution-banner__actions,
  .card-header__actions,
  .page-header,
  .card-header,
  .daily-task-head,
  .daily-task-foot,
  .profile-progress__head {
    flex-direction: column;
    align-items: flex-start;
  }

  .execution-banner__grid,
  .summary-grid,
  .profile-metrics {
    grid-template-columns: 1fr;
  }

  .student-empty-panel__actions {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
