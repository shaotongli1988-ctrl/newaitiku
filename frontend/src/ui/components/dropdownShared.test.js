import { describe, expect, it } from 'vitest'
import {
  normalizeDropdownTrigger,
  resolveDropdownCommand,
  shouldCloseDropdownOnCommand,
} from './dropdownShared'

describe('dropdownShared', () => {
  it('normalizes trigger mode to supported values', () => {
    expect(normalizeDropdownTrigger('hover')).toBe('hover')
    expect(normalizeDropdownTrigger('contextmenu')).toBe('click')
  })

  it('covers 异常路径 when command payload is omitted', () => {
    expect(resolveDropdownCommand(undefined, 'DEFAULT')).toBe('DEFAULT')
  })

  it('covers 边界路径 for click-hide behavior', () => {
    expect(shouldCloseDropdownOnCommand({ hideOnClick: true, disabled: false })).toBe(true)
    expect(shouldCloseDropdownOnCommand({ hideOnClick: true, disabled: true })).toBe(false)
  })
})
