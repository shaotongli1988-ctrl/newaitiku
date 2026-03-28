import { describe, expect, it } from 'vitest'
import { normalizeCollapseDuration } from './collapseTransitionShared'

describe('collapseTransitionShared', () => {
  it('normalizes explicit duration values', () => {
    expect(normalizeCollapseDuration(180)).toBe(180)
  })

  it('covers 异常路径 when duration input is missing or invalid', () => {
    expect(normalizeCollapseDuration(undefined)).toBe(220)
    expect(normalizeCollapseDuration(-1)).toBe(220)
  })
})
