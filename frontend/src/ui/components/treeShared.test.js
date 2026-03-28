import { describe, expect, it } from 'vitest'
import {
  buildTreeLabelMap,
  filterTreeNodes,
  flattenTreeNodes,
  normalizeTreeSelectValue,
  resolveTreeConfig,
  toggleTreeValue,
} from './treeShared'

const treeData = [
  {
    id: 'POL',
    name: '政治',
    children: [
      { id: 'POL-1', name: '马原', children: [] },
    ],
  },
  {
    id: 'ENG',
    name: '英语',
    children: [],
  },
]

describe('treeShared', () => {
  it('resolves tree config and flattens nested rows', () => {
    expect(resolveTreeConfig({ value: 'id', label: 'name', children: 'children' }, 'id')).toEqual({
      valueKey: 'id',
      labelKey: 'name',
      childrenKey: 'children',
    })
    expect(flattenTreeNodes(treeData, { props: { value: 'id', label: 'name', children: 'children' }, nodeKey: 'id' })).toEqual([
      expect.objectContaining({ key: 'POL', level: 0 }),
      expect.objectContaining({ key: 'POL-1', level: 1 }),
      expect.objectContaining({ key: 'ENG', level: 0 }),
    ])
  })

  it('covers 异常路径 when select value input is empty', () => {
    expect(normalizeTreeSelectValue(undefined, { multiple: true })).toEqual([])
    expect(toggleTreeValue('', '', { multiple: false })).toBe('')
  })

  it('covers 边界路径 for filtering and multi-select toggling', () => {
    expect(filterTreeNodes(treeData, '马', (keyword, node) => String(node?.name || '').includes(keyword), { props: { value: 'id', label: 'name', children: 'children' }, nodeKey: 'id' })).toEqual([
      expect.objectContaining({ key: 'POL', level: 0 }),
      expect.objectContaining({ key: 'POL-1', level: 1 }),
    ])
    expect(toggleTreeValue(['POL'], 'POL-1', { multiple: true })).toEqual(['POL', 'POL-1'])
    expect(toggleTreeValue(['POL', 'POL-1'], 'POL', { multiple: true })).toEqual(['POL-1'])
  })

  it('builds a label map for selected tree values', () => {
    expect(buildTreeLabelMap(treeData, { props: { value: 'id', label: 'name', children: 'children' }, nodeKey: 'id' }).get('ENG')).toBe('英语')
  })
})
