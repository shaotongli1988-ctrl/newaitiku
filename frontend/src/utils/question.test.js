import { describe, expect, it } from 'vitest'

import { questionDifficultyLabel, questionStatusMeta } from './question'

describe('questionStatusMeta', () => {
  it('falls back to draft metadata for unknown question statuses', () => {
    expect(questionStatusMeta('OFFLINE')).toEqual(questionStatusMeta('DRAFT'))
  })
})

describe('questionDifficultyLabel', () => {
  it('maps english difficulty values to chinese labels', () => {
    expect(questionDifficultyLabel('easy')).toBe('简单')
    expect(questionDifficultyLabel('medium')).toBe('中等')
    expect(questionDifficultyLabel('hard')).toBe('困难')
  })
})
