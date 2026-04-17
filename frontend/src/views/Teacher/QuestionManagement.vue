<script setup>
import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from '@/ui/feedback'
import { useRoute, useRouter } from 'vue-router'
import { resolveApiErrorMessage } from '../../api/request'
import BaseFilterPanel from '../../components/common/BaseFilterPanel.vue'
import QuestionUpload from '../../components/questions/QuestionUpload.vue'
import {
  deleteQuestion,
  deleteQuestionsBatch,
  fetchContentBaseline,
  fetchQuestionDetail,
  fetchQuestionList,
  fetchQuestionReviews,
  restoreDeletedQuestion,
  restoreDeletedQuestionsBatch,
  transitionStatusBatch,
  updateQuestionData,
  updateQuestionStatus,
} from '../../api/services/questionBank'
import { paperTargetWeights } from '../../api/services/papers'
import { useForm } from '../../composables/useForm'
import { useTable } from '../../composables/useTable'
import { useUserStore } from '../../stores/userStore.js'
import { buildContentLabelMaps, resolveContentLabel } from '../../utils/contentBaseline.js'
import { canTransitionQuestionStatus, parseExtJson, questionStatusMeta, questionTypeLabel } from '../../utils/question'
import { resolveManualDraftScope } from '../../utils/paperDraftScope'

const userStore = useUserStore()
const route = useRoute()
const router = useRouter()

const errorMessage = ref('')
const fallbackSearchNotice = ref('')
const subjectCodeOptions = ref([])
const transitioningQuestionId = ref('')
const questionTableRef = ref(null)
const selectedQuestionMap = ref({})
const selectionTargetWeightMap = ref({})
const syncingTableSelection = ref(false)

const editDialogVisible = ref(false)
const editSaving = ref(false)
function createInitialEditForm() {
  return {
    id: '',
    knowledgeId: '',
    userId: '',
    type: '',
    stem: '',
    optionsJson: '[]',
    answer: '',
    status: '',
    extJsonObject: {},
    extJsonText: '{}',
    createTime: '',
    updateTime: '',
  }
}

const { form: editForm, resetForm: resetEditFormState, patchForm: patchEditForm } = useForm(createInitialEditForm)

const detailDrawerVisible = ref(false)
const detailLoading = ref(false)
const detailQuestion = ref(null)
const detailReviews = ref([])
const deletingQuestionId = ref('')
const batchActing = ref(false)
const lastDeletedQuestionSnapshotId = ref('')
const lastDeletedQuestionId = ref('')
const lastDeletedQuestionExpireAt = ref(0)
const lastDeletedBatchSnapshotId = ref('')
const lastDeletedBatchCount = ref(0)
const lastDeletedBatchExpireAt = ref(0)

const UNDO_HINT_STORAGE_PREFIX = 'qb-question-management-undo-hint'
const UNDO_DEFAULT_EXPIRE_SEC = 600

const undoHintStorageKey = computed(() => {
  const userId = String(userStore.userId || '').trim() || 'anonymous'
  return `${UNDO_HINT_STORAGE_PREFIX}:${userId}`
})

function toPositiveInteger(value, fallback = 0) {
  const normalized = Number(value)
  if (!Number.isFinite(normalized)) {
    return fallback
  }
  return Math.max(0, Math.trunc(normalized))
}

function isExpired(expireAt) {
  const normalizedExpireAt = toPositiveInteger(expireAt, 0)
  if (!normalizedExpireAt) {
    return false
  }
  return normalizedExpireAt <= Date.now()
}

function persistUndoHintState() {
  const payload = {}

  if (lastDeletedQuestionSnapshotId.value && !isExpired(lastDeletedQuestionExpireAt.value)) {
    payload.single = {
      snapshotId: String(lastDeletedQuestionSnapshotId.value || '').trim(),
      questionId: String(lastDeletedQuestionId.value || '').trim(),
      expireAt: toPositiveInteger(lastDeletedQuestionExpireAt.value, 0),
    }
  }

  if (lastDeletedBatchSnapshotId.value && !isExpired(lastDeletedBatchExpireAt.value)) {
    payload.batch = {
      snapshotId: String(lastDeletedBatchSnapshotId.value || '').trim(),
      count: toPositiveInteger(lastDeletedBatchCount.value, 0),
      expireAt: toPositiveInteger(lastDeletedBatchExpireAt.value, 0),
    }
  }

  try {
    if (Object.keys(payload).length > 0) {
      window.sessionStorage.setItem(undoHintStorageKey.value, JSON.stringify(payload))
      return
    }
    window.sessionStorage.removeItem(undoHintStorageKey.value)
  } catch (error) {
    // ignore storage errors
  }
}

function restoreUndoHintState() {
  let parsed = {}
  try {
    const raw = window.sessionStorage.getItem(undoHintStorageKey.value)
    const next = raw ? JSON.parse(raw) : {}
    parsed = next && typeof next === 'object' && !Array.isArray(next) ? next : {}
  } catch (error) {
    parsed = {}
  }

  const single = parsed.single && typeof parsed.single === 'object' ? parsed.single : {}
  const singleSnapshotId = String(single.snapshotId || '').trim()
  const singleQuestionId = String(single.questionId || '').trim()
  const singleExpireAt = toPositiveInteger(single.expireAt, 0)
  if (singleSnapshotId && !isExpired(singleExpireAt)) {
    lastDeletedQuestionSnapshotId.value = singleSnapshotId
    lastDeletedQuestionId.value = singleQuestionId
    lastDeletedQuestionExpireAt.value = singleExpireAt
  } else {
    lastDeletedQuestionSnapshotId.value = ''
    lastDeletedQuestionId.value = ''
    lastDeletedQuestionExpireAt.value = 0
  }

  const batch = parsed.batch && typeof parsed.batch === 'object' ? parsed.batch : {}
  const batchSnapshotId = String(batch.snapshotId || '').trim()
  const batchCount = toPositiveInteger(batch.count, 0)
  const batchExpireAt = toPositiveInteger(batch.expireAt, 0)
  if (batchSnapshotId && !isExpired(batchExpireAt)) {
    lastDeletedBatchSnapshotId.value = batchSnapshotId
    lastDeletedBatchCount.value = batchCount
    lastDeletedBatchExpireAt.value = batchExpireAt
  } else {
    lastDeletedBatchSnapshotId.value = ''
    lastDeletedBatchCount.value = 0
    lastDeletedBatchExpireAt.value = 0
  }

  persistUndoHintState()
}

function createQuestionFilters() {
  return {
    keyword: '',
    examCategoryCode: '',
    jointExamGroupCode: '',
    subjectCode: '',
    status: '',
  }
}

function createQuestionPagination() {
  return {
    page: 1,
    size: 10,
    total: 0,
  }
}

const {
  rows: questionRows,
  loading,
  filters,
  pagination,
  loadRows: loadQuestionList,
  resetFilters,
  handlePageChange: tableHandlePageChange,
  handlePageSizeChange: tableHandlePageSizeChange,
} = useTable({
  createInitialFilters: createQuestionFilters,
  createInitialPagination: createQuestionPagination,
  async fetchPage({ filters: currentFilters, pagination: currentPagination }) {
    const requestPayload = {
      page: currentPagination.page,
      size: currentPagination.size,
      questionIds: scopedQuestionIds.value.join(','),
      keyword: String(currentFilters.keyword || '').trim(),
      examCategoryCode: String(currentFilters.examCategoryCode || '').trim(),
      jointExamGroupCode: String(currentFilters.jointExamGroupCode || '').trim(),
      subjectCode: String(currentFilters.subjectCode || '').trim(),
      status: String(currentFilters.status || '').trim(),
    }
    const primaryPage = await fetchQuestionList(requestPayload)
    const primaryItems = Array.isArray(primaryPage?.items) ? primaryPage.items : []
    if (primaryItems.length > 0) {
      fallbackSearchNotice.value = ''
      return primaryPage
    }

    const shouldRunRelaxedScopeFallback = (
      !scopedQuestionIds.value.length
      && Boolean(requestPayload.subjectCode)
      && (Boolean(requestPayload.examCategoryCode) || Boolean(requestPayload.jointExamGroupCode))
    )
    if (!shouldRunRelaxedScopeFallback) {
      fallbackSearchNotice.value = ''
      return primaryPage
    }

    const relaxedPage = await fetchQuestionList({
      ...requestPayload,
      examCategoryCode: '',
      jointExamGroupCode: '',
    })
    const relaxedItems = Array.isArray(relaxedPage?.items) ? relaxedPage.items : []
    if (relaxedItems.length > 0) {
      fallbackSearchNotice.value = '当前筛选范围未命中，已自动展示同科目下匹配关键词的题目。'
      return relaxedPage
    }

    fallbackSearchNotice.value = ''
    return primaryPage
  },
  async onLoaded(rows) {
    errorMessage.value = ''
    if (scopedQuestionIds.value.length === 1 && rows.length === 1) {
      await loadDetailDrawerData(String(rows[0]?.id || ''))
      detailDrawerVisible.value = true
    }
  },
  onError(error) {
    errorMessage.value = error?.response?.data?.message || error?.message || '题库数据加载失败'
  },
})

const hasExecutedFilterSearch = ref(false)

const filterModel = computed({
  get() {
    return {
      keyword: filters.keyword,
      examCategoryCode: filters.examCategoryCode,
      jointExamGroupCode: filters.jointExamGroupCode,
      subjectCode: filters.subjectCode,
      status: filters.status,
    }
  },
  set(value) {
    filters.keyword = String(value?.keyword || '')
    filters.examCategoryCode = String(value?.examCategoryCode || '')
    filters.jointExamGroupCode = String(value?.jointExamGroupCode || '')
    filters.subjectCode = String(value?.subjectCode || '')
    filters.status = String(value?.status || '')
  },
})

function hasFilterCondition(value) {
  const model = value && typeof value === 'object' ? value : {}
  return [
    String(model.keyword || '').trim(),
    String(model.examCategoryCode || '').trim(),
    String(model.jointExamGroupCode || '').trim(),
    String(model.subjectCode || '').trim(),
    String(model.status || '').trim(),
  ].some((item) => Boolean(item))
}

function clearQuestionResults() {
  questionRows.value = []
  pagination.total = 0
}

const examCategoryOptions = computed(() => userStore.availableExamCategories)
const scopeLabelMaps = computed(() => buildContentLabelMaps(userStore.availableExamCategories))
const resolveExamCategoryLabel = (code) => resolveContentLabel(scopeLabelMaps.value.examCategoryNameMap, code)
const resolveJointExamGroupLabel = (code) => resolveContentLabel(scopeLabelMaps.value.jointExamGroupNameMap, code)
const isSelectionMode = computed(() => String(route.query.mode || '').trim() === 'selection')
const shouldDisplayQueryResults = computed(() =>
  isSelectionMode.value || scopedQuestionIds.value.length > 0 || hasExecutedFilterSearch.value,
)
const selectedQuestionIds = computed(() => Object.keys(selectedQuestionMap.value))
const selectedQuestionCount = computed(() => selectedQuestionIds.value.length)
const selectedQuestionRows = computed(() =>
  Object.values(selectedQuestionMap.value || {}).map((item) => ({
    id: String(item?.id || '').trim(),
    stem: String(item?.stem || ''),
    type: String(item?.type || ''),
    knowledgeId: String(item?.knowledgeId || ''),
    latestStatus: String(item?.latestStatus || item?.status || '').trim(),
    userId: String(item?.userId || '').trim(),
  })),
)
const batchTransitionActions = computed(() => {
  if (!selectedQuestionRows.value.length || isSelectionMode.value) {
    return []
  }
  const actionBuckets = selectedQuestionRows.value.map((row) => resolveTransitionActions(row))
  const firstRowActions = actionBuckets[0] || []
  return firstRowActions.filter((candidate) =>
    actionBuckets.every((actions) => actions.some((item) => item.targetStatus === candidate.targetStatus)),
  )
})
const scopedQuestionIds = computed(() => parseScopedQuestionIdsFromQuery())
const scopedSourceTaskId = computed(() => String(route.query.sourceTaskId || '').trim())
const scopedQuestionAlertTitle = computed(() => {
  if (!scopedQuestionIds.value.length) {
    return ''
  }
  const task_suffix = scopedSourceTaskId.value ? `，来源任务 ${scopedSourceTaskId.value}` : ''
  return `当前仅展示导入任务关联的 ${scopedQuestionIds.value.length} 道题目${task_suffix}。`
})

function parseScopedQuestionIdsFromQuery() {
  const raw_ids = String(route.query.questionIds || route.query.question_ids || '').trim()
  if (!raw_ids) {
    return []
  }
  return Array.from(
    new Set(
      raw_ids
        .split(',')
        .map((item) => String(item || '').trim())
        .filter((item) => Boolean(item)),
    ),
  )
}

function parseTargetKnowledgeIdsFromQuery() {
  const raw_ids = String(route.query.targetKnowledgeIds || '').trim()
  if (!raw_ids) {
    return []
  }
  return Array.from(
    new Set(
      raw_ids
        .split(',')
        .map((item) => String(item || '').trim())
        .filter((item) => Boolean(item)),
    ),
  )
}

function parseTargetKnowledgeMapFromQuery() {
  const raw_map = route.query.targetKnowledgeMap
  if (!raw_map) {
    return {}
  }
  try {
    const parsed = JSON.parse(String(raw_map))
    if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
      return {}
    }
    const normalized = {}
    Object.keys(parsed).forEach((key) => {
      const normalized_key = String(key || '').trim()
      if (!normalized_key) {
        return
      }
      normalized[normalized_key] = String(parsed[key] || normalized_key).trim() || normalized_key
    })
    return normalized
  } catch (error) {
    return {}
  }
}

function parseTargetWeightMapFromQuery() {
  const raw_map = route.query.targetWeightMap
  if (!raw_map) {
    return {}
  }
  try {
    const parsed = JSON.parse(String(raw_map))
    if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
      return {}
    }
    const normalized = {}
    Object.keys(parsed).forEach((key) => {
      const normalized_key = String(key || '').trim()
      if (!normalized_key) {
        return
      }
      const numeric_value = Number(parsed[key])
      if (!Number.isFinite(numeric_value)) {
        return
      }
      normalized[normalized_key] = Math.min(1, Math.max(0, numeric_value))
    })
    return normalized
  } catch (error) {
    return {}
  }
}

async function loadSelectionTargetWeightMap() {
  if (!isSelectionMode.value) {
    selectionTargetWeightMap.value = {}
    return
  }

  const query_target_weight_map = parseTargetWeightMapFromQuery()
  if (Object.keys(query_target_weight_map).length) {
    selectionTargetWeightMap.value = query_target_weight_map
    return
  }

  const target_knowledge_ids = parseTargetKnowledgeIdsFromQuery()
  try {
    const response = await paperTargetWeights({
      knowledgeIds: target_knowledge_ids.join(','),
    })
    const payload = response && typeof response === 'object' && 'data' in response ? response.data : response
    const source_map = payload?.targetWeightMap && typeof payload.targetWeightMap === 'object'
      ? payload.targetWeightMap
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
    selectionTargetWeightMap.value = next_map
  } catch (error) {
    selectionTargetWeightMap.value = {}
  }
}

const tableRows = computed(() =>
  questionRows.value.map((questionItem) => {
    const ext = parseExtJson(questionItem.extJson)
    const reviewSummary = ext.reviewSummary && typeof ext.reviewSummary === 'object'
      ? ext.reviewSummary
      : {}

    return {
      id: String(questionItem.id || ''),
      stem: String(questionItem.stem || ''),
      type: String(questionItem.type || ''),
      knowledgeId: String(questionItem.knowledgeId || ''),
      typeLabel: questionTypeLabel(questionItem.type),
      status: String(questionItem.status || ''),
      latestStatus: String(reviewSummary.latestStatus || questionItem.status || ''),
      latestStatusLabel: questionStatusMeta(reviewSummary.latestStatus || questionItem.status).label,
      userId: String(questionItem.userId || ''),
      examCategoryCode: String(ext.examCategoryCode || ''),
      examCategoryLabel: resolveExamCategoryLabel(ext.examCategoryCode),
      jointExamGroupCode:
        String(ext.jointExamGroupCode || '') ||
        (Array.isArray(ext.applicableGroups) ? String(ext.applicableGroups[0] || '') : ''),
      jointExamGroupLabel: resolveJointExamGroupLabel(
        String(ext.jointExamGroupCode || '') ||
        (Array.isArray(ext.applicableGroups) ? String(ext.applicableGroups[0] || '') : ''),
      ),
      subjectCode: String(ext.subjectCode || ''),
      answer: String(questionItem.answer || '').trim(),
      updateTime: String(questionItem.updateTime || ''),
    }
  }),
)

function buildSelectedQuestionEntry(row) {
  return {
    id: String(row?.id || '').trim(),
    stem: String(row?.stem || ''),
    type: String(row?.type || ''),
    knowledgeId: String(row?.knowledgeId || ''),
    latestStatus: String(row?.latestStatus || row?.status || ''),
    userId: String(row?.userId || ''),
    examCategoryCode: String(row?.examCategoryCode || ''),
    jointExamGroupCode: String(row?.jointExamGroupCode || ''),
    subjectCode: String(row?.subjectCode || ''),
    updateTime: String(row?.updateTime || ''),
  }
}

const queryResultRows = computed(() =>
  tableRows.value.map((row, index) => ({
    id: String(row?.id || '').trim(),
    seq: (Math.max(1, Number(pagination.page || 1)) - 1) * Math.max(1, Number(pagination.size || 10)) + index + 1,
    stem: String(row?.stem || '').trim(),
    answer: String(row?.answer || '').trim() || '-',
    checked: Boolean(selectedQuestionMap.value[String(row?.id || '').trim()]),
    row,
  })),
)

const queryResultCheckedCount = computed(() =>
  queryResultRows.value.filter((item) => item.checked).length,
)

const queryResultAllChecked = computed(() =>
  queryResultRows.value.length > 0 && queryResultCheckedCount.value === queryResultRows.value.length,
)

const queryResultIndeterminate = computed(() =>
  queryResultCheckedCount.value > 0 && queryResultCheckedCount.value < queryResultRows.value.length,
)

const detailExtJson = computed(() => parseExtJson(detailQuestion.value?.extJson))

const detailReviewSummary = computed(() => {
  const summary = detailExtJson.value.reviewSummary
  return summary && typeof summary === 'object' ? summary : {}
})

const detailOptions = computed(() => {
  try {
    const options = JSON.parse(String(detailQuestion.value?.optionsJson || '[]'))
    return Array.isArray(options) ? options : []
  } catch (error) {
    return []
  }
})

const detailStatusLabel = computed(() => {
  const status = String(
    detailReviewSummary.value.latestStatus || detailQuestion.value?.status || '',
  ).trim()
  return questionStatusMeta(status).label
})

const detailFixedRows = computed(() => {
  if (!detailQuestion.value) {
    return []
  }

  return [
    { label: '题目ID', value: String(detailQuestion.value.id || '-') },
    { label: '知识点ID', value: String(detailQuestion.value.knowledgeId || '-') },
    { label: '出题人', value: String(detailQuestion.value.userId || '-') },
    { label: '题型', value: questionTypeLabel(detailQuestion.value.type) },
    { label: '当前状态', value: detailStatusLabel.value },
    { label: '创建时间', value: String(detailQuestion.value.createTime || '-') },
    { label: '更新时间', value: String(detailQuestion.value.updateTime || '-') },
  ]
})

const detailExtOverviewRows = computed(() => {
  const ext = detailExtJson.value
  const knowledgeTags = Array.isArray(ext.knowledgeTags) ? ext.knowledgeTags.join(' / ') : ''
  const applicableGroups = Array.isArray(ext.applicableGroups)
    ? ext.applicableGroups.map((groupCode) => resolveJointExamGroupLabel(groupCode)).join(' / ')
    : ''

  return [
    { label: 'subjectId', value: String(ext.subjectId || '-') },
    { label: 'chapter', value: String(ext.chapter || '-') },
    { label: 'difficulty', value: String(ext.difficulty || '-') },
    { label: 'knowledgeTags', value: knowledgeTags || '-' },
    { label: 'examCategoryCode', value: resolveExamCategoryLabel(ext.examCategoryCode) },
    { label: 'jointExamGroupCode', value: resolveJointExamGroupLabel(ext.jointExamGroupCode) },
    { label: 'subjectCode', value: String(ext.subjectCode || '-') },
    { label: 'sourceType', value: String(ext.sourceType || '-') },
    { label: 'policyVersionCode', value: String(ext.policyVersionCode || '-') },
    { label: 'applicableGroups', value: applicableGroups || '-' },
  ]
})

const detailReviewTimeline = computed(() => {
  const normalizedRows = detailReviews.value
    .map((reviewItem) => {
      const ext = parseExtJson(reviewItem?.extJson)
      const fromStatus = String(ext.fromStatus || '').trim()
      const toStatus = String(ext.toStatus || reviewItem?.status || '').trim()

      return {
        id: String(reviewItem?.id || ''),
        reviewerUserId: String(reviewItem?.reviewerUserId || '-'),
        createTime: String(reviewItem?.createTime || '-'),
        fromStatus,
        toStatus,
        fromStatusLabel: questionStatusMeta(fromStatus).label,
        toStatusLabel: questionStatusMeta(toStatus).label,
        reviewReason: String(ext.reviewReason || '-'),
        actorRole: String(ext.actorRole || '-'),
      }
    })
    .sort((leftItem, rightItem) => {
      const leftTime = String(leftItem.createTime || '')
      const rightTime = String(rightItem.createTime || '')
      if (leftTime === rightTime) {
        return String(leftItem.id || '').localeCompare(String(rightItem.id || ''))
      }
      return leftTime.localeCompare(rightTime)
    })

  return normalizedRows
})

const detailRejectedTimeline = computed(() =>
  detailReviewTimeline.value.filter((reviewItem) => reviewItem.toStatus === 'REJECTED'),
)

const detailTransitionActions = computed(() => {
  if (!detailQuestion.value) {
    return []
  }

  const ext = parseExtJson(detailQuestion.value.extJson)
  const reviewSummary = ext.reviewSummary && typeof ext.reviewSummary === 'object'
    ? ext.reviewSummary
    : {}

  return resolveTransitionActions({
    id: String(detailQuestion.value.id || ''),
    userId: String(detailQuestion.value.userId || ''),
    latestStatus: String(reviewSummary.latestStatus || detailQuestion.value.status || ''),
  })
})

function statusTagType(status) {
  return questionStatusMeta(status).type
}

function quickFilterPendingReview() {
  filterModel.value = {
    ...filterModel.value,
    status: 'REVIEW_PENDING',
  }
  handleSearch(filterModel.value)
}

function syncSelectionForVisibleRows() {
  nextTick(() => {
    const tableRef = questionTableRef.value
    if (!tableRef || typeof tableRef.clearSelection !== 'function') {
      return
    }

    syncingTableSelection.value = true
    tableRef.clearSelection()
    tableRows.value.forEach((row) => {
      if (selectedQuestionMap.value[row.id]) {
        tableRef.toggleRowSelection(row, true)
      }
    })
    nextTick(() => {
      syncingTableSelection.value = false
    })
  })
}

function handleSelectionChange(selectedRows) {
  if (syncingTableSelection.value) {
    return
  }
  const normalizedRows = Array.isArray(selectedRows) ? selectedRows : []
  if (isSelectionMode.value) {
    const nextSelectedMap = { ...selectedQuestionMap.value }
    const currentPageIds = new Set(
      tableRows.value
        .map((row) => String(row?.id || '').trim())
        .filter((id) => Boolean(id)),
    )
    const selectedIds = new Set(
      normalizedRows
        .map((row) => String(row?.id || '').trim())
        .filter((id) => Boolean(id)),
    )
    currentPageIds.forEach((id) => {
      if (!selectedIds.has(id)) {
        delete nextSelectedMap[id]
      }
    })
    normalizedRows.forEach((row) => {
      const id = String(row?.id || '').trim()
      if (!id) {
        return
      }
      nextSelectedMap[id] = buildSelectedQuestionEntry(row)
    })
    selectedQuestionMap.value = nextSelectedMap
    return
  }

  const nextSelectedMap = {}
  normalizedRows.forEach((row) => {
    const id = String(row?.id || '').trim()
    if (!id) {
      return
    }
    nextSelectedMap[id] = buildSelectedQuestionEntry(row)
  })
  selectedQuestionMap.value = nextSelectedMap
}

function handleQueryResultSelectAllChange(checked) {
  const shouldSelect = Boolean(checked)
  const nextSelectedMap = {}
  if (shouldSelect) {
    queryResultRows.value.forEach((item) => {
      const id = String(item?.id || '').trim()
      if (!id) {
        return
      }
      nextSelectedMap[id] = buildSelectedQuestionEntry(item.row)
    })
  }
  selectedQuestionMap.value = nextSelectedMap
  syncSelectionForVisibleRows()
}

function handleQueryResultRowCheckedChange(item, checked) {
  const id = String(item?.id || '').trim()
  if (!id) {
    return
  }
  const nextSelectedMap = {}
  queryResultRows.value.forEach((rowItem) => {
    const rowId = String(rowItem?.id || '').trim()
    if (!rowId) {
      return
    }
    const shouldKeepChecked = rowId === id ? Boolean(checked) : Boolean(rowItem?.checked)
    if (!shouldKeepChecked) {
      return
    }
    nextSelectedMap[rowId] = buildSelectedQuestionEntry(rowItem?.row)
  })
  selectedQuestionMap.value = nextSelectedMap
  syncSelectionForVisibleRows()
}

function clearSelectedQuestions() {
  selectedQuestionMap.value = {}
  if (questionTableRef.value && typeof questionTableRef.value.clearSelection === 'function') {
    questionTableRef.value.clearSelection()
  }
}

function handleCompleteSelection() {
  if (!selectedQuestionCount.value) {
    ElMessage.warning('请先至少勾选一道题目。')
    return
  }

  try {
    const target_knowledge_ids = parseTargetKnowledgeIdsFromQuery()
    const target_knowledge_map = parseTargetKnowledgeMapFromQuery()
    const query_target_weight_map = parseTargetWeightMapFromQuery()
    const source_target_weight_map = Object.keys(query_target_weight_map).length
      ? query_target_weight_map
      : selectionTargetWeightMap.value
    const scoped_knowledge_ids = target_knowledge_ids.length
      ? target_knowledge_ids
      : Array.from(
        new Set(
          Object.values(selectedQuestionMap.value)
            .map((item) => String(item?.knowledgeId || '').trim())
            .filter((id) => Boolean(id)),
        ),
      )
    const target_weight_map = {}
    scoped_knowledge_ids.forEach((knowledge_id) => {
      const normalized_id = String(knowledge_id || '').trim()
      if (!normalized_id) {
        return
      }
      const numeric_value = Number(source_target_weight_map[normalized_id])
      if (!Number.isFinite(numeric_value)) {
        return
      }
      target_weight_map[normalized_id] = Math.min(1, Math.max(0, numeric_value))
    })
    const first_selected_question = Object.values(selectedQuestionMap.value)[0] || {}
    const draft_scope = resolveManualDraftScope(
      {
        exam_category_code: route.query.examCategoryCode || route.query.exam_category_code || filterModel.value.examCategoryCode || first_selected_question.examCategoryCode,
        joint_exam_group_code: route.query.jointExamGroupCode || route.query.joint_exam_group_code || filterModel.value.jointExamGroupCode || first_selected_question.jointExamGroupCode,
        subject_code: route.query.subjectCode || route.query.subject_code || filterModel.value.subjectCode || first_selected_question.subjectCode,
        policy_version: route.query.policyVersion || route.query.policy_version || 'HB_ZSB_2026',
      },
      {},
    )
    sessionStorage.setItem(
      'qbManualPaperSelectionDraft',
      JSON.stringify({
        questionIds: selectedQuestionIds.value,
        targetKnowledgeIds: target_knowledge_ids.length ? target_knowledge_ids : scoped_knowledge_ids,
        targetKnowledgeMap: target_knowledge_map,
        targetWeightMap: target_weight_map,
        examCategoryCode: draft_scope.examCategoryCode,
        jointExamGroupCode: draft_scope.jointExamGroupCode,
        subjectCode: draft_scope.subjectCode,
        exam_category_code: draft_scope.exam_category_code,
        joint_exam_group_code: draft_scope.joint_exam_group_code,
        subject_code: draft_scope.subject_code,
        policyVersion: draft_scope.policyVersion || 'HB_ZSB_2026',
        policy_version: draft_scope.policy_version || 'HB_ZSB_2026',
        scope_path: draft_scope.scope_path,
        questions: Object.values(selectedQuestionMap.value).map((item) => ({
          id: String(item?.id || ''),
          stem: String(item?.stem || ''),
          type: String(item?.type || ''),
          knowledgeId: String(item?.knowledgeId || ''),
          score: 5,
        })),
      }),
    )
  } catch (error) {
    // ignore session storage errors
  }

  ElMessage.success(`已完成选题，共选择 ${selectedQuestionCount.value} 道题。`)
  router.push('/teacher/papers')
}

function prettyJson(value) {
  return JSON.stringify(value, null, 2)
}

function unwrapData(response) {
  if (response && typeof response === 'object' && 'data' in response) {
    return response.data
  }
  return response
}

async function loadContentBaselineOptions() {
  try {
    const baselineData = await fetchContentBaseline()
    const categories = Array.isArray(baselineData?.examCategories) ? baselineData.examCategories : []
    const nextSubjectCodeOptions = []

    categories.forEach((examCategoryItem) => {
      const examCategoryCode = String(examCategoryItem?.examCategoryCode || '').trim()
      const jointExamGroups = Array.isArray(examCategoryItem?.jointExamGroups)
        ? examCategoryItem.jointExamGroups
        : []

      jointExamGroups.forEach((jointExamGroupItem) => {
        const jointExamGroupCode = String(jointExamGroupItem?.jointExamGroupCode || '').trim()
        const subjects = Array.isArray(jointExamGroupItem?.subjects)
          ? jointExamGroupItem.subjects
          : []

        subjects.forEach((subjectItem) => {
          const subjectCode = String(subjectItem?.subjectCode || '').trim()
          if (!subjectCode) {
            return
          }

          nextSubjectCodeOptions.push({
            subjectCode,
            subjectName: String(subjectItem?.subjectName || subjectCode),
            subjectType: String(subjectItem?.subjectType || ''),
            examCategoryCode,
            jointExamGroupCode,
          })
        })
      })
    })

    subjectCodeOptions.value = nextSubjectCodeOptions
  } catch (error) {
    subjectCodeOptions.value = []
  }
}

function clearScopedQuestionFilter() {
  const next_query = { ...route.query }
  delete next_query.questionIds
  delete next_query.question_ids
  delete next_query.sourceTaskId
  delete next_query.source
  router.replace({
    name: 'teacherQuestions',
    query: next_query,
  })
}

function handleSearch(nextFilter) {
  filterModel.value = nextFilter || {}
  if (!isSelectionMode.value && !scopedQuestionIds.value.length && !hasFilterCondition(filterModel.value)) {
    hasExecutedFilterSearch.value = false
    fallbackSearchNotice.value = ''
    clearQuestionResults()
    ElMessage.warning('请至少选择一个筛选条件后再查询。')
    return
  }
  hasExecutedFilterSearch.value = true
  pagination.page = 1
  fallbackSearchNotice.value = ''
  if (!isSelectionMode.value) {
    clearSelectedQuestions()
  }
  loadQuestionList()
}

function handleReset() {
  resetFilters()
  hasExecutedFilterSearch.value = false
  pagination.page = 1
  fallbackSearchNotice.value = ''
  clearQuestionResults()
}

function handleClearQueryResultList() {
  clearSelectedQuestions()
  fallbackSearchNotice.value = ''
  pagination.page = 1
  hasExecutedFilterSearch.value = false
  clearQuestionResults()
  if (!isSelectionMode.value && scopedQuestionIds.value.length > 0) {
    clearScopedQuestionFilter()
  }
  ElMessage.success('查询结果列表已清空。')
}

function handleQuestionCreated() {
  if (!shouldDisplayQueryResults.value) {
    return
  }
  pagination.page = 1
  loadQuestionList()
}

function handleResultPageChange(nextPage) {
  if (!shouldDisplayQueryResults.value) {
    return
  }
  if (!isSelectionMode.value) {
    clearSelectedQuestions()
  }
  tableHandlePageChange(nextPage)
}

function handleResultPageSizeChange(nextSize) {
  if (!shouldDisplayQueryResults.value) {
    return
  }
  if (!isSelectionMode.value) {
    clearSelectedQuestions()
  }
  tableHandlePageSizeChange(nextSize)
}

function resolveTransitionActions(row) {
  const actions = []
  const isOwner = row.userId === userStore.userId

  if (row.latestStatus === 'DRAFT' && isOwner && canTransitionQuestionStatus(row.latestStatus, 'REVIEW_PENDING')) {
    actions.push({ label: '提审', targetStatus: 'REVIEW_PENDING', type: 'warning' })
  }

  if (row.latestStatus === 'QA_IN_PROGRESS' && !isOwner && canTransitionQuestionStatus(row.latestStatus, 'REVIEW_PENDING')) {
    actions.push({ label: '提审', targetStatus: 'REVIEW_PENDING', type: 'warning' })
  }

  if (row.latestStatus === 'REVIEW_PENDING' && !isOwner) {
    if (canTransitionQuestionStatus(row.latestStatus, 'PUBLISHED')) {
      actions.push({ label: '通过', targetStatus: 'PUBLISHED', type: 'success' })
    }
    if (canTransitionQuestionStatus(row.latestStatus, 'REJECTED')) {
      actions.push({ label: '驳回', targetStatus: 'REJECTED', type: 'danger' })
    }
  }

  if (row.latestStatus === 'REJECTED' && isOwner && canTransitionQuestionStatus(row.latestStatus, 'DRAFT')) {
    actions.push({ label: '退回草稿', targetStatus: 'DRAFT', type: 'info' })
  }

  return actions
}

async function loadDetailDrawerData(questionId) {
  if (!questionId) {
    detailQuestion.value = null
    detailReviews.value = []
    return
  }

  detailLoading.value = true

  try {
    const [questionData, reviewRows] = await Promise.all([
      fetchQuestionDetail(questionId),
      fetchQuestionReviews(questionId),
    ])

    detailQuestion.value = questionData || null
    detailReviews.value = Array.isArray(reviewRows) ? reviewRows : []
  } catch (error) {
    detailQuestion.value = null
    detailReviews.value = []
    ElMessage.error(error?.response?.data?.message || error?.message || '题目详情加载失败')
  } finally {
    detailLoading.value = false
  }
}

async function openDetailDrawer(row) {
  const questionId = String(row?.id || '').trim()
  if (!questionId) {
    return
  }

  detailDrawerVisible.value = true
  await loadDetailDrawerData(questionId)
}

function closeDetailDrawer() {
  detailQuestion.value = null
  detailReviews.value = []
}

async function handleTransition(row, action) {
  if (!row?.id || !action?.targetStatus) {
    return
  }

  const payload = {}

  if (action.targetStatus === 'REJECTED') {
    const promptResult = await ElMessageBox.prompt('请填写驳回原因', '驳回题目', {
      confirmButtonText: '确认驳回',
      cancelButtonText: '取消',
      inputPlaceholder: '请输入驳回原因',
      inputValidator: (value) => (String(value || '').trim() ? true : '驳回原因不能为空'),
    }).catch(() => null)

    if (!promptResult) {
      return
    }

    payload.reason = String(promptResult.value || '').trim()
  }

  transitioningQuestionId.value = row.id

  try {
    await updateQuestionStatus(row.id, action.targetStatus, payload)
    ElMessage.success(`题目 ${row.id} 已流转到 ${questionStatusMeta(action.targetStatus).label}`)
    await loadQuestionList()

    if (detailDrawerVisible.value && String(detailQuestion.value?.id || '') === String(row.id || '')) {
      await loadDetailDrawerData(String(row.id || ''))
    }
  } catch (error) {
    ElMessage.error(resolveApiErrorMessage(error, '状态流转失败'))
  } finally {
    transitioningQuestionId.value = ''
  }
}

async function handleBatchTransition(action) {
  const questionIds = selectedQuestionRows.value.map((item) => String(item?.id || '').trim()).filter(Boolean)
  if (!questionIds.length || !action?.targetStatus) {
    ElMessage.warning('请先勾选要批量操作的题目。')
    return
  }
  const payload = {
    questionIds,
    targetStatus: String(action.targetStatus || '').trim(),
  }
  if (payload.targetStatus === 'REJECTED') {
    const promptResult = await ElMessageBox.prompt('请填写批量驳回原因', '批量驳回题目', {
      confirmButtonText: '确认驳回',
      cancelButtonText: '取消',
      inputPlaceholder: '请输入统一驳回原因',
      inputValidator: (value) => (String(value || '').trim() ? true : '驳回原因不能为空'),
    }).catch(() => null)
    if (!promptResult) {
      return
    }
    payload.reason = String(promptResult.value || '').trim()
  }

  batchActing.value = true
  try {
    const result = unwrapData(await transitionStatusBatch(payload)) || {}
    ElMessage.success(`已批量更新 ${Number(result?.updatedCount || questionIds.length)} 道题目。`)
    clearSelectedQuestions()
    await loadQuestionList()
    if (detailDrawerVisible.value && detailQuestion.value?.id) {
      await loadDetailDrawerData(String(detailQuestion.value.id || ''))
    }
  } catch (error) {
    ElMessage.error(resolveApiErrorMessage(error, '批量状态流转失败'))
  } finally {
    batchActing.value = false
  }
}

async function handleDeleteQuestion(row) {
  const questionId = String(row?.id || '').trim()
  if (!questionId) {
    return
  }
  try {
    await ElMessageBox.confirm(
      `确认删除题目「${questionId}」吗？`,
      '删除题目',
      {
        type: 'warning',
        confirmButtonText: '确认删除',
        cancelButtonText: '取消',
      },
    )
  } catch {
    return
  }

  deletingQuestionId.value = questionId
  try {
    const result = unwrapData(await deleteQuestion(questionId)) || {}
    lastDeletedQuestionSnapshotId.value = String(result?.undoSnapshotId || '').trim()
    lastDeletedQuestionId.value = questionId
    lastDeletedQuestionExpireAt.value =
      Date.now() + toPositiveInteger(result?.undoExpireSec, UNDO_DEFAULT_EXPIRE_SEC) * 1000
    persistUndoHintState()
    ElMessage.success('题目已删除，可在 10 分钟内恢复。')
    clearSelectedQuestions()
    if (detailDrawerVisible.value && String(detailQuestion.value?.id || '') === questionId) {
      detailDrawerVisible.value = false
      closeDetailDrawer()
    }
    await loadQuestionList()
  } catch (error) {
    ElMessage.error(resolveApiErrorMessage(error, '删除题目失败'))
  } finally {
    deletingQuestionId.value = ''
  }
}

async function handleRestoreDeletedQuestion() {
  if (!lastDeletedQuestionSnapshotId.value) {
    return
  }
  deletingQuestionId.value = lastDeletedQuestionId.value || '__restore__'
  try {
    await restoreDeletedQuestion(lastDeletedQuestionSnapshotId.value)
    ElMessage.success('题目已恢复。')
    lastDeletedQuestionSnapshotId.value = ''
    lastDeletedQuestionId.value = ''
    lastDeletedQuestionExpireAt.value = 0
    persistUndoHintState()
    await loadQuestionList()
  } catch (error) {
    ElMessage.error(resolveApiErrorMessage(error, '恢复题目失败'))
  } finally {
    deletingQuestionId.value = ''
  }
}

async function handleBatchDelete() {
  const questionIds = selectedQuestionRows.value.map((item) => String(item?.id || '').trim()).filter(Boolean)
  if (!questionIds.length) {
    ElMessage.warning('请先勾选要删除的题目。')
    return
  }
  try {
    await ElMessageBox.confirm(
      `确认批量删除已勾选的 ${questionIds.length} 道题目吗？`,
      '批量删除题目',
      {
        type: 'warning',
        confirmButtonText: '确认删除',
        cancelButtonText: '取消',
      },
    )
  } catch {
    return
  }

  batchActing.value = true
  try {
    const result = unwrapData(await deleteQuestionsBatch({ questionIds })) || {}
    lastDeletedBatchSnapshotId.value = String(result?.undoSnapshotId || '').trim()
    lastDeletedBatchCount.value = questionIds.length
    lastDeletedBatchExpireAt.value =
      Date.now() + toPositiveInteger(result?.undoExpireSec, UNDO_DEFAULT_EXPIRE_SEC) * 1000
    persistUndoHintState()
    ElMessage.success(`已批量删除 ${questionIds.length} 道题目，可在 10 分钟内恢复。`)
    clearSelectedQuestions()
    await loadQuestionList()
  } catch (error) {
    ElMessage.error(resolveApiErrorMessage(error, '批量删除失败'))
  } finally {
    batchActing.value = false
  }
}

async function handleRestoreDeletedBatch() {
  if (!lastDeletedBatchSnapshotId.value) {
    return
  }
  batchActing.value = true
  try {
    const result = unwrapData(await restoreDeletedQuestionsBatch(lastDeletedBatchSnapshotId.value)) || {}
    ElMessage.success(`已恢复 ${Number(result?.restoredCount || 0)} 道题目。`)
    lastDeletedBatchSnapshotId.value = ''
    lastDeletedBatchCount.value = 0
    lastDeletedBatchExpireAt.value = 0
    persistUndoHintState()
    await loadQuestionList()
  } catch (error) {
    ElMessage.error(resolveApiErrorMessage(error, '批量恢复失败'))
  } finally {
    batchActing.value = false
  }
}

function resetEditForm() {
  resetEditFormState()
}

async function openEditDialog(row) {
  if (!row?.id) {
    return
  }

  try {
    const detail = await fetchQuestionDetail(row.id)

    let parsedOptions = []
    try {
      const optionsData = JSON.parse(String(detail.optionsJson || '[]'))
      parsedOptions = Array.isArray(optionsData) ? optionsData : []
    } catch (error) {
      parsedOptions = []
    }

    const nextExtJsonObject = parseExtJson(detail.extJson)
    patchEditForm({
      id: String(detail.id || ''),
      knowledgeId: String(detail.knowledgeId || ''),
      userId: String(detail.userId || ''),
      type: String(detail.type || ''),
      stem: String(detail.stem || ''),
      optionsJson: JSON.stringify(parsedOptions, null, 2),
      answer: String(detail.answer || ''),
      status: String(detail.status || ''),
      extJsonObject: nextExtJsonObject,
      extJsonText: prettyJson(nextExtJsonObject),
      createTime: String(detail.createTime || ''),
      updateTime: String(detail.updateTime || ''),
    })

    editDialogVisible.value = true
  } catch (error) {
    ElMessage.error(error?.response?.data?.message || error?.message || '题目详情加载失败')
  }
}

async function saveQuestionEdit() {
  editSaving.value = true

  try {
    const parsedOptions = JSON.parse(String(editForm.optionsJson || '[]'))
    const parsedExtCandidate = JSON.parse(String(editForm.extJsonText || '{}'))
    const parsedExt = parsedExtCandidate && typeof parsedExtCandidate === 'object'
      ? parsedExtCandidate
      : {}
    editForm.extJsonObject = parsedExt
    const normalizedOptions = Array.isArray(parsedOptions) ? parsedOptions : []
    const normalizedExt = parsedExt && typeof parsedExt === 'object' ? parsedExt : {}

    const payload = {
      content: String(editForm.stem || '').trim(),
      type: String(editForm.type || '').trim(),
      options: normalizedOptions,
      answer: String(editForm.answer || '').trim(),
      status: String(editForm.status || '').trim(),
      ext_json: normalizedExt,
    }
    if (editForm.knowledgeId) payload.knowledge_points = [String(editForm.knowledgeId || '').trim()]
    if (editForm.userId) payload.user_id = String(editForm.userId || '').trim()
    if (editForm.createTime) payload.create_time = String(editForm.createTime || '').trim()
    if (editForm.updateTime) payload.update_time = String(editForm.updateTime || '').trim()
    const extTitle = normalizedExt.title
    const extSubjectCode = normalizedExt.subject_code ?? normalizedExt.subjectCode
    const extSubjectType = normalizedExt.subject_type ?? normalizedExt.subjectType
    const extJointExamGroupCode = normalizedExt.joint_exam_group_code ?? normalizedExt.jointExamGroupCode
    const extModuleCode = normalizedExt.module_code ?? normalizedExt.moduleCode
    const extSourceType = normalizedExt.source_type ?? normalizedExt.sourceType
    const extDifficulty = normalizedExt.difficulty
    const extScore = normalizedExt.score

    if (extTitle) payload.title = String(extTitle || '').trim()
    if (extSubjectCode) payload.subject_code = String(extSubjectCode || '').trim()
    if (extSubjectType !== undefined) payload.subject_type = String(extSubjectType || '').trim()
    if (extJointExamGroupCode !== undefined) {
      payload.joint_exam_group_code = String(extJointExamGroupCode || '').trim()
    }
    if (extModuleCode !== undefined) payload.module_code = String(extModuleCode || '').trim()
    if (extSourceType !== undefined) payload.source_type = String(extSourceType || '').trim()
    if (extDifficulty !== undefined) payload.difficulty = String(extDifficulty || '').trim()
    if (extScore !== undefined && extScore !== null && extScore !== '') {
      payload.score = Number(extScore)
    }

    await updateQuestionData(editForm.id, payload)
    ElMessage.success('题目已更新')
    editDialogVisible.value = false
    await loadQuestionList()

    if (detailDrawerVisible.value && String(detailQuestion.value?.id || '') === String(editForm.id || '')) {
      await loadDetailDrawerData(String(editForm.id || ''))
    }
  } catch (error) {
    ElMessage.error(error?.response?.data?.message || error?.message || '题目更新失败')
  } finally {
    editSaving.value = false
  }
}

onMounted(async () => {
  restoreUndoHintState()
  await loadSelectionTargetWeightMap()
  await loadContentBaselineOptions()
  if (scopedQuestionIds.value.length > 0 || isSelectionMode.value) {
    hasExecutedFilterSearch.value = true
    await loadQuestionList()
    return
  }
  clearQuestionResults()
})

watch(
  () => undoHintStorageKey.value,
  () => {
    restoreUndoHintState()
  },
)

watch(
  tableRows,
  () => {
    syncSelectionForVisibleRows()
  },
)

watch(
  isSelectionMode,
  (enabled) => {
    if (enabled) {
      syncSelectionForVisibleRows()
      return
    }
    clearSelectedQuestions()
  },
)

watch(
  () => [route.query.questionIds, route.query.question_ids, route.query.sourceTaskId].join('|'),
  () => {
    if (scopedQuestionIds.value.length > 0) {
      hasExecutedFilterSearch.value = true
      pagination.page = 1
      loadQuestionList()
      return
    }
    if (isSelectionMode.value) {
      pagination.page = 1
      loadQuestionList()
      return
    }
    hasExecutedFilterSearch.value = false
    fallbackSearchNotice.value = ''
    clearQuestionResults()
  },
)
</script>

<template>
  <section class="page-shell" :class="{ 'selection-mode': isSelectionMode }">
    <header>
      <h3>题库管理</h3>
      <p v-if="isSelectionMode">当前为手动组卷选题模式，请勾选题目并点击“完成选题”。</p>
      <p v-else>已切换真实接口联调，支持高级筛选、编辑、状态流转与审核流水线详情抽屉。</p>
    </header>

    <el-alert
      v-if="errorMessage"
      type="error"
      :title="errorMessage"
      show-icon
      :closable="false"
    />

    <el-alert
      v-if="scopedQuestionIds.length"
      type="info"
      :title="scopedQuestionAlertTitle"
      show-icon
      :closable="false"
    >
      <template #default>
        <div class="scoped-question-alert">
          <span>你可以直接查看、编辑或审核这批刚入库的题目。</span>
          <el-button link type="primary" @click="clearScopedQuestionFilter">退出本次导入范围</el-button>
        </div>
      </template>
    </el-alert>

    <el-alert
      v-if="lastDeletedQuestionSnapshotId"
      type="warning"
      show-icon
      :closable="false"
      :title="`题目 ${lastDeletedQuestionId || ''} 已删除，可在 10 分钟内恢复。`"
    >
      <template #default>
        <el-button
          type="primary"
          plain
          :loading="deletingQuestionId === (lastDeletedQuestionId || '__restore__')"
          @click="handleRestoreDeletedQuestion"
        >
          撤销删除
        </el-button>
      </template>
    </el-alert>

    <el-alert
      v-if="lastDeletedBatchSnapshotId"
      type="info"
      show-icon
      :closable="false"
      :title="`最近一批已删除 ${lastDeletedBatchCount} 道题目，可在 10 分钟内恢复。`"
    >
      <template #default>
        <el-button type="primary" plain :loading="batchActing" @click="handleRestoreDeletedBatch">
          恢复最近批次
        </el-button>
      </template>
    </el-alert>

    <QuestionUpload v-if="!isSelectionMode" @created="handleQuestionCreated" />

    <el-card v-if="!isSelectionMode" class="batch-toolbar" shadow="never">
      <div class="batch-toolbar__content">
        <div>
          <strong>批量操作</strong>
          <p>当前已勾选 {{ selectedQuestionCount }} 道题目，可批量流转或删除。</p>
        </div>
        <div class="action-group">
          <el-button
            v-for="action in batchTransitionActions"
            :key="`batch-${action.targetStatus}`"
            size="small"
            :type="action.type"
            :disabled="selectedQuestionCount <= 0"
            :loading="batchActing"
            @click="handleBatchTransition(action)"
          >
            {{ action.label }}
          </el-button>
          <el-button
            size="small"
            type="danger"
            :plain="selectedQuestionCount <= 0"
            :disabled="selectedQuestionCount <= 0"
            :loading="batchActing"
            @click="handleBatchDelete"
          >
            批量删除
          </el-button>
          <el-button size="small" :disabled="selectedQuestionCount <= 0" @click="clearSelectedQuestions">
            清空勾选
          </el-button>
        </div>
      </div>
    </el-card>

    <BaseFilterPanel
      v-model="filterModel"
      title="题库筛选"
      :exam-category-options="examCategoryOptions"
      :subject-code-options="subjectCodeOptions"
      :enable-subject-code="true"
      :initially-collapsed="false"
      @search="handleSearch"
      @reset="handleReset"
    >
      <template #fields="{ filters: panelFilters, examCategoryOptions: panelExamCategoryOptions, jointExamGroupOptions: panelJointExamGroupOptions, subjectCodeOptions: panelSubjectCodeOptions }">
        <el-input
          v-model="panelFilters.keyword"
          clearable
          placeholder="输入关键词"
        />
        <el-select
          v-model="panelFilters.examCategoryCode"
          clearable
          filterable
          placeholder="学科门类"
        >
          <el-option
            v-for="option in panelExamCategoryOptions"
            :key="option.examCategoryCode"
            :label="option.examCategoryName"
            :value="option.examCategoryCode"
          />
        </el-select>
        <el-select
          v-model="panelFilters.jointExamGroupCode"
          clearable
          filterable
          :disabled="!panelFilters.examCategoryCode"
          placeholder="专业组"
        >
          <el-option
            v-for="option in panelJointExamGroupOptions"
            :key="option.jointExamGroupCode"
            :label="option.jointExamGroupName"
            :value="option.jointExamGroupCode"
          />
        </el-select>
        <el-select
          v-model="panelFilters.subjectCode"
          clearable
          filterable
          placeholder="考试科目"
        >
          <el-option
            v-for="option in panelSubjectCodeOptions"
            :key="option.subjectCode"
            :label="option.subjectName"
            :value="option.subjectCode"
          />
        </el-select>
        <el-select
          v-model="panelFilters.status"
          clearable
          placeholder="题目状态"
        >
          <el-option label="草稿" value="DRAFT" />
          <el-option label="QA 互审中" value="QA_IN_PROGRESS" />
          <el-option label="待终审" value="REVIEW_PENDING" />
          <el-option label="已发布" value="PUBLISHED" />
          <el-option label="已驳回" value="REJECTED" />
        </el-select>
      </template>
      <template #actions="{ search, reset }">
        <el-button type="info" plain @click="quickFilterPendingReview">待终审题目</el-button>
        <el-button type="primary" @click="search">查询</el-button>
        <el-button @click="reset">重置</el-button>
      </template>
    </BaseFilterPanel>

    <el-alert
      v-if="fallbackSearchNotice"
      type="info"
      show-icon
      :closable="false"
      :title="fallbackSearchNotice"
    />

    <section class="query-result-list-panel">
      <header class="query-result-list-panel__header">
        <div class="query-result-list-panel__meta">
          <strong>查询结果列表</strong>
          <span class="helper-text">按序号展示题目与正确答案</span>
        </div>
        <el-button
          size="small"
          text
          :disabled="!shouldDisplayQueryResults && !queryResultRows.length"
          @click="handleClearQueryResultList"
        >
          清空列表
        </el-button>
      </header>
      <div v-if="!shouldDisplayQueryResults" class="query-result-list-panel__empty">请先选择筛选条件并点击查询</div>
      <div v-else-if="queryResultRows.length" class="query-result-list-panel__list">
        <div class="query-result-list-panel__row query-result-list-panel__row--head">
          <span class="query-result-list-panel__selector">
            <el-checkbox
              :model-value="queryResultAllChecked"
              :indeterminate="queryResultIndeterminate"
              @change="handleQueryResultSelectAllChange"
            />
          </span>
          <span>序号</span>
          <span>题目</span>
          <span>正确答案</span>
        </div>
        <div
          v-for="item in queryResultRows"
          :key="`query-result-${item.id || item.seq}`"
          class="query-result-list-panel__row"
        >
          <span class="query-result-list-panel__selector">
            <el-checkbox
              :model-value="item.checked"
              @change="(checked) => handleQueryResultRowCheckedChange(item, checked)"
            />
          </span>
          <span>{{ item.seq }}</span>
          <span>{{ item.stem }}</span>
          <span>{{ item.answer }}</span>
        </div>
      </div>
      <div v-else class="query-result-list-panel__empty">当前筛选条件下暂无题目数据</div>
    </section>

    <el-table
      v-if="shouldDisplayQueryResults"
      ref="questionTableRef"
      v-loading="loading"
      :data="tableRows"
      border
      row-key="id"
      @selection-change="handleSelectionChange"
    >
      <el-table-column type="selection" width="55" fixed="left" reserve-selection />
      <el-table-column prop="id" label="题目ID" min-width="130" />
      <el-table-column prop="stem" label="题干" min-width="260" show-overflow-tooltip />
      <el-table-column prop="typeLabel" label="题型" min-width="100" />
      <el-table-column label="状态" min-width="120">
        <template #default="scope">
          <el-tag :type="statusTagType(scope.row.latestStatus)" effect="light">
            {{ scope.row.latestStatusLabel }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="examCategoryLabel" label="学科门类" min-width="170" />
      <el-table-column prop="jointExamGroupLabel" label="专业组" min-width="170" />
      <el-table-column prop="updateTime" label="更新时间" min-width="180" />
      <el-table-column label="操作" min-width="450" fixed="right">
        <template #default="scope">
          <div class="action-group">
            <el-button
              size="small"
              @click="openDetailDrawer(scope.row)"
            >
              详情
            </el-button>
            <el-button
              size="small"
              type="primary"
              plain
              @click="openEditDialog(scope.row)"
            >
              编辑
            </el-button>
            <el-button
              v-for="action in resolveTransitionActions(scope.row)"
              :key="`${scope.row.id}-${action.targetStatus}`"
              size="small"
              :type="action.type"
              :loading="transitioningQuestionId === scope.row.id"
              @click="handleTransition(scope.row, action)"
            >
              {{ action.label }}
            </el-button>
            <el-button
              size="small"
              type="danger"
              plain
              :loading="deletingQuestionId === scope.row.id"
              @click="handleDeleteQuestion(scope.row)"
            >
              删除
            </el-button>
          </div>
        </template>
      </el-table-column>

      <template #empty>
        <el-empty description="当前筛选条件下暂无题目数据" />
      </template>
    </el-table>

    <div v-if="shouldDisplayQueryResults" class="pagination-wrap">
      <el-pagination
        background
        layout="total, sizes, prev, pager, next, jumper"
        :current-page="pagination.page"
        :page-size="pagination.size"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        @current-change="(nextPage) => handleResultPageChange(nextPage)"
        @size-change="(nextSize) => handleResultPageSizeChange(nextSize)"
      />
    </div>

    <div v-if="isSelectionMode" class="selection-floating-bar">
      <div class="selection-summary">
        <strong>已选题目 {{ selectedQuestionCount }} 道</strong>
        <span class="helper-text">可跨分页勾选，完成后返回组卷中心。</span>
      </div>
      <div class="selection-actions">
        <el-button @click="clearSelectedQuestions">清空选择</el-button>
        <el-button type="primary" :disabled="selectedQuestionCount === 0" @click="handleCompleteSelection">
          完成选题
        </el-button>
      </div>
    </div>

    <el-drawer
      v-model="detailDrawerVisible"
      title="题目详情与审核轨迹"
      direction="rtl"
      size="56%"
      @closed="closeDetailDrawer"
    >
      <el-skeleton
        v-if="detailLoading"
        animated
        :rows="10"
      />

      <el-empty
        v-else-if="!detailQuestion"
        description="题目详情不存在"
      />

      <div v-else class="detail-drawer-body">
        <section class="detail-block">
          <h4>固定字段</h4>
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item
              v-for="item in detailFixedRows"
              :key="item.label"
              :label="item.label"
            >
              {{ item.value }}
            </el-descriptions-item>
          </el-descriptions>
        </section>

        <section class="detail-block">
          <h4>状态流转快捷操作</h4>
          <div class="action-group">
            <el-button
              v-for="action in detailTransitionActions"
              :key="`detail-${detailQuestion.id}-${action.targetStatus}`"
              size="small"
              :type="action.type"
              :loading="transitioningQuestionId === detailQuestion.id"
              @click="handleTransition({ id: detailQuestion.id, userId: detailQuestion.userId, latestStatus: detailReviewSummary.latestStatus || detailQuestion.status }, action)"
            >
              {{ action.label }}
            </el-button>
            <span v-if="!detailTransitionActions.length" class="helper-text">
              当前状态下无可执行流转动作
            </span>
          </div>
        </section>

        <section class="detail-block">
          <h4>题目选项</h4>
          <div v-if="detailOptions.length" class="option-list">
            <div
              v-for="(option, index) in detailOptions"
              :key="`detail-option-${index}`"
              class="option-item"
            >
              <strong>{{ option.key || String.fromCharCode(65 + index) }}.</strong>
              <span>{{ option.content || '-' }}</span>
            </div>
          </div>
          <p v-else class="helper-text">当前题目无选项（通常为主观题）。</p>
        </section>

        <section class="detail-block">
          <h4>扩展字段摘要</h4>
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item
              v-for="item in detailExtOverviewRows"
              :key="item.label"
              :label="item.label"
            >
              {{ item.value }}
            </el-descriptions-item>
          </el-descriptions>
        </section>

        <section class="detail-block">
          <h4>扩展 JSON</h4>
          <pre class="json-block">{{ prettyJson(detailExtJson) }}</pre>
        </section>

        <section class="detail-block">
          <h4>审核流水线</h4>

          <div class="pipeline-summary-grid">
            <article class="summary-card">
              <span>累计审核</span>
              <strong>{{ Number(detailReviewSummary.reviewCount || detailReviewTimeline.length || 0) }}</strong>
            </article>
            <article class="summary-card">
              <span>最新状态</span>
              <strong>{{ questionStatusMeta(detailReviewSummary.latestStatus || detailQuestion.status).label }}</strong>
            </article>
            <article class="summary-card">
              <span>最新审核人</span>
              <strong>{{ detailReviewSummary.latestReviewerUserId || '-' }}</strong>
            </article>
            <article class="summary-card">
              <span>最近审核时间</span>
              <strong>{{ detailReviewSummary.latestReviewedAt || '-' }}</strong>
            </article>
          </div>

          <div class="pipeline-section">
            <h5>状态节点</h5>
            <el-empty
              v-if="!detailReviewTimeline.length"
              description="暂无审核节点"
            />
            <div v-else class="pipeline-list">
              <article
                v-for="item in detailReviewTimeline"
                :key="`timeline-${item.id}`"
                class="pipeline-item"
                :class="{ rejected: item.toStatus === 'REJECTED' }"
              >
                <strong>{{ item.fromStatusLabel }} -> {{ item.toStatusLabel }}</strong>
                <span>审核人：{{ item.reviewerUserId }}</span>
                <span>审核时间：{{ item.createTime }}</span>
                <span>执行角色：{{ item.actorRole }}</span>
                <span>原因：{{ item.reviewReason }}</span>
              </article>
            </div>
          </div>

          <div class="pipeline-section">
            <h5>驳回节点</h5>
            <el-empty
              v-if="!detailRejectedTimeline.length"
              description="暂无驳回记录"
            />
            <div v-else class="pipeline-list">
              <article
                v-for="item in detailRejectedTimeline"
                :key="`rejected-${item.id}`"
                class="pipeline-item rejected"
              >
                <strong>驳回节点</strong>
                <span>{{ item.reviewerUserId }} 于 {{ item.createTime }} 驳回题目</span>
                <span>原因：{{ item.reviewReason }}</span>
              </article>
            </div>
          </div>
        </section>
      </div>
    </el-drawer>

    <el-dialog
      v-model="editDialogVisible"
      title="编辑题目"
      width="860px"
      @closed="resetEditForm"
    >
      <el-form label-width="120px">
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="题目ID">
              <el-input v-model="editForm.id" disabled />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="知识点ID">
              <el-input v-model="editForm.knowledgeId" disabled />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="出题人">
              <el-input v-model="editForm.userId" disabled />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="题型">
              <el-input v-model="editForm.type" disabled />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="题干">
          <el-input
            v-model="editForm.stem"
            type="textarea"
            :rows="3"
            placeholder="请输入题干"
          />
        </el-form-item>

        <el-form-item label="答案">
          <el-input v-model="editForm.answer" placeholder="请输入答案" />
        </el-form-item>

        <el-form-item label="选项JSON">
          <el-input
            v-model="editForm.optionsJson"
            type="textarea"
            :rows="6"
            placeholder="请填写 optionsJson（JSON 数组）"
          />
        </el-form-item>

        <el-form-item label="扩展JSON">
          <el-input
            v-model="editForm.extJsonText"
            type="textarea"
            :rows="8"
            placeholder="请填写 extJson（JSON 对象）"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="editSaving" @click="saveQuestionEdit">保存</el-button>
      </template>
    </el-dialog>
  </section>
</template>

<style scoped>
.page-shell {
  display: grid;
  gap: 14px;
}

.batch-toolbar {
  border: 1px solid var(--qb-primary-soft-border);
  background: linear-gradient(180deg, var(--qb-bg-card), var(--qb-primary-soft-bg));
}

.batch-toolbar__content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.batch-toolbar__content strong,
.batch-toolbar__content p {
  margin: 0;
}

.batch-toolbar__content p {
  margin-top: 4px;
}

.scoped-question-alert {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.page-shell.selection-mode {
  padding-bottom: 88px;
}

h3,
p {
  margin: 0;
}

p {
  margin-top: 6px;
  color: var(--qb-text-subtle-6);
}

.action-group {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.query-result-list-panel {
  border: 1px solid var(--qb-primary-soft-border);
  border-radius: 12px;
  background: var(--qb-bg-card);
  padding: 10px;
  display: grid;
  gap: 8px;
}

.query-result-list-panel__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.query-result-list-panel__meta {
  display: grid;
  gap: 2px;
}

.query-result-list-panel__list {
  border: 1px solid var(--qb-border-muted);
  border-radius: 8px;
  overflow: hidden;
}

.query-result-list-panel__row {
  display: grid;
  grid-template-columns: 52px 96px 1fr 160px;
  gap: 8px;
  align-items: start;
  padding: 10px 12px;
  border-bottom: 1px solid var(--qb-border-muted);
  font-size: 13px;
}

.query-result-list-panel__row:last-child {
  border-bottom: none;
}

.query-result-list-panel__row--head {
  background: var(--qb-primary-soft-bg);
  font-weight: 600;
}

.query-result-list-panel__selector {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.query-result-list-panel__empty {
  border: 1px dashed var(--qb-border-muted);
  border-radius: 8px;
  color: var(--qb-text-subtle-8);
  font-size: 13px;
  padding: 16px 12px;
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
}

.selection-floating-bar {
  position: fixed;
  right: 24px;
  bottom: 16px;
  left: 24px;
  z-index: 100;
  border: 1px solid var(--qb-primary-soft-border);
  border-radius: 12px;
  background: var(--qb-bg-card);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
  padding: 12px 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.selection-summary {
  display: grid;
  gap: 4px;
}

.selection-actions {
  display: flex;
  gap: 8px;
}

.detail-drawer-body {
  display: grid;
  gap: 16px;
  padding-bottom: 14px;
}

.detail-block {
  display: grid;
  gap: 10px;
}

.detail-block h4,
.detail-block h5 {
  margin: 0;
}

.option-list {
  display: grid;
  gap: 8px;
}

.option-item {
  display: flex;
  gap: 8px;
  padding: 8px 10px;
  border: 1px solid var(--qb-primary-soft-border);
  border-radius: 8px;
  background: var(--qb-primary-soft-bg);
}

.json-block {
  margin: 0;
  padding: 12px;
  border-radius: 8px;
  border: 1px solid var(--qb-border-muted);
  background: var(--qb-text-heading);
  color: var(--qb-border-muted);
  font-size: 12px;
  line-height: 1.55;
  overflow: auto;
}

.pipeline-summary-grid {
  display: grid;
  gap: 10px;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
}

.summary-card {
  border: 1px solid var(--qb-primary-soft-border);
  border-radius: 10px;
  background: var(--qb-primary-soft-bg);
  padding: 10px;
  display: grid;
  gap: 6px;
}

.summary-card span {
  color: var(--qb-text-subtle-9);
  font-size: 12px;
}

.summary-card strong {
  font-size: 16px;
  color: var(--qb-text-heading);
}

.pipeline-section {
  display: grid;
  gap: 8px;
}

.pipeline-list {
  display: grid;
  gap: 8px;
}

.pipeline-item {
  border: 1px solid var(--qb-border-muted);
  border-radius: 8px;
  background: var(--qb-bg-card);
  padding: 10px;
  display: grid;
  gap: 4px;
}

.pipeline-item.rejected {
  border-color: var(--qb-danger-soft-border);
  background: var(--qb-danger-soft-bg);
}

.pipeline-item span {
  color: var(--qb-text-secondary);
  font-size: 12px;
}

.helper-text {
  color: var(--qb-text-subtle-9);
  font-size: 12px;
}
</style>
