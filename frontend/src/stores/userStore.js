import { defineStore } from 'pinia'
import { fetchManagementProfile, login as login_by_password_api, logout as logout_api } from '../api/auth'
import { clearAccessToken, getAccessToken, setAccessToken } from '../api/request'
import { fetchContentBaseline } from '../api/services/questionBank'
import { fetchStudentDashboard } from '../api/services/student'

const ROLE_STORAGE_KEY = 'qbUserRole'
const USER_ID_STORAGE_KEY = 'qbUserId'
const PERMISSIONS_STORAGE_KEY = 'qbPermissionKeys'
const EXAM_CATEGORY_STORAGE_KEY = 'qbExamCategoryCode'
const JOINT_EXAM_GROUP_STORAGE_KEY = 'qbJointExamGroupCode'
const ASSIGNED_JOINT_GROUP_STORAGE_KEY = 'qbAssignedJointGroupCode'
const ACTIVE_SCOPE_STORAGE_KEY = 'qbActiveScope'
const EXAM_CATEGORIES_STORAGE_KEY = 'qbExamCategoryOptions'

const ROLE_HOME_MAP = {
  super_admin: '/admin/home',
  teacher: '/teacher/home',
  student: '/student/home',
}

const DEFAULT_EXAM_CATEGORIES = [
  {
    examCategoryCode: 'SCIENCE_ENGINEERING',
    examCategoryName: '理工类',
    jointExamGroups: [
      {
        jointExamGroupCode: 'SCIENCE_ENGINEERING_1',
        jointExamGroupName: '理工 1',
      },
      {
        jointExamGroupCode: 'SCIENCE_ENGINEERING_2',
        jointExamGroupName: '理工 2',
      },
    ],
  },
  {
    examCategoryCode: 'MANAGEMENT',
    examCategoryName: '管理学类',
    jointExamGroups: [
      {
        jointExamGroupCode: 'MANAGEMENT_1',
        jointExamGroupName: '管理学 1',
      },
      {
        jointExamGroupCode: 'MANAGEMENT_2',
        jointExamGroupName: '管理学 2',
      },
    ],
  },
  {
    examCategoryCode: 'LITERATURE',
    examCategoryName: '文学类',
    jointExamGroups: [
      {
        jointExamGroupCode: 'LITERATURE_1',
        jointExamGroupName: '文学 1',
      },
      {
        jointExamGroupCode: 'LITERATURE_2',
        jointExamGroupName: '文学 2',
      },
    ],
  },
]

function normalizeRole(role) {
  const normalizedRole = String(role || '').trim()
  if (normalizedRole === 'super_admin' || normalizedRole === 'teacher' || normalizedRole === 'student') {
    return normalizedRole
  }
  return null
}

function defaultUserIdByRole(role) {
  if (role === 'super_admin') {
    return 'admin-001'
  }
  if (role === 'teacher') {
    return 'teacher-001'
  }
  if (role === 'student') {
    return 'student-001'
  }
  return ''
}

function normalizeUserId(userId, role) {
  const normalizedUserId = String(userId || '').trim()
  if (normalizedUserId) {
    return normalizedUserId
  }
  return defaultUserIdByRole(role)
}

function normalizePermissions(permissions) {
  if (!Array.isArray(permissions)) {
    return []
  }
  const dedupedPermissions = []
  const seen = new Set()
  permissions.forEach((permissionItem) => {
    const permissionKey = String(permissionItem || '').trim()
    if (!permissionKey || seen.has(permissionKey)) {
      return
    }
    seen.add(permissionKey)
    dedupedPermissions.push(permissionKey)
  })
  return dedupedPermissions
}

function normalizeSubjectList(subjects, { examCategoryCode = '', jointExamGroupCode = '' } = {}) {
  if (!Array.isArray(subjects)) {
    return []
  }

  const normalizedExamCategoryCode = String(examCategoryCode || '').trim()
  const normalizedJointExamGroupCode = String(jointExamGroupCode || '').trim()
  const seen = new Set()

  return subjects
    .map((subjectItem) => {
      const subjectCode = String(subjectItem?.subjectCode || '').trim()
      if (!subjectCode || seen.has(subjectCode)) {
        return null
      }
      seen.add(subjectCode)
      return {
        subjectCode,
        subjectName: String(subjectItem?.subjectName || subjectCode).trim(),
        subjectType: String(subjectItem?.subjectType || '').trim(),
        examCategoryCode: String(subjectItem?.examCategoryCode || normalizedExamCategoryCode).trim(),
        jointExamGroupCode: String(subjectItem?.jointExamGroupCode || normalizedJointExamGroupCode).trim(),
      }
    })
    .filter(Boolean)
}

function normalizeExamCategoryList(examCategories) {
  if (!Array.isArray(examCategories)) {
    return []
  }

  return examCategories
    .map((examCategoryItem) => {
      const examCategoryCode = String(examCategoryItem?.examCategoryCode || '').trim()
      if (!examCategoryCode) {
        return null
      }

      const jointExamGroups = Array.isArray(examCategoryItem?.jointExamGroups)
        ? examCategoryItem.jointExamGroups
            .map((jointExamGroupItem) => {
              const jointExamGroupCode = String(jointExamGroupItem?.jointExamGroupCode || '').trim()
              if (!jointExamGroupCode) {
                return null
              }
              return {
                jointExamGroupCode,
                jointExamGroupName: String(
                  jointExamGroupItem?.jointExamGroupName || jointExamGroupCode,
                ),
                examCategoryCode,
                subjects: normalizeSubjectList(jointExamGroupItem?.subjects, {
                  examCategoryCode,
                  jointExamGroupCode,
                }),
              }
            })
            .filter(Boolean)
        : []

      return {
        examCategoryCode,
        examCategoryName: String(examCategoryItem?.examCategoryName || examCategoryCode),
        sortNo: Number(examCategoryItem?.sortNo || 0),
        jointExamGroups,
      }
    })
    .filter(Boolean)
}

function deriveJointExamGroups(availableExamCategories, examCategoryCode) {
  const selectedExamCategoryCode = String(examCategoryCode || '').trim()
  if (!selectedExamCategoryCode) {
    return []
  }

  const matchedExamCategory = availableExamCategories.find(
    (examCategoryItem) => examCategoryItem.examCategoryCode === selectedExamCategoryCode,
  )

  return matchedExamCategory ? matchedExamCategory.jointExamGroups.slice() : []
}

function deriveExamCategoryCodeByJointGroup(availableExamCategories, jointExamGroupCode) {
  const normalizedJointExamGroupCode = String(jointExamGroupCode || '').trim()
  if (!normalizedJointExamGroupCode) {
    return ''
  }
  const matchedCategory = (Array.isArray(availableExamCategories) ? availableExamCategories : []).find(
    (examCategoryItem) =>
      Array.isArray(examCategoryItem?.jointExamGroups)
      && examCategoryItem.jointExamGroups.some(
        (jointExamGroupItem) =>
          String(jointExamGroupItem?.jointExamGroupCode || '').trim() === normalizedJointExamGroupCode,
      ),
  )
  return String(matchedCategory?.examCategoryCode || '').trim()
}

function resolveRoleFromPath(path) {
  const normalizedPath = String(path || '').trim()
  if (normalizedPath.startsWith('/admin')) {
    return 'super_admin'
  }
  if (normalizedPath.startsWith('/teacher')) {
    return 'teacher'
  }
  if (normalizedPath.startsWith('/student')) {
    return 'student'
  }
  return ''
}

function resolveEntryTypeFromWindow() {
  const normalized = String(window.__QB_ENTRY_TYPE__ || '').trim()
  if (normalized === 'student' || normalized === 'teacher') {
    return normalized
  }
  return ''
}

function unwrapResponseData(response) {
  if (response && typeof response === 'object' && 'data' in response) {
    return response.data || {}
  }
  return response || {}
}

function normalizeOnboardingCompleted(completed) {
  if (completed === true) {
    return true
  }
  if (completed === false) {
    return false
  }
  return null
}

function clearQuestionBankStorage() {
  const keysToRemove = []
  for (let index = 0; index < localStorage.length; index += 1) {
    const storageKey = String(localStorage.key(index) || '')
    if (!storageKey) {
      continue
    }
    if (storageKey.startsWith('qb')) {
      keysToRemove.push(storageKey)
    }
  }
  keysToRemove.forEach((storageKey) => {
    localStorage.removeItem(storageKey)
  })
}

function syncAssignedJointGroupToWindow(value) {
  window.__QB_ASSIGNED_JOINT_GROUP__ = String(value || '').trim()
}

export const useUserStore = defineStore('user', {
  state: () => ({
    initialized: false,
    isHydrated: false,
    initializingPromise: null,
    role: null,
    userId: '',
    permissions: [],
    examCategoryCode: '',
    jointExamGroupCode: '',
    assigned_joint_group_code: '',
    activeScope: '',
    availableExamCategories: normalizeExamCategoryList(DEFAULT_EXAM_CATEGORIES),
    availableJointExamGroups: [],
    studentOnboardingCompleted: null,
  }),

  getters: {
    hasPermission: (state) => (permissionKey) => {
      const normalizedPermissionKey = String(permissionKey || '').trim()
      return normalizedPermissionKey ? state.permissions.includes(normalizedPermissionKey) : false
    },

    homePath: (state) => {
      if (!state.role) {
        return '/login'
      }
      return ROLE_HOME_MAP[state.role] || '/login'
    },
    currentScope: (state) => {
      const normalizedRole = normalizeRole(state.role) || ''
      const examCategoryCode = String(state.examCategoryCode || '').trim()
      const assignedJointGroupCode = String(state.assigned_joint_group_code || '').trim()
      const selectedJointGroupCode = String(state.jointExamGroupCode || '').trim()
      const activeScope = String(state.activeScope || '').trim()
      const effectiveJointGroupCode = normalizedRole === 'student'
        ? (activeScope || assignedJointGroupCode || selectedJointGroupCode)
        : (selectedJointGroupCode || assignedJointGroupCode || activeScope)
      return {
        role: normalizedRole,
        examCategoryCode,
        exam_category_code: examCategoryCode,
        jointExamGroupCode: effectiveJointGroupCode,
        joint_exam_group_code: effectiveJointGroupCode,
        assignedJointGroupCode,
        assigned_joint_group_code: assignedJointGroupCode,
        activeScope: effectiveJointGroupCode,
        active_scope: effectiveJointGroupCode,
        policyVersion: 'HB_ZSB_2026',
        policy_version: 'HB_ZSB_2026',
      }
    },
    assignedJointGroupCode: (state) => state.assigned_joint_group_code,
  },

  actions: {
    bootstrapFromStorage() {
      this.role = normalizeRole(localStorage.getItem(ROLE_STORAGE_KEY) || this.role)
      this.userId = normalizeUserId(localStorage.getItem(USER_ID_STORAGE_KEY), this.role)

      const rawPermissions = localStorage.getItem(PERMISSIONS_STORAGE_KEY)
      try {
        this.permissions = normalizePermissions(rawPermissions ? JSON.parse(rawPermissions) : [])
      } catch (error) {
        this.permissions = []
      }

      this.examCategoryCode = String(localStorage.getItem(EXAM_CATEGORY_STORAGE_KEY) || '').trim()
      this.jointExamGroupCode = String(localStorage.getItem(JOINT_EXAM_GROUP_STORAGE_KEY) || '').trim()
      this.assigned_joint_group_code = String(localStorage.getItem(ASSIGNED_JOINT_GROUP_STORAGE_KEY) || '').trim()
      syncAssignedJointGroupToWindow(this.assigned_joint_group_code)
      this.activeScope = String(localStorage.getItem(ACTIVE_SCOPE_STORAGE_KEY) || '').trim()

      const rawExamCategoryOptions = localStorage.getItem(EXAM_CATEGORIES_STORAGE_KEY)
      if (rawExamCategoryOptions) {
        try {
          const parsedExamCategoryOptions = JSON.parse(rawExamCategoryOptions)
          const normalizedExamCategoryOptions = normalizeExamCategoryList(parsedExamCategoryOptions)
          if (normalizedExamCategoryOptions.length) {
            this.availableExamCategories = normalizedExamCategoryOptions
          }
        } catch (error) {
          // Ignore invalid cache and keep current options.
        }
      }

      this.availableJointExamGroups = deriveJointExamGroups(
        this.availableExamCategories,
        this.examCategoryCode,
      )

      if (
        this.jointExamGroupCode &&
        !this.availableJointExamGroups.some(
          (jointExamGroupItem) => jointExamGroupItem.jointExamGroupCode === this.jointExamGroupCode,
        )
      ) {
        this.jointExamGroupCode = ''
      }
      this.lockStudentAssignedScope()
    },

    persistState() {
      localStorage.setItem(ROLE_STORAGE_KEY, this.role)
      localStorage.setItem(USER_ID_STORAGE_KEY, this.userId)
      localStorage.setItem(PERMISSIONS_STORAGE_KEY, JSON.stringify(this.permissions))
      localStorage.setItem(EXAM_CATEGORY_STORAGE_KEY, this.examCategoryCode)
      localStorage.setItem(JOINT_EXAM_GROUP_STORAGE_KEY, this.jointExamGroupCode)
      localStorage.setItem(ASSIGNED_JOINT_GROUP_STORAGE_KEY, this.assigned_joint_group_code)
      syncAssignedJointGroupToWindow(this.assigned_joint_group_code)
      localStorage.setItem(ACTIVE_SCOPE_STORAGE_KEY, this.activeScope)
      localStorage.setItem(EXAM_CATEGORIES_STORAGE_KEY, JSON.stringify(this.availableExamCategories))
    },

    setRole(role) {
      this.role = normalizeRole(role)
      this.userId = normalizeUserId(this.userId, this.role)
      if (this.role !== 'student') {
        this.studentOnboardingCompleted = null
      }
    },

    setUserId(userId) {
      this.userId = normalizeUserId(userId, this.role)
    },

    setPermissions(permissions) {
      this.permissions = normalizePermissions(permissions)
    },

    setStudentOnboardingCompleted(completed) {
      this.studentOnboardingCompleted = normalizeOnboardingCompleted(completed)
    },

    setAssignedJointGroupCode(jointExamGroupCode) {
      this.assigned_joint_group_code = String(jointExamGroupCode || '').trim()
      syncAssignedJointGroupToWindow(this.assigned_joint_group_code)
      this.lockStudentAssignedScope()
    },

    syncActiveScope() {
      const normalizedRole = normalizeRole(this.role) || ''
      const assignedJointGroupCode = String(this.assigned_joint_group_code || '').trim()
      const selectedJointExamGroupCode = String(this.jointExamGroupCode || '').trim()
      if (normalizedRole === 'student' && assignedJointGroupCode) {
        this.activeScope = assignedJointGroupCode
        return
      }
      this.activeScope = selectedJointExamGroupCode || assignedJointGroupCode || ''
    },

    lockStudentAssignedScope() {
      const normalizedRole = normalizeRole(this.role) || ''
      const assignedJointGroupCode = String(this.assigned_joint_group_code || '').trim()
      if (normalizedRole !== 'student' || !assignedJointGroupCode) {
        this.syncActiveScope()
        return
      }

      const scopedExamCategoryCode = deriveExamCategoryCodeByJointGroup(
        this.availableExamCategories,
        assignedJointGroupCode,
      )
      if (scopedExamCategoryCode) {
        this.examCategoryCode = scopedExamCategoryCode
      }
      this.availableJointExamGroups = deriveJointExamGroups(
        this.availableExamCategories,
        this.examCategoryCode,
      )
      this.jointExamGroupCode = assignedJointGroupCode
      this.activeScope = assignedJointGroupCode
    },

    setExamCategoryOptions(examCategories, preferredExamCategoryCode = '') {
      const normalizedExamCategories = normalizeExamCategoryList(examCategories)
      this.availableExamCategories = normalizedExamCategories.length
        ? normalizedExamCategories
        : normalizeExamCategoryList(DEFAULT_EXAM_CATEGORIES)

      const preferredCode = String(preferredExamCategoryCode || '').trim()
      const hasPreferredCode = this.availableExamCategories.some(
        (examCategoryItem) => examCategoryItem.examCategoryCode === preferredCode,
      )
      const canKeepCurrentCode = this.availableExamCategories.some(
        (examCategoryItem) => examCategoryItem.examCategoryCode === this.examCategoryCode,
      )

      if (hasPreferredCode) {
        this.examCategoryCode = preferredCode
      } else if (!canKeepCurrentCode) {
        this.examCategoryCode = this.availableExamCategories[0]?.examCategoryCode || ''
      }

      this.availableJointExamGroups = deriveJointExamGroups(
        this.availableExamCategories,
        this.examCategoryCode,
      )

      const hasCurrentJointExamGroup = this.availableJointExamGroups.some(
        (jointExamGroupItem) => jointExamGroupItem.jointExamGroupCode === this.jointExamGroupCode,
      )
      if (!hasCurrentJointExamGroup) {
        this.jointExamGroupCode = this.availableJointExamGroups[0]?.jointExamGroupCode || ''
      }
      this.lockStudentAssignedScope()
    },

    setStudentScope({ examCategoryCode = '', jointExamGroupCode = '' } = {}) {
      const normalizedExamCategoryCode = String(examCategoryCode || '').trim()
      const normalizedJointExamGroupCode = String(jointExamGroupCode || '').trim()
      if (normalizeRole(this.role) === 'student' && this.assigned_joint_group_code) {
        this.lockStudentAssignedScope()
        return
      }

      if (normalizedExamCategoryCode) {
        this.examCategoryCode = normalizedExamCategoryCode
      }

      this.availableJointExamGroups = deriveJointExamGroups(
        this.availableExamCategories,
        this.examCategoryCode,
      )

      const hasRequestedJointExamGroup = this.availableJointExamGroups.some(
        (jointExamGroupItem) =>
          jointExamGroupItem.jointExamGroupCode === normalizedJointExamGroupCode,
      )

      if (hasRequestedJointExamGroup) {
        this.jointExamGroupCode = normalizedJointExamGroupCode
      } else {
        this.jointExamGroupCode = this.availableJointExamGroups[0]?.jointExamGroupCode || ''
      }
      this.syncActiveScope()
    },

    setExamCategoryCode(examCategoryCode) {
      if (normalizeRole(this.role) === 'student' && this.assigned_joint_group_code) {
        this.lockStudentAssignedScope()
        return
      }
      const nextExamCategoryCode = String(examCategoryCode || '').trim()
      this.examCategoryCode = nextExamCategoryCode
      this.availableJointExamGroups = deriveJointExamGroups(
        this.availableExamCategories,
        nextExamCategoryCode,
      )

      const jointExamGroupStillValid = this.availableJointExamGroups.some(
        (jointExamGroupItem) => jointExamGroupItem.jointExamGroupCode === this.jointExamGroupCode,
      )
      if (!jointExamGroupStillValid) {
        this.jointExamGroupCode = this.availableJointExamGroups[0]?.jointExamGroupCode || ''
      }
      this.syncActiveScope()
    },

    setJointExamGroupCode(jointExamGroupCode) {
      if (normalizeRole(this.role) === 'student' && this.assigned_joint_group_code) {
        this.lockStudentAssignedScope()
        return
      }
      const nextJointExamGroupCode = String(jointExamGroupCode || '').trim()
      const canSelect = this.availableJointExamGroups.some(
        (jointExamGroupItem) => jointExamGroupItem.jointExamGroupCode === nextJointExamGroupCode,
      )
      this.jointExamGroupCode = canSelect ? nextJointExamGroupCode : ''
      this.syncActiveScope()
    },

    ensureAccess({ role = '', allowedRoles = [], requiredPermissions = [] } = {}) {
      if (this.role === 'super_admin') {
        return { allowed: true, reason: '' }
      }

      const normalizedRole = String(role || '').trim()
      const normalizedAllowedRoles = (Array.isArray(allowedRoles) ? allowedRoles : [])
        .map((roleItem) => normalizeRole(roleItem))
        .filter(Boolean)

      if (normalizedRole && !normalizedAllowedRoles.includes(normalizedRole)) {
        normalizedAllowedRoles.push(normalizedRole)
      }

      if (normalizedAllowedRoles.length && !normalizedAllowedRoles.includes(this.role)) {
        return { allowed: false, reason: 'role' }
      }

      const normalizedRequiredPermissions = normalizePermissions(requiredPermissions)
      if (
        normalizedRequiredPermissions.length &&
        !normalizedRequiredPermissions.every((permissionKey) => this.hasPermission(permissionKey))
      ) {
        return { allowed: false, reason: 'permission' }
      }

      return { allowed: true, reason: '' }
    },

    async tryInitializeFromManagementProfile() {
      try {
        const profileResponse = await fetchManagementProfile()
        const profileData = unwrapResponseData(profileResponse)

        this.setRole(profileData.role)
        this.setUserId(profileData.userId)
        this.setPermissions(profileData.permissions)
        this.setAssignedJointGroupCode(
          profileData.assigned_joint_group_code
          || profileData.assignedJointGroupCode
          || profileData.jointExamGroupCode
          || '',
        )

        if (this.role === 'student') {
          return this.tryInitializeFromStudentDashboard()
        }

        // 管理端也尝试拉取筛选大类，失败则继续使用本地默认值。
        try {
          const baselineResponse = await fetchContentBaseline()
          const baselineData = unwrapResponseData(baselineResponse)
          this.setExamCategoryOptions(
            baselineData.examCategories || baselineData.availableExamCategories || [],
            this.examCategoryCode,
          )
        } catch (error) {
          this.setExamCategoryOptions(this.availableExamCategories, this.examCategoryCode)
        }
        if (this.role !== 'super_admin' && this.assigned_joint_group_code) {
          const scopedExamCategoryCode = deriveExamCategoryCodeByJointGroup(
            this.availableExamCategories,
            this.assigned_joint_group_code,
          )
          this.examCategoryCode = scopedExamCategoryCode
          this.availableJointExamGroups = deriveJointExamGroups(
            this.availableExamCategories,
            this.examCategoryCode,
          )
          this.jointExamGroupCode = this.assigned_joint_group_code
        } else {
          this.examCategoryCode = ''
          this.jointExamGroupCode = ''
          this.availableJointExamGroups = []
        }
        this.syncActiveScope()
        return true
      } catch (error) {
        return false
      }
    },

    async tryInitializeFromStudentDashboard() {
      const currentRole = normalizeRole(this.role)
      if (currentRole && currentRole !== 'student') {
        return false
      }
      try {
        const dashboardResponse = await fetchStudentDashboard()
        const dashboardData = unwrapResponseData(dashboardResponse)
        const preferredExamCategoryCode = String(dashboardData.examCategoryCode || this.examCategoryCode || '').trim()
        const preferredJointExamGroupCode = String(
          dashboardData.jointExamGroupCode || this.assigned_joint_group_code || this.jointExamGroupCode || '',
        ).trim()
        const dashboardExamCategories = Array.isArray(dashboardData.availableExamCategories)
          ? dashboardData.availableExamCategories
          : []

        this.setRole('student')
        this.setUserId(dashboardData.userId || this.userId)
        this.setPermissions([])
        this.setStudentOnboardingCompleted(
          normalizeOnboardingCompleted(dashboardData?.onboarding?.completed),
        )

        if (dashboardExamCategories.length) {
          this.setExamCategoryOptions(dashboardExamCategories, preferredExamCategoryCode)
        } else {
          const initializedFromBaseline = await this.tryInitializeStudentContextFromBaseline({
            preferredExamCategoryCode,
            preferredJointExamGroupCode,
          })
          if (!initializedFromBaseline) {
            this.setExamCategoryOptions(this.availableExamCategories, preferredExamCategoryCode)
          }
        }

        this.setAssignedJointGroupCode(preferredJointExamGroupCode)
        this.setStudentScope({
          examCategoryCode: preferredExamCategoryCode || this.examCategoryCode,
          jointExamGroupCode: preferredJointExamGroupCode,
        })
        this.lockStudentAssignedScope()
        return true
      } catch (error) {
        return this.tryInitializeStudentContextFromBaseline({
          preferredExamCategoryCode: this.examCategoryCode,
          preferredJointExamGroupCode: this.assigned_joint_group_code || this.jointExamGroupCode,
        })
      }
    },

    async tryInitializeStudentContextFromBaseline({
      preferredExamCategoryCode = '',
      preferredJointExamGroupCode = '',
    } = {}) {
      try {
        const baselinePayload = await fetchContentBaseline()
        const baselineData = unwrapResponseData(baselinePayload)
        const baselineExamCategories = baselineData.examCategories || baselineData.availableExamCategories || []
        const normalizedBaselineCategories = normalizeExamCategoryList(baselineExamCategories)
        if (!normalizedBaselineCategories.length) {
          return false
        }

        const resolvedJointExamGroupCode = String(
          preferredJointExamGroupCode || this.assigned_joint_group_code || this.jointExamGroupCode || '',
        ).trim()
        const resolvedExamCategoryCode = String(
          preferredExamCategoryCode
          || deriveExamCategoryCodeByJointGroup(normalizedBaselineCategories, resolvedJointExamGroupCode)
          || this.examCategoryCode
          || normalizedBaselineCategories[0]?.examCategoryCode
          || '',
        ).trim()

        this.setRole('student')
        this.setPermissions([])
        this.setStudentOnboardingCompleted(null)
        this.setExamCategoryOptions(normalizedBaselineCategories, resolvedExamCategoryCode)
        this.setAssignedJointGroupCode(resolvedJointExamGroupCode)
        this.setStudentScope({
          examCategoryCode: resolvedExamCategoryCode,
          jointExamGroupCode: resolvedJointExamGroupCode,
        })
        this.lockStudentAssignedScope()
        return true
      } catch (error) {
        return false
      }
    },

    async initialize({ routePath = '/', entryType = '', force = false } = {}) {
      if (this.initialized && !force) {
        return
      }

      if (this.initializingPromise) {
        await this.initializingPromise
        return
      }

      this.isHydrated = false
      this.initializingPromise = (async () => {
        this.bootstrapFromStorage()
        const hasToken = Boolean(String(getAccessToken() || '').trim())
        if (!hasToken && String(routePath || '').trim().startsWith('/login')) {
          this.isHydrated = true
          this.initialized = true
          return
        }

        const pathRole = resolveRoleFromPath(routePath)
        const currentEntryType = String(entryType || '').trim() || resolveEntryTypeFromWindow()
        const preferStudentContext = currentEntryType === 'student' || pathRole === 'student'
        let initializedByStudentContext = false
        let initializedByManagementProfile = false

        if (preferStudentContext) {
          initializedByStudentContext = await this.tryInitializeFromStudentDashboard()
          if (!initializedByStudentContext) {
            initializedByManagementProfile = await this.tryInitializeFromManagementProfile()
          }
        } else {
          initializedByManagementProfile = await this.tryInitializeFromManagementProfile()
        }

        if (this.role === 'student' && !initializedByStudentContext) {
          initializedByStudentContext = await this.tryInitializeFromStudentDashboard()
        } else if (!initializedByManagementProfile && preferStudentContext) {
          initializedByStudentContext = await this.tryInitializeFromStudentDashboard()
        }

        if (this.role === 'student') {
          this.lockStudentAssignedScope()
        } else {
          this.syncActiveScope()
        }

        const initializedSuccessfully = Boolean(initializedByStudentContext || initializedByManagementProfile)
        this.persistState()
        this.isHydrated = initializedSuccessfully
        this.initialized = initializedSuccessfully
      })()

      try {
        await this.initializingPromise
      } finally {
        this.initializingPromise = null
      }
    },

    async login({ phone = '', password = '', routePath = '' } = {}) {
      const normalizedPhone = String(phone || '').trim()
      const normalizedPassword = String(password || '').trim()
      const normalizedRoutePath = String(routePath || '').trim()
      if (!normalizedPhone) {
        throw new Error('phone is required')
      }
      if (!normalizedPassword) {
        throw new Error('password is required')
      }

      const loginResponse = await login_by_password_api({
        phone: normalizedPhone,
        password: normalizedPassword,
      })
      const loginData = unwrapResponseData(loginResponse)
      const accessToken = String(loginData.accessToken || '').trim()
      if (!accessToken) {
        throw new Error('登录失败：服务端未返回 accessToken')
      }

      setAccessToken(accessToken)
      this.setRole(loginData.role)
      this.setUserId(loginData.userId)
      this.setPermissions([])
      this.setAssignedJointGroupCode(
        loginData.assigned_joint_group_code
        || loginData.assignedJointGroupCode
        || '',
      )
      localStorage.setItem(ROLE_STORAGE_KEY, String(this.role || ''))
      localStorage.setItem(USER_ID_STORAGE_KEY, String(this.userId || ''))
      localStorage.setItem(ASSIGNED_JOINT_GROUP_STORAGE_KEY, String(this.assigned_joint_group_code || ''))
      syncAssignedJointGroupToWindow(this.assigned_joint_group_code)
      this.initialized = false
      this.isHydrated = false
      await this.initialize({ routePath: normalizedRoutePath || this.homePath, force: true })
      this.persistState()
      return {
        role: this.role,
        userId: this.userId,
        homePath: this.homePath,
      }
    },

    async logout() {
      try {
        await logout_api()
      } catch (error) {
        // Ignore backend logout failure and always clear local state.
      }
      clearAccessToken()
      clearQuestionBankStorage()
      this.permissions = []
      this.setRole(null)
      this.setUserId('')
      this.setAssignedJointGroupCode('')
      this.activeScope = ''
      this.setStudentOnboardingCompleted(null)
      this.setExamCategoryOptions(DEFAULT_EXAM_CATEGORIES, '')
      this.setStudentScope({
        examCategoryCode: this.availableExamCategories[0]?.examCategoryCode || '',
        jointExamGroupCode: this.availableExamCategories[0]?.jointExamGroups?.[0]?.jointExamGroupCode || '',
      })
      this.initialized = false
      this.isHydrated = false
    },
  },
})
