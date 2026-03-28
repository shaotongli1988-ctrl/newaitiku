import { beforeEach, describe, expect, it } from 'vitest'
import {
  clearStudentOnboardingCompleted,
  hasStudentOnboardingCompleted,
  isStudentOnboardingFlowPath,
  markStudentOnboardingCompleted,
  resolveStudentOnboardingRedirect,
} from './studentOnboarding'

function createStorageMock() {
  const store = new Map()
  return {
    clear() {
      store.clear()
    },
    getItem(key) {
      return store.has(key) ? store.get(key) : null
    },
    removeItem(key) {
      store.delete(key)
    },
    setItem(key, value) {
      store.set(String(key), String(value))
    },
  }
}

beforeEach(() => {
  Object.defineProperty(globalThis, 'localStorage', {
    value: createStorageMock(),
    configurable: true,
    writable: true,
  })
})

describe('student onboarding helpers', () => {
  it('detects onboarding flow routes', () => {
    expect(isStudentOnboardingFlowPath('/student/onboarding/diagnosis')).toBe(true)
    expect(isStudentOnboardingFlowPath('/student/subscription/checkout')).toBe(true)
    expect(isStudentOnboardingFlowPath('/student/home')).toBe(false)
  })

  it('正常路径: does not block incomplete student from other student pages', () => {
    expect(resolveStudentOnboardingRedirect({
      role: 'student',
      path: '/student/home',
      userId: 'student-001',
    })).toBe('')
  })

  it('skips redirect when student has completed onboarding', () => {
    markStudentOnboardingCompleted('student-001')

    expect(resolveStudentOnboardingRedirect({
      role: 'student',
      path: '/student/home',
      userId: 'student-001',
    })).toBe('')
    expect(hasStudentOnboardingCompleted('student-001')).toBe(true)
  })

  it('scopes completion state by user id', () => {
    markStudentOnboardingCompleted('student-001')

    expect(hasStudentOnboardingCompleted('student-001')).toBe(true)
    expect(hasStudentOnboardingCompleted('student-002')).toBe(false)

    clearStudentOnboardingCompleted('student-001')
    expect(hasStudentOnboardingCompleted('student-001')).toBe(false)
  })

  it('uses non-blocking navigation regardless of completion state', () => {
    expect(resolveStudentOnboardingRedirect({
      role: 'student',
      path: '/student/home',
      userId: 'student-001',
      completed: true,
    })).toBe('')

    expect(resolveStudentOnboardingRedirect({
      role: 'student',
      path: '/student/home',
      userId: 'student-001',
      completed: false,
    })).toBe('')
  })

  it('异常路径: never redirects non-student roles', () => {
    expect(resolveStudentOnboardingRedirect({
      role: 'teacher',
      path: '/student/home',
      userId: 'teacher-001',
    })).toBe('')
  })

  it('treats role matching as case-insensitive', () => {
    expect(resolveStudentOnboardingRedirect({
      role: 'STUDENT',
      path: '/student/home',
      userId: 'student-001',
    })).toBe('')
  })

  it('边界路径: skips redirect for non-student route path', () => {
    expect(resolveStudentOnboardingRedirect({
      role: 'student',
      path: '/teacher/home',
      userId: 'student-001',
    })).toBe('')
  })
})
