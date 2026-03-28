function toText(value) {
  return String(value || '').trim()
}

function toInt(value, fallback = 0) {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? Math.max(0, Math.trunc(parsed)) : fallback
}

function normalizeSubjectType(subjectType) {
  return toText(subjectType).toUpperCase() || 'PROFESSIONAL'
}

function toSearchText(value) {
  return toText(value).toLowerCase()
}

export function normalizeStudentCoreSubjects(payloadOrRows = {}) {
  const sourceRows = Array.isArray(payloadOrRows)
    ? payloadOrRows
    : Array.isArray(payloadOrRows?.coreSubjects)
      ? payloadOrRows.coreSubjects
      : []

  const seen = new Set()

  return sourceRows
    .map((item) => {
      const subjectCode = toText(item?.subjectCode)
      if (!subjectCode || seen.has(subjectCode)) {
        return null
      }
      seen.add(subjectCode)
      return {
        subjectCode,
        subjectName: toText(item?.subjectName || item?.subjectCode) || subjectCode,
        subjectType: normalizeSubjectType(item?.subjectType),
      }
    })
    .filter(Boolean)
}

function collectAncestorIds(index, nodeId) {
  const ancestors = []
  const visited = new Set()
  let currentId = toText(nodeId)
  while (currentId) {
    const parentId = toText(index?.parentByChild?.get(currentId))
    if (!parentId || visited.has(parentId)) {
      break
    }
    visited.add(parentId)
    ancestors.push(parentId)
    currentId = parentId
  }
  return ancestors
}

function resolveSectionId(index, nodeId, { contentRootId = '', introNodeId = '', examNodeId = '' } = {}) {
  const lineage = [toText(nodeId), ...collectAncestorIds(index, nodeId)]
  if (!lineage[0]) {
    return ''
  }
  if (introNodeId && lineage.includes(introNodeId)) {
    return introNodeId
  }
  if (examNodeId && lineage.includes(examNodeId)) {
    return examNodeId
  }
  const level3SectionId = lineage.find((item) => Number(index?.nodesById?.get(item)?.level || 0) === 3)
  if (level3SectionId) {
    return level3SectionId
  }
  if (contentRootId && lineage.includes(contentRootId)) {
    return contentRootId
  }
  return lineage.find((item) => Number(index?.nodesById?.get(item)?.level || 0) === 2) || lineage[0]
}

export function normalizeStudentSyllabusCatalog(payload = {}) {
  const sourceSubjects = Array.isArray(payload?.subjects) ? payload.subjects : []
  const subjects = sourceSubjects
    .map((item) => ({
      subjectCode: toText(item?.subjectCode),
      subjectName: toText(item?.subjectName),
      subjectType: normalizeSubjectType(item?.subjectType),
      examCategoryCode: toText(item?.examCategoryCode),
      examCategoryName: toText(item?.examCategoryName),
      jointExamGroupCode: toText(item?.jointExamGroupCode),
      jointExamGroupName: toText(item?.jointExamGroupName),
      nodeCount: toInt(item?.nodeCount),
      sourceFile: toText(item?.sourceFile),
      tree: item?.tree && typeof item.tree === 'object' ? item.tree : {},
      nodes: Array.isArray(item?.nodes) ? item.nodes : [],
    }))
    .filter((item) => item.subjectCode && item.subjectName)
    .sort((left, right) =>
      [
        toText(left.examCategoryCode),
        toText(left.jointExamGroupCode),
        String(left.subjectType !== 'PUBLIC'),
        toText(left.subjectName),
      ].join('::').localeCompare(
        [
          toText(right.examCategoryCode),
          toText(right.jointExamGroupCode),
          String(right.subjectType !== 'PUBLIC'),
          toText(right.subjectName),
        ].join('::'),
        'zh-Hans-CN',
      ))

  return {
    generatedAt: toText(payload?.generatedAt),
    policyVersionCode: toText(payload?.policyVersionCode),
    subjectCount: toInt(payload?.subjectCount, subjects.length),
    nodeCount: toInt(payload?.nodeCount),
    examCategoryCount: toInt(payload?.examCategoryCount),
    jointExamGroupCount: toInt(payload?.jointExamGroupCount),
    publicSubjectCount: toInt(payload?.publicSubjectCount),
    professionalSubjectCount: toInt(payload?.professionalSubjectCount),
    subjects,
  }
}

export function buildStudentSyllabusGraphPayload(subject = {}) {
  const sourceNodes = Array.isArray(subject?.nodes) ? subject.nodes : []
  const nodes = sourceNodes
    .map((item) => {
      const id = toText(item?.id)
      if (!id) {
        return null
      }
      return {
        id,
        label: toText(item?.name || item?.label || id) || id,
        parentId: toText(item?.parent_id || item?.parentId) || null,
        level: toInt(item?.level),
        sort: toInt(item?.sort),
        mastery: 1,
        questionCount: 0,
      }
    })
    .filter(Boolean)

  const links = nodes
    .filter((item) => item.parentId)
    .map((item) => ({
      source: item.parentId,
      target: item.id,
      type: 'parent',
    }))

  return { nodes, links }
}

export function buildStudentSyllabusOverview(payload = {}) {
  const catalog = normalizeStudentSyllabusCatalog(payload)
  const examCategoryCodes = new Set()
  const jointExamGroupCodes = new Set()
  catalog.subjects.forEach((item) => {
    if (item.examCategoryCode) {
      examCategoryCodes.add(item.examCategoryCode)
    }
    if (item.jointExamGroupCode) {
      jointExamGroupCodes.add(item.jointExamGroupCode)
    }
  })
  return {
    subjectCount: catalog.subjects.length,
    nodeCount: catalog.subjects.reduce((sum, item) => sum + toInt(item.nodeCount), 0),
    publicSubjectCount: catalog.subjects.filter((item) => item.subjectType === 'PUBLIC').length,
    professionalSubjectCount: catalog.subjects.filter((item) => item.subjectType !== 'PUBLIC').length,
    examCategoryCount: examCategoryCodes.size,
    jointExamGroupCount: jointExamGroupCodes.size,
  }
}

export function buildStudentSyllabusDisplayPlan(catalogPayload = {}, dashboardPayload = {}) {
  const catalog = normalizeStudentSyllabusCatalog(catalogPayload)
  const coreSubjects = normalizeStudentCoreSubjects(dashboardPayload)
  const subjectByCode = new Map(
    catalog.subjects.map((item) => [toText(item.subjectCode), item]),
  )
  const requiredSubjects = coreSubjects
    .map((item) => subjectByCode.get(toText(item.subjectCode)))
    .filter(Boolean)
  const requiredCodeSet = new Set(requiredSubjects.map((item) => toText(item.subjectCode)))

  if (!requiredSubjects.length) {
    catalog.subjects.slice(0, 4).forEach((item) => {
      const subjectCode = toText(item.subjectCode)
      if (!subjectCode || requiredCodeSet.has(subjectCode)) {
        return
      }
      requiredCodeSet.add(subjectCode)
      requiredSubjects.push(item)
    })
  }

  return {
    requiredSubjects,
    optionalSubjects: catalog.subjects.filter((item) => !requiredCodeSet.has(toText(item.subjectCode))),
    requiredSubjectCodes: Array.from(requiredCodeSet),
    coreSubjects,
  }
}

export function formatStudentSyllabusTimestamp(value) {
  const normalizedValue = toText(value)
  if (!normalizedValue) {
    return ''
  }
  const parsed = new Date(normalizedValue)
  if (Number.isNaN(parsed.getTime())) {
    return normalizedValue
  }
  const pad = (item) => String(item).padStart(2, '0')
  return [
    parsed.getFullYear(),
    pad(parsed.getMonth() + 1),
    pad(parsed.getDate()),
  ].join('-') + ` ${pad(parsed.getHours())}:${pad(parsed.getMinutes())}`
}

export function searchStudentSyllabusContent(index = {}, keyword = '', {
  contentRootId = '',
  introNodeId = '',
  examNodeId = '',
} = {}) {
  const normalizedKeyword = toSearchText(keyword)
  if (!normalizedKeyword) {
    return {
      keyword: '',
      totalMatches: 0,
      matchedNodeIds: [],
      expandedNodeIds: [],
      matchedSectionIds: [],
      firstMatchNodeId: '',
      firstMatchSectionId: '',
    }
  }

  const matchedNodeIds = []
  const expandedNodeIdSet = new Set()
  const matchedSectionIdSet = new Set()

  const candidateNodes = Array.isArray(index?.allNodes) ? index.allNodes : []
  candidateNodes.forEach((node) => {
    const nodeId = toText(node?.id)
    const nodeLabel = toSearchText(node?.label)
    const nodeLevel = toInt(node?.level)
    if (!nodeId || nodeLevel < 2 || !nodeLabel.includes(normalizedKeyword)) {
      return
    }

    matchedNodeIds.push(nodeId)
    collectAncestorIds(index, nodeId).forEach((ancestorId) => {
      if (ancestorId && ancestorId !== contentRootId) {
        expandedNodeIdSet.add(ancestorId)
      }
    })

    const sectionId = resolveSectionId(index, nodeId, { contentRootId, introNodeId, examNodeId })
    if (sectionId) {
      matchedSectionIdSet.add(sectionId)
    }
  })

  return {
    keyword: normalizedKeyword,
    totalMatches: matchedNodeIds.length,
    matchedNodeIds,
    expandedNodeIds: Array.from(expandedNodeIdSet),
    matchedSectionIds: Array.from(matchedSectionIdSet),
    firstMatchNodeId: matchedNodeIds[0] || '',
    firstMatchSectionId: Array.from(matchedSectionIdSet)[0] || '',
  }
}
