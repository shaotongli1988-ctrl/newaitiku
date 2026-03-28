import { describe, expect, it } from 'vitest'
import {
  clampSliderValue,
  normalizeSliderStep,
  normalizeSliderValue,
  resolveSliderFillPercent,
} from './sliderShared'

describe('sliderShared', () => {
  it('normalizes slider values into the configured range', () => {
    expect(normalizeSliderValue(3, { min: 1, max: 5, step: 1 })).toBe(3)
  })

  it('covers 异常路径 when value or step input is invalid', () => {
    expect(clampSliderValue('abc', 1, 5)).toBe(1)
    expect(normalizeSliderStep(0)).toBe(1)
  })

  it('covers 边界路径 for stepping and fill percentage', () => {
    expect(normalizeSliderValue(4.6, { min: 1, max: 5, step: 1 })).toBe(5)
    expect(resolveSliderFillPercent(3, 1, 5)).toBe(50)
  })
})
