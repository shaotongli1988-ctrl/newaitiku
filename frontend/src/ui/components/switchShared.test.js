import { describe, expect, it } from 'vitest'
import {
  resolveSwitchChecked,
  resolveSwitchNextValue,
  resolveSwitchPrompt,
} from './switchShared'

describe('switchShared', () => {
  it('matches model value against active value', () => {
    expect(resolveSwitchChecked(true, true)).toBe(true)
    expect(resolveSwitchChecked('ENABLED', 'ENABLED')).toBe(true)
    expect(resolveSwitchChecked(false, true)).toBe(false)
  })

  it('returns the right next switch value', () => {
    expect(resolveSwitchNextValue(true, 'ON', 'OFF')).toBe('ON')
    expect(resolveSwitchNextValue(false, 'ON', 'OFF')).toBe('OFF')
  })

  it('selects the visible prompt from checked state', () => {
    expect(resolveSwitchPrompt(true, '启用', '停用')).toBe('启用')
    expect(resolveSwitchPrompt(false, '启用', '停用')).toBe('停用')
  })

  it('covers 异常路径 when prompt text is missing', () => {
    expect(resolveSwitchPrompt(true, '', '')).toBe('')
    expect(resolveSwitchPrompt(false, '', '')).toBe('')
  })

  it('covers 边界路径 for zero-like inactive values', () => {
    expect(resolveSwitchNextValue(false, 1, 0)).toBe(0)
    expect(resolveSwitchChecked(0, 1)).toBe(false)
  })
})
