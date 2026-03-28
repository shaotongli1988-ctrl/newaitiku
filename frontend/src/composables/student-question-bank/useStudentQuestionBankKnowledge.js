import { ref } from 'vue'
import { ElMessage } from '@/ui/feedback'
import {
  buildKnowledgeLevelTreeState,
  buildKnowledgeSelectorState,
  buildKnowledgeSemanticMap,
} from '../../utils/knowledgeTree'

function toText(value) {
  return String(value || '').trim()
}

export function useStudentQuestionBankKnowledge({
  route,
  router,
  effectiveSubjectCode,
  knowledgePathNodeId,
  knowledgeId,
  chapterCode,
  pointCode,
  fetchKnowledgeTree,
  loadErrorMessage = '知识树加载失败',
} = {}) {
  const knowledgeTreeLoading = ref(false)
  const knowledgeFilterOptions = ref([])
  const selectedKnowledgePath = ref([])
  const knowledgeSelectorState = ref(buildKnowledgeSelectorState({}))
  const knowledgeSemanticMap = ref({})

  function resetKnowledgeState() {
    knowledgeSelectorState.value = buildKnowledgeSelectorState({})
    knowledgeFilterOptions.value = []
    knowledgeSemanticMap.value = {}
    selectedKnowledgePath.value = []
  }

  function resolveKnowledgeFilterPathByRoute() {
    const selectorState = knowledgeSelectorState.value || {}
    const pathMap = selectorState?.pathMap || {}
    const chapterCodeMap = selectorState?.chapterCodeMap || {}
    const pointCodeMap = selectorState?.pointCodeMap || {}
    const targetNodeId = toText(knowledgePathNodeId?.value) || toText(knowledgeId?.value)

    if (targetNodeId && Array.isArray(pathMap[targetNodeId])) {
      return pathMap[targetNodeId]
    }

    const matchedPointEntry = Object.entries(pointCodeMap).find(([, value]) => toText(value) === toText(pointCode?.value))
    if (matchedPointEntry && Array.isArray(pathMap[matchedPointEntry[0]])) {
      return pathMap[matchedPointEntry[0]]
    }

    const matchedChapterEntry = Object.entries(chapterCodeMap).find(([, value]) => toText(value) === toText(chapterCode?.value))
    if (matchedChapterEntry && Array.isArray(pathMap[matchedChapterEntry[0]])) {
      return pathMap[matchedChapterEntry[0]]
    }

    return []
  }

  function syncSelectedKnowledgePathFromRoute() {
    selectedKnowledgePath.value = resolveKnowledgeFilterPathByRoute()
  }

  async function loadKnowledgeTree() {
    if (!toText(effectiveSubjectCode?.value)) {
      resetKnowledgeState()
      return
    }

    knowledgeTreeLoading.value = true
    try {
      const response = await fetchKnowledgeTree({
        status: 'ENABLED',
        subject_code: effectiveSubjectCode.value,
      })
      const selectorState = buildKnowledgeSelectorState(response?.data || response || {})
      const levelTreeState = buildKnowledgeLevelTreeState(selectorState, { startLevel: 3, endLevel: 5 })
      knowledgeSelectorState.value = selectorState
      knowledgeFilterOptions.value = Array.isArray(levelTreeState?.options) ? levelTreeState.options : []
      knowledgeSemanticMap.value = buildKnowledgeSemanticMap(selectorState)
      syncSelectedKnowledgePathFromRoute()
    } catch (error) {
      resetKnowledgeState()
      ElMessage.error(toText(error?.response?.data?.message || error?.message || loadErrorMessage))
    } finally {
      knowledgeTreeLoading.value = false
    }
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
    const semanticMap = knowledgeSemanticMap.value || {}
    const nextQuery = { ...(route?.query || {}) }

    selectedKnowledgePath.value = normalizedPath
    delete nextQuery.knowledgePathNodeId
    delete nextQuery.knowledgeId
    delete nextQuery.chapterCode
    delete nextQuery.chapterName
    delete nextQuery.pointCode
    delete nextQuery.pointName
    delete nextQuery.pathLabel

    if (!normalizedPath.length) {
      await router.replace({ path: route.path, query: nextQuery })
      return
    }

    const selectedId = normalizedPath[normalizedPath.length - 1]
    const selectedLevel = Number(levelById[selectedId] || 0)
    const semantic = semanticMap[selectedId] || {}
    const semanticTrail = Array.isArray(semantic?.semanticTrail) ? semantic.semanticTrail : []
    const chapterNode = semanticTrail.find((item) => Number(item.level || 0) === 4) || {}

    nextQuery.knowledgePathNodeId = selectedId
    nextQuery.pathLabel = toText(
      semantic?.fullPathLabel
      || semanticTrail.map((item) => item.label).join(' / ')
      || normalizedPath.map((item) => toText(labelMap[item] || item)).join(' / '),
    )

    if (selectedLevel >= 5) {
      nextQuery.knowledgeId = selectedId
      nextQuery.pointCode = toText(pointCodeMap[selectedId])
      nextQuery.pointName = toText(labelMap[selectedId] || selectedId)
      if (chapterNode?.id) {
        nextQuery.chapterCode = toText(chapterCodeMap[chapterNode.id])
        nextQuery.chapterName = toText(chapterNode.label || chapterNode.id)
      }
    } else if (selectedLevel === 4) {
      nextQuery.chapterCode = toText(chapterCodeMap[selectedId])
      nextQuery.chapterName = toText(labelMap[selectedId] || selectedId)
    }

    await router.replace({ path: route.path, query: nextQuery })
  }

  return {
    knowledgeTreeLoading,
    knowledgeFilterOptions,
    selectedKnowledgePath,
    knowledgeSelectorState,
    knowledgeSemanticMap,
    loadKnowledgeTree,
    handleKnowledgePathChange,
    syncSelectedKnowledgePathFromRoute,
    resetKnowledgeState,
  }
}
