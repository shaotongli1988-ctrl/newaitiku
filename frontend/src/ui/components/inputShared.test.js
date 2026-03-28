import { describe, expect, it } from 'vitest'
import {
  normalizeInputValue,
  resolveInputControlType,
  resolveInputMaxlength,
  shouldShowInputClear,
} from './inputShared'

describe('inputShared', () => {
  it('normalizes model values into text that inputs can display', () => {
    expect(normalizeInputValue(undefined)).toBe('')
    expect(normalizeInputValue(42)).toBe('42')
  })

  it('covers 异常路径 when maxlength is not a valid positive number', () => {
    expect(resolveInputMaxlength('abc')).toBeUndefined()
    expect(resolveInputMaxlength(0)).toBeUndefined()
  })

  it('covers 边界路径 for password toggle and textarea mode', () => {
    expect(resolveInputControlType('password', true, false)).toBe('password')
    expect(resolveInputControlType('password', true, true)).toBe('text')
    expect(resolveInputControlType('textarea', true, true)).toBe('textarea')
  })

  it('only shows the clear trigger when the field can really be cleared', () => {
    expect(shouldShowInputClear({ clearable: true, hasValue: true })).toBe(true)
    expect(shouldShowInputClear({ clearable: true, hasValue: true, readonly: true })).toBe(false)
  })
})
