import { describe, expect, it } from 'vitest'
import {
  clampInputNumber,
  formatInputNumberValue,
  normalizeInputNumberValue,
  resolveInputNumberPrecision,
  stepInputNumber,
} from './inputNumberShared'

describe('inputNumberShared', () => {
  it('normalizes values into the configured numeric range', () => {
    expect(normalizeInputNumberValue(36, { min: 30, max: 240, precision: 0 })).toBe(36)
    expect(normalizeInputNumberValue(500, { min: 30, max: 240, precision: 0 })).toBe(240)
  })

  it('covers 异常路径 when input is not a finite number', () => {
    expect(normalizeInputNumberValue('abc', { min: 0, max: 10, precision: 0 })).toBeUndefined()
    expect(clampInputNumber(undefined, 0, 10)).toBeUndefined()
  })

  it('covers 边界路径 for decimal precision and stepping', () => {
    expect(resolveInputNumberPrecision(0.01, 6)).toBe(6)
    expect(stepInputNumber(0.99, 1, { min: 0, max: 1, step: 0.01, precision: 6 })).toBe(1)
  })

  it('formats numeric display text without trailing zero noise', () => {
    expect(formatInputNumberValue(1, 2)).toBe('1')
    expect(formatInputNumberValue(0.125, 6)).toBe('0.125')
  })
})
