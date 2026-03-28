import { describe, expect, it } from 'vitest'
import {
  buildStickyOffsets,
  normalizeExpandedKeys,
  normalizeFixedPosition,
  normalizeTableColumnType,
  resolveTableRowKey,
} from './tableShared'

describe('tableShared', () => {
  it('normalizes supported column types and fixed positions', () => {
    expect(normalizeTableColumnType('selection')).toBe('selection')
    expect(normalizeTableColumnType('unknown')).toBe('default')
    expect(normalizeFixedPosition(true)).toBe('left')
    expect(normalizeFixedPosition('right')).toBe('right')
  })

  it('covers 异常路径 when row-key input is missing or blank', () => {
    expect(resolveTableRowKey({ id: 'row-1' }, '', 2)).toBe('2')
    expect(resolveTableRowKey({}, 'id', 0)).toBe('')
  })

  it('covers 边界路径 for normalized expanded keys and function row keys', () => {
    expect(normalizeExpandedKeys(['a', 'a', '', 'b'])).toEqual(['a', 'b'])
    expect(resolveTableRowKey({ traceId: 't-1' }, (row) => row.traceId, 0)).toBe('t-1')
  })

  it('builds sticky offsets for left and right fixed columns', () => {
    const offsets = buildStickyOffsets([
      { uid: 'selection', type: 'selection', fixed: 'left', width: 55 },
      { uid: 'name', minWidth: 200 },
      { uid: 'actions', fixed: 'right', width: 140 },
    ])

    expect(offsets.leftOffsets).toEqual({ selection: 0 })
    expect(offsets.rightOffsets).toEqual({ actions: 0 })
  })
})
