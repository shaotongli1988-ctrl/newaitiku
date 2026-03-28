import { describe, expect, it } from 'vitest'
import {
  normalizeButtonSize,
  normalizeButtonType,
  resolveButtonPalette,
  resolveButtonVariant,
} from './buttonShared'

describe('buttonShared', () => {
  it('normalizes button type and size into supported values', () => {
    expect(normalizeButtonType('primary')).toBe('primary')
    expect(normalizeButtonType('unknown')).toBe('')
    expect(normalizeButtonSize('small')).toBe('small')
    expect(normalizeButtonSize('weird')).toBe('default')
  })

  it('covers 异常路径 when conflicting variant flags are present', () => {
    expect(resolveButtonVariant({ plain: true, text: true, link: true })).toBe('link')
    expect(resolveButtonVariant({ plain: true, text: true })).toBe('text')
  })

  it('covers 边界路径 for plain and solid palette resolution', () => {
    expect(resolveButtonVariant({ plain: true })).toBe('plain')
    expect(resolveButtonVariant({})).toBe('solid')
    expect(resolveButtonPalette('danger', 'plain').text).toContain('var(--qb-danger)')
  })

  it('falls back to default palette when type or variant is unknown', () => {
    const fallback = resolveButtonPalette('unknown', 'mystery')
    expect(fallback.bg).toBe('var(--qb-surface-strong)')
    expect(fallback.border).toContain('var(--qb-border-muted)')
  })
})
