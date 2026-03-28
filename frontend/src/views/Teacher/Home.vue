<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  Bell,
  DataAnalysis,
  DocumentChecked,
  Reading,
  RefreshRight,
} from '@/ui/icons'
import { ElMessage } from '@/ui/feedback'
import {
  fetchAnalyticsSummary,
  fetchMessageUnreadSummary,
  fetchQuestionList,
  paperOverview,
} from '../../api/services/questionBank'
import { useUserStore } from '../../stores/userStore.js'
import { normalizeAnalyticsSummary } from '../../utils/analyticsSummary'
import { buildContentLabelMaps, resolveContentLabel } from '../../utils/contentBaseline.js'

const router = useRouter()
const userStore = useUserStore()

const loading = ref(true)
const refreshing = ref(false)
const metrics = reactive({
  pendingQuestionCount: 0,
  publishedPaperCount: 0,
  unreadMessageCount: 0,
  coverageRate: 0,
  averageAccuracy: 0,
  atRiskStudentCount: 0,
  aiReport: '',
  weakestKnowledgeTag: '',
  chapterRiskLabel: '',
})

const canManageQuestions = computed(() => userStore.hasPermission('question:manage'))
const canManagePapers = computed(() => userStore.hasPermission('paper:manage'))
const canViewAnalytics = computed(() => userStore.hasPermission('analytics:view'))
const canManageStudents = computed(() => userStore.hasPermission('student:manage'))
const assignedJointGroupCode = computed(() =>
  String(userStore.assigned_joint_group_code || userStore.jointExamGroupCode || '').trim(),
)
const scopeLabelMaps = computed(() => buildContentLabelMaps(userStore.availableExamCategories))
const assignedJointGroupLabel = computed(() =>
  resolveContentLabel(scopeLabelMaps.value.jointExamGroupNameMap, assignedJointGroupCode.value),
)

const scopeDescription = computed(() =>
  assignedJointGroupCode.value
    ? `当前账号已绑定专业组 ${assignedJointGroupLabel.value}，首页统计按该范围实时收敛。`
    : '当前账号未绑定单一专业组，首页统计展示你有权访问的全量教师范围。',
)

const capabilityTags = computed(() => ([
  {
    key: 'question:manage',
    label: '题库管理',
    enabled: canManageQuestions.value,
  },
  {
    key: 'paper:manage',
    label: '试卷管理',
    enabled: canManagePapers.value,
  },
  {
    key: 'analytics:view',
    label: '学情查看',
    enabled: canViewAnalytics.value,
  },
  {
    key: 'student:manage',
    label: '学生开通',
    enabled: canManageStudents.value,
  },
]))

const cardItems = computed(() => ([
  {
    key: 'pending-questions',
    title: '待终审题目',
    value: metrics.pendingQuestionCount,
    unit: '题',
    icon: Reading,
    accent: 'is-primary',
    hint: canManageQuestions.value
      ? '来自题库管理真实状态：REVIEW_PENDING。'
      : '当前账号未开通题库管理权限。',
    actionText: canManageQuestions.value ? '去处理' : '权限未开通',
    disabled: !canManageQuestions.value,
    path: '/teacher/questions',
  },
  {
    key: 'published-papers',
    title: '已发布试卷',
    value: metrics.publishedPaperCount,
    unit: '份',
    icon: DocumentChecked,
    accent: 'is-success',
    hint: canManagePapers.value
      ? '来自试卷概览真实状态：PUBLISHED。'
      : '当前账号未开通试卷管理权限。',
    actionText: canManagePapers.value ? '查看试卷' : '权限未开通',
    disabled: !canManagePapers.value,
    path: '/teacher/papers',
  },
  {
    key: 'unread-messages',
    title: '未读教学消息',
    value: metrics.unreadMessageCount,
    unit: '条',
    icon: Bell,
    accent: 'is-warning',
    hint: '来自消息中心未读统计，可直接回到教学触达入口处理。',
    actionText: '打开消息',
    disabled: false,
    path: '/messages',
  },
  {
    key: 'coverage-rate',
    title: '班级覆盖率',
    value: `${Math.round(metrics.coverageRate * 100)}%`,
    unit: '',
    icon: DataAnalysis,
    accent: 'is-analytics',
    hint: canViewAnalytics.value
      ? `平均正确率 ${Math.round(metrics.averageAccuracy * 100)}%，待干预学生 ${metrics.atRiskStudentCount} 人。`
      : '当前账号未开通学情查看权限。',
    actionText: canViewAnalytics.value ? '查看学情' : '权限未开通',
    disabled: !canViewAnalytics.value,
    path: '/teacher/analytics',
  },
]))

const quickActions = computed(() => ([
  {
    key: 'question-center',
    title: '题库管理',
    desc: '进入真实题库列表，处理终审与状态流转。',
    path: '/teacher/questions',
    enabled: canManageQuestions.value,
  },
  {
    key: 'paper-center',
    title: '组卷中心',
    desc: '查看试卷概览，继续人工组卷或 AI 组卷。',
    path: '/teacher/papers',
    enabled: canManagePapers.value,
  },
  {
    key: 'message-center',
    title: '消息中心',
    desc: '回到教学消息与发送历史，处理未读提醒。',
    path: '/messages',
    enabled: true,
  },
  {
    key: 'student-account-center',
    title: '学生账号开通',
    desc: '开通、停用学生账号，并维护考生基础信息。',
    path: '/teacher/student-accounts',
    enabled: canManageStudents.value,
  },
  {
    key: 'analytics-center',
    title: '学情管理',
    desc: '查看覆盖率、正确率与待干预学生。',
    path: '/teacher/analytics',
    enabled: canViewAnalytics.value,
  },
].filter((item) => item.enabled)))

const aiReportSummary = computed(() => {
  const raw = String(metrics.aiReport || '').trim()
  if (raw) {
    return raw
  }
  if (!canViewAnalytics.value) {
    return '当前账号没有学情查看权限，无法生成班级干预摘要。'
  }
  return '当前暂无可生成的班级干预摘要。'
})

function unwrapData(response) {
  if (response && typeof response === 'object' && 'data' in response) {
    return response.data
  }
  return response
}

async function loadPendingQuestions() {
  if (!canManageQuestions.value) {
    metrics.pendingQuestionCount = 0
    return
  }
  const pageData = await fetchQuestionList({
    page: 1,
    size: 1,
    status: 'REVIEW_PENDING',
  })
  metrics.pendingQuestionCount = Number(pageData?.total || 0)
}

async function loadPaperSnapshot() {
  if (!canManagePapers.value) {
    metrics.publishedPaperCount = 0
    return
  }
  const response = await paperOverview()
  const rows = Array.isArray(unwrapData(response)) ? unwrapData(response) : []
  metrics.publishedPaperCount = rows.filter(
    (item) => String(item?.paperStatus || '').trim() === 'PUBLISHED',
  ).length
}

async function loadUnreadMessages() {
  const messageSummary = await fetchMessageUnreadSummary()
  metrics.unreadMessageCount = Number(messageSummary?.totalUnread || 0)
}

async function loadAnalyticsSnapshot() {
  if (!canViewAnalytics.value) {
    metrics.coverageRate = 0
    metrics.averageAccuracy = 0
    metrics.atRiskStudentCount = 0
    metrics.aiReport = ''
    metrics.weakestKnowledgeTag = ''
    metrics.chapterRiskLabel = ''
    return
  }
  const summary = normalizeAnalyticsSummary(await fetchAnalyticsSummary({}))
  metrics.coverageRate = Number(summary.coverageRate || 0)
  metrics.averageAccuracy = Number(summary.averageAccuracy || 0)
  metrics.atRiskStudentCount = Number(summary.atRiskStudentCount || 0)
  metrics.aiReport = String(summary.aiReport || '').trim()
  metrics.weakestKnowledgeTag = String(summary.weakKnowledgeTags?.[0]?.knowledgeTag || '').trim()
  metrics.chapterRiskLabel = String(summary.chapterRankings?.[0]?.chapter || '').trim()
}

async function loadDashboard() {
  const loaders = [
    loadPendingQuestions(),
    loadPaperSnapshot(),
    loadUnreadMessages(),
    loadAnalyticsSnapshot(),
  ]
  const results = await Promise.allSettled(loaders)
  const firstRejected = results.find((item) => item.status === 'rejected')
  if (firstRejected?.status === 'rejected') {
    throw firstRejected.reason
  }
}

async function refreshDashboard() {
  if (refreshing.value) {
    return
  }
  refreshing.value = true
  try {
    await loadDashboard()
  } catch (error) {
    ElMessage.error(String(error?.response?.data?.message || error?.message || '教师工作台加载失败'))
  } finally {
    loading.value = false
    refreshing.value = false
  }
}

function openPath(path) {
  if (!String(path || '').trim()) {
    return
  }
  router.push(path)
}

onMounted(async () => {
  await refreshDashboard()
})
</script>

<template>
  <section class="page-shell">
    <el-card class="hero-card" shadow="never">
      <div class="hero-top">
        <div>
          <p class="eyebrow">Teacher Real Entry</p>
          <h3>教师工作台</h3>
          <p class="hero-copy">{{ scopeDescription }}</p>
        </div>
        <el-button type="primary" :icon="RefreshRight" :loading="refreshing" @click="refreshDashboard">
          刷新首页
        </el-button>
      </div>

      <div class="capability-row">
        <el-tag
          v-for="tag in capabilityTags"
          :key="tag.key"
          :type="tag.enabled ? 'success' : 'info'"
          effect="light"
        >
          {{ tag.label }}{{ tag.enabled ? '已开通' : '未开通' }}
        </el-tag>
      </div>
    </el-card>

    <section v-if="loading" class="kpi-grid">
      <el-card v-for="index in 4" :key="`kpi-skeleton-${index}`" class="kpi-card" shadow="never">
        <el-skeleton animated>
          <template #template>
            <div class="skeleton-block">
              <el-skeleton-item class="skeleton-title" variant="text" />
              <el-skeleton-item class="skeleton-value" variant="h1" />
              <el-skeleton-item class="skeleton-copy" variant="text" />
            </div>
          </template>
        </el-skeleton>
      </el-card>
    </section>

    <section v-else class="kpi-grid">
      <article
        v-for="card in cardItems"
        :key="card.key"
        class="kpi-card"
        :class="card.accent"
      >
        <div class="kpi-head">
          <span class="kpi-icon">
            <el-icon>
              <component :is="card.icon" />
            </el-icon>
          </span>
          <span class="kpi-title">{{ card.title }}</span>
        </div>
        <div class="kpi-value-row">
          <strong>{{ card.value }}</strong>
          <span v-if="card.unit" class="kpi-unit">{{ card.unit }}</span>
        </div>
        <p class="kpi-hint">{{ card.hint }}</p>
        <el-button text :disabled="card.disabled" @click="openPath(card.path)">
          {{ card.actionText }}
        </el-button>
      </article>
    </section>

    <section class="insight-grid">
      <el-card class="insight-card" shadow="never">
        <template #header>
          <div class="section-head">
            <h4>教学干预摘要</h4>
            <span>真实数据快照</span>
          </div>
        </template>
        <p class="insight-copy">{{ aiReportSummary }}</p>
        <div class="insight-meta">
          <article>
            <span>高风险章节</span>
            <strong>{{ metrics.chapterRiskLabel || '暂无' }}</strong>
          </article>
          <article>
            <span>薄弱知识点</span>
            <strong>{{ metrics.weakestKnowledgeTag || '暂无' }}</strong>
          </article>
        </div>
      </el-card>

      <el-card class="insight-card quick-card" shadow="never">
        <template #header>
          <div class="section-head">
            <h4>快捷入口</h4>
            <span>按权限展示</span>
          </div>
        </template>
        <div class="quick-grid">
          <button
            v-for="item in quickActions"
            :key="item.key"
            type="button"
            class="quick-action"
            @click="openPath(item.path)"
          >
            <span class="quick-title">{{ item.title }}</span>
            <span class="quick-desc">{{ item.desc }}</span>
            <span class="quick-link">立即进入</span>
          </button>
        </div>
      </el-card>
    </section>
  </section>
</template>

<style scoped>
.page-shell {
  display: grid;
  gap: 16px;
}

.hero-card,
.kpi-card,
.insight-card {
  border-color: var(--qb-primary-soft-border);
}

.hero-card {
  background:
    radial-gradient(circle at top right, rgba(34, 197, 94, 0.15), transparent 34%),
    linear-gradient(135deg, rgba(15, 118, 110, 0.08), rgba(255, 255, 255, 0.95));
}

.hero-top {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
}

.eyebrow {
  margin: 0 0 8px;
  color: var(--qb-text-subtle-7);
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

h3,
h4,
p {
  margin: 0;
}

h3 {
  font-size: 28px;
  color: var(--qb-text-heading);
}

.hero-copy {
  margin-top: 8px;
  max-width: 760px;
  color: var(--qb-text-subtle-7);
  line-height: 1.6;
}

.capability-row {
  margin-top: 14px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.kpi-grid {
  display: grid;
  gap: 14px;
  grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
}

.kpi-card {
  display: grid;
  gap: 12px;
  padding: 18px;
  border-radius: 18px;
  background: linear-gradient(180deg, var(--qb-bg-card), rgba(255, 255, 255, 0.9));
}

.kpi-card.is-primary {
  box-shadow: inset 0 0 0 1px rgba(59, 130, 246, 0.12);
}

.kpi-card.is-success {
  box-shadow: inset 0 0 0 1px rgba(34, 197, 94, 0.12);
}

.kpi-card.is-warning {
  box-shadow: inset 0 0 0 1px rgba(245, 158, 11, 0.16);
}

.kpi-card.is-analytics {
  box-shadow: inset 0 0 0 1px rgba(15, 118, 110, 0.14);
}

.kpi-head {
  display: flex;
  align-items: center;
  gap: 10px;
}

.kpi-icon {
  width: 38px;
  height: 38px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.95);
  color: var(--el-color-primary);
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
}

.kpi-title {
  color: var(--qb-text-subtle-8);
  font-size: 14px;
}

.kpi-value-row {
  display: flex;
  align-items: flex-end;
  gap: 6px;
}

.kpi-value-row strong {
  font-size: 34px;
  line-height: 1;
  color: var(--qb-text-heading);
}

.kpi-unit {
  color: var(--qb-text-subtle-7);
  padding-bottom: 4px;
}

.kpi-hint {
  min-height: 38px;
  color: var(--qb-text-subtle-7);
  line-height: 1.5;
  font-size: 13px;
}

.insight-grid {
  display: grid;
  gap: 14px;
  grid-template-columns: minmax(0, 1.15fr) minmax(0, 0.85fr);
}

.section-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: baseline;
}

.section-head h4 {
  color: var(--qb-text-heading);
  font-size: 17px;
}

.section-head span {
  color: var(--qb-text-subtle-6);
  font-size: 12px;
}

.insight-copy {
  color: var(--qb-text-subtle-8);
  line-height: 1.7;
}

.insight-meta {
  margin-top: 16px;
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.insight-meta article {
  padding: 14px;
  border-radius: 14px;
  background: linear-gradient(180deg, var(--qb-primary-soft-bg), rgba(255, 255, 255, 0.9));
  display: grid;
  gap: 8px;
}

.insight-meta span {
  color: var(--qb-text-subtle-6);
  font-size: 12px;
}

.insight-meta strong {
  color: var(--qb-text-heading);
  line-height: 1.5;
}

.quick-grid {
  display: grid;
  gap: 10px;
}

.quick-action {
  border: 1px solid var(--qb-primary-soft-border);
  border-radius: 16px;
  padding: 14px 16px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), var(--qb-primary-soft-bg));
  display: grid;
  gap: 8px;
  text-align: left;
  cursor: pointer;
  transition: transform 0.16s ease, box-shadow 0.16s ease, border-color 0.16s ease;
}

.quick-action:hover {
  transform: translateY(-1px);
  border-color: rgba(15, 118, 110, 0.24);
  box-shadow: 0 12px 26px rgba(15, 23, 42, 0.08);
}

.quick-title {
  color: var(--qb-text-heading);
  font-weight: 600;
}

.quick-desc {
  color: var(--qb-text-subtle-7);
  line-height: 1.5;
  font-size: 13px;
}

.quick-link {
  color: var(--el-color-primary);
  font-size: 13px;
}

.skeleton-block {
  display: grid;
  gap: 12px;
}

.skeleton-title {
  width: 46%;
}

.skeleton-value {
  width: 34%;
}

.skeleton-copy {
  width: 74%;
}

@media (max-width: 1024px) {
  .insight-grid {
    grid-template-columns: minmax(0, 1fr);
  }
}

@media (max-width: 720px) {
  .hero-top {
    flex-direction: column;
    align-items: stretch;
  }

  .insight-meta {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
