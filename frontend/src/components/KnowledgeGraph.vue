<script setup>
import { computed, defineAsyncComponent, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ElMessage } from '@/ui/feedback'
import { useRouter } from 'vue-router'
import { addEdge, MarkerType } from '@vue-flow/core'
import { hasBackendErrorCode, resolveApiErrorMessage } from '../api/request'
import {
  fetchAdaptivePracticeList,
  knowledgeTree,
  persistKnowledgeGraphLayout,
  updateKnowledgePrerequisites,
} from '../api/services/questionBank'
import {
  buildTeacherExamSectionSummary,
  buildKnowledgeDisplayLabel,
  buildTeacherKnowledgeIndex,
  buildTeacherNodeDetail,
  buildTeacherContentOutlineTree,
  buildTeacherMindmapLayout,
  buildTeacherVisibleSummary,
  collectTeacherVisibleNodeIds,
  resolveTeacherFocusNodeId,
  resolveTeacherSpecialSections,
} from '../utils/knowledgeGraphTeacher'

const props = defineProps({
  status: {
    type: String,
    default: '',
  },
  graphScope: {
    type: Object,
    default: () => ({}),
  },
  highlightedNodeIds: {
    type: Array,
    default: () => [],
  },
  mode: {
    type: String,
    default: 'teacher',
    validator: (value) => ['teacher', 'student'].includes(String(value || '').trim()),
  },
})
const emit = defineEmits(['active-node-change'])
const KnowledgeGraphFlowSurface = defineAsyncComponent(() => import('./KnowledgeGraphFlowSurface.vue'))

const router = useRouter()

const loading = ref(false)
const reinforcing = ref(false)
const nodes = ref([])
const edges = ref([])
const allFlowNodes = ref([])
const allFlowEdges = ref([])
const graphPayload = ref({ nodes: [], links: [] })
const pendingPrerequisiteSource = ref(null)
const teacherIndex = ref(buildTeacherKnowledgeIndex({}))
const teacherFocusNodeId = ref('')
const teacherActiveNodeId = ref('')
const teacherRelationMode = ref(false)
const teacherExamExpandedItemId = ref('')

const formulaText = '$$NodeSize = 20 + \\ln(QuestionCount + 1) \\times 10$$'
const layoutSaveTimers = new Map()

const isTeacherMode = computed(() => String(props.mode || '').trim() === 'teacher')
const isStudentMode = computed(() => String(props.mode || '').trim() === 'student')
const hasGraphData = computed(() => nodes.value.length > 0)
const panelTitle = computed(() => (isStudentMode.value ? '知识星系（学习模式）' : '知识星系（教学模式）'))
const helperText = computed(() => {
  if (isStudentMode.value) {
    return '置灰的 L5 原子知识点代表尚未练习；点击低掌握节点可直接触发弱项强化练。'
  }
  if (teacherRelationMode.value) {
    return '关系编辑模式已开启：当前仅显示聚焦分支，并显式展示 prerequisite 连线。'
  }
  return '导航树只服务于“具体内容与要求”主线；考试形式与参考题型固定展示在树上方，思维导图只展开一个章节分支。'
})

const teacherExamSectionSummary = computed(() => buildTeacherExamSectionSummary(teacherIndex.value))
const teacherSpecialSections = computed(() => resolveTeacherSpecialSections(teacherIndex.value))

const teacherVisibleNodeIds = computed(() =>
  isTeacherMode.value
    ? collectTeacherVisibleNodeIds(teacherIndex.value, teacherFocusNodeId.value)
    : allFlowNodes.value.map((item) => String(item?.id || '').trim()).filter((item) => item),
)
const teacherVisibleSummary = computed(() =>
  buildTeacherVisibleSummary(teacherIndex.value, teacherVisibleNodeIds.value),
)
const teacherActiveNodeDetail = computed(() =>
  buildTeacherNodeDetail(teacherIndex.value, teacherActiveNodeId.value),
)
const teacherFocusDetail = computed(() =>
  buildTeacherNodeDetail(teacherIndex.value, teacherFocusNodeId.value),
)
const flowRenderKey = computed(() => {
  if (!isTeacherMode.value) {
    return `student-${nodes.value.length}`
  }
  return `teacher-${teacherFocusNodeId.value || 'skeleton'}-${teacherRelationMode.value ? 'edit' : 'browse'}-${nodes.value.length}`
})

function normalizeGraphPayload(response) {
  const payload = response && typeof response === 'object' && 'data' in response ? response.data : response
  const graph = payload && typeof payload === 'object' ? payload : {}
  return {
    nodes: Array.isArray(graph.nodes) ? graph.nodes : [],
    links: Array.isArray(graph.links) ? graph.links : [],
  }
}

function normalizeMastery(value) {
  const numericValue = Number(value || 0)
  if (!Number.isFinite(numericValue)) {
    return 0
  }
  return Math.max(0, Math.min(1, numericValue))
}

function resolveQuestionCount(node) {
  const directCount = Number(node?.questionCount)
  if (Number.isFinite(directCount) && directCount >= 0) {
    return Math.floor(directCount)
  }
  const encodedSize = Number(node?.size)
  if (Number.isFinite(encodedSize) && encodedSize >= 0) {
    return Math.max(0, Math.round((encodedSize - 8) / 2))
  }
  return 0
}

function resolveNodeSize(node) {
  const encodedSize = Number(node?.size)
  if (Number.isFinite(encodedSize) && encodedSize > 0) {
    return Math.round(encodedSize)
  }
  return Math.round(20 + (Math.log(resolveQuestionCount(node) + 1) * 10))
}

function buildNodeId(rawId) {
  return String(rawId || '').trim()
}

function normalizeQuestionIds(payload) {
  const sourceRows = Array.isArray(payload?.question_ids)
    ? payload.question_ids
    : Array.isArray(payload?.questionIds)
      ? payload.questionIds
      : []
  return Array.from(new Set(sourceRows.map((item) => String(item || '').trim()).filter((item) => item)))
}

function normalizeDimension(label) {
  const normalized = String(label || '')
    .trim()
    .replace(/[^a-zA-Z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .toUpperCase()
  return normalized || 'KNOWLEDGE'
}

function buildPrerequisiteEdge(source, target) {
  return {
    id: `prerequisite:${source}->${target}`,
    source,
    target,
    type: 'smoothstep',
    pathOptions: {
      borderRadius: 30,
      offset: 18,
    },
    markerEnd: {
      type: MarkerType.ArrowClosed,
      color: 'rgba(15, 118, 110, 0.9)',
      width: 16,
      height: 16,
    },
    style: {
      stroke: 'rgba(15, 118, 110, 0.9)',
      strokeWidth: 2.2,
      strokeDasharray: '6 4',
      strokeLinecap: 'round',
      strokeLinejoin: 'round',
    },
    data: {
      linkType: 'prerequisite',
    },
  }
}

function buildParentEdge(source, target) {
  return {
    id: `parent:${source}->${target}`,
    source,
    target,
    type: 'smoothstep',
    pathOptions: {
      borderRadius: 44,
      offset: 26,
    },
    selectable: false,
    focusable: false,
    updatable: false,
    deletable: false,
    style: {
      stroke: 'rgba(120, 131, 155, 0.22)',
      strokeWidth: 1.4,
      strokeLinecap: 'round',
      strokeLinejoin: 'round',
    },
    data: {
      linkType: 'parent',
    },
  }
}

function resolveNodePosition(node, index) {
  const x = Number(node?.x)
  const y = Number(node?.y)
  if (Number.isFinite(x) && Number.isFinite(y)) {
    return { x, y }
  }
  return {
    x: 120 + ((index % 5) * 220),
    y: 90 + (Math.floor(index / 5) * 120),
  }
}

function mapGraphToFlow(graph) {
  const sourceNodes = Array.isArray(graph?.nodes) ? graph.nodes : []
  const sourceLinks = Array.isArray(graph?.links) ? graph.links : []
  const highlightedIdSet = new Set(
    (Array.isArray(props.highlightedNodeIds) ? props.highlightedNodeIds : [])
      .map((item) => String(item || '').trim())
      .filter((item) => item),
  )

  const nodeMap = new Map()
  const mappedNodes = sourceNodes
    .map((node, index) => {
      const id = buildNodeId(node?.id)
      if (!id) {
        return null
      }
      nodeMap.set(id, true)
      return {
        id,
        type: 'knowledge',
        position: resolveNodePosition(node, index),
        data: {
          id,
          label: buildKnowledgeDisplayLabel(node?.label || id),
          fullLabel: String(node?.label || id),
          level: Number(node?.level || 0),
          mastery: normalizeMastery(node?.mastery),
          questionCount: resolveQuestionCount(node),
          size: resolveNodeSize(node),
          isHighlighted: highlightedIdSet.has(id),
          isActive: false,
          showHandles: false,
          emphasisMode: isTeacherMode.value ? 'teacher' : 'student',
          onContextMenu: null,
        },
      }
    })
    .filter(Boolean)

  const mappedEdges = sourceLinks
    .map((link) => {
      const source = buildNodeId(link?.source)
      const target = buildNodeId(link?.target)
      if (!source || !target || source === target || !nodeMap.has(source) || !nodeMap.has(target)) {
        return null
      }
      return String(link?.type || '').trim() === 'prerequisite'
        ? buildPrerequisiteEdge(source, target)
        : buildParentEdge(source, target)
    })
    .filter(Boolean)

  return {
    nodes: mappedNodes,
    edges: mappedEdges,
  }
}

function resolveOutlineAnchorNodeId(nodeId) {
  let currentId = buildNodeId(nodeId)
  while (currentId) {
    const detail = buildTeacherNodeDetail(teacherIndex.value, currentId)
    if (detail && Number(detail.level || 0) <= 3) {
      return currentId
    }
    currentId = String(detail?.parentId || '').trim()
  }
  return ''
}

function resolveTeacherBranchColor(nodeId) {
  const normalizedNodeId = String(nodeId || '').trim()
  const palette = [
    'var(--qb-branch-color-1)',
    'var(--qb-branch-color-2)',
    'var(--qb-branch-color-3)',
    'var(--qb-branch-color-4)',
    'var(--qb-branch-color-5)',
    'var(--qb-branch-color-6)',
  ]
  if (!normalizedNodeId) {
    return ''
  }
  const focusId = String(teacherFocusNodeId.value || '').trim()
  if (!focusId) {
    return ''
  }
  const childIds = (teacherIndex.value?.childrenByParent?.get(focusId) || [])
    .map((item) => String(item || '').trim())
    .filter((item) => item)
  if (!childIds.length) {
    return ''
  }
  if (childIds.includes(normalizedNodeId)) {
    return palette[childIds.indexOf(normalizedNodeId) % palette.length]
  }
  let currentId = normalizedNodeId
  while (currentId) {
    const parentId = String(teacherIndex.value?.parentByChild?.get(currentId) || '').trim()
    if (!parentId) {
      break
    }
    if (childIds.includes(parentId)) {
      return palette[childIds.indexOf(parentId) % palette.length]
    }
    currentId = parentId
  }
  return ''
}

function decorateVisibleNodes(baseNodes, visibleIdSet) {
  const autoLayoutMap = buildTeacherMindmapLayout(
    teacherIndex.value,
    Array.from(visibleIdSet),
    teacherFocusNodeId.value,
  )
  const subjectRootId = String(teacherSpecialSections.value?.subjectRootId || '').trim()
  return baseNodes
    .filter((node) => visibleIdSet.has(String(node?.id || '').trim()))
    .map((node) => ({
      ...node,
      position: autoLayoutMap.get(String(node?.id || '').trim()) || node.position,
      data: {
        ...(node.data || {}),
        isActive: String(node?.id || '').trim() === teacherActiveNodeId.value,
        showHandles: teacherRelationMode.value,
        emphasisMode: 'teacher',
        nodeRole:
          String(node?.id || '').trim() === subjectRootId
            ? 'subject'
            : String(node?.id || '').trim() === teacherFocusNodeId.value
              ? 'focus'
              : Number(node?.data?.level || 0) >= 5
                ? 'leaf'
                : 'branch',
        branchColor: resolveTeacherBranchColor(String(node?.id || '').trim()),
        onContextMenu: teacherRelationMode.value ? handleTeacherNodeContextMenu : null,
      },
    }))
}

function decorateVisibleEdges(baseEdges, visibleIdSet) {
  const contentNodeId = String(teacherSpecialSections.value?.contentNodeId || '').trim()
  const subjectRootId = String(teacherSpecialSections.value?.subjectRootId || '').trim()
  return baseEdges.filter((edge) => {
    const source = String(edge?.source || '').trim()
    const target = String(edge?.target || '').trim()
    if (!visibleIdSet.has(source) || !visibleIdSet.has(target)) {
      if (
        source === contentNodeId
        && subjectRootId
        && visibleIdSet.has(subjectRootId)
        && visibleIdSet.has(target)
        && String(edge?.data?.linkType || '').trim() === 'parent'
      ) {
        return true
      }
      return false
    }
    if (!teacherRelationMode.value && String(edge?.data?.linkType || '').trim() === 'prerequisite') {
      return false
    }
    return true
  }).map((edge) => {
    const source = String(edge?.source || '').trim()
    const target = String(edge?.target || '').trim()
    const sourceLevel = Number(teacherIndex.value?.nodesById?.get(source)?.level || 0)
    const targetLevel = Number(teacherIndex.value?.nodesById?.get(target)?.level || 0)
    if (
      source === contentNodeId
      && subjectRootId
      && String(edge?.data?.linkType || '').trim() === 'parent'
    ) {
      return {
        ...edge,
        id: `parent:${subjectRootId}->${edge.target}`,
        source: subjectRootId,
        style: {
          stroke: 'rgba(15, 118, 110, 0.5)',
          strokeWidth: 4.4,
          strokeLinecap: 'round',
          strokeLinejoin: 'round',
        },
      }
    }
    if (String(edge?.data?.linkType || '').trim() === 'prerequisite') {
      return edge
    }
    const branchColor = resolveTeacherBranchColor(target) || resolveTeacherBranchColor(source)
    if (sourceLevel <= 1 || target === teacherFocusNodeId.value) {
      return {
        ...edge,
        style: {
          stroke: branchColor || 'rgba(15, 118, 110, 0.48)',
          strokeWidth: 3.8,
          strokeLinecap: 'round',
          strokeLinejoin: 'round',
        },
      }
    }
    if (sourceLevel <= 3 && targetLevel >= 4) {
      return {
        ...edge,
        style: {
          stroke: branchColor || 'rgba(93, 126, 143, 0.32)',
          strokeWidth: 2.3,
          strokeLinecap: 'round',
          strokeLinejoin: 'round',
        },
      }
    }
    return {
      ...edge,
      style: {
        stroke: 'rgba(120, 131, 155, 0.2)',
        strokeWidth: 1.6,
        strokeLinecap: 'round',
        strokeLinejoin: 'round',
      },
    }
  })
}

function applyGraphViewport() {
  if (!isTeacherMode.value) {
    nodes.value = allFlowNodes.value.map((node) => ({
      ...node,
      data: {
        ...(node.data || {}),
        isActive: false,
        showHandles: false,
        emphasisMode: 'student',
        onContextMenu: null,
      },
    }))
    edges.value = allFlowEdges.value.slice()
    return
  }

  const visibleIdSet = new Set(teacherVisibleNodeIds.value.map((item) => String(item || '').trim()).filter((item) => item))
  nodes.value = decorateVisibleNodes(allFlowNodes.value, visibleIdSet)
  edges.value = decorateVisibleEdges(allFlowEdges.value, visibleIdSet)
}

async function reloadGraph() {
  loading.value = true
  try {
    const response = await knowledgeTree({
      status: props.status,
      examCategoryCode: String(props.graphScope?.exam_category_code || props.graphScope?.examCategoryCode || '').trim(),
      jointExamGroupCode: String(props.graphScope?.joint_exam_group_code || props.graphScope?.jointExamGroupCode || '').trim(),
      subjectCode: String(props.graphScope?.subject_code || props.graphScope?.subjectCode || '').trim(),
      policyVersion: String(props.graphScope?.policy_version || props.graphScope?.policyVersion || 'HB_ZSB_2026').trim(),
    })
    graphPayload.value = normalizeGraphPayload(response)
    const mapped = mapGraphToFlow(graphPayload.value)
    allFlowNodes.value = mapped.nodes
    allFlowEdges.value = mapped.edges
    teacherIndex.value = buildTeacherKnowledgeIndex(graphPayload.value)

    if (isTeacherMode.value) {
      teacherFocusNodeId.value = resolveTeacherFocusNodeId(teacherIndex.value, teacherFocusNodeId.value)
      teacherActiveNodeId.value = buildTeacherNodeDetail(teacherIndex.value, teacherActiveNodeId.value)
        ? teacherActiveNodeId.value
        : teacherFocusNodeId.value
      teacherExamExpandedItemId.value = ''
      pendingPrerequisiteSource.value = null
    }

    applyGraphViewport()
    await nextTick()
  } catch (error) {
    graphPayload.value = { nodes: [], links: [] }
    allFlowNodes.value = []
    allFlowEdges.value = []
    nodes.value = []
    edges.value = []
    teacherIndex.value = buildTeacherKnowledgeIndex({})
    if (hasBackendErrorCode(error, 'QUESTION_FORBIDDEN')) {
      ElMessage.error('当前账号暂无知识图谱访问权限。')
      return
    }
    if (hasBackendErrorCode(error, 'QUESTION_NOT_FOUND')) {
      ElMessage.error('当前知识图谱数据不存在或已失效。')
      return
    }
    ElMessage.error(resolveApiErrorMessage(error, '知识图谱加载失败'))
  } finally {
    loading.value = false
  }
}

function setTeacherFocus(nodeId) {
  const nextFocusNodeId = resolveTeacherFocusNodeId(teacherIndex.value, nodeId)
  teacherFocusNodeId.value = nextFocusNodeId
  teacherActiveNodeId.value = nextFocusNodeId
  pendingPrerequisiteSource.value = null
}

function resetTeacherFocus() {
  teacherFocusNodeId.value = ''
  teacherActiveNodeId.value = resolveTeacherFocusNodeId(teacherIndex.value, '')
  pendingPrerequisiteSource.value = null
}

function toggleTeacherRelationMode() {
  teacherRelationMode.value = !teacherRelationMode.value
  if (!teacherRelationMode.value) {
    pendingPrerequisiteSource.value = null
  }
}

function toggleTeacherExamItem(itemId) {
  const normalizedItemId = String(itemId || '').trim()
  if (!normalizedItemId) {
    return
  }
  teacherExamExpandedItemId.value = teacherExamExpandedItemId.value === normalizedItemId ? '' : normalizedItemId
}

function handleTeacherNodeContextMenu(payload) {
  if (!isTeacherMode.value || !teacherRelationMode.value) {
    return
  }
  const nodeId = buildNodeId(payload?.id)
  if (!nodeId) {
    return
  }
  const nodeLabel = String(payload?.label || nodeId)
  teacherActiveNodeId.value = nodeId

  if (!pendingPrerequisiteSource.value || pendingPrerequisiteSource.value.id === nodeId) {
    pendingPrerequisiteSource.value = { id: nodeId, label: nodeLabel }
    ElMessage.info(`已选择前置节点：${nodeLabel}，请右键目标节点完成连线。`)
    return
  }

  const sourceNode = pendingPrerequisiteSource.value
  pendingPrerequisiteSource.value = null
  connectPrerequisite(sourceNode.id, nodeId)
}

async function connectPrerequisite(sourceId, targetId) {
  const source = buildNodeId(sourceId)
  const target = buildNodeId(targetId)
  if (!source || !target) {
    return
  }
  if (source === target) {
    ElMessage.warning('不能给同一个知识点建立前置关系。')
    return
  }
  const duplicate = allFlowEdges.value.some(
    (edge) =>
      String(edge?.source || '') === source
      && String(edge?.target || '') === target
      && String(edge?.data?.linkType || '') === 'prerequisite',
  )
  if (duplicate) {
    ElMessage.info('该前置关系已存在。')
    return
  }

  try {
    await updateKnowledgePrerequisites(target, { sourceId: source })
    graphPayload.value = {
      ...graphPayload.value,
      links: [
        ...(Array.isArray(graphPayload.value?.links) ? graphPayload.value.links : []),
        { source, target, type: 'prerequisite' },
      ],
    }
    allFlowEdges.value = addEdge(buildPrerequisiteEdge(source, target), allFlowEdges.value)
    teacherIndex.value = buildTeacherKnowledgeIndex(graphPayload.value)
    applyGraphViewport()
    ElMessage.success('前置依赖已更新。')
  } catch (error) {
    if (hasBackendErrorCode(error, 'QUESTION_INVALID_STATUS')) {
      ElMessage.error('当前知识点状态不允许建立此前置关系。')
      await reloadGraph()
      return
    }
    ElMessage.error(resolveApiErrorMessage(error, '更新前置关系失败'))
    await reloadGraph()
  }
}

async function handleConnect(connection) {
  if (!isTeacherMode.value || !teacherRelationMode.value) {
    return
  }
  await connectPrerequisite(connection?.source, connection?.target)
}

async function triggerStudentReinforce(nodeData) {
  if (!isStudentMode.value) {
    return
  }
  const nodeId = String(nodeData?.id || '').trim()
  if (!nodeId || reinforcing.value) {
    return
  }

  reinforcing.value = true
  try {
    const payload = await fetchAdaptivePracticeList({
      count: 10,
      knowledgeId: nodeId,
    })
    const questionIds = normalizeQuestionIds(payload)
    if (!questionIds.length) {
      ElMessage.warning('当前节点暂未命中可强化题目，请先完成更多练习。')
      return
    }
    await router.push({
      path: '/student/practice',
      query: {
        adaptiveQuestionIds: questionIds.join(','),
        adaptiveDimension: normalizeDimension(nodeData?.label || nodeId),
        adaptiveMastery: (normalizeMastery(nodeData?.mastery) * 100).toFixed(2),
        sourceKnowledgeId: nodeId,
      },
    })
    ElMessage.success(`已生成 ${questionIds.length} 道弱项强化题，开始练习吧。`)
  } catch (error) {
    ElMessage.error(resolveApiErrorMessage(error, '触发弱项强化失败'))
  } finally {
    reinforcing.value = false
  }
}

function handleTeacherNodeClick(nodeData) {
  const nodeId = String(nodeData?.id || '').trim()
  if (!nodeId) {
    return
  }
  teacherActiveNodeId.value = nodeId
  const anchorNodeId = resolveOutlineAnchorNodeId(nodeId)
  if (anchorNodeId && anchorNodeId !== teacherFocusNodeId.value) {
    teacherFocusNodeId.value = anchorNodeId
  }
}

function handleNodeClick(payload) {
  const clickedNode = payload?.node
  if (!clickedNode) {
    return
  }
  const nodeData = clickedNode.data || {}
  const mastery = normalizeMastery(nodeData.mastery)

  if (isStudentMode.value) {
    if (mastery < 0.6) {
      triggerStudentReinforce(nodeData)
    }
    return
  }

  handleTeacherNodeClick(nodeData)
}

function scheduleLayoutSave(node) {
  if (!isTeacherMode.value || !teacherRelationMode.value) {
    return
  }
  const nodeId = buildNodeId(node?.id)
  const x = Number(node?.position?.x)
  const y = Number(node?.position?.y)
  if (!nodeId || !Number.isFinite(x) || !Number.isFinite(y)) {
    return
  }

  allFlowNodes.value = allFlowNodes.value.map((item) => (
    String(item?.id || '').trim() === nodeId
      ? { ...item, position: { x, y } }
      : item
  ))
  nodes.value = nodes.value.map((item) => (
    String(item?.id || '').trim() === nodeId
      ? { ...item, position: { x, y } }
      : item
  ))

  if (layoutSaveTimers.has(nodeId)) {
    clearTimeout(layoutSaveTimers.get(nodeId))
  }
  const timer = setTimeout(async () => {
    layoutSaveTimers.delete(nodeId)
    try {
      await persistKnowledgeGraphLayout([{ id: nodeId, x, y }])
    } catch (error) {
      ElMessage.error(resolveApiErrorMessage(error, '图谱布局保存失败'))
    }
  }, 260)
  layoutSaveTimers.set(nodeId, timer)
}

function handleNodeDragStop(payload) {
  if (!isTeacherMode.value || !teacherRelationMode.value) {
    return
  }
  const draggedNode = payload?.node || payload
  if (!draggedNode) {
    return
  }
  scheduleLayoutSave(draggedNode)
}

function handleTeacherQuestionDrilldown() {
  if (!teacherActiveNodeDetail.value?.id) {
    return
  }
  router.push({
    name: 'teacherQuestions',
    query: {
      knowledgeId: String(teacherActiveNodeDetail.value.id || ''),
      strategy: Number(teacherActiveNodeDetail.value.mastery || 0) < 0.6 ? 'reinforce' : 'detail',
    },
  })
}

function focusTeacherBranchFromActiveNode() {
  const anchorNodeId = resolveOutlineAnchorNodeId(teacherActiveNodeId.value)
  if (!anchorNodeId) {
    return
  }
  teacherFocusNodeId.value = anchorNodeId
}

watch(
  () => [
    props.status,
    props.mode,
    String(props.graphScope?.exam_category_code || props.graphScope?.examCategoryCode || '').trim(),
    String(props.graphScope?.joint_exam_group_code || props.graphScope?.jointExamGroupCode || '').trim(),
    String(props.graphScope?.subject_code || props.graphScope?.subjectCode || '').trim(),
    String(props.graphScope?.policy_version || props.graphScope?.policyVersion || '').trim(),
  ],
  () => {
    teacherRelationMode.value = false
    pendingPrerequisiteSource.value = null
    reloadGraph()
  },
)

watch(
  () => (Array.isArray(props.highlightedNodeIds) ? [...props.highlightedNodeIds] : []),
  () => {
    const mapped = mapGraphToFlow(graphPayload.value)
    allFlowNodes.value = mapped.nodes
    allFlowEdges.value = mapped.edges
    applyGraphViewport()
  },
)

watch(
  () => [teacherFocusNodeId.value, teacherRelationMode.value, teacherActiveNodeId.value],
  () => {
    if (!isTeacherMode.value) {
      return
    }
    applyGraphViewport()
  },
)

watch(
  () => teacherActiveNodeDetail.value,
  (detail) => {
    if (!isTeacherMode.value) {
      return
    }
    emit('active-node-change', detail ? { ...detail } : null)
  },
  { immediate: true },
)

defineExpose({
  reloadGraph,
})

onMounted(() => {
  reloadGraph()
})

onBeforeUnmount(() => {
  Array.from(layoutSaveTimers.values()).forEach((timer) => clearTimeout(timer))
  layoutSaveTimers.clear()
})
</script>

<template>
  <section class="knowledge-graph-panel">
    <header class="panel-header">
      <div>
        <p class="panel-kicker">{{ isTeacherMode ? 'Teaching Browser' : 'Adaptive Galaxy' }}</p>
        <h3>{{ panelTitle }}</h3>
        <p class="helper-text">{{ helperText }}</p>
        <p v-if="isTeacherMode && pendingPrerequisiteSource?.id" class="pending-link-tip">
          当前前置节点：{{ pendingPrerequisiteSource.label }}（请右键目标节点完成连线）
        </p>
      </div>
      <div class="panel-actions">
        <el-button
          v-if="isTeacherMode"
          :type="teacherRelationMode ? 'primary' : 'default'"
          plain
          @click="toggleTeacherRelationMode"
        >
          {{ teacherRelationMode ? '退出关系编辑' : '进入关系编辑' }}
        </el-button>
        <el-button :loading="loading || reinforcing" @click="reloadGraph">刷新图谱</el-button>
      </div>
    </header>

    <template v-if="isTeacherMode">
      <section class="teacher-summary-strip">
        <article class="summary-pill">
          <span>当前可见节点</span>
          <strong>{{ teacherVisibleSummary.visibleNodeCount }}</strong>
        </article>
        <article class="summary-pill">
          <span>细节层节点</span>
          <strong>{{ teacherVisibleSummary.detailNodeCount }}</strong>
        </article>
        <article class="summary-pill">
          <span>待干预节点</span>
          <strong>{{ teacherVisibleSummary.weakNodeCount }}</strong>
        </article>
        <article class="summary-pill">
          <span>已收起节点</span>
          <strong>{{ teacherVisibleSummary.hiddenNodeCount }}</strong>
        </article>
        <article v-if="teacherExamSectionSummary" class="summary-pill summary-pill-wide summary-pill-exam">
          <div class="exam-summary-head">
            <span class="exam-summary-kicker">树外信息</span>
            <strong>{{ teacherExamSectionSummary.label }}</strong>
          </div>
          <div class="exam-summary-cards">
            <button
              v-for="item in teacherExamSectionSummary.items"
              :key="item.id"
              type="button"
              class="exam-summary-item"
              :class="{ 'is-active': teacherExamExpandedItemId === item.id }"
              :title="item.label"
              @click="toggleTeacherExamItem(item.id)"
            >
              <span class="exam-summary-item-level">L{{ item.level }}</span>
              <strong>{{ buildKnowledgeDisplayLabel(item.label, 10) }}</strong>
              <small>{{ teacherExamExpandedItemId === item.id ? '点击收起正文' : '点击查看正文' }}</small>
            </button>
          </div>
          <transition name="exam-detail-fade" mode="out-in">
            <div
              v-if="teacherExamExpandedItemId"
              :key="teacherExamExpandedItemId"
              class="exam-summary-detail"
            >
              <template
                v-for="item in teacherExamSectionSummary.items"
                :key="`${item.id}-detail`"
              >
                <template v-if="teacherExamExpandedItemId === item.id">
                  <div class="exam-summary-detail-head">
                    <span>已展开</span>
                    <strong>{{ item.label }}</strong>
                  </div>
                  <ul v-if="item.children.length" class="exam-summary-detail-list">
                    <li v-for="child in item.children" :key="child.id">
                      {{ child.label }}
                    </li>
                  </ul>
                  <p v-else class="exam-summary-empty">当前导入数据暂无正文内容。</p>
                </template>
              </template>
            </div>
          </transition>
        </article>
      </section>

      <section class="teacher-workbench">
        <aside class="teacher-focus-panel">
          <div class="subpanel-head">
            <div>
              <h4>当前聚焦</h4>
              <p>思维导图只保留当前章节主线，点击分支节点即可切换聚焦与详情。</p>
            </div>
            <el-button text @click="resetTeacherFocus">返回科目主题</el-button>
          </div>

          <div v-if="teacherFocusDetail" class="focus-detail-card">
            <div class="focus-detail-head">
              <span class="focus-label">当前聚焦</span>
              <strong>{{ teacherFocusDetail.shortLabel || teacherFocusDetail.label }}</strong>
            </div>
            <p class="focus-detail-copy">
              {{ teacherFocusDetail.level ? `当前展示 L${teacherFocusDetail.level} 分支，导图主区已放大并只保留这一条内容主线。` : '当前展示科目主题与一级章节主线。' }}
            </p>
            <div class="detail-kpi-grid">
              <article>
                <span>层级</span>
                <strong>L{{ teacherFocusDetail.level }}</strong>
              </article>
              <article>
                <span>子节点数</span>
                <strong>{{ teacherFocusDetail.childCount }}</strong>
              </article>
              <article>
                <span>关联题数</span>
                <strong>{{ teacherFocusDetail.questionCount }}</strong>
              </article>
              <article>
                <span>掌握度</span>
                <strong>{{ Math.round(Number(teacherFocusDetail.mastery || 0) * 100) }}%</strong>
              </article>
            </div>
          </div>

          <div v-if="teacherActiveNodeDetail" class="detail-body">
            <div class="detail-title-row">
              <el-tag effect="light" type="info">L{{ teacherActiveNodeDetail.level }}</el-tag>
              <h5>{{ teacherActiveNodeDetail.shortLabel || teacherActiveNodeDetail.label }}</h5>
            </div>

            <div class="detail-copy">
              <p v-if="teacherActiveNodeDetail.fullLabel && teacherActiveNodeDetail.fullLabel !== teacherActiveNodeDetail.shortLabel">
                <span>完整内容</span>
                <strong>{{ teacherActiveNodeDetail.fullLabel }}</strong>
              </p>
              <p>
                <span>上级节点</span>
                <strong>{{ teacherActiveNodeDetail.parentLabel || '当前已是科目主题' }}</strong>
              </p>
              <p>
                <span>教学判断</span>
                <strong>{{ Number(teacherActiveNodeDetail.mastery || 0) < 0.6 ? '建议优先强化，先筛题再补依赖。' : '掌握度稳定，可继续完善结构关系。' }}</strong>
              </p>
            </div>

            <div class="detail-actions">
              <el-button plain @click="focusTeacherBranchFromActiveNode">聚焦所属分支</el-button>
              <el-button type="primary" @click="handleTeacherQuestionDrilldown">按知识点筛题</el-button>
            </div>
          </div>

          <div v-else class="focus-empty-state">
            <el-empty description="点击导图节点后查看节点详情" />
          </div>

          <div v-if="teacherRelationMode" class="formula-box">
            <p class="formula-title">节点尺寸公式</p>
            <p class="formula-line">NodeSize = 20 + ln(QuestionCount + 1) * 10</p>
            <p class="formula-block">{{ formulaText }}</p>
          </div>
        </aside>

        <div class="graph-column graph-column-wide">
          <KnowledgeGraphFlowSurface
            v-model:nodes="nodes"
            v-model:edges="edges"
            :loading="loading"
            :has-graph-data="hasGraphData"
            :is-teacher-mode="true"
            :teacher-relation-mode="teacherRelationMode"
            :flow-render-key="flowRenderKey"
            @node-click="handleNodeClick"
            @node-drag-stop="handleNodeDragStop"
            @connect="handleConnect"
          />
        </div>
      </section>
    </template>

    <template v-else>
      <div class="formula-box">
        <p class="formula-title">节点尺寸公式</p>
        <p class="formula-line">NodeSize = 20 + ln(QuestionCount + 1) * 10</p>
        <p class="formula-block">{{ formulaText }}</p>
      </div>

      <KnowledgeGraphFlowSurface
        v-model:nodes="nodes"
        v-model:edges="edges"
        :loading="loading"
        :has-graph-data="hasGraphData"
        :is-teacher-mode="false"
        :flow-render-key="flowRenderKey"
        @node-click="handleNodeClick"
      />
    </template>
  </section>
</template>

<style scoped>
.knowledge-graph-panel {
  display: grid;
  gap: 16px;
  border: 1px solid var(--qb-primary-soft-border);
  border-radius: 22px;
  padding: 18px;
  background:
    radial-gradient(circle at top right, rgba(15, 118, 110, 0.12), transparent 26%),
    linear-gradient(155deg, rgba(248, 252, 255, 0.98), rgba(235, 247, 245, 0.72));
}

.panel-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.panel-kicker {
  margin: 0 0 8px;
  color: var(--qb-text-subtle-6);
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.panel-header h3 {
  margin: 0;
  font-size: 18px;
}

.helper-text {
  margin: 6px 0 0;
  color: var(--qb-text-subtle-8);
  font-size: 13px;
  line-height: 1.6;
  max-width: 760px;
}

.pending-link-tip {
  margin: 8px 0 0;
  color: var(--el-color-primary);
  font-size: 12px;
}

.panel-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.teacher-summary-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.summary-pill {
  padding: 14px 16px;
  border-radius: 16px;
  border: 1px solid rgba(15, 118, 110, 0.12);
  background: rgba(255, 255, 255, 0.78);
  display: grid;
  gap: 8px;
}

.summary-pill span {
  color: var(--qb-text-subtle-7);
  font-size: 12px;
}

.summary-pill strong {
  color: var(--qb-text-heading);
  font-size: 24px;
}

.summary-pill-wide {
  grid-column: span 2;
}

.teacher-workbench {
  display: grid;
  grid-template-columns: minmax(280px, 340px) minmax(0, 1fr);
  gap: 14px;
  align-items: start;
}

.teacher-focus-panel {
  display: grid;
  gap: 14px;
  padding: 16px;
  border-radius: 18px;
  border: 1px solid rgba(15, 118, 110, 0.12);
  background: rgba(255, 255, 255, 0.9);
}

.graph-column {
  display: grid;
  gap: 12px;
}

.graph-column-wide .graph-surface {
  min-height: clamp(420px, 68vh, 860px);
}

.graph-column-wide .graph-flow {
  height: clamp(400px, 66vh, 840px);
}

.subpanel-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.subpanel-head h4 {
  margin: 0;
  font-size: 15px;
}

.subpanel-head p {
  margin: 6px 0 0;
  color: var(--qb-text-subtle-8);
  font-size: 12px;
  line-height: 1.5;
}

.exam-summary-card {
  display: grid;
  gap: 12px;
  padding: 14px;
  border-radius: 18px;
  border: 1px solid rgba(245, 158, 11, 0.16);
  background:
    radial-gradient(circle at top right, rgba(245, 158, 11, 0.12), transparent 24%),
    linear-gradient(160deg, rgba(255, 251, 235, 0.99), rgba(255, 247, 237, 0.94));
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.04);
}

.exam-summary-head {
  display: grid;
  gap: 4px;
}

.exam-summary-kicker {
  color: var(--qb-text-subtle-6);
  font-size: 12px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.exam-summary-head strong {
  color: var(--qb-text-heading);
  font-size: 15px;
}

.exam-summary-cards {
  display: grid;
  gap: 10px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.exam-summary-item {
  border: 1px solid rgba(245, 158, 11, 0.16);
  border-radius: 16px;
  padding: 14px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(255, 250, 241, 0.92));
  display: grid;
  gap: 8px;
  text-align: left;
  cursor: pointer;
  transition: transform 0.16s ease, border-color 0.16s ease, box-shadow 0.16s ease;
}

.exam-summary-item:hover {
  transform: translateY(-1px);
  border-color: rgba(245, 158, 11, 0.3);
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
}

.exam-summary-item.is-active {
  border-color: rgba(245, 158, 11, 0.4);
  box-shadow:
    inset 0 0 0 1px rgba(245, 158, 11, 0.18),
    0 12px 26px rgba(245, 158, 11, 0.08);
}

.exam-summary-item-level {
  color: var(--qb-text-subtle-6);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.exam-summary-item strong {
  color: var(--qb-text-heading);
  font-size: 15px;
  line-height: 1.4;
}

.exam-summary-item small {
  color: var(--qb-text-subtle-7);
  font-size: 12px;
}

.exam-summary-detail {
  display: grid;
  gap: 10px;
  padding: 14px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(245, 158, 11, 0.16);
}

.exam-summary-detail-head {
  display: grid;
  gap: 4px;
}

.exam-summary-detail-head span {
  color: var(--qb-text-subtle-6);
  font-size: 12px;
}

.exam-summary-detail-head strong {
  color: var(--qb-text-heading);
}

.exam-summary-detail-list {
  margin: 0;
  padding-left: 18px;
  display: grid;
  gap: 8px;
  color: var(--qb-text-subtle-8);
  font-size: 13px;
  line-height: 1.6;
}

.exam-summary-empty {
  margin: 0;
  color: var(--qb-text-subtle-7);
  font-size: 13px;
}

.exam-detail-fade-enter-active,
.exam-detail-fade-leave-active {
  transition: opacity 0.16s ease, transform 0.16s ease;
}

.exam-detail-fade-enter-from,
.exam-detail-fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

.focus-detail-card {
  display: grid;
  gap: 10px;
  padding: 14px;
  border-radius: 16px;
  border: 1px solid rgba(15, 118, 110, 0.12);
  background: linear-gradient(135deg, rgba(219, 242, 236, 0.92), rgba(255, 255, 255, 0.95));
}

.focus-detail-head {
  display: grid;
  gap: 4px;
}

.focus-label {
  color: var(--qb-text-subtle-6);
  font-size: 12px;
}

.focus-detail-head strong {
  color: var(--qb-text-heading);
  font-size: 20px;
}

.focus-detail-copy {
  margin: 0;
  color: var(--qb-text-subtle-8);
  font-size: 13px;
  line-height: 1.6;
}

.formula-box {
  border: 1px dashed rgba(15, 118, 110, 0.18);
  border-radius: 14px;
  padding: 12px 14px;
  background: rgba(244, 251, 249, 0.78);
}

.formula-title {
  margin: 0;
  font-weight: 600;
  font-size: 13px;
}

.formula-line {
  margin: 6px 0 0;
  font-family: Menlo, Consolas, Monaco, monospace;
  font-size: 12px;
  color: var(--qb-text-subtle-8);
}

.formula-block {
  margin: 4px 0 0;
  font-size: 12px;
  color: var(--qb-text-subtle-8);
}

.graph-surface {
  min-height: clamp(340px, 56vh, 700px);
  border: 1px solid rgba(15, 118, 110, 0.1);
  border-radius: 20px;
  background:
    radial-gradient(circle at top right, rgba(15, 118, 110, 0.06), transparent 22%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(248, 251, 250, 0.94));
  overflow: hidden;
}

.graph-flow {
  width: 100%;
  height: clamp(320px, 54vh, 680px);
}

.detail-body {
  display: grid;
  gap: 14px;
}

.focus-empty-state {
  border: 1px dashed rgba(15, 118, 110, 0.16);
  border-radius: 16px;
  padding: 14px;
  background: rgba(255, 255, 255, 0.72);
}

.detail-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.detail-title-row h5 {
  margin: 0;
  color: var(--qb-text-heading);
  font-size: 18px;
  line-height: 1.4;
}

.detail-kpi-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.detail-kpi-grid article {
  padding: 12px;
  border-radius: 14px;
  background: rgba(244, 249, 248, 0.96);
  display: grid;
  gap: 6px;
}

.detail-kpi-grid span,
.detail-copy span {
  color: var(--qb-text-subtle-6);
  font-size: 12px;
}

.detail-kpi-grid strong,
.detail-copy strong {
  color: var(--qb-text-heading);
  line-height: 1.5;
}

.detail-copy {
  display: grid;
  gap: 10px;
}

.detail-copy p {
  margin: 0;
  display: grid;
  gap: 4px;
}

.detail-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

@media (max-width: 1180px) {
  .teacher-workbench {
    grid-template-columns: minmax(0, 1fr);
  }

  .teacher-summary-strip {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .summary-pill-wide {
    grid-column: span 2;
  }
}

@media (max-width: 720px) {
  .panel-header {
    flex-direction: column;
    align-items: stretch;
  }

  .panel-actions {
    flex-wrap: wrap;
  }

  .teacher-summary-strip {
    grid-template-columns: minmax(0, 1fr);
  }

  .detail-kpi-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .summary-pill-wide {
    grid-column: span 1;
  }

  .exam-summary-cards {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
