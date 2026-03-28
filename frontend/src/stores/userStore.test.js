import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

const mocks = vi.hoisted(() => ({
  clearAccessTokenMock: vi.fn(),
  fetchContentBaselineMock: vi.fn(),
  fetchManagementProfileMock: vi.fn(),
  fetchStudentDashboardMock: vi.fn(),
  getAccessTokenMock: vi.fn(),
  loginMock: vi.fn(),
  logoutMock: vi.fn(),
  setAccessTokenMock: vi.fn(),
}))

vi.mock('../api/auth', () => ({
  fetchManagementProfile: mocks.fetchManagementProfileMock,
  login: mocks.loginMock,
  logout: mocks.logoutMock,
}))

vi.mock('../api/request', () => ({
  clearAccessToken: mocks.clearAccessTokenMock,
  getAccessToken: mocks.getAccessTokenMock,
  setAccessToken: mocks.setAccessTokenMock,
}))

vi.mock('../api/services/questionBank', () => ({
  fetchContentBaseline: mocks.fetchContentBaselineMock,
}))

vi.mock('../api/services/student', () => ({
  fetchStudentDashboard: mocks.fetchStudentDashboardMock,
}))

function createStorageMock() {
  const store = new Map()
  return {
    get length() {
      return store.size
    },
    clear() {
      store.clear()
    },
    getItem(key) {
      return store.has(key) ? store.get(key) : null
    },
    key(index) {
      return Array.from(store.keys())[index] || null
    },
    removeItem(key) {
      store.delete(key)
    },
    setItem(key, value) {
      store.set(String(key), String(value))
    },
  }
}

const SCIENCE_ENGINEERING_BASELINE = {
  examCategories: [
    {
      examCategoryCode: 'SCIENCE_ENGINEERING',
      examCategoryName: '理工类',
      sortNo: 1,
      jointExamGroups: [
        {
          jointExamGroupCode: 'SCIENCE_ENGINEERING_3',
          jointExamGroupName: '理工 3',
          subjects: [
            { subjectCode: 'POLITICS', subjectName: '政治', subjectType: 'PUBLIC' },
            { subjectCode: 'ENGLISH', subjectName: '英语', subjectType: 'PUBLIC' },
            { subjectCode: 'INFO_TECH_INTRO', subjectName: '信息技术概论', subjectType: 'PROFESSIONAL_1' },
            { subjectCode: 'ADVANCED_MATH_1', subjectName: '高等数学（一）', subjectType: 'PROFESSIONAL_2' },
          ],
        },
      ],
    },
  ],
}

async function loadUserStore() {
  return import('./userStore.js')
}

beforeEach(() => {
  vi.resetModules()
  Object.values(mocks).forEach((mockItem) => {
    mockItem.mockReset()
  })
  setActivePinia(createPinia())
  Object.defineProperty(globalThis, 'localStorage', {
    value: createStorageMock(),
    configurable: true,
    writable: true,
  })
  Object.defineProperty(globalThis, 'window', {
    value: {
      __QB_ASSIGNED_JOINT_GROUP__: '',
      __QB_ENTRY_TYPE__: 'student',
    },
    configurable: true,
    writable: true,
  })
  mocks.getAccessTokenMock.mockReturnValue('token-student')
})

describe('userStore student initialization', () => {
  it('falls back to baseline scoped subjects when the student dashboard is unavailable', async () => {
    mocks.fetchStudentDashboardMock.mockRejectedValue(new Error('dashboard unavailable'))
    mocks.fetchContentBaselineMock.mockResolvedValue(SCIENCE_ENGINEERING_BASELINE)

    localStorage.setItem('qbUserRole', 'student')
    localStorage.setItem('qbAssignedJointGroupCode', 'SCIENCE_ENGINEERING_3')

    const { useUserStore } = await loadUserStore()
    const store = useUserStore()

    await store.initialize({
      routePath: '/student/home',
      entryType: 'student',
      force: true,
    })

    expect(store.initialized).toBe(true)
    expect(store.isHydrated).toBe(true)
    expect(store.role).toBe('student')
    expect(store.examCategoryCode).toBe('SCIENCE_ENGINEERING')
    expect(store.jointExamGroupCode).toBe('SCIENCE_ENGINEERING_3')
    expect(
      store.availableExamCategories[0]?.jointExamGroups?.[0]?.subjects?.map((item) => item.subjectCode),
    ).toEqual(['POLITICS', 'ENGLISH', 'INFO_TECH_INTRO', 'ADVANCED_MATH_1'])
  })

  it('keeps the store unhydrated when neither dashboard nor baseline can recover the student context', async () => {
    mocks.fetchStudentDashboardMock.mockRejectedValue(new Error('dashboard unavailable'))
    mocks.fetchContentBaselineMock.mockRejectedValue(new Error('baseline unavailable'))
    mocks.fetchManagementProfileMock.mockRejectedValue(new Error('profile unavailable'))

    localStorage.setItem('qbUserRole', 'student')

    const { useUserStore } = await loadUserStore()
    const store = useUserStore()

    await store.initialize({
      routePath: '/student/home',
      entryType: 'student',
      force: true,
    })

    expect(store.initialized).toBe(false)
    expect(store.isHydrated).toBe(false)
  })

  it('hydrates onboarding completion state from student dashboard payload', async () => {
    mocks.fetchStudentDashboardMock.mockResolvedValue({
      data: {
        userId: 'student-001',
        examCategoryCode: 'SCIENCE_ENGINEERING',
        jointExamGroupCode: 'SCIENCE_ENGINEERING_3',
        availableExamCategories: SCIENCE_ENGINEERING_BASELINE.examCategories,
        onboarding: {
          completed: true,
        },
      },
    })

    localStorage.setItem('qbUserRole', 'student')

    const { useUserStore } = await loadUserStore()
    const store = useUserStore()

    await store.initialize({
      routePath: '/student/home',
      entryType: 'student',
      force: true,
    })

    expect(store.initialized).toBe(true)
    expect(store.isHydrated).toBe(true)
    expect(store.studentOnboardingCompleted).toBe(true)
  })
})

describe('userStore teacher post tags', () => {
  it('routes recruit-only teacher to student account entry path', async () => {
    const { useUserStore } = await loadUserStore()
    const store = useUserStore()

    store.setRole('teacher')
    store.setPermissions(['student:manage', 'analytics:view', 'message:send'])
    store.setPostTags(['recruit'])

    expect(store.homePath).toBe('/teacher/student-accounts')
    expect(store.teacherHomePath).toBe('/teacher/student-accounts')
  })

  it('hydrates teacher post tags from management profile and persists home path decision', async () => {
    mocks.fetchManagementProfileMock.mockResolvedValue({
      data: {
        userId: 'teacher-recruit-001',
        role: 'teacher',
        permissions: ['student:manage', 'analytics:view', 'message:send'],
        postTags: ['recruit'],
        assigned_joint_group_code: '',
      },
    })
    mocks.fetchContentBaselineMock.mockResolvedValue(SCIENCE_ENGINEERING_BASELINE)
    globalThis.window.__QB_ENTRY_TYPE__ = 'teacher'
    mocks.getAccessTokenMock.mockReturnValue('token-teacher')

    const { useUserStore } = await loadUserStore()
    const store = useUserStore()

    await store.initialize({
      routePath: '/teacher/home',
      entryType: 'teacher',
      force: true,
    })

    expect(store.isHydrated).toBe(true)
    expect(store.role).toBe('teacher')
    expect(store.postTags).toEqual(['recruit'])
    expect(store.homePath).toBe('/teacher/student-accounts')
    expect(localStorage.getItem('qbTeacherPostTags')).toBe(JSON.stringify(['recruit']))
  })
})
