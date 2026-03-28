import { describe, expect, it } from 'vitest'
import {
  filterSelectOptions,
  isSelectValueEmpty,
  isSelectValueEqual,
  normalizeSelectValue,
  toggleSelectMultipleValue,
} from './selectShared'

describe('selectShared', () => {
  it('normalizes single and multiple model values into stable shapes', () => {
    expect(normalizeSelectValue(undefined, { multiple: false })).toBeUndefined()
    expect(normalizeSelectValue('POLITICS', { multiple: false })).toBe('POLITICS')
    expect(normalizeSelectValue(undefined, { multiple: true })).toEqual([])
  })

  it('covers 异常路径 when empty values are checked', () => {
    expect(isSelectValueEmpty('', { multiple: false })).toBe(true)
    expect(isSelectValueEmpty(undefined, { multiple: false })).toBe(true)
    expect(isSelectValueEmpty([], { multiple: true })).toBe(true)
  })

  it('covers 边界路径 for multiple selection toggling', () => {
    expect(toggleSelectMultipleValue(['A'], 'B')).toEqual(['A', 'B'])
    expect(toggleSelectMultipleValue(['A', 'B'], 'A')).toEqual(['B'])
  })

  it('filters options by label or value and compares values safely', () => {
    const options = [
      { label: '政治', value: 'POLITICS' },
      { label: '英语', value: 'ENGLISH' },
    ]

    expect(filterSelectOptions(options, '英')).toEqual([options[1]])
    expect(filterSelectOptions(options, 'polit')).toEqual([options[0]])
    expect(isSelectValueEqual(['A', 'B'], ['A', 'B'], { multiple: true })).toBe(true)
  })
})
