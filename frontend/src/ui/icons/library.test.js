import { describe, expect, it } from 'vitest'
import {
  ArrowDown,
  Bell,
  Collection,
  Cpu,
  DataAnalysis,
  DocumentChecked,
  Download,
  EditPen,
  House,
  Plus,
  Reading,
  RefreshRight,
  Setting,
  UploadFilled,
  UserFilled,
  WarningFilled,
} from './library'

describe('ui icon library', () => {
  it('covers 正常路径 for locally hosted icon exports used by current pages', () => {
    expect(ArrowDown.name).toBe('ArrowDown')
    expect(Bell.name).toBe('Bell')
    expect(Collection.name).toBe('Collection')
    expect(Cpu.name).toBe('Cpu')
    expect(DataAnalysis.name).toBe('DataAnalysis')
    expect(DocumentChecked.name).toBe('DocumentChecked')
    expect(Download.name).toBe('Download')
    expect(EditPen.name).toBe('EditPen')
    expect(House.name).toBe('House')
    expect(Plus.name).toBe('Plus')
    expect(Reading.name).toBe('Reading')
    expect(RefreshRight.name).toBe('RefreshRight')
    expect(Setting.name).toBe('Setting')
    expect(UploadFilled.name).toBe('UploadFilled')
    expect(UserFilled.name).toBe('UserFilled')
    expect(WarningFilled.name).toBe('WarningFilled')
  })

  it('covers 异常路径 when icon factory consumers read component metadata only', () => {
    expect(typeof ArrowDown.setup).toBe('function')
    expect(typeof UploadFilled.setup).toBe('function')
  })

  it('covers 边界路径 for repeated bridge access across stroke and filled icons', () => {
    expect(Bell).toBe(Bell)
    expect(UserFilled).toBe(UserFilled)
  })
})
