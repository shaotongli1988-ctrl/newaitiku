import { describe, expect, it } from 'vitest'
import { isRoutePathAllowedInEntry } from './navigationScope'

describe('isRoutePathAllowedInEntry', () => {
  it('keeps shared routes visible in both entries', () => {
    expect(isRoutePathAllowedInEntry('/', 'student')).toBe(true)
    expect(isRoutePathAllowedInEntry('/login', 'teacher')).toBe(true)
    expect(isRoutePathAllowedInEntry('/messages', 'student')).toBe(true)
    expect(isRoutePathAllowedInEntry('/error/500', 'teacher')).toBe(true)
  })

  it('blocks teacher pages from student entry', () => {
    expect(isRoutePathAllowedInEntry('/teacher/import-history', 'student')).toBe(false)
    expect(isRoutePathAllowedInEntry('/teacher/analytics', 'student')).toBe(false)
    expect(isRoutePathAllowedInEntry('/admin/home', 'student')).toBe(false)
  })

  it('blocks student pages from teacher entry', () => {
    expect(isRoutePathAllowedInEntry('/student/home', 'teacher')).toBe(false)
    expect(isRoutePathAllowedInEntry('/student/practice', 'teacher')).toBe(false)
  })

  it('keeps in-scope pages available', () => {
    expect(isRoutePathAllowedInEntry('/student/home', 'student')).toBe(true)
    expect(isRoutePathAllowedInEntry('/student/practice', 'student')).toBe(true)
    expect(isRoutePathAllowedInEntry('/teacher/home', 'teacher')).toBe(true)
    expect(isRoutePathAllowedInEntry('/teacher/analytics', 'teacher')).toBe(true)
    expect(isRoutePathAllowedInEntry('/admin/home', 'teacher')).toBe(true)
  })
})
