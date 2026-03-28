<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage } from '@/ui/feedback'
import { useRouter } from 'vue-router'
import { deleteQuestionsBatch, fetchQuestionDetail, getTask } from '../../api/services/questionBank'

const props = defineProps({
  taskId: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['restore-result'])
const router = useRouter()

const loading = ref(false)
const rollbackLoading = ref(false)
const taskRow = ref(null)
const rollbackDrawerVisible = ref(false)
const rollbackCandidateRows = ref([])

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

function normalizeTaskRow(item = {}) {
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
    rollbackStrategy: result?.rollbackStrategy && typeof result.rollbackStrategy === 'object'
      ? result.rollbackStrategy
      : null,
  }
}

const resultRows = computed(() => {
  const result = taskRow.value?.result && typeof taskRow.value.result === 'object'
    ? taskRow.value.result
    : {}
  return Array.isArray(result?.items) ? result.items : []
})

const errorRows = computed(() => {
  const result = taskRow.value?.result && typeof taskRow.value.result === 'object'
    ? taskRow.value.result
    : {}
  return Array.isArray(result?.errors) ? result.errors : []
})

const createFailureRows = computed(() => {
  const result = taskRow.value?.result && typeof taskRow.value.result === 'object'
    ? taskRow.value.result
    : {}
  return Array.isArray(result?.createFailures) ? result.createFailures : []
})

const createdQuestionIds = computed(() => {
  const result = taskRow.value?.result && typeof taskRow.value.result === 'object'
    ? taskRow.value.result
    : {}
  const direct_ids = Array.isArray(result?.createdQuestionIds) ? result.createdQuestionIds : []
  if (direct_ids.length) {
    return direct_ids.map((item) => String(item || '').trim()).filter((item) => Boolean(item))
  }
  const rollback_ids = Array.isArray(taskRow.value?.rollbackStrategy?.questionIds)
    ? taskRow.value.rollbackStrategy.questionIds
    : []
  return rollback_ids.map((item) => String(item || '').trim()).filter((item) => Boolean(item))
})

async function loadTask() {
  const normalizedTaskId = String(props.taskId || '').trim()
  if (!normalizedTaskId) {
    taskRow.value = null
    return
  }
  loading.value = true
  try {
    const response = await getTask(normalizedTaskId)
    taskRow.value = normalizeTaskRow(parseEnvelopeData(response) || {})
  } catch (error) {
    taskRow.value = null
    ElMessage.error(String(error?.response?.data?.message || error?.message || '任务详情加载失败'))
  } finally {
    loading.value = false
  }
}

function restoreResult() {
  if (!taskRow.value) {
    return
  }
  emit('restore-result', {
    taskId: taskRow.value.taskId,
    status: taskRow.value.status,
    progress: taskRow.value.progress,
    summary: taskRow.value.resultSummary,
    result: taskRow.value.result || {},
  })
  ElMessage.success('已恢复该任务解析结果。')
}

async function viewRollbackCandidates() {
  const questionIds = Array.isArray(taskRow.value?.rollbackStrategy?.questionIds) ? taskRow.value.rollbackStrategy.questionIds : []
  if (!questionIds.length) {
    ElMessage.warning('当前任务暂无可回滚候选题目。')
    return
  }
  rollbackLoading.value = true
  try {
    const details = await Promise.all(
      questionIds.map(async (questionId) => {
        const payload = await fetchQuestionDetail(questionId)
        return {
          id: String(payload?.id || questionId),
          stem: String(payload?.stem || '-'),
          type: String(payload?.type || '-'),
          status: String(payload?.status || '-'),
        }
      }),
    )
    rollbackCandidateRows.value = details
    rollbackDrawerVisible.value = true
  } catch (error) {
    rollbackCandidateRows.value = []
    ElMessage.error(String(error?.response?.data?.message || error?.message || '回滚候选题目加载失败'))
  } finally {
    rollbackLoading.value = false
  }
}

async function runRollback() {
  const questionIds = Array.isArray(taskRow.value?.rollbackStrategy?.questionIds) ? taskRow.value.rollbackStrategy.questionIds : []
  if (!questionIds.length) {
    ElMessage.warning('当前任务没有可回滚题目。')
    return
  }
  try {
    const response = await deleteQuestionsBatch({
      question_ids: questionIds,
    })
    const payload = parseEnvelopeData(response) || {}
    ElMessage.success(`已触发批量回滚，撤销快照：${String(payload?.undoSnapshotId || '').trim() || '已生成'}`)
    rollbackDrawerVisible.value = false
  } catch (error) {
    ElMessage.error(String(error?.response?.data?.message || error?.message || '批量回滚失败'))
  }
}

function openCreatedQuestions() {
  if (!createdQuestionIds.value.length) {
    ElMessage.warning('当前任务还没有已入库题目。')
    return
  }
  router.push({
    name: 'teacherQuestions',
    query: {
      questionIds: createdQuestionIds.value.join(','),
      sourceTaskId: String(taskRow.value?.taskId || '').trim(),
      source: 'import-history',
    },
  })
}

watch(
  () => props.taskId,
  () => {
    loadTask()
  },
  { immediate: true },
)

onMounted(() => {
  loadTask()
})

defineExpose({
  reload: loadTask,
})
</script>

<template>
  <section class="task-detail" v-loading="loading">
    <el-empty v-if="!taskRow" description="当前任务不存在或已失效。" />

    <template v-else>
      <section class="detail-grid">
        <article class="summary-card">
          <span>任务ID</span>
          <strong>{{ taskRow.taskId }}</strong>
        </article>
        <article class="summary-card">
          <span>状态</span>
          <strong>{{ taskRow.status }}</strong>
        </article>
        <article class="summary-card">
          <span>进度</span>
          <strong>{{ taskRow.progress }}%</strong>
        </article>
        <article class="summary-card">
          <span>文件名</span>
          <strong>{{ taskRow.fileName || '-' }}</strong>
        </article>
        <article class="summary-card">
          <span>有效题数</span>
          <strong>{{ taskRow.validCount }}</strong>
        </article>
        <article class="summary-card">
          <span>异常题数</span>
          <strong>{{ taskRow.invalidCount }}</strong>
        </article>
        <article class="summary-card">
          <span>已入库题数</span>
          <strong>{{ createdQuestionIds.length }}</strong>
        </article>
      </section>

      <el-alert
        v-if="taskRow.resultSummary"
        type="info"
        :closable="false"
        :title="taskRow.resultSummary"
      />

      <section class="detail-section">
        <div class="detail-section-head">
          <h5>解析结果预览</h5>
          <div class="inline-actions">
            <el-button
              type="success"
              plain
              :disabled="!resultRows.length"
              @click="restoreResult"
            >
              恢复到预览区
            </el-button>
            <el-button
              plain
              :disabled="!(taskRow.rollbackStrategy && Array.isArray(taskRow.rollbackStrategy.questionIds) && taskRow.rollbackStrategy.questionIds.length)"
              @click="viewRollbackCandidates"
            >
              查看回滚候选
            </el-button>
            <el-button
              type="primary"
              :disabled="!createdQuestionIds.length"
              @click="openCreatedQuestions"
            >
              查看已入库题目
            </el-button>
          </div>
        </div>
        <el-empty v-if="!resultRows.length" description="当前任务暂无可恢复的解析结果。" />
        <el-table v-else :data="resultRows" border size="small">
          <el-table-column prop="title" label="题目标题" min-width="180" show-overflow-tooltip />
          <el-table-column prop="content" label="题干" min-width="260" show-overflow-tooltip />
          <el-table-column prop="path_label" label="标签路径" min-width="260" show-overflow-tooltip />
          <el-table-column label="置信度" width="100">
            <template #default="scope">
              {{ Math.round(Number(scope.row.confidence || 0) * 100) }}%
            </template>
          </el-table-column>
        </el-table>
      </section>

      <section class="detail-section">
        <div class="detail-section-head">
          <h5>异常列表</h5>
        </div>
        <el-empty v-if="!errorRows.length" description="当前任务暂无异常记录。" />
        <el-table
          v-else
          :data="errorRows.map((message, index) => ({ id: index + 1, message }))"
          border
          size="small"
        >
          <el-table-column prop="id" label="#" width="60" />
          <el-table-column prop="message" label="异常信息" min-width="420" show-overflow-tooltip />
        </el-table>
      </section>

      <section class="detail-section">
        <div class="detail-section-head">
          <h5>入库失败列表</h5>
        </div>
        <el-empty v-if="!createFailureRows.length" description="当前任务暂无入库失败记录。" />
        <el-table
          v-else
          :data="createFailureRows"
          border
          size="small"
        >
          <el-table-column prop="index" label="#" width="60" />
          <el-table-column prop="title" label="题目标题" min-width="180" show-overflow-tooltip />
          <el-table-column prop="message" label="失败原因" min-width="320" show-overflow-tooltip />
        </el-table>
      </section>

      <section class="detail-section">
        <div class="detail-section-head">
          <h5>回滚策略</h5>
        </div>
        <p class="rollback-text">{{ taskRow.rollbackStrategy?.message || '当前任务暂无回滚信息。' }}</p>
      </section>
    </template>

    <el-drawer v-model="rollbackDrawerVisible" title="回滚候选题目" size="55%">
      <el-table :data="rollbackCandidateRows" border v-loading="rollbackLoading">
        <el-table-column prop="id" label="题目ID" min-width="160" />
        <el-table-column prop="stem" label="题干" min-width="260" show-overflow-tooltip />
        <el-table-column prop="type" label="题型" width="120" />
        <el-table-column prop="status" label="状态" width="120" />
      </el-table>
      <template #footer>
        <div class="drawer-actions">
          <el-button @click="rollbackDrawerVisible = false">关闭</el-button>
          <el-button
            type="danger"
            :disabled="!rollbackCandidateRows.length"
            @click="runRollback"
          >
            一键回滚候选题目
          </el-button>
        </div>
      </template>
    </el-drawer>
  </section>
</template>

<style scoped>
.task-detail {
  display: grid;
  gap: 12px;
}

.detail-grid {
  display: grid;
  gap: 10px;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
}

.summary-card {
  border: 1px solid var(--qb-primary-soft-border);
  border-radius: 12px;
  background: var(--qb-primary-soft-bg);
  padding: 12px;
  display: grid;
  gap: 6px;
}

.summary-card strong {
  font-size: 18px;
}

.detail-section {
  display: grid;
  gap: 10px;
}

.detail-section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.detail-section-head h5,
.rollback-text {
  margin: 0;
}

.inline-actions,
.drawer-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.rollback-text {
  color: var(--qb-text-subtle-8);
}
</style>
