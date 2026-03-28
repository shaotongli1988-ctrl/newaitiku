function toText(value) {
  return String(value || '').trim()
}

export function buildOptionLabelMap(options, { codeKey = 'code', nameKey = 'name' } = {}) {
  const labelMap = new Map()
  const rows = Array.isArray(options) ? options : []

  rows.forEach((item) => {
    const code = toText(item?.[codeKey])
    if (!code) {
      return
    }
    labelMap.set(code, toText(item?.[nameKey]) || code)
  })

  return labelMap
}

export function buildContentLabelMaps(source) {
  const examCategories = Array.isArray(source)
    ? source
    : Array.isArray(source?.examCategories)
      ? source.examCategories
      : Array.isArray(source?.availableExamCategories)
        ? source.availableExamCategories
        : []

  const examCategoryNameMap = new Map()
  const jointExamGroupNameMap = new Map()
  const subjectNameMap = new Map()

  examCategories.forEach((examCategoryItem) => {
    const examCategoryCode = toText(examCategoryItem?.examCategoryCode)
    if (!examCategoryCode) {
      return
    }

    examCategoryNameMap.set(
      examCategoryCode,
      toText(examCategoryItem?.examCategoryName) || examCategoryCode,
    )

    const jointExamGroups = Array.isArray(examCategoryItem?.jointExamGroups)
      ? examCategoryItem.jointExamGroups
      : []

    jointExamGroups.forEach((jointExamGroupItem) => {
      const jointExamGroupCode = toText(jointExamGroupItem?.jointExamGroupCode)
      if (!jointExamGroupCode) {
        return
      }

      jointExamGroupNameMap.set(
        jointExamGroupCode,
        toText(jointExamGroupItem?.jointExamGroupName) || jointExamGroupCode,
      )

      const subjects = Array.isArray(jointExamGroupItem?.subjects)
        ? jointExamGroupItem.subjects
        : []

      subjects.forEach((subjectItem) => {
        const subjectCode = toText(subjectItem?.subjectCode)
        if (!subjectCode || subjectNameMap.has(subjectCode)) {
          return
        }

        subjectNameMap.set(subjectCode, toText(subjectItem?.subjectName) || subjectCode)
      })
    })
  })

  return {
    examCategoryNameMap,
    jointExamGroupNameMap,
    subjectNameMap,
  }
}

export function resolveContentLabel(labelMap, code, fallback = '-') {
  const normalizedCode = toText(code)
  if (!normalizedCode) {
    return fallback
  }
  const mappedValue = labelMap instanceof Map ? toText(labelMap.get(normalizedCode)) : ''
  return mappedValue || normalizedCode
}

export function normalizeContentBaseline(payload) {
  const examCategories = Array.isArray(payload?.examCategories) ? payload.examCategories : []
  const examCategoryOptions = []
  const jointExamGroupOptions = []
  const subjectCodeOptions = []

  examCategories.forEach((examCategoryItem) => {
    const examCategoryCode = toText(examCategoryItem?.examCategoryCode)
    if (!examCategoryCode) {
      return
    }

    examCategoryOptions.push({
      examCategoryCode,
      examCategoryName: toText(examCategoryItem?.examCategoryName) || examCategoryCode,
      sortNo: Number(examCategoryItem?.sortNo || 0),
    })

    const jointExamGroups = Array.isArray(examCategoryItem?.jointExamGroups)
      ? examCategoryItem.jointExamGroups
      : []

    jointExamGroups.forEach((jointExamGroupItem) => {
      const jointExamGroupCode = toText(jointExamGroupItem?.jointExamGroupCode)
      if (!jointExamGroupCode) {
        return
      }

      const normalizedExamCategoryCode =
        toText(jointExamGroupItem?.examCategoryCode) || examCategoryCode
      jointExamGroupOptions.push({
        jointExamGroupCode,
        jointExamGroupName: toText(jointExamGroupItem?.jointExamGroupName) || jointExamGroupCode,
        examCategoryCode: normalizedExamCategoryCode,
      })

      const subjects = Array.isArray(jointExamGroupItem?.subjects) ? jointExamGroupItem.subjects : []
      subjects.forEach((subjectItem) => {
        const subjectCode = toText(subjectItem?.subjectCode)
        if (!subjectCode) {
          return
        }

        subjectCodeOptions.push({
          subjectCode,
          subjectName: toText(subjectItem?.subjectName) || subjectCode,
          subjectType: toText(subjectItem?.subjectType),
          examCategoryCode: normalizedExamCategoryCode,
          jointExamGroupCode,
        })
      })
    })
  })

  examCategoryOptions.sort((left, right) => left.sortNo - right.sortNo)

  return {
    examCategoryOptions,
    jointExamGroupOptions,
    subjectCodeOptions,
  }
}

export function normalizeStudentDashboardDictionary(payload) {
  const availableExamCategories = Array.isArray(payload?.availableExamCategories)
    ? payload.availableExamCategories
    : []
  const coreSubjects = Array.isArray(payload?.coreSubjects) ? payload.coreSubjects : []

  const examCategoryOptions = availableExamCategories
    .map((examCategoryItem) => {
      const examCategoryCode = toText(examCategoryItem?.examCategoryCode)
      if (!examCategoryCode) {
        return null
      }
      return {
        examCategoryCode,
        examCategoryName: toText(examCategoryItem?.examCategoryName) || examCategoryCode,
        sortNo: Number(examCategoryItem?.sortNo || 0),
      }
    })
    .filter(Boolean)
    .sort((left, right) => left.sortNo - right.sortNo)

  const jointExamGroupOptions = availableExamCategories.flatMap((examCategoryItem) => {
    const examCategoryCode = toText(examCategoryItem?.examCategoryCode)
    const jointExamGroups = Array.isArray(examCategoryItem?.jointExamGroups)
      ? examCategoryItem.jointExamGroups
      : []
    return jointExamGroups
      .map((jointExamGroupItem) => {
        const jointExamGroupCode = toText(jointExamGroupItem?.jointExamGroupCode)
        if (!jointExamGroupCode) {
          return null
        }
        return {
          jointExamGroupCode,
          jointExamGroupName: toText(jointExamGroupItem?.jointExamGroupName) || jointExamGroupCode,
          examCategoryCode,
        }
      })
      .filter(Boolean)
  })

  const subjectCodeOptions = coreSubjects
    .map((subjectItem) => {
      const subjectCode = toText(subjectItem?.subjectCode)
      if (!subjectCode) {
        return null
      }
      return {
        subjectCode,
        subjectName: toText(subjectItem?.subjectName) || subjectCode,
        subjectType: toText(subjectItem?.subjectType),
        examCategoryCode: toText(payload?.examCategoryCode),
        jointExamGroupCode: toText(payload?.jointExamGroupCode),
      }
    })
    .filter(Boolean)

  return {
    examCategoryOptions,
    jointExamGroupOptions,
    subjectCodeOptions,
  }
}

export function filterJointExamGroupOptions(options, examCategoryCode) {
  const selectedExamCategoryCode = toText(examCategoryCode)
  if (!selectedExamCategoryCode) {
    return Array.isArray(options) ? options : []
  }
  return (Array.isArray(options) ? options : []).filter(
    (item) => toText(item?.examCategoryCode) === selectedExamCategoryCode,
  )
}

export function filterSubjectCodeOptions(options, examCategoryCode, jointExamGroupCode) {
  const normalizedExamCategoryCode = toText(examCategoryCode)
  const normalizedJointExamGroupCode = toText(jointExamGroupCode)
  const source = Array.isArray(options) ? options : []
  const deduped = []
  const seen = new Set()

  source.forEach((item) => {
    const subjectCode = toText(item?.subjectCode)
    if (!subjectCode || seen.has(subjectCode)) {
      return
    }
    if (normalizedExamCategoryCode && toText(item?.examCategoryCode) !== normalizedExamCategoryCode) {
      return
    }
    if (
      normalizedJointExamGroupCode &&
      toText(item?.subjectType) !== 'PUBLIC' &&
      toText(item?.jointExamGroupCode) !== normalizedJointExamGroupCode
    ) {
      return
    }
    seen.add(subjectCode)
    deduped.push(item)
  })

  return deduped
}
