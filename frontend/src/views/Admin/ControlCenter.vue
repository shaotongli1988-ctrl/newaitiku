<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from '@/ui/feedback'
import { usePermission } from '../../composables/usePermission.js'
import { useUserStore } from '../../stores/userStore.js'
import { buildContentLabelMaps, resolveContentLabel } from '../../utils/contentBaseline.js'
import {
  exportManagedStudentsDirectory,
  fetchAdminConsoleData,
  fetchManagedUsersPage,
  importManagedStudents,
  saveManagedUserRecord,
  saveSystemSettings,
} from '../../api/services/questionBank'

const userStore = useUserStore()
const { hasPermission } = usePermission(userStore)
const summaryKeyOrder = ['studentCount', 'teacherCount', 'disabledCount', 'messageCount', 'templateCount']
const summaryLabelMap = {
  studentCount: '学生人数',
  teacherCount: '教师人数',
  disabledCount: '停用账号',
  messageCount: '消息总数',
  templateCount: '模板总数',
}
const roleLabelMap = {
  student: '学生',
  teacher: '教师',
  super_admin: '总管理员',
}
const permissionOptionsByRole = {
  super_admin: ['question:manage', 'paper:manage', 'analytics:view', 'student:manage', 'settings:manage', 'message:send'],
  teacher: ['question:manage', 'paper:manage', 'analytics:view', 'student:manage', 'message:send'],
  student: [],
}
const teacherPostTagOptions = [
  { label: '教学岗', value: 'teach' },
  { label: '招生岗', value: 'recruit' },
]
const teacherPermissionTemplateByPostTag = {
  recruit: ['student:manage', 'analytics:view', 'message:send'],
  teach: ['question:manage', 'paper:manage', 'analytics:view', 'message:send'],
}
const teacherPostTagLabelMap = {
  recruit: '招生岗',
  teach: '教学岗',
}

const DEFAULT_MOCK_EXAM_RULE_PROFILES = {
  POLITICS: {
    durationMinutes: 90,
    typeRules: [
      { type: 'single_choice', count: 20, questionScore: 2 },
      { type: 'multiple_choice', count: 5, questionScore: 4 },
      { type: 'judge', count: 10, questionScore: 2 },
      { type: 'subjective', count: 2, questionScore: 10 },
    ],
    difficultyRatio: { easy: 0.3, medium: 0.5, hard: 0.2 },
  },
  ENGLISH: {
    durationMinutes: 90,
    typeRules: [
      { type: 'single_choice', count: 25, questionScore: 2 },
      { type: 'judge', count: 10, questionScore: 1 },
      { type: 'subjective', count: 4, questionScore: 10 },
    ],
    difficultyRatio: { easy: 0.25, medium: 0.55, hard: 0.2 },
  },
  __DEFAULT_150__: {
    durationMinutes: 120,
    typeRules: [
      { type: 'single_choice', count: 20, questionScore: 2 },
      { type: 'multiple_choice', count: 10, questionScore: 4 },
      { type: 'judge', count: 10, questionScore: 2 },
      { type: 'subjective', count: 5, questionScore: 10 },
    ],
    difficultyRatio: { easy: 0.25, medium: 0.5, hard: 0.25 },
  },
  __DEFAULT_100__: {
    durationMinutes: 90,
    typeRules: [
      { type: 'single_choice', count: 20, questionScore: 2 },
      { type: 'multiple_choice', count: 5, questionScore: 4 },
      { type: 'judge', count: 10, questionScore: 2 },
      { type: 'subjective', count: 2, questionScore: 10 },
    ],
    difficultyRatio: { easy: 0.3, medium: 0.5, hard: 0.2 },
  },
}
const DEFAULT_MOCK_EXAM_PROFILE_LABELS = {
  POLITICS: '政治预设',
  ENGLISH: '英语预设',
  __DEFAULT_150__: '默认 150 分档',
  __DEFAULT_100__: '默认 100 分档',
}

const mockExamRuleCopyForm = reactive({
  sourceKey: '',
  targetKey: '',
})

function tryParseMockExamRuleProfiles(text) {
  try {
    const parsed = JSON.parse(String(text || '{}'))
    if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
      return parsed
    }
  } catch (error) {
    // fall through
  }
  return null
}

function stringifyMockExamRuleProfiles(profiles) {
  return JSON.stringify(profiles || {}, null, 2)
}

function resolveMockExamRuleProfileValue(key, parsedProfiles = {}) {
  if (!key) {
    return null
  }
  if (parsedProfiles && typeof parsedProfiles === 'object' && key in parsedProfiles) {
    return parsedProfiles[key]
  }
  if (key in DEFAULT_MOCK_EXAM_RULE_PROFILES) {
    return DEFAULT_MOCK_EXAM_RULE_PROFILES[key]
  }
  return null
}

function deepCloneProfile(value) {
  if (value && typeof value === 'object') {
    return JSON.parse(JSON.stringify(value))
  }
  return value
}

function fillDefaultMockExamRuleProfiles() {
  settingsForm.mockExamRuleProfilesText = stringifyMockExamRuleProfiles(DEFAULT_MOCK_EXAM_RULE_PROFILES)
  ElMessage.success('已填充默认模考规则模板。')
}

function handleCopyMockExamRuleProfile() {
  const sourceKey = String(mockExamRuleCopyForm.sourceKey || '').trim()
  const targetKey = String(mockExamRuleCopyForm.targetKey || '').trim()
  if (!sourceKey) {
    ElMessage.warning('请选择要复制的源配置。')
    return
  }
  if (!targetKey) {
    ElMessage.warning('请输入目标科目编码或默认档标签。')
    return
  }
  const parsed = tryParseMockExamRuleProfiles(settingsForm.mockExamRuleProfilesText)
  if (parsed === null) {
    ElMessage.warning('当前模考配置不是合法 JSON，请先修复再复制。')
    return
  }
  const sourceProfile = resolveMockExamRuleProfileValue(sourceKey, parsed)
  if (!sourceProfile || typeof sourceProfile !== 'object') {
    ElMessage.warning('未能找到选中的源配置，请检查源配置键。')
    return
  }
  const nextProfiles = {
    ...parsed,
    [targetKey]: deepCloneProfile(sourceProfile),
  }
  settingsForm.mockExamRuleProfilesText = stringifyMockExamRuleProfiles(nextProfiles)
  mockExamRuleCopyForm.targetKey = targetKey
  ElMessage.success(`已将 ${sourceKey} 复制到 ${targetKey}。`)
}

const parsedMockExamRuleProfiles = computed(() => {
  const parsed = tryParseMockExamRuleProfiles(settingsForm.mockExamRuleProfilesText)
  return parsed || {}
})

const mockExamRuleProfileOptions = computed(() => {
  const parsed = parsedMockExamRuleProfiles.value
  const resolvedKeys = new Set()
  const options = []

  Object.keys(DEFAULT_MOCK_EXAM_RULE_PROFILES).forEach((key) => {
    resolvedKeys.add(key)
    const label = DEFAULT_MOCK_EXAM_PROFILE_LABELS[key]
      ? `${key} (${DEFAULT_MOCK_EXAM_PROFILE_LABELS[key]})`
      : key
    options.push({ key, label })
  })

  Object.keys(parsed || {}).forEach((key) => {
    if (resolvedKeys.has(key)) {
      return
    }
    resolvedKeys.add(key)
    options.push({ key, label: `${key} (已配置)` })
  })

  return options
})

const loading = ref(false)
const savingSettings = ref(false)
const managedUsersLoading = ref(false)
const savingUser = ref(false)
const importing = ref(false)
const exporting = ref(false)
const editingUserId = ref('')
const importSummary = ref(null)
const exportPreview = ref('')

const settingsFormRef = ref(null)
const summary = reactive({
  studentCount: 0,
  teacherCount: 0,
  disabledCount: 0,
  messageCount: 0,
  templateCount: 0,
})
const settingsForm = reactive({
  platformName: '',
  defaultExamMinutes: 120,
  dailyCheckInPoints: 2,
  practiceRewardThreshold: 10,
  practiceRewardPoints: 2,
  paperRewardPoints: 2,
  wrongBookRewardThreshold: 5,
  wrongBookRewardPoints: 2,
  aiDailyLimit: 20,
  mockExamRuleProfilesText: '{}',
})
const managedUserForm = reactive(createManagedUserForm())
const managedUserQuery = reactive({
  role: '',
  keyword: '',
  page: 1,
  size: 20,
})
const importForm = reactive({
  csvText: [
    'name,mobile,examCategoryCode,jointExamGroupCode,vocationalMajor,prepStage',
    '管理考生,13800000007,MANAGEMENT,MANAGEMENT_1,财经商贸类,基础阶段',
  ].join('\n'),
})
const exportFormat = ref('csv')
const managedUsers = ref([])
const managedUsersTotal = ref(0)

const canManageStudents = computed(() => hasPermission('student:manage'))
const scopeLabelMaps = computed(() => buildContentLabelMaps(userStore.availableExamCategories))
const resolveExamCategoryLabel = (code) => resolveContentLabel(scopeLabelMaps.value.examCategoryNameMap, code)
const resolveJointExamGroupLabel = (code) => resolveContentLabel(scopeLabelMaps.value.jointExamGroupNameMap, code)
const isStudentRole = computed(() => managedUserForm.role === 'student')
const isTeacherRole = computed(() => managedUserForm.role === 'teacher')

const availableExamCategories = computed(() => {
  return Array.isArray(userStore.availableExamCategories) ? userStore.availableExamCategories : []
})

const availableJointExamGroups = computed(() => {
  const selectedCategory = managedUserForm.examCategoryCode
  if (!selectedCategory) {
    const groups = []
    availableExamCategories.value.forEach(category => {
      if (Array.isArray(category.jointExamGroups)) {
        groups.push(...category.jointExamGroups)
      }
    })
    return groups
  } else {
    const category = availableExamCategories.value.find(c => c.examCategoryCode === selectedCategory)
    return category && Array.isArray(category.jointExamGroups) ? category.jointExamGroups : []
  }
})


const availablePermissionOptions = computed(() => permissionOptionsByRole[managedUserForm.role] || [])
const summaryCards = computed(() =>
  summaryKeyOrder.map((key) => ({
    key,
    label: summaryLabelMap[key] || key,
    value: Number(summary[key] || 0),
  })),
)
const totalManagedUserPages = computed(() => Math.max(1, Math.ceil(managedUsersTotal.value / managedUserQuery.size)))
const permissionInputValue = computed({
  get() {
    return Array.isArray(managedUserForm.permissions) ? managedUserForm.permissions.join(', ') : ''
  },
  set(value) {
    managedUserForm.permissions = normalizePermissionList(value)
  },
})
const managedStudentIdsInputValue = computed({
  get() {
    return Array.isArray(managedUserForm.managedStudentIds) ? managedUserForm.managedStudentIds.join(', ') : ''
  },
  set(value) {
    managedUserForm.managedStudentIds = normalizeScopeIdList(value)
  },
})
const managedJointExamGroupCodesInputValue = computed({
  get() {
    return Array.isArray(managedUserForm.managedJointExamGroupCodes)
      ? managedUserForm.managedJointExamGroupCodes.join(', ')
      : ''
  },
  set(value) {
    managedUserForm.managedJointExamGroupCodes = normalizeScopeIdList(value)
  },
})
const teacherTemplatePermissions = computed(() => {
  if (!isTeacherRole.value) {
    return []
  }
  return resolveTeacherTemplatePermissions(managedUserForm.postTags)
})

const settingsRules = {
  platformName: [
    { required: true, message: '平台名称不能为空', trigger: 'blur' },
    { min: 1, max: 60, message: '平台名称长度需在 1-60 之间', trigger: 'blur' },
  ],
}

function createManagedUserForm() {
  return {
    userId: '',
    role: 'student',
    name: '',
    mobile: '',
    enabled: true,
    permissions: [],
    examCategoryCode: '',
    jointExamGroupCode: '',
    vocationalMajor: '',
    prepStage: '',
    postTags: [],
    managedStudentIds: [],
    managedJointExamGroupCodes: [],
  }
}

function normalizePermissionList(value) {
  if (Array.isArray(value)) {
    return value
      .map((item) => String(item || '').trim())
      .filter(Boolean)
  }
  return String(value || '')
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
}

function normalizeScopeIdList(value) {
  const values = Array.isArray(value)
    ? value
    : String(value || '').split(',')
  const normalized = []
  values.forEach((item) => {
    const key = String(item || '').trim()
    if (!key || normalized.includes(key)) {
      return
    }
    normalized.push(key)
  })
  return normalized
}

function normalizePostTags(value) {
  const values = Array.isArray(value) ? value : []
  const normalized = []
  values.forEach((item) => {
    const key = String(item || '').trim()
    if (!teacherPostTagLabelMap[key] || normalized.includes(key)) {
      return
    }
    normalized.push(key)
  })
  return normalized
}

function resolveTeacherTemplatePermissions(postTags = []) {
  const normalizedPostTags = normalizePostTags(postTags)
  const permissions = []
  normalizedPostTags.forEach((postTag) => {
    const templatePermissions = teacherPermissionTemplateByPostTag[postTag] || []
    templatePermissions.forEach((permissionKey) => {
      if (!permissions.includes(permissionKey)) {
        permissions.push(permissionKey)
      }
    })
  })
  return permissions
}

function applyConsoleData(payload) {
  const nextSummary = payload?.summary && typeof payload.summary === 'object' ? payload.summary : {}
  summary.studentCount = Number(nextSummary.studentCount || 0)
  summary.teacherCount = Number(nextSummary.teacherCount || 0)
  summary.disabledCount = Number(nextSummary.disabledCount || 0)
  summary.messageCount = Number(nextSummary.messageCount || 0)
  summary.templateCount = Number(nextSummary.templateCount || 0)

  const nextSettings = payload?.systemSettings && typeof payload.systemSettings === 'object' ? payload.systemSettings : {}
  settingsForm.platformName = String(nextSettings.platformName || '')
  settingsForm.defaultExamMinutes = Number(nextSettings.defaultExamMinutes || 120)
  settingsForm.dailyCheckInPoints = Number(nextSettings.dailyCheckInPoints || 2)
  settingsForm.practiceRewardThreshold = Number(nextSettings.practiceRewardThreshold || 10)
  settingsForm.practiceRewardPoints = Number(nextSettings.practiceRewardPoints || 2)
  settingsForm.paperRewardPoints = Number(nextSettings.paperRewardPoints || 2)
  settingsForm.wrongBookRewardThreshold = Number(nextSettings.wrongBookRewardThreshold || 5)
  settingsForm.wrongBookRewardPoints = Number(nextSettings.wrongBookRewardPoints || 2)
  settingsForm.aiDailyLimit = Number(nextSettings.aiDailyLimit || 20)
  settingsForm.mockExamRuleProfilesText = JSON.stringify(nextSettings.mockExamRuleProfiles || {}, null, 2)
}

function populateManagedUserForm(user) {
  Object.assign(managedUserForm, {
    userId: String(user?.userId || ''),
    role: String(user?.role || 'student'),
    name: String(user?.name || ''),
    mobile: String(user?.mobile || ''),
    enabled: Boolean(user?.enabled),
    permissions: Array.isArray(user?.permissions) ? user.permissions.map((item) => String(item || '').trim()).filter(Boolean) : [],
    examCategoryCode: String(user?.examCategoryCode || ''),
    jointExamGroupCode: String(user?.jointExamGroupCode || ''),
    vocationalMajor: String(user?.vocationalMajor || ''),
    prepStage: String(user?.prepStage || ''),
    postTags: normalizePostTags(user?.postTags),
    managedStudentIds: normalizeScopeIdList(user?.managedStudentIds),
    managedJointExamGroupCodes: normalizeScopeIdList(user?.managedJointExamGroupCodes),
  })
  editingUserId.value = managedUserForm.userId
}

function resetManagedUserForm() {
  Object.assign(managedUserForm, createManagedUserForm())
  editingUserId.value = ''
}

function formatRoleLabel(role) {
  return roleLabelMap[String(role || '').trim()] || String(role || '-')
}

function formatEnabledLabel(enabled) {
  return enabled ? '启用' : '停用'
}

function formatPostTagLabel(postTag) {
  return teacherPostTagLabelMap[String(postTag || '').trim()] || String(postTag || '').trim()
}

function formatManagedUserScopeSummary(user) {
  const ranges = []
  const examCategoryCode = String(user?.examCategoryCode || '').trim()
  const jointExamGroupCode = String(user?.jointExamGroupCode || '').trim()
  if (examCategoryCode || jointExamGroupCode) {
    ranges.push(`${resolveExamCategoryLabel(examCategoryCode)} / ${resolveJointExamGroupLabel(jointExamGroupCode)}`)
  }
  const managedStudentIds = normalizeScopeIdList(user?.managedStudentIds)
  if (managedStudentIds.length) {
    ranges.push(`负责学生 ${managedStudentIds.length} 人`)
  }
  const managedJointExamGroupCodes = normalizeScopeIdList(user?.managedJointExamGroupCodes)
  if (managedJointExamGroupCodes.length) {
    ranges.push(`负责专业组 ${managedJointExamGroupCodes.length} 个`)
  }
  return ranges.length ? ranges.join('；') : '-'
}

function applyTeacherPermissionTemplate() {
  if (!isTeacherRole.value) {
    return
  }
  const templatePermissions = resolveTeacherTemplatePermissions(managedUserForm.postTags)
  if (!templatePermissions.length) {
    ElMessage.warning('请先选择岗位标签。')
    return
  }
  managedUserForm.permissions = templatePermissions
  ElMessage.success('已按岗位标签填充权限模板。')
}

function validateManagedUserForm() {
  if (!String(managedUserForm.name || '').trim()) {
    throw new Error('请填写姓名。')
  }
  if (!/^1\d{10}$/.test(String(managedUserForm.mobile || '').trim())) {
    throw new Error('mobile 必须是合法中国大陆手机号。')
  }
  if (isStudentRole.value) {
    if (!String(managedUserForm.examCategoryCode || '').trim() || !String(managedUserForm.jointExamGroupCode || '').trim()) {
      throw new Error('学生账号必须填写学科门类与联考专业组。')
    }
    managedUserForm.permissions = []
    managedUserForm.postTags = []
    managedUserForm.managedStudentIds = []
    managedUserForm.managedJointExamGroupCodes = []
    return
  }
  if (isTeacherRole.value) {
    managedUserForm.postTags = normalizePostTags(managedUserForm.postTags)
    if (!managedUserForm.postTags.length) {
      throw new Error('教师账号至少需要一个岗位标签（招生岗/教学岗）。')
    }
    managedUserForm.managedStudentIds = normalizeScopeIdList(managedUserForm.managedStudentIds)
    managedUserForm.managedJointExamGroupCodes = normalizeScopeIdList(managedUserForm.managedJointExamGroupCodes)
    if (managedUserForm.postTags.includes('recruit')) {
      const hasScope = Boolean(
        String(managedUserForm.examCategoryCode || '').trim()
        || String(managedUserForm.jointExamGroupCode || '').trim()
        || managedUserForm.managedStudentIds.length
        || managedUserForm.managedJointExamGroupCodes.length,
      )
      if (!hasScope) {
        throw new Error('招生岗位至少需要一个数据范围（学科门类/联考专业组/负责学生/负责专业组）。')
      }
    }
    managedUserForm.permissions = normalizePermissionList(managedUserForm.permissions)
    if (!managedUserForm.permissions.length) {
      managedUserForm.permissions = resolveTeacherTemplatePermissions(managedUserForm.postTags)
    }
  } else {
    managedUserForm.postTags = []
    managedUserForm.managedStudentIds = []
    managedUserForm.managedJointExamGroupCodes = []
  }
  managedUserForm.permissions = normalizePermissionList(managedUserForm.permissions)
  if (!managedUserForm.permissions.length) {
    throw new Error('后台账号至少需要一个 permissions 权限点。')
  }
}

async function loadConsoleData() {
  const payload = await fetchAdminConsoleData()
  applyConsoleData(payload)
}

async function loadManagedUsers() {
  if (!canManageStudents.value) {
    managedUsers.value = []
    managedUsersTotal.value = 0
    return
  }
  managedUsersLoading.value = true
  try {
    const pageData = await fetchManagedUsersPage({
      role: managedUserQuery.role,
      keyword: managedUserQuery.keyword,
      page: managedUserQuery.page,
      size: managedUserQuery.size,
    })
    managedUsers.value = Array.isArray(pageData.items) ? pageData.items : []
    managedUsersTotal.value = Number(pageData.total || 0)
    managedUserQuery.page = Number(pageData.page || managedUserQuery.page)
    managedUserQuery.size = Number(pageData.size || managedUserQuery.size)
  } finally {
    managedUsersLoading.value = false
  }
}

watch(() => managedUserForm.examCategoryCode, () => {
  if (managedUserForm.jointExamGroupCode) {
    const group = availableJointExamGroups.value.find(g => g.jointExamGroupCode === managedUserForm.jointExamGroupCode)
    if (!group) {
      managedUserForm.jointExamGroupCode = ''
    }
  }
})

async function loadControlCenter() {
  loading.value = true
  try {
    await Promise.all([
      loadConsoleData(),
      loadManagedUsers(),
    ])
  } catch (error) {
    ElMessage.error(String(error?.response?.data?.message || error?.message || '控制台数据加载失败'))
  } finally {
    loading.value = false
  }
}

async function submitSettings() {
  if (savingSettings.value) {
    return
  }
  try {
    await settingsFormRef.value?.validate()
  } catch (error) {
    return
  }
  savingSettings.value = true
  try {
    let mockExamRuleProfiles = {}
    try {
      mockExamRuleProfiles = JSON.parse(String(settingsForm.mockExamRuleProfilesText || '{}'))
    } catch (error) {
      ElMessage.warning('模考规则配置必须是合法 JSON。')
      savingSettings.value = false
      return
    }
    await saveSystemSettings({
      platformName: settingsForm.platformName,
      defaultExamMinutes: Number(settingsForm.defaultExamMinutes || 120),
      dailyCheckInPoints: Number(settingsForm.dailyCheckInPoints || 0),
      practiceRewardThreshold: Number(settingsForm.practiceRewardThreshold || 1),
      practiceRewardPoints: Number(settingsForm.practiceRewardPoints || 0),
      paperRewardPoints: Number(settingsForm.paperRewardPoints || 0),
      wrongBookRewardThreshold: Number(settingsForm.wrongBookRewardThreshold || 1),
      wrongBookRewardPoints: Number(settingsForm.wrongBookRewardPoints || 0),
      aiDailyLimit: Number(settingsForm.aiDailyLimit || 1),
      mockExamRuleProfiles,
    })
    await loadConsoleData()
    ElMessage.success('系统参数已保存。')
  } catch (error) {
    ElMessage.error(String(error?.response?.data?.message || error?.message || '系统参数保存失败'))
  } finally {
    savingSettings.value = false
  }
}

async function submitManagedUser() {
  if (savingUser.value) {
    return
  }
  try {
    validateManagedUserForm()
  } catch (error) {
    ElMessage.warning(String(error?.message || error))
    return
  }
  savingUser.value = true
  try {
    await saveManagedUserRecord({
      userId: managedUserForm.userId,
      role: managedUserForm.role,
      name: managedUserForm.name,
      mobile: managedUserForm.mobile,
      enabled: Boolean(managedUserForm.enabled),
      permissions: managedUserForm.permissions,
      examCategoryCode: managedUserForm.examCategoryCode,
      jointExamGroupCode: managedUserForm.jointExamGroupCode,
      vocationalMajor: managedUserForm.vocationalMajor,
      prepStage: managedUserForm.prepStage,
      postTags: managedUserForm.postTags,
      managedStudentIds: managedUserForm.managedStudentIds,
      managedJointExamGroupCodes: managedUserForm.managedJointExamGroupCodes,
    })
    resetManagedUserForm()
    managedUserQuery.page = 1
    await Promise.all([loadConsoleData(), loadManagedUsers()])
    ElMessage.success('账号目录已更新。')
  } catch (error) {
    ElMessage.error(String(error?.response?.data?.message || error?.message || '账号保存失败'))
  } finally {
    savingUser.value = false
  }
}

async function submitImport() {
  if (importing.value) {
    return
  }
  if (!String(importForm.csvText || '').trim()) {
    ElMessage.warning('请先填写导入模板内容。')
    return
  }
  importing.value = true
  try {
    importSummary.value = await importManagedStudents({ csvText: importForm.csvText })
    managedUserQuery.page = 1
    await Promise.all([loadConsoleData(), loadManagedUsers()])
    ElMessage.success('考生批量导入已执行。')
  } catch (error) {
    ElMessage.error(String(error?.response?.data?.message || error?.message || '考生导入失败'))
  } finally {
    importing.value = false
  }
}

async function handleExport() {
  if (exporting.value) {
    return
  }
  exporting.value = true
  try {
    const result = await exportManagedStudentsDirectory({ format: exportFormat.value })
    exportPreview.value = String(result?.content || '')
    ElMessage.success('考生目录已导出。')
  } catch (error) {
    ElMessage.error(String(error?.response?.data?.message || error?.message || '考生导出失败'))
  } finally {
    exporting.value = false
  }
}

async function refreshManagedUsers() {
  managedUserQuery.page = 1
  await loadManagedUsers()
}

async function handlePageChange(page) {
  managedUserQuery.page = Number(page || 1)
  await loadManagedUsers()
}

async function handlePageSizeChange(size) {
  managedUserQuery.size = Number(size || 20)
  managedUserQuery.page = 1
  await loadManagedUsers()
}

watch(
  () => managedUserForm.role,
  (role) => {
    if (role === 'student') {
      managedUserForm.permissions = []
      managedUserForm.postTags = []
      managedUserForm.managedStudentIds = []
      managedUserForm.managedJointExamGroupCodes = []
      return
    }
    if (role === 'teacher' && !managedUserForm.postTags.length) {
      managedUserForm.postTags = ['teach']
      return
    }
    managedUserForm.postTags = []
    managedUserForm.managedStudentIds = []
    managedUserForm.managedJointExamGroupCodes = []
  },
  { immediate: true },
)

onMounted(() => {
  loadControlCenter()
})
</script>

<template>
  <section class="control-center-shell" v-loading="loading">
    <header class="page-header">
      <div>
        <h3>系统控制台</h3>
        <p>把系统参数、账号权限、考生导入导出和账号目录统一收敛到新版超管工作台。</p>
      </div>
      <el-button @click="loadControlCenter">刷新控制台</el-button>
    </header>

    <section class="summary-grid">
      <article v-for="summaryItem in summaryCards" :key="summaryItem.key" class="summary-card">
        <span>{{ summaryItem.label }}</span>
        <strong>{{ summaryItem.value }}</strong>
      </article>
    </section>

    <section class="content-grid">
      <el-card shadow="never">
        <template #header>
          <div class="card-header">
            <span>系统参数</span>
            <el-button type="primary" :loading="savingSettings" @click="submitSettings">保存参数</el-button>
          </div>
        </template>
        <el-form ref="settingsFormRef" :model="settingsForm" :rules="settingsRules" label-position="top">
          <el-row :gutter="12">
            <el-col :span="12">
              <el-form-item label="平台名称" prop="platformName">
                <el-input v-model="settingsForm.platformName" maxlength="60" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="默认考试时长（分钟）">
                <el-input-number v-model="settingsForm.defaultExamMinutes" :min="30" :max="240" :step="5" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="每日打卡积分">
                <el-input-number v-model="settingsForm.dailyCheckInPoints" :min="0" :max="200" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="刷题奖励阈值">
                <el-input-number v-model="settingsForm.practiceRewardThreshold" :min="1" :max="200" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="刷题奖励积分">
                <el-input-number v-model="settingsForm.practiceRewardPoints" :min="0" :max="200" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="试卷奖励积分">
                <el-input-number v-model="settingsForm.paperRewardPoints" :min="0" :max="200" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="错题本奖励阈值">
                <el-input-number v-model="settingsForm.wrongBookRewardThreshold" :min="1" :max="200" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="错题本奖励积分">
                <el-input-number v-model="settingsForm.wrongBookRewardPoints" :min="0" :max="200" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="AI 每日额度">
                <el-input-number v-model="settingsForm.aiDailyLimit" :min="1" :max="200" />
              </el-form-item>
            </el-col>
            <el-col :span="24">
              <el-form-item label="模考规则配置（JSON）">
                <el-input
                  v-model="settingsForm.mockExamRuleProfilesText"
                  type="textarea"
                  :rows="14"
                  placeholder="按 subjectCode 配置 durationMinutes / typeRules / difficultyRatio"
                />
                <div class="mock-exam-controls">
                  <el-button size="small" type="primary" @click="fillDefaultMockExamRuleProfiles">
                    一键填充默认模考规则模板
                  </el-button>
                  <el-select
                    size="small"
                    v-model="mockExamRuleCopyForm.sourceKey"
                    placeholder="选择源科目/默认档"
                    class="mock-exam-select"
                  >
                    <el-option
                      v-for="option in mockExamRuleProfileOptions"
                      :key="option.key"
                      :label="option.label"
                      :value="option.key"
                    />
                  </el-select>
                  <el-input
                    size="small"
                    v-model="mockExamRuleCopyForm.targetKey"
                    placeholder="目标科目编码或默认档"
                    class="mock-exam-input"
                  />
                  <el-button size="small" type="success" @click="handleCopyMockExamRuleProfile">
                    复制预设
                  </el-button>
                </div>
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>
      </el-card>

      <el-card shadow="never">
        <template #header>
          <div class="card-header">
            <span>{{ editingUserId ? `编辑账号 ${editingUserId}` : '新增账号' }}</span>
            <div class="inline-actions">
              <el-button v-if="editingUserId" @click="resetManagedUserForm">取消编辑</el-button>
              <el-button type="primary" :loading="savingUser" :disabled="!canManageStudents" @click="submitManagedUser">
                保存账号
              </el-button>
            </div>
          </div>
        </template>
        <el-form label-position="top">
          <el-row :gutter="12">
            <el-col :span="12">
              <el-form-item label="用户ID（非必填）">
                <el-input v-model="managedUserForm.userId" :disabled="Boolean(editingUserId)" placeholder="不填写时系统会自动生成" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="角色">
                <el-select v-model="managedUserForm.role">
                  <el-option label="学生" value="student" />
                  <el-option label="教师" value="teacher" />
                  <el-option label="总管理员" value="super_admin" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="姓名">
                <el-input v-model="managedUserForm.name" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="手机号">
                <el-input v-model="managedUserForm.mobile" maxlength="11" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="账号状态">
                <el-switch
                  v-model="managedUserForm.enabled"
                  inline-prompt
                  active-text="启用"
                  inactive-text="停用"
                />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="权限点">
                <div class="permission-editor">
                  <el-input
                    v-model="permissionInputValue"
                    :disabled="isStudentRole"
                    :placeholder="isStudentRole ? '该账号不配置后台权限点' : availablePermissionOptions.join(', ')"
                  />
                  <el-button
                    v-if="isTeacherRole"
                    size="small"
                    type="primary"
                    plain
                    @click="applyTeacherPermissionTemplate"
                  >
                    按岗位套用权限
                  </el-button>
                </div>
                <span v-if="isTeacherRole && teacherTemplatePermissions.length" class="helper-text">
                  岗位模板建议：{{ teacherTemplatePermissions.join(', ') }}
                </span>
              </el-form-item>
            </el-col>
            <el-col v-if="isTeacherRole" :span="12">
              <el-form-item label="岗位标签">
                <el-select v-model="managedUserForm.postTags" multiple collapse-tags collapse-tags-tooltip>
                  <el-option
                    v-for="option in teacherPostTagOptions"
                    :key="option.value"
                    :label="option.label"
                    :value="option.value"
                  />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="学科门类">
                <el-select v-model="managedUserForm.examCategoryCode" style="width: 100%" placeholder="请选择学科门类" clearable>
                  <el-option
                    v-for="category in availableExamCategories"
                    :key="category.examCategoryCode"
                    :label="category.examCategoryName"
                    :value="category.examCategoryCode"
                  />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="联考专业组">
                <el-select v-model="managedUserForm.jointExamGroupCode" style="width: 100%" placeholder="请选择联考专业组" clearable>
                  <el-option
                    v-for="group in availableJointExamGroups"
                    :key="group.jointExamGroupCode"
                    :label="group.jointExamGroupName"
                    :value="group.jointExamGroupCode"
                  />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="高职专业">
                <el-input v-model="managedUserForm.vocationalMajor" placeholder="请输入高职专业" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="备考阶段">
                <el-input v-model="managedUserForm.prepStage" />
              </el-form-item>
            </el-col>
            <el-col v-if="isTeacherRole" :span="12">
              <el-form-item label="负责学生（userId，逗号分隔）">
                <el-input
                  v-model="managedStudentIdsInputValue"
                  placeholder="示例：student-001, student-031"
                />
              </el-form-item>
            </el-col>
            <el-col v-if="isTeacherRole" :span="12">
              <el-form-item label="负责联考专业组（逗号分隔）">
                <el-input
                  v-model="managedJointExamGroupCodesInputValue"
                  placeholder="示例：SCIENCE_ENGINEERING_3, MANAGEMENT_1"
                />
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>
      </el-card>
    </section>

    <section class="content-grid secondary-grid">
      <el-card shadow="never">
        <template #header>
          <div class="card-header">
            <span>考生导入导出</span>
            <div class="inline-actions">
              <el-select v-model="exportFormat" class="export-select">
                <el-option label="CSV 格式" value="csv" />
                <el-option label="PDF 目录文本" value="pdf" />
              </el-select>
              <el-button :loading="exporting" :disabled="!canManageStudents" @click="handleExport">导出目录</el-button>
            </div>
          </div>
        </template>
        <el-form label-position="top">
          <el-form-item label="导入模板">
            <el-input v-model="importForm.csvText" type="textarea" :rows="8" />
          </el-form-item>
          <div class="inline-actions">
            <el-button type="primary" :loading="importing" :disabled="!canManageStudents" @click="submitImport">
              批量导入考生
            </el-button>
          </div>
        </el-form>

        <el-alert
          v-if="importSummary"
          class="feedback-block"
          type="success"
          :closable="false"
          show-icon
          :title="`导入完成：成功 ${importSummary.imported || 0} 条，失败 ${importSummary.failed || 0} 条。`"
        />
        <pre v-if="importSummary" class="result-block">{{ JSON.stringify(importSummary, null, 2) }}</pre>
        <pre v-if="exportPreview" class="result-block">{{ exportPreview }}</pre>
      </el-card>

      <el-card shadow="never">
        <template #header>
          <div class="card-header">
            <span>账号目录</span>
            <div class="inline-actions">
              <el-select v-model="managedUserQuery.role" clearable placeholder="全部角色" @change="refreshManagedUsers">
                <el-option label="学生" value="student" />
                <el-option label="教师" value="teacher" />
                <el-option label="总管理员" value="super_admin" />
              </el-select>
              <el-input
                v-model="managedUserQuery.keyword"
                clearable
                placeholder="搜索 userId / 姓名 / 手机号"
                @keyup.enter="refreshManagedUsers"
              />
              <el-button :loading="managedUsersLoading" @click="refreshManagedUsers">刷新列表</el-button>
            </div>
          </div>
        </template>

        <el-table :data="managedUsers" border v-loading="managedUsersLoading">
          <el-table-column prop="userId" label="用户ID" min-width="140" />
          <el-table-column label="角色" width="110">
            <template #default="scope">
              {{ formatRoleLabel(scope.row.role) }}
            </template>
          </el-table-column>
          <el-table-column prop="name" label="姓名" min-width="120" />
          <el-table-column prop="mobile" label="手机号" width="140" />
          <el-table-column label="状态" width="90">
            <template #default="scope">
              <el-tag :type="scope.row.enabled ? 'success' : 'info'" effect="light">
                {{ formatEnabledLabel(scope.row.enabled) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="岗位标签" min-width="160">
            <template #default="scope">
              {{ normalizePostTags(scope.row.postTags).map((item) => formatPostTagLabel(item)).join('、') || '-' }}
            </template>
          </el-table-column>
          <el-table-column label="范围信息" min-width="260">
            <template #default="scope">
              <span>{{ formatManagedUserScopeSummary(scope.row) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="权限点" min-width="220">
            <template #default="scope">
              {{ Array.isArray(scope.row.permissions) && scope.row.permissions.length ? scope.row.permissions.join(', ') : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100" fixed="right">
            <template #default="scope">
              <el-button link type="primary" @click="populateManagedUserForm(scope.row)">编辑</el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="pagination-row">
          <span class="helper-text">第 {{ managedUserQuery.page }} / {{ totalManagedUserPages }} 页，共 {{ managedUsersTotal }} 条</span>
          <el-pagination
            background
            layout="total, sizes, prev, pager, next"
            :current-page="managedUserQuery.page"
            :page-size="managedUserQuery.size"
            :page-sizes="[10, 20, 50]"
            :total="managedUsersTotal"
            @current-change="handlePageChange"
            @size-change="handlePageSizeChange"
          />
        </div>
      </el-card>
    </section>

  </section>
</template>

<style scoped>
.control-center-shell {
  display: grid;
  gap: 12px;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.page-header h3,
.page-header p {
  margin: 0;
}

.page-header p {
  margin-top: 6px;
  color: var(--qb-text-subtle-8);
}

.summary-grid {
  display: grid;
  gap: 10px;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
}

.summary-card {
  border: 1px solid var(--qb-primary-soft-border);
  border-radius: 12px;
  background: var(--qb-primary-soft-bg);
  padding: 14px;
  display: grid;
  gap: 8px;
}

.summary-card strong {
  font-size: 24px;
}

.content-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(2, minmax(320px, 1fr));
}

.secondary-grid {
  align-items: start;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.inline-actions {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.permission-editor {
  display: flex;
  gap: 8px;
  align-items: center;
}

.export-select {
  width: 150px;
}

.feedback-block {
  margin-top: 12px;
}

.result-block {
  margin: 12px 0 0;
  padding: 12px;
  border-radius: 10px;
  background: var(--qb-bg-card);
  border: 1px solid var(--qb-border-muted);
  max-height: 260px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-word;
}
.mock-exam-controls {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}
.mock-exam-select {
  min-width: 220px;
}
.mock-exam-input {
  min-width: 200px;
}

.pagination-row {
  margin-top: 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.helper-text {
  color: var(--qb-text-subtle-6);
  font-size: 13px;
}

@media (max-width: 1100px) {
  .content-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 900px) {
  .page-header,
  .card-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .permission-editor {
    width: 100%;
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
