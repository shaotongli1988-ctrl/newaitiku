export function resolveTreeConfig(rawProps = {}, nodeKey = '') {
  const props = rawProps && typeof rawProps === 'object' ? rawProps : {}
  const valueKey = String(props.value || nodeKey || 'value').trim() || 'value'
  return {
    valueKey,
    labelKey: String(props.label || 'label').trim() || 'label',
    childrenKey: String(props.children || 'children').trim() || 'children',
  }
}

export function normalizeTreeSelectValue(modelValue, { multiple = false } = {}) {
  if (multiple) {
    return Array.isArray(modelValue)
      ? modelValue.map((item) => String(item ?? '').trim()).filter((item) => Boolean(item))
      : []
  }
  return String(modelValue ?? '').trim()
}

export function flattenTreeNodes(nodes, options = {}, level = 0, ancestorsVisible = true) {
  const config = resolveTreeConfig(options.props, options.nodeKey)
  const rows = []
  const source = Array.isArray(nodes) ? nodes : []
  source.forEach((node) => {
    const value = String(node?.[config.valueKey] ?? '').trim()
    const label = String(node?.[config.labelKey] ?? value).trim() || value
    if (!value) {
      return
    }
    rows.push({
      key: value,
      level,
      label,
      data: node,
      ancestorsVisible,
    })
    const children = Array.isArray(node?.[config.childrenKey]) ? node[config.childrenKey] : []
    rows.push(...flattenTreeNodes(children, options, level + 1, ancestorsVisible))
  })
  return rows
}

export function filterTreeNodes(nodes, keyword, filterMethod, options = {}, level = 0) {
  const config = resolveTreeConfig(options.props, options.nodeKey)
  const source = Array.isArray(nodes) ? nodes : []
  const normalizedKeyword = String(keyword || '').trim()
  const rows = []

  source.forEach((node) => {
    const children = Array.isArray(node?.[config.childrenKey]) ? node[config.childrenKey] : []
    const childRows = filterTreeNodes(children, normalizedKeyword, filterMethod, options, level + 1)
    const matched = !normalizedKeyword
      || (typeof filterMethod === 'function'
        ? Boolean(filterMethod(normalizedKeyword, node))
        : String(node?.[config.labelKey] ?? '').includes(normalizedKeyword))

    if (!matched && !childRows.length) {
      return
    }

    const value = String(node?.[config.valueKey] ?? '').trim()
    const label = String(node?.[config.labelKey] ?? value).trim() || value
    if (!value) {
      rows.push(...childRows)
      return
    }

    rows.push({
      key: value,
      level,
      label,
      data: node,
      matched,
    })
    rows.push(...childRows)
  })

  return rows
}

export function buildTreeLabelMap(nodes, options = {}) {
  return flattenTreeNodes(nodes, options).reduce((result, row) => {
    result.set(row.key, row.label)
    return result
  }, new Map())
}

export function toggleTreeValue(currentValue, nextKey, { multiple = false } = {}) {
  const normalizedKey = String(nextKey ?? '').trim()
  if (!normalizedKey) {
    return multiple ? [] : ''
  }

  if (!multiple) {
    return normalizedKey
  }

  const currentValues = normalizeTreeSelectValue(currentValue, { multiple: true })
  if (currentValues.includes(normalizedKey)) {
    return currentValues.filter((item) => item !== normalizedKey)
  }
  return [...currentValues, normalizedKey]
}

export function resolveTreeDropType(event) {
  const bounds = event?.currentTarget?.getBoundingClientRect?.()
  if (!bounds) {
    return 'after'
  }
  const pointerY = Number(event.clientY || 0)
  return pointerY <= bounds.top + bounds.height / 2 ? 'before' : 'after'
}
