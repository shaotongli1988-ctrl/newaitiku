import { describe, expect, it } from 'vitest'
import {
  formatDatePickerOutput,
  normalizeDatePickerInputValue,
  resolveDatePickerInputType,
} from './datePickerShared'

describe('datePickerShared', () => {
  it('covers 正常路径 for datetime-local input and formatted output', () => {
    expect(resolveDatePickerInputType('datetime')).toBe('datetime-local')
    expect(
      normalizeDatePickerInputValue('2026-03-24T08:30:00', { type: 'datetime' }),
    ).toBe('2026-03-24T08:30:00')
    expect(
      formatDatePickerOutput('2026-03-24T08:30:00', { type: 'datetime', valueFormat: 'YYYY-MM-DDTHH:mm:ss' }),
    ).toBe('2026-03-24T08:30:00')
  })

  it('covers 异常路径 when incoming values are invalid', () => {
    expect(normalizeDatePickerInputValue('not-a-date', { type: 'datetime' })).toBe('')
    expect(formatDatePickerOutput('bad-input', { type: 'datetime', valueFormat: 'YYYY-MM-DDTHH:mm:ss' })).toBe('')
  })

  it('covers 边界路径 for missing seconds and date-only values', () => {
    expect(
      normalizeDatePickerInputValue('2026-03-24 08:30', { type: 'datetime' }),
    ).toBe('2026-03-24T08:30:00')
    expect(formatDatePickerOutput('2026-03-24T08:30', { type: 'datetime', valueFormat: 'YYYY-MM-DDTHH:mm:ss' })).toBe('2026-03-24T08:30:00')
    expect(formatDatePickerOutput('2026-03-24', { type: 'date' })).toBe('2026-03-24')
  })

  it('supports native date input formatting without datetime conversion noise', () => {
    expect(resolveDatePickerInputType('date')).toBe('date')
    expect(normalizeDatePickerInputValue('2026-03-24', { type: 'date' })).toBe('2026-03-24')
  })
})
