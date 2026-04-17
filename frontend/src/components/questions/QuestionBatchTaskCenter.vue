<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from '@/ui/feedback'
import { useRouter } from 'vue-router'
import { getTask, listTasks } from '../../api/services/questionBank'

const props = defineProps({
  embedded: {
    type: Boolean,
    default: false,
  },
  detailRouteName: {
    type: String,
    default: 'teacherImportHistoryDetail',
  },
  latestTaskId: {
    type: String,
    default: '',
  },
  currentUserId: {
    type: String,
    default: '',
  },
  latestTaskSnapshot: {
    type: Object,
    default: null,
  },
})

const emit = defineEmits(['restore-result'])
const router = useRouter()

const loading = ref(false)
const taskRows = ref([])
const selectedTaskId = ref('')
const filters = reactive({
  keyword: '',
  status: '',
})

const statusOptions = [
  { label: '全部状态', value: '' },
  { label: '排队中', value: 'QUEUED' },
  { label: '执行中', value: 'RUNNING' },
  { label: '已完成', value: 'COMPLETED' },
  { label: '失败', value: 'FAILED' },
  { label: '已取消', value: 'CANCELLED' },
]

const statusLabelMap = {
  QUEUED: '排队中',
  RUNNING: '执行中',
  COMPLETED: '已完成',
  FAILED: '失败',
  CANCELLED: '已取消',
}

function parseEnvelopeData(response) {
  if (response && typeof response === 'object' && 'data' in response) {
    return response.data
  }
  return response
}

function resolveBackendErrorCode(error) {
  return String(error?.response?.data?.code || error?.response?.data?.errorCode || '').trim().toUpperCase()
}

function parseTaskExt(taskPayload = {}) {
  if (taskPayload?.extJson && typeof taskPayload.extJson === 'object') {
    return taskPayload.extJson
  }
  if (typeof taskPayload?.extJson !== 'string') {
    return {}
  }
  try {
    const parsed = JSON.parse(taskPayload.extJson)
    return parsed && typeof parsed === 'object' ? parsed : {}
  } catch (error) {
    return {}
  }
}

function normalizeTaskRows(items = []) {
  const rows = Array.isArray(items) ? items : []
  return rows.map((item) => {
    const extJson = parseTaskExt(item)
    const result = extJson?.result && typeof extJson.result === 'object' ? extJson.result : {}
    const requestPayload = extJson?.requestPayload && typeof extJson.requestPayload === 'object'
      ? extJson.requestPayload
      : {}
    const taskId = String(item?.taskId || item?.task_id || item?.id || '').trim()
    return {
      taskId,
      status: String(item?.status || '').trim(),
      progress: Number(item?.progress || 0),
      updateTime: String(item?.updateTime || item?.update_time || '').trim(),
      fileName: String(requestPayload?.fileName || '').trim(),
      taskName: String(requestPayload?.fileName || '').trim() || `任务 ${taskId || '-'}`,
      resultSummary: String(extJson?.resultSummary || '').trim(),
      validCount: Number(result?.valid_count || 0),
      invalidCount: Number(result?.invalid_count || 0),
      result,
    }
  })
}

function normalizeTaskSnapshot(snapshot = null) {
  if (!snapshot || typeof snapshot !== 'object') {
    return null
  }
  const taskId = String(snapshot.taskId || snapshot.id || '').trim()
  if (!taskId) {
    return null
  }
  return {
    taskId,
    status: String(snapshot.status || '').trim(),
    progress: Number(snapshot.progress || 0),
    updateTime: String(snapshot.updateTime || '').trim(),
    fileName: String(snapshot.fileName || '').trim(),
    taskName: String(snapshot.taskName || snapshot.fileName || '').trim() || `任务 ${taskId}`,
    resultSummary: String(snapshot.resultSummary || snapshot.summary || '').trim(),
    validCount: Number(snapshot.validCount || 0),
    invalidCount: Number(snapshot.invalidCount || 0),
    result: snapshot.result && typeof snapshot.result === 'object' ? snapshot.result : {},
  }
}

const filteredTaskRows = computed(() => {
  const keyword = String(filters.keyword || '').trim().toLowerCase()
  const status = String(filters.status || '').trim()
  return taskRows.value.filter((row) => {
    if (status && row.status !== status) {
      return false
    }
    if (!keyword) {
      return true
    }
    const haystack = [row.taskId, row.fileName, row.resultSummary].join(' ').toLowerCase()
    return haystack.includes(keyword)
  })
})

const quickTaskRows = computed(() =>
  filteredTaskRows.value.map((row) => ({
    ...row,
    taskName: String(row.taskName || row.fileName || '').trim() || `任务 ${row.taskId || '-'}`,
    statusLabel: statusLabelMap[String(row.status || '').trim()] || String(row.status || '-'),
  })),
)

const activeTaskRow = computed(() => {
  const taskId = String(selectedTaskId.value || '').trim()
  if (!taskId) {
    return quickTaskRows.value[0] || null
  }
  return quickTaskRows.value.find((row) => String(row.taskId || '').trim() === taskId) || quickTaskRows.value[0] || null
})

function taskStatusTagType(status = '') {
  const normalized = String(status || '').trim()
  if (normalized === 'COMPLETED') return 'success'
  if (normalized === 'FAILED' || normalized === 'CANCELLED') return 'danger'
  if (normalized === 'RUNNING') return 'warning'
  if (normalized === 'QUEUED') return 'info'
  return 'info'
}

function selectTaskRow(row) {
  selectedTaskId.value = String(row?.taskId || '').trim()
}

function extractTaskIdCandidates(rawValue = '') {
  const normalized = String(rawValue || '').trim()
  if (!normalized) {
    return []
  }
  const matched = normalized.match(/\btask-[A-Za-z0-9_-]+\b/g) || []
  return Array.from(new Set(matched.map((item) => String(item || '').trim()).filter((item) => item)))
}

const hintedTaskIds = computed(() => {
  const latestTaskIds = extractTaskIdCandidates(props.latestTaskId)
  const keywordTaskIds = extractTaskIdCandidates(filters.keyword)
  return Array.from(new Set([...latestTaskIds, ...keywordTaskIds]))
})

async function hydrateMissingTasksByIds(taskIds = [], { notifyForbidden = false } = {}) {
  const normalizedTaskIds = Array.from(
    new Set(
      (Array.isArray(taskIds) ? taskIds : [])
        .map((item) => String(item || '').trim())
        .filter((item) => item),
    ),
  )
  if (!normalizedTaskIds.length) {
    return
  }
  let hasForbiddenTask = false
  for (const taskId of normalizedTaskIds) {
    const alreadyLoaded = taskRows.value.some((row) => String(row?.taskId || '').trim() === taskId)
    if (alreadyLoaded) {
      continue
    }
    try {
      const response = await getTask(taskId)
      const payload = parseEnvelopeData(response) || {}
      if (payload && typeof payload === 'object') {
        upsertTaskRow(payload)
      }
    } catch (error) {
      if (resolveBackendErrorCode(error) === 'TASK_FORBIDDEN') {
        hasForbiddenTask = true
      }
    }
  }
  if (notifyForbidden && hasForbiddenTask) {
    ElMessage.warning('该任务属于其他账号，请确认当前登录账号后再刷新任务。')
  }
}

async function loadTasks() {
  const latestSnapshotRow = normalizeTaskSnapshot(props.latestTaskSnapshot)
  if (latestSnapshotRow) {
    upsertTaskRow(latestSnapshotRow)
  }
  loading.value = true
  try {
    const response = await listTasks({
      page: 1,
      size: 50,
      type: 'QUESTION_BATCH_PARSE',
    })
    const payload = parseEnvelopeData(response) || {}
    const items = Array.isArray(payload?.items) ? payload.items : []
    taskRows.value = normalizeTaskRows(items)
  } catch (error) {
    taskRows.value = []
    ElMessage.error(String(error?.response?.data?.message || error?.message || '任务记录加载失败'))
  } finally {
    loading.value = false
  }
  if (latestSnapshotRow) {
    upsertTaskRow(latestSnapshotRow)
  }
  await hydrateMissingTasksByIds(hintedTaskIds.value, { notifyForbidden: true })
}

function upsertTaskRow(taskPayload = {}) {
  let nextRow = null
  if (taskPayload && typeof taskPayload === 'object' && !('id' in taskPayload) && 'taskId' in taskPayload && 'resultSummary' in taskPayload) {
    nextRow = normalizeTaskSnapshot(taskPayload)
  }
  if (!nextRow) {
    const normalizedRows = normalizeTaskRows([taskPayload])
    nextRow = normalizedRows[0]
  }
  if (!nextRow || !nextRow.taskId) {
    return
  }
  const nextTaskId = String(nextRow.taskId || '').trim()
  if (!nextTaskId) {
    return
  }
  const nextRows = [...taskRows.value]
  const existingIndex = nextRows.findIndex((item) => String(item?.taskId || '').trim() === nextTaskId)
  if (existingIndex >= 0) {
    nextRows.splice(existingIndex, 1, nextRow)
  } else {
    nextRows.unshift(nextRow)
  }
  taskRows.value = nextRows
}

async function reloadByTask(taskId = '') {
  const normalizedTaskId = String(taskId || '').trim()
  await loadTasks()
  if (!normalizedTaskId) {
    return
  }
  await hydrateMissingTasksByIds([normalizedTaskId], { notifyForbidden: false })
}

function handleRefresh() {
  filters.status = ''
  void loadTasks()
}

async function continuePolling(row) {
  const normalizedTaskId = String(row?.taskId || '').trim()
  if (!normalizedTaskId) {
    return
  }
  try {
    for (let attempt = 0; attempt < 12; attempt += 1) {
      const response = await getTask(normalizedTaskId)
      const taskPayload = parseEnvelopeData(response) || {}
      const taskStatus = String(taskPayload?.status || '').trim()
      if (taskStatus === 'COMPLETED') {
        const extJson = parseTaskExt(taskPayload)
        emit('restore-result', {
          taskId: normalizedTaskId,
          status: taskStatus,
          progress: Number(taskPayload?.progress || 100),
          summary: String(extJson?.resultSummary || '').trim(),
          result: extJson?.result || {},
        })
        await loadTasks()
        ElMessage.success('任务已完成，结果已可恢复。')
        return
      }
      if (taskStatus === 'FAILED' || taskStatus === 'CANCELLED') {
        throw new Error(String(taskPayload?.message || '任务执行失败'))
      }
      await new Promise((resolve) => window.setTimeout(resolve, 800))
    }
    ElMessage.warning('任务仍在处理中，请稍后刷新。')
  } catch (error) {
    ElMessage.error(String(error?.response?.data?.message || error?.message || '继续轮询失败'))
  }
}

function restoreResult(row) {
  emit('restore-result', {
    taskId: row.taskId,
    status: row.status,
    progress: row.progress,
    summary: row.resultSummary,
    result: row.result || {},
  })
  if (props.embedded) {
    ElMessage.success('已恢复该任务解析结果。')
  }
}

function openTaskDetail(row) {
  const taskId = String(row?.taskId || '').trim()
  if (!taskId) {
    return
  }
  if (props.embedded) {
    restoreResult(row)
    return
  }
  router.push({
    name: props.detailRouteName,
    params: {
      taskId,
    },
  })
}

onMounted(() => {
  loadTasks()
})

watch(
  () => String(props.latestTaskId || '').trim(),
  (taskId) => {
    if (!taskId) {
      return
    }
    const alreadyLoaded = taskRows.value.some((row) => String(row?.taskId || '').trim() === taskId)
    if (alreadyLoaded) {
      return
    }
    void reloadByTask(taskId)
  },
)

watch(
  () => props.latestTaskSnapshot,
  (snapshot) => {
    const row = normalizeTaskSnapshot(snapshot)
    if (!row) {
      return
    }
    upsertTaskRow(row)
  },
  { deep: true },
)

watch(
  () => quickTaskRows.value.map((row) => String(row.taskId || '').trim()).join(','),
  () => {
    const selected = String(selectedTaskId.value || '').trim()
    if (!selected && quickTaskRows.value.length) {
      selectedTaskId.value = String(quickTaskRows.value[0]?.taskId || '').trim()
      return
    }
    const exists = quickTaskRows.value.some((row) => String(row.taskId || '').trim() === selected)
    if (!exists) {
      selectedTaskId.value = String(quickTaskRows.value[0]?.taskId || '').trim()
    }
  },
  { immediate: true },
)

defineExpose({
  reload: loadTasks,
  reloadByTask,
})
</script>

<template>
  <section class="task-center" :class="{ embedded }">
    <header class="task-center-header">
      <div>
        <h4>批量导入任务中心</h4>
        <p>支持按状态和关键词筛选，并进入独立详情页查看解析结果和回滚信息。</p>
        <p v-if="currentUserId" class="task-center-account">当前登录账号：{{ currentUserId }}</p>
      </div>
      <el-button plain :loading="loading" @click="handleRefresh">刷新任务</el-button>
    </header>

    <section class="task-filter-row">
      <el-input v-model="filters.keyword" clearable placeholder="搜索任务ID / 文件名 / 摘要" />
      <el-select v-model="filters.status" clearable placeholder="任务状态">
        <el-option
          v-for="option in statusOptions"
          :key="option.value"
          :label="option.label"
          :value="option.value"
        />
      </el-select>
    </section>

    <section v-if="quickTaskRows.length" class="task-switch-list">
      <header class="task-switch-header">
        <strong>任务列表</strong>
        <span>共 {{ quickTaskRows.length }} 个</span>
      </header>
      <div class="task-switch-items">
        <button
          v-for="row in quickTaskRows"
          :key="row.taskId"
          type="button"
          class="task-switch-item"
          :class="{ active: String(activeTaskRow?.taskId || '') === String(row.taskId || '') }"
          @click="selectTaskRow(row)"
        >
          <span class="task-switch-name">{{ row.taskName }}</span>
          <el-tag size="small" :type="taskStatusTagType(row.status)">{{ row.statusLabel }}</el-tag>
        </button>
      </div>
      <p v-if="activeTaskRow" class="task-switch-current">
        当前任务：{{ activeTaskRow.taskName }} ｜ 当前状态：{{ activeTaskRow.statusLabel || activeTaskRow.status || '-' }}
      </p>
    </section>

    <el-empty v-if="!filteredTaskRows.length && !loading" description="当前暂无批量导入任务。" />
    <el-table v-else :data="filteredTaskRows" border size="small" v-loading="loading">
      <el-table-column prop="taskId" label="任务ID" min-width="150" />
      <el-table-column prop="fileName" label="文件名" min-width="180" show-overflow-tooltip />
      <el-table-column prop="status" label="状态" width="120" />
      <el-table-column prop="progress" label="进度(%)" width="100" />
      <el-table-column label="解析结果" min-width="220" show-overflow-tooltip>
        <template #default="scope">
          {{ scope.row.resultSummary || `有效 ${scope.row.validCount} / 异常 ${scope.row.invalidCount}` }}
        </template>
      </el-table-column>
      <el-table-column prop="updateTime" label="更新时间" min-width="180" />
      <el-table-column label="操作" width="260" fixed="right">
        <template #default="scope">
          <div class="inline-actions">
            <el-button
              v-if="scope.row.status !== 'COMPLETED'"
              type="primary"
              plain
              @click="continuePolling(scope.row)"
            >
              继续轮询
            </el-button>
            <el-button
              v-else
              type="success"
              plain
              @click="restoreResult(scope.row)"
            >
              恢复结果
            </el-button>
            <el-button plain @click="openTaskDetail(scope.row)">查看详情</el-button>
          </div>
        </template>
      </el-table-column>
    </el-table>
  </section>
</template>

<style scoped>
.task-center {
  display: grid;
  gap: 12px;
}

.task-center.embedded {
  margin-top: 8px;
}

.task-center-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.task-center-header h4,
.task-center-header p {
  margin: 0;
}

.task-center-header p {
  margin-top: 6px;
  color: var(--qb-text-subtle-8);
}

.task-center-account {
  margin-top: 4px;
  color: var(--qb-text-subtle-7);
  font-size: 12px;
}

.task-filter-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 180px;
  gap: 12px;
}

.task-switch-list {
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 10px;
  padding: 10px 12px;
  display: grid;
  gap: 8px;
  background: var(--el-fill-color-extra-light);
}

.task-switch-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.task-switch-items {
  display: grid;
  gap: 8px;
  max-height: 180px;
  overflow: auto;
  padding-right: 4px;
}

.task-switch-item {
  width: 100%;
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  padding: 8px 10px;
  background: var(--el-bg-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  cursor: pointer;
  transition: border-color 0.2s ease, background-color 0.2s ease;
}

.task-switch-item.active {
  border-color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
}

.task-switch-name {
  color: var(--el-text-color-primary);
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.task-switch-current {
  margin: 0;
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.inline-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

@media (max-width: 768px) {
  .task-center-header,
  .task-filter-row {
    grid-template-columns: 1fr;
    flex-direction: column;
  }
}
</style>
