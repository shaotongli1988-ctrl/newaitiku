import { describe, expect, it } from 'vitest'
import {
  normalizeDialogWidth,
  normalizeOverlayDirection,
  normalizeOverlaySize,
  resolveDrawerPanelStyle,
} from './dialogShared'

describe('dialogShared', () => {
  it('normalizes direction to supported drawer placements', () => {
    expect(normalizeOverlayDirection('ltr')).toBe('ltr')
    expect(normalizeOverlayDirection('')).toBe('rtl')
  })

  it('covers 异常路径 when size or width input is invalid', () => {
    expect(normalizeOverlaySize('', '55%')).toBe('55%')
    expect(normalizeDialogWidth(undefined, '720px')).toBe('720px')
  })

  it('covers 边界路径 for numeric sizing and top-to-bottom drawers', () => {
    expect(normalizeOverlaySize(280)).toBe('280px')
    expect(resolveDrawerPanelStyle('ttb', '72vh')).toEqual({
      '--ui-drawer-width': '100vw',
      '--ui-drawer-height': '72vh',
    })
  })

  it('resolves side drawer width when direction is horizontal', () => {
    expect(resolveDrawerPanelStyle('rtl', '36%')).toEqual({
      '--ui-drawer-width': '36%',
      '--ui-drawer-height': '100vh',
    })
  })
})
