import { buildKnowledgeLevelTreeState } from './knowledgeTree'

function normalizeMasteryValue(value) {
  const normalized = Number(value)
  if (!Number.isFinite(normalized)) {
    return 0
  }
  return Math.max(0, Math.min(1, normalized))
}

function normalizePercent(value) {
  return Math.round(normalizeMasteryValue(value) * 100)
}

export function classifyGalaxyMasteryBand(value) {
  const mastery = normalizeMasteryValue(value)
  if (mastery <= 0) {
    return 'unpracticed'
  }
  if (mastery < 0.6) {
    return 'weak'
  }
  if (mastery > 0.85) {
    return 'strong'
  }
  return 'fuzzy'
}

function toText(value) {
  return String(value || '').trim()
}

function resolveDisplayLabel(node = {}, fallback = '') {
  return toText(node?.shortLabel || node?.label || fallback) || toText(node?.fullLabel || fallback)
}

export function buildStudentGalaxyModel(selectorState = {}) {
  const state = selectorState && typeof selectorState === 'object' ? selectorState : {}
  const graphIndex = state?.graphIndex || {}
  const nodeMap = graphIndex?.nodeMap || {}
  const childrenById = graphIndex?.childrenById || {}
  const levelById = graphIndex?.levelById || {}
  const pathById = graphIndex?.pathById || {}
  const orderedRoots = Array.isArray(graphIndex?.orderedRoots) ? graphIndex.orderedRoots : []
  const sortChildIds = typeof graphIndex?.sortChildIds === 'function' ? graphIndex.sortChildIds : ((rows) => rows)
  const chapterCodeMap = state?.chapterCodeMap || {}
  const pointCodeMap = state?.pointCodeMap || {}
  const scopedTree = buildKnowledgeLevelTreeState(state, { startLevel: 4, endLevel: 5 })
  const pathLabelMap = scopedTree?.pathLabelMap || {}

  function resolveDisplayPathLabel(nodeId, fallback = '') {
    const pathIds = Array.isArray(pathById[nodeId]) ? pathById[nodeId] : [nodeId]
    const labels = pathIds
      .map((pathNodeId) => resolveDisplayLabel(nodeMap[pathNodeId], pathNodeId))
      .filter(Boolean)
    return labels.join(' / ') || fallback
  }

  const subjectRootId = orderedRoots.find((nodeId) => Number(levelById[nodeId] || 0) === 1) || orderedRoots[0] || ''
  const subjectRootLabel = resolveDisplayLabel(nodeMap[subjectRootId], subjectRootId)
  const chapterIds = sortChildIds(
    Object.keys(nodeMap).filter((nodeId) => Number(levelById[nodeId] || 0) === 4),
  )

  const chapterRows = chapterIds.map((chapterId) => {
    const chapterNode = nodeMap[chapterId] || {}
    const pointIds = sortChildIds(childrenById[chapterId] || []).filter((pointId) => Number(levelById[pointId] || 0) >= 5)
    const points = pointIds.map((pointId) => {
      const pointNode = nodeMap[pointId] || {}
      const masteryValue = normalizeMasteryValue(pointNode.mastery)
      const fullLabel = toText(pointNode.fullLabel || pointNode.label || pointId) || pointId
      const displayLabel = resolveDisplayLabel(pointNode, pointId)
      return {
        id: pointId,
        label: fullLabel,
        fullLabel,
        displayLabel,
        level: Number(levelById[pointId] || 5),
        chapterId,
        chapterCode: String(chapterCodeMap[chapterId] || '').trim(),
        pointCode: String(pointCodeMap[pointId] || '').trim(),
        mastery: masteryValue,
        masteryScore: normalizePercent(masteryValue),
        masteryBand: classifyGalaxyMasteryBand(masteryValue),
        wrongCount: Math.max(0, Number(pointNode.wrongCount || 0)),
        questionCount: Math.max(0, Number(pointNode.questionCount || 0)),
        pathLabel: String(pathLabelMap[pointId] || pointNode.label || pointId).trim(),
        displayPathLabel: resolveDisplayPathLabel(pointId, displayLabel),
      }
    })

    const totalQuestionCount = points.reduce((sum, item) => sum + Number(item.questionCount || 0), 0)
    const totalWrongCount = points.reduce((sum, item) => sum + Number(item.wrongCount || 0), 0)
    const averageMasteryValue = points.length
      ? points.reduce((sum, item) => sum + Number(item.mastery || 0), 0) / points.length
      : normalizeMasteryValue(chapterNode.mastery)
    const chapterLabel = toText(chapterNode.fullLabel || chapterNode.label || chapterId) || chapterId
    const chapterDisplayLabel = resolveDisplayLabel(chapterNode, chapterLabel)

    return {
      id: chapterId,
      label: chapterLabel,
      fullLabel: chapterLabel,
      displayLabel: chapterDisplayLabel,
      level: 4,
      chapterCode: String(chapterCodeMap[chapterId] || '').trim(),
      mastery: averageMasteryValue,
      masteryScore: normalizePercent(averageMasteryValue),
      masteryBand: classifyGalaxyMasteryBand(averageMasteryValue),
      pathLabel: String(pathLabelMap[chapterId] || chapterNode.label || chapterId).trim(),
      displayPathLabel: resolveDisplayPathLabel(chapterId, chapterDisplayLabel),
      wrongCount: totalWrongCount,
      questionCount: totalQuestionCount,
      pointCount: points.length,
      unpracticedPointCount: points.filter((item) => item.masteryBand === 'unpracticed').length,
      weakPointCount: points.filter((item) => item.masteryBand === 'weak').length,
      points,
    }
  })

  const allPoints = chapterRows.flatMap((item) => item.points)
  const averageMasteryValue = allPoints.length
    ? allPoints.reduce((sum, item) => sum + Number(item.mastery || 0), 0) / allPoints.length
    : 0
  const totalWrongCount = allPoints.reduce((sum, item) => sum + Number(item.wrongCount || 0), 0)

  return {
    subjectRootId,
    subjectRootLabel,
    chapterRows,
    chapterCount: chapterRows.length,
    pointCount: allPoints.length,
    renderedNodeCount: chapterRows.length + allPoints.length,
    averageMasteryValue,
    averageMastery: normalizePercent(averageMasteryValue),
    wrongCount: totalWrongCount,
    weakPointCount: allPoints.filter((item) => item.masteryBand === 'weak').length,
    unpracticedPointCount: allPoints.filter((item) => item.masteryBand === 'unpracticed').length,
    strongPointCount: allPoints.filter((item) => item.masteryBand === 'strong').length,
    fuzzyPointCount: allPoints.filter((item) => item.masteryBand === 'fuzzy').length,
  }
}

export function buildStudentGalaxySunburstData(galaxyModel, resolveColor) {
  const model = galaxyModel && typeof galaxyModel === 'object' ? galaxyModel : {}
  const chapterRows = Array.isArray(model.chapterRows) ? model.chapterRows : []
  const subjectRootId = String(model.subjectRootId || model.subjectCode || 'subject-root').trim() || 'subject-root'
  const subjectRootLabel = String(model.subjectRootLabel || model.subjectName || model.subjectCode || '当前科目').trim() || '当前科目'
  const colorFor = typeof resolveColor === 'function' ? resolveColor : () => '#D0D7E2'

  return [
    {
      id: subjectRootId,
      name: subjectRootLabel,
      value: Math.max(1, Number(model.pointCount || 0), Number(model.chapterCount || 0)),
      itemStyle: {
        color: colorFor(1, 'subject'),
      },
        meta: {
          id: subjectRootId,
          label: subjectRootLabel,
          fullLabel: subjectRootLabel,
          level: 1,
          mastery: Number(model.averageMasteryValue || 0),
          wrongCount: Number(model.wrongCount || 0),
          questionCount: chapterRows.reduce((sum, item) => sum + Number(item.questionCount || 0), 0),
          pathLabel: subjectRootLabel,
        },
      children: chapterRows.map((chapter) => ({
        id: chapter.id,
        name: chapter.displayLabel || chapter.label,
        value: Math.max(1, Number(chapter.pointCount || 0), Number(chapter.questionCount || 0)),
        itemStyle: {
          color: colorFor(chapter.mastery, chapter.masteryBand),
        },
        meta: {
          id: chapter.id,
          label: chapter.displayLabel || chapter.label,
          fullLabel: chapter.fullLabel || chapter.label,
          level: 4,
          chapterCode: chapter.chapterCode,
          chapterName: chapter.displayLabel || chapter.label,
          mastery: Number(chapter.mastery || 0),
          wrongCount: Number(chapter.wrongCount || 0),
          questionCount: Number(chapter.questionCount || 0),
          pathLabel: chapter.displayPathLabel || chapter.pathLabel,
          fullPathLabel: chapter.pathLabel,
        },
        children: chapter.points.map((point) => ({
          id: point.id,
          name: point.displayLabel || point.label,
          value: Math.max(1, Number(point.questionCount || 0)),
          itemStyle: {
            color: colorFor(point.mastery, point.masteryBand),
          },
          meta: {
            id: point.id,
            label: point.displayLabel || point.label,
            fullLabel: point.fullLabel || point.label,
            level: point.level,
            chapterId: chapter.id,
            chapterCode: point.chapterCode,
            chapterName: chapter.displayLabel || chapter.label,
            pointCode: point.pointCode,
            mastery: Number(point.mastery || 0),
            wrongCount: Number(point.wrongCount || 0),
            questionCount: Number(point.questionCount || 0),
            pathLabel: point.displayPathLabel || point.pathLabel,
            fullPathLabel: point.pathLabel,
          },
        })),
      })),
    },
  ]
}
