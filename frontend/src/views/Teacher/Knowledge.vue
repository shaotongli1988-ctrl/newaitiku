<script setup>
import { computed, defineAsyncComponent, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from '@/ui/feedback'
import {
  createKnowledge,
  deleteKnowledge,
  getKnowledge,
  moveKnowledge,
  parseKnowledgeGraphFromWordFile,
  professionalTree,
  restoreDeletedKnowledge,
  updateKnowledge,
} from '../../api/services/questionBank'
import {
  buildProfessionalScopeOptions as createProfessionalScopeOptions,
  buildScopeKey,
  isProfessionalScopePathSelectable,
  normalizeScopePath,
  resolveFirstAvailableProfessionalScopePath,
} from '../../utils/professionalScope'
import { useUserStore } from '../../stores/userStore'

const userStore = useUserStore()
const graphRef = ref(null)
const parsingWord = ref(false)
const loadingScope = ref(false)
const professionalOptions = ref([])
const professionalTreeRaw = ref([])
const scopeMetaMap = ref({})
const highlightedNodeIds = ref([])
const autoMatchRows = ref([])
const semanticPoolOptions = ref([])
const autoMatchSavingMap = ref({})
const uploadInputRef = ref(null)
const activeKnowledgeDetail = ref(null)
const activeKnowledgeLoading = ref(false)
const knowledgeSaving = ref(false)
const knowledgeDeleting = ref(false)
const lastDeletedKnowledgeSnapshotId = ref('')
const lastDeletedKnowledgeName = ref('')
const knowledgeEditorMode = ref('edit')
const KnowledgeGraph = defineAsyncComponent(() => import('../../components/KnowledgeGraph.vue'))

const professionalCascaderProps = {
  value: 'code',
  label: 'name',
  children: 'children',
  checkStrictly: false,
}
const PREFERRED_DEFAULT_SCOPE_PATH = ['SCIENCE_ENGINEERING', 'SCIENCE_ENGINEERING_3', 'INFO_TECH_INTRO']

const graphScope = reactive({
  scope_path: [],
  exam_category_code: '',
  joint_exam_group_code: '',
  subject_code: '',
  policy_version: 'HB_ZSB_2026',
})

const assignedJointGroupCode = computed(() =>
  String(userStore.assignedJointGroupCode || userStore.jointExamGroupCode || '').trim(),
)

const isScopeLocked = computed(() =>
  String(userStore.role || '').trim() !== 'super_admin' && Boolean(assignedJointGroupCode.value),
)

const selectedScopeLabel = computed(() => {
  const scopePath = Array.isArray(graphScope.scope_path) ? graphScope.scope_path : []
  if (scopePath.length !== 3) {
    return '未选择科目范围'
  }
  const [categoryCode, groupCode, subjectCode] = scopePath.map((item) => String(item || '').trim())
  const scopeKey = `${categoryCode}::${groupCode}::${subjectCode}`
  const scopeMeta = scopeMetaMap.value[scopeKey] || {}
  const parts = [
    String(scopeMeta.categoryName || categoryCode || '').trim(),
    String(scopeMeta.groupName || groupCode || '').trim(),
    String(scopeMeta.subjectName || subjectCode || '').trim(),
  ].filter((item) => item)
  return parts.length ? parts.join(' / ') : '未选择科目范围'
})

const selectedScopeMeta = computed(() => {
  const scopePath = Array.isArray(graphScope.scope_path) ? graphScope.scope_path : []
  if (scopePath.length !== 3) {
    return null
  }
  const [categoryCode, groupCode, subjectCode] = scopePath.map((item) => String(item || '').trim())
  return scopeMetaMap.value[`${categoryCode}::${groupCode}::${subjectCode}`] || null
})
const activeNodeId = computed(() => String(activeKnowledgeDetail.value?.id || '').trim())
const activeNodeLabel = computed(() => String(activeKnowledgeDetail.value?.name || '').trim() || '未选中节点')
const canRestoreDeletedKnowledge = computed(() => Boolean(lastDeletedKnowledgeSnapshotId.value))
const showKnowledgeNodeAdminPanel = false
const knowledgeForm = reactive(createKnowledgeEditorForm())

function createKnowledgeEditorForm() {
  return {
    id: '',
    parentId: '',
    name: '',
    sort: 10,
    status: 'ENABLED',
    extJsonText: '{}',
  }
}

function unwrapData(response) {
  if (response && typeof response === 'object' && 'data' in response) {
    return response.data
  }
  return response
}

function parseExtJsonObject(rawValue) {
  if (rawValue && typeof rawValue === 'object') {
    return rawValue
  }
  if (typeof rawValue !== 'string') {
    return {}
  }
  try {
    const parsed = JSON.parse(rawValue)
    return parsed && typeof parsed === 'object' ? parsed : {}
  } catch (error) {
    return {}
  }
}

function stringifyKnowledgeExtJson(extJson) {
  return JSON.stringify(extJson || {}, null, 2)
}

function resetKnowledgeEditorForm() {
  Object.assign(knowledgeForm, createKnowledgeEditorForm())
  knowledgeEditorMode.value = 'edit'
}

function buildScopedExtJson(sourceExt = {}) {
  return {
    ...sourceExt,
    examCategoryCode: sourceExt.examCategoryCode || graphScope.exam_category_code || '',
    jointExamGroupCode: sourceExt.jointExamGroupCode || graphScope.joint_exam_group_code || '',
    subjectCode: sourceExt.subjectCode || graphScope.subject_code || '',
    policyVersion: sourceExt.policyVersion || graphScope.policy_version || 'HB_ZSB_2026',
  }
}

function patchKnowledgeEditorForm(detail) {
  const extJsonObject = parseExtJsonObject(detail?.extJson)
  Object.assign(knowledgeForm, {
    id: String(detail?.id || '').trim(),
    parentId: detail?.parentId === null ? '' : String(detail?.parentId || '').trim(),
    name: String(detail?.name || '').trim(),
    sort: Math.max(0, Number(detail?.sort || 0)),
    status: String(detail?.status || 'ENABLED').trim() || 'ENABLED',
    extJsonText: stringifyKnowledgeExtJson(buildScopedExtJson(extJsonObject)),
  })
}

function cancelKnowledgeCreate() {
  if (activeKnowledgeDetail.value) {
    patchKnowledgeEditorForm(activeKnowledgeDetail.value)
    knowledgeEditorMode.value = 'edit'
    return
  }
  resetKnowledgeEditorForm()
}

function applyProfessionalScopeOptions(treeNodes) {
  const { options, scopeMetaMap: nextScopeMetaMap } = createProfessionalScopeOptions(treeNodes, {
    assignedJointGroupCode: isScopeLocked.value ? assignedJointGroupCode.value : '',
  })
  professionalOptions.value = options
  scopeMetaMap.value = nextScopeMetaMap

  const currentGroupCode = String(normalizeScopePath(graphScope.scope_path)[1] || '').trim()
  if (isScopeLocked.value && currentGroupCode && currentGroupCode !== assignedJointGroupCode.value) {
    graphScope.scope_path = []
  }
  applyDefaultScopePathIfNeeded()
}

function resolvePreferredScopePath() {
  if (!isProfessionalScopePathSelectable(PREFERRED_DEFAULT_SCOPE_PATH, scopeMetaMap.value)) {
    return []
  }
  return [...PREFERRED_DEFAULT_SCOPE_PATH]
}

function applyDefaultScopePathIfNeeded({ force = false } = {}) {
  const currentPath = normalizeScopePath(graphScope.scope_path)
  if (!force && isProfessionalScopePathSelectable(currentPath, scopeMetaMap.value)) {
    return
  }
  const preferredPath = resolvePreferredScopePath()
  const fallbackPath = resolveFirstAvailableProfessionalScopePath(professionalOptions.value, scopeMetaMap.value)
  const nextPath = preferredPath.length ? preferredPath : fallbackPath
  if (!nextPath.length) {
    return
  }
  if (buildScopeKey(nextPath) === buildScopeKey(currentPath)) {
    return
  }
  graphScope.scope_path = nextPath
}

async function loadProfessionalTree() {
  loadingScope.value = true
  try {
    const response = await professionalTree()
    professionalTreeRaw.value = unwrapData(response) || []
    applyProfessionalScopeOptions(professionalTreeRaw.value)
  } catch (error) {
    professionalTreeRaw.value = []
    professionalOptions.value = []
    scopeMetaMap.value = {}
    ElMessage.error(error?.response?.data?.message || error?.message || '专业层级字典加载失败')
  } finally {
    loadingScope.value = false
  }
}

function loadKnowledgeGraph(subjectCode) {
  const normalizedSubjectCode = String(subjectCode || '').trim()
  if (!normalizedSubjectCode) {
    return
  }
  graphScope.subject_code = normalizedSubjectCode
}

function clearHighlightNodes() {
  highlightedNodeIds.value = []
}

function clearAutoMatchRows() {
  autoMatchRows.value = []
  semanticPoolOptions.value = []
  autoMatchSavingMap.value = {}
}

function normalizeSemanticPoolOptions(rawRows) {
  const rows = Array.isArray(rawRows) ? rawRows : []
  const seenValues = new Set()
  const normalized = []
  rows.forEach((item) => {
    const moduleCode = String(item?.module_code || item?.moduleCode || '').trim()
    const knowledgeName = String(item?.name || '').trim()
    const level = Number(item?.level || 0)
    if (!moduleCode || seenValues.has(moduleCode)) {
      return
    }
    seenValues.add(moduleCode)
    normalized.push({
      label: knowledgeName ? `L${level || '-'} ${knowledgeName}（${moduleCode}）` : moduleCode,
      value: moduleCode,
      name: knowledgeName || moduleCode,
      level,
    })
  })
  return normalized
}

function isAutoMatchSaving(pointNodeId) {
  return Boolean(autoMatchSavingMap.value[String(pointNodeId || '').trim()])
}

function setAutoMatchSaving(pointNodeId, saving) {
  const nextMap = { ...(autoMatchSavingMap.value || {}) }
  const key = String(pointNodeId || '').trim()
  if (!key) {
    autoMatchSavingMap.value = nextMap
    return
  }
  if (saving) {
    nextMap[key] = true
  } else {
    delete nextMap[key]
  }
  autoMatchSavingMap.value = nextMap
}

async function applyAutoMatchAdjust(row) {
  const pointNodeId = String(row?.pointNodeId || '').trim()
  const selectedModuleCode = String(row?.selectedModuleCode || '').trim()
  if (!pointNodeId || !selectedModuleCode) {
    ElMessage.warning('请先选择要保存的 module_code。')
    return
  }
  setAutoMatchSaving(pointNodeId, true)
  try {
    const detailResponse = await getKnowledge(pointNodeId)
    const detail = unwrapData(detailResponse) || {}
    const detailExt = detail?.extJson && typeof detail.extJson === 'object'
      ? detail.extJson
      : (() => {
        if (typeof detail?.extJson !== 'string') {
          return {}
        }
        try {
          const parsed = JSON.parse(detail.extJson)
          return parsed && typeof parsed === 'object' ? parsed : {}
        } catch (error) {
          return {}
        }
      })()
    const mergedExt = {
      ...detailExt,
      moduleCode: selectedModuleCode,
    }
    await updateKnowledge(pointNodeId, {
      id: String(detail?.id || pointNodeId).trim(),
      parent_id: detail?.parentId === null ? null : String(detail?.parentId || '').trim(),
      name: String(detail?.name || '').trim(),
      sort: Number(detail?.sort || 0),
      status: String(detail?.status || 'ENABLED').trim() || 'ENABLED',
      policy_version: String(
        mergedExt?.policyVersionCode || mergedExt?.policy_version || 'HB_ZSB_2026',
      ).trim() || 'HB_ZSB_2026',
      exam_category_code: String(
        mergedExt?.examCategoryCode || mergedExt?.exam_category_code || '',
      ).trim(),
      joint_exam_group_code: String(
        mergedExt?.jointExamGroupCode || mergedExt?.joint_exam_group_code || '',
      ).trim(),
      subject_code: String(
        mergedExt?.subjectCode || mergedExt?.subject_code || '',
      ).trim(),
      ext_json: mergedExt,
    })

    const rowIndex = autoMatchRows.value.findIndex((item) => String(item?.pointNodeId || '') === pointNodeId)
    if (rowIndex >= 0) {
      autoMatchRows.value[rowIndex] = {
        ...autoMatchRows.value[rowIndex],
        moduleCode: selectedModuleCode,
        selectedModuleCode,
      }
    }
    ElMessage.success(`考点 ${pointNodeId} 的 module_code 已更新。`)
  } catch (error) {
    ElMessage.error(error?.response?.data?.message || error?.message || '微调保存失败')
  } finally {
    setAutoMatchSaving(pointNodeId, false)
  }
}

async function reloadKnowledgeWorkbench() {
  if (graphRef.value?.reloadGraph) {
    await graphRef.value.reloadGraph()
  }
}

async function loadKnowledgeDetail(nodeId) {
  const normalizedNodeId = String(nodeId || '').trim()
  if (!normalizedNodeId) {
    activeKnowledgeDetail.value = null
    resetKnowledgeEditorForm()
    return
  }
  activeKnowledgeLoading.value = true
  try {
    const detail = unwrapData(await getKnowledge(normalizedNodeId)) || null
    activeKnowledgeDetail.value = detail
    patchKnowledgeEditorForm(detail)
    knowledgeEditorMode.value = 'edit'
  } catch (error) {
    activeKnowledgeDetail.value = null
    resetKnowledgeEditorForm()
    ElMessage.error(error?.response?.data?.message || error?.message || '知识点详情加载失败')
  } finally {
    activeKnowledgeLoading.value = false
  }
}

async function handleActiveNodeChange(detail) {
  const nodeId = String(detail?.id || '').trim()
  if (!nodeId) {
    activeKnowledgeDetail.value = null
    resetKnowledgeEditorForm()
    return
  }
  if (activeNodeId.value === nodeId && knowledgeEditorMode.value === 'edit') {
    return
  }
  await loadKnowledgeDetail(nodeId)
}

function prepareKnowledgeCreate(mode) {
  if (!activeKnowledgeDetail.value?.id) {
    ElMessage.warning('请先在知识星系中点击一个节点，再新增同级或子级节点。')
    return
  }
  const detail = activeKnowledgeDetail.value
  const extJsonObject = buildScopedExtJson(parseExtJsonObject(detail?.extJson))
  const isSibling = mode === 'sibling'
  Object.assign(knowledgeForm, {
    id: '',
    parentId: isSibling ? String(detail?.parentId || '').trim() : String(detail?.id || '').trim(),
    name: '',
    sort: Math.max(0, Number(detail?.sort || 0)) + 10,
    status: 'ENABLED',
    extJsonText: stringifyKnowledgeExtJson(extJsonObject),
  })
  knowledgeEditorMode.value = isSibling ? 'create-sibling' : 'create-child'
}

async function handleSaveKnowledge() {
  const payload = {
    id: String(knowledgeForm.id || '').trim(),
    parentId: String(knowledgeForm.parentId || '').trim(),
    name: String(knowledgeForm.name || '').trim(),
    sort: Math.max(0, Number(knowledgeForm.sort || 0)),
    status: String(knowledgeForm.status || 'ENABLED').trim() || 'ENABLED',
    extJson: JSON.stringify(buildScopedExtJson(parseExtJsonObject(knowledgeForm.extJsonText))),
  }
  if (!payload.name) {
    ElMessage.warning('请填写知识点名称。')
    return
  }

  knowledgeSaving.value = true
  try {
    if (knowledgeEditorMode.value === 'edit' && activeNodeId.value) {
      const result = unwrapData(await updateKnowledge(activeNodeId.value, payload)) || {}
      activeKnowledgeDetail.value = result
      patchKnowledgeEditorForm(result)
      ElMessage.success('知识点已更新。')
    } else {
      const created = unwrapData(await createKnowledge(payload)) || {}
      activeKnowledgeDetail.value = created
      patchKnowledgeEditorForm(created)
      knowledgeEditorMode.value = 'edit'
      ElMessage.success('知识点已创建。')
    }
    await reloadKnowledgeWorkbench()
  } catch (error) {
    ElMessage.error(error?.response?.data?.message || error?.message || '知识点保存失败')
  } finally {
    knowledgeSaving.value = false
  }
}

async function handleDeleteCurrentKnowledge() {
  const knowledgeId = activeNodeId.value
  if (!knowledgeId) {
    ElMessage.warning('请先选择要删除的知识点。')
    return
  }
  try {
    await ElMessageBox.confirm(
      `确认删除知识点「${activeNodeLabel.value}」吗？`,
      '删除知识点',
      {
        type: 'warning',
        confirmButtonText: '确认删除',
        cancelButtonText: '取消',
      },
    )
  } catch {
    return
  }
  knowledgeDeleting.value = true
  try {
    const result = unwrapData(await deleteKnowledge(knowledgeId)) || {}
    lastDeletedKnowledgeSnapshotId.value = String(result?.undoSnapshotId || '').trim()
    lastDeletedKnowledgeName.value = activeNodeLabel.value
    activeKnowledgeDetail.value = null
    resetKnowledgeEditorForm()
    ElMessage.success('知识点已删除，可在 10 分钟内恢复。')
    await reloadKnowledgeWorkbench()
  } catch (error) {
    ElMessage.error(error?.response?.data?.message || error?.message || '删除知识点失败')
  } finally {
    knowledgeDeleting.value = false
  }
}

async function handleRestoreDeletedKnowledge() {
  if (!lastDeletedKnowledgeSnapshotId.value) {
    return
  }
  knowledgeDeleting.value = true
  try {
    const result = unwrapData(await restoreDeletedKnowledge(lastDeletedKnowledgeSnapshotId.value)) || {}
    lastDeletedKnowledgeSnapshotId.value = ''
    lastDeletedKnowledgeName.value = ''
    ElMessage.success('知识点已恢复。')
    await reloadKnowledgeWorkbench()
    await loadKnowledgeDetail(String(result?.id || '').trim())
  } catch (error) {
    ElMessage.error(error?.response?.data?.message || error?.message || '恢复知识点失败')
  } finally {
    knowledgeDeleting.value = false
  }
}

async function handleMoveKnowledge(direction) {
  const knowledgeId = activeNodeId.value
  if (!knowledgeId) {
    ElMessage.warning('请先选择要排序的知识点。')
    return
  }
  knowledgeSaving.value = true
  try {
    await moveKnowledge(knowledgeId, direction)
    ElMessage.success(`知识点已${direction === 'up' ? '上移' : '下移'}。`)
    await reloadKnowledgeWorkbench()
    await loadKnowledgeDetail(knowledgeId)
  } catch (error) {
    ElMessage.error(error?.response?.data?.message || error?.message || '知识点排序失败')
  } finally {
    knowledgeSaving.value = false
  }
}

function ensureScopeSelected() {
  const scopePath = Array.isArray(graphScope.scope_path) ? graphScope.scope_path : []
  const [categoryCode, groupCode, subjectCode] = scopePath.map((item) => String(item || '').trim())
  if (scopePath.length !== 3 || !categoryCode || !groupCode || !subjectCode) {
    ElMessage.warning('请先通过导航雷达选择：学科门类 / 联考专业组 / 科目。')
    return null
  }
  const scopeKey = `${categoryCode}::${groupCode}::${subjectCode}`
  const scopeMeta = scopeMetaMap.value[scopeKey]
  if (!scopeMeta) {
    ElMessage.warning('当前级联路径无效，请重新选择。')
    return null
  }
  return scopeMeta
}

function handleOpenWordUpload() {
  const scopeMeta = ensureScopeSelected()
  if (!scopeMeta) {
    return
  }
  uploadInputRef.value?.click()
}

async function handleWordFileChange(event) {
  const file = event?.target?.files?.[0]
  event.target.value = ''
  if (!file) {
    return
  }
  const fileName = String(file.name || '').toLowerCase()
  if (!fileName.endsWith('.doc') && !fileName.endsWith('.docx')) {
    ElMessage.warning('仅支持上传 DOC / DOCX 文件。')
    return
  }

  const scopeMeta = ensureScopeSelected()
  if (!scopeMeta) {
    return
  }

  parsingWord.value = true
  try {
    const payload = await parseKnowledgeGraphFromWordFile({
      file,
      exam_category_code: scopeMeta.categoryCode,
      joint_exam_group_code: scopeMeta.groupCode,
      subject_code: scopeMeta.subjectCode,
      policy_version: graphScope.policy_version,
    })

    const recognizedScope = payload?.hb_zsb_2026_scope || payload?.scope || {}
    const normalizedScopePath = normalizeScopePath(
      Array.isArray(recognizedScope?.scope_path)
        ? recognizedScope.scope_path
        : [
            recognizedScope?.exam_category_code ?? recognizedScope?.examCategoryCode ?? scopeMeta.categoryCode,
            recognizedScope?.joint_exam_group_code ?? recognizedScope?.jointExamGroupCode ?? scopeMeta.groupCode,
            recognizedScope?.subject_code ?? recognizedScope?.subjectCode ?? scopeMeta.subjectCode,
          ],
    )
    const normalizedPolicyVersion = String(
      recognizedScope?.policy_version
      || recognizedScope?.policyVersion
      || graphScope.policy_version
      || 'HB_ZSB_2026',
    ).trim() || 'HB_ZSB_2026'
    graphScope.policy_version = normalizedPolicyVersion

    if (normalizedScopePath.length === 3 && isProfessionalScopePathSelectable(normalizedScopePath, scopeMetaMap.value)) {
      const currentScopeKey = buildScopeKey(graphScope.scope_path)
      const recognizedScopeKey = buildScopeKey(normalizedScopePath)
      if (recognizedScopeKey && recognizedScopeKey !== currentScopeKey) {
        graphScope.scope_path = normalizedScopePath
      }
    }

    const createdIds = Array.isArray(payload?.createdNodeIds) ? payload.createdNodeIds : []
    const recognizedIds = Array.isArray(payload?.recognizedNodeIds) ? payload.recognizedNodeIds : []
    const parserReport = payload?.parserReport && typeof payload.parserReport === 'object'
      ? payload.parserReport
      : {}
    const semanticPoolRows = normalizeSemanticPoolOptions(parserReport?.semanticPool)
    semanticPoolOptions.value = semanticPoolRows
    const autoMatchedRows = Array.isArray(parserReport?.autoMatchedPoints)
      ? parserReport.autoMatchedPoints
      : []
    autoMatchRows.value = autoMatchedRows.map((item, index) => {
      const moduleCode = String(item?.moduleCode || '').trim()
      const pointNodeId = String(item?.pointNodeId || '').trim()
      return {
        rowKey: `${pointNodeId || 'point'}-${index}`,
        chapterName: String(item?.chapterName || '').trim(),
        pointName: String(item?.pointName || '').trim(),
        pointNodeId,
        knowledgeId: String(item?.knowledgeId || '').trim(),
        moduleCode,
        matchedName: String(item?.matchedName || '').trim(),
        matchedLevel: Number(item?.matchedLevel || 0),
        matchedParentName: String(item?.matchedParentName || '').trim(),
        similarity: Number(item?.similarity || 0),
        selectedModuleCode: moduleCode,
      }
    })

    const autoMatchedNodeIds = autoMatchRows.value
      .map((item) => String(item?.pointNodeId || '').trim())
      .filter((item) => Boolean(item))
    highlightedNodeIds.value = autoMatchedNodeIds.length
      ? autoMatchedNodeIds
      : createdIds.length
        ? createdIds.map((item) => String(item || '').trim()).filter((item) => item)
        : recognizedIds.map((item) => String(item || '').trim()).filter((item) => item)

    if (graphRef.value?.reloadGraph) {
      await graphRef.value.reloadGraph()
    }

    const chapterCount = Number(payload?.chapterCount || 0)
    const pointCount = Number(payload?.pointCount || 0)
    ElMessage.success(`识别完成：章节 ${chapterCount} 个，考点 ${pointCount} 个。`)
  } catch (error) {
    clearAutoMatchRows()
    ElMessage.error(error?.response?.data?.message || error?.message || 'Word 大纲识别失败')
  } finally {
    parsingWord.value = false
  }
}

onMounted(async () => {
  await loadProfessionalTree()
  applyDefaultScopePathIfNeeded({ force: true })
})

watch(
  () => [String(userStore.role || '').trim(), assignedJointGroupCode.value],
  () => {
    if (!professionalTreeRaw.value.length) {
      return
    }
    applyProfessionalScopeOptions(professionalTreeRaw.value)
    applyDefaultScopePathIfNeeded({ force: true })
    clearHighlightNodes()
    clearAutoMatchRows()
    activeKnowledgeDetail.value = null
    resetKnowledgeEditorForm()
  },
)

watch(
  () => (Array.isArray(graphScope.scope_path) ? [...graphScope.scope_path] : []),
  (nextScopePath) => {
    const [categoryCode, groupCode, subjectCode] = nextScopePath.map((item) => String(item || '').trim())
    if (nextScopePath.length !== 3 || !categoryCode || !groupCode || !subjectCode) {
      graphScope.exam_category_code = ''
      graphScope.joint_exam_group_code = ''
      graphScope.subject_code = ''
      clearHighlightNodes()
      clearAutoMatchRows()
      activeKnowledgeDetail.value = null
      resetKnowledgeEditorForm()
      return
    }
    graphScope.exam_category_code = categoryCode
    graphScope.joint_exam_group_code = groupCode
    graphScope.subject_code = subjectCode
    clearHighlightNodes()
    clearAutoMatchRows()
    activeKnowledgeDetail.value = null
    resetKnowledgeEditorForm()
    loadKnowledgeGraph(subjectCode)
  },
)
</script>

<template>
  <section class="knowledge-page">
    <header class="page-header">
      <h2>知识点管理一体化视图</h2>
      <p>导航雷达先锁骨架，知识星系再按章节展开细节，避免把整科知识网一次性压在同一张图上。</p>
    </header>

    <section class="scope-level-strip">
      <article class="scope-level-card">
        <span>L1</span>
        <strong>{{ selectedScopeMeta?.groupName || '未锁定专业组' }}</strong>
        <p>专业组主题</p>
      </article>
      <article class="scope-level-card">
        <span>L2</span>
        <strong>{{ selectedScopeMeta?.subjectName || '未锁定科目' }}</strong>
        <p>科目主题</p>
      </article>
    </section>

    <section class="intent-grid">
      <article class="intent-card">
        <span>第一步</span>
        <strong>先锁范围</strong>
        <p>通过学科门类 / 联考专业组 / 科目收敛到单科上下文，再进入图谱聚焦。</p>
      </article>
      <article class="intent-card">
        <span>第二步</span>
        <strong>再看骨架</strong>
        <p>先看 L1-L3 章节骨架，再点击展开某个章节的 L4-L5 细节。</p>
      </article>
      <article class="intent-card">
        <span>第三步</span>
        <strong>最后做编辑</strong>
        <p>只有进入关系编辑模式时才显示 prerequisite 连线，降低首屏噪音。</p>
      </article>
    </section>

    <section class="radar-card" v-loading="loadingScope">
      <div class="radar-head">
        <div>
          <h3>导航雷达</h3>
          <p>先锁定专业范围，再切科目驱动知识星系切到对应骨架视图。</p>
        </div>
        <div class="radar-actions">
          <el-button
            type="primary"
            plain
            :loading="parsingWord"
            :disabled="loadingScope"
            @click="handleOpenWordUpload"
          >
            上传大纲识别
          </el-button>
          <input
            ref="uploadInputRef"
            class="file-input"
            type="file"
            accept=".doc,.docx,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            @change="handleWordFileChange"
          >
        </div>
      </div>

      <div class="radar-body">
        <el-cascader
          v-model="graphScope.scope_path"
          class="scope-cascader"
          :options="professionalOptions"
          :props="professionalCascaderProps"
          filterable
          clearable
          :teleported="false"
          expand-trigger="hover"
          :show-all-levels="false"
          :disabled="loadingScope || parsingWord"
          placeholder="请选择：学科门类 / 联考专业组 / 科目"
        />
        <p class="scope-summary">当前范围：{{ selectedScopeLabel }}</p>
      </div>
    </section>

    <section v-if="autoMatchRows.length" class="auto-match-card">
      <header class="auto-match-head">
        <div>
          <h3>AI 语义贴标预览</h3>
          <p>已高亮自动匹配考点，可直接微调 module_code 并保存。</p>
        </div>
      </header>
      <el-table :data="autoMatchRows" border size="small">
        <el-table-column prop="chapterName" label="章节" min-width="180" />
        <el-table-column prop="pointName" label="考点" min-width="220" />
        <el-table-column prop="matchedName" label="AI 匹配结果" min-width="220">
          <template #default="scope">
            <div class="matched-result-cell">
              <el-tag type="success" effect="light">{{ scope.row.matchedName || '-' }}</el-tag>
              <small v-if="scope.row.matchedLevel || scope.row.matchedParentName">
                {{ scope.row.matchedParentName || '当前层级' }} / L{{ scope.row.matchedLevel || '-' }}
              </small>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="匹配度" width="100">
          <template #default="scope">
            <strong>{{ Number(scope.row.similarity || 0).toFixed(2) }}</strong>
          </template>
        </el-table-column>
        <el-table-column label="微调 module_code" min-width="280">
          <template #default="scope">
            <el-select
              v-model="scope.row.selectedModuleCode"
              filterable
              clearable
              placeholder="选择 module_code"
              style="width: 100%"
            >
              <el-option
                v-for="option in semanticPoolOptions"
                :key="`${scope.row.rowKey}-${option.value}`"
                :label="option.label"
                :value="option.value"
              />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="scope">
            <el-button
              type="primary"
              plain
              size="small"
              :loading="isAutoMatchSaving(scope.row.pointNodeId)"
              :disabled="!scope.row.selectedModuleCode || !scope.row.pointNodeId"
              @click="applyAutoMatchAdjust(scope.row)"
            >
              保存微调
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <section v-if="showKnowledgeNodeAdminPanel" class="knowledge-admin-card">
      <header class="admin-card-head">
        <div>
          <h3>节点管理面板</h3>
          <p>点击知识星系中的任意节点后，可直接编辑、增删、排序和恢复。</p>
        </div>
        <div class="admin-actions">
          <el-button plain :disabled="!activeNodeId" @click="prepareKnowledgeCreate('sibling')">新增同级</el-button>
          <el-button type="primary" plain :disabled="!activeNodeId" @click="prepareKnowledgeCreate('child')">新增子级</el-button>
          <el-button v-if="canRestoreDeletedKnowledge" plain :loading="knowledgeDeleting" @click="handleRestoreDeletedKnowledge">
            恢复最近删除
          </el-button>
        </div>
      </header>

      <el-alert
        v-if="canRestoreDeletedKnowledge"
        type="warning"
        show-icon
        :closable="false"
        :title="`知识点「${lastDeletedKnowledgeName || '未命名节点'}」已删除，可在 10 分钟内恢复。`"
      />

      <div class="admin-summary">
        <el-tag type="info" effect="light">当前节点：{{ activeNodeLabel }}</el-tag>
        <el-tag type="success" effect="light">模式：{{ knowledgeEditorMode === 'edit' ? '编辑当前节点' : knowledgeEditorMode === 'create-child' ? '新增子级节点' : '新增同级节点' }}</el-tag>
      </div>

      <el-skeleton v-if="activeKnowledgeLoading" :rows="6" animated />

      <el-form v-else label-position="top" class="knowledge-editor-grid">
        <el-form-item label="节点名称">
          <el-input v-model="knowledgeForm.name" placeholder="请输入知识点名称" />
        </el-form-item>
        <el-form-item label="父节点 ID">
          <el-input v-model="knowledgeForm.parentId" placeholder="根节点可留空" />
        </el-form-item>
        <el-form-item label="排序值">
          <el-input-number v-model="knowledgeForm.sort" :min="0" :max="9999" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="knowledgeForm.status" placeholder="请选择状态">
            <el-option label="启用" value="ENABLED" />
            <el-option label="停用" value="DISABLED" />
          </el-select>
        </el-form-item>
        <el-form-item label="扩展 JSON" class="span-2">
          <el-input
            v-model="knowledgeForm.extJsonText"
            type="textarea"
            :rows="6"
            placeholder="请输入 extJson，默认会自动补齐当前专业范围信息"
          />
        </el-form-item>
      </el-form>

      <div class="admin-footer">
        <div class="admin-footer-actions">
          <el-button :disabled="!activeNodeId" :loading="knowledgeSaving" @click="handleMoveKnowledge('up')">上移</el-button>
          <el-button :disabled="!activeNodeId" :loading="knowledgeSaving" @click="handleMoveKnowledge('down')">下移</el-button>
          <el-button
            v-if="knowledgeEditorMode !== 'edit'"
            :disabled="knowledgeSaving"
            @click="cancelKnowledgeCreate"
          >
            取消新建
          </el-button>
        </div>
        <div class="admin-footer-actions">
          <el-button type="danger" plain :disabled="!activeNodeId || knowledgeEditorMode !== 'edit'" :loading="knowledgeDeleting" @click="handleDeleteCurrentKnowledge">
            删除当前节点
          </el-button>
          <el-button type="primary" :loading="knowledgeSaving" @click="handleSaveKnowledge">
            {{ knowledgeEditorMode === 'edit' ? '保存当前节点' : '创建节点' }}
          </el-button>
        </div>
      </div>
    </section>

    <KnowledgeGraph
      ref="graphRef"
      :graph-scope="graphScope"
      :highlighted-node-ids="highlightedNodeIds"
      @active-node-change="handleActiveNodeChange"
    />
  </section>
</template>

<style scoped>
.knowledge-page {
  display: grid;
  gap: 14px;
}

.scope-level-strip {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.scope-level-card {
  display: grid;
  gap: 6px;
  padding: 14px 16px;
  border-radius: 16px;
  border: 1px solid rgba(15, 118, 110, 0.12);
  background: linear-gradient(160deg, rgba(255, 255, 255, 0.96), rgba(240, 250, 248, 0.74));
}

.scope-level-card span {
  color: var(--qb-text-subtle-6);
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.scope-level-card strong {
  color: var(--qb-text-heading);
  font-size: 20px;
}

.scope-level-card p {
  margin: 0;
  color: var(--qb-text-subtle-7);
  font-size: 12px;
}

.intent-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.intent-card {
  display: grid;
  gap: 8px;
  padding: 14px 16px;
  border-radius: 16px;
  border: 1px solid rgba(15, 118, 110, 0.12);
  background: linear-gradient(160deg, rgba(255, 255, 255, 0.96), rgba(240, 250, 248, 0.74));
}

.intent-card span {
  color: var(--qb-text-subtle-6);
  font-size: 12px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.intent-card strong {
  color: var(--qb-text-heading);
  font-size: 18px;
}

.intent-card p {
  margin: 0;
  color: var(--qb-text-subtle-8);
  font-size: 13px;
  line-height: 1.6;
}

.page-header h2 {
  margin: 0;
  font-size: 20px;
}

.page-header p {
  margin: 6px 0 0;
  color: var(--qb-text-subtle-8);
}

.radar-card {
  display: grid;
  gap: 12px;
  border: 1px solid rgba(57, 123, 255, 0.25);
  border-radius: 14px;
  padding: 14px;
  background: linear-gradient(130deg, rgba(239, 246, 255, 0.92), rgba(231, 244, 255, 0.62));
}

.radar-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.radar-head h3 {
  margin: 0;
  font-size: 16px;
}

.radar-head p {
  margin: 4px 0 0;
  color: var(--qb-text-subtle-8);
  font-size: 12px;
}

.radar-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.file-input {
  display: none;
}

.radar-body {
  display: grid;
  gap: 8px;
}

.scope-cascader {
  width: min(860px, 100%);
}

.scope-summary {
  margin: 0;
  color: var(--qb-text-subtle-8);
  font-size: 12px;
}

.auto-match-card {
  display: grid;
  gap: 10px;
  border: 1px solid rgba(42, 157, 84, 0.2);
  border-radius: 14px;
  padding: 14px;
  background: linear-gradient(130deg, rgba(240, 253, 244, 0.9), rgba(236, 253, 245, 0.6));
}

.auto-match-head h3 {
  margin: 0;
  font-size: 16px;
}

.auto-match-head p {
  margin: 6px 0 0;
  color: var(--qb-text-subtle-8);
  font-size: 12px;
}

.matched-result-cell {
  display: grid;
  gap: 4px;
}

.matched-result-cell small {
  color: var(--qb-text-subtle-8);
}

.knowledge-admin-card {
  display: grid;
  gap: 12px;
  border: 1px solid rgba(15, 118, 110, 0.16);
  border-radius: 16px;
  padding: 16px;
  background: linear-gradient(160deg, rgba(255, 255, 255, 0.96), rgba(247, 250, 252, 0.84));
}

.admin-card-head,
.admin-actions,
.admin-summary,
.admin-footer,
.admin-footer-actions {
  display: flex;
  gap: 10px;
}

.admin-card-head,
.admin-footer {
  align-items: flex-start;
  justify-content: space-between;
  flex-wrap: wrap;
}

.admin-card-head h3,
.admin-card-head p {
  margin: 0;
}

.admin-card-head p {
  margin-top: 6px;
  color: var(--qb-text-subtle-8);
  font-size: 12px;
}

.admin-actions,
.admin-summary,
.admin-footer-actions {
  flex-wrap: wrap;
}

.knowledge-editor-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.span-2 {
  grid-column: 1 / -1;
}

@media (max-width: 900px) {
  .scope-level-strip {
    grid-template-columns: minmax(0, 1fr);
  }

  .intent-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .radar-head {
    flex-direction: column;
    align-items: flex-start;
  }

  .scope-cascader {
    width: 100%;
  }

  .knowledge-editor-grid {
    grid-template-columns: 1fr;
  }

  .span-2 {
    grid-column: auto;
  }
}
</style>
