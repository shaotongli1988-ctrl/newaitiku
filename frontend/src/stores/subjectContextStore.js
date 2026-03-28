// Observability note: store synchronization should preserve subject log/trace/metric context across route changes.
import { defineStore } from 'pinia'
import { fetchStudentDashboard } from '../api/services/student.js'
import { fetchContentBaseline } from '../api/services/questionBank.js'
import { useUserStore } from './userStore.js'
import { filterSubjectCodeOptions, normalizeContentBaseline } from '../utils/contentBaseline.js'
import {
  normalizeStudentSubjectOptions,
  resolveStudentSubjectCode,
} from '../utils/studentSubjectContext.js'

const SUBJECT_CODE_STORAGE_KEY = 'qbCurrentStudentSubjectCode'

function toText(value) {
  return String(value || '').trim()
}

function buildScopedSubjectOptionsFromBaseline(baselinePayload, userStore) {
  const normalizedBaseline = normalizeContentBaseline(baselinePayload || {})
  const currentScope = userStore?.currentScope || {}
  const examCategoryCode = toText(currentScope.examCategoryCode)
  const jointExamGroupCode = toText(currentScope.jointExamGroupCode)

  return filterSubjectCodeOptions(
    normalizedBaseline.subjectCodeOptions,
    examCategoryCode,
    jointExamGroupCode,
  ).map((item) => ({
    subjectCode: toText(item?.subjectCode),
    subjectId: toText(item?.subjectId || item?.subjectCode),
    subjectName: toText(item?.subjectName || item?.subjectCode),
    subjectType: toText(item?.subjectType),
  }))
}

export const useSubjectContextStore = defineStore('subjectContext', {
  state: () => ({
    initialized: false,
    loading: false,
    subjectOptions: [],
    currentSubjectCode: '',
  }),

  getters: {
    currentSubject(state) {
      return state.subjectOptions.find((item) => item.subjectCode === state.currentSubjectCode) || null
    },
    currentSubjectName() {
      return this.currentSubject?.subjectName || this.currentSubjectCode || ''
    },
    subjectMetaMap(state) {
      return Object.fromEntries(
        (Array.isArray(state.subjectOptions) ? state.subjectOptions : [])
          .map((item) => [item.subjectCode, item])
          .filter(([subjectCode]) => Boolean(subjectCode)),
      )
    },
  },

  actions: {
    bootstrapFromStorage() {
      this.currentSubjectCode = toText(localStorage.getItem(SUBJECT_CODE_STORAGE_KEY))
      this.initialized = true
    },

    persistState() {
      localStorage.setItem(SUBJECT_CODE_STORAGE_KEY, this.currentSubjectCode)
    },

    setCurrentSubjectCode(subjectCode, { persist = true } = {}) {
      const normalizedSubjectCode = toText(subjectCode)
      if (!normalizedSubjectCode) {
        return
      }
      const nextSubjectCode = this.subjectOptions.length
        ? resolveStudentSubjectCode(this.subjectOptions, normalizedSubjectCode, this.currentSubjectCode)
        : normalizedSubjectCode
      if (!nextSubjectCode) {
        return
      }
      this.currentSubjectCode = nextSubjectCode
      if (persist) {
        this.persistState()
      }
    },

    setSubjectOptions(subjectRows, preferredSubjectCode = '') {
      const normalizedOptions = normalizeStudentSubjectOptions(subjectRows)
      this.subjectOptions = normalizedOptions

      const preferredCode = toText(preferredSubjectCode)
      const nextSubjectCode = resolveStudentSubjectCode(
        normalizedOptions,
        this.currentSubjectCode,
        preferredCode,
      )

      if (nextSubjectCode) {
        this.currentSubjectCode = nextSubjectCode
        this.persistState()
      }
    },

    async loadSubjectOptionsFromBaseline() {
      const userStore = useUserStore()
      try {
        const baseline = await fetchContentBaseline()
        return buildScopedSubjectOptionsFromBaseline(baseline, userStore)
      } catch (_error) {
        return []
      }
    },

    async ensureStudentSubjectContext({ force = false } = {}) {
      if (this.loading) {
        return
      }
      if (!this.initialized) {
        this.bootstrapFromStorage()
      }
      if (!force && this.subjectOptions.length) {
        return
      }

      this.loading = true
      try {
        const dashboard = await fetchStudentDashboard()
        const dashboardRows = normalizeStudentSubjectOptions(dashboard)
        if (dashboardRows.length) {
          this.setSubjectOptions(dashboardRows, this.currentSubjectCode)
          return
        }

        const fallbackRows = await this.loadSubjectOptionsFromBaseline()
        this.setSubjectOptions(fallbackRows, this.currentSubjectCode)
      } catch (_error) {
        const fallbackRows = await this.loadSubjectOptionsFromBaseline()
        this.setSubjectOptions(fallbackRows, this.currentSubjectCode)
      } finally {
        this.loading = false
      }
    },
  },
})
