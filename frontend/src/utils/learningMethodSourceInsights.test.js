import { describe, expect, it } from 'vitest'
import {
  computeLearningMethodSourceInsights,
  summarizeLearningMethodSourceInsights,
} from './learningMethodSourceInsights.js'

describe('learningMethodSourceInsights', () => {
  it('groups by source and computes average metrics', () => {
    const insights = computeLearningMethodSourceInsights([
      {
        recommendationStrategySource: 'SUGGESTED',
        recommendationStrategyCode: 'SPRINT',
        studentProfileFitAverage: 0.82,
        averageScore: 0.74,
        feedbackStatus: 'ACCEPTED',
      },
      {
        recommendationStrategySource: 'SUGGESTED',
        recommendationStrategyCode: 'BALANCED',
        studentProfileFitAverage: 0.9,
        averageScore: 0.81,
        feedbackStatus: 'PARTIAL',
      },
      {
        recommendationStrategySource: 'MANUAL',
        recommendationStrategyCode: 'FOUNDATION',
        studentProfileFitAverage: 0.65,
        averageScore: 0.6,
        feedbackStatus: 'REJECTED',
      },
    ])

    expect(insights[0]).toEqual(expect.objectContaining({
      source: 'SUGGESTED',
      sampleCount: 2,
      averageFit: 0.86,
      averageScore: 0.775,
      acceptedRate: 0.5,
      recommendedStrategyCode: 'BALANCED',
      recommendedStrategySampleCount: 1,
    }))
    expect(insights[1]).toEqual(expect.objectContaining({
      source: 'MANUAL',
      sampleCount: 1,
      averageFit: 0.65,
      averageScore: 0.6,
      acceptedRate: 0,
      recommendedStrategyCode: 'FOUNDATION',
      recommendedStrategySampleCount: 1,
    }))
  })

  it('normalizes unknown source to DEFAULT and supports percentage fit values', () => {
    const insights = computeLearningMethodSourceInsights([
      {
        recommendationStrategySource: 'UNKNOWN',
        studentProfileFitAverage: 78,
        averageScore: 0.7,
        feedbackStatus: 'PENDING',
      },
    ])

    expect(insights).toEqual([
      expect.objectContaining({
        source: 'DEFAULT',
        sampleCount: 1,
        averageFit: 0.78,
        averageScore: 0.7,
        acceptedRate: 0,
        recommendedStrategyCode: '',
        recommendedStrategySampleCount: 0,
      }),
    ])
  })

  it('builds summary text from top source insight', () => {
    expect(summarizeLearningMethodSourceInsights([
      {
        source: 'SUGGESTED',
        sampleCount: 3,
        averageFit: 0.84,
      },
    ])).toBe('当前最优来源：趋势建议，样本 3 次，平均画像匹配 84%。')

    expect(summarizeLearningMethodSourceInsights([])).toContain('暂无来源对比数据')
  })
})
