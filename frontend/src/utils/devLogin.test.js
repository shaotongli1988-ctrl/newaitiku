import { describe, expect, it } from 'vitest'
import {
  buildNormalizedBootstrapUrl,
  resolveBootstrapPathname,
  resolveDevLoginPresetFromLocation,
  resolveDevLoginPresetFromPath,
} from './devLogin'

describe('devLogin helpers', () => {
  it('resolves dev login preset from query string', () => {
    expect(resolveDevLoginPresetFromLocation('?devLogin=teacher')?.phone).toBe('13800000002')
    expect(resolveDevLoginPresetFromLocation('?foo=bar')).toBe(null)
  })

  it('resolves student preset from student pathname', () => {
    expect(resolveDevLoginPresetFromPath('/student/question-bank/repair')?.role).toBe('student')
    expect(resolveDevLoginPresetFromPath('/teacher/home')?.role).toBe('teacher')
  })

  it('maps teacher entry html to teacher home when dev login preset is present', () => {
    expect(resolveBootstrapPathname({
      pathname: '/login',
      homePath: '',
      devLoginPreset: { homePath: '/teacher/home' },
    })).toBe('/teacher/home')
  })

  it('keeps current page path when no redirect target is present', () => {
    expect(resolveBootstrapPathname({
      pathname: '/teacher/home',
      homePath: '',
      devLoginPreset: null,
    })).toBe('/teacher/home')
  })

  it('removes devLogin query from normalized url', () => {
    expect(buildNormalizedBootstrapUrl({
      pathname: '/teacher/home',
      search: '?devLogin=teacher&foo=bar',
      hash: '',
    })).toBe('/teacher/home?foo=bar')
  })
})
