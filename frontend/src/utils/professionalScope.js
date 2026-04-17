function normalizeString(value) {
  return String(value || '').trim()
}

function isPlaceholderName(value) {
  const normalized = normalizeString(value)
  if (!normalized) {
    return true
  }
  return /^[?？�]+$/.test(normalized)
}

function normalizeDisplayName(value, fallback = '') {
  const normalized = normalizeString(value)
  if (isPlaceholderName(normalized)) {
    return normalizeString(fallback)
  }
  return normalized
}

export function normalizeScopePath(pathValue) {
  const rows = Array.isArray(pathValue) ? pathValue : []
  return rows
    .slice(0, 3)
    .map((item) => normalizeString(item))
    .filter((item) => Boolean(item))
}

export function buildScopeKey(pathValue) {
  const normalizedPath = normalizeScopePath(pathValue)
  if (normalizedPath.length !== 3) {
    return ''
  }
  return normalizedPath.join('::')
}

export function buildGroupScopeKey(pathValue) {
  const normalizedPath = normalizeScopePath(pathValue)
  if (normalizedPath.length < 2) {
    return ''
  }
  return normalizedPath.slice(0, 2).join('::')
}

export function buildProfessionalScopeOptions(treeNodes, { assignedJointGroupCode = '' } = {}) {
  const examCategories = Array.isArray(treeNodes) ? treeNodes : []
  const targetGroupCode = normalizeString(assignedJointGroupCode)
  const fullScopeMetaMap = {}
  const fullOptions = examCategories
    .map((categoryItem) => {
      const categoryCode = normalizeString(categoryItem?.code)
      const categoryName = normalizeDisplayName(categoryItem?.name, categoryCode)
      const groupRows = Array.isArray(categoryItem?.children) ? categoryItem.children : []

      return {
        code: categoryCode,
        name: categoryName || categoryCode,
        children: groupRows.map((groupItem) => {
          const groupCode = normalizeString(groupItem?.code)
          const groupName = normalizeDisplayName(groupItem?.name, groupCode)
          const rawSubjects = Array.isArray(groupItem?.children) ? groupItem.children : []
          const subjectChildren = []
          const seenSubjectCodes = new Set()

          rawSubjects.forEach((subjectItem) => {
            const subjectCode = normalizeString(subjectItem?.code)
            if (!subjectCode || seenSubjectCodes.has(subjectCode)) {
              return
            }

            seenSubjectCodes.add(subjectCode)
            const subjectName = normalizeDisplayName(subjectItem?.name, subjectCode) || subjectCode
            const leafKey = `${categoryCode}::${groupCode}::${subjectCode}`
            fullScopeMetaMap[leafKey] = {
              categoryCode,
              categoryName,
              groupCode,
              groupName,
              subjectCode,
              subjectName,
              subjectType: normalizeString(subjectItem?.subjectType),
              subjectSlot: normalizeString(subjectItem?.subjectSlot),
              score: Number(subjectItem?.score || 0),
            }
            subjectChildren.push({
              code: subjectCode,
              name: subjectName,
              leaf: true,
            })
          })

          return {
            code: groupCode,
            name: groupName || groupCode,
            children: subjectChildren,
          }
        }),
      }
    })
    .filter((item) => Boolean(normalizeString(item?.code)))

  if (!targetGroupCode) {
    return {
      options: fullOptions,
      scopeMetaMap: fullScopeMetaMap,
    }
  }

  const scopedOptions = []
  const scopedMetaMap = {}
  fullOptions.forEach((categoryItem) => {
    const scopedGroups = (Array.isArray(categoryItem?.children) ? categoryItem.children : [])
      .filter((groupItem) => normalizeString(groupItem?.code) === targetGroupCode)
    if (!scopedGroups.length) {
      return
    }

    scopedOptions.push({
      code: normalizeString(categoryItem.code),
      name: normalizeString(categoryItem.name || categoryItem.code),
      children: scopedGroups,
    })

    scopedGroups.forEach((groupItem) => {
      const groupCode = normalizeString(groupItem?.code)
      const subjectChildren = Array.isArray(groupItem?.children) ? groupItem.children : []
      subjectChildren.forEach((subjectItem) => {
        const subjectCode = normalizeString(subjectItem?.code)
        const leafKey = `${normalizeString(categoryItem.code)}::${groupCode}::${subjectCode}`
        if (fullScopeMetaMap[leafKey]) {
          scopedMetaMap[leafKey] = fullScopeMetaMap[leafKey]
        }
      })
    })
  })

  return {
    options: scopedOptions,
    scopeMetaMap: scopedMetaMap,
  }
}

export function isProfessionalScopePathSelectable(pathValue, scopeMetaMap = {}) {
  const scopeKey = buildScopeKey(pathValue)
  return Boolean(scopeKey && scopeMetaMap[scopeKey])
}

export function resolveFirstAvailableProfessionalScopePath(options = [], scopeMetaMap = {}) {
  const categories = Array.isArray(options) ? options : []
  for (const categoryItem of categories) {
    const categoryCode = normalizeString(categoryItem?.code)
    const groups = Array.isArray(categoryItem?.children) ? categoryItem.children : []
    for (const groupItem of groups) {
      const groupCode = normalizeString(groupItem?.code)
      const subjects = Array.isArray(groupItem?.children) ? groupItem.children : []
      for (const subjectItem of subjects) {
        const subjectCode = normalizeString(subjectItem?.code)
        const candidatePath = [categoryCode, groupCode, subjectCode]
        if (isProfessionalScopePathSelectable(candidatePath, scopeMetaMap)) {
          return candidatePath
        }
      }
    }
  }
  return []
}

export function resolveFirstAvailableProfessionalGroupPath(options = []) {
  const categories = Array.isArray(options) ? options : []
  for (const categoryItem of categories) {
    const categoryCode = normalizeString(categoryItem?.code)
    const groups = Array.isArray(categoryItem?.children) ? categoryItem.children : []
    for (const groupItem of groups) {
      const groupCode = normalizeString(groupItem?.code)
      if (categoryCode && groupCode) {
        return [categoryCode, groupCode]
      }
    }
  }
  return []
}
