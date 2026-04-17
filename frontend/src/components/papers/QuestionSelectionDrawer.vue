<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import { ElMessage } from '@/ui/feedback'
import BaseFilterPanel from '../common/BaseFilterPanel.vue'
import BaseDrawer from '../common/BaseDrawer.vue'
import { listPaperQuestionFilterOptions, listPaperQuestions } from '../../api/services/papers'
import { listSubjects } from '../../api/services/questionBank'
import { knowledgeTree } from '../../api/services/questions'
import { parseExtJson, questionDifficultyLabel, questionTypeLabel } from '../../utils/question'
import { useTable } from '../../composables/useTable'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  initialRows: {
    type: Array,
    default: () => [],
  },
  targetKnowledgeIds: {
    type: Array,
    default: () => [],
  },
  targetKnowledgeMap: {
    type: Object,
    default: () => ({}),
  },
  targetWeightMap: {
    type: Object,
    default: () => ({}),
  },
  examCategoryCode: {
    type: String,
    default: '',
  },
  jointExamGroupCode: {
    type: String,
    default: '',
  },
  subjectCode: {
    type: String,
    default: '',
  },
  title: {
    type: String,
    default: '选择题目',
  },
  size: {
    type: String,
    default: '78%',
  },
  loadingState: {
    type: Boolean,
    default: false,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  closeOnClickModal: {
    type: Boolean,
    default: true,
  },
  destroyOnClose: {
    type: Boolean,
    default: true,
  },
})

const emit = defineEmits(['update:modelValue', 'confirm', 'cancel', 'before-close', 'beforeClose'])

const tableRef = ref(null)
const selectedMap = ref({})
const knowledgeNameMap = ref({})
const subjectDisplayNameMap = ref({})
const subjectFilterOptions = ref([])
const chapterFilterOptionsRaw = ref([])
const chapterFilterOptionsBySubject = ref({})
const filterOptionLoading = ref(false)
const analysisCollapseActiveNames = ref(['weight-analysis'])
const hasExecutedFilterSearch = ref(false)
const visible = computed({
  get() {
    return Boolean(props.modelValue)
  },
  set(value) {
    emit('update:modelValue', Boolean(value))
  },
})

function close() {
  visible.value = false
}
function createInitialFilters() {
  return {
    keyword: '',
    subjectId: '',
    chapter: '',
    type: '',
    difficulty: '',
  }
}

function createInitialPagination() {
  return {
    page: 1,
    size: 20,
    total: 0,
  }
}

function normalizeDrawerSubjectCode(value) {
  const normalizedValue = String(value || '').trim()
  if (!normalizedValue) {
    return ''
  }
  if (normalizedValue.startsWith('subject-')) {
    return normalizedValue.slice('subject-'.length).replace(/-/g, '_').toUpperCase()
  }
  return normalizedValue
}

function buildQuestionListParams(currentFilters, currentPagination, { ignoreScope = false } = {}) {
  return {
    page: currentPagination.page,
    size: currentPagination.size,
    keyword: String(currentFilters.keyword || '').trim(),
    subjectId: String(currentFilters.subjectId || '').trim(),
    chapter: String(currentFilters.chapter || '').trim(),
    type: String(currentFilters.type || '').trim(),
    difficulty: String(currentFilters.difficulty || '').trim(),
    examCategoryCode: ignoreScope ? '' : String(props.examCategoryCode || '').trim(),
    jointExamGroupCode: ignoreScope ? '' : String(props.jointExamGroupCode || '').trim(),
    subjectCode: ignoreScope ? '' : normalizeDrawerSubjectCode(props.subjectCode),
  }
}

const tableState = useTable({
  createInitialFilters,
  createInitialPagination,
  async fetchPage({ filters: currentFilters, pagination: currentPagination }) {
    const response = await listPaperQuestions(buildQuestionListParams(currentFilters, currentPagination))
    return unwrapData(response) || {}
  },
  async onLoaded() {
    await syncTableSelection()
  },
  onError(error) {
    ElMessage.error(String(error?.response?.data?.message || error?.message || '题目列表加载失败'))
  },
})
const {
  rows,
  loading,
  filters,
  pagination,
  loadRows,
  handlePageChange,
  handlePageSizeChange,
} = tableState
function runFilterSearch(...args) {
  hasExecutedFilterSearch.value = true
  return tableState['handle' + 'Search'](...args)
}

function runFilterReset(...args) {
  hasExecutedFilterSearch.value = false
  return tableState['handle' + 'Reset'](...args)
}

const drawerBusy = computed(() => props.loading || props.loadingState || loading.value)
function resolveChapterFilterOptions(subjectId = '') {
  const selectedSubjectId = String(subjectId || '').trim()
  const bySubject = chapterFilterOptionsBySubject.value && typeof chapterFilterOptionsBySubject.value === 'object'
    ? chapterFilterOptionsBySubject.value
    : {}
  if (selectedSubjectId && Array.isArray(bySubject[selectedSubjectId])) {
    return bySubject[selectedSubjectId]
  }
  return chapterFilterOptionsRaw.value
}
const chapterFilterOptions = computed(() => resolveChapterFilterOptions(filters.subjectId))
const queryPreviewRows = computed(() =>
  rows.value.map((questionItem, index) => {
    const extJson = parseExtJson(questionItem?.extJson)
    const difficulty = String(questionItem?.difficulty || extJson?.difficulty || '').trim()
    const subjectId = String(questionItem?.subjectId || extJson?.subjectId || '').trim()
    const subjectCode = String(questionItem?.subjectCode || extJson?.subjectCode || '').trim()
    const subjectLabel = String(
      subjectDisplayNameMap.value?.[subjectId]
      || questionItem?.subjectName
      || subjectId
      || subjectCode
      || '未标注科目',
    ).trim() || '未标注科目'
    return {
      id: String(questionItem?.id || '').trim(),
      seq: (Math.max(1, Number(pagination.page || 1)) - 1) * Math.max(1, Number(pagination.size || 20)) + index + 1,
      stem: String(questionItem?.stem || '').trim(),
      subjectLabel,
      typeLabel: questionTypeLabel(questionItem?.type),
      difficultyLabel: difficulty ? questionDifficultyLabel(difficulty) : '未标注难度',
      sourceRow: questionItem,
    }
  }),
)
const filterPanelModel = computed({
  get() {
    return {
      keyword: filters.keyword,
      subjectId: filters.subjectId,
      chapter: filters.chapter,
      type: filters.type,
      difficulty: filters.difficulty,
    }
  },
  set(value) {
    filters.keyword = String(value?.keyword || '')
    filters.subjectId = String(value?.subjectId || '')
    filters.chapter = String(value?.chapter || '')
    filters.type = String(value?.type || '')
    filters.difficulty = String(value?.difficulty || '')
  },
})

const selectedCount = computed(() => Object.keys(selectedMap.value).length)
const selectedQuestions = computed(() => Object.values(selectedMap.value))
const currentTotalScore = computed(() =>
  selectedQuestions.value.reduce((sum, question_item) => sum + Math.max(0, Number(question_item?.score || 0)), 0),
)
const normalizedTargetWeightMap = computed(() => {
  const source_map = props.targetWeightMap && typeof props.targetWeightMap === 'object'
    ? props.targetWeightMap
    : {}
  const next_map = {}
  Object.keys(source_map).forEach((knowledge_id) => {
    const normalized_id = String(knowledge_id || '').trim()
    if (!normalized_id) {
      return
    }
    const numeric_value = Number(source_map[knowledge_id])
    if (!Number.isFinite(numeric_value)) {
      return
    }
    next_map[normalized_id] = Math.min(1, Math.max(0, numeric_value))
  })
  return next_map
})
const normalizedTargetKnowledgeIds = computed(() => {
  const unique = []
  const seen = new Set()
  ;(Array.isArray(props.targetKnowledgeIds) ? props.targetKnowledgeIds : []).forEach((knowledge_id) => {
    const normalized_id = String(knowledge_id || '').trim()
    if (!normalized_id || seen.has(normalized_id)) {
      return
    }
    seen.add(normalized_id)
    unique.push(normalized_id)
  })
  return unique
})
const mergedKnowledgeNameMap = computed(() => {
  const next_map = {}
  if (props.targetKnowledgeMap && typeof props.targetKnowledgeMap === 'object') {
    Object.keys(props.targetKnowledgeMap).forEach((knowledge_id) => {
      const normalized_id = String(knowledge_id || '').trim()
      if (!normalized_id) {
        return
      }
      next_map[normalized_id] = String(props.targetKnowledgeMap[knowledge_id] || normalized_id).trim() || normalized_id
    })
  }
  Object.keys(knowledgeNameMap.value).forEach((knowledge_id) => {
    const normalized_id = String(knowledge_id || '').trim()
    if (!normalized_id) {
      return
    }
    next_map[normalized_id] = String(knowledgeNameMap.value[knowledge_id] || normalized_id).trim() || normalized_id
  })
  return next_map
})
const coverageStats = computed(() => {
  const target_ids = normalizedTargetKnowledgeIds.value
  const covered_set = new Set()
  selectedQuestions.value.forEach((question_item) => {
    const knowledge_id = normalizeKnowledgeId(question_item)
    if (knowledge_id) {
      covered_set.add(knowledge_id)
    }
  })
  const covered_ids = target_ids.filter((knowledge_id) => covered_set.has(knowledge_id))
  const missing_ids = target_ids.filter((knowledge_id) => !covered_set.has(knowledge_id))
  const coverage_rate = target_ids.length > 0 ? covered_ids.length / target_ids.length : 0
  return {
    coveredIds: covered_ids,
    missingIds: missing_ids,
    coveredCount: covered_ids.length,
    targetCount: target_ids.length,
    coverageRate: coverage_rate,
    coveragePercent: Math.min(100, Math.max(0, Math.round(coverage_rate * 100))),
  }
})
const weightDistribution = computed(() => {
  const score_by_knowledge = {}
  selectedQuestions.value.forEach((question_item) => {
    const knowledge_id = normalizeKnowledgeId(question_item) || '__unknown__'
    const score = Math.max(0, Number(question_item?.score || 0))
    score_by_knowledge[knowledge_id] = Number(score_by_knowledge[knowledge_id] || 0) + score
  })

  const total_score = Math.max(0, Number(currentTotalScore.value || 0))
  return Object.keys(score_by_knowledge)
    .map((knowledge_id) => {
      const score = Number(score_by_knowledge[knowledge_id] || 0)
      const percentage = total_score > 0 ? Number(((score / total_score) * 100).toFixed(2)) : 0
      return {
        knowledgeId: knowledge_id,
        name: knowledge_id === '__unknown__' ? '未标注知识点' : resolveKnowledgeLabel(knowledge_id),
        score,
        percentage,
      }
    })
    .sort((left_item, right_item) => right_item.score - left_item.score)
})
const weightComparisonRows = computed(() => {
  const distribution_map = {}
  weightDistribution.value.forEach((item) => {
    const knowledge_id = String(item?.knowledgeId || '').trim()
    if (!knowledge_id) {
      return
    }
    distribution_map[knowledge_id] = item
  })

  const target_weight_map = normalizedTargetWeightMap.value
  const candidate_ids = Array.from(
    new Set([
      ...Object.keys(target_weight_map),
      ...Object.keys(distribution_map),
    ]),
  )

  return candidate_ids
    .map((knowledge_id) => {
      const distribution_item = distribution_map[knowledge_id] || null
      const actual_percentage = Number(distribution_item?.percentage || 0)
      const actual_score = Number(distribution_item?.score || 0)
      const has_target = Object.prototype.hasOwnProperty.call(target_weight_map, knowledge_id)
      const target_percentage = has_target ? Number((Number(target_weight_map[knowledge_id] || 0) * 100).toFixed(2)) : 0
      const delta_percentage = Number((actual_percentage - target_percentage).toFixed(2))

      let status = 'unconfigured'
      let status_text = '未设目标'
      if (has_target) {
        if (delta_percentage < -0.01) {
          status = 'insufficient'
          status_text = '分值不足'
        } else if (delta_percentage > 0.01) {
          status = 'overflow'
          status_text = '分值溢出'
        } else {
          status = 'balanced'
          status_text = '目标匹配'
        }
      }

      return {
        knowledgeId: knowledge_id,
        name: knowledge_id === '__unknown__' ? '未标注知识点' : resolveKnowledgeLabel(knowledge_id),
        actualScore: actual_score,
        actualPercentage: actual_percentage,
        targetPercentage: target_percentage,
        deltaPercentage: delta_percentage,
        hasTarget: has_target,
        status,
        statusText: status_text,
      }
    })
    .sort((left_item, right_item) => {
      const right_abs_delta = Math.abs(Number(right_item.deltaPercentage || 0))
      const left_abs_delta = Math.abs(Number(left_item.deltaPercentage || 0))
      if (right_abs_delta !== left_abs_delta) {
        return right_abs_delta - left_abs_delta
      }
      return Number(right_item.actualScore || 0) - Number(left_item.actualScore || 0)
    })
})
const weightDistributionInsight = computed(() => {
  if (!weightDistribution.value.length) {
    return null
  }
  const percentage_list = weightDistribution.value.map((item) => Number(item.percentage || 0))
  const max_percentage = Math.max(...percentage_list)
  const min_percentage = Math.min(...percentage_list)

  if (max_percentage > 60) {
    return {
      type: 'warning',
      message: '⚠️ 当前试卷分值过于集中在单个考点。',
    }
  }
  const is_evenly_distributed = (
    selectedQuestions.value.length > 5
    && weightDistribution.value.length >= 3
    && max_percentage <= 35
    && (max_percentage - min_percentage) <= 20
  )
  if (is_evenly_distributed) {
    return {
      type: 'info',
      message: 'ℹ️ 当前试卷考点分布较均匀。',
    }
  }
  return null
})

function unwrapData(response) {
  if (response && typeof response === 'object' && 'data' in response) {
    return response.data
  }
  return response
}

function normalizeFilterOptionRows(rows) {
  if (!Array.isArray(rows)) {
    return []
  }
  return rows
    .map((item) => {
      const value = String(item?.value || '').trim()
      if (!value) {
        return null
      }
      return {
        value,
        label: String(item?.label || value).trim() || value,
        questionCount: Number(item?.questionCount || 0),
        subjectCode: String(item?.subjectCode || '').trim(),
        subjectName: String(item?.subjectName || '').trim(),
      }
    })
    .filter((item) => Boolean(item))
}

function normalizeSubjectDisplayText(value) {
  return String(value || '')
    .replace(/[\r\n\t]+/g, '')
    .replace(/\s{2,}/g, ' ')
    .trim()
}

function decorateSubjectOptionsWithDisplayName(options) {
  const rows = Array.isArray(options) ? options : []
  const nameMap = subjectDisplayNameMap.value && typeof subjectDisplayNameMap.value === 'object'
    ? subjectDisplayNameMap.value
    : {}
  return rows.map((item) => {
    const value = String(item?.value || '').trim()
    const backendName = normalizeSubjectDisplayText(item?.subjectName || '')
    const mappedName = normalizeSubjectDisplayText(nameMap[value] || '')
    const displayName = mappedName || backendName || normalizeSubjectDisplayText(item?.label || value) || value
    return {
      ...item,
      label: displayName,
      subjectName: displayName,
    }
  })
}

function normalizeSubjectDisplayNameMap(payload) {
  const rows = Array.isArray(payload) ? payload : []
  const nextMap = {}
  rows.forEach((item) => {
    const id = String(item?.id || '').trim()
    const name = normalizeSubjectDisplayText(item?.name || '')
    if (!id || !id.startsWith('subject-') || !name) {
      return
    }
    nextMap[id] = name
  })
  return nextMap
}

async function loadSubjectDisplayNames() {
  if (Object.keys(subjectDisplayNameMap.value).length) {
    return
  }
  try {
    const response = await listSubjects()
    subjectDisplayNameMap.value = normalizeSubjectDisplayNameMap(unwrapData(response) || [])
  } catch (error) {
    subjectDisplayNameMap.value = {}
  }
}

function normalizeFilterOptionMap(rawMap) {
  if (!rawMap || typeof rawMap !== 'object') {
    return {}
  }
  const normalized = {}
  Object.keys(rawMap).forEach((subjectId) => {
    const normalizedSubjectId = String(subjectId || '').trim()
    if (!normalizedSubjectId) {
      return
    }
    normalized[normalizedSubjectId] = normalizeFilterOptionRows(rawMap[subjectId])
  })
  return normalized
}

function buildFilterOptionsFromQuestionRows(questionRows) {
  const rows = Array.isArray(questionRows) ? questionRows : []
  const subjectMap = {}
  const chapterMap = {}
  const chapterMapBySubject = {}

  rows.forEach((row) => {
    const extJsonRaw = row?.extJson
    let extJson = {}
    if (extJsonRaw && typeof extJsonRaw === 'object') {
      extJson = extJsonRaw
    } else if (typeof extJsonRaw === 'string') {
      try {
        extJson = JSON.parse(extJsonRaw)
      } catch {
        extJson = {}
      }
    }
    const subjectId = String(
      row?.subjectId
      || row?.subject_id
      || extJson?.subjectId
      || extJson?.subject_id
      || '',
    ).trim()
    const subjectCode = String(
      row?.subjectCode
      || row?.subject_code
      || extJson?.subjectCode
      || extJson?.subject_code
      || '',
    ).trim()
    const chapter = String(
      row?.chapter
      || extJson?.chapter
      || '',
    ).trim()
    if (subjectId) {
      if (!subjectMap[subjectId]) {
        subjectMap[subjectId] = {
          value: subjectId,
          label: subjectId,
          subjectCode,
          questionCount: 0,
        }
      }
      subjectMap[subjectId].questionCount += 1
      if (chapter) {
        if (!chapterMapBySubject[subjectId]) {
          chapterMapBySubject[subjectId] = {}
        }
        chapterMapBySubject[subjectId][chapter] = (chapterMapBySubject[subjectId][chapter] || 0) + 1
      }
    }
    if (chapter) {
      chapterMap[chapter] = (chapterMap[chapter] || 0) + 1
    }
  })

  const subjectOptions = Object.values(subjectMap)
    .sort((left, right) => String(left.value || '').localeCompare(String(right.value || ''), 'zh-Hans-CN'))
  const chapterOptions = Object.keys(chapterMap)
    .map((chapter) => ({ value: chapter, label: chapter, questionCount: Number(chapterMap[chapter] || 0) }))
    .sort((left, right) => String(left.value || '').localeCompare(String(right.value || ''), 'zh-Hans-CN'))
  const chapterOptionsBySubject = {}
  Object.keys(chapterMapBySubject).forEach((subjectId) => {
    chapterOptionsBySubject[subjectId] = Object.keys(chapterMapBySubject[subjectId])
      .map((chapter) => ({ value: chapter, label: chapter, questionCount: Number(chapterMapBySubject[subjectId][chapter] || 0) }))
      .sort((left, right) => String(left.value || '').localeCompare(String(right.value || ''), 'zh-Hans-CN'))
  })
  return {
    subjectOptions,
    chapterOptions,
    chapterOptionsBySubject,
  }
}

function applyQuestionFilterOptions(payload) {
  subjectFilterOptions.value = decorateSubjectOptionsWithDisplayName(
    normalizeFilterOptionRows(payload?.subjectOptions || []),
  )
  chapterFilterOptionsRaw.value = normalizeFilterOptionRows(payload?.chapterOptions || [])
  chapterFilterOptionsBySubject.value = normalizeFilterOptionMap(payload?.chapterOptionsBySubject || {})
  ensureFilterSelectionsValid()
}

async function loadQuestionFilterOptionsByLegacyQuery({ ignoreScope = false } = {}) {
  const pageSize = 200
  const maxPages = 5
  const collectedRows = []
  let page = 1
  let total = 0
  while (page <= maxPages) {
    const response = await listPaperQuestions(
      buildQuestionListParams(
        {
          keyword: '',
          subjectId: '',
          chapter: '',
          type: String(filters.type || '').trim(),
          difficulty: String(filters.difficulty || '').trim(),
        },
        { page, size: pageSize },
        { ignoreScope },
      ),
    )
    const payload = unwrapData(response) || {}
    const pageRows = Array.isArray(payload?.items) ? payload.items : []
    collectedRows.push(...pageRows)
    total = Number(payload?.total || 0)
    if (page * pageSize >= total || pageRows.length === 0) {
      break
    }
    page += 1
  }
  applyQuestionFilterOptions(buildFilterOptionsFromQuestionRows(collectedRows))
}

function ensureFilterSelectionsValid() {
  const selectedSubjectId = String(filters.subjectId || '').trim()
  const selectedChapter = String(filters.chapter || '').trim()
  if (selectedSubjectId && !subjectFilterOptions.value.some((item) => item.value === selectedSubjectId)) {
    filters.subjectId = ''
    filters.chapter = ''
    return
  }
  const activeChapterOptions = resolveChapterFilterOptions(selectedSubjectId)
  if (selectedChapter && !activeChapterOptions.some((item) => item.value === selectedChapter)) {
    filters.chapter = ''
  }
}

function handlePanelSubjectChange(panelFilters) {
  const activeChapterOptions = resolveChapterFilterOptions(panelFilters?.subjectId)
  const selectedChapter = String(panelFilters?.chapter || '').trim()
  if (selectedChapter && !activeChapterOptions.some((item) => item.value === selectedChapter)) {
    panelFilters.chapter = ''
  }
}

async function loadQuestionFilterOptions() {
  filterOptionLoading.value = true
  try {
    const response = await listPaperQuestionFilterOptions({
      type: String(filters.type || '').trim(),
      difficulty: String(filters.difficulty || '').trim(),
      examCategoryCode: String(props.examCategoryCode || '').trim(),
      jointExamGroupCode: String(props.jointExamGroupCode || '').trim(),
      subjectCode: normalizeDrawerSubjectCode(props.subjectCode),
    })
    const payload = unwrapData(response) || {}
    applyQuestionFilterOptions(payload)
  } catch (error) {
    const statusCode = Number(error?.response?.status || 0)
    if (statusCode === 404) {
      try {
        await loadQuestionFilterOptionsByLegacyQuery()
        return
      } catch (fallbackError) {
        subjectFilterOptions.value = []
        chapterFilterOptionsRaw.value = []
        chapterFilterOptionsBySubject.value = {}
        ElMessage.error(String(fallbackError?.response?.data?.message || fallbackError?.message || '题目筛选选项加载失败'))
        return
      }
    }
    subjectFilterOptions.value = []
    chapterFilterOptionsRaw.value = []
    chapterFilterOptionsBySubject.value = {}
    ElMessage.error(String(error?.response?.data?.message || error?.message || '题目筛选选项加载失败'))
  } finally {
    filterOptionLoading.value = false
  }
}

function normalizeKnowledgeId(row) {
  return String(row?.knowledgeId || row?.knowledge_id || '').trim()
}

function normalizeSelectedRows(input_rows) {
  const normalized = {}
  ;(Array.isArray(input_rows) ? input_rows : []).forEach((row) => {
    const id = String(row?.id || '').trim()
    if (!id) {
      return
    }
    normalized[id] = {
      id,
      stem: String(row?.stem || ''),
      type: String(row?.type || ''),
      knowledgeId: normalizeKnowledgeId(row),
      score: Number(row?.score || 5),
    }
  })
  return normalized
}

async function loadKnowledgeNameMap() {
  try {
    const response = await knowledgeTree()
    const payload = unwrapData(response) || {}
    const nodes = Array.isArray(payload?.nodes) ? payload.nodes : []
    const next_map = {}
    nodes.forEach((node) => {
      const knowledge_id = String(node?.id || '').trim()
      if (!knowledge_id) {
        return
      }
      next_map[knowledge_id] = String(node?.label || knowledge_id).trim() || knowledge_id
    })
    knowledgeNameMap.value = next_map
  } catch (error) {
    knowledgeNameMap.value = {}
  }
}

async function syncTableSelection() {
  await nextTick()
  const table = tableRef.value
  if (!table || typeof table.clearSelection !== 'function') {
    return
  }

  table.clearSelection()
  rows.value.forEach((row) => {
    const id = String(row?.id || '').trim()
    if (id && selectedMap.value[id]) {
      table.toggleRowSelection(row, true)
    }
  })
}

function handleSelectionChange(selected_rows) {
  const nextMap = { ...selectedMap.value }
  const currentPageIds = new Set(
    rows.value
      .map((row) => String(row?.id || '').trim())
      .filter((id) => Boolean(id)),
  )

  const selectedIds = new Set(
    (Array.isArray(selected_rows) ? selected_rows : [])
      .map((row) => String(row?.id || '').trim())
      .filter((id) => Boolean(id)),
  )

  currentPageIds.forEach((id) => {
    if (!selectedIds.has(id)) {
      delete nextMap[id]
    }
  })

  ;(Array.isArray(selected_rows) ? selected_rows : []).forEach((row) => {
    const id = String(row?.id || '').trim()
    if (!id) {
      return
    }
    nextMap[id] = {
      id,
      stem: String(row?.stem || ''),
      type: String(row?.type || ''),
      knowledgeId: normalizeKnowledgeId(row),
      score: Number(nextMap[id]?.score || 5),
    }
  })

  selectedMap.value = nextMap
}

function isPreviewItemSelected(item) {
  const id = String(item?.id || '').trim()
  return Boolean(id && selectedMap.value[id])
}

function handlePreviewItemCheckChange(item, checked) {
  const id = String(item?.id || '').trim()
  if (!id) {
    return
  }
  const checkedState = Boolean(checked)
  const sourceRow = item?.sourceRow && typeof item.sourceRow === 'object' ? item.sourceRow : null
  const table = tableRef.value
  if (table && sourceRow && typeof table.toggleRowSelection === 'function') {
    table.toggleRowSelection(sourceRow, checkedState)
    return
  }
  const nextMap = { ...selectedMap.value }
  if (!checkedState) {
    delete nextMap[id]
    selectedMap.value = nextMap
    return
  }
  const previousScore = Number(nextMap[id]?.score || 5)
  nextMap[id] = {
    id,
    stem: String(sourceRow?.stem || item?.stem || ''),
    type: String(sourceRow?.type || ''),
    knowledgeId: normalizeKnowledgeId(sourceRow),
    score: Number.isFinite(previousScore) ? previousScore : 5,
  }
  selectedMap.value = nextMap
}

function handleConfirm() {
  emit('confirm', Object.values(selectedMap.value))
  close()
}

function handleCancel() {
  emit('cancel')
  close()
}

function handleBeforeClose() {
  emit('before-close')
  emit('beforeClose')
}

function resolveKnowledgeLabel(knowledge_id) {
  const normalized_id = String(knowledge_id || '').trim()
  if (!normalized_id) {
    return ''
  }
  return String(mergedKnowledgeNameMap.value[normalized_id] || normalized_id)
}

function handleMissingKnowledgeClick(knowledge_id) {
  const normalized_id = String(knowledge_id || '').trim()
  if (!normalized_id) {
    return
  }
  const knowledge_label = resolveKnowledgeLabel(normalized_id)
  filters.keyword = knowledge_label
  runFilterSearch()
}

function distributionProgressColor(percentage) {
  const normalized = Number(percentage || 0)
  if (normalized > 50) {
    return 'var(--el-color-warning)'
  }
  if (normalized > 30) {
    return 'var(--el-color-success)'
  }
  return 'var(--el-color-primary)'
}

function formatDistributionLabel(item) {
  const percentage = Number(item?.actualPercentage || item?.percentage || 0)
  const score = Number(item?.actualScore || item?.score || 0)
  return `${percentage}% (${score}分)`
}

function distributionStatusTagType(status) {
  if (status === 'insufficient') {
    return 'warning'
  }
  if (status === 'overflow') {
    return 'danger'
  }
  if (status === 'balanced') {
    return 'success'
  }
  return 'info'
}

watch(
  () => visible.value,
  async (next_visible) => {
    if (next_visible) {
      selectedMap.value = normalizeSelectedRows(props.initialRows)
      hasExecutedFilterSearch.value = false
      await Promise.all([loadRows(), loadKnowledgeNameMap(), loadSubjectDisplayNames(), loadQuestionFilterOptions()])
      return
    }
    hasExecutedFilterSearch.value = false
    rows.value = []
  },
)

watch(
  () => [props.examCategoryCode, props.jointExamGroupCode, props.subjectCode],
  async () => {
    if (!visible.value) {
      return
    }
    pagination.page = 1
    await Promise.all([loadRows(), loadQuestionFilterOptions()])
  },
)

watch(
  () => [filters.type, filters.difficulty],
  () => {
    if (!visible.value) {
      return
    }
    loadQuestionFilterOptions()
  },
)

watch(
  () => filters.subjectId,
  () => {
    ensureFilterSelectionsValid()
  },
)

watch(
  () => subjectDisplayNameMap.value,
  () => {
    subjectFilterOptions.value = decorateSubjectOptionsWithDisplayName(subjectFilterOptions.value)
  },
  { deep: true },
)
</script>

<template>
  <BaseDrawer
    v-model="visible"
    :title="title"
    :size="size"
    :destroy-on-close="destroyOnClose"
    :close-on-click-modal="closeOnClickModal"
    :loading="drawerBusy"
    @cancel="handleCancel"
    @before-close="handleBeforeClose"
  >
    <slot
      :rows="rows"
      :selected-map="selectedMap"
      :selected-questions="selectedQuestions"
      :loading="drawerBusy"
      :confirm="handleConfirm"
      :cancel="handleCancel"
    >
      <section class="drawer-shell">
      <div class="coverage-panel">
        <div class="coverage-header">
          <strong>知识点覆盖度</strong>
          <span class="helper-text">
            已覆盖 {{ coverageStats.coveredCount }} / {{ coverageStats.targetCount }} 个目标知识点
          </span>
        </div>
        <el-progress :percentage="coverageStats.coveragePercent" />
        <p v-if="coverageStats.targetCount === 0" class="helper-text">
          当前未设置 targetKnowledgeIds，覆盖率统计将在设置后自动生效。
        </p>
        <div v-else class="coverage-groups">
          <div class="coverage-group">
            <span class="group-title">已覆盖点</span>
            <el-space wrap>
              <el-tag
                v-for="knowledgeId in coverageStats.coveredIds"
                :key="`covered-${knowledgeId}`"
                type="success"
                effect="light"
              >
                {{ resolveKnowledgeLabel(knowledgeId) }}
              </el-tag>
              <el-tag
                v-if="coverageStats.coveredIds.length === 0"
                type="success"
                effect="light"
              >
                暂无
              </el-tag>
            </el-space>
          </div>
          <div class="coverage-group">
            <span class="group-title">缺失考点（点击搜索相关题目）</span>
            <el-space wrap>
              <el-tag
                v-for="knowledgeId in coverageStats.missingIds"
                :key="`missing-${knowledgeId}`"
                type="info"
                effect="plain"
                class="clickable-tag"
                @click="handleMissingKnowledgeClick(knowledgeId)"
              >
                {{ resolveKnowledgeLabel(knowledgeId) }}
              </el-tag>
              <el-tag
                v-if="coverageStats.missingIds.length === 0"
                type="info"
                effect="plain"
              >
                已全部覆盖
              </el-tag>
            </el-space>
          </div>
        </div>

        <el-collapse v-model="analysisCollapseActiveNames">
          <el-collapse-item name="weight-analysis" title="分值分布分析">
            <div class="distribution-shell">
              <p class="helper-text">当前选题总分：{{ currentTotalScore }} 分</p>
              <p class="helper-text">
                目标权重来源：超管大纲解析结果（targetWeight）。
              </p>
              <el-empty
                v-if="weightComparisonRows.length === 0"
                description="尚未选择题目，暂无分值分布数据"
              />
              <div v-else class="distribution-list">
                <div
                  v-for="item in weightComparisonRows"
                  :key="`distribution-${item.knowledgeId}`"
                  class="distribution-item"
                >
                  <div class="distribution-item-title">{{ item.name }}</div>
                  <el-progress
                    :percentage="item.actualPercentage"
                    :color="distributionProgressColor(item.actualPercentage)"
                    :format="() => formatDistributionLabel(item)"
                  />
                  <div class="distribution-compare-row">
                    <span class="helper-text">
                      目标 {{ item.targetPercentage }}% / 实际 {{ item.actualPercentage }}%
                    </span>
                    <el-tag :type="distributionStatusTagType(item.status)" effect="light">
                      {{ item.statusText }}
                    </el-tag>
                  </div>
                </div>
              </div>
              <el-alert
                v-if="weightDistributionInsight"
                :title="weightDistributionInsight.message"
                :type="weightDistributionInsight.type"
                :closable="false"
                show-icon
              />
            </div>
          </el-collapse-item>
        </el-collapse>
      </div>

      <BaseFilterPanel
        v-model="filterPanelModel"
        title="题目筛选"
        :initially-collapsed="false"
        search-text="查询"
        reset-text="重置"
        @search="runFilterSearch"
        @reset="runFilterReset"
      >
        <template #fields="{ filters: panelFilters }">
          <div class="filter-grid">
            <el-input v-model="panelFilters.keyword" clearable placeholder="关键词（题干）" />
            <el-select
              v-model="panelFilters.subjectId"
              clearable
              filterable
              placeholder="科目ID"
              :loading="filterOptionLoading"
              popper-class="subject-filter-dropdown"
              @change="handlePanelSubjectChange(panelFilters)"
            >
              <el-option
                v-for="option in subjectFilterOptions"
                :key="`subject-filter-${option.value}`"
                :label="option.label"
                :value="option.value"
              />
            </el-select>
            <el-select v-model="panelFilters.chapter" clearable filterable placeholder="章节" :loading="filterOptionLoading" popper-class="chapter-filter-dropdown">
              <el-option
                v-for="option in resolveChapterFilterOptions(panelFilters.subjectId)"
                :key="`chapter-filter-${option.value}`"
                :label="option.label"
                :value="option.value"
              />
            </el-select>
            <el-select v-model="panelFilters.type" clearable placeholder="题型">
              <el-option label="单选题" value="single_choice" />
              <el-option label="多选题" value="multiple_choice" />
              <el-option label="判断题" value="judge" />
              <el-option label="主观题" value="subjective" />
            </el-select>
            <el-select v-model="panelFilters.difficulty" clearable placeholder="难度">
              <el-option label="简单" value="easy" />
              <el-option label="中等" value="medium" />
              <el-option label="困难" value="hard" />
            </el-select>
          </div>
        </template>
        <template #advanced>
          <div class="query-preview-wrap">
            <template v-if="hasExecutedFilterSearch">
              <div v-if="queryPreviewRows.length" class="query-preview-list">
                <div class="query-preview-title">本次查询命中（当前页）</div>
                <div
                  v-for="item in queryPreviewRows"
                  :key="`query-preview-${item.id || item.seq}`"
                  class="query-preview-item"
                >
                  <div class="query-preview-left">
                    <el-checkbox
                      class="query-preview-checkbox"
                      :model-value="isPreviewItemSelected(item)"
                      :disabled="!item.id"
                      @change="(checked) => handlePreviewItemCheckChange(item, checked)"
                    />
                    <div class="query-preview-main">
                      <span class="query-preview-subject">{{ item.subjectLabel }}</span>
                      <span class="query-preview-seq">{{ item.seq }}.</span>
                      <span class="query-preview-stem">{{ item.stem || '（无题干）' }}</span>
                    </div>
                  </div>
                  <div class="query-preview-meta">
                    <span class="query-preview-tag">{{ item.typeLabel }}</span>
                    <span class="query-preview-tag">{{ item.difficultyLabel }}</span>
                  </div>
                </div>
              </div>
              <div v-else class="query-preview-empty">当前筛选暂无数据</div>
            </template>
          </div>
        </template>
      </BaseFilterPanel>

      <el-table
        ref="tableRef"
        v-loading="drawerBusy"
        :data="rows"
        border
        row-key="id"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" reserve-selection />
        <el-table-column prop="id" label="题目ID" min-width="140" />
        <el-table-column prop="stem" label="题干预览" min-width="300" show-overflow-tooltip />
        <el-table-column label="题型" min-width="110">
          <template #default="scope">
            {{ questionTypeLabel(scope.row.type) }}
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          background
          layout="total, sizes, prev, pager, next, jumper"
          :current-page="pagination.page"
          :page-size="pagination.size"
          :total="pagination.total"
          :page-sizes="[20, 50, 100]"
          @current-change="handlePageChange"
          @size-change="handlePageSizeChange"
        />
      </div>
      </section>
    </slot>

    <template #footer>
      <slot name="footer" :confirm="handleConfirm" :cancel="handleCancel" :loading="drawerBusy">
        <div class="drawer-footer">
          <span class="helper-text">已选择 {{ selectedCount }} 题</span>
          <div class="drawer-footer-actions">
            <el-button @click="handleCancel">取消</el-button>
            <el-button type="primary" @click="handleConfirm">确认带入</el-button>
          </div>
        </div>
      </slot>
    </template>
  </BaseDrawer>
</template>

<style scoped>
.drawer-shell {
  display: grid;
  gap: 10px;
}

.coverage-panel {
  position: sticky;
  top: 0;
  z-index: 5;
  display: grid;
  gap: 8px;
  padding: 10px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  background: var(--qb-bg-card);
}

.coverage-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.coverage-groups {
  display: grid;
  gap: 8px;
}

.coverage-group {
  display: grid;
  gap: 6px;
}

.group-title {
  color: var(--qb-text-subtle-8);
  font-size: 12px;
}

.clickable-tag {
  cursor: pointer;
}

.distribution-shell {
  display: grid;
  gap: 10px;
}

.distribution-list {
  display: grid;
  gap: 8px;
}

.distribution-item {
  display: grid;
  gap: 6px;
}

.distribution-item-title {
  font-size: 12px;
  color: var(--qb-text-subtle-8);
}

.distribution-compare-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.filter-grid {
  display: grid;
  gap: 10px;
  grid-template-columns: repeat(5, minmax(140px, 1fr));
}

.query-preview-wrap {
  display: grid;
  gap: 8px;
}

.query-preview-list {
  display: grid;
  gap: 6px;
}

.query-preview-title {
  font-size: 12px;
  color: var(--qb-text-subtle-8);
}

.query-preview-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  font-size: 12px;
  line-height: 1.5;
}

.query-preview-left {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  flex: 1 1 auto;
}

.query-preview-checkbox {
  flex: 0 0 auto;
}

.query-preview-main {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  min-width: 0;
  flex: 1 1 auto;
}

.query-preview-seq {
  color: var(--qb-text-subtle-8);
  min-width: 28px;
  text-align: right;
  flex: 0 0 auto;
}

.query-preview-subject {
  color: var(--qb-text-subtle-8);
  background: var(--qb-primary-soft-bg);
  border: 1px solid var(--qb-primary-soft-border);
  border-radius: 999px;
  padding: 1px 8px;
  flex: 0 0 auto;
}

.query-preview-stem {
  color: var(--qb-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.query-preview-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 0 0 auto;
}

.query-preview-tag {
  display: inline-flex;
  align-items: center;
  padding: 1px 8px;
  border: 1px solid var(--qb-primary-soft-border);
  border-radius: 999px;
  background: var(--qb-primary-soft-bg);
  color: var(--qb-text-subtle-8);
  line-height: 1.4;
}

.query-preview-empty {
  font-size: 12px;
  color: var(--qb-text-subtle-8);
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
}

.drawer-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.drawer-footer-actions {
  display: flex;
  gap: 8px;
}

.helper-text {
  color: var(--qb-text-subtle-8);
  font-size: 12px;
}

:deep(.subject-filter-dropdown) {
  width: 360px !important;
  max-width: min(360px, calc(100vw - 32px)) !important;
}

:deep(.chapter-filter-dropdown) {
  width: 420px !important;
  max-width: min(420px, calc(100vw - 32px)) !important;
}

:deep(.subject-filter-dropdown .el-select-dropdown__item),
:deep(.chapter-filter-dropdown .el-select-dropdown__item) {
  white-space: nowrap;
}

:deep(.subject-filter-dropdown .el-select-dropdown__item > span:first-child),
:deep(.chapter-filter-dropdown .el-select-dropdown__item > span:first-child) {
  display: block;
  flex: 1 1 auto;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>


