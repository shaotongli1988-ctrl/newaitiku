import { describe, expect, it } from 'vitest'
import {
  buildCascaderColumns,
  buildCascaderSelections,
  filterCascaderSelections,
  findCascaderSelection,
  formatCascaderSelectionLabel,
  toCascaderModelValue,
} from './cascaderShared'

const professionalOptions = [
  {
    code: 'SCIENCE',
    name: '理工类',
    children: [
      {
        code: 'SCIENCE_3',
        name: '联考组三',
        children: [
          { code: 'INFO_TECH', name: '信息技术' },
        ],
      },
    ],
  },
]

describe('cascaderShared', () => {
  it('covers 正常路径 for leaf-only cascaders with emitPath output', () => {
    const rows = buildCascaderSelections(professionalOptions, {
      value: 'code',
      label: 'name',
      children: 'children',
      checkStrictly: false,
      emitPath: true,
    })

    expect(rows).toHaveLength(1)
    expect(rows[0].path).toEqual(['SCIENCE', 'SCIENCE_3', 'INFO_TECH'])
  })

  it('covers 异常路径 when the model value does not match any option', () => {
    const selected = findCascaderSelection(professionalOptions, ['UNKNOWN'], {
      value: 'code',
      label: 'name',
      children: 'children',
      emitPath: true,
    })

    expect(selected).toBeNull()
  })

  it('covers 边界路径 for strict selection and column expansion', () => {
    const rows = buildCascaderSelections(professionalOptions, {
      value: 'code',
      label: 'name',
      children: 'children',
      checkStrictly: true,
    })
    const columns = buildCascaderColumns(professionalOptions, ['SCIENCE', 'SCIENCE_3'], {
      value: 'code',
      label: 'name',
      children: 'children',
    })

    expect(rows).toHaveLength(3)
    expect(columns).toHaveLength(3)
  })

  it('filters rows and formats selection labels consistently', () => {
    const rows = buildCascaderSelections(professionalOptions, {
      value: 'code',
      label: 'name',
      children: 'children',
      emitPath: true,
      checkStrictly: false,
    })
    const selected = findCascaderSelection(professionalOptions, ['SCIENCE', 'SCIENCE_3', 'INFO_TECH'], {
      value: 'code',
      label: 'name',
      children: 'children',
      emitPath: true,
    })

    expect(filterCascaderSelections(rows, '信息')).toEqual(rows)
    expect(formatCascaderSelectionLabel(selected)).toBe('理工类 / 联考组三 / 信息技术')
    expect(toCascaderModelValue(selected, { emitPath: false })).toBe('INFO_TECH')
  })
})
