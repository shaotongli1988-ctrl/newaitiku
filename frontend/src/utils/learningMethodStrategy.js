const LEARNING_METHOD_STRATEGY_STORAGE_KEY = 'student_learning_method_strategy_state_v1'

export const LEARNING_METHOD_RECOMMENDATION_STRATEGY = Object.freeze({
  FOUNDATION: 'FOUNDATION',
  BALANCED: 'BALANCED',
  SPRINT: 'SPRINT',
})

export const LEARNING_METHOD_RECOMMENDATION_STRATEGY_SOURCE = Object.freeze({
  DEFAULT: 'DEFAULT',
  MANUAL: 'MANUAL',
  SUGGESTED: 'SUGGESTED',
})

const PRACTICE_STRATEGY_CODE_MAP = Object.freeze({
  FOUNDATION_REINFORCE: LEARNING_METHOD_RECOMMENDATION_STRATEGY.FOUNDATION,
  BALANCED_ADVANCE: LEARNING_METHOD_RECOMMENDATION_STRATEGY.BALANCED,
  SPRINT_BREAKTHROUGH: LEARNING_METHOD_RECOMMENDATION_STRATEGY.SPRINT,
  DEFAULT: LEARNING_METHOD_RECOMMENDATION_STRATEGY.BALANCED,
})

const LEARNING_METHOD_STRATEGY_SOURCE_LABEL_MAP = Object.freeze({
  DEFAULT: '系统默认',
  MANUAL: '手动切换',
  SUGGESTED: '趋势建议',
})

function normalizeText(value) {
  return String(value || '').trim()
}

function safeLocalStorage() {
  if (typeof localStorage === 'undefined') {
    return null
  }
  return localStorage
}

function normalizeScopePart(value) {
  const normalizedValue = normalizeText(value).toUpperCase()
  return normalizedValue || '*'
}

function resolveStrategyStorageScopeKey({ subjectCode = '', methodCode = '' } = {}) {
  return `${normalizeScopePart(subjectCode)}::${normalizeScopePart(methodCode)}`
}

function parseStoredStrategyState(raw) {
  if (!raw) {
    return {}
  }
  try {
    const parsed = JSON.parse(raw)
    if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
      return {}
    }
    return parsed
  } catch (error) {
    return {}
  }
}

function normalizeStoredStrategyEntry(entry) {
  if (!entry || typeof entry !== 'object' || Array.isArray(entry)) {
    return null
  }
  const strategyCode = normalizeLearningMethodRecommendationStrategyCode(entry.strategyCode, '')
  if (!strategyCode) {
    return null
  }
  const source = normalizeLearningMethodRecommendationStrategySource(
    entry.source,
    LEARNING_METHOD_RECOMMENDATION_STRATEGY_SOURCE.DEFAULT,
  )
  return {
    strategyCode,
    source,
    updateTime: normalizeText(entry.updateTime),
  }
}

export function normalizeLearningMethodRecommendationStrategyCode(value, fallback = LEARNING_METHOD_RECOMMENDATION_STRATEGY.BALANCED) {
  const normalizedValue = normalizeText(value).toUpperCase()
  if (Object.prototype.hasOwnProperty.call(LEARNING_METHOD_RECOMMENDATION_STRATEGY, normalizedValue)) {
    return normalizedValue
  }
  return fallback
}

export function normalizeLearningMethodRecommendationStrategySource(
  value,
  fallback = LEARNING_METHOD_RECOMMENDATION_STRATEGY_SOURCE.DEFAULT,
) {
  const normalizedValue = normalizeText(value).toUpperCase()
  if (Object.prototype.hasOwnProperty.call(LEARNING_METHOD_RECOMMENDATION_STRATEGY_SOURCE, normalizedValue)) {
    return normalizedValue
  }
  return fallback
}

export function learningMethodRecommendationStrategySourceLabel(source) {
  const normalizedSource = normalizeLearningMethodRecommendationStrategySource(source)
  return LEARNING_METHOD_STRATEGY_SOURCE_LABEL_MAP[normalizedSource] || LEARNING_METHOD_STRATEGY_SOURCE_LABEL_MAP.DEFAULT
}

export function recommendationStrategyCodeByPracticeStrategy(value, fallback = '') {
  const normalizedValue = normalizeText(value).toUpperCase()
  if (!normalizedValue) {
    return fallback
  }
  return PRACTICE_STRATEGY_CODE_MAP[normalizedValue] || fallback
}

export function resolveLearningMethodRecommendationStrategyFromPayload(payload = {}, fallback = '') {
  const source = payload && typeof payload === 'object' ? payload : {}
  const explicitCode = normalizeLearningMethodRecommendationStrategyCode(
    source.recommendationStrategyCode,
    '',
  )
  if (explicitCode) {
    return explicitCode
  }
  const recommendationLog = source.recommendationLog && typeof source.recommendationLog === 'object'
    ? source.recommendationLog
    : {}
  const extJson = source.extJson && typeof source.extJson === 'object'
    ? source.extJson
    : {}
  return recommendationStrategyCodeByPracticeStrategy(
    source.practiceStrategy
      || recommendationLog.practiceStrategy
      || extJson.practiceStrategy,
    fallback,
  )
}

export function resolveLearningMethodRecommendationStrategySourceFromPayload(payload = {}, fallback = '') {
  const source = payload && typeof payload === 'object' ? payload : {}
  const recommendationLog = source.recommendationLog && typeof source.recommendationLog === 'object'
    ? source.recommendationLog
    : {}
  const extJson = source.extJson && typeof source.extJson === 'object'
    ? source.extJson
    : {}
  return normalizeLearningMethodRecommendationStrategySource(
    source.recommendationStrategySource
      || recommendationLog.strategySource
      || extJson.strategySource,
    fallback,
  )
}

export function loadPersistedLearningMethodRecommendationStrategy({ subjectCode = '', methodCode = '' } = {}) {
  const storage = safeLocalStorage()
  if (!storage) {
    return null
  }
  const scopeKey = resolveStrategyStorageScopeKey({ subjectCode, methodCode })
  try {
    const source = parseStoredStrategyState(storage.getItem(LEARNING_METHOD_STRATEGY_STORAGE_KEY))
    return normalizeStoredStrategyEntry(source[scopeKey])
  } catch (error) {
    return null
  }
}

export function savePersistedLearningMethodRecommendationStrategy(
  { subjectCode = '', methodCode = '', strategyCode = '', source = '' } = {},
) {
  const storage = safeLocalStorage()
  if (!storage) {
    return
  }
  const normalizedStrategyCode = normalizeLearningMethodRecommendationStrategyCode(strategyCode, '')
  if (!normalizedStrategyCode) {
    return
  }
  const normalizedSource = normalizeLearningMethodRecommendationStrategySource(
    source,
    LEARNING_METHOD_RECOMMENDATION_STRATEGY_SOURCE.DEFAULT,
  )
  const scopeKey = resolveStrategyStorageScopeKey({ subjectCode, methodCode })

  try {
    const currentState = parseStoredStrategyState(storage.getItem(LEARNING_METHOD_STRATEGY_STORAGE_KEY))
    currentState[scopeKey] = {
      strategyCode: normalizedStrategyCode,
      source: normalizedSource,
      updateTime: new Date().toISOString(),
    }
    storage.setItem(LEARNING_METHOD_STRATEGY_STORAGE_KEY, JSON.stringify(currentState))
  } catch (error) {
    // Ignore storage write failures and keep recommendation flow available.
  }
}
