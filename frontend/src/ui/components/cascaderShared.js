export function resolveCascaderConfig(rawProps = {}) {
  return {
    valueKey: rawProps.value || 'value',
    labelKey: rawProps.label || 'label',
    childrenKey: rawProps.children || 'children',
    emitPath: rawProps.emitPath !== false,
    checkStrictly: Boolean(rawProps.checkStrictly),
  }
}

function normalizeNodeValue(value) {
  if (value === null || value === undefined) {
    return ''
  }
  return value
}

export function walkCascaderOptions(options, rawProps = {}, visit, parents = []) {
  const config = resolveCascaderConfig(rawProps)
  const optionNodes = Array.isArray(options) ? options : []

  optionNodes.forEach((node, index) => {
    const value = normalizeNodeValue(node?.[config.valueKey])
    const label = String(node?.[config.labelKey] ?? value)
    const path = [...parents.map((item) => item.value), value]
    const labelPath = [...parents.map((item) => item.label), label]
    const children = Array.isArray(node?.[config.childrenKey]) ? node[config.childrenKey] : []
    const meta = {
      node,
      value,
      label,
      path,
      labelPath,
      level: parents.length,
      index,
      disabled: Boolean(node?.disabled),
      isLeaf: children.length === 0,
      children,
    }

    visit(meta)
    if (children.length) {
      walkCascaderOptions(
        children,
        rawProps,
        visit,
        [...parents, { value, label }],
      )
    }
  })
}

export function buildCascaderSelections(options, rawProps = {}) {
  const config = resolveCascaderConfig(rawProps)
  const selectionRows = []

  walkCascaderOptions(options, rawProps, (meta) => {
    const selectable = config.checkStrictly || meta.isLeaf
    if (!selectable) {
      return
    }

    selectionRows.push({
      value: meta.value,
      label: meta.label,
      path: meta.path,
      labelPath: meta.labelPath,
      disabled: meta.disabled,
      node: meta.node,
    })
  })

  return selectionRows
}

export function findCascaderSelection(options, modelValue, rawProps = {}) {
  const config = resolveCascaderConfig(rawProps)
  const selections = buildCascaderSelections(options, rawProps)

  if (config.emitPath) {
    const targetPath = Array.isArray(modelValue) ? modelValue : []
    return selections.find((item) => (
      item.path.length === targetPath.length
      && item.path.every((segment, index) => segment === targetPath[index])
    )) || null
  }

  return selections.find((item) => item.value === modelValue) || null
}

export function formatCascaderSelectionLabel(selection, { showAllLevels = true, separator = ' / ' } = {}) {
  if (!selection) {
    return ''
  }

  if (!showAllLevels) {
    return String(selection.labelPath?.[selection.labelPath.length - 1] || selection.label || '')
  }

  return (Array.isArray(selection.labelPath) ? selection.labelPath : [selection.label])
    .map((item) => String(item || '').trim())
    .filter((item) => item)
    .join(separator)
}

export function filterCascaderSelections(selections, keyword) {
  const normalizedKeyword = String(keyword ?? '').trim().toLowerCase()
  if (!normalizedKeyword) {
    return selections
  }

  return selections.filter((item) => {
    const fullLabel = formatCascaderSelectionLabel(item).toLowerCase()
    const leafLabel = String(item?.label || '').toLowerCase()
    const rawValue = String(item?.value ?? '').toLowerCase()
    return fullLabel.includes(normalizedKeyword)
      || leafLabel.includes(normalizedKeyword)
      || rawValue.includes(normalizedKeyword)
  })
}

export function buildCascaderColumns(options, activePath = [], rawProps = {}) {
  const config = resolveCascaderConfig(rawProps)
  const rootOptions = Array.isArray(options) ? options : []
  const columns = []
  let currentRows = rootOptions
  let depth = 0

  while (Array.isArray(currentRows) && currentRows.length) {
    columns.push(currentRows)
    const currentValue = activePath[depth]
    const matchedNode = currentRows.find((item) => normalizeNodeValue(item?.[config.valueKey]) === currentValue)
    if (!matchedNode) {
      break
    }
    currentRows = Array.isArray(matchedNode?.[config.childrenKey]) ? matchedNode[config.childrenKey] : []
    depth += 1
  }

  return columns
}

export function toCascaderModelValue(selection, rawProps = {}) {
  const config = resolveCascaderConfig(rawProps)
  if (!selection) {
    return config.emitPath ? [] : undefined
  }
  return config.emitPath ? selection.path : selection.value
}
