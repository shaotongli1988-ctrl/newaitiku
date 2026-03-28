<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from '@/ui/feedback'
import { useRoute, useRouter } from 'vue-router'
import {
  listStudentExamTasks,
  startStudentExamTask,
} from '../../api/services/questionBank.js'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const rows = ref([])
const filters = reactive({
  status: '',
})

const currentSubjectCode = computed(() => String(route.query.subjectCode || '').trim())
const currentSubjectLabel = computed(() => currentSubjectCode.value || '未选择科目')
const activeTaskCount = computed(() =>
  rows.value.filter((item) => ['NOT_STARTED', 'IN_PROGRESS', 'SUBMITTED', 'PENDING_REVIEW'].includes(toText(item?.effectiveStatus))).length,
)
const completedTaskCount = computed(() =>
  rows.value.filter((item) => toText(item?.effectiveStatus) === 'COMPLETED').length,
)
const overdueTaskCount = computed(() =>
  rows.value.filter((item) => toText(item?.effectiveStatus) === 'EXPIRED').length,
)
const heroSummary = computed(() => {
  if (!rows.value.length) {
    return `当前科目 ${currentSubjectLabel.value} 还没有老师下发的考试任务，可以先去知识诊断定方向，或者先刷题把段位分稳稳拉起来。`
  }
  if (overdueTaskCount.value > 0) {
    return `当前共有 ${rows.value.length} 项老师任务，其中 ${overdueTaskCount.value} 项已过期。先把老师明确要求的动作接回今天的执行节奏，再去刷题冲分，整体提分会更稳。`
  }
  if (activeTaskCount.value > 0) {
    return `当前共有 ${rows.value.length} 项老师任务，其中 ${activeTaskCount.value} 项还在推进中。老师任务不是另一套系统，它会和你的今日任务、刷题段位一起决定这门课能不能稳定拿分。`
  }
  return `当前共有 ${rows.value.length} 项老师任务，已完成 ${completedTaskCount.value} 项。继续回看关键任务或转去刷题段位，更容易把老师布置的要求沉淀成稳定正确输出。`
})

const statusOptions = [
  { label: '全部状态', value: '' },
  { label: '未开始', value: 'NOT_STARTED' },
  { label: '进行中', value: 'IN_PROGRESS' },
  { label: '已提交', value: 'SUBMITTED' },
  { label: '待批改', value: 'PENDING_REVIEW' },
  { label: '已完成', value: 'COMPLETED' },
  { label: '已过期', value: 'EXPIRED' },
]

function toText(value) {
  return String(value || '').trim()
}

function statusLabel(status) {
  return {
    NOT_STARTED: '未开始',
    IN_PROGRESS: '进行中',
    SUBMITTED: '已提交',
    PENDING_REVIEW: '待批改',
    COMPLETED: '已完成',
    EXPIRED: '已过期',
  }[toText(status)] || '未知状态'
}

function statusTagType(status) {
  return {
    NOT_STARTED: 'info',
    IN_PROGRESS: 'warning',
    SUBMITTED: '',
    PENDING_REVIEW: 'warning',
    COMPLETED: 'success',
    EXPIRED: 'danger',
  }[toText(status)] || 'info'
}

function progressLabel(row) {
  const ext = row?.extJson && typeof row.extJson === 'object' ? row.extJson : {}
  const completed = Number(ext?.progressCount || 0)
  const target = Number(ext?.targetQuestionCount || 0)
  if (!target) {
    return '-'
  }
  return `${completed} / ${target}`
}

function formatDateTime(value) {
  const normalized = toText(value)
  if (!normalized) {
    return '-'
  }
  return normalized.replace('T', ' ').replace('Z', '')
}

async function loadRows() {
  loading.value = true
  try {
    const response = await listStudentExamTasks({
      page: 1,
      size: 100,
      status: filters.status,
      subjectCode: currentSubjectCode.value,
    })
    const payload = response?.data?.items ? response.data : response?.data || response || {}
    rows.value = Array.isArray(payload?.items) ? payload.items : []
  } catch (error) {
    ElMessage.error(String(error?.response?.data?.message || error?.message || '考试任务加载失败'))
    rows.value = []
  } finally {
    loading.value = false
  }
}

async function handleStart(row) {
  const assignmentId = toText(row?.id)
  if (!assignmentId) {
    return
  }
  try {
    const response = await startStudentExamTask(assignmentId)
    const payload = response?.data || response || {}
    const actionPath = toText(payload?.actionPath)
    const actionQuery = payload?.actionQuery && typeof payload.actionQuery === 'object'
      ? payload.actionQuery
      : {}
    if (!actionPath) {
      ElMessage.warning('当前任务尚未配置跳转目标。')
      return
    }
    await router.push({
      path: actionPath,
      query: actionQuery,
    })
  } catch (error) {
    ElMessage.error(String(error?.response?.data?.message || error?.message || '考试任务启动失败'))
  }
}

async function openChallengePoints() {
  await router.push({
    path: '/student/analysis/points',
    query: currentSubjectCode.value ? { subjectCode: currentSubjectCode.value } : {},
  })
}

async function openKnowledgeDiagnosis() {
  await router.push({
    path: '/student/analysis/overview',
    query: currentSubjectCode.value ? { subjectCode: currentSubjectCode.value } : {},
  })
}

watch(() => route.query.subjectCode, loadRows)
onMounted(loadRows)
</script>

<template>
  <section class="exam-task-page" v-loading="loading">
    <header class="exam-task-page__hero">
      <div class="exam-task-page__hero-copy">
        <p class="exam-task-page__eyebrow">学生端 / 考试任务</p>
        <h2>老师任务要并进同一套提分节奏，不单独悬着</h2>
        <p>{{ heroSummary }}</p>
        <div class="exam-task-page__hero-meta">
          <span>当前科目：{{ currentSubjectLabel }}</span>
          <span>待推进 {{ activeTaskCount }} 项</span>
          <span>已完成 {{ completedTaskCount }} 项</span>
        </div>
        <div class="exam-task-page__hero-actions">
          <el-button type="primary" plain @click="openChallengePoints">看刷题段位</el-button>
          <el-button plain @click="openKnowledgeDiagnosis">回知识诊断</el-button>
        </div>
      </div>
      <el-select v-model="filters.status" class="exam-task-page__filter" placeholder="筛选状态" @change="loadRows">
        <el-option
          v-for="item in statusOptions"
          :key="item.value || 'all'"
          :label="item.label"
          :value="item.value"
        />
      </el-select>
    </header>

    <el-empty
      v-if="!rows.length"
      description="当前科目下暂无老师任务，先去知识诊断确认薄弱点，或者先刷题把段位分涨起来。"
    />

    <div v-else class="exam-task-grid">
      <article v-for="row in rows" :key="row.id" class="exam-task-card">
        <div class="exam-task-card__header">
          <div>
            <h3>{{ row?.task?.taskName || '未命名任务' }}</h3>
            <p>{{ row?.task?.teacherName || '任课老师' }}</p>
          </div>
          <el-tag :type="statusTagType(row.effectiveStatus)" effect="light">
            {{ statusLabel(row.effectiveStatus) }}
          </el-tag>
        </div>
        <p class="exam-task-card__desc">
          {{ row?.task?.description || '老师没有补充说明，先按任务入口完成这一步，再把结果继续转成稳定正确输出。' }}
        </p>
        <dl class="exam-task-card__meta">
          <div>
            <dt>截止时间</dt>
            <dd>{{ formatDateTime(row?.task?.dueAt) }}</dd>
          </div>
          <div>
            <dt>得分</dt>
            <dd>{{ Number(row?.score || 0) }} / {{ Number(row?.totalScore || 0) }}</dd>
          </div>
          <div>
            <dt>是否允许重做</dt>
            <dd>{{ row?.task?.allowRedo ? '允许' : '不允许' }}</dd>
          </div>
          <div>
            <dt>任务类型</dt>
            <dd>{{ row?.task?.taskType || '-' }}</dd>
          </div>
          <div>
            <dt>完成进度</dt>
            <dd>{{ progressLabel(row) }}</dd>
          </div>
        </dl>
        <div class="exam-task-card__actions">
          <el-button type="primary" @click="handleStart(row)">
            {{ row.effectiveStatus === 'IN_PROGRESS' ? '继续完成' : row.effectiveStatus === 'COMPLETED' ? '查看或重做' : '开始任务' }}
          </el-button>
        </div>
      </article>
    </div>
  </section>
</template>

<style scoped>
.exam-task-page {
  display: grid;
  gap: 20px;
}

.exam-task-page__hero {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 24px;
  border-radius: 24px;
  background: linear-gradient(135deg, var(--qb-warning-soft-bg) 0%, var(--qb-primary-soft-bg) 100%);
}

.exam-task-page__hero-copy {
  display: grid;
  gap: 10px;
}

.exam-task-page__eyebrow {
  margin: 0 0 8px;
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--qb-text-warning-ink);
}

.exam-task-page__hero h2 {
  margin: 0 0 8px;
  font-size: 24px;
  line-height: 1.4;
}

.exam-task-page__hero p {
  margin: 0;
  color: var(--qb-text-copy);
}

.exam-task-page__hero-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  color: var(--qb-text-meta);
  font-size: 13px;
}

.exam-task-page__hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.exam-task-page__filter {
  width: 180px;
}

.exam-task-grid {
  display: grid;
  gap: 16px;
}

.exam-task-card {
  display: grid;
  gap: 16px;
  padding: 20px;
  border-radius: 20px;
  background: var(--qb-bg-card);
  box-shadow: var(--qb-shadow-panel);
}

.exam-task-card__header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.exam-task-card__header h3 {
  margin: 0 0 6px;
  font-size: 18px;
}

.exam-task-card__header p,
.exam-task-card__desc {
  margin: 0;
  color: var(--qb-text-copy);
}

.exam-task-card__meta {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 12px;
  margin: 0;
}

.exam-task-card__meta dt {
  margin-bottom: 4px;
  font-size: 12px;
  color: var(--qb-text-meta);
}

.exam-task-card__meta dd {
  margin: 0;
  font-weight: 600;
}

.exam-task-card__actions {
  display: flex;
  justify-content: flex-end;
}

@media (max-width: 768px) {
  .exam-task-page__hero {
    flex-direction: column;
  }

  .exam-task-page__filter {
    width: 100%;
  }
}
</style>
