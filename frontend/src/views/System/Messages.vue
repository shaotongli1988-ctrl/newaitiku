<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { Bell, Cpu, WarningFilled } from '@/ui/icons'
import { ElMessage, ElMessageBox } from '@/ui/feedback'
import {
  fetchContentBaseline,
  fetchMessageListPage,
  fetchMessageSendHistoryPage,
  fetchMessageSettings,
  fetchMessageUnreadSummary,
  markMessageAsRead,
  markMessagesAsReadBatch,
  recallMessageSendRecord,
  saveMessageSettingsData,
  sendMessageBatch,
} from '../../api/services/questionBank'
import { useUserStore } from '../../stores/userStore.js'
import {
  filterJointExamGroupOptions,
  filterSubjectCodeOptions,
  normalizeContentBaseline,
} from '../../utils/contentBaseline'

const userStore = useUserStore()

const canSendMessages = computed(() => userStore.hasPermission('message:send'))

const tableLoading = ref(false)
const historyLoading = ref(false)
const settingsSaving = ref(false)
const sendSubmitting = ref(false)
const messageRows = ref([])
const sendHistoryRows = ref([])
const unreadCount = ref(0)
const selectedMessageIds = ref([])
const activeMessageTab = ref('announcement')
const actingMessageId = ref('')
const actingTraceId = ref('')

const filterModel = reactive({
  readStatus: '',
})

const settingsModel = reactive({
  allowAiTutor: true,
  allowSystemNotice: true,
  allowReviewNotice: true,
  allowStudyReminder: true,
  allowWeeklyReport: true,
  allowPointsNotice: true,
})

const sendForm = reactive({
  targetMode: 'userIds',
  templateKey: '',
  userIdsText: 'student-001',
  examCategoryCode: '',
  jointExamGroupCode: '',
  subjectCode: '',
  sendAt: '',
  category: 'STUDY_REMINDER',
  title: '学习提醒',
  content: '请及时完成今日刷题与错题复盘。',
})

const pagination = reactive({
  page: 1,
  size: 6,
  total: 0,
})

const historyPagination = reactive({
  page: 1,
  size: 10,
  total: 0,
})

const dictionaryState = reactive({
  examCategoryOptions: [],
  jointExamGroupOptions: [],
  subjectCodeOptions: [],
})

const INBOX_FETCH_PAGE_SIZE = 100
const MAX_INBOX_FETCH_PAGES = 20

const announcementCategories = new Set(['SYSTEM_NOTICE', 'REVIEW_NOTICE', 'WEEKLY_REPORT', 'POINTS_NOTICE'])
const alertCategories = new Set(['STUDY_REMINDER'])
const aiCategories = new Set(['AI_TUTOR', 'AI_MARKING', 'TEACHER_QA'])
const alertKeywords = ['警报', '预警', '掌握度', 'mastery', 'l5', '薄弱', '低于40', '低于 40', '复盘', '错因']
const aiKeywords = ['ai', '答疑', '批改', '智能', '老师答疑']

const messageTabOptions = [
  {
    key: 'announcement',
    label: '全员公告',
    helper: '系统公告、阶段播报与班级通知集中展示。',
    icon: Bell,
    accent: 'announcement',
    tagType: 'info',
  },
  {
    key: 'alert',
    label: '学情警报',
    helper: '优先承接 Mastery < 40% 的 L5 风险语义与待复盘提醒。',
    icon: WarningFilled,
    accent: 'alert',
    tagType: 'danger',
  },
  {
    key: 'ai',
    label: 'AI 建议',
    helper: '聚合 AI 答疑、批改反馈和智能学习建议。',
    icon: Cpu,
    accent: 'ai',
    tagType: 'success',
  },
]

const readStatusOptions = [
  { value: '', label: '全部状态' },
  { value: 'unread', label: '未读' },
  { value: 'read', label: '已读' },
]

const messageCategoryOptions = [
  { value: '', label: '全部分类' },
  { value: 'AI_TUTOR', label: 'AI答疑' },
  { value: 'AI_MARKING', label: 'AI批改' },
  { value: 'SYSTEM_NOTICE', label: '系统通知' },
  { value: 'REVIEW_NOTICE', label: '评审通知' },
  { value: 'STUDY_REMINDER', label: '学习提醒' },
  { value: 'WEEKLY_REPORT', label: '周报通知' },
  { value: 'POINTS_NOTICE', label: '积分通知' },
]

const sendTemplateOptions = [
  {
    value: '',
    label: '手动填写',
    payload: null,
  },
  {
    value: 'daily-practice',
    label: '今日学习提醒',
    payload: {
      category: 'STUDY_REMINDER',
      title: '今日学习提醒',
      content: '请在今晚 21:00 前完成今日章节刷题与错题复盘。',
    },
  },
  {
    value: 'weekly-summary',
    label: '周报通知模板',
    payload: {
      category: 'WEEKLY_REPORT',
      title: '周报提醒',
      content: '请及时查看本周学习周报，关注薄弱章节与掌握度变化。',
    },
  },
  {
    value: 'system-update',
    label: '系统公告模板',
    payload: {
      category: 'SYSTEM_NOTICE',
      title: '系统公告',
      content: '平台功能已更新，请刷新页面后使用新功能。',
    },
  },
]

const targetModeOptions = [
  { value: 'userIds', label: '按用户ID发送' },
  { value: 'cohort', label: '按分群发送' },
]

const filteredJointExamGroupOptions = computed(() =>
  filterJointExamGroupOptions(dictionaryState.jointExamGroupOptions, sendForm.examCategoryCode),
)

const filteredSubjectCodeOptions = computed(() =>
  filterSubjectCodeOptions(
    dictionaryState.subjectCodeOptions,
    sendForm.examCategoryCode,
    sendForm.jointExamGroupCode,
  ),
)
const selectedExamCategoryLabel = computed(() =>
  dictionaryState.examCategoryOptions.find(
    (item) => String(item?.examCategoryCode || '').trim() === String(sendForm.examCategoryCode || '').trim(),
  )?.examCategoryName || '',
)
const selectedJointExamGroupLabel = computed(() =>
  dictionaryState.jointExamGroupOptions.find(
    (item) => String(item?.jointExamGroupCode || '').trim() === String(sendForm.jointExamGroupCode || '').trim(),
  )?.jointExamGroupName || '',
)
const selectedSubjectLabel = computed(() =>
  dictionaryState.subjectCodeOptions.find(
    (item) => String(item?.subjectCode || '').trim() === String(sendForm.subjectCode || '').trim(),
  )?.subjectName || '',
)

const selectedMessageCountLabel = computed(() => `已勾选 ${selectedMessageIds.value.length} 条`)
const selectedUserIdsPreview = computed(() =>
  String(sendForm.userIdsText || '')
    .split(/[\n,]+/)
    .map((item) => String(item || '').trim())
    .filter(Boolean)
    .join('、'),
)
const messageTabCards = computed(() =>
  messageTabOptions.map((tab) => ({
    ...tab,
    count: messageRows.value.filter((row) => resolveMessageTabKey(row) === tab.key).length,
  })),
)
const activeTabMessageRows = computed(() =>
  messageRows.value.filter((row) => resolveMessageTabKey(row) === activeMessageTab.value),
)
const inboxTotal = computed(() => activeTabMessageRows.value.length)
const pagedMessageRows = computed(() => {
  const start = Math.max(0, (pagination.page - 1) * pagination.size)
  return activeTabMessageRows.value.slice(start, start + pagination.size)
})
const visibleSelectableMessageRows = computed(() => pagedMessageRows.value.filter((row) => canSelectMessageRow(row)))
const hasVisibleSelectableMessages = computed(() => visibleSelectableMessageRows.value.length > 0)
const areAllVisibleMessagesSelected = computed(
  () =>
    visibleSelectableMessageRows.value.length > 0
    && visibleSelectableMessageRows.value.every((row) => isMessageSelected(row?.messageId)),
)
const readMessageCount = computed(() => messageRows.value.filter((row) => Boolean(row?.isRead)).length)
const handledMessagePercent = computed(() => {
  const total = Math.max(messageRows.value.length, unreadCount.value + readMessageCount.value)
  if (!total) {
    return 0
  }
  return Math.max(0, Math.min(100, Math.round((readMessageCount.value / total) * 100)))
})

watch(
  () => sendForm.examCategoryCode,
  () => {
    if (
      !filteredJointExamGroupOptions.value.some(
        (optionItem) => optionItem.jointExamGroupCode === sendForm.jointExamGroupCode,
      )
    ) {
      sendForm.jointExamGroupCode = ''
    }
    if (
      !filteredSubjectCodeOptions.value.some(
        (optionItem) => optionItem.subjectCode === sendForm.subjectCode,
      )
    ) {
      sendForm.subjectCode = ''
    }
  },
)

watch(
  () => sendForm.jointExamGroupCode,
  () => {
    if (
      !filteredSubjectCodeOptions.value.some(
        (optionItem) => optionItem.subjectCode === sendForm.subjectCode,
      )
    ) {
      sendForm.subjectCode = ''
    }
  },
)

watch(activeMessageTab, () => {
  pagination.page = 1
})

watch(inboxTotal, (total) => {
  const totalPages = Math.max(1, Math.ceil(total / pagination.size))
  if (pagination.page > totalPages) {
    pagination.page = totalPages
  }
})

function formatDateTime(value) {
  const normalized = String(value || '').trim()
  if (!normalized) {
    return '-'
  }
  const parsed = new Date(normalized)
  if (Number.isNaN(parsed.getTime())) {
    return normalized
  }
  const year = parsed.getFullYear()
  const month = `${parsed.getMonth() + 1}`.padStart(2, '0')
  const day = `${parsed.getDate()}`.padStart(2, '0')
  const hour = `${parsed.getHours()}`.padStart(2, '0')
  const minute = `${parsed.getMinutes()}`.padStart(2, '0')
  return `${year}-${month}-${day} ${hour}:${minute}`
}

function formatCategoryLabel(category) {
  const normalizedCategory = String(category || '').trim()
  const matchedOption = messageCategoryOptions.find((item) => item.value === normalizedCategory)
  return matchedOption?.label || normalizedCategory || '-'
}

function normalizeMessageText(row) {
  return `${String(row?.title || '').trim()} ${String(row?.content || '').trim()}`.toLowerCase()
}

function matchesMessageKeywords(text, keywords) {
  return keywords.some((keyword) => text.includes(keyword))
}

function isAiMessage(row) {
  const category = String(row?.category || '').trim()
  if (aiCategories.has(category)) {
    return true
  }
  return matchesMessageKeywords(normalizeMessageText(row), aiKeywords)
}

function isAlertMessage(row) {
  const category = String(row?.category || '').trim()
  if (alertCategories.has(category)) {
    return true
  }
  return matchesMessageKeywords(normalizeMessageText(row), alertKeywords)
}

function resolveMessageTabKey(row) {
  const category = String(row?.category || '').trim()
  if (isAiMessage(row)) {
    return 'ai'
  }
  if (isAlertMessage(row)) {
    return 'alert'
  }
  if (announcementCategories.has(category)) {
    return 'announcement'
  }
  return 'announcement'
}

function resolveMessageVisual(row) {
  const tabKey = resolveMessageTabKey(row)
  return messageTabOptions.find((tab) => tab.key === tabKey) || messageTabOptions[0]
}

function formatTargetModeLabel(targetMode) {
  return String(targetMode || '').trim() === 'cohort' ? '按分群' : '按用户ID'
}

function formatHistoryStatusType(status) {
  if (status === 'RECALLED') {
    return 'info'
  }
  if (status === 'SCHEDULED') {
    return 'warning'
  }
  return 'success'
}

function canSelectMessageRow(row) {
  return !row?.isRead && !row?.isRecalled
}

function buildSendPayload() {
  return {
    targetMode: sendForm.targetMode,
    userIds: String(sendForm.userIdsText || '')
      .split(/[\n,]+/)
      .map((item) => String(item || '').trim())
      .filter(Boolean),
    examCategoryCode: sendForm.examCategoryCode,
    jointExamGroupCode: sendForm.jointExamGroupCode,
    subjectCode: sendForm.subjectCode,
    sendAt: sendForm.sendAt,
    category: sendForm.category,
    title: sendForm.title,
    content: sendForm.content,
  }
}

function applySendTemplate(templateKey) {
  const template = sendTemplateOptions.find((item) => item.value === templateKey)?.payload
  if (!template) {
    return
  }
  sendForm.category = template.category
  sendForm.title = template.title
  sendForm.content = template.content
}

async function loadContentDictionary() {
  if (!canSendMessages.value) {
    return
  }
  const baseline = await fetchContentBaseline()
  const normalized = normalizeContentBaseline(baseline?.data || baseline)
  dictionaryState.examCategoryOptions = normalized.examCategoryOptions
  dictionaryState.jointExamGroupOptions = normalized.jointExamGroupOptions
  dictionaryState.subjectCodeOptions = normalized.subjectCodeOptions
}

async function loadUnreadSummary() {
  try {
    const summary = await fetchMessageUnreadSummary()
    unreadCount.value = Number(summary?.totalUnread || 0)
  } catch (error) {
    unreadCount.value = 0
  }
}

async function loadMessageSettings() {
  const settings = await fetchMessageSettings()
  Object.assign(settingsModel, {
    allowAiTutor: Boolean(settings?.allowAiTutor),
    allowSystemNotice: Boolean(settings?.allowSystemNotice),
    allowReviewNotice: Boolean(settings?.allowReviewNotice),
    allowStudyReminder: Boolean(settings?.allowStudyReminder),
    allowWeeklyReport: Boolean(settings?.allowWeeklyReport),
    allowPointsNotice: Boolean(settings?.allowPointsNotice),
  })
}

async function loadMessageRows() {
  tableLoading.value = true
  try {
    const aggregatedRows = []
    let currentPage = 1
    let total = 0

    while (currentPage <= MAX_INBOX_FETCH_PAGES) {
      const pageData = await fetchMessageListPage({
        page: currentPage,
        size: INBOX_FETCH_PAGE_SIZE,
        readStatus: filterModel.readStatus,
      })
      const pageItems = Array.isArray(pageData?.items) ? pageData.items : []
      total = Number(pageData?.total || pageItems.length || 0)
      aggregatedRows.push(...pageItems)
      if (!pageItems.length || aggregatedRows.length >= total || pageItems.length < INBOX_FETCH_PAGE_SIZE) {
        break
      }
      currentPage += 1
    }

    messageRows.value = aggregatedRows
    pagination.total = aggregatedRows.length
    selectedMessageIds.value = selectedMessageIds.value.filter((messageId) =>
      aggregatedRows.some((row) => String(row?.messageId || '').trim() === messageId && canSelectMessageRow(row)),
    )
  } catch (error) {
    messageRows.value = []
    pagination.total = 0
    ElMessage.error(String(error?.response?.data?.message || error?.message || '消息列表加载失败'))
  } finally {
    tableLoading.value = false
  }
}

async function loadSendHistory() {
  if (!canSendMessages.value) {
    sendHistoryRows.value = []
    historyPagination.total = 0
    return
  }
  historyLoading.value = true
  try {
    const pageData = await fetchMessageSendHistoryPage({
      page: historyPagination.page,
      size: historyPagination.size,
    })
    sendHistoryRows.value = Array.isArray(pageData?.items) ? pageData.items : []
    historyPagination.total = Number(pageData?.total || 0)
  } catch (error) {
    sendHistoryRows.value = []
    historyPagination.total = 0
    ElMessage.error(String(error?.response?.data?.message || error?.message || '发送历史加载失败'))
  } finally {
    historyLoading.value = false
  }
}

async function reloadInbox() {
  await Promise.all([loadMessageRows(), loadUnreadSummary()])
}

async function reloadHistoryAndInbox() {
  const jobs = [reloadInbox()]
  if (canSendMessages.value) {
    jobs.push(loadSendHistory())
  }
  await Promise.all(jobs)
}

async function bootstrapPage() {
  const jobs = [loadMessageSettings(), reloadInbox()]
  if (canSendMessages.value) {
    jobs.push(loadContentDictionary(), loadSendHistory())
  }
  await Promise.all(jobs)
}

async function onFilterChange() {
  pagination.page = 1
  await loadMessageRows()
}

function onInboxPageChange(nextPage) {
  pagination.page = Number(nextPage || 1)
}

async function onHistoryPageChange(nextPage) {
  historyPagination.page = Number(nextPage || 1)
  await loadSendHistory()
}

function isMessageSelected(messageId) {
  const normalizedId = String(messageId || '').trim()
  return normalizedId ? selectedMessageIds.value.includes(normalizedId) : false
}

function toggleMessageSelection(row, checked) {
  const messageId = String(row?.messageId || '').trim()
  if (!messageId || !canSelectMessageRow(row)) {
    return
  }
  const selection = new Set(selectedMessageIds.value)
  if (checked) {
    selection.add(messageId)
  } else {
    selection.delete(messageId)
  }
  selectedMessageIds.value = Array.from(selection)
}

function handleToggleSelectAllVisible(checked) {
  const selection = new Set(selectedMessageIds.value)
  visibleSelectableMessageRows.value.forEach((row) => {
    const messageId = String(row?.messageId || '').trim()
    if (!messageId) {
      return
    }
    if (checked) {
      selection.add(messageId)
    } else {
      selection.delete(messageId)
    }
  })
  selectedMessageIds.value = Array.from(selection)
}

function clearSelectedMessages() {
  selectedMessageIds.value = []
}

async function handleMarkRead(row) {
  const messageId = String(row?.messageId || '').trim()
  if (!messageId || row?.isRead || row?.isRecalled || actingMessageId.value) {
    return
  }
  actingMessageId.value = messageId
  try {
    const result = await markMessageAsRead(messageId)
    row.isRead = true
    selectedMessageIds.value = selectedMessageIds.value.filter((item) => item !== messageId)
    unreadCount.value = Number(result?.unreadCount || 0)
    ElMessage.success('消息已标记为已读')
    await loadMessageRows()
  } catch (error) {
    ElMessage.error(String(error?.response?.data?.message || error?.message || '标记已读失败'))
  } finally {
    actingMessageId.value = ''
  }
}

async function handleBatchMarkRead() {
  if (!selectedMessageIds.value.length) {
    ElMessage.warning('请先勾选至少 1 条未读消息')
    return
  }
  try {
    const result = await markMessagesAsReadBatch(selectedMessageIds.value)
    unreadCount.value = Number(result?.unreadCount || 0)
    ElMessage.success(`已批量标记 ${Number(result?.markedCount || 0)} 条消息为已读`)
    await loadMessageRows()
  } catch (error) {
    ElMessage.error(String(error?.response?.data?.message || error?.message || '批量已读失败'))
  }
}

async function handleSaveSettings() {
  settingsSaving.value = true
  try {
    await saveMessageSettingsData({ ...settingsModel })
    ElMessage.success('消息设置已更新')
  } catch (error) {
    ElMessage.error(String(error?.response?.data?.message || error?.message || '消息设置保存失败'))
  } finally {
    settingsSaving.value = false
  }
}

async function handleSendMessage() {
  sendSubmitting.value = true
  try {
    const payload = buildSendPayload()
    const result = await sendMessageBatch(payload)
    if (Number(result?.scheduledCount || 0) > 0) {
      ElMessage.success(`消息已加入定时发送，目标 ${Number(result?.scheduledCount || 0)} 人`)
    } else {
      ElMessage.success(`消息已发送，触达 ${Number(result?.sentCount || 0)} 人`)
    }
    sendForm.templateKey = ''
    await reloadHistoryAndInbox()
  } catch (error) {
    ElMessage.error(String(error?.response?.data?.message || error?.message || '消息发送失败'))
  } finally {
    sendSubmitting.value = false
  }
}

async function handleRecall(row) {
  const traceId = String(row?.traceId || '').trim()
  if (!traceId || row?.status === 'RECALLED' || actingTraceId.value) {
    return
  }
  try {
    await ElMessageBox.confirm(
      '撤回后，未读消息将不再作为有效消息展示；已读消息不会回滚。',
      '确认撤回发送',
      {
        type: 'warning',
        confirmButtonText: '确认撤回',
        cancelButtonText: '取消',
      },
    )
  } catch {
    return
  }

  actingTraceId.value = traceId
  try {
    const result = await recallMessageSendRecord(traceId)
    ElMessage.success(`发送记录已撤回，影响 ${Number(result?.recalledCount || 0)} 条消息`)
    await reloadHistoryAndInbox()
  } catch (error) {
    ElMessage.error(String(error?.response?.data?.message || error?.message || '撤回发送失败'))
  } finally {
    actingTraceId.value = ''
  }
}

onMounted(async () => {
  try {
    await bootstrapPage()
  } catch (error) {
    ElMessage.error(String(error?.response?.data?.message || error?.message || '消息中心初始化失败'))
  }
})
</script>

<template>
  <section class="messages-shell">
    <section class="message-canvas">
      <div class="message-main">
        <el-card class="hero-card" shadow="never">
          <div class="hero-header">
            <div>
              <p class="eyebrow">消息中心</p>
              <h3>消息中心</h3>
              <p class="hero-copy">
                {{ canSendMessages ? '当前账号可发送教学提醒、查看发送历史并执行撤回。' : '在这里统一查看学术通知、AI 学习建议与系统提醒。' }}
              </p>
            </div>
            <div class="hero-meta">
              <el-tag type="danger" effect="dark">未读 {{ unreadCount }}</el-tag>
              <el-tag v-if="canSendMessages" type="success" effect="light">已开通发送权限</el-tag>
            </div>
          </div>
        </el-card>

        <el-card v-if="canSendMessages" class="content-card composer-card" shadow="never">
          <template #header>
            <div class="card-header">
              <div>
                <h4>发送提醒</h4>
                <p>支持定向发送、分群发送和定时发送</p>
              </div>
              <el-button type="primary" :loading="sendSubmitting" @click="handleSendMessage">发送消息</el-button>
            </div>
          </template>

          <div class="send-grid">
            <el-select v-model="sendForm.targetMode" placeholder="发送方式">
              <el-option
                v-for="item in targetModeOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>

            <el-select
              v-model="sendForm.templateKey"
              placeholder="快捷模板"
              @change="(value) => applySendTemplate(String(value || ''))"
            >
              <el-option
                v-for="item in sendTemplateOptions"
                :key="item.value || 'manual'"
                :label="item.label"
                :value="item.value"
              />
            </el-select>

            <el-select v-model="sendForm.category" placeholder="消息分类">
              <el-option
                v-for="item in messageCategoryOptions.filter((option) => option.value)"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>

            <el-date-picker
              v-model="sendForm.sendAt"
              type="datetime"
              value-format="YYYY-MM-DDTHH:mm:ss"
              placeholder="立即发送（可留空）"
              clearable
            />

            <el-input
              v-model="sendForm.title"
              class="span-2"
              maxlength="100"
              show-word-limit
              placeholder="请输入消息标题"
            />

            <el-input
              v-model="sendForm.userIdsText"
              class="span-2"
              type="textarea"
              :rows="3"
              :disabled="sendForm.targetMode === 'cohort'"
              placeholder="多个用户可用换行或逗号分隔"
            />

            <el-select
              v-model="sendForm.examCategoryCode"
              clearable
              :disabled="sendForm.targetMode !== 'cohort'"
              placeholder="报考大类"
            >
              <el-option
                v-for="item in dictionaryState.examCategoryOptions"
                :key="item.examCategoryCode"
                :label="item.examCategoryName"
                :value="item.examCategoryCode"
              />
            </el-select>

            <el-select
              v-model="sendForm.jointExamGroupCode"
              clearable
              :disabled="sendForm.targetMode !== 'cohort'"
              placeholder="联考专业组"
            >
              <el-option
                v-for="item in filteredJointExamGroupOptions"
                :key="item.jointExamGroupCode"
                :label="item.jointExamGroupName"
                :value="item.jointExamGroupCode"
              />
            </el-select>

            <el-select
              v-model="sendForm.subjectCode"
              clearable
              :disabled="sendForm.targetMode !== 'cohort'"
              placeholder="考试科目"
            >
              <el-option
                v-for="item in filteredSubjectCodeOptions"
                :key="item.subjectCode"
                :label="item.subjectName"
                :value="item.subjectCode"
              />
            </el-select>

            <el-input
              v-model="sendForm.content"
              class="span-2"
              type="textarea"
              :rows="4"
              maxlength="1000"
              show-word-limit
              placeholder="请输入消息内容"
            />
          </div>

          <div class="helper-card">
            <p v-if="sendForm.targetMode === 'userIds'">
              当前按用户ID发送{{ selectedUserIdsPreview ? `：${selectedUserIdsPreview}` : '，请输入至少 1 个用户ID。' }}
            </p>
            <p v-else>
              当前按分群发送：{{ selectedExamCategoryLabel || '不限大类' }} / {{ selectedJointExamGroupLabel || '不限专业组' }} / {{ selectedSubjectLabel || '不限科目' }}
            </p>
          </div>
        </el-card>

        <el-card class="content-card inbox-card" shadow="never">
          <template #header>
            <div class="card-header card-header-wrap">
              <div>
                <h4>消息列表</h4>
                <p>按公告、学情警报和 AI 建议聚合展示，支持批量已读和单条处理</p>
              </div>
              <div class="toolbar">
                <el-select
                  v-model="filterModel.readStatus"
                  placeholder="阅读状态"
                  style="width: 140px"
                  @change="onFilterChange"
                >
                  <el-option
                    v-for="item in readStatusOptions"
                    :key="item.value || 'all-status'"
                    :label="item.label"
                    :value="item.value"
                  />
                </el-select>
                <el-button :disabled="selectedMessageIds.length <= 0" @click="handleBatchMarkRead">
                  批量标记已读
                </el-button>
                <el-checkbox
                  v-if="hasVisibleSelectableMessages"
                  :model-value="areAllVisibleMessagesSelected"
                  @change="handleToggleSelectAllVisible"
                >
                  本页全选
                </el-checkbox>
                <el-button text :disabled="selectedMessageIds.length <= 0" @click="clearSelectedMessages">
                  清空选择
                </el-button>
                <el-button :loading="tableLoading" @click="reloadInbox">刷新</el-button>
              </div>
            </div>
          </template>

          <el-tabs v-model="activeMessageTab" class="message-tabs">
            <el-tab-pane
              v-for="tab in messageTabCards"
              :key="tab.key"
              :name="tab.key"
            >
              <template #label>
                <div class="message-tab-label">
                  <el-icon><component :is="tab.icon" /></el-icon>
                  <span>{{ tab.label }}</span>
                  <em>{{ tab.count }}</em>
                </div>
              </template>

              <div class="tab-intro-card" :class="`is-${tab.accent}`">
                <div class="tab-intro-main">
                  <div class="message-icon-chip" :class="`is-${tab.accent}`">
                    <el-icon><component :is="tab.icon" /></el-icon>
                  </div>
                  <div>
                    <strong>{{ tab.label }}</strong>
                    <p>{{ tab.helper }}</p>
                  </div>
                </div>
                <div class="tab-intro-meta">
                  <span>{{ selectedMessageCountLabel }}</span>
                  <span>当前未读 {{ unreadCount }} 条</span>
                </div>
              </div>

              <div v-loading="tableLoading" class="message-card-stack">
                <el-empty
                  v-if="pagedMessageRows.length === 0"
                  :description="`当前没有${tab.label}消息`"
                />

                <template v-else>
                  <article
                    v-for="row in pagedMessageRows"
                    :key="row.messageId"
                    class="message-card"
                    :class="[
                      `is-${resolveMessageVisual(row).accent}`,
                      { 'is-unread': !row?.isRead, 'is-recalled': row?.isRecalled },
                    ]"
                  >
                    <div class="message-card-layout">
                      <div class="message-card-side">
                        <div class="message-icon-chip" :class="`is-${resolveMessageVisual(row).accent}`">
                          <el-icon><component :is="resolveMessageVisual(row).icon" /></el-icon>
                        </div>
                      </div>

                      <div class="message-card-main">
                        <div class="message-card-header">
                          <div class="message-chip-row">
                            <el-checkbox
                              v-if="canSelectMessageRow(row)"
                              :model-value="isMessageSelected(row?.messageId)"
                              @change="(checked) => toggleMessageSelection(row, checked)"
                            />
                            <el-tag size="small" effect="plain" :type="resolveMessageVisual(row).tagType">
                              {{ resolveMessageVisual(row).label }}
                            </el-tag>
                            <el-tag size="small" :type="row?.isRead ? 'info' : 'danger'">
                              {{ row?.isRead ? '已读' : '未读' }}
                            </el-tag>
                            <el-tag v-if="row?.isRecalled" size="small" type="warning">已撤回</el-tag>
                            <el-tag size="small" effect="plain">
                              {{ formatCategoryLabel(row?.category) }}
                            </el-tag>
                          </div>
                          <span class="message-time">{{ formatDateTime(row?.createTime) }}</span>
                        </div>

                        <strong class="message-card-title">{{ row?.title || '未命名消息' }}</strong>
                        <p class="message-card-content">{{ String(row?.content || '-') }}</p>

                        <div class="message-meta-row">
                          <span>发送人 {{ String(row?.senderUserId || '系统') }}</span>
                          <span>{{ tab.label }}</span>
                          <span v-if="row?.isRecalled" class="muted-text">该消息已撤回</span>
                        </div>

                        <div class="message-action-row">
                          <el-button
                            v-if="!row?.isRead && !row?.isRecalled"
                            link
                            type="primary"
                            :loading="actingMessageId === row?.messageId"
                            @click="handleMarkRead(row)"
                          >
                            标记已读
                          </el-button>
                          <el-button v-if="resolveMessageTabKey(row) !== 'announcement'" link>
                            立即处理
                          </el-button>
                          <span v-if="row?.isRead || row?.isRecalled" class="muted-text">
                            {{ row?.isRecalled ? '已撤回' : '无需处理' }}
                          </span>
                        </div>
                      </div>
                    </div>
                  </article>
                </template>
              </div>
            </el-tab-pane>
          </el-tabs>

          <el-pagination
            background
            class="table-pagination"
            layout="total, prev, pager, next"
            :total="inboxTotal"
            :page-size="pagination.size"
            :current-page="pagination.page"
            @current-change="onInboxPageChange"
          />
        </el-card>
      </div>

      <aside class="message-sidebar">
        <el-card class="content-card settings-card" shadow="never">
          <template #header>
            <div class="card-header">
              <div>
                <h4>推送设置</h4>
                <p>按个人维度控制各类消息是否接收</p>
              </div>
              <el-button type="primary" :loading="settingsSaving" @click="handleSaveSettings">保存设置</el-button>
            </div>
          </template>

          <div class="switch-grid">
            <div class="switch-row">
              <div>
                <strong>AI 实时提醒</strong>
                <p>当 AI 检测到学习异常或瓶颈时通知我</p>
              </div>
              <el-switch v-model="settingsModel.allowAiTutor" />
            </div>
            <div class="switch-row">
              <div>
                <strong>系统重要公告</strong>
                <p>接收维护及重大功能更新通知</p>
              </div>
              <el-switch v-model="settingsModel.allowSystemNotice" />
            </div>
            <div class="switch-row">
              <div>
                <strong>学习提醒</strong>
                <p>接收每日打卡和任务推进提醒</p>
              </div>
              <el-switch v-model="settingsModel.allowStudyReminder" />
            </div>
            <div class="switch-row">
              <div>
                <strong>每周学习周报</strong>
                <p>每周日生成数据总结推送</p>
              </div>
              <el-switch v-model="settingsModel.allowWeeklyReport" />
            </div>
          </div>
        </el-card>

        <article class="status-card">
          <div class="status-card__content">
            <h4>学习状态</h4>
            <div class="status-card__headline">
              <strong>{{ unreadCount }}</strong>
              <span>条未读消息</span>
            </div>
            <p>保持关注，不错过任何学习建议。</p>
            <div class="status-progress">
              <span :style="{ width: `${handledMessagePercent}%` }" />
            </div>
            <small>已处理消息 {{ handledMessagePercent }}%</small>
          </div>
        </article>

        <article class="support-card">
          <strong>遇到问题了？</strong>
          <p>如果您无法接收消息，请尝试检查浏览器通知权限或联系在线导师。</p>
          <button type="button" class="support-link">联系客服</button>
        </article>
      </aside>
    </section>

    <el-card v-if="canSendMessages" class="content-card" shadow="never">
      <template #header>
        <div class="card-header">
          <div>
            <h4>发送历史</h4>
            <p>查看发送结果、定时状态与撤回记录</p>
          </div>
          <el-button :loading="historyLoading" @click="loadSendHistory">刷新历史</el-button>
        </div>
      </template>

      <el-table v-loading="historyLoading" :data="sendHistoryRows" border row-key="traceId">
        <el-table-column prop="title" label="标题" min-width="180" />
        <el-table-column label="分类" width="120">
          <template #default="{ row }">
            {{ formatCategoryLabel(row?.category) }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="formatHistoryStatusType(row?.status)" size="small">
              {{ String(row?.status || '-') }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="目标人数" width="110">
          <template #default="{ row }">
            {{ Number(row?.targetCount || 0) }}
          </template>
        </el-table-column>
        <el-table-column label="发送方式" width="120">
          <template #default="{ row }">
            {{ formatTargetModeLabel(row?.targetMode) }}
          </template>
        </el-table-column>
        <el-table-column label="发送时间" width="170">
          <template #default="{ row }">
            {{ formatDateTime(row?.sendAt) }}
          </template>
        </el-table-column>
        <el-table-column label="撤回时间" width="170">
          <template #default="{ row }">
            {{ formatDateTime(row?.recalledAt) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row?.status !== 'RECALLED'"
              link
              type="danger"
              :loading="actingTraceId === row?.traceId"
              @click="handleRecall(row)"
            >
              撤回发送
            </el-button>
            <span v-else class="muted-text">已撤回</span>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        background
        class="table-pagination"
        layout="total, prev, pager, next"
        :total="historyPagination.total"
        :page-size="historyPagination.size"
        :current-page="historyPagination.page"
        @current-change="onHistoryPageChange"
      />
    </el-card>

  </section>
</template>

<style scoped>
.messages-shell {
  display: grid;
  gap: 18px;
}

.hero-card,
.content-card {
  border: 1px solid var(--qb-border-muted);
  border-radius: 24px;
  box-shadow: 0 14px 36px rgba(15, 23, 42, 0.05);
}

.hero-header,
.card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.hero-header h3,
.hero-header p,
.card-header h4,
.card-header p {
  margin: 0;
}

.hero-header h3 {
  font-size: 30px;
}

.eyebrow {
  margin-bottom: 6px;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.04em;
  color: var(--qb-primary-student);
}

.hero-copy,
.card-header p,
.muted-text {
  color: var(--qb-text-subtle-3);
}

.hero-card {
  background:
    radial-gradient(circle at top right, rgba(59, 130, 246, 0.14), transparent 24%),
    linear-gradient(145deg, rgba(255, 255, 255, 0.98), rgba(239, 246, 255, 0.98));
}

.hero-meta,
.toolbar,
.list-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.message-canvas {
  display: grid;
  grid-template-columns: minmax(0, 1.7fr) minmax(320px, 0.9fr);
  gap: 18px;
}

.message-main,
.message-sidebar {
  display: grid;
  gap: 18px;
}

.switch-grid,
.send-grid {
  display: grid;
  gap: 12px;
}

.switch-grid {
  grid-template-columns: 1fr;
}

.switch-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 16px;
  border: 1px solid var(--qb-border-muted);
  border-radius: 18px;
  background: linear-gradient(180deg, rgba(248, 250, 252, 0.92) 0%, rgba(255, 255, 255, 0.98) 100%);
}

.switch-row strong,
.switch-row p {
  display: block;
  margin: 0;
}

.switch-row p {
  margin-top: 4px;
  font-size: 12px;
  color: var(--qb-text-subtle-3);
}

.send-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.span-2 {
  grid-column: span 2;
}

.helper-card {
  margin-top: 12px;
  padding: 12px 14px;
  border-radius: 12px;
  background: var(--qb-primary-soft-bg);
  color: var(--qb-text-heading);
}

.helper-card p {
  margin: 0;
}

.card-header-wrap {
  align-items: center;
  flex-wrap: wrap;
}

.message-tabs :deep(.el-tabs__header) {
  margin-bottom: 16px;
}

.message-tabs :deep(.el-tabs__nav) {
  gap: 8px;
}

.message-tabs :deep(.el-tabs__item) {
  padding: 0 4px;
}

.message-tabs :deep(.el-tabs__active-bar) {
  display: none;
}

.message-tabs :deep(.el-tabs__nav-wrap::after) {
  display: none;
}

.message-tab-label {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 38px;
  padding: 0 14px;
  border-radius: 999px;
  background: rgba(248, 250, 252, 0.98);
  border: 1px solid var(--qb-border-muted);
  font-weight: 600;
}

.message-tab-label em {
  min-width: 22px;
  padding: 2px 7px;
  border-radius: 999px;
  background: var(--qb-bg-muted);
  color: var(--qb-text-secondary);
  font-style: normal;
  font-size: 12px;
  text-align: center;
}

.tab-intro-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 14px;
  padding: 18px 20px;
  border: 1px solid var(--qb-border-muted);
  border-radius: 22px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.98) 0%, var(--qb-bg-muted) 100%);
}

.tab-intro-card.is-alert {
  background: linear-gradient(135deg, rgba(255, 245, 245, 0.98) 0%, rgba(255, 241, 242, 1) 100%);
}

.tab-intro-card.is-ai {
  background: linear-gradient(135deg, rgba(240, 253, 250, 0.98) 0%, rgba(236, 253, 243, 1) 100%);
}

.tab-intro-main,
.tab-intro-meta,
.message-card-header,
.message-card-layout,
.message-chip-row,
.message-meta-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.tab-intro-main strong {
  display: block;
  margin-bottom: 4px;
  color: var(--qb-text-heading);
}

.tab-intro-main p,
.tab-intro-meta {
  margin: 0;
  color: var(--qb-text-subtle-3);
}

.tab-intro-meta {
  justify-content: flex-end;
  font-size: 13px;
}

.message-card-stack {
  display: grid;
  gap: 14px;
}

.message-card {
  border: 1px solid var(--qb-border-muted);
  border-radius: 22px;
  padding: 20px;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 252, 0.96));
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

.message-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--qb-shadow-card);
}

.message-card.is-unread {
  border-color: var(--qb-primary-soft-border);
  box-shadow: 0 10px 26px rgba(37, 99, 235, 0.08);
}

.message-card.is-alert.is-unread {
  border-color: var(--qb-danger-soft-border);
}

.message-card.is-ai.is-unread {
  border-color: color-mix(in srgb, var(--qb-success) 35%, var(--qb-border-muted) 65%);
}

.message-card-layout {
  align-items: flex-start;
}

.message-card-side {
  display: grid;
  justify-items: center;
  gap: 12px;
  min-width: 56px;
}

.message-icon-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 999px;
  background: var(--qb-primary-soft-bg);
  color: var(--el-color-primary);
  font-size: 20px;
}

.message-icon-chip.is-alert {
  background: var(--qb-danger-soft-bg);
  color: var(--qb-danger-strong);
}

.message-icon-chip.is-ai {
  background: var(--qb-success-soft-bg);
  color: var(--qb-success);
}

.message-card-main {
  flex: 1;
  min-width: 0;
}

.message-card-header {
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
}

.message-time {
  color: var(--qb-text-subtle-3);
  font-size: 12px;
  white-space: nowrap;
}

.message-card-title {
  display: block;
  margin-bottom: 8px;
  font-size: 18px;
  line-height: 1.4;
  color: var(--qb-text-heading);
}

.message-card-content {
  margin: 0 0 12px;
  color: var(--qb-text-secondary);
  line-height: 1.65;
  white-space: pre-wrap;
}

.message-meta-row {
  color: var(--qb-text-subtle-3);
  font-size: 13px;
}

.message-action-row {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
  margin-top: 12px;
}

.message-select-placeholder {
  color: var(--qb-text-subtle-5);
  font-size: 12px;
}

.status-card {
  position: relative;
  overflow: hidden;
  padding: 28px;
  border-radius: 24px;
  background:
    radial-gradient(circle at 78% 26%, rgba(255, 255, 255, 0.16), transparent 20%),
    linear-gradient(145deg, var(--qb-primary-600), var(--qb-text-info-ink));
  color: var(--qb-text-inverse);
  box-shadow: var(--qb-shadow-accent);
}

.status-card__content {
  position: relative;
  z-index: 1;
  display: grid;
  gap: 14px;
}

.status-card__content h4,
.status-card__content p,
.status-card__content small {
  margin: 0;
}

.status-card__headline {
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.status-card__headline strong {
  font-size: 42px;
  line-height: 1;
}

.status-card__content p,
.status-card__content small {
  color: rgba(219, 234, 254, 0.9);
}

.status-progress {
  position: relative;
  height: 8px;
  border-radius: 999px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.18);
}

.status-progress span {
  position: absolute;
  inset: 0 auto 0 0;
  border-radius: inherit;
  background: linear-gradient(90deg, rgba(111, 251, 190, 0.98), rgba(255, 255, 255, 0.96));
}

.support-card {
  padding: 20px;
  border-radius: 24px;
  border: 1px solid var(--qb-border-muted);
  background: rgba(246, 248, 251, 0.94);
  display: grid;
  gap: 10px;
}

.support-card strong,
.support-card p {
  margin: 0;
}

.support-link {
  width: fit-content;
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--qb-primary-student);
  font-weight: 700;
  cursor: pointer;
}

.table-pagination {
  margin-top: 14px;
  justify-content: flex-end;
}

@media (max-width: 1080px) {
  .message-canvas,
  .send-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .span-2 {
    grid-column: span 1;
  }

  .tab-intro-card,
  .message-card-layout,
  .message-card-header {
    flex-direction: column;
    align-items: flex-start;
  }
}

@media (max-width: 720px) {
  .message-card-side {
    min-width: 48px;
  }

  .message-card-layout {
    gap: 10px;
  }

  .message-card-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .tab-intro-meta {
    justify-content: flex-start;
  }

  .hero-header,
  .card-header {
    flex-direction: column;
  }
}
</style>
