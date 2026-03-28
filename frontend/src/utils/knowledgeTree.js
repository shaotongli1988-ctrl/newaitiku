function normalize_integer(value, fallback = 0) {
  const normalized = Number(value)
  if (!Number.isFinite(normalized)) {
    return fallback
  }
  return Math.trunc(normalized)
}

function normalize_number(value, fallback = 0) {
  const normalized = Number(value)
  return Number.isFinite(normalized) ? normalized : fallback
}

function compare_knowledge_order(left_id, right_id, node_map) {
  const left = node_map[left_id] || {}
  const right = node_map[right_id] || {}
  const sort_delta = normalize_integer(left.sort, 0) - normalize_integer(right.sort, 0)
  if (sort_delta !== 0) {
    return sort_delta
  }
  const create_time_delta = String(left.createTime || '').localeCompare(String(right.createTime || ''))
  if (create_time_delta !== 0) {
    return create_time_delta
  }
  const id_delta = String(left.id || '').localeCompare(String(right.id || ''))
  if (id_delta !== 0) {
    return id_delta
  }
  return String(left.label || '').localeCompare(String(right.label || ''), 'zh-Hans-CN')
}

function normalize_display_level(raw_level, max_depth_in_root) {
  const normalized_raw_level = normalize_integer(raw_level, 0)
  const normalized_max_depth = Math.max(1, normalize_integer(max_depth_in_root, 1))
  if (normalized_raw_level <= 1) {
    return 1
  }
  const distance_from_leaf = Math.max(0, normalized_max_depth - normalized_raw_level)
  if (distance_from_leaf === 0) {
    return 5
  }
  if (distance_from_leaf === 1) {
    return 4
  }
  if (distance_from_leaf === 2) {
    return 3
  }
  return 2
}

export function buildKnowledgeGraphIndex(treePayload = {}) {
  const source = treePayload && typeof treePayload === 'object' ? treePayload : {}
  const nodes = Array.isArray(source.nodes) ? source.nodes : []
  const links = Array.isArray(source.links) ? source.links : []
  const nodeMap = {}
  const parentById = {}
  const childrenById = {}
  const rawLevelById = {}
  const levelById = {}
  const pathById = {}

  nodes.forEach((item) => {
    const id = String(item?.id || '').trim()
    if (!id) {
      return
    }
    const fallbackLabel = String(item?.label || item?.name || id).trim() || id
    nodeMap[id] = {
      id,
      label: fallbackLabel,
      fullLabel: String(item?.fullLabel || item?.full_label || item?.label || item?.name || id).trim() || id,
      shortLabel: String(item?.shortLabel || item?.short_label || item?.label || item?.name || id).trim() || id,
      parentId: String(item?.parentId || item?.parent_id || '').trim(),
      sort: normalize_integer(item?.sort, 0),
      createTime: String(item?.createTime || item?.create_time || '').trim(),
      level: normalize_integer(item?.level, 0),
      moduleCode: String(item?.moduleCode || item?.module_code || '').trim(),
      mastery: normalize_number(item?.mastery, 0),
      wrongCount: Math.max(0, normalize_integer(item?.wrongCount || item?.wrong_count, 0)),
      questionCount: Math.max(0, normalize_integer(item?.questionCount || item?.question_count, 0)),
      size: Math.max(1, normalize_integer(item?.size, 1)),
    }
    childrenById[id] = []
  })

  links.forEach((link) => {
    if (String(link?.type || '').trim() !== 'parent') {
      return
    }
    const parentId = String(link?.source || '').trim()
    const childId = String(link?.target || '').trim()
    if (!parentId || !childId || !nodeMap[parentId] || !nodeMap[childId] || parentId === childId) {
      return
    }
    if (!childrenById[parentId].includes(childId)) {
      childrenById[parentId].push(childId)
    }
    parentById[childId] = parentId
    if (!nodeMap[childId].parentId) {
      nodeMap[childId].parentId = parentId
    }
  })

  Object.keys(nodeMap).forEach((nodeId) => {
    const parentId = String(nodeMap[nodeId]?.parentId || '').trim()
    if (!parentId || !nodeMap[parentId] || parentId === nodeId) {
      return
    }
    if (!childrenById[parentId]) {
      childrenById[parentId] = []
    }
    if (!childrenById[parentId].includes(nodeId)) {
      childrenById[parentId].push(nodeId)
    }
    parentById[nodeId] = parentId
  })

  function sortChildIds(childIds) {
    return childIds
      .slice()
      .sort((leftId, rightId) => compare_knowledge_order(leftId, rightId, nodeMap))
  }

  Object.keys(childrenById).forEach((id) => {
    childrenById[id] = sortChildIds(childrenById[id] || [])
  })

  const roots = Object.keys(nodeMap).filter((id) => !parentById[id])
  const orderedRoots = sortChildIds(roots)

  function fillLevelsAndPaths(nodeId, fallbackLevel, parentPath) {
    if (!nodeMap[nodeId]) {
      return
    }
    const explicitLevel = normalize_integer(nodeMap[nodeId].level, 0)
    const nextLevel = explicitLevel > 0 ? explicitLevel : fallbackLevel
    const existingLevel = normalize_integer(rawLevelById[nodeId], 0)
    if (existingLevel && existingLevel <= nextLevel) {
      return
    }
    rawLevelById[nodeId] = nextLevel
    const nextPath = [...parentPath, nodeId]
    pathById[nodeId] = nextPath
    ;(childrenById[nodeId] || []).forEach((childId) => {
      fillLevelsAndPaths(childId, nextLevel + 1, nextPath)
    })
  }

  orderedRoots.forEach((rootId) => {
    fillLevelsAndPaths(rootId, 1, [])
  })

  Object.keys(nodeMap).forEach((nodeId) => {
    if (rawLevelById[nodeId]) {
      return
    }
    const explicitLevel = normalize_integer(nodeMap[nodeId].level, 0)
    fillLevelsAndPaths(nodeId, explicitLevel > 0 ? explicitLevel : 1, [])
  })

  const rootMaxDepthById = {}
  Object.keys(pathById).forEach((nodeId) => {
    const path = Array.isArray(pathById[nodeId]) ? pathById[nodeId] : [nodeId]
    const rootId = String(path[0] || nodeId).trim() || nodeId
    const rawLevel = normalize_integer(rawLevelById[nodeId], path.length || 1)
    rootMaxDepthById[rootId] = Math.max(normalize_integer(rootMaxDepthById[rootId], 0), rawLevel)
  })

  Object.keys(rawLevelById).forEach((nodeId) => {
    const path = Array.isArray(pathById[nodeId]) ? pathById[nodeId] : [nodeId]
    const rootId = String(path[0] || nodeId).trim() || nodeId
    const maxDepthInRoot = normalize_integer(rootMaxDepthById[rootId], normalize_integer(rawLevelById[nodeId], 1))
    levelById[nodeId] = normalize_display_level(rawLevelById[nodeId], maxDepthInRoot)
  })

  return {
    nodeMap,
    parentById,
    childrenById,
    rawLevelById,
    levelById,
    pathById,
    orderedRoots,
    sortChildIds,
  }
}

export function buildKnowledgeSelectorState(treePayload = {}) {
  const graphIndex = buildKnowledgeGraphIndex(treePayload)
  const {
    nodeMap,
    parentById,
    childrenById,
    levelById,
    pathById,
    orderedRoots,
    sortChildIds,
  } = graphIndex
  const labelMap = {}
  const pathMap = {}
  const chapterCodeMap = {}
  const pointCodeMap = {}
  const moduleCodeMap = {}

  function formatChapterCode(index) {
    return `CH_${String(Math.max(0, index)).padStart(3, '0')}`
  }

  function formatPointCode(chapterIndex, pointIndex) {
    return `PT_${String(Math.max(0, chapterIndex)).padStart(3, '0')}_${String(Math.max(0, pointIndex)).padStart(3, '0')}`
  }

  function resolveL45Path(nodeId) {
    const normalizedNodeId = String(nodeId || '').trim()
    if (!normalizedNodeId || !nodeMap[normalizedNodeId]) {
      return []
    }
    let chapterId = ''
    let cursorId = normalizedNodeId
    while (cursorId) {
      if (Number(levelById[cursorId] || 0) === 4) {
        chapterId = cursorId
        break
      }
      cursorId = String(parentById[cursorId] || '').trim()
    }
    if (!chapterId) {
      const fallbackPath = Array.isArray(pathById[normalizedNodeId]) ? pathById[normalizedNodeId] : [normalizedNodeId]
      return fallbackPath.slice(-2)
    }
    if (chapterId === normalizedNodeId) {
      return [chapterId]
    }
    return [chapterId, normalizedNodeId]
  }

  function buildFullTreeNode(nodeId) {
    const children = sortChildIds(childrenById[nodeId] || []).map((childId) => buildFullTreeNode(childId))
    return {
      value: nodeId,
      label: String(nodeMap[nodeId]?.label || nodeId),
      children,
      leaf: children.length === 0,
    }
  }

  Object.keys(nodeMap).forEach((id) => {
    labelMap[id] = String(nodeMap[id]?.label || id)
    moduleCodeMap[id] = String(nodeMap[id]?.moduleCode || '').trim()
  })

  const level4Ids = Object.keys(nodeMap).filter((id) => Number(levelById[id] || 0) === 4)
  let options = []

  if (level4Ids.length > 0) {
    options = sortChildIds(level4Ids).map((chapterId, chapterOffset) => {
      const chapterIndex = chapterOffset + 1
      chapterCodeMap[chapterId] = formatChapterCode(chapterIndex)
      const l5Children = sortChildIds(childrenById[chapterId] || []).filter((childId) => Number(levelById[childId] || 0) >= 5)
      const children = l5Children.map((pointId, pointOffset) => {
        const pointIndex = pointOffset + 1
        pathMap[pointId] = resolveL45Path(pointId)
        pointCodeMap[pointId] = formatPointCode(chapterIndex, pointIndex)
        return {
          value: pointId,
          label: String(nodeMap[pointId]?.label || pointId),
          leaf: true,
        }
      })
      pathMap[chapterId] = resolveL45Path(chapterId)
      return {
        value: chapterId,
        label: String(nodeMap[chapterId]?.label || chapterId),
        children,
        leaf: children.length === 0,
      }
    })
  } else {
    options = orderedRoots.map((rootId) => buildFullTreeNode(rootId))
    Object.keys(nodeMap).forEach((nodeId) => {
      const fallbackPath = Array.isArray(pathById[nodeId]) ? pathById[nodeId] : [nodeId]
      pathMap[nodeId] = fallbackPath
    })
  }

  let searchNodeIds = Object.keys(nodeMap).filter((id) => Number(levelById[id] || 0) === 5)
  if (!searchNodeIds.length) {
    searchNodeIds = Object.keys(nodeMap).filter((id) => (childrenById[id] || []).length === 0)
  }

  const searchOptions = sortChildIds(searchNodeIds).map((nodeId) => {
    const pathIds = Array.isArray(pathMap[nodeId]) ? pathMap[nodeId] : resolveL45Path(nodeId)
    const pathLabel = pathIds.map((id) => String(labelMap[id] || id)).join(' / ')
    return {
      value: String(labelMap[nodeId] || nodeId),
      nodeId,
      pathIds,
      pathLabel: pathLabel || String(labelMap[nodeId] || nodeId),
      moduleCode: String(moduleCodeMap[nodeId] || '').trim(),
    }
  })

  return {
    options,
    pathMap,
    labelMap,
    chapterCodeMap,
    pointCodeMap,
    moduleCodeMap,
    searchOptions,
    graphIndex,
  }
}

export function buildKnowledgeLevelTreeState(selectorState = {}, { startLevel = 3, endLevel = 5 } = {}) {
  const state = selectorState && typeof selectorState === 'object' ? selectorState : {}
  const graphIndex = state?.graphIndex || buildKnowledgeGraphIndex({})
  const {
    nodeMap,
    childrenById,
    levelById,
    pathById,
    orderedRoots,
    sortChildIds,
  } = graphIndex
  const labelMap = state?.labelMap || {}
  const normalizedStartLevel = Math.max(1, normalize_integer(startLevel, 3))
  const normalizedEndLevel = Math.max(normalizedStartLevel, normalize_integer(endLevel, 5))
  const availableIds = Object.keys(nodeMap)
  const availableLevels = availableIds
    .map((nodeId) => normalize_integer(levelById[nodeId], 0))
    .filter((level) => level >= normalizedStartLevel && level <= normalizedEndLevel)
  const rootLevel = availableLevels.length ? Math.min(...availableLevels) : normalizedStartLevel
  const pathMap = {}
  const pathLabelMap = {}

  function resolveScopedPath(nodeId) {
    const rawPath = Array.isArray(pathById[nodeId]) ? pathById[nodeId] : [nodeId]
    const scopedPath = rawPath.filter((pathNodeId) => {
      const level = normalize_integer(levelById[pathNodeId], 0)
      return level >= rootLevel && level <= normalizedEndLevel
    })
    return scopedPath.length ? scopedPath : [nodeId]
  }

  function buildTreeNode(nodeId) {
    const level = normalize_integer(levelById[nodeId], 0)
    const scopedPath = resolveScopedPath(nodeId)
    pathMap[nodeId] = scopedPath
    pathLabelMap[nodeId] = scopedPath.map((pathNodeId) => String(labelMap[pathNodeId] || nodeMap[pathNodeId]?.label || pathNodeId)).join(' / ')

    const childIds = level >= normalizedEndLevel
      ? []
      : sortChildIds(childrenById[nodeId] || []).filter((childId) => {
          const childLevel = normalize_integer(levelById[childId], 0)
          return childLevel > level && childLevel <= normalizedEndLevel
        })

    return {
      value: nodeId,
      label: String(labelMap[nodeId] || nodeMap[nodeId]?.label || nodeId),
      level,
      leaf: childIds.length === 0,
      children: childIds.map((childId) => buildTreeNode(childId)),
    }
  }

  const rootIds = sortChildIds(
    availableIds.filter((nodeId) => normalize_integer(levelById[nodeId], 0) === rootLevel),
  )
  const fallbackRootIds = rootIds.length ? rootIds : orderedRoots
  const options = fallbackRootIds.map((nodeId) => buildTreeNode(nodeId))

  return {
    options,
    pathMap,
    pathLabelMap,
    rootLevel,
  }
}

export function buildKnowledgeSemanticMap(selectorState = {}) {
  const state = selectorState && typeof selectorState === 'object' ? selectorState : {}
  const graphIndex = state?.graphIndex || buildKnowledgeGraphIndex({})
  const { nodeMap, levelById, pathById } = graphIndex
  const levelSemanticNameMap = {
    1: 'L1 科目',
    2: 'L2 学科域',
    3: 'L3 模块',
    4: 'L4 章节',
    5: 'L5 原子知识点',
  }
  const semanticMap = {}

  Object.keys(nodeMap).forEach((nodeId) => {
    const level = normalize_integer(levelById[nodeId], 0)
    const fullPathIds = Array.isArray(pathById[nodeId]) ? pathById[nodeId] : [nodeId]
    const semanticTrail = fullPathIds.map((pathNodeId) => {
      const pathLevel = normalize_integer(levelById[pathNodeId], 0)
      return {
        id: pathNodeId,
        level: pathLevel,
        levelLabel: String(levelSemanticNameMap[pathLevel] || `L${pathLevel || '-'}`),
        label: String(nodeMap[pathNodeId]?.label || pathNodeId),
      }
    })

    semanticMap[nodeId] = {
      id: nodeId,
      level,
      levelLabel: String(levelSemanticNameMap[level] || `L${level || '-'}`),
      fullPathIds,
      fullPathLabel: semanticTrail.map((item) => item.label).join(' / '),
      semanticTrail,
    }
  })

  return semanticMap
}
