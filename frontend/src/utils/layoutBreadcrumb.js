function normalizeQueryValue(value) {
  return String(Array.isArray(value) ? value[0] : value || '').trim()
}

function isMeaningfulLabel(label) {
  const normalized = String(label || '').trim()
  if (!normalized) {
    return false
  }
  return !normalized.startsWith('未') && !normalized.includes('待定位')
}

export function buildKnowledgePathItems(query = {}) {
  const rawPathLabel = normalizeQueryValue(query.pathLabel)
  const chapterName = normalizeQueryValue(query.chapterName)
  const pointName = normalizeQueryValue(query.pointName)
  const pathSegments = rawPathLabel
    ? rawPathLabel.split('/').map((item) => item.trim()).filter(Boolean).slice(-3)
    : []

  return [
    { level: 'L3', label: pathSegments[0] || (chapterName || pointName ? '知识模块待定位' : '未进入知识路径') },
    { level: 'L4', label: pathSegments[1] || chapterName || '未定位章节' },
    { level: 'L5', label: pathSegments[2] || pointName || '未定位考点' },
  ]
}

export function buildSelectedKnowledgeBreadcrumb(query = {}) {
  return buildKnowledgePathItems(query)
    .filter((item) => item.level === 'L4' || item.level === 'L5')
    .filter((item) => isMeaningfulLabel(item.label))
}

export function buildKnowledgeBreadcrumbText(query = {}) {
  const selectedItems = buildSelectedKnowledgeBreadcrumb(query)
  if (!selectedItems.length) {
    return '当前未选择 L4 / L5 路径'
  }
  return selectedItems.map((item) => item.label).join(' > ')
}
