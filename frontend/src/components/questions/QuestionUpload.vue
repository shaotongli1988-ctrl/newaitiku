<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from '@/ui/feedback'
import { UploadFilled } from '@/ui/icons'
import QuestionBatchTaskCenter from './QuestionBatchTaskCenter.vue'
import {
  batchCreateQuestions,
  createQuestion,
  getKnowledge,
  getTask,
  knowledgeTreeV2,
  parseQuestionBatchFromWordFile,
  professionalTree,
  templateImportExample,
} from '../../api/services/questionBank'
import {
  buildProfessionalScopeOptions as createProfessionalScopeOptions,
  buildScopeKey,
  resolveFirstAvailableProfessionalScopePath,
} from '../../utils/professionalScope'
import { buildKnowledgeSelectorState } from '../../utils/knowledgeTree'
import { useUserStore } from '../../stores/userStore'

const emit = defineEmits(['created'])

const formRef = ref(null)
const submitting = ref(false)
const uploadMode = ref('single')
const loadingTree = ref(false)
const loadingKnowledgeTree = ref(false)
const professionalOptions = ref([])
const professionalTreeRaw = ref([])
const knowledgeCascaderOptions = ref([])
const knowledgeNodeLabelMap = ref({})
const knowledgePathMap = ref({})
const knowledgeChapterCodeMap = ref({})
const knowledgePointCodeMap = ref({})
const l5SearchOptions = ref([])
const subjectScopeMap = ref({})
const batchParsing = ref(false)
const batchCreating = ref(false)
const batchRows = ref([])
const batchErrors = ref([])
const batchTaskId = ref('')
const batchTaskStatus = ref('')
const batchTaskProgress = ref(0)
const batchTaskSummary = ref('')
const batchFileName = ref('')
const batchParserReport = ref({})
const templateExampleVisible = ref(false)
const templateExampleContent = ref('')
const templateExampleFileName = ref('question-batch-template.txt')
const loadingTemplateExample = ref(false)
const taskCenterRef = ref(null)
const userStore = useUserStore()

const objectiveTypes = new Set(['single_choice', 'multiple_choice', 'judge'])
const batchUploadNotes = [
  '推荐使用 DOCX；公式请尽量使用可编辑的 Word 公式或文本，不要直接贴截图。',
  '每道题建议按【题型】【题干】【选项】【答案】【解析】【知识点】组织，题与题之间用 --- 分隔。',
  '英文长文本、公式推导、解析说明都可以换行续写，系统会尽量保留在同一题目或同一字段内。',
  '客观题选项既支持 A.内容|B.内容，也支持换行续写长选项。',
  '数学公式建议写成 x^2、lim、sin、积分上下限等线性形式；系统会兼容常见上标/下标字符。',
  '化学式和反应式建议写成 H2SO4、Ca(OH)2、2H2 + O2 -> 2H2O；截图中的公式/结构式仅做 OCR 兜底识别。',
  '如果部署机本地安装了 pix2tex，系统会优先尝试数学公式图片识别；未安装时自动回退到 Tesseract OCR。',
]

const formModel = reactive({
  title: '',
  content: '',
  type: 'single_choice',
  knowledgePath: [],
  answer: '',
  analysis: '',
  scopePath: [],
  pointSearchKeyword: '',
  options: [
    { key: 'A', content: '' },
    { key: 'B', content: '' },
  ],
})

function createEmptyBatchRow() {
  return {
    previewId: '',
    title: '',
    content: '',
    type: 'single_choice',
    options: [],
    answer: '',
    analysis: '',
    scopePath: [],
    knowledgePath: [],
    chapterCode: '',
    pointCode: '',
    moduleCode: '',
    pathLabel: '',
    confidence: 0,
    manualReviewRequired: false,
    reviewMessage: '',
    createStatus: 'pending',
    createMessage: '',
    createdQuestionId: '',
  }
}

const rules = {
  title: [{ required: true, message: '请输入题目标题', trigger: 'blur' }],
  content: [{ required: true, message: '请输入题干', trigger: 'blur' }],
  type: [{ required: true, message: '请选择题型', trigger: 'change' }],
  knowledgePath: [
    {
      validator: (_, value, callback) => {
        if (Array.isArray(value) && value.length > 0) {
          callback()
          return
        }
        callback(new Error('请从知识树中选择知识点'))
      },
      trigger: 'change',
    },
  ],
  answer: [{ required: true, message: '请输入标准答案', trigger: 'blur' }],
  scopePath: [
    {
      validator: (_, value, callback) => {
        if (Array.isArray(value) && value.length === 3) {
          callback()
          return
        }
        callback(new Error('请按“学科门类 -> 联考组 -> 科目”完成级联选择'))
      },
      trigger: 'change',
    },
  ],
}

const cascaderProps = {
  value: 'code',
  label: 'name',
  children: 'children',
  emitPath: true,
  checkStrictly: false,
}
const knowledgeCascaderProps = {
  value: 'value',
  label: 'label',
  children: 'children',
  emitPath: true,
  checkStrictly: false,
}

const isObjectiveQuestion = computed(() => objectiveTypes.has(String(formModel.type || '').trim()))
const selectedKnowledgePointId = computed(() => {
  const path = Array.isArray(formModel.knowledgePath) ? formModel.knowledgePath : []
  return String(path[path.length - 1] || '').trim()
})
const selectedSubjectCode = computed(() => {
  const path = Array.isArray(formModel.scopePath) ? formModel.scopePath : []
  return String(path[path.length - 1] || '').trim()
})
const assignedJointGroupCode = computed(() =>
  String(userStore.assigned_joint_group_code || userStore.assignedJointGroupCode || userStore.jointExamGroupCode || '').trim(),
)
const isScopeLocked = computed(() =>
  String(userStore.role || '').trim() !== 'super_admin' && Boolean(assignedJointGroupCode.value),
)

function parseEnvelopeData(response) {
  if (response && typeof response === 'object' && 'data' in response) {
    return response.data
  }
  return response
}

function applyProfessionalScopeOptions(treePayload) {
  const { options, scopeMetaMap } = createProfessionalScopeOptions(treePayload, {
    assignedJointGroupCode: isScopeLocked.value ? assignedJointGroupCode.value : '',
  })
  subjectScopeMap.value = scopeMetaMap
  professionalOptions.value = options

  const currentScopeValid = Boolean(subjectScopeMap.value[buildScopeKey(formModel.scopePath)])
  if (!isScopeLocked.value) {
    if (Array.isArray(formModel.scopePath) && formModel.scopePath.length === 3 && !currentScopeValid) {
      formModel.scopePath = []
    }
    return
  }

  if (!currentScopeValid) {
    formModel.scopePath = resolveFirstAvailableProfessionalScopePath(
      professionalOptions.value,
      subjectScopeMap.value,
    )
  }
}

async function fetchProfessionalTree() {
  loadingTree.value = true
  try {
    const response = await professionalTree()
    professionalTreeRaw.value = parseEnvelopeData(response) || []
    applyProfessionalScopeOptions(professionalTreeRaw.value)
  } catch (error) {
    professionalTreeRaw.value = []
    professionalOptions.value = []
    subjectScopeMap.value = {}
    ElMessage.error(error?.response?.data?.message || error?.message || '专业层级字典加载失败')
  } finally {
    loadingTree.value = false
  }
}

function normalizeKnowledgeTreeOptions(treePayload) {
  return buildKnowledgeSelectorState(treePayload)
}

async function loadKnowledgeTreeOptions(subjectCode = '', { force = false } = {}) {
  const normalizedSubjectCode = String(subjectCode || '').trim()
  if (!normalizedSubjectCode) {
    knowledgeCascaderOptions.value = []
    knowledgeNodeLabelMap.value = {}
    knowledgePathMap.value = {}
    knowledgeChapterCodeMap.value = {}
    knowledgePointCodeMap.value = {}
    l5SearchOptions.value = []
    formModel.pointSearchKeyword = ''
    return
  }
  if (!force && knowledgeCascaderOptions.value.length) {
    return
  }
  loadingKnowledgeTree.value = true
  try {
    const response = await knowledgeTreeV2({
      status: 'ENABLED',
      subject_code: normalizedSubjectCode,
    })
    const treePayload = parseEnvelopeData(response) || {}
    const selectorState = normalizeKnowledgeTreeOptions(treePayload)
    knowledgeCascaderOptions.value = Array.isArray(selectorState.options) ? selectorState.options : []
    knowledgePathMap.value = selectorState.pathMap || {}
    knowledgeNodeLabelMap.value = selectorState.labelMap || {}
    knowledgeChapterCodeMap.value = selectorState.chapterCodeMap || {}
    knowledgePointCodeMap.value = selectorState.pointCodeMap || {}
    l5SearchOptions.value = Array.isArray(selectorState.searchOptions) ? selectorState.searchOptions : []
  } catch (error) {
    knowledgeCascaderOptions.value = []
    knowledgeNodeLabelMap.value = {}
    knowledgePathMap.value = {}
    knowledgeChapterCodeMap.value = {}
    knowledgePointCodeMap.value = {}
    l5SearchOptions.value = []
    ElMessage.error(error?.response?.data?.message || error?.message || '知识树加载失败')
  } finally {
    loadingKnowledgeTree.value = false
  }
}

function normalizeBatchPreviewRows(items = []) {
  const rows = Array.isArray(items) ? items : []
  return rows.map((item, index) => ({
    ...createEmptyBatchRow(),
    previewId: String(item?.preview_id || item?.previewId || `preview-${index + 1}`),
    title: String(item?.title || '').trim(),
    content: String(item?.content || '').trim(),
    type: String(item?.type || 'single_choice').trim() || 'single_choice',
    options: Array.isArray(item?.options) ? item.options : [],
    answer: String(item?.answer || '').trim(),
    analysis: String(item?.analysis || '').trim(),
    scopePath: Array.isArray(item?.scope_path)
      ? item.scope_path.map((value) => String(value || '').trim()).filter((value) => value)
      : [],
    knowledgePath: Array.isArray(item?.knowledge_path)
      ? item.knowledge_path.map((value) => String(value || '').trim()).filter((value) => value)
      : [],
    chapterCode: String(item?.chapter_code || '').trim(),
    pointCode: String(item?.point_code || '').trim(),
    moduleCode: String(item?.module_code || '').trim(),
    pathLabel: String(item?.path_label || '').trim(),
    confidence: Number(item?.confidence || 0),
    manualReviewRequired: Boolean(item?.manual_review_required || item?.manualReviewRequired),
    reviewMessage: String(item?.review_message || item?.reviewMessage || '').trim(),
  }))
}

function updateBatchRows(payload = {}) {
  batchRows.value = normalizeBatchPreviewRows(payload?.items)
  batchErrors.value = Array.isArray(payload?.errors) ? payload.errors : []
  batchParserReport.value = payload?.parserReport && typeof payload.parserReport === 'object' ? payload.parserReport : {}
}

const batchParserSummary = computed(() => {
  const report = batchParserReport.value || {}
  const extractMethod = String(report?.extractMethod || '').trim()
  const formulaEngines = Array.isArray(report?.imageFormulaOcrEngines) ? report.imageFormulaOcrEngines.filter(Boolean) : []
  const chemicalEngines = Array.isArray(report?.imageChemicalOcrEngines) ? report.imageChemicalOcrEngines.filter(Boolean) : []
  const parts = []
  if (extractMethod) {
    parts.push(`提取链路：${extractMethod}`)
  }
  if (formulaEngines.length) {
    parts.push(`公式引擎：${formulaEngines.join(' / ')}`)
  }
  if (chemicalEngines.length) {
    parts.push(`化学引擎：${chemicalEngines.join(' / ')}`)
  }
  return parts.join('；')
})

async function pollBatchTaskUntilDone(taskId) {
  const normalizedTaskId = String(taskId || '').trim()
  if (!normalizedTaskId) {
    return
  }
  batchTaskId.value = normalizedTaskId
  for (let attempt = 0; attempt < 12; attempt += 1) {
    const response = await getTask(normalizedTaskId)
    const taskPayload = parseEnvelopeData(response) || {}
    const taskExt = taskPayload?.extJson && typeof taskPayload.extJson === 'object'
      ? taskPayload.extJson
      : (() => {
        if (typeof taskPayload?.extJson !== 'string') {
          return {}
        }
        try {
          const parsed = JSON.parse(taskPayload.extJson)
          return parsed && typeof parsed === 'object' ? parsed : {}
        } catch (error) {
          return {}
        }
      })()
    const taskStatus = String(taskPayload?.status || '').trim()
    batchTaskStatus.value = taskStatus
    batchTaskProgress.value = Number(taskPayload?.progress || 0)
    batchTaskSummary.value = String(taskExt?.resultSummary || '').trim()
    if (taskStatus === 'COMPLETED') {
      updateBatchRows(taskExt?.result || {})
      taskCenterRef.value?.reload?.()
      return
    }
    if (taskStatus === 'FAILED' || taskStatus === 'CANCELLED') {
      throw new Error(String(taskExt?.errorMessage || taskPayload?.message || '批量解析任务执行失败'))
    }
    await new Promise((resolve) => window.setTimeout(resolve, 800))
  }
  throw new Error('批量解析任务超时，请稍后重试。')
}

function restoreBatchTaskResult(row) {
  const result = row?.result && typeof row.result === 'object' ? row.result : {}
  updateBatchRows(result)
  batchTaskId.value = String(row?.taskId || '').trim()
  batchTaskStatus.value = String(row?.status || '').trim()
  batchTaskProgress.value = Number(row?.progress || 0)
  batchTaskSummary.value = String(row?.summary || row?.resultSummary || '').trim()
  ElMessage.success('已恢复该批次解析结果到当前预览区。')
}

async function ensureBatchKnowledgeOptions(row) {
  const subjectCode = String(row?.scopePath?.[2] || '').trim()
  if (!subjectCode) {
    return
  }
  await loadKnowledgeTreeOptions(subjectCode, { force: true })
}

async function handleBatchScopePathChange(row, nextPath) {
  row.scopePath = Array.isArray(nextPath)
    ? nextPath.map((item) => String(item || '').trim()).filter((item) => item)
    : []
  row.knowledgePath = []
  row.chapterCode = ''
  row.pointCode = ''
  row.moduleCode = ''
  row.pathLabel = ''
  row.manualReviewRequired = true
  row.reviewMessage = '请重新选择 L5 标签'
  await ensureBatchKnowledgeOptions(row)
}

async function handleBatchKnowledgePathChange(row, nextPath) {
  const knowledgePath = Array.isArray(nextPath)
    ? nextPath.map((item) => String(item || '').trim()).filter((item) => item)
    : []
  row.knowledgePath = knowledgePath
  const scopeKey = buildScopeKey(row.scopePath)
  const scopeMeta = subjectScopeMap.value[scopeKey]
  if (!scopeMeta) {
    row.reviewMessage = '请先完成 学科门类 / 联考组 / 科目 选择。'
    return
  }
  const knowledgeId = String(knowledgePath[knowledgePath.length - 1] || '').trim()
  if (!knowledgeId) {
    row.reviewMessage = '请至少选择到 L5 知识点。'
    return
  }
  row.chapterCode = String(knowledgeChapterCodeMap.value[knowledgePath[0] || ''] || '').trim()
  row.pointCode = String(knowledgePointCodeMap.value[knowledgeId] || '').trim()
  row.moduleCode = await resolveSelectedKnowledgeModuleCode(knowledgeId)
  row.pathLabel = knowledgePath
    .map((item) => String(knowledgeNodeLabelMap.value[item] || item))
    .join(' / ')
  row.manualReviewRequired = false
  row.reviewMessage = ''
}

async function resolveSelectedKnowledgeModuleCode(knowledgeId) {
  const normalizedKnowledgeId = String(knowledgeId || '').trim()
  if (!normalizedKnowledgeId) {
    return ''
  }
  try {
    const response = await getKnowledge(normalizedKnowledgeId)
    const knowledgeData = parseEnvelopeData(response) || {}
    let extJson = {}
    if (knowledgeData?.extJson && typeof knowledgeData.extJson === 'object') {
      extJson = knowledgeData.extJson
    } else if (typeof knowledgeData?.extJson === 'string') {
      try {
        const parsed = JSON.parse(knowledgeData.extJson)
        extJson = parsed && typeof parsed === 'object' ? parsed : {}
      } catch (error) {
        extJson = {}
      }
    }
    const extModuleCode = String(extJson?.moduleCode || extJson?.module_code || '').trim()
    return extModuleCode || normalizedKnowledgeId
  } catch (error) {
    return normalizedKnowledgeId
  }
}

function queryL5KnowledgeSuggestions(queryString, callback) {
  const keyword = String(queryString || '').trim().toLowerCase()
  const candidates = l5SearchOptions.value.filter((item) => {
    const value = String(item?.value || '').toLowerCase()
    const pathLabel = String(item?.pathLabel || '').toLowerCase()
    if (!keyword) {
      return true
    }
    return value.includes(keyword) || pathLabel.includes(keyword)
  })
  callback(candidates.slice(0, 30))
}

function handleL5KnowledgeSelect(item) {
  const pathIds = Array.isArray(item?.pathIds) ? item.pathIds.filter((value) => String(value || '').trim()) : []
  if (!pathIds.length) {
    return
  }
  formModel.knowledgePath = pathIds
  formModel.pointSearchKeyword = String(item?.pathLabel || item?.value || '').trim()
}

function normalizeOptionsPayload() {
  if (!isObjectiveQuestion.value) {
    return []
  }
  const normalizedOptions = formModel.options
    .map((item) => ({
      key: String(item?.key || '').trim(),
      content: String(item?.content || '').trim(),
    }))
    .filter((item) => item.key && item.content)
  return normalizedOptions
}

function addOptionRow() {
  const nextIndex = formModel.options.length + 1
  const fallbackKey = String.fromCharCode(64 + Math.min(nextIndex, 26))
  formModel.options.push({ key: fallbackKey, content: '' })
}

function removeOptionRow(index) {
  if (formModel.options.length <= 2) {
    ElMessage.warning('客观题至少保留 2 个选项。')
    return
  }
  formModel.options.splice(index, 1)
}

function resetForm() {
  formModel.title = ''
  formModel.content = ''
  formModel.type = 'single_choice'
  formModel.knowledgePath = []
  formModel.pointSearchKeyword = ''
  formModel.answer = ''
  formModel.analysis = ''
  formModel.scopePath = []
  formModel.options = [
    { key: 'A', content: '' },
    { key: 'B', content: '' },
  ]
}

function resetBatchState() {
  batchRows.value = []
  batchErrors.value = []
  batchTaskId.value = ''
  batchFileName.value = ''
  batchTaskStatus.value = ''
  batchTaskProgress.value = 0
  batchTaskSummary.value = ''
  batchParserReport.value = {}
}

async function ensureTemplateExampleLoaded() {
  if (templateExampleContent.value) {
    return
  }
  loadingTemplateExample.value = true
  try {
    const response = await templateImportExample()
    const payload = parseEnvelopeData(response) || {}
    templateExampleContent.value = String(payload?.content || '').trim()
    templateExampleFileName.value = String(payload?.fileName || 'question-batch-template.txt').trim() || 'question-batch-template.txt'
  } catch (error) {
    throw new Error(String(error?.response?.data?.message || error?.message || '加载上传模板失败'))
  } finally {
    loadingTemplateExample.value = false
  }
}

async function handlePreviewTemplateExample() {
  try {
    await ensureTemplateExampleLoaded()
    templateExampleVisible.value = !templateExampleVisible.value
  } catch (error) {
    ElMessage.error(String(error?.message || '加载上传模板失败'))
  }
}

async function handleDownloadTemplateExample() {
  try {
    await ensureTemplateExampleLoaded()
    const blob = new Blob([templateExampleContent.value], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = templateExampleFileName.value
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    ElMessage.success('上传模板已下载。')
  } catch (error) {
    ElMessage.error(String(error?.message || '下载上传模板失败'))
  }
}

async function handleBatchFileChange(uploadFile) {
  const file = uploadFile?.raw || uploadFile
  const normalizedFileName = String(file?.name || '').toLowerCase()
  if (!file) {
    return
  }
  if (!normalizedFileName.endsWith('.doc') && !normalizedFileName.endsWith('.docx') && !normalizedFileName.endsWith('.txt')) {
    ElMessage.warning('批量上传仅支持 DOC / DOCX / TXT 文件。')
    return
  }
  const scopeKey = buildScopeKey(formModel.scopePath)
  const scopeMeta = subjectScopeMap.value[scopeKey]
  if (!scopeMeta) {
    ElMessage.warning('请先选择专业属性后再进行批量上传。')
    return
  }
  batchParsing.value = true
  batchFileName.value = String(file?.name || '').trim()
  resetBatchState()
  try {
    const payload = await parseQuestionBatchFromWordFile({
      file,
      exam_category_code: scopeMeta.categoryCode,
      joint_exam_group_code: scopeMeta.groupCode,
      subject_code: scopeMeta.subjectCode,
    })
    if (payload?.deferred && payload?.taskId) {
      await pollBatchTaskUntilDone(payload.taskId)
      ElMessage.success('批量题目解析完成，请确认后入库。')
      return
    }
    updateBatchRows(payload || {})
    batchTaskStatus.value = 'COMPLETED'
    batchTaskProgress.value = 100
    batchTaskSummary.value = `本次同步解析完成，共识别 ${batchRows.value.length} 道题目。`
    taskCenterRef.value?.reload?.()
    ElMessage.success(`已识别 ${batchRows.value.length} 道题目，请确认标签后入库。`)
  } catch (error) {
    resetBatchState()
    ElMessage.error(String(error?.response?.data?.message || error?.message || '批量解析失败'))
  } finally {
    batchParsing.value = false
  }
}

async function handleBatchCreate() {
  if (!batchRows.value.length) {
    ElMessage.warning('请先上传并解析题目。')
    return
  }
  const payloadItems = batchRows.value
    .filter((row) => Array.isArray(row.scopePath) && row.scopePath.length === 3)
    .filter((row) => Array.isArray(row.knowledgePath) && row.knowledgePath.length > 0)
    .map((row) => {
      const scopeKey = buildScopeKey(row.scopePath)
      const scopeMeta = subjectScopeMap.value[scopeKey] || {}
      const knowledgeId = String(row.knowledgePath[row.knowledgePath.length - 1] || '').trim()
      return {
        title: String(row.title || '').trim() || String(row.content || '').trim().slice(0, 60),
        content: String(row.content || '').trim(),
        type: String(row.type || 'single_choice').trim() || 'single_choice',
        exam_category_code: String(scopeMeta.categoryCode || row.scopePath[0] || '').trim(),
        joint_exam_group_code: String(scopeMeta.groupCode || row.scopePath[1] || '').trim(),
        subject_code: String(scopeMeta.subjectCode || row.scopePath[2] || '').trim(),
        subject_type: String(scopeMeta.subjectType || scopeMeta.subjectSlot || '').trim(),
        module_code: String(row.moduleCode || '').trim(),
        knowledge_points: [knowledgeId],
        options: Array.isArray(row.options) ? row.options : [],
        answer: String(row.answer || '').trim(),
        analysis: String(row.analysis || '').trim(),
        source_type: 'word_batch_parse',
        status: 'DRAFT',
        ext_json: {
          chapter_code: String(row.chapterCode || '').trim(),
          point_code: String(row.pointCode || '').trim(),
          path_label: String(row.pathLabel || '').trim(),
          batch_preview_id: String(row.previewId || '').trim(),
        },
      }
    })
    .filter((item) => item.content && item.answer && item.knowledge_points.length)

  if (!payloadItems.length) {
    ElMessage.warning('当前没有通过校验的题目，请先修正标签和答案。')
    return
  }

  batchCreating.value = true
  try {
    const response = await batchCreateQuestions({
      items: payloadItems,
      sourceTaskId: String(batchTaskId.value || '').trim(),
    })
    const result = parseEnvelopeData(response) || {}
    const createdItems = Array.isArray(result?.items) ? result.items : []
    const failureRows = Array.isArray(result?.failures) ? result.failures : []
    const createdByPreviewId = {}
    createdItems.forEach((item) => {
      let extJson = item?.extJson
      if (typeof extJson === 'string') {
        try {
          extJson = JSON.parse(extJson)
        } catch (error) {
          extJson = {}
        }
      }
      const previewId = String(extJson?.batch_preview_id || '').trim()
      if (previewId) {
        createdByPreviewId[previewId] = item
      }
    })
    const failureByPreviewId = {}
    failureRows.forEach((item) => {
      const previewId = String(item?.previewId || '').trim()
      if (previewId) {
        failureByPreviewId[previewId] = item
      }
    })
    batchRows.value.forEach((row) => {
      const created = createdByPreviewId[row.previewId]
      const failed = failureByPreviewId[row.previewId]
      if (created) {
        row.createStatus = 'success'
        row.createMessage = '已入库'
        row.createdQuestionId = String(created?.id || '').trim()
        return
      }
      if (failed) {
        row.createStatus = 'error'
        row.createMessage = String(failed?.message || '入库失败')
        return
      }
      row.createStatus = 'pending'
      row.createMessage = ''
      row.createdQuestionId = ''
    })
    const rollbackMessage = String(result?.rollbackStrategy?.message || '').trim()
    taskCenterRef.value?.reload?.()
    ElMessage.success(`批量入库完成：成功 ${Number(result?.createdCount || 0)} 道题。${rollbackMessage ? ` ${rollbackMessage}` : ''}`)
    emit('created', result)
  } catch (error) {
    ElMessage.error(String(error?.response?.data?.message || error?.message || '批量入库失败'))
  } finally {
    batchCreating.value = false
  }
}

async function handleSubmit() {
  if (!formRef.value) {
    return
  }

  try {
    await formRef.value.validate()
  } catch (error) {
    return
  }

  const scopeKey = buildScopeKey(formModel.scopePath)
  const scopeMeta = subjectScopeMap.value[scopeKey]
  if (!scopeMeta) {
    ElMessage.error('当前科目级联路径无效，请重新选择。')
    return
  }

  const optionsPayload = normalizeOptionsPayload()
  if (isObjectiveQuestion.value && optionsPayload.length < 2) {
    ElMessage.warning('客观题至少需要 2 个有效选项。')
    return
  }
  if (!selectedKnowledgePointId.value) {
    ElMessage.warning('请在知识树中选择知识点。')
    return
  }
  const knowledgePath = Array.isArray(formModel.knowledgePath) ? formModel.knowledgePath : []
  const chapterNodeId = String(knowledgePath[0] || '').trim()
  const chapterCode = String(knowledgeChapterCodeMap.value[chapterNodeId] || '').trim()
  const pointCode = String(knowledgePointCodeMap.value[selectedKnowledgePointId.value] || '').trim()
  if (!pointCode) {
    ElMessage.warning('请在 L5 层级选择具体考点后再提交。')
    return
  }
  const selectedModuleCode = await resolveSelectedKnowledgeModuleCode(selectedKnowledgePointId.value)

  const payload = {
    title: String(formModel.title || '').trim(),
    content: String(formModel.content || '').trim(),
    type: String(formModel.type || '').trim(),
    exam_category_code: scopeMeta.categoryCode,
    joint_exam_group_code: scopeMeta.groupCode,
    subject_code: scopeMeta.subjectCode,
    subject_type: scopeMeta.subjectType || scopeMeta.subjectSlot || '',
    module_code: selectedModuleCode,
    knowledge_points: [selectedKnowledgePointId.value],
    ext_json: {
      chapter_code: chapterCode,
      point_code: pointCode,
    },
    options: optionsPayload,
    answer: String(formModel.answer || '').trim(),
    analysis: String(formModel.analysis || '').trim(),
    source_type: 'manual',
    status: 'DRAFT',
  }

  submitting.value = true
  try {
    const response = await createQuestion(payload)
    const createdData = parseEnvelopeData(response) || {}
    ElMessage.success(`题目创建成功：${String(createdData.id || '') || '已创建'}`)
    emit('created', createdData)
    resetForm()
    formRef.value.clearValidate()
  } catch (error) {
    ElMessage.error(error?.response?.data?.message || error?.message || '题目创建失败')
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  await fetchProfessionalTree()
  if (selectedSubjectCode.value) {
    await loadKnowledgeTreeOptions(selectedSubjectCode.value, { force: true })
  }
})

watch(
  () => [String(userStore.role || '').trim(), assignedJointGroupCode.value],
  () => {
    if (!professionalTreeRaw.value.length) {
      return
    }
    applyProfessionalScopeOptions(professionalTreeRaw.value)
    formModel.knowledgePath = []
    formModel.pointSearchKeyword = ''
  },
)

watch(
  () => selectedSubjectCode.value,
  (nextSubjectCode, previousSubjectCode) => {
    if (nextSubjectCode === previousSubjectCode) {
      return
    }
    formModel.knowledgePath = []
    formModel.pointSearchKeyword = ''
    loadKnowledgeTreeOptions(nextSubjectCode, { force: true })
  },
)

watch(
  () => selectedKnowledgePointId.value,
  (nextKnowledgeId) => {
    const normalizedKnowledgeId = String(nextKnowledgeId || '').trim()
    if (!normalizedKnowledgeId) {
      formModel.pointSearchKeyword = ''
      return
    }
    const matched = l5SearchOptions.value.find((item) => String(item?.nodeId || '').trim() === normalizedKnowledgeId)
    if (matched) {
      formModel.pointSearchKeyword = String(matched.pathLabel || matched.value || '').trim()
      return
    }
    const pathIds = Array.isArray(knowledgePathMap.value[normalizedKnowledgeId]) ? knowledgePathMap.value[normalizedKnowledgeId] : []
    if (!pathIds.length) {
      formModel.pointSearchKeyword = String(knowledgeNodeLabelMap.value[normalizedKnowledgeId] || normalizedKnowledgeId)
      return
    }
    formModel.pointSearchKeyword = pathIds
      .map((id) => String(knowledgeNodeLabelMap.value[id] || id))
      .join(' / ')
  },
)

</script>

<template>
  <section class="upload-card">
    <header class="upload-header">
      <h4>题目录入</h4>
      <p>录题必须先选择 学科门类 -> 联考组 -> 科目，确保专业属性准确挂载。</p>
    </header>
    <el-radio-group v-model="uploadMode" class="mode-switch">
      <el-radio-button label="single">单题录入</el-radio-button>
      <el-radio-button label="batch">Word 批量上传</el-radio-button>
    </el-radio-group>

    <el-form
      v-if="uploadMode === 'single'"
      ref="formRef"
      :model="formModel"
      :rules="rules"
      label-width="120px"
      class="upload-form"
    >
      <el-form-item label="题目标题" prop="title">
        <el-input v-model="formModel.title" placeholder="请输入题目标题" />
      </el-form-item>

      <el-form-item label="题型" prop="type">
        <el-select v-model="formModel.type" placeholder="请选择题型">
          <el-option label="单选题" value="single_choice" />
          <el-option label="多选题" value="multiple_choice" />
          <el-option label="判断题" value="judge" />
          <el-option label="主观题" value="subjective" />
        </el-select>
      </el-form-item>

      <el-form-item label="专业属性" prop="scopePath">
        <el-cascader
          v-model="formModel.scopePath"
          :props="cascaderProps"
          :options="professionalOptions"
          :loading="loadingTree"
          :teleported="false"
          expand-trigger="hover"
          clearable
          filterable
          style="width: 100%"
          placeholder="请依次选择：学科门类 / 联考专业组 / 考试科目"
        />
      </el-form-item>

      <el-form-item label="知识点" prop="knowledgePath">
        <el-autocomplete
          v-model="formModel.pointSearchKeyword"
          :fetch-suggestions="queryL5KnowledgeSuggestions"
          value-key="pathLabel"
          clearable
          style="width: 100%; margin-bottom: 8px"
          placeholder="搜索 L5 知识点名称，自动补齐路径"
          @select="handleL5KnowledgeSelect"
        >
          <template #default="{ item }">
            <div class="knowledge-search-item">
              <span class="knowledge-search-name">{{ item.value }}</span>
              <small class="knowledge-search-path">{{ item.pathLabel }}</small>
            </div>
          </template>
        </el-autocomplete>
        <el-cascader
          v-model="formModel.knowledgePath"
          :props="knowledgeCascaderProps"
          :options="knowledgeCascaderOptions"
          :loading="loadingKnowledgeTree"
          clearable
          filterable
          style="width: 100%"
          placeholder="请从该科目 L4/L5 知识树中选择知识点"
        />
      </el-form-item>

      <el-form-item label="题干" prop="content">
        <el-input
          v-model="formModel.content"
          type="textarea"
          :rows="3"
          placeholder="请输入题干内容"
        />
      </el-form-item>

      <el-form-item v-if="isObjectiveQuestion" label="选项">
        <div class="option-block">
          <div
            v-for="(optionItem, optionIndex) in formModel.options"
            :key="`upload-option-${optionIndex}`"
            class="option-row"
          >
            <el-input v-model="optionItem.key" class="option-key" placeholder="键（A/B/C）" />
            <el-input v-model="optionItem.content" class="option-content" placeholder="选项内容" />
            <el-button
              type="danger"
              plain
              @click="removeOptionRow(optionIndex)"
            >
              删除
            </el-button>
          </div>
          <el-button plain @click="addOptionRow">新增选项</el-button>
        </div>
      </el-form-item>

      <el-form-item label="标准答案" prop="answer">
        <el-input v-model="formModel.answer" placeholder="例如：B / AC / 正确 / 文本答案" />
      </el-form-item>

      <el-form-item label="题目解析">
        <el-input
          v-model="formModel.analysis"
          type="textarea"
          :rows="2"
          placeholder="可选：输入解析内容"
        />
      </el-form-item>

      <el-form-item>
        <el-button
          type="primary"
          :loading="submitting"
          @click="handleSubmit"
        >
          上传题目
        </el-button>
      </el-form-item>
    </el-form>

    <section v-else class="batch-panel">
      <el-form label-width="120px" class="upload-form">
        <el-form-item label="专业属性" prop="scopePath">
          <el-cascader
            v-model="formModel.scopePath"
            :props="cascaderProps"
            :options="professionalOptions"
            :loading="loadingTree"
            :teleported="false"
            expand-trigger="hover"
            clearable
            filterable
            style="width: 100%"
            placeholder="请依次选择：学科门类 / 联考专业组 / 考试科目"
          />
        </el-form-item>
      </el-form>

      <section class="batch-guide">
        <div class="batch-guide__header">
          <div>
            <h5>上传格式说明</h5>
            <p>先选专业属性，再按模板整理题目内容，系统会优先按字段和题块识别。</p>
          </div>
          <div class="batch-guide__actions">
            <el-button plain :loading="loadingTemplateExample" @click="handlePreviewTemplateExample">
              {{ templateExampleVisible ? '收起模板示例' : '查看模板示例' }}
            </el-button>
            <el-button type="primary" plain :loading="loadingTemplateExample" @click="handleDownloadTemplateExample">
              下载上传模板
            </el-button>
          </div>
        </div>
        <ul class="batch-guide__list">
          <li v-for="note in batchUploadNotes" :key="note">{{ note }}</li>
        </ul>
        <pre v-if="templateExampleVisible && templateExampleContent" class="batch-guide__example">{{ templateExampleContent }}</pre>
      </section>

      <el-upload
        drag
        action="#"
        :show-file-list="false"
        :auto-upload="false"
        :on-change="handleBatchFileChange"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          拖拽 Word 文件到此处，或 <em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持 DOC / DOCX / TXT，超过 10 道题会自动转为后台任务处理。
          </div>
        </template>
      </el-upload>

      <el-alert
        v-if="batchTaskId"
        type="info"
        :closable="false"
        :title="`后台解析任务已创建：${batchTaskId}`"
        :description="batchTaskSummary || `当前状态 ${batchTaskStatus || '-'}，进度 ${batchTaskProgress}%`"
      />

      <el-progress
        v-if="batchTaskId && batchTaskStatus !== 'COMPLETED'"
        :percentage="Number(batchTaskProgress || 0)"
        :status="batchTaskStatus === 'FAILED' ? 'exception' : undefined"
      />

      <el-alert
        v-if="batchErrors.length"
        type="warning"
        :closable="false"
        :title="`解析过程中发现 ${batchErrors.length} 条问题`"
        :description="batchErrors.join('；')"
      />

      <el-alert
        v-if="batchParserSummary"
        type="success"
        :closable="false"
        title="识别引擎摘要"
        :description="batchParserSummary"
      />

      <el-table v-if="batchRows.length" :data="batchRows" border class="batch-table">
        <el-table-column prop="title" label="题目标题" min-width="180" show-overflow-tooltip />
        <el-table-column prop="content" label="AI 识别题干" min-width="300" show-overflow-tooltip />
        <el-table-column label="标签路径" min-width="320">
          <template #default="scope">
            <div class="knowledge-search-item">
              <span class="knowledge-search-name">{{ scope.row.pathLabel || '建议手动标注' }}</span>
              <small class="knowledge-search-path">
                置信度 {{ Math.round(Number(scope.row.confidence || 0) * 100) }}%
                <span v-if="scope.row.reviewMessage"> / {{ scope.row.reviewMessage }}</span>
              </small>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="3+2 标签纠偏" min-width="360">
          <template #default="scope">
            <div class="batch-edit-grid">
              <el-cascader
                :model-value="scope.row.scopePath"
                :props="cascaderProps"
                :options="professionalOptions"
                :loading="loadingTree"
                clearable
                filterable
                @change="(value) => handleBatchScopePathChange(scope.row, value)"
              />
              <el-cascader
                :model-value="scope.row.knowledgePath"
                :props="knowledgeCascaderProps"
                :options="knowledgeCascaderOptions"
                :loading="loadingKnowledgeTree"
                clearable
                filterable
                @visible-change="(visible) => visible && ensureBatchKnowledgeOptions(scope.row)"
                @change="(value) => handleBatchKnowledgePathChange(scope.row, value)"
              />
            </div>
          </template>
        </el-table-column>
        <el-table-column label="题型" width="120">
          <template #default="scope">
            {{ scope.row.type }}
          </template>
        </el-table-column>
        <el-table-column label="入库结果" width="180" fixed="right">
          <template #default="scope">
            <el-tag v-if="scope.row.createStatus === 'success'" type="success">已入库</el-tag>
            <el-tag v-else-if="scope.row.createStatus === 'error'" type="danger">入库失败</el-tag>
            <el-tag v-else type="info">待入库</el-tag>
            <div class="knowledge-search-path" v-if="scope.row.createMessage">{{ scope.row.createMessage }}</div>
            <div class="knowledge-search-path" v-if="scope.row.createdQuestionId">ID: {{ scope.row.createdQuestionId }}</div>
          </template>
        </el-table-column>
      </el-table>

      <div class="batch-actions">
        <el-button
          type="success"
          :loading="batchCreating"
          :disabled="!batchRows.length"
          @click="handleBatchCreate"
        >
          确认入库
        </el-button>
      </div>

      <QuestionBatchTaskCenter
        ref="taskCenterRef"
        embedded
        @restore-result="restoreBatchTaskResult"
      />
    </section>
  </section>
</template>

<style scoped>
.upload-card {
  border: 1px solid var(--el-border-color-light);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 16px;
  background: var(--el-bg-color);
}

.upload-header h4 {
  margin: 0;
}

.upload-header p {
  margin: 8px 0 0;
  color: var(--el-text-color-secondary);
}

.upload-form {
  margin-top: 16px;
}

.mode-switch {
  margin-top: 16px;
}

.batch-panel {
  margin-top: 16px;
  display: grid;
  gap: 16px;
}

.batch-guide {
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 12px;
  padding: 16px;
  background: var(--el-fill-color-extra-light);
}

.batch-guide__header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
}

.batch-guide__header h5 {
  margin: 0;
  font-size: 15px;
}

.batch-guide__header p {
  margin: 6px 0 0;
  color: var(--el-text-color-secondary);
  line-height: 1.6;
}

.batch-guide__actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.batch-guide__list {
  margin: 12px 0 0;
  padding-left: 18px;
  color: var(--el-text-color-regular);
  line-height: 1.7;
}

.batch-guide__example {
  margin: 12px 0 0;
  padding: 12px;
  border-radius: 10px;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-lighter);
  color: var(--el-text-color-primary);
  white-space: pre-wrap;
  word-break: break-word;
  font-family: var(--el-font-family-monospace, 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace);
}

.batch-table {
  width: 100%;
}

.batch-edit-grid {
  display: grid;
  gap: 8px;
}

.batch-actions {
  display: flex;
  justify-content: flex-end;
}

.option-block {
  width: 100%;
}

.option-row {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.option-key {
  max-width: 120px;
}

.option-content {
  flex: 1;
}

.knowledge-search-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.knowledge-search-name {
  color: var(--el-text-color-primary);
  font-size: 13px;
}

.knowledge-search-path {
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

@media (max-width: 768px) {
  .batch-guide__header {
    flex-direction: column;
  }
}
</style>
