// Observability note: scope helpers should preserve log/trace/metric context naming across API calls.
import { fetchContentBaseline } from './questionBank'

function toText(value) {
  return String(value || '').trim()
}

function toNumber(value, fallback = 0) {
  const numeric = Number(value)
  return Number.isFinite(numeric) ? numeric : fallback
}

function normalizeExamCategoryItems(rawExamCategories) {
  const source = Array.isArray(rawExamCategories) ? rawExamCategories : []
  return source
    .map((examCategoryItem) => {
      const examCategoryCode = toText(examCategoryItem?.examCategoryCode)
      if (!examCategoryCode) {
        return null
      }
      const examCategoryName = toText(examCategoryItem?.examCategoryName) || examCategoryCode
      return {
        id: examCategoryCode,
        name: examCategoryName,
        examCategoryCode,
        examCategoryName,
        sortNo: toNumber(examCategoryItem?.sortNo, 0),
        jointExamGroups: Array.isArray(examCategoryItem?.jointExamGroups)
          ? examCategoryItem.jointExamGroups
          : [],
      }
    })
    .filter(Boolean)
    .sort((left, right) => left.sortNo - right.sortNo)
}

/**
 * GET /api/question-bank/content/baseline
 * 必填字段: 无
 */
export async function fetchExamCategories() {
  const baselinePayload = await fetchContentBaseline()
  return normalizeExamCategoryItems(baselinePayload?.examCategories)
}
