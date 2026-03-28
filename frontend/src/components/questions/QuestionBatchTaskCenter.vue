<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
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
})

const emit = defineEmits(['restore-result'])
const router = useRouter()

const loading = ref(false)
const taskRows = ref([])
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

function parseEnvelopeData(response) {
  if (response && typeof response === 'object' && 'data' in response) {
    return response.data
  }
  return response
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
    return {
      taskId: String(item?.taskId || item?.task_id || item?.id || '').trim(),
      status: String(item?.status || '').trim(),
      progress: Number(item?.progress || 0),
      updateTime: String(item?.updateTime || item?.update_time || '').trim(),
      fileName: String(requestPayload?.fileName || '').trim(),
      resultSummary: String(extJson?.resultSummary || '').trim(),
      validCount: Number(result?.valid_count || 0),
      invalidCount: Number(result?.invalid_count || 0),
      result,
    }
  })
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

async function loadTasks() {
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

defineExpose({
  reload: loadTasks,
})
</script>

<template>
  <section class="task-center" :class="{ embedded }">
    <header class="task-center-header">
      <div>
        <h4>批量导入任务中心</h4>
        <p>支持按状态和关键词筛选，并进入独立详情页查看解析结果和回滚信息。</p>
      </div>
      <el-button plain :loading="loading" @click="loadTasks">刷新任务</el-button>
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

.task-filter-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 180px;
  gap: 12px;
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
