<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from '@/ui/feedback'
import {
  createExamTask,
  fetchQuestionList,
  knowledgeTreeV2,
  listExamTasks,
  listSubjects,
  paperOverview,
} from '../../api/services/questionBank.js'
import { listTeacherPaperClasses } from '../../api/services/papers.js'
import { parseExtJson, questionDifficultyLabel } from '../../utils/question.js'

const loading = ref(false)
const saving = ref(false)
const rows = ref([])
const subjectOptions = ref([])
const classOptions = ref([])
const sourceResourceOptions = ref([])

const createDialogVisible = ref(false)
const filters = reactive({
  status: '',
  taskType: '',
})

const form = reactive({
  task_name: '',
  task_type: 'CHAPTER',
  subject_code: '',
  source_type: 'KNOWLEDGE',
  source_id: '',
  source_label: '',
  description: '',
  allow_redo: false,
  target_question_count: 1,
  due_at: '',
  status: 'PUBLISHED',
  class_ids: [],
})

const taskTypeOptions = [
  { label: '章节练习', value: 'CHAPTER', sourceType: 'KNOWLEDGE' },
  { label: '专项练习', value: 'SPECIAL', sourceType: 'SPECIAL_SET' },
  { label: '模拟卷', value: 'PAPER', sourceType: 'PAPER' },
  { label: '主观题批改任务', value: 'SUBJECTIVE_MARKING', sourceType: 'SUBJECTIVE' },
]

const SUBJECTIVE_OPTION_PAGE_SIZE = 50
const SUBJECTIVE_OPTION_STEM_LENGTH = 72

const statusOptions = [
  { label: '全部状态', value: '' },
  { label: '草稿', value: 'DRAFT' },
  { label: '已发布', value: 'PUBLISHED' },
  { label: '已关闭', value: 'CLOSED' },
]

function toText(value) {
  return String(value || '').trim()
}

function formatDateTime(value) {
  return toText(value).replace('T', ' ').replace('Z', '') || '-'
}

function taskTypeLabel(value) {
  return taskTypeOptions.find((item) => item.value === toText(value))?.label || toText(value) || '-'
}

function statusLabel(value) {
  return {
    DRAFT: '草稿',
    PUBLISHED: '已发布',
    CLOSED: '已关闭',
  }[toText(value)] || '未知状态'
}

function statusTagType(value) {
  return {
    DRAFT: 'info',
    PUBLISHED: 'success',
    CLOSED: 'warning',
  }[toText(value)] || 'info'
}

const sourceFieldLabel = computed(() => {
  const taskType = toText(form.task_type)
  if (taskType === 'PAPER') {
    return '试卷 ID'
  }
  if (taskType === 'SUBJECTIVE_MARKING') {
    return '批改题目'
  }
  return '知识点/资源 ID'
})

const sourceSelectPlaceholder = computed(() => {
  const taskType = toText(form.task_type)
  if (taskType === 'SUBJECTIVE_MARKING') {
    return '请选择要批改的主观题'
  }
  return '请选择关联资源'
})

function normalizePage(response) {
  if (response?.data?.items) {
    return response.data
  }
  if (response?.data) {
    return response.data
  }
  return response || {}
}

function normalizePaperOptions(payload) {
  const rows = Array.isArray(payload) ? payload : []
  return rows
    .map((item) => ({
      value: toText(item?.paperId || item?.id),
      label: `${toText(item?.paperName || item?.id)} · ${Number(item?.questionCount || 0)} 题 · ${Number(item?.totalScore || 0)} 分`,
      meta: item,
    }))
    .filter((item) => item.value)
}

function flattenKnowledgeNodes(treePayload = {}) {
  const nodes = Array.isArray(treePayload?.nodes) ? treePayload.nodes : []
  return nodes
    .map((item) => ({
      value: toText(item?.id),
      label: toText(item?.full_label || item?.fullLabel || item?.label || item?.id),
      level: Number(item?.level || 0),
      meta: item,
    }))
    .filter((item) => item.value && item.level >= 4)
}

function buildSubjectiveQuestionLabel(question = {}) {
  const stem = toText(question?.stem)
  const truncatedStem =
    stem.length > SUBJECTIVE_OPTION_STEM_LENGTH
      ? `${stem.slice(0, SUBJECTIVE_OPTION_STEM_LENGTH)}…`
      : stem || '未命名主观题'
  const extJson = parseExtJson(question?.extJson)
  const difficultyLabel = questionDifficultyLabel(extJson?.difficulty)
  const chapter = toText(extJson?.chapter)
  const metaParts = []
  if (chapter) {
    metaParts.push(chapter)
  }
  if (difficultyLabel && difficultyLabel !== '-') {
    metaParts.push(difficultyLabel)
  }
  const metaLabel = metaParts.join(' · ')
  const baseLabel = metaLabel ? `${metaLabel} · ${truncatedStem}` : truncatedStem
  const questionId = toText(question?.id)
  return questionId ? `${baseLabel}（${questionId}）` : baseLabel
}

function normalizeSubjectiveQuestionOptions(payload = []) {
  const rows = Array.isArray(payload) ? payload : []
  return rows
    .map((item) => ({
      value: toText(item?.id),
      label: buildSubjectiveQuestionLabel(item),
      meta: item,
    }))
    .filter((item) => item.value)
}

async function loadDictionary() {
  try {
    const [subjectResponse, classResponse] = await Promise.all([
      listSubjects(),
      listTeacherPaperClasses(),
    ])
    const subjectPayload = subjectResponse?.data || subjectResponse || []
    subjectOptions.value = Array.isArray(subjectPayload) ? subjectPayload : []
    const classPayload = classResponse?.data || classResponse || []
    classOptions.value = Array.isArray(classPayload) ? classPayload : []
  } catch (error) {
    ElMessage.error(String(error?.response?.data?.message || error?.message || '考试任务字典加载失败'))
  }
}

async function loadSourceResourceOptions() {
  const taskType = toText(form.task_type)
  const subjectCode = toText(form.subject_code)
  sourceResourceOptions.value = []
  if (!taskType || !subjectCode) {
    return
  }
  try {
    if (taskType === 'SUBJECTIVE_MARKING') {
      const pageData = await fetchQuestionList({
        page: 1,
        size: SUBJECTIVE_OPTION_PAGE_SIZE,
        subjectCode,
        type: 'subjective',
        status: 'PUBLISHED',
      })
      const items = Array.isArray(pageData?.items) ? pageData.items : []
      sourceResourceOptions.value = normalizeSubjectiveQuestionOptions(items)
      return
    }
    if (taskType === 'PAPER') {
      const response = await paperOverview()
      const payload = response?.data || response || []
      sourceResourceOptions.value = normalizePaperOptions(payload).filter((item) => {
        const paperStatus = toText(item?.meta?.paperStatus)
        const paperSubjectCode = toText(item?.meta?.subjectCode)
        return paperStatus === 'PUBLISHED' && (!paperSubjectCode || paperSubjectCode === subjectCode)
      })
      return
    }
    if (taskType === 'CHAPTER' || taskType === 'SPECIAL') {
      const response = await knowledgeTreeV2({
        status: 'ENABLED',
        subject_code: subjectCode,
      })
      const payload = response?.data || response || {}
      sourceResourceOptions.value = flattenKnowledgeNodes(payload)
    }
  } catch (error) {
    sourceResourceOptions.value = []
    ElMessage.error(String(error?.response?.data?.message || error?.message || '任务资源选项加载失败'))
  }
}

async function loadRows() {
  loading.value = true
  try {
    const response = await listExamTasks({
      page: 1,
      size: 100,
      status: filters.status,
      taskType: filters.taskType,
    })
    const payload = normalizePage(response)
    rows.value = Array.isArray(payload?.items) ? payload.items : []
  } catch (error) {
    ElMessage.error(String(error?.response?.data?.message || error?.message || '考试任务列表加载失败'))
    rows.value = []
  } finally {
    loading.value = false
  }
}

function resetForm() {
  form.task_name = ''
  form.task_type = 'CHAPTER'
  form.subject_code = ''
  form.source_type = 'KNOWLEDGE'
  form.source_id = ''
  form.source_label = ''
  form.description = ''
  form.allow_redo = false
  form.target_question_count = 1
  form.due_at = ''
  form.status = 'PUBLISHED'
  form.class_ids = []
  sourceResourceOptions.value = []
}

function syncSourceTypeByTaskType() {
  const matched = taskTypeOptions.find((item) => item.value === form.task_type)
  if (matched?.sourceType) {
    form.source_type = matched.sourceType
  }
  form.source_id = ''
  form.source_label = ''
}

function handleSourceResourceChange(value) {
  const normalizedValue = toText(value)
  const matched = sourceResourceOptions.value.find((item) => item.value === normalizedValue)
  form.source_id = normalizedValue
  form.source_label = matched?.label || ''
}

async function handleCreate() {
  if (!toText(form.task_name)) {
    ElMessage.warning('请先填写任务名称。')
    return
  }
  if (!toText(form.subject_code)) {
    ElMessage.warning('请先选择考试科目。')
    return
  }
  if (!Array.isArray(form.class_ids) || !form.class_ids.length) {
    ElMessage.warning('请至少选择一个班级。')
    return
  }
  saving.value = true
  try {
    await createExamTask({
      ...form,
      source_type: form.source_type,
    })
    ElMessage.success('考试任务已创建并下发到学生端。')
    createDialogVisible.value = false
    resetForm()
    await loadRows()
  } catch (error) {
    ElMessage.error(String(error?.response?.data?.message || error?.message || '考试任务创建失败'))
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  await Promise.all([loadDictionary(), loadRows()])
})

watch(
  () => [form.task_type, form.subject_code],
  async () => {
    await loadSourceResourceOptions()
  },
)
</script>

<template>
  <section class="teacher-exam-task-page" v-loading="loading">
    <header class="teacher-exam-task-page__hero">
      <div>
        <p class="teacher-exam-task-page__eyebrow">教师端 / 考试任务管理</p>
        <h2>把章节练习、专项练习、模拟卷和主观题批改任务统一发布给学生</h2>
      </div>
      <el-button type="primary" @click="createDialogVisible = true">新建考试任务</el-button>
    </header>

    <section class="teacher-exam-task-page__filters">
      <el-select v-model="filters.status" clearable placeholder="状态" @change="loadRows">
        <el-option v-for="item in statusOptions" :key="item.value || 'all'" :label="item.label" :value="item.value" />
      </el-select>
      <el-select v-model="filters.taskType" clearable placeholder="任务类型" @change="loadRows">
        <el-option v-for="item in taskTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
      </el-select>
    </section>

    <el-table :data="rows" border stripe empty-text="暂时还没有考试任务">
      <el-table-column prop="taskName" label="任务名称" min-width="220" />
      <el-table-column label="任务类型" min-width="120">
        <template #default="{ row }">
          {{ taskTypeLabel(row.taskType) }}
        </template>
      </el-table-column>
      <el-table-column label="状态" width="120">
        <template #default="{ row }">
          <el-tag :type="statusTagType(row.status)" effect="light">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="subjectCode" label="科目" min-width="140" />
      <el-table-column prop="dueAt" label="截止时间" min-width="180">
        <template #default="{ row }">
          {{ formatDateTime(row.dueAt) }}
        </template>
      </el-table-column>
      <el-table-column label="发布对象" min-width="180">
        <template #default="{ row }">
          {{ Number(row?.assignmentSummary?.total || 0) }} 名学生 / {{ Number(row?.targets?.length || 0) }} 个目标
        </template>
      </el-table-column>
      <el-table-column prop="teacherName" label="老师" min-width="120" />
    </el-table>

    <el-dialog v-model="createDialogVisible" title="新建考试任务" width="720px" @closed="resetForm">
      <div class="teacher-exam-task-form">
        <el-form label-position="top">
          <el-form-item label="任务名称">
            <el-input v-model="form.task_name" placeholder="例如：政治第一章课后巩固" />
          </el-form-item>
          <div class="teacher-exam-task-form__grid">
            <el-form-item label="任务类型">
              <el-select v-model="form.task_type" placeholder="请选择任务类型" @change="syncSourceTypeByTaskType">
                <el-option v-for="item in taskTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
            </el-form-item>
            <el-form-item label="考试科目">
              <el-select v-model="form.subject_code" filterable placeholder="请选择考试科目">
                <el-option
                  v-for="item in subjectOptions"
                  :key="item.subjectCode || item.id"
                  :label="item.subjectName || item.name || item.subjectCode || item.id"
                  :value="item.subjectCode || item.id"
                />
              </el-select>
            </el-form-item>
          </div>
          <div class="teacher-exam-task-form__grid">
            <el-form-item :label="sourceFieldLabel">
              <el-select
                v-if="['PAPER', 'CHAPTER', 'SPECIAL', 'SUBJECTIVE_MARKING'].includes(form.task_type)"
                v-model="form.source_id"
                filterable
                clearable
                :placeholder="sourceSelectPlaceholder"
                @change="handleSourceResourceChange"
              >
                <el-option
                  v-for="item in sourceResourceOptions"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                />
              </el-select>
              <el-input v-else v-model="form.source_id" placeholder="填写关联资源 ID，先打通真实任务链路" />
            </el-form-item>
            <el-form-item label="来源名称">
              <el-input v-model="form.source_label" placeholder="填写资源名称，方便学生识别" />
            </el-form-item>
          </div>
          <el-form-item label="下发班级">
            <el-select v-model="form.class_ids" multiple collapse-tags filterable placeholder="选择要下发的班级">
              <el-option
                v-for="item in classOptions"
                :key="item.value || item.classId || item.class_id"
                :label="item.label || item.className || item.class_name || item.value"
                :value="item.value || item.classId || item.class_id"
              />
            </el-select>
          </el-form-item>
          <div class="teacher-exam-task-form__grid">
            <el-form-item label="截止时间">
              <el-input v-model="form.due_at" placeholder="例如：2026-03-31T23:59:00Z" />
            </el-form-item>
            <el-form-item label="状态">
              <el-select v-model="form.status">
                <el-option label="已发布" value="PUBLISHED" />
                <el-option label="草稿" value="DRAFT" />
              </el-select>
            </el-form-item>
          </div>
          <el-form-item v-if="form.task_type === 'CHAPTER' || form.task_type === 'SPECIAL' || form.task_type === 'SUBJECTIVE_MARKING'" label="完成目标题量">
            <el-input-number v-model="form.target_question_count" :min="1" :max="200" />
          </el-form-item>
          <el-form-item label="作业说明">
            <el-input v-model="form.description" :rows="4" maxlength="1000" show-word-limit type="textarea" />
          </el-form-item>
          <el-form-item label="允许重做">
            <el-switch v-model="form.allow_redo" />
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleCreate">创建并发布</el-button>
      </template>
    </el-dialog>
  </section>
</template>

<style scoped>
.teacher-exam-task-page {
  display: grid;
  gap: 20px;
}

.teacher-exam-task-page__hero {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 24px;
  border-radius: 24px;
  background: linear-gradient(135deg, var(--qb-success-soft-bg) 0%, var(--qb-primary-soft-bg) 100%);
}

.teacher-exam-task-page__eyebrow {
  margin: 0 0 8px;
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--qb-text-success-ink);
}

.teacher-exam-task-page__hero h2 {
  margin: 0;
  font-size: 24px;
  line-height: 1.4;
}

.teacher-exam-task-page__filters {
  display: flex;
  gap: 12px;
}

.teacher-exam-task-form {
  padding-top: 8px;
}

.teacher-exam-task-form__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

@media (max-width: 768px) {
  .teacher-exam-task-page__hero,
  .teacher-exam-task-page__filters,
  .teacher-exam-task-form__grid {
    display: grid;
  }
}
</style>
