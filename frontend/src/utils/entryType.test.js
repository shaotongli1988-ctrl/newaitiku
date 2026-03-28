import { describe, expect, it } from 'vitest'
import { resolveEntryTypeFromLocation, resolveEntryTypeFromRole } from './entryType'

describe('resolveEntryTypeFromLocation', () => {
  it('uses teacher entry for teacher and admin paths', () => {
    expect(resolveEntryTypeFromLocation('/teacher', '')).toBe('teacher')
    expect(resolveEntryTypeFromLocation('/teacher/home', '')).toBe('teacher')
    expect(resolveEntryTypeFromLocation('/admin', '')).toBe('teacher')
    expect(resolveEntryTypeFromLocation('/teacher/questions', '')).toBe('teacher')
    expect(resolveEntryTypeFromLocation('/admin/home', '')).toBe('teacher')
  })

  it('uses student entry for student paths', () => {
    expect(resolveEntryTypeFromLocation('/student', '')).toBe('student')
    expect(resolveEntryTypeFromLocation('/student/home', '')).toBe('student')
  })

  it('falls back to stored role for shared routes', () => {
    expect(resolveEntryTypeFromLocation('/login', 'teacher')).toBe('teacher')
    expect(resolveEntryTypeFromLocation('/messages', 'super_admin')).toBe('teacher')
    expect(resolveEntryTypeFromLocation('/login', 'student')).toBe('student')
  })

  it('prefers live actor role on shared routes when available', () => {
    expect(resolveEntryTypeFromLocation('/messages', 'teacher', 'student')).toBe('student')
    expect(resolveEntryTypeFromLocation('/login', 'student', 'super_admin')).toBe('teacher')
  })

  it('defaults to student when route and role are both ambiguous', () => {
    expect(resolveEntryTypeFromLocation('/', '')).toBe('student')
    expect(resolveEntryTypeFromLocation('/login', '')).toBe('student')
  })
})

describe('resolveEntryTypeFromRole', () => {
  it('maps management roles to teacher entry', () => {
    expect(resolveEntryTypeFromRole('teacher')).toBe('teacher')
    expect(resolveEntryTypeFromRole('super_admin')).toBe('teacher')
  })

  it('defaults non-management roles to student entry', () => {
    expect(resolveEntryTypeFromRole('student')).toBe('student')
    expect(resolveEntryTypeFromRole('')).toBe('student')
  })
})
