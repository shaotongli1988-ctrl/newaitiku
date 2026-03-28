function normalizeString(value) {
  return String(value || '').trim()
}

function normalizeNumber(value, fallback = 0) {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : fallback
}

function sortByLevelAndLabel(left, right) {
  const levelDiff = normalizeNumber(left?.level) - normalizeNumber(right?.level)
  if (levelDiff !== 0) {
    return levelDiff
  }
  const sortDiff = normalizeNumber(left?.sort) - normalizeNumber(right?.sort)
  if (sortDiff !== 0) {
    return sortDiff
  }
  return normalizeString(left?.label || left?.id).localeCompare(
    normalizeString(right?.label || right?.id),
    'zh-Hans-CN',
  )
}

function collectDescendants(nodeId, childrenByParent, visited = new Set()) {
  const normalizedNodeId = normalizeString(nodeId)
  if (!normalizedNodeId || visited.has(normalizedNodeId)) {
    return []
  }
  visited.add(normalizedNodeId)
  const directChildren = childrenByParent.get(normalizedNodeId) || []
  const collected = []
  directChildren.forEach((childId) => {
    const normalizedChildId = normalizeString(childId)
    if (!normalizedChildId) {
      return
    }
    collected.push(normalizedChildId)
    collectDescendants(normalizedChildId, childrenByParent, visited).forEach((descendantId) => {
      if (!collected.includes(descendantId)) {
        collected.push(descendantId)
      }
    })
  })
  return collected
}

function collectAncestors(nodeId, parentByChild) {
  const ancestors = []
  const seen = new Set()
  let currentId = normalizeString(nodeId)
  while (currentId) {
    const parentId = normalizeString(parentByChild.get(currentId))
    if (!parentId || seen.has(parentId)) {
      break
    }
    seen.add(parentId)
    ancestors.push(parentId)
    currentId = parentId
  }
  return ancestors
}

function groupChildren(childrenByParent, parentId) {
  return (childrenByParent.get(normalizeString(parentId)) || []).slice()
}

const LEADING_VERB_PATTERN = /^(掌握|了解|理解|熟悉|能够|会|认识|知道|具备)/

export function buildKnowledgeDisplayLabel(label = '', maxLength = 14) {
  const normalizedLabel = normalizeString(label)
  if (!normalizedLabel) {
    return ''
  }

  const firstClause = normalizedLabel
    .split(/[，。；：、\s]/)
    .map((item) => normalizeString(item))
    .find((item) => item)
    || normalizedLabel

  const withoutVerb = firstClause.replace(LEADING_VERB_PATTERN, '')
  const candidate = normalizeString(withoutVerb || firstClause || normalizedLabel)
  if (candidate.length <= maxLength) {
    return candidate
  }
  return `${candidate.slice(0, Math.max(4, maxLength - 1))}…`
}

function collectLeafCount(nodeId, childrenByParent, nodesById) {
  const childIds = groupChildren(childrenByParent, nodeId).filter((childId) => nodesById.has(childId))
  if (!childIds.length) {
    return 1
  }
  return childIds.reduce((sum, childId) => sum + collectLeafCount(childId, childrenByParent, nodesById), 0)
}

export function buildTeacherKnowledgeIndex(graphPayload = {}) {
  const rawNodes = Array.isArray(graphPayload?.nodes) ? graphPayload.nodes : []
  const rawLinks = Array.isArray(graphPayload?.links) ? graphPayload.links : []

  const nodesById = new Map()
  rawNodes.forEach((node) => {
    const id = normalizeString(node?.id)
    if (!id) {
      return
    }
    nodesById.set(id, {
      id,
      label: normalizeString(node?.label || id),
      shortLabel: buildKnowledgeDisplayLabel(node?.label || id),
      level: normalizeNumber(node?.level),
      sort: normalizeNumber(node?.sort),
      mastery: normalizeNumber(node?.mastery),
      questionCount: Math.max(0, Math.floor(normalizeNumber(node?.questionCount))),
    })
  })

  const childrenByParent = new Map()
  const parentByChild = new Map()
  const prerequisiteOutgoing = new Map()
  const prerequisiteIncoming = new Map()

  rawLinks.forEach((link) => {
    const source = normalizeString(link?.source)
    const target = normalizeString(link?.target)
    if (!source || !target || source === target || !nodesById.has(source) || !nodesById.has(target)) {
      return
    }

    if (normalizeString(link?.type) === 'parent') {
      const nextChildren = childrenByParent.get(source) || []
      if (!nextChildren.includes(target)) {
        nextChildren.push(target)
      }
      childrenByParent.set(source, nextChildren)
      if (!parentByChild.has(target)) {
        parentByChild.set(target, source)
      }
      return
    }

    if (normalizeString(link?.type) === 'prerequisite') {
      const nextOutgoing = prerequisiteOutgoing.get(source) || []
      if (!nextOutgoing.includes(target)) {
        nextOutgoing.push(target)
      }
      prerequisiteOutgoing.set(source, nextOutgoing)

      const nextIncoming = prerequisiteIncoming.get(target) || []
      if (!nextIncoming.includes(source)) {
        nextIncoming.push(source)
      }
      prerequisiteIncoming.set(target, nextIncoming)
    }
  })

  const allNodes = Array.from(nodesById.values()).sort(sortByLevelAndLabel)
  const outlineRows = allNodes
    .filter((node) => normalizeNumber(node.level) > 0 && normalizeNumber(node.level) <= 3)
    .map((node) => {
      const descendantIds = collectDescendants(node.id, childrenByParent)
      const descendants = descendantIds
        .map((item) => nodesById.get(item))
        .filter(Boolean)
      const weakCount = descendants.filter((item) => normalizeNumber(item.mastery) < 0.6).length
      const leafCount = descendants.filter((item) => normalizeNumber(item.level) >= 5).length
      return {
        ...node,
        weakCount,
        leafCount,
        descendantCount: descendants.length,
      }
    })

  return {
    allNodes,
    nodesById,
    rawLinks,
    childrenByParent,
    parentByChild,
    prerequisiteOutgoing,
    prerequisiteIncoming,
    outlineRows,
  }
}

export function buildTeacherOutlineTree(index) {
  const rows = Array.isArray(index?.outlineRows) ? index.outlineRows : []
  const rowMap = new Map(
    rows.map((row) => [
      normalizeString(row.id),
      {
        ...row,
        children: [],
      },
    ]),
  )

  const roots = []
  rowMap.forEach((row, rowId) => {
    const parentId = normalizeString(index?.parentByChild?.get(rowId))
    if (parentId && rowMap.has(parentId)) {
      rowMap.get(parentId).children.push(row)
      return
    }
    roots.push(row)
  })

  function sortTree(items) {
    return items
      .slice()
      .sort(sortByLevelAndLabel)
      .map((item) => ({
        ...item,
        children: sortTree(Array.isArray(item.children) ? item.children : []),
      }))
  }

  return sortTree(roots)
}

export function resolveTeacherSpecialSections(index) {
  const rows = Array.isArray(index?.allNodes) ? index.allNodes : []
  const result = {
    subjectRootId: '',
    contentNodeId: '',
    contentNodeLabel: '',
    examNodeId: '',
    examNodeLabel: '',
    introNodeId: '',
    introNodeLabel: '',
  }

  rows.forEach((row) => {
    if (normalizeNumber(row?.level) !== 2) {
      return
    }
    const label = normalizeString(row?.label)
    if (label === '具体内容与要求') {
      result.contentNodeId = normalizeString(row?.id)
      result.contentNodeLabel = label
      return
    }
    if (label === '考试形式与参考题型') {
      result.examNodeId = normalizeString(row?.id)
      result.examNodeLabel = label
      return
    }
    if (label === '科目简介') {
      result.introNodeId = normalizeString(row?.id)
      result.introNodeLabel = label
    }
  })

  result.subjectRootId = normalizeString(index?.parentByChild?.get(result.contentNodeId || result.examNodeId || result.introNodeId))

  return result
}

export function buildTeacherExamSectionSummary(index) {
  const specialSections = resolveTeacherSpecialSections(index)
  const examNodeId = normalizeString(specialSections.examNodeId)
  if (!examNodeId || !index?.nodesById?.has(examNodeId)) {
    return null
  }

  const examChildren = groupChildren(index.childrenByParent, examNodeId)
    .map((childId) => index.nodesById.get(childId))
    .filter(Boolean)
    .sort(sortByLevelAndLabel)

  return {
    id: examNodeId,
    label: specialSections.examNodeLabel || '考试形式与参考题型',
    items: examChildren.map((item) => ({
      id: item.id,
      label: item.label,
      shortLabel: item.shortLabel,
      level: item.level,
      children: groupChildren(index.childrenByParent, item.id)
        .map((childId) => index.nodesById.get(childId))
        .filter(Boolean)
        .sort(sortByLevelAndLabel)
        .map((child) => ({
          id: child.id,
          label: child.label,
          shortLabel: child.shortLabel,
          level: child.level,
        })),
    })),
  }
}

export function buildTeacherContentOutlineTree(index) {
  const specialSections = resolveTeacherSpecialSections(index)
  const contentNodeId = normalizeString(specialSections.contentNodeId)
  if (!contentNodeId) {
    return []
  }

  function buildBranch(nodeId) {
    const node = index?.nodesById?.get(nodeId)
    if (!node || normalizeNumber(node.level) < 3) {
      return null
    }
    const childIds = groupChildren(index.childrenByParent, nodeId)
    const children = childIds
      .map((childId) => buildBranch(childId))
      .filter(Boolean)
      .sort(sortByLevelAndLabel)
    const descendantIds = collectDescendants(nodeId, index.childrenByParent)
    const descendants = descendantIds.map((item) => index.nodesById.get(item)).filter(Boolean)
    return {
      ...node,
      weakCount: descendants.filter((item) => normalizeNumber(item.mastery) < 0.6).length,
      descendantCount: descendants.length,
      children,
    }
  }

  return groupChildren(index.childrenByParent, contentNodeId)
    .map((childId) => buildBranch(childId))
    .filter(Boolean)
    .sort(sortByLevelAndLabel)
}

export function resolveTeacherFocusNodeId(index, requestedNodeId = '') {
  const requestedId = normalizeString(requestedNodeId)
  if (requestedId && index?.nodesById?.has(requestedId)) {
    return requestedId
  }

  const contentOutlineTree = buildTeacherContentOutlineTree(index)
  const firstContentRow = Array.isArray(contentOutlineTree) ? contentOutlineTree[0] : null
  if (firstContentRow?.id) {
    return normalizeString(firstContentRow.id)
  }

  const outlineRows = Array.isArray(index?.outlineRows) ? index.outlineRows : []
  const preferredRow = outlineRows.find((item) => normalizeNumber(item.level) === 3)
    || outlineRows.find((item) => normalizeNumber(item.level) === 2)
    || outlineRows[0]
  return normalizeString(preferredRow?.id)
}

export function collectTeacherVisibleNodeIds(index, focusNodeId = '') {
  const normalizedFocusId = normalizeString(focusNodeId)
  const specialSections = resolveTeacherSpecialSections(index)
  const subjectRootId = normalizeString(specialSections.subjectRootId)
  const contentNodeId = normalizeString(specialSections.contentNodeId)
  const contentOutlineTree = buildTeacherContentOutlineTree(index)
  if (!normalizedFocusId) {
    const visibleIds = new Set()
    if (subjectRootId) {
      visibleIds.add(subjectRootId)
    }
    contentOutlineTree.forEach((item) => {
      visibleIds.add(normalizeString(item.id))
    })
    return Array.from(visibleIds)
  }
  if (!index?.nodesById?.has(normalizedFocusId)) {
    return collectTeacherVisibleNodeIds(index, '')
  }

  const visibleIds = new Set()
  if (subjectRootId) {
    visibleIds.add(subjectRootId)
  }
  collectAncestors(normalizedFocusId, index.parentByChild)
    .filter((item) => item !== contentNodeId)
    .forEach((item) => visibleIds.add(item))
  visibleIds.add(normalizedFocusId)
  collectDescendants(normalizedFocusId, index.childrenByParent).forEach((item) => visibleIds.add(item))
  return Array.from(visibleIds)
}

export function buildTeacherVisibleSummary(index, visibleNodeIds = []) {
  const visibleIds = Array.isArray(visibleNodeIds) ? visibleNodeIds.map((item) => normalizeString(item)).filter((item) => item) : []
  const visibleNodes = visibleIds.map((item) => index?.nodesById?.get(item)).filter(Boolean)
  const weakCount = visibleNodes.filter((item) => normalizeNumber(item.mastery) < 0.6).length
  const detailNodeCount = visibleNodes.filter((item) => normalizeNumber(item.level) >= 4).length
  const leafNodeCount = visibleNodes.filter((item) => normalizeNumber(item.level) >= 5).length
  return {
    visibleNodeCount: visibleNodes.length,
    weakNodeCount: weakCount,
    detailNodeCount,
    leafNodeCount,
    hiddenNodeCount: Math.max(0, (index?.allNodes?.length || 0) - visibleNodes.length),
  }
}

export function buildTeacherNodeDetail(index, nodeId = '') {
  const normalizedNodeId = normalizeString(nodeId)
  const node = index?.nodesById?.get(normalizedNodeId)
  if (!node) {
    return null
  }
  const parentId = normalizeString(index?.parentByChild?.get(normalizedNodeId))
  const parentNode = parentId ? index?.nodesById?.get(parentId) : null
  const childIds = index?.childrenByParent?.get(normalizedNodeId) || []
  const prerequisiteOutgoing = index?.prerequisiteOutgoing?.get(normalizedNodeId) || []
  const prerequisiteIncoming = index?.prerequisiteIncoming?.get(normalizedNodeId) || []
  return {
    ...node,
    fullLabel: node.label,
    parentId,
    parentLabel: normalizeString(parentNode?.label || ''),
    childCount: childIds.length,
    outgoingPrerequisiteCount: prerequisiteOutgoing.length,
    incomingPrerequisiteCount: prerequisiteIncoming.length,
  }
}

export function buildTeacherAutoLayout(index, visibleNodeIds = [], { xStart = 120, yStart = 100, xGap = 220, yGap = 120 } = {}) {
  const visibleIdSet = new Set(
    (Array.isArray(visibleNodeIds) ? visibleNodeIds : [])
      .map((item) => normalizeString(item))
      .filter((item) => item),
  )
  const positions = new Map()
  let currentY = yStart

  const rootIds = Array.from(visibleIdSet)
    .filter((nodeId) => !visibleIdSet.has(normalizeString(index?.parentByChild?.get(nodeId))))
    .sort((leftId, rightId) => {
      const leftNode = index?.nodesById?.get(leftId)
      const rightNode = index?.nodesById?.get(rightId)
      return sortByLevelAndLabel(leftNode, rightNode)
    })

  function layoutSubtree(nodeId, depth) {
    const childIds = groupChildren(index?.childrenByParent || new Map(), nodeId)
      .filter((childId) => visibleIdSet.has(normalizeString(childId)))
      .sort((leftId, rightId) => {
        const leftNode = index?.nodesById?.get(leftId)
        const rightNode = index?.nodesById?.get(rightId)
        return sortByLevelAndLabel(leftNode, rightNode)
      })

    if (!childIds.length) {
      const y = currentY
      positions.set(nodeId, { x: xStart + (depth * xGap), y })
      currentY += yGap
      return y
    }

    const childCenters = childIds.map((childId) => layoutSubtree(childId, depth + 1))
    const minCenter = Math.min(...childCenters)
    const maxCenter = Math.max(...childCenters)
    const y = minCenter + ((maxCenter - minCenter) / 2)
    positions.set(nodeId, { x: xStart + (depth * xGap), y })
    return y
  }

  rootIds.forEach((rootId, indexPosition) => {
    if (indexPosition > 0 && currentY > yStart) {
      currentY += Math.round(yGap * 0.35)
    }
    layoutSubtree(rootId, 0)
  })

  return positions
}

export function buildTeacherMindmapLayout(index, visibleNodeIds = [], focusNodeId = '', {
  xCenter = 360,
  yCenter = 320,
  xGap = 235,
  yGap = 96,
} = {}) {
  const visibleIdSet = new Set(
    (Array.isArray(visibleNodeIds) ? visibleNodeIds : [])
      .map((item) => normalizeString(item))
      .filter((item) => item),
  )
  const positions = new Map()
  const normalizedFocusId = normalizeString(focusNodeId)

  if (!visibleIdSet.size) {
    return positions
  }

  if (!normalizedFocusId || !visibleIdSet.has(normalizedFocusId)) {
    return buildTeacherAutoLayout(index, visibleNodeIds, { xStart, yStart, xGap, yGap })
  }

  positions.set(normalizedFocusId, { x: xCenter, y: yCenter })

  const ancestors = collectAncestors(normalizedFocusId, index.parentByChild)
    .filter((item) => visibleIdSet.has(item))
    .reverse()

  ancestors.forEach((ancestorId, indexOffset) => {
    positions.set(ancestorId, {
      x: xCenter - ((ancestors.length - indexOffset) * xGap),
      y: yCenter,
    })
  })

  function layoutChildren(nodeId, depth, startY) {
    const childIds = groupChildren(index.childrenByParent, nodeId)
      .filter((childId) => visibleIdSet.has(normalizeString(childId)))
      .sort((leftId, rightId) => {
        const leftNode = index?.nodesById?.get(leftId)
        const rightNode = index?.nodesById?.get(rightId)
        return sortByLevelAndLabel(leftNode, rightNode)
      })
    if (!childIds.length) {
      return startY + yGap
    }

    let cursorY = startY
    childIds.forEach((childId) => {
      const leafCount = collectLeafCount(childId, index.childrenByParent, index.nodesById)
      const blockHeight = Math.max(yGap, leafCount * yGap)
      const nodeY = cursorY + (blockHeight / 2)
      positions.set(childId, {
        x: xCenter + (depth * xGap),
        y: nodeY,
      })
      layoutChildren(childId, depth + 1, cursorY)
      cursorY += blockHeight
    })
    return cursorY
  }

  const childIds = groupChildren(index.childrenByParent, normalizedFocusId)
    .filter((childId) => visibleIdSet.has(normalizeString(childId)))
  if (childIds.length) {
    const totalLeafCount = childIds.reduce(
      (sum, childId) => sum + collectLeafCount(childId, index.childrenByParent, index.nodesById),
      0,
    )
    const startY = yCenter - ((Math.max(1, totalLeafCount) * yGap) / 2)
    layoutChildren(normalizedFocusId, 1, startY)
  }

  return positions
}
