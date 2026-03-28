import { afterEach, describe, expect, it } from 'vitest'
import {
  LEARNING_METHOD_RECOMMENDATION_STRATEGY,
  LEARNING_METHOD_RECOMMENDATION_STRATEGY_SOURCE,
  learningMethodRecommendationStrategySourceLabel,
  loadPersistedLearningMethodRecommendationStrategy,
  normalizeLearningMethodRecommendationStrategyCode,
  normalizeLearningMethodRecommendationStrategySource,
  recommendationStrategyCodeByPracticeStrategy,
  resolveLearningMethodRecommendationStrategyFromPayload,
  resolveLearningMethodRecommendationStrategySourceFromPayload,
  savePersistedLearningMethodRecommendationStrategy,
} from './learningMethodStrategy'

function createLocalStorageMock() {
  const store = new Map()
  return {
    getItem(key) {
      return store.has(key) ? store.get(key) : null
    },
    setItem(key, value) {
      store.set(key, String(value))
    },
    removeItem(key) {
      store.delete(key)
    },
  }
}

afterEach(() => {
  delete globalThis.localStorage
})

describe('learningMethodStrategy helpers', () => {
  it('normalizes strategy code and source with defaults', () => {
    expect(normalizeLearningMethodRecommendationStrategyCode('foundation')).toBe(
      LEARNING_METHOD_RECOMMENDATION_STRATEGY.FOUNDATION,
    )
    expect(normalizeLearningMethodRecommendationStrategyCode('invalid')).toBe(
      LEARNING_METHOD_RECOMMENDATION_STRATEGY.BALANCED,
    )
    expect(normalizeLearningMethodRecommendationStrategySource('manual')).toBe(
      LEARNING_METHOD_RECOMMENDATION_STRATEGY_SOURCE.MANUAL,
    )
    expect(normalizeLearningMethodRecommendationStrategySource('unknown')).toBe(
      LEARNING_METHOD_RECOMMENDATION_STRATEGY_SOURCE.DEFAULT,
    )
  })

  it('maps practiceStrategy to recommendation strategy code', () => {
    expect(recommendationStrategyCodeByPracticeStrategy('FOUNDATION_REINFORCE')).toBe(
      LEARNING_METHOD_RECOMMENDATION_STRATEGY.FOUNDATION,
    )
    expect(recommendationStrategyCodeByPracticeStrategy('SPRINT_BREAKTHROUGH')).toBe(
      LEARNING_METHOD_RECOMMENDATION_STRATEGY.SPRINT,
    )
    expect(recommendationStrategyCodeByPracticeStrategy('DEFAULT')).toBe(
      LEARNING_METHOD_RECOMMENDATION_STRATEGY.BALANCED,
    )
  })

  it('resolves strategy code from payload fields', () => {
    expect(resolveLearningMethodRecommendationStrategyFromPayload({
      recommendationStrategyCode: 'SPRINT',
      practiceStrategy: 'FOUNDATION_REINFORCE',
    })).toBe(LEARNING_METHOD_RECOMMENDATION_STRATEGY.SPRINT)

    expect(resolveLearningMethodRecommendationStrategyFromPayload({
      recommendationLog: {
        practiceStrategy: 'FOUNDATION_REINFORCE',
      },
    })).toBe(LEARNING_METHOD_RECOMMENDATION_STRATEGY.FOUNDATION)

    expect(resolveLearningMethodRecommendationStrategyFromPayload({
      extJson: {
        practiceStrategy: 'BALANCED_ADVANCE',
      },
    })).toBe(LEARNING_METHOD_RECOMMENDATION_STRATEGY.BALANCED)
  })

  it('resolves strategy source from payload fields', () => {
    expect(resolveLearningMethodRecommendationStrategySourceFromPayload({
      recommendationStrategySource: 'manual',
    })).toBe(LEARNING_METHOD_RECOMMENDATION_STRATEGY_SOURCE.MANUAL)

    expect(resolveLearningMethodRecommendationStrategySourceFromPayload({
      recommendationLog: {
        strategySource: 'suggested',
      },
    })).toBe(LEARNING_METHOD_RECOMMENDATION_STRATEGY_SOURCE.SUGGESTED)

    expect(resolveLearningMethodRecommendationStrategySourceFromPayload({
      extJson: {
        strategySource: 'default',
      },
    })).toBe(LEARNING_METHOD_RECOMMENDATION_STRATEGY_SOURCE.DEFAULT)
  })

  it('stores and loads strategy state by subject and method', () => {
    globalThis.localStorage = createLocalStorageMock()
    savePersistedLearningMethodRecommendationStrategy({
      subjectCode: 'POLITICS',
      methodCode: 'M01',
      strategyCode: 'SPRINT',
      source: 'manual',
    })

    expect(loadPersistedLearningMethodRecommendationStrategy({
      subjectCode: 'POLITICS',
      methodCode: 'M01',
    })).toMatchObject({
      strategyCode: LEARNING_METHOD_RECOMMENDATION_STRATEGY.SPRINT,
      source: LEARNING_METHOD_RECOMMENDATION_STRATEGY_SOURCE.MANUAL,
    })

    expect(loadPersistedLearningMethodRecommendationStrategy({
      subjectCode: 'ENGLISH',
      methodCode: 'M01',
    })).toBeNull()
  })

  it('returns readable source label', () => {
    expect(learningMethodRecommendationStrategySourceLabel('manual')).toBe('手动切换')
    expect(learningMethodRecommendationStrategySourceLabel('suggested')).toBe('趋势建议')
    expect(learningMethodRecommendationStrategySourceLabel('unknown')).toBe('系统默认')
  })
})
