import {
  LEARNING_METHOD_RECOMMENDATION_STRATEGY_SOURCE,
  learningMethodRecommendationStrategySourceLabel,
  normalizeLearningMethodRecommendationStrategyCode,
  normalizeLearningMethodRecommendationStrategySource,
} from './learningMethodStrategy.js'

const SOURCE_DISPLAY_ORDER = [
  LEARNING_METHOD_RECOMMENDATION_STRATEGY_SOURCE.SUGGESTED,
  LEARNING_METHOD_RECOMMENDATION_STRATEGY_SOURCE.MANUAL,
  LEARNING_METHOD_RECOMMENDATION_STRATEGY_SOURCE.DEFAULT,
]

function toNumber(value) {
  const numericValue = Number(value || 0)
  if (!Number.isFinite(numericValue)) {
    return 0
  }
  return numericValue
}

function normalizeFitRatio(value) {
  const numericValue = toNumber(value)
  if (numericValue <= 0) {
    return 0
  }
  if (numericValue > 1) {
    return Math.max(0, Math.min(1, numericValue / 100))
  }
  return Math.max(0, Math.min(1, numericValue))
}

function normalizeFeedbackStatus(value) {
  return String(value || '').trim().toUpperCase()
}

function sourceInsightOrder(source) {
  const index = SOURCE_DISPLAY_ORDER.indexOf(source)
  if (index >= 0) {
    return index
  }
  return SOURCE_DISPLAY_ORDER.length
}

function resolveBestStrategyInsight(strategyMap) {
  const rows = Array.from(strategyMap.values())
  if (!rows.length) {
    return {
      code: '',
      sampleCount: 0,
    }
  }
  rows.sort((left, right) => {
    if (right.sampleCount !== left.sampleCount) {
      return right.sampleCount - left.sampleCount
    }
    if (right.averageFit !== left.averageFit) {
      return right.averageFit - left.averageFit
    }
    if (right.acceptedRate !== left.acceptedRate) {
      return right.acceptedRate - left.acceptedRate
    }
    return String(left.code || '').localeCompare(String(right.code || ''))
  })
  return {
    code: String(rows[0]?.code || '').trim().toUpperCase(),
    sampleCount: Number(rows[0]?.sampleCount || 0),
  }
}

export function computeLearningMethodSourceInsights(rows = []) {
  const sourceRows = Array.isArray(rows) ? rows : []
  const grouped = new Map()

  sourceRows.forEach((row) => {
    const source = normalizeLearningMethodRecommendationStrategySource(
      row?.recommendationStrategySource,
      LEARNING_METHOD_RECOMMENDATION_STRATEGY_SOURCE.DEFAULT,
    )
    const previous = grouped.get(source) || {
      source,
      totalCount: 0,
      totalFit: 0,
      totalScore: 0,
      feedbackCount: 0,
      acceptedCount: 0,
      strategies: new Map(),
    }
    previous.totalCount += 1
    const fitRatio = normalizeFitRatio(row?.studentProfileFitAverage)
    const averageScore = toNumber(row?.averageScore)
    previous.totalFit += fitRatio
    previous.totalScore += averageScore
    const feedbackStatus = normalizeFeedbackStatus(row?.feedbackStatus)
    if (feedbackStatus === 'ACCEPTED' || feedbackStatus === 'PARTIAL' || feedbackStatus === 'REJECTED') {
      previous.feedbackCount += 1
      if (feedbackStatus === 'ACCEPTED') {
        previous.acceptedCount += 1
      }
    }
    const strategyCode = normalizeLearningMethodRecommendationStrategyCode(
      row?.recommendationStrategyCode,
      '',
    )
    if (strategyCode) {
      const strategyPrev = previous.strategies.get(strategyCode) || {
        code: strategyCode,
        sampleCount: 0,
        totalFit: 0,
        feedbackCount: 0,
        acceptedCount: 0,
      }
      strategyPrev.sampleCount += 1
      strategyPrev.totalFit += fitRatio
      if (feedbackStatus === 'ACCEPTED' || feedbackStatus === 'PARTIAL' || feedbackStatus === 'REJECTED') {
        strategyPrev.feedbackCount += 1
        if (feedbackStatus === 'ACCEPTED') {
          strategyPrev.acceptedCount += 1
        }
      }
      strategyPrev.averageFit = strategyPrev.sampleCount
        ? Number((strategyPrev.totalFit / strategyPrev.sampleCount).toFixed(4))
        : 0
      strategyPrev.acceptedRate = strategyPrev.feedbackCount
        ? Number((strategyPrev.acceptedCount / strategyPrev.feedbackCount).toFixed(4))
        : 0
      previous.strategies.set(strategyCode, strategyPrev)
    }
    grouped.set(source, previous)
  })

  return Array.from(grouped.values())
    .map((item) => {
      const bestStrategy = resolveBestStrategyInsight(item.strategies)
      return {
        source: item.source,
        sampleCount: item.totalCount,
        averageFit: item.totalCount ? Number((item.totalFit / item.totalCount).toFixed(4)) : 0,
        averageScore: item.totalCount ? Number((item.totalScore / item.totalCount).toFixed(4)) : 0,
        acceptedRate: item.feedbackCount ? Number((item.acceptedCount / item.feedbackCount).toFixed(4)) : 0,
        recommendedStrategyCode: bestStrategy.code,
        recommendedStrategySampleCount: bestStrategy.sampleCount,
      }
    })
    .sort((left, right) => {
      if (right.sampleCount !== left.sampleCount) {
        return right.sampleCount - left.sampleCount
      }
      if (right.averageFit !== left.averageFit) {
        return right.averageFit - left.averageFit
      }
      return sourceInsightOrder(left.source) - sourceInsightOrder(right.source)
    })
}

export function summarizeLearningMethodSourceInsights(insights = []) {
  const sourceInsights = Array.isArray(insights) ? insights : []
  if (!sourceInsights.length) {
    return '暂无来源对比数据，继续生成题包后会自动形成效果看板。'
  }
  const top = sourceInsights[0]
  if (!top || Number(top.sampleCount || 0) <= 0) {
    return '暂无来源对比数据，继续生成题包后会自动形成效果看板。'
  }
  const fitPercent = Math.round(normalizeFitRatio(top.averageFit) * 100)
  return `当前最优来源：${learningMethodRecommendationStrategySourceLabel(top.source)}，样本 ${top.sampleCount} 次，平均画像匹配 ${fitPercent}%。`
}
