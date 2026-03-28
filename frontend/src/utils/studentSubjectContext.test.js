import { describe, expect, it } from 'vitest'
import { resolveStudentSubjectCode } from './studentSubjectContext.js'

describe('studentSubjectContext helpers', () => {
  it('prefers the first valid candidate subject code', () => {
    const subjectOptions = [
      { subjectCode: 'POLITICS', subjectName: '政治' },
      { subjectCode: 'ENGLISH', subjectName: '英语' },
      { subjectCode: 'ADVANCED_MATH_1', subjectName: '高等数学（一）' },
    ]

    expect(
      resolveStudentSubjectCode(subjectOptions, 'UNKNOWN', 'ENGLISH', 'ADVANCED_MATH_1'),
    ).toBe('ENGLISH')
  })

  it('falls back to the first available subject when the route subject code is invalid', () => {
    const subjectOptions = [
      { subjectCode: 'POLITICS', subjectName: '政治' },
      { subjectCode: 'ENGLISH', subjectName: '英语' },
    ]

    expect(resolveStudentSubjectCode(subjectOptions, 'invalid-subject')).toBe('POLITICS')
  })
})
