<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { Cpu, Download, Plus, RefreshRight } from '@/ui/icons'
import { ElMessage, ElMessageBox } from '@/ui/feedback'
import {
  aiGeneratePaper,
  deletePaper,
  deletePaperTemplate,
  exportPaper,
  fetchMyClasses,
  paperOverview,
  paperTemplates,
  restoreDeletedPaper,
  restoreDeletedPaperTemplate,
  saveAutoPaper,
  saveManualPaper,
  savePaperTemplate,
  updatePaperStatus,
} from '../../api/services/papers'
import { listSubjects, professionalTree } from '../../api/services/questionBank'
import AiGenerationDialog from '../../components/papers/AiGenerationDialog.vue'
import QuestionSelectionDrawer from '../../components/papers/QuestionSelectionDrawer.vue'
import { questionTypeLabel } from '../../utils/question'
import { resolveManualDraftScope } from '../../utils/paperDraftScope'
import { buildContentLabelMaps, resolveContentLabel } from '../../utils/contentBaseline.js'
import {
  buildProfessionalScopeOptions as createProfessionalScopeOptions,
  buildScopeKey,
  normalizeScopePath,
  resolveFirstAvailableProfessionalGroupPath,
} from '../../utils/professionalScope'
import { useUserStore } from '../../stores/userStore'

const MANUAL_SELECTION_DRAFT_KEY = 'qbManualPaperSelectionDraft'

const loading = ref(false)
const deletingPaperId = ref('')
const updatingPaperId = ref('')
const exportingPaperId = ref('')
const paperRows = ref([])
const exportDialogVisible = ref(false)
const exportPreview = ref('')
const exportPreviewTitle = ref('')
const exportPaperName = ref('')
const exportFormat = ref('txt')
const exportTargetPaperId = ref('')
const deletedPaperUndoSnapshotId = ref('')
const deletedPaperName = ref('')
const manualDialogVisible = ref(false)
const manualSaving = ref(false)
const manualSubjectLoading = ref(false)
const manualProfessionalLoading = ref(false)
const professionalOptions = ref([])
const professionalTreeRaw = ref([])
const professionalScopeMetaMap = ref({})
const manualSubjectNameToIdMap = ref({})
const manualSubjectCodeToIdMap = ref({})
const classList = ref([])
const questionSelectionDrawerVisible = ref(false)
const selectedQuestions = ref([])
const manualTargetKnowledgeIds = ref([])
const manualTargetKnowledgeMap = ref({})
const manualTargetWeightMap = ref({})
const aiDialogVisible = ref(false)
const aiGenerating = ref(false)
const aiGenerationProgress = ref(0)
const templateLoading = ref(false)
const templateSaving = ref(false)
const applyingTemplateId = ref('')
const deletingTemplateId = ref('')
const lastDeletedTemplateSnapshotId = ref('')
const lastDeletedTemplateName = ref('')
const paperTemplateRows = ref([])
let aiProgressTimer = 0
const userStore = useUserStore()

const SUBJECT_ID_FALLBACK_BY_CODE = {
  POLITICS: 'subject-politics',
  ENGLISH: 'subject-english',
  ADVANCED_MATH_1: 'subject-advanced-math-1',
  ADVANCED_MATH_2: 'subject-advanced-math-2',
  INFO_TECH_INTRO: 'subject-computer',
}
const SUBJECT_CODE_FALLBACK_BY_ID = {
  'subject-politics': 'POLITICS',
  'subject-english': 'ENGLISH',
  'subject-advanced-math-1': 'ADVANCED_MATH_1',
  'subject-advanced-math-2': 'ADVANCED_MATH_2',
  'subject-computer': 'INFO_TECH_INTRO',
}
const POLICY_VERSION = 'HB_ZSB_2026'
const professionalCascaderProps = {
  value: 'code',
  label: 'name',
  children: 'children',
  checkStrictly: false,
}
const groupPaperCascaderProps = {
  ...professionalCascaderProps,
  checkStrictly: false,
}
const manualPaperCascaderProps = {
  ...professionalCascaderProps,
  checkStrictly: false,
}
const PAPER_EXPORT_FORMAT_OPTIONS = [
  { value: 'txt', label: 'TXT 文本预览' },
  { value: 'word', label: 'Word 文本预览' },
  { value: 'pdf', label: 'PDF 文本预览' },
]
const PAPER_TEMPLATE_TYPE_OPTIONS = [
  { value: 'single_choice', label: '单选题' },
  { value: 'multiple_choice', label: '多选题' },
  { value: 'judge', label: '判断题' },
  { value: 'subjective', label: '主观题' },
]

const manualForm = reactive({
  paperName: '',
  scope_path: [],
  exam_category_code: '',
  joint_exam_group_code: '',
  subject_code: '',
  subject_id: '',
  policy_version: POLICY_VERSION,
  paperType: 'chapter',
  paperStatus: 'DRAFT',
  durationMinutes: 30,
  visibleToStudents: true,
  difficulty: 'medium',
  publish_class_ids: [],
})
const templateForm = reactive(createTemplateForm())
const selectedQuestionCount = computed(() => selectedQuestions.value.length)
const totalScore = computed(() =>
  selectedQuestions.value.reduce((sum, questionItem) => sum + Number(questionItem.score || 0), 0),
)
const assignedJointGroupCode = computed(() =>
  String(userStore.assigned_joint_group_code || userStore.assignedJointGroupCode || userStore.jointExamGroupCode || '').trim(),
)
const scopeLabelMaps = computed(() => buildContentLabelMaps(userStore.availableExamCategories))
const isScopeLocked = computed(() =>
  String(userStore.role || '').trim() !== 'super_admin' && Boolean(assignedJointGroupCode.value),
)
const paperStatusActionMap = computed(() => ({
  DRAFT: [{ label: '提审', targetStatus: 'REVIEW_PENDING', type: 'warning' }],
  REVIEW_PENDING: [
    { label: '退回草稿', targetStatus: 'DRAFT', type: 'info' },
    { label: '发布', targetStatus: 'PUBLISHED', type: 'success' },
  ],
  PUBLISHED: [{ label: '下架', targetStatus: 'OFFLINE', type: 'warning' }],
  OFFLINE: [{ label: '重新提审', targetStatus: 'REVIEW_PENDING', type: 'primary' }],
}))

function createDefaultTemplateRules() {
  return [
    { type: 'single_choice', count: 5, questionScore: 4 },
    { type: 'multiple_choice', count: 2, questionScore: 10 },
  ]
}

function createTemplateForm() {
  return {
    templateId: '',
    templateName: '',
    scope_path: [],
    exam_category_code: '',
    joint_exam_group_code: '',
    subject_code: '',
    subject_id: '',
    policy_version: POLICY_VERSION,
    paperType: 'chapter',
    chapter: '',
    difficulty: 'medium',
    totalScore: 40,
    durationMinutes: 45,
    typeRules: createDefaultTemplateRules(),
  }
}

function unwrapData(response) {
  if (response && typeof response === 'object' && 'data' in response) {
    return response.data
  }
  return response
}

function normalizePaperRows(payload) {
  const rows = Array.isArray(payload) ? payload : []
  return rows.map((item) => ({
    paperId: String(item?.paperId || item?.id || ''),
    paperName: String(item?.paperName || '-'),
    questionCount: Number(item?.questionCount || 0),
    totalScore: Number(item?.totalScore || 0),
    updateTime: String(item?.updateTime || item?.createTime || '-'),
    paperStatus: String(item?.paperStatus || 'UNKNOWN').trim() || 'UNKNOWN',
  }))
}

async function fetchPaperOverview() {
  const response = await paperOverview()
  return unwrapData(response)
}

async function loadPaperOverview() {
  loading.value = true
  try {
    const payload = await fetchPaperOverview()
    paperRows.value = normalizePaperRows(payload)
  } catch (error) {
    paperRows.value = []
    ElMessage.error(String(error?.response?.data?.message || error?.message || '试卷概览加载失败'))
  } finally {
    loading.value = false
  }
}

function normalizeSubjectName(value) {
  return String(value || '').replace(/\s+/g, '').replace(/[()（）]/g, '').trim()
}

function normalizeManualSubjectRoots(payload) {
  const rows = Array.isArray(payload) ? payload : []
  const rootRows = []
  const seenIds = new Set()
  rows.forEach((item) => {
    const id = String(item?.id || '').trim()
    const name = String(item?.name || id).trim()
    const parentId = String(item?.parentId || '').trim()
    if (!id || parentId || seenIds.has(id)) {
      return
    }
    seenIds.add(id)
    rootRows.push({ id, name: name || id })
  })
  return rootRows
}

function applyProfessionalScopeOptions(treeNodes) {
  const { options, scopeMetaMap } = createProfessionalScopeOptions(treeNodes, {
    assignedJointGroupCode: isScopeLocked.value ? assignedJointGroupCode.value : '',
  })
  professionalOptions.value = options
  professionalScopeMetaMap.value = scopeMetaMap

  const currentScopePath = normalizeScopePath(manualForm.scope_path)
  if (!isScopeLocked.value) {
    if (currentScopePath.length >= 2 && !isSelectableManualScopePath(currentScopePath)) {
      manualForm.scope_path = []
    }
    return
  }

  if (!isSelectableManualScopePath(currentScopePath)) {
    manualForm.scope_path = resolveFirstAvailableProfessionalGroupPath(professionalOptions.value)
  }
}

function isSelectableManualScopePath(pathValue) {
  const normalizedPath = normalizeScopePath(pathValue)
  const [categoryCode = '', groupCode = '', subjectCode = ''] = normalizedPath
  if (!categoryCode || !groupCode) {
    return false
  }
  const categoryItem = professionalOptions.value.find((item) => String(item?.code || '').trim() === categoryCode)
  if (!categoryItem) {
    return false
  }
  const groupItem = (Array.isArray(categoryItem?.children) ? categoryItem.children : []).find(
    (item) => String(item?.code || '').trim() === groupCode,
  )
  if (!groupItem) {
    return false
  }
  if (!subjectCode) {
    return true
  }
  const scopeKey = buildScopeKey(normalizedPath)
  return Boolean(scopeKey && professionalScopeMetaMap.value[scopeKey])
}

function resolveManualScopeSelection(pathValue) {
  const normalizedPath = normalizeScopePath(pathValue)
  const [examCategoryCode = '', jointExamGroupCode = '', subjectCode = ''] = normalizedPath
  const isSingleSubject = normalizedPath.length === 3 && Boolean(subjectCode)
  const scopeMeta = isSingleSubject
    ? (professionalScopeMetaMap.value[buildScopeKey(normalizedPath)] || {})
    : {}
  return {
    examCategoryCode,
    jointExamGroupCode,
    subjectCode: isSingleSubject ? subjectCode : '',
    subjectId: isSingleSubject ? resolveSubjectId(subjectCode, scopeMeta.subjectName || '') : '',
    scopePath: normalizedPath.slice(0, isSingleSubject ? 3 : 2),
  }
}

function buildManualScopeIdentity(pathValue) {
  return resolveManualScopeSelection(pathValue).scopePath.join('::')
}

function normalizeTemplateRows(payload) {
  const rows = Array.isArray(payload) ? payload : []
  return rows.map((item) => ({
    templateId: String(item?.templateId || ''),
    templateName: String(item?.templateName || '-'),
    paperType: String(item?.paperType || '-'),
    subjectId: String(item?.subjectId || ''),
    chapter: String(item?.chapter || ''),
    difficulty: String(item?.difficulty || ''),
    totalScore: Number(item?.totalScore || 0),
    durationMinutes: Number(item?.durationMinutes || 0),
    examCategoryCode: String(item?.examCategoryCode || ''),
    jointExamGroupCode: String(item?.jointExamGroupCode || ''),
    subjectCode: String(item?.subjectCode || ''),
    typeRules: Array.isArray(item?.typeRules) ? item.typeRules : [],
    createTime: String(item?.createTime || ''),
    updateTime: String(item?.updateTime || ''),
  }))
}

function resetTemplateForm() {
  Object.assign(templateForm, createTemplateForm())
  if (professionalTreeRaw.value.length) {
    applyProfessionalScopeOptions(professionalTreeRaw.value)
  }
}

function populateTemplateForm(row) {
  const examCategoryCode = String(row?.examCategoryCode || '').trim()
  const jointExamGroupCode = String(row?.jointExamGroupCode || '').trim()
  const subjectCode = String(row?.subjectCode || '').trim() || resolveSubjectCodeById(row?.subjectId)
  Object.assign(templateForm, {
    templateId: String(row?.templateId || '').trim(),
    templateName: String(row?.templateName || '').trim(),
    scope_path: examCategoryCode && jointExamGroupCode
      ? [examCategoryCode, jointExamGroupCode, ...(subjectCode ? [subjectCode] : [])]
      : [],
    exam_category_code: examCategoryCode,
    joint_exam_group_code: jointExamGroupCode,
    subject_code: subjectCode,
    subject_id: String(row?.subjectId || '').trim() || resolveSubjectId(subjectCode),
    policy_version: POLICY_VERSION,
    paperType: String(row?.paperType || 'chapter').trim() || 'chapter',
    chapter: String(row?.chapter || '').trim(),
    difficulty: String(row?.difficulty || 'medium').trim() || 'medium',
    totalScore: Math.max(1, Number(row?.totalScore || 40)),
    durationMinutes: Math.max(1, Number(row?.durationMinutes || 45)),
    typeRules: Array.isArray(row?.typeRules) && row.typeRules.length
      ? row.typeRules.map((item) => ({
        type: String(item?.type || 'single_choice').trim() || 'single_choice',
        count: Math.max(1, Number(item?.count || 1)),
        questionScore: Math.max(1, Number(item?.questionScore || 1)),
      }))
      : createDefaultTemplateRules(),
  })
}

function resolveTemplateScopeLabel(row) {
  const examCategoryCode = String(row?.examCategoryCode || '').trim()
  const jointExamGroupCode = String(row?.jointExamGroupCode || '').trim()
  const subjectCode = String(row?.subjectCode || '').trim()

  if (examCategoryCode && jointExamGroupCode && subjectCode) {
    const subjectScopeMeta = professionalScopeMetaMap.value[
      buildScopeKey([examCategoryCode, jointExamGroupCode, subjectCode])
    ] || {}
    const subjectName = String(subjectScopeMeta.subjectName || '').trim()
    if (subjectName) {
      return subjectName
    }
  }

  return `${resolveContentLabel(scopeLabelMaps.value.examCategoryNameMap, examCategoryCode)} / ${resolveContentLabel(scopeLabelMaps.value.jointExamGroupNameMap, jointExamGroupCode)}`
}

function resolvePaperTypeLabel(paperType) {
  const normalized = String(paperType || '').trim()
  if (normalized === 'chapter') return '章节练习'
  if (normalized === 'unit') return '单元练习'
  if (normalized === 'final') return '期末考'
  if (normalized === 'simulation') return '模拟考试'
  return normalized || '-'
}

function buildTemplateDescription(row) {
  const parts = []
  const paperTypeLabel = resolvePaperTypeLabel(row?.paperType)
  if (paperTypeLabel) {
    parts.push(`卷型：${paperTypeLabel}`)
  }
  const scopeLabel = resolveTemplateScopeLabel(row)
  if (scopeLabel) {
    parts.push(`范围：${scopeLabel}`)
  }
  const difficultyLabel = String(row?.difficulty || '').trim()
  if (difficultyLabel) {
    parts.push(`难度：${difficultyLabel}`)
  }
  const totalScore = Number(row?.totalScore || 0)
  if (totalScore > 0) {
    parts.push(`总分：${totalScore}`)
  }
  const durationMinutes = Number(row?.durationMinutes || 0)
  if (durationMinutes > 0) {
    parts.push(`考试时长：${durationMinutes} 分钟`)
  }
  const ruleCount = Array.isArray(row?.typeRules) ? row.typeRules.length : 0
  parts.push(`题型规则：${ruleCount} 条`)
  return parts.join(' · ')
}

function addTemplateRule() {
  templateForm.typeRules.push({
    type: 'single_choice',
    count: 1,
    questionScore: 5,
  })
}

function buildTemplatePaperName(templateName) {
  const normalizedTemplateName = String(templateName || '').trim() || '模板'
  const now = new Date()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const date = String(now.getDate()).padStart(2, '0')
  const hour = String(now.getHours()).padStart(2, '0')
  const minute = String(now.getMinutes()).padStart(2, '0')
  return `${normalizedTemplateName}-应用组卷-${month}${date}-${hour}${minute}`
}

function removeTemplateRule(index) {
  if (templateForm.typeRules.length <= 1) {
    ElMessage.warning('模板至少保留 1 条题型规则。')
    return
  }
  templateForm.typeRules.splice(index, 1)
}

async function loadPaperTemplates() {
  templateLoading.value = true
  try {
    const response = await paperTemplates()
    paperTemplateRows.value = normalizeTemplateRows(unwrapData(response))
  } catch (error) {
    paperTemplateRows.value = []
    ElMessage.error(String(error?.response?.data?.message || error?.message || '试卷模板加载失败'))
  } finally {
    templateLoading.value = false
  }
}

function resolveSubjectId(subjectCode, subjectName = '') {
  const normalizedCode = String(subjectCode || '').trim()
  if (!normalizedCode) {
    return ''
  }
  const byCode = String(manualSubjectCodeToIdMap.value[normalizedCode] || '').trim()
  if (byCode) {
    return byCode
  }

  const normalizedName = normalizeSubjectName(subjectName)
  const byName = String(manualSubjectNameToIdMap.value[normalizedName] || '').trim()
  if (byName) {
    return byName
  }

  const fallback = String(SUBJECT_ID_FALLBACK_BY_CODE[normalizedCode] || '').trim()
  if (fallback) {
    return fallback
  }
  return normalizedCode
}

function resolveSubjectCodeById(subjectId) {
  const normalizedSubjectId = String(subjectId || '').trim()
  if (!normalizedSubjectId) {
    return ''
  }
  const byFallback = String(SUBJECT_CODE_FALLBACK_BY_ID[normalizedSubjectId] || '').trim()
  if (byFallback) {
    return byFallback
  }
  const matchedEntry = Object.entries(manualSubjectCodeToIdMap.value).find(
    ([, value]) => String(value || '').trim() === normalizedSubjectId,
  )
  return String(matchedEntry?.[0] || '').trim()
}

function normalizeClassList(payload) {
  const rows = Array.isArray(payload) ? payload : []
  const normalized = []
  const seen = new Set()
  rows.forEach((item) => {
    const class_id = String(item?.class_id || item?.classId || '').trim()
    if (!class_id || seen.has(class_id)) {
      return
    }
    seen.add(class_id)
    normalized.push({
      class_id,
      class_name: String(item?.class_name || item?.className || class_id).trim() || class_id,
    })
  })
  return normalized
}

async function loadMyClasses() {
  try {
    const response = await fetchMyClasses()
    classList.value = normalizeClassList(unwrapData(response))
  } catch (error) {
    classList.value = []
    ElMessage.error(String(error?.response?.data?.message || error?.message || '班级列表加载失败'))
  }
}

async function loadManualSubjectOptions() {
  if (Object.keys(manualSubjectNameToIdMap.value).length) {
    return
  }

  manualSubjectLoading.value = true
  try {
    const response = await listSubjects()
    const rootRows = normalizeManualSubjectRoots(unwrapData(response))
    const nextNameToIdMap = {}
    const nextCodeToIdMap = {}
    rootRows.forEach((item) => {
      const subjectName = String(item?.name || '').trim()
      const subjectId = String(item?.id || '').trim()
      if (!subjectName || !subjectId) {
        return
      }
      nextNameToIdMap[normalizeSubjectName(subjectName)] = subjectId

      if (subjectName.includes('政治')) {
        nextCodeToIdMap.POLITICS = subjectId
      }
      if (subjectName.includes('英语')) {
        nextCodeToIdMap.ENGLISH = subjectId
      }
      if (subjectName.includes('数学')) {
        nextCodeToIdMap.ADVANCED_MATH_1 = subjectId
        nextCodeToIdMap.ADVANCED_MATH_2 = subjectId
      }
      if (subjectName.includes('信息技术') || subjectName.includes('计算机')) {
        nextCodeToIdMap.INFO_TECH_INTRO = subjectId
      }
    })
    manualSubjectNameToIdMap.value = nextNameToIdMap
    manualSubjectCodeToIdMap.value = nextCodeToIdMap
  } catch (error) {
    manualSubjectNameToIdMap.value = {}
    manualSubjectCodeToIdMap.value = {}
    ElMessage.error(String(error?.response?.data?.message || error?.message || '科目列表加载失败'))
  } finally {
    manualSubjectLoading.value = false
  }
}

async function fetchProfessionalTree() {
  if (professionalTreeRaw.value.length) {
    applyProfessionalScopeOptions(professionalTreeRaw.value)
    return
  }

  manualProfessionalLoading.value = true
  try {
    const response = await professionalTree()
    professionalTreeRaw.value = unwrapData(response) || []
    applyProfessionalScopeOptions(professionalTreeRaw.value)
  } catch (error) {
    professionalTreeRaw.value = []
    professionalOptions.value = []
    professionalScopeMetaMap.value = {}
    ElMessage.error(String(error?.response?.data?.message || error?.message || '专业层级字典加载失败'))
  } finally {
    manualProfessionalLoading.value = false
  }
}

function paperStatusLabel(status) {
  const normalized = String(status || '').trim()
  if (normalized === 'DRAFT') return '草稿'
  if (normalized === 'REVIEW_PENDING') return '待审核'
  if (normalized === 'PUBLISHED') return '已发布'
  if (normalized === 'OFFLINE') return '已下架'
  if (normalized === 'ARCHIVED') return '已归档'
  if (normalized === 'DISABLED') return '已停用'
  return normalized || '-'
}

function paperStatusTagType(status) {
  const normalized = String(status || '').trim()
  if (normalized === 'PUBLISHED') return 'success'
  if (normalized === 'REVIEW_PENDING') return 'warning'
  if (normalized === 'OFFLINE') return 'info'
  if (normalized === 'ARCHIVED') return 'warning'
  if (normalized === 'DISABLED') return 'danger'
  if (normalized === 'DRAFT') return 'info'
  return ''
}

function resolvePaperTransitionActions(status) {
  return paperStatusActionMap.value[String(status || '').trim()] || []
}

async function handleManualCreate() {
  hydrateManualSelectionDraft()
  await Promise.all([loadManualSubjectOptions(), fetchProfessionalTree()])
  if (!manualDialogVisible.value) {
    if (!String(manualForm.paperName || '').trim()) {
      manualForm.paperName = buildDefaultPaperName()
    }
    manualDialogVisible.value = true
  }
}

async function handleAiCompose() {
  await Promise.all([fetchProfessionalTree(), loadManualSubjectOptions()])
  aiGenerationProgress.value = 0
  aiDialogVisible.value = true
}

function stopAiProgress() {
  if (aiProgressTimer) {
    clearInterval(aiProgressTimer)
    aiProgressTimer = 0
  }
}

function startAiProgress() {
  stopAiProgress()
  aiGenerationProgress.value = 8
  aiProgressTimer = window.setInterval(() => {
    const current = Number(aiGenerationProgress.value || 0)
    if (current >= 92) {
      stopAiProgress()
      return
    }
    const step = current < 40 ? 8 : (current < 70 ? 5 : 2)
    aiGenerationProgress.value = Math.min(92, current + step)
  }, 220)
}

async function handleAiGenerate(payload) {
  const examCategoryCode = String(payload?.exam_category_code || '').trim()
  const jointExamGroupCode = String(payload?.joint_exam_group_code || '').trim()
  const subjectCode = String(payload?.subject_code || '').trim()
  const subjectId = String(payload?.subject_id || resolveSubjectId(subjectCode)).trim()
  const classIds = Array.isArray(payload?.class_ids)
    ? payload.class_ids.map((item) => String(item || '').trim()).filter((item) => Boolean(item))
    : []
  const totalCount = Number(payload?.total_count || 0)
  const difficultyLevel = Number(payload?.difficulty_level || 0)
  const knowledgeScope = Array.isArray(payload?.knowledge_scope)
    ? payload.knowledge_scope.map((item) => String(item || '').trim()).filter((item) => Boolean(item))
    : []
  if (!examCategoryCode || !jointExamGroupCode) {
    ElMessage.warning('请选择目标专业（学科门类 + 联考专业组）。')
    return
  }
  aiGenerating.value = true
  startAiProgress()

  try {
    const response = await aiGeneratePaper({
      subjectId,
      examCategoryCode,
      jointExamGroupCode,
      subjectCode,
      classIds,
      totalCount,
      difficulty: difficultyLevel,
      knowledgeScope,
    })
    stopAiProgress()
    aiGenerationProgress.value = 100
    const result = unwrapData(response) || {}
    const paperId = String(result?.paper_id || result?.paperId || '').trim()
    if (!paperId) {
      throw new Error('后端未返回 paper_id，无法确认生成结果。')
    }

    ElMessage.success(`AI 智能组卷完成，试卷ID：${paperId}`)
    aiDialogVisible.value = false
    await loadPaperOverview()
    await loadPaperTemplates()
  } catch (error) {
    stopAiProgress()
    aiGenerationProgress.value = 0
    ElMessage.error(String(error?.response?.data?.message || error?.message || 'AI 智能组卷失败'))
  } finally {
    aiGenerating.value = false
  }
}

function normalizeQuestionRows(input_rows) {
  const source_rows = Array.isArray(input_rows) ? input_rows : []
  const unique_rows = []
  const seen = new Set()

  source_rows.forEach((item) => {
    const normalizedId = String(item?.id || item || '').trim()
    if (!normalizedId || seen.has(normalizedId)) {
      return
    }
    seen.add(normalizedId)
    unique_rows.push({
      id: normalizedId,
      stem: String(item?.stem || ''),
      type: String(item?.type || ''),
      knowledgeId: String(item?.knowledgeId || item?.knowledge_id || '').trim(),
      knowledgeName: String(item?.knowledgeName || item?.knowledge_name || '').trim(),
      score: Math.max(1, Number(item?.score || 5)),
    })
  })

  return unique_rows
}

function buildDefaultPaperName() {
  const now = new Date()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const date = String(now.getDate()).padStart(2, '0')
  const hour = String(now.getHours()).padStart(2, '0')
  const minute = String(now.getMinutes()).padStart(2, '0')
  return `手动组卷-${month}${date}-${hour}${minute}`
}

function hydrateManualSelectionDraft() {
  try {
    const raw = sessionStorage.getItem(MANUAL_SELECTION_DRAFT_KEY)
    if (!raw) {
      return
    }

    const parsed = JSON.parse(raw)
    const target_knowledge_ids = Array.isArray(parsed?.targetKnowledgeIds)
      ? parsed.targetKnowledgeIds.map((id) => String(id || '').trim()).filter((id) => Boolean(id))
      : []
    const target_knowledge_map = parsed?.targetKnowledgeMap && typeof parsed.targetKnowledgeMap === 'object'
      ? parsed.targetKnowledgeMap
      : {}
    const target_weight_map = parsed?.targetWeightMap && typeof parsed.targetWeightMap === 'object'
      ? parsed.targetWeightMap
      : {}
    const draft_scope = resolveManualDraftScope(
      parsed,
      { policy_version: POLICY_VERSION },
    )
    const exam_category_code = String(draft_scope.exam_category_code || '').trim()
    const joint_exam_group_code = String(draft_scope.joint_exam_group_code || '').trim()
    const subject_code = String(draft_scope.subject_code || '').trim()
    const subject_id = String(parsed?.subjectId || parsed?.subject_id || '').trim()
    const policy_version = String(draft_scope.policy_version || POLICY_VERSION).trim() || POLICY_VERSION
    const publish_class_ids = Array.isArray(parsed?.publishClassIds)
      ? parsed.publishClassIds.map((id) => String(id || '').trim()).filter((id) => Boolean(id))
      : (Array.isArray(parsed?.publish_class_ids)
          ? parsed.publish_class_ids.map((id) => String(id || '').trim()).filter((id) => Boolean(id))
          : (Array.isArray(parsed?.targetClassIds)
              ? parsed.targetClassIds.map((id) => String(id || '').trim()).filter((id) => Boolean(id))
              : (Array.isArray(parsed?.target_class_ids)
                  ? parsed.target_class_ids.map((id) => String(id || '').trim()).filter((id) => Boolean(id))
                  : [])))
    const draft_rows = Array.isArray(parsed?.questions) && parsed.questions.length
      ? parsed.questions
      : (Array.isArray(parsed?.questionIds) ? parsed.questionIds : []).map((question_id) => ({
        id: String(question_id || '').trim(),
        stem: '',
        type: '',
        score: 5,
      }))
    const normalized_rows = normalizeQuestionRows(draft_rows)
    if (!normalized_rows.length) {
      return
    }

    selectedQuestions.value = normalized_rows
    manualTargetKnowledgeIds.value = Array.from(new Set(target_knowledge_ids))
    manualTargetKnowledgeMap.value = target_knowledge_map
    manualTargetWeightMap.value = target_weight_map
    const normalizedSubjectCode = subject_code || resolveSubjectCodeById(subject_id)
    manualForm.scope_path = (exam_category_code && joint_exam_group_code)
      ? [exam_category_code, joint_exam_group_code, ...(normalizedSubjectCode ? [normalizedSubjectCode] : [])]
      : (Array.isArray(draft_scope.scope_path) ? draft_scope.scope_path : [])
    if (!manualForm.scope_path.length) {
      manualForm.exam_category_code = exam_category_code
      manualForm.joint_exam_group_code = joint_exam_group_code
      manualForm.subject_code = normalizedSubjectCode
      manualForm.subject_id = subject_id || resolveSubjectId(normalizedSubjectCode)
    }
    manualForm.policy_version = policy_version
    manualForm.publish_class_ids = Array.from(new Set(publish_class_ids))
    if (!String(manualForm.paperName || '').trim()) {
      manualForm.paperName = buildDefaultPaperName()
    }
    manualDialogVisible.value = true
  } catch (error) {
    sessionStorage.removeItem(MANUAL_SELECTION_DRAFT_KEY)
  }
}

function persistManualSelectionDraft() {
  const normalized_rows = normalizeQuestionRows(selectedQuestions.value)
  if (!normalized_rows.length) {
    sessionStorage.removeItem(MANUAL_SELECTION_DRAFT_KEY)
    return
  }

  const draft_scope = resolveManualDraftScope(
    {
      exam_category_code: manualForm.exam_category_code,
      joint_exam_group_code: manualForm.joint_exam_group_code,
      subject_code: manualForm.subject_code,
      scope_path: manualForm.scope_path,
      policy_version: manualForm.policy_version,
    },
    { policy_version: POLICY_VERSION },
  )
  const target_knowledge_ids = Array.isArray(manualTargetKnowledgeIds.value)
    ? manualTargetKnowledgeIds.value.map((id) => String(id || '').trim()).filter((id) => Boolean(id))
    : []
  const publish_class_ids = Array.isArray(manualForm.publish_class_ids)
    ? manualForm.publish_class_ids.map((id) => String(id || '').trim()).filter((id) => Boolean(id))
    : []

  sessionStorage.setItem(
    MANUAL_SELECTION_DRAFT_KEY,
    JSON.stringify({
      paperName: String(manualForm.paperName || '').trim(),
      policyVersion: draft_scope.policyVersion || POLICY_VERSION,
      policy_version: draft_scope.policy_version || POLICY_VERSION,
      examCategoryCode: draft_scope.examCategoryCode,
      jointExamGroupCode: draft_scope.jointExamGroupCode,
      subjectCode: draft_scope.subjectCode,
      exam_category_code: draft_scope.exam_category_code,
      joint_exam_group_code: draft_scope.joint_exam_group_code,
      subject_code: draft_scope.subject_code,
      scope_path: draft_scope.scope_path,
      subjectId: String(manualForm.subject_id || '').trim(),
      subject_id: String(manualForm.subject_id || '').trim(),
      targetKnowledgeIds: Array.from(new Set(target_knowledge_ids)),
      targetKnowledgeMap: manualTargetKnowledgeMap.value,
      targetWeightMap: manualTargetWeightMap.value,
      publishClassIds: Array.from(new Set(publish_class_ids)),
      publish_class_ids: Array.from(new Set(publish_class_ids)),
      questionIds: normalized_rows.map((item) => item.id),
      questions: normalized_rows.map((item) => ({
        id: String(item.id || ''),
        stem: String(item.stem || ''),
        type: String(item.type || ''),
        knowledgeId: String(item.knowledgeId || ''),
        score: Math.max(1, Number(item.score || 1)),
      })),
    }),
  )
}

function resetManualForm() {
  manualForm.paperName = ''
  manualForm.scope_path = []
  manualForm.exam_category_code = ''
  manualForm.joint_exam_group_code = ''
  manualForm.subject_code = ''
  manualForm.subject_id = ''
  manualForm.policy_version = POLICY_VERSION
  manualForm.paperType = 'chapter'
  manualForm.paperStatus = 'DRAFT'
  manualForm.durationMinutes = 30
  manualForm.visibleToStudents = true
  manualForm.difficulty = 'medium'
  manualForm.publish_class_ids = []
  selectedQuestions.value = []
  manualTargetKnowledgeIds.value = []
  manualTargetKnowledgeMap.value = {}
  manualTargetWeightMap.value = {}
  if (professionalTreeRaw.value.length) {
    applyProfessionalScopeOptions(professionalTreeRaw.value)
  }
}

watch(
  () => (Array.isArray(manualForm.scope_path) ? [...manualForm.scope_path] : []),
  (nextPath, previousPath) => {
    const nextSelection = resolveManualScopeSelection(nextPath)
    const previousIdentity = buildManualScopeIdentity(previousPath)
    const currentIdentity = nextSelection.scopePath.join('::')

    if (!nextSelection.examCategoryCode || !nextSelection.jointExamGroupCode) {
      manualForm.exam_category_code = ''
      manualForm.joint_exam_group_code = ''
      manualForm.subject_code = ''
      manualForm.subject_id = ''
      if (previousIdentity && selectedQuestions.value.length) {
        selectedQuestions.value = []
        ElMessage.info('组卷范围已变更，已自动清空已选题目，请重新选题。')
      }
      persistManualSelectionDraft()
      return
    }

    manualForm.exam_category_code = nextSelection.examCategoryCode
    manualForm.joint_exam_group_code = nextSelection.jointExamGroupCode
    manualForm.subject_code = nextSelection.subjectCode
    manualForm.subject_id = nextSelection.subjectId
    persistManualSelectionDraft()

    if (previousIdentity && previousIdentity !== currentIdentity && selectedQuestions.value.length) {
      selectedQuestions.value = []
      ElMessage.info('组卷范围已变更，已自动清空已选题目，请重新选题。')
      persistManualSelectionDraft()
    }
  },
  { deep: true },
)

watch(
  () => (Array.isArray(templateForm.scope_path) ? [...templateForm.scope_path] : []),
  (nextPath) => {
    const nextSelection = resolveManualScopeSelection(nextPath)
    if (!nextSelection.examCategoryCode || !nextSelection.jointExamGroupCode) {
      templateForm.exam_category_code = ''
      templateForm.joint_exam_group_code = ''
      templateForm.subject_code = ''
      templateForm.subject_id = ''
      return
    }
    templateForm.exam_category_code = nextSelection.examCategoryCode
    templateForm.joint_exam_group_code = nextSelection.jointExamGroupCode
    templateForm.subject_code = nextSelection.subjectCode
    templateForm.subject_id = nextSelection.subjectId
  },
  { deep: true },
)

watch(
  () => selectedQuestions.value,
  () => {
    persistManualSelectionDraft()
  },
  { deep: true },
)

watch(
  () => ({
    paper_name: manualForm.paperName,
    policy_version: manualForm.policy_version,
    subject_id: manualForm.subject_id,
    publish_class_ids: Array.isArray(manualForm.publish_class_ids) ? [...manualForm.publish_class_ids] : [],
  }),
  () => {
    persistManualSelectionDraft()
  },
  { deep: true },
)

function openQuestionSelectionDrawer() {
  if (!String(manualForm.exam_category_code || '').trim() || !String(manualForm.joint_exam_group_code || '').trim()) {
    ElMessage.warning('请先选择所属专业（学科门类 + 联考专业组）。')
    return
  }
  questionSelectionDrawerVisible.value = true
}

function handleQuestionSelectionConfirm(rows) {
  selectedQuestions.value = normalizeQuestionRows(rows)
  persistManualSelectionDraft()
}

function handleRemoveSelectedQuestion(question_id) {
  selectedQuestions.value = selectedQuestions.value.filter(
    (question_item) => String(question_item?.id || '') !== String(question_id || ''),
  )
  persistManualSelectionDraft()
}

async function handleManualSubmit() {
  const paperName = String(manualForm.paperName || '').trim()
  const exam_category_code = String(manualForm.exam_category_code || '').trim()
  const joint_exam_group_code = String(manualForm.joint_exam_group_code || '').trim()
  const subject_code = String(manualForm.subject_code || '').trim()
  const subject_id = String(manualForm.subject_id || '').trim()
  const policy_version = String(manualForm.policy_version || POLICY_VERSION).trim() || POLICY_VERSION
  const paperType = String(manualForm.paperType || '').trim()
  const paperStatus = String(manualForm.paperStatus || '').trim()
  const publish_class_ids = Array.isArray(manualForm.publish_class_ids)
    ? manualForm.publish_class_ids.map((id) => String(id || '').trim()).filter((id) => Boolean(id))
    : []
  const question_rows = normalizeQuestionRows(selectedQuestions.value)
  const question_ids = question_rows.map((item) => item.id)
  const question_scores = {}
  question_rows.forEach((item) => {
    question_scores[item.id] = Math.max(1, Number(item.score || 1))
  })
  const total_score = question_rows.reduce((sum, item) => sum + Number(item.score || 0), 0)

  if (!paperName) {
    ElMessage.warning('请填写试卷名称。')
    return
  }
  if (!paperType) {
    ElMessage.warning('请填写卷型。')
    return
  }
  if (!exam_category_code || !joint_exam_group_code) {
    ElMessage.warning('请选择所属专业（学科门类 + 联考专业组）。')
    return
  }
  if (!paperStatus) {
    ElMessage.warning('请选择试卷状态。')
    return
  }
  if (!question_ids.length) {
    ElMessage.warning('请先选择至少 1 道题目。')
    return
  }
  if (total_score < 1) {
    ElMessage.warning('总分必须大于 0。')
    return
  }

  manualSaving.value = true
  try {
    await saveManualPaper({
      paperName,
      subjectId: subject_id,
      examCategoryCode: exam_category_code,
      jointExamGroupCode: joint_exam_group_code,
      subjectCode: subject_code,
      policy_version,
      paperType,
      paperStatus,
      durationMinutes: Number(manualForm.durationMinutes || 0),
      totalScore: Number(total_score || 0),
      visibleToStudents: Boolean(manualForm.visibleToStudents),
      publish_class_ids,
      questionIds: question_ids,
      questionScores: question_scores,
    })
    ElMessage.success(`试卷已生成，并已同步发送至 ${publish_class_ids.length} 个班级的学生端`)
    sessionStorage.removeItem(MANUAL_SELECTION_DRAFT_KEY)
    manualDialogVisible.value = false
    resetManualForm()
    await loadPaperOverview()
  } catch (error) {
    ElMessage.error(String(error?.response?.data?.message || error?.message || '手动组卷失败'))
  } finally {
    manualSaving.value = false
  }
}

function handleViewDetail(row) {
  ElMessageBox.alert(
    [
      `试卷 ID：${row.paperId || '-'}`,
      `试卷名称：${row.paperName || '-'}`,
      `题目总数：${row.questionCount}`,
      `总分：${row.totalScore}`,
      `更新时间：${row.updateTime || '-'}`,
      `状态：${paperStatusLabel(row.paperStatus)}`,
    ].join('\n'),
    '试卷详情',
    {
      confirmButtonText: '知道了',
    },
  )
}

async function handleUpdatePaperStatus(row, targetStatus) {
  const paperId = String(row?.paperId || '').trim()
  if (!paperId || !targetStatus) {
    return
  }
  updatingPaperId.value = paperId
  try {
    await updatePaperStatus(paperId, targetStatus)
    ElMessage.success(`试卷已流转到 ${paperStatusLabel(targetStatus)}`)
    await loadPaperOverview()
  } catch (error) {
    ElMessage.error(String(error?.response?.data?.message || error?.message || '试卷状态流转失败'))
  } finally {
    updatingPaperId.value = ''
  }
}

async function handleExport(row, nextFormat = exportFormat.value) {
  const paperId = String(row?.paperId || exportTargetPaperId.value || '').trim()
  if (!paperId) {
    ElMessage.warning('当前试卷缺少 ID，无法导出。')
    return
  }
  exportingPaperId.value = paperId
  try {
    const response = await exportPaper(paperId, { format: nextFormat })
    const payload = unwrapData(response) || {}
    exportTargetPaperId.value = paperId
    exportPaperName.value = String(row?.paperName || exportPaperName.value || paperId).trim() || paperId
    exportFormat.value = String(payload?.format || nextFormat || 'txt').trim() || 'txt'
    exportPreview.value = String(payload?.content || '').trim()
    exportPreviewTitle.value = `${exportPaperName.value} / ${String(exportFormat.value || 'txt').toUpperCase()}`
    exportDialogVisible.value = true
  } catch (error) {
    ElMessage.error(String(error?.response?.data?.message || error?.message || '试卷导出失败'))
  } finally {
    exportingPaperId.value = ''
  }
}

async function handleDelete(row) {
  if (!row.paperId) {
    ElMessage.warning('当前试卷缺少 ID，无法删除。')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确认删除试卷「${row.paperName || row.paperId}」吗？`,
      '删除确认',
      {
        type: 'warning',
        confirmButtonText: '确认删除',
        cancelButtonText: '取消',
      },
    )
  } catch (error) {
    return
  }

  deletingPaperId.value = row.paperId
  try {
    const result = unwrapData(await deletePaper(row.paperId)) || {}
    deletedPaperUndoSnapshotId.value = String(result?.undoSnapshotId || '').trim()
    deletedPaperName.value = String(row.paperName || row.paperId || '').trim()
    ElMessage.success('试卷删除成功，可在 10 分钟内撤销。')
    await loadPaperOverview()
  } catch (error) {
    ElMessage.error(String(error?.response?.data?.message || error?.message || '试卷删除失败'))
  } finally {
    deletingPaperId.value = ''
  }
}

async function handleRestoreDeletedPaper() {
  if (!deletedPaperUndoSnapshotId.value) {
    return
  }
  deletingPaperId.value = deletedPaperName.value || '__restore__'
  try {
    await restoreDeletedPaper(deletedPaperUndoSnapshotId.value)
    ElMessage.success('试卷已恢复。')
    deletedPaperUndoSnapshotId.value = ''
    deletedPaperName.value = ''
    await loadPaperOverview()
  } catch (error) {
    ElMessage.error(String(error?.response?.data?.message || error?.message || '试卷恢复失败'))
  } finally {
    deletingPaperId.value = ''
  }
}

async function handleSaveTemplate() {
  const templateName = String(templateForm.templateName || '').trim()
  const examCategoryCode = String(templateForm.exam_category_code || '').trim()
  const jointExamGroupCode = String(templateForm.joint_exam_group_code || '').trim()
  const subjectCode = String(templateForm.subject_code || '').trim()
  const subjectId = String(templateForm.subject_id || '').trim()
  const typeRules = Array.isArray(templateForm.typeRules)
    ? templateForm.typeRules.map((item) => ({
      type: String(item?.type || '').trim(),
      count: Math.max(1, Number(item?.count || 1)),
      questionScore: Math.max(1, Number(item?.questionScore || 1)),
    }))
    : []
  if (!templateName) {
    ElMessage.warning('请填写模板名称。')
    return
  }
  if (!examCategoryCode || !jointExamGroupCode) {
    ElMessage.warning('请先选择模板所属专业（学科门类 + 联考专业组）。')
    return
  }
  if (!typeRules.length) {
    ElMessage.warning('请至少配置 1 条题型规则。')
    return
  }
  templateSaving.value = true
  try {
    await savePaperTemplate({
      templateId: String(templateForm.templateId || '').trim() || undefined,
      templateName,
      paperType: String(templateForm.paperType || '').trim() || 'chapter',
      subjectId,
      chapter: String(templateForm.chapter || '').trim(),
      difficulty: String(templateForm.difficulty || '').trim() || 'medium',
      totalScore: Math.max(1, Number(templateForm.totalScore || 1)),
      durationMinutes: Math.max(1, Number(templateForm.durationMinutes || 1)),
      examCategoryCode,
      jointExamGroupCode,
      subjectCode,
      policyVersion: POLICY_VERSION,
      typeRules,
    })
    ElMessage.success(templateForm.templateId ? '模板已更新。' : '模板已保存。')
    resetTemplateForm()
    await loadPaperTemplates()
  } catch (error) {
    ElMessage.error(String(error?.response?.data?.message || error?.message || '模板保存失败'))
  } finally {
    templateSaving.value = false
  }
}

async function handleApplyTemplate(row) {
  const templateId = String(row?.templateId || '').trim()
  const templateName = String(row?.templateName || '').trim() || '未命名模板'
  const examCategoryCode = String(row?.examCategoryCode || '').trim()
  const jointExamGroupCode = String(row?.jointExamGroupCode || '').trim()
  const subjectCode = String(row?.subjectCode || '').trim()
  const subjectId = String(row?.subjectId || '').trim()
  const typeRules = Array.isArray(row?.typeRules)
    ? row.typeRules.map((item) => ({
      type: String(item?.type || '').trim(),
      count: Math.max(1, Number(item?.count || 1)),
      questionScore: Math.max(1, Number(item?.questionScore || 1)),
    })).filter((item) => item.type)
    : []

  if (!templateId) {
    ElMessage.warning('当前模板缺少 ID，无法应用生成。')
    return
  }
  if (!examCategoryCode || !jointExamGroupCode) {
    ElMessage.warning('模板缺少专业组范围，无法应用生成。')
    return
  }
  if (!typeRules.length) {
    ElMessage.warning('模板缺少题型规则，无法应用生成。')
    return
  }

  applyingTemplateId.value = templateId
  try {
    const response = await saveAutoPaper({
      paperName: buildTemplatePaperName(templateName),
      subjectId: subjectId || undefined,
      examCategoryCode,
      jointExamGroupCode,
      subjectCode: subjectCode || undefined,
      paperType: String(row?.paperType || 'chapter').trim() || 'chapter',
      paperStatus: 'DRAFT',
      durationMinutes: Math.max(1, Number(row?.durationMinutes || 45)),
      totalScore: Math.max(1, Number(row?.totalScore || 1)),
      visibleToStudents: false,
      chapter: String(row?.chapter || '').trim(),
      difficulty: String(row?.difficulty || '').trim() || 'medium',
      policyVersion: POLICY_VERSION,
      typeRules,
    })
    const result = unwrapData(response) || {}
    const paperId = String(result?.paperId || '').trim()
    ElMessage.success(paperId ? `已根据模板生成试卷，试卷ID：${paperId}` : '已根据模板生成试卷。')
    await loadPaperOverview()
  } catch (error) {
    ElMessage.error(String(error?.response?.data?.message || error?.message || '模板应用生成失败'))
  } finally {
    applyingTemplateId.value = ''
  }
}

async function handleDeleteTemplate(row) {
  const templateId = String(row?.templateId || '').trim()
  if (!templateId) {
    return
  }
  try {
    await ElMessageBox.confirm(
      `确认删除模板「${row?.templateName || templateId}」吗？`,
      '删除模板',
      {
        type: 'warning',
        confirmButtonText: '确认删除',
        cancelButtonText: '取消',
      },
    )
  } catch {
    return
  }
  deletingTemplateId.value = templateId
  try {
    const result = unwrapData(await deletePaperTemplate(templateId)) || {}
    lastDeletedTemplateSnapshotId.value = String(result?.undoSnapshotId || '').trim()
    lastDeletedTemplateName.value = String(row?.templateName || templateId).trim()
    ElMessage.success('模板已删除，可在 10 分钟内恢复。')
    await loadPaperTemplates()
  } catch (error) {
    ElMessage.error(String(error?.response?.data?.message || error?.message || '模板删除失败'))
  } finally {
    deletingTemplateId.value = ''
  }
}

async function handleRestoreDeletedTemplate() {
  if (!lastDeletedTemplateSnapshotId.value) {
    return
  }
  deletingTemplateId.value = lastDeletedTemplateName.value || '__restore__'
  try {
    await restoreDeletedPaperTemplate(lastDeletedTemplateSnapshotId.value)
    ElMessage.success('模板已恢复。')
    lastDeletedTemplateSnapshotId.value = ''
    lastDeletedTemplateName.value = ''
    await loadPaperTemplates()
  } catch (error) {
    ElMessage.error(String(error?.response?.data?.message || error?.message || '模板恢复失败'))
  } finally {
    deletingTemplateId.value = ''
  }
}

onMounted(async () => {
  await Promise.all([
    loadPaperOverview(),
    loadPaperTemplates(),
    loadManualSubjectOptions(),
    fetchProfessionalTree(),
    loadMyClasses(),
  ])
  hydrateManualSelectionDraft()
})

onBeforeUnmount(() => {
  stopAiProgress()
})

watch(
  () => [String(userStore.role || '').trim(), assignedJointGroupCode.value],
  () => {
    if (!professionalTreeRaw.value.length) {
      return
    }
    applyProfessionalScopeOptions(professionalTreeRaw.value)
    selectedQuestions.value = []
  },
)
</script>

<template>
  <section class="papers-page" v-loading="loading">
    <header class="page-header">
      <h3>组卷中心</h3>
      <p>展示试卷业务列表，支持状态流转、导出、删除恢复和模板管理。</p>
    </header>

    <el-alert
      v-if="deletedPaperUndoSnapshotId"
      type="warning"
      show-icon
      :closable="false"
      :title="`试卷「${deletedPaperName || '未命名试卷'}」已删除，可在 10 分钟内恢复。`"
    >
      <template #default>
        <el-button
          type="primary"
          plain
          :loading="deletingPaperId === (deletedPaperName || '__restore__')"
          @click="handleRestoreDeletedPaper"
        >
          撤销删除
        </el-button>
      </template>
    </el-alert>

    <el-row class="action-row" justify="space-between" align="middle">
      <el-col :span="24">
        <div class="action-buttons">
          <el-button type="primary" :icon="Plus" @click="handleManualCreate">
            手动组卷
          </el-button>
          <el-button type="success" :icon="Cpu" @click="handleAiCompose">
            AI 智能组卷
          </el-button>
        </div>
      </el-col>
    </el-row>

    <el-table :data="paperRows" border stripe empty-text="暂无试卷数据">
      <el-table-column prop="paperName" label="试卷名称" min-width="240" />
      <el-table-column prop="questionCount" label="题目总数" width="120" />
      <el-table-column prop="totalScore" label="总分" width="120" />
      <el-table-column prop="updateTime" label="更新时间" min-width="180" />
      <el-table-column prop="paperStatus" label="状态标签" width="130">
        <template #default="scope">
          <el-tag :type="paperStatusTagType(scope.row.paperStatus)" effect="light">
            {{ paperStatusLabel(scope.row.paperStatus) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="300" fixed="right">
        <template #default="scope">
          <el-button link type="primary" @click="handleViewDetail(scope.row)">
            查看详情
          </el-button>
          <el-dropdown trigger="click" @command="(targetStatus) => handleUpdatePaperStatus(scope.row, targetStatus)">
            <el-button
              link
              type="success"
              :loading="updatingPaperId === scope.row.paperId"
            >
              流转状态
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item
                  v-for="action in resolvePaperTransitionActions(scope.row.paperStatus)"
                  :key="`${scope.row.paperId}-${action.targetStatus}`"
                  :command="action.targetStatus"
                >
                  {{ action.label }}
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          <el-button
            link
            type="primary"
            :icon="Download"
            :loading="exportingPaperId === scope.row.paperId"
            @click="handleExport(scope.row)"
          >
            导出
          </el-button>
          <el-button
            link
            type="danger"
            :loading="deletingPaperId === scope.row.paperId"
            @click="handleDelete(scope.row)"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-card class="template-card" shadow="never">
      <template #header>
        <div class="card-header">
          <div>
            <h4>组卷模板</h4>
            <p>保存 AI/规则组卷模板，支持编辑、删除和恢复。</p>
          </div>
          <div class="header-actions">
            <el-button :icon="RefreshRight" :loading="templateLoading" @click="loadPaperTemplates">刷新模板</el-button>
            <el-button v-if="templateForm.templateId" @click="resetTemplateForm">取消编辑</el-button>
            <el-button type="primary" :loading="templateSaving" @click="handleSaveTemplate">
              {{ templateForm.templateId ? '保存模板' : '新增模板' }}
            </el-button>
          </div>
        </div>
      </template>

      <el-alert
        v-if="lastDeletedTemplateSnapshotId"
        class="template-alert"
        type="info"
        show-icon
        :closable="false"
        :title="`模板「${lastDeletedTemplateName || '未命名模板'}」已删除，可在 10 分钟内恢复。`"
      >
        <template #default>
          <el-button
            type="primary"
            plain
            :loading="deletingTemplateId === (lastDeletedTemplateName || '__restore__')"
            @click="handleRestoreDeletedTemplate"
          >
            恢复模板
          </el-button>
        </template>
      </el-alert>

      <div class="manual-grid template-grid">
        <el-form-item label="模板名称">
          <el-input v-model="templateForm.templateName" placeholder="请输入模板名称" />
        </el-form-item>
        <el-form-item label="卷型">
          <el-select v-model="templateForm.paperType" placeholder="请选择卷型">
            <el-option label="章节练" value="chapter" />
            <el-option label="单元测" value="unit" />
            <el-option label="期末考" value="final" />
            <el-option label="simulation" value="simulation" />
          </el-select>
        </el-form-item>
        <el-form-item label="所属专业" class="span-2">
          <el-cascader
            v-model="templateForm.scope_path"
            :options="professionalOptions"
            :props="groupPaperCascaderProps"
            filterable
            clearable
            :teleported="false"
            expand-trigger="hover"
            :show-all-levels="true"
            placeholder="请选择：报考大类 / 联考专业组，可继续下钻到考试科目"
          />
        </el-form-item>
        <el-form-item label="章节/主题">
          <el-input v-model="templateForm.chapter" placeholder="可填写章节、主题或空白" />
        </el-form-item>
        <el-form-item label="难度">
          <el-select v-model="templateForm.difficulty" placeholder="请选择难度">
            <el-option label="简单" value="easy" />
            <el-option label="中等" value="medium" />
            <el-option label="困难" value="hard" />
          </el-select>
        </el-form-item>
        <el-form-item label="总分">
          <el-input-number v-model="templateForm.totalScore" :min="1" :max="200" />
        </el-form-item>
        <el-form-item label="考试时长">
          <el-input-number v-model="templateForm.durationMinutes" :min="1" :max="240" />
        </el-form-item>
      </div>

      <div class="template-rule-head">
        <strong>题型规则</strong>
        <el-button plain @click="addTemplateRule">新增规则</el-button>
      </div>
      <div class="template-rule-list">
        <div
          v-for="(rule, index) in templateForm.typeRules"
          :key="`template-rule-${index}`"
          class="template-rule-row"
        >
          <el-select v-model="rule.type" placeholder="题型">
            <el-option
              v-for="option in PAPER_TEMPLATE_TYPE_OPTIONS"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
          <el-input-number v-model="rule.count" :min="1" :max="50" />
          <el-input-number v-model="rule.questionScore" :min="1" :max="100" />
          <el-button link type="danger" @click="removeTemplateRule(index)">删除</el-button>
        </div>
      </div>

      <div class="template-list-block">
        <div class="template-list-head">
          <strong>已有模板</strong>
          <span>如果数据库中已有模板，会在这里按列表展示。</span>
        </div>
        <div v-loading="templateLoading" class="template-list">
          <el-empty v-if="!paperTemplateRows.length" description="暂无组卷模板" />
          <article
            v-for="row in paperTemplateRows"
            :key="row.templateId"
            class="template-list-item"
          >
            <div class="template-list-item__body">
              <div class="template-list-item__head">
                <h5>{{ row.templateName }}</h5>
                <el-tag size="small" effect="light">{{ resolvePaperTypeLabel(row.paperType) }}</el-tag>
              </div>
              <p class="template-list-item__desc">{{ buildTemplateDescription(row) }}</p>
            </div>
            <div class="template-list-item__actions">
              <el-button
                link
                type="success"
                :loading="applyingTemplateId === row.templateId"
                @click="handleApplyTemplate(row)"
              >
                应用生成
              </el-button>
              <el-button link type="primary" @click="populateTemplateForm(row)">编辑</el-button>
              <el-button
                link
                type="danger"
                :loading="deletingTemplateId === row.templateId"
                @click="handleDeleteTemplate(row)"
              >
                删除
              </el-button>
            </div>
          </article>
        </div>
      </div>
    </el-card>

    <el-dialog
      v-model="manualDialogVisible"
      title="手动组卷表单"
      width="760px"
      class="manual-dialog"
    >
      <el-form label-width="108px" class="manual-form">
        <el-divider content-position="left">基本信息</el-divider>
        <div class="manual-grid">
          <el-form-item label="所属专业" class="span-2">
            <el-cascader
              v-model="manualForm.scope_path"
              :options="professionalOptions"
              :props="manualPaperCascaderProps"
              filterable
              clearable
              :teleported="false"
              expand-trigger="hover"
              :show-all-levels="true"
              :disabled="manualProfessionalLoading"
              placeholder="请选择：学科门类 / 联考专业组，可继续下钻到考试科目"
            />
          </el-form-item>
          <el-form-item label="试卷名称">
            <el-input v-model="manualForm.paperName" placeholder="请输入试卷名称" />
          </el-form-item>
          <el-form-item label="卷型">
            <el-select v-model="manualForm.paperType" placeholder="请选择卷型">
              <el-option label="章节练" value="chapter" />
              <el-option label="单元测" value="unit" />
              <el-option label="期末考" value="final" />
            </el-select>
          </el-form-item>
        </div>

        <el-divider content-position="left">发布与时间</el-divider>
        <div class="manual-grid">
          <el-form-item label="发布对象" class="span-2">
            <el-select
              v-model="manualForm.publish_class_ids"
              multiple
              :collapse-tags="manualForm.publish_class_ids.length > 5"
              :collapse-tags-tooltip="manualForm.publish_class_ids.length > 5"
              :max-collapse-tags="5"
              filterable
              clearable
              placeholder="请选择发布班级"
            >
              <el-option
                v-for="classItem in classList"
                :key="classItem.class_id"
                :label="classItem.class_name"
                :value="classItem.class_id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="考试时长(分钟)">
            <el-input-number v-model="manualForm.durationMinutes" :min="1" :max="240" />
          </el-form-item>
          <el-form-item label="试卷状态">
            <el-select v-model="manualForm.paperStatus" placeholder="请选择试卷状态">
              <el-option label="草稿" value="DRAFT" />
              <el-option label="待审核" value="REVIEW_PENDING" />
              <el-option label="已发布" value="PUBLISHED" />
              <el-option label="已下架" value="OFFLINE" />
            </el-select>
          </el-form-item>
          <el-form-item label="学生可见">
            <el-switch v-model="manualForm.visibleToStudents" />
          </el-form-item>
        </div>

        <el-divider content-position="left">题目配置</el-divider>
        <div class="manual-grid">
          <el-form-item label="难度">
            <el-select v-model="manualForm.difficulty" placeholder="请选择难度">
              <el-option label="简单" value="easy" />
              <el-option label="中等" value="medium" />
              <el-option label="困难" value="hard" />
            </el-select>
          </el-form-item>
          <el-form-item label="总分">
            <el-input :model-value="String(totalScore)" readonly />
          </el-form-item>
          <el-form-item label="题目选择" class="span-2">
            <div class="question-selection-panel">
              <el-alert
                class="question-selection-alert"
                type="info"
                :closable="false"
                show-icon
                :title="`已选择 ${selectedQuestionCount} 道题目，点击【选题中心】进行增删`"
              />
              <el-button type="primary" plain @click="openQuestionSelectionDrawer">
                选题中心
              </el-button>
              <el-tag class="count-tag" type="success" effect="light">
                自动总分 {{ totalScore }}
              </el-tag>
            </div>
          </el-form-item>
        </div>
      </el-form>

      <el-card class="question-list-card" shadow="never">
        <template #header>
          <div class="question-list-header">
            <strong>已选题目预览</strong>
            <span class="helper-text">可直接修改单题分值，系统将自动汇总总分。</span>
          </div>
        </template>

        <el-empty
          v-if="!selectedQuestions.length"
          description="尚未选择题目"
        />

        <el-table
          v-else
          :data="selectedQuestions"
          border
          max-height="300"
          empty-text="暂无题目"
        >
          <el-table-column prop="stem" label="题干预览" min-width="300" show-overflow-tooltip />
          <el-table-column label="题型" width="120">
            <template #default="scope">
              {{ questionTypeLabel(scope.row.type) }}
            </template>
          </el-table-column>
          <el-table-column label="分值" width="160">
            <template #default="scope">
              <el-input-number v-model="scope.row.score" :min="1" :step="1" />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100" fixed="right">
            <template #default="scope">
              <el-button link type="danger" @click="handleRemoveSelectedQuestion(scope.row.id)">
                移除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <template #footer>
        <div class="manual-footer">
          <el-button @click="manualDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="manualSaving" @click="handleManualSubmit">
            生成手动试卷
          </el-button>
        </div>
      </template>
    </el-dialog>

    <el-dialog
      v-model="exportDialogVisible"
      title="试卷导出预览"
      width="760px"
    >
      <div class="export-toolbar">
        <el-select v-model="exportFormat" placeholder="导出格式" style="width: 180px">
          <el-option
            v-for="item in PAPER_EXPORT_FORMAT_OPTIONS"
            :key="item.value"
            :label="item.label"
            :value="item.value"
          />
        </el-select>
        <el-button
          type="primary"
          :icon="Download"
          :loading="exportingPaperId === exportTargetPaperId"
          @click="handleExport({ paperId: exportTargetPaperId, paperName: exportPaperName }, exportFormat)"
        >
          刷新预览
        </el-button>
      </div>
      <el-alert
        class="export-alert"
        type="info"
        :closable="false"
        :title="exportPreviewTitle || '导出结果'"
      />
      <pre class="export-preview">{{ exportPreview || '当前暂无导出内容。' }}</pre>
      <template #footer>
        <el-button @click="exportDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <QuestionSelectionDrawer
      v-model="questionSelectionDrawerVisible"
      :initial-rows="selectedQuestions"
      :exam-category-code="manualForm.exam_category_code"
      :joint-exam-group-code="manualForm.joint_exam_group_code"
      :subject-code="manualForm.subject_code"
      :target-knowledge-ids="manualTargetKnowledgeIds"
      :target-knowledge-map="manualTargetKnowledgeMap"
      :target-weight-map="manualTargetWeightMap"
      @confirm="handleQuestionSelectionConfirm"
    />

    <AiGenerationDialog
      v-model="aiDialogVisible"
      :generating="aiGenerating"
      :generation-progress="aiGenerationProgress"
      :professional-options="professionalOptions"
      @start-generate="handleAiGenerate"
    />
  </section>
</template>

<style scoped>
.papers-page {
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

.action-buttons {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.template-card {
  border: 1px solid var(--qb-primary-soft-border);
  background: linear-gradient(180deg, var(--qb-bg-card), rgba(255, 255, 255, 0.96));
}

.card-header,
.header-actions,
.template-rule-head,
.export-toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
}

.card-header {
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
}

.card-header h4,
.card-header p {
  margin: 0;
}

.card-header p {
  margin-top: 4px;
  color: var(--qb-text-subtle-7);
}

.header-actions {
  flex-wrap: wrap;
}

.template-alert,
.export-alert {
  margin-bottom: 12px;
}

.template-grid {
  margin-bottom: 12px;
}

.template-rule-head {
  justify-content: space-between;
  margin: 12px 0 10px;
}

.template-rule-list {
  display: grid;
  gap: 10px;
  margin-bottom: 12px;
}

.template-list-block {
  display: grid;
  gap: 12px;
  margin-top: 8px;
}

.template-list-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
}

.template-list-head strong {
  font-size: 16px;
}

.template-list-head span {
  color: var(--qb-text-subtle-7);
  font-size: 13px;
}

.template-list {
  display: grid;
  gap: 10px;
}

.template-list-item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 16px;
  border: 1px solid var(--qb-primary-soft-border);
  border-radius: 16px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(244, 248, 255, 0.95));
}

.template-list-item__body {
  min-width: 0;
  flex: 1;
}

.template-list-item__head {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.template-list-item__head h5 {
  margin: 0;
  font-size: 15px;
  line-height: 1.4;
}

.template-list-item__desc {
  margin: 8px 0 0;
  color: var(--qb-text-subtle-7);
  line-height: 1.6;
}

.template-list-item__actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
  flex-shrink: 0;
}

.template-rule-row {
  display: grid;
  grid-template-columns: minmax(160px, 1fr) 120px 120px auto;
  gap: 10px;
  align-items: center;
}

.template-table {
  margin-top: 8px;
}

.rule-preview {
  white-space: normal;
  line-height: 1.5;
}

.export-toolbar {
  justify-content: space-between;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.export-preview {
  min-height: 240px;
  max-height: 420px;
  overflow: auto;
  padding: 14px;
  border-radius: 14px;
  background: var(--qb-text-heading);
  color: var(--qb-bg-card);
  line-height: 1.6;
  white-space: pre-wrap;
}

.manual-form {
  margin-top: 0;
}

.manual-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  column-gap: 12px;
}

.span-2 {
  grid-column: 1 / -1;
}

.question-selection-panel {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.question-selection-alert {
  flex: 1;
  min-width: 220px;
}

.count-tag {
  margin-left: 0;
}

.question-list-card {
  margin-top: 6px;
  border: 1px solid var(--qb-primary-soft-border);
  background: linear-gradient(180deg, var(--qb-bg-card), var(--qb-primary-soft-bg));
}

.question-list-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.helper-text {
  color: var(--qb-text-subtle-8);
  font-size: 12px;
}

.manual-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 8px 0 0;
  border-top: 1px solid var(--qb-primary-soft-border);
}

.manual-dialog :deep(.el-dialog__header) {
  border-bottom: 1px solid var(--qb-primary-soft-border);
  margin-right: 0;
  padding-bottom: 10px;
}

.manual-dialog :deep(.el-dialog__body) {
  padding-top: 10px;
  padding-bottom: 10px;
}

.manual-form :deep(.el-divider) {
  margin: 10px 0;
}

.manual-form :deep(.el-divider__text) {
  color: var(--el-color-primary);
  font-weight: 600;
  background: linear-gradient(90deg, var(--qb-primary-soft-bg), var(--qb-bg-card));
  border-radius: 999px;
  padding: 2px 10px;
}

.manual-form :deep(.el-form-item) {
  margin-bottom: 10px;
}

@media (max-width: 900px) {
  .manual-grid {
    grid-template-columns: 1fr;
  }

  .template-rule-row {
    grid-template-columns: 1fr;
  }

  .span-2 {
    grid-column: auto;
  }
}

</style>
