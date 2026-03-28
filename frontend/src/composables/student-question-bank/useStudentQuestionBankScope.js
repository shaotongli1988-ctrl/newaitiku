import { computed } from 'vue'

function toText(value) {
  return String(value || '').trim()
}

function resolveSourceValue(source) {
  if (typeof source === 'function') {
    return toText(source())
  }
  if (source && typeof source === 'object' && 'value' in source) {
    return toText(source.value)
  }
  return toText(source)
}

export function useStudentQuestionBankScope({
  route,
  currentSubjectCode = '',
} = {}) {
  const subjectCode = computed(() => toText(route?.query?.subjectCode))
  const chapterName = computed(() => toText(route?.query?.chapterName))
  const chapterCode = computed(() => toText(route?.query?.chapterCode))
  const pointCode = computed(() => toText(route?.query?.pointCode))
  const pointName = computed(() => toText(route?.query?.pointName))
  const knowledgeId = computed(() => toText(route?.query?.knowledgeId))
  const knowledgePathNodeId = computed(() => toText(route?.query?.knowledgePathNodeId))
  const pathLabel = computed(() => toText(route?.query?.pathLabel))
  const effectiveSubjectCode = computed(() => subjectCode.value || resolveSourceValue(currentSubjectCode))

  function buildScopeFilters(extra = {}) {
    return {
      ...extra,
      subjectCode: effectiveSubjectCode.value,
      knowledgePathNodeId: knowledgePathNodeId.value,
      chapterCode: chapterCode.value,
      pointCode: pointCode.value,
      knowledgeId: knowledgeId.value,
    }
  }

  function buildAnalysisQuery(extra = {}) {
    const query = { ...(extra || {}) }
    if (effectiveSubjectCode.value) {
      query.subjectCode = effectiveSubjectCode.value
    }
    if (chapterCode.value) {
      query.chapterCode = chapterCode.value
      query.chapterName = chapterName.value
    }
    if (pointCode.value) {
      query.pointCode = pointCode.value
      query.pointName = pointName.value
    }
    if (knowledgeId.value) {
      query.knowledgeId = knowledgeId.value
    }
    if (knowledgePathNodeId.value) {
      query.knowledgePathNodeId = knowledgePathNodeId.value
    }
    if (pathLabel.value) {
      query.pathLabel = pathLabel.value
    }
    return query
  }

  return {
    subjectCode,
    chapterName,
    chapterCode,
    pointCode,
    pointName,
    knowledgeId,
    knowledgePathNodeId,
    pathLabel,
    effectiveSubjectCode,
    buildScopeFilters,
    buildAnalysisQuery,
  }
}
