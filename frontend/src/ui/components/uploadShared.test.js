import { describe, expect, it } from 'vitest'
import {
  buildUploadFile,
  matchesUploadAccept,
  normalizeUploadFileList,
  splitUploadFiles,
} from './uploadShared'

describe('uploadShared', () => {
  it('normalizes raw files into stable upload entries', () => {
    const file = buildUploadFile({ name: 'syllabus.pdf', size: 128 })
    expect(file.name).toBe('syllabus.pdf')
    expect(file.size).toBe(128)
    expect(file.status).toBe('ready')
    expect(file.uid).toContain('ui-upload-')
  })

  it('covers 异常路径 when file list input is missing or accept is empty', () => {
    expect(normalizeUploadFileList(undefined)).toEqual([])
    expect(matchesUploadAccept({ name: 'outline.docx', type: '' }, '')).toBe(true)
  })

  it('covers 边界路径 for accept matching and limit splitting', () => {
    expect(matchesUploadAccept({ name: 'outline.docx', type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' }, '.pdf,.doc,.docx')).toBe(true)
    expect(matchesUploadAccept({ name: 'outline.png', type: 'image/png' }, '.pdf,.docx')).toBe(false)
    expect(splitUploadFiles([{ name: 'a' }, { name: 'b' }], 1, 0)).toEqual({
      accepted: [{ name: 'a' }],
      exceeded: [{ name: 'b' }],
    })
  })

  it('keeps explicit file metadata when normalizing existing upload lists', () => {
    expect(normalizeUploadFileList([{ uid: '1', name: 'demo.txt', size: 12 }])).toEqual([
      expect.objectContaining({ uid: '1', name: 'demo.txt', size: 12 }),
    ])
  })
})
