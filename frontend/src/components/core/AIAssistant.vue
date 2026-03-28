<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ElMessage } from '@/ui/feedback'
import {
  fetchTaskList,
  submitAiMarkingTask,
  submitAiTutorTask,
} from '../../api/services/student'

const props = defineProps({
  questionOptions: {
    type: Array,
    default: () => [],
  },
  defaultQuestionId: {
    type: String,
    default: '',
  },
})

const panelVisible = ref(false)
const sending = ref(false)
const refreshingTasks = ref(false)
const currentQuestionId = ref('')
const mode = ref('AI_TUTOR')
const prompt = ref('')
const aiMarkingAnswer = ref('')
const taskRows = ref([])
const pollTimer = ref(0)
const conversationRows = ref([])

const pendingTaskCount = computed(() =>
  taskRows.value.filter((taskItem) => taskItem.status === 'QUEUED' || taskItem.status === 'RUNNING').length,
)

const questionIdOptions = computed(() =>
  (Array.isArray(props.questionOptions) ? props.questionOptions : []).map((questionItem) => ({
    questionId: String(questionItem?.id || ''),
    label: `${String(questionItem?.stem || '-').slice(0, 26)} · ${String(questionItem?.type || '')}`,
    type: String(questionItem?.type || ''),
  })),
)

const selectedQuestionType = computed(() => {
  const matched = questionIdOptions.value.find(
    (optionItem) => optionItem.questionId === String(currentQuestionId.value || ''),
  )
  return matched?.type || ''
})

const canUseAiMarking = computed(() => selectedQuestionType.value === 'subjective')

function taskStatusLabel(status) {
  if (status === 'QUEUED') {
    return '排队中'
  }
  if (status === 'RUNNING') {
    return '执行中'
  }
  if (status === 'COMPLETED') {
    return '已完成'
  }
  if (status === 'FAILED') {
    return '失败'
  }
  if (status === 'CANCELLED') {
    return '已取消'
  }
  return status || '-'
}

function parseExt(extJson) {
  try {
    const parsed = JSON.parse(String(extJson || '{}'))
    return parsed && typeof parsed === 'object' ? parsed : {}
  } catch (error) {
    return {}
  }
}

async function refreshTaskQueue() {
  refreshingTasks.value = true
  try {
    const pageData = await fetchTaskList({
      page: 1,
      size: 20,
      status: '',
      questionId: '',
    })
    taskRows.value = (pageData.items || []).map((taskItem) => {
      const ext = parseExt(taskItem.extJson)
      return {
        ...taskItem,
        resultSummary: String(ext.resultSummary || ''),
        queueName: String(ext?.queue?.queueName || ''),
      }
    })
  } catch (error) {
    ElMessage.error(error?.response?.data?.message || error?.message || '任务队列刷新失败')
  } finally {
    refreshingTasks.value = false
  }
}

function startPolling() {
  stopPolling()
  pollTimer.value = window.setInterval(() => {
    refreshTaskQueue()
  }, 3000)
}

function stopPolling() {
  if (pollTimer.value) {
    window.clearInterval(pollTimer.value)
    pollTimer.value = 0
  }
}

function togglePanel() {
  panelVisible.value = !panelVisible.value
}

async function sendMessage() {
  if (!currentQuestionId.value) {
    ElMessage.warning('请先选择一道题目')
    return
  }
  if (mode.value === 'AI_MARKING' && !canUseAiMarking.value) {
    ElMessage.warning('AI 批改仅支持主观题')
    return
  }
  if (mode.value === 'AI_TUTOR' && !String(prompt.value || '').trim()) {
    ElMessage.warning('请输入你的提问内容')
    return
  }
  if (mode.value === 'AI_MARKING' && !String(aiMarkingAnswer.value || '').trim()) {
    ElMessage.warning('请填写用于批改的答案')
    return
  }

  sending.value = true
  try {
    let taskResponse = {}
    if (mode.value === 'AI_TUTOR') {
      taskResponse = await submitAiTutorTask(currentQuestionId.value, {
        prompt: String(prompt.value || '').trim(),
        promptImageUrl: '',
      })
      conversationRows.value.push({
        role: 'user',
        content: String(prompt.value || '').trim(),
        createTime: new Date().toISOString(),
      })
      prompt.value = ''
    } else {
      taskResponse = await submitAiMarkingTask(currentQuestionId.value, {
        answer: String(aiMarkingAnswer.value || '').trim(),
        answerImageUrl: '',
      })
      conversationRows.value.push({
        role: 'user',
        content: `请批改：${String(aiMarkingAnswer.value || '').trim()}`,
        createTime: new Date().toISOString(),
      })
      aiMarkingAnswer.value = ''
    }

    conversationRows.value.push({
      role: 'assistant',
      content: `任务已提交，任务号 ${taskResponse.id || '-'}。`,
      createTime: new Date().toISOString(),
    })
    ElMessage.success('AI 任务已提交')
    await refreshTaskQueue()
  } catch (error) {
    ElMessage.error(error?.response?.data?.message || error?.message || 'AI 任务提交失败')
  } finally {
    sending.value = false
  }
}

watch(
  () => props.defaultQuestionId,
  (value) => {
    if (!currentQuestionId.value && value) {
      currentQuestionId.value = String(value)
    }
  },
  { immediate: true },
)

watch(
  () => props.questionOptions,
  (value) => {
    if (!currentQuestionId.value && Array.isArray(value) && value.length) {
      currentQuestionId.value = String(value[0]?.id || '')
    }
  },
  { immediate: true, deep: true },
)

watch(
  () => panelVisible.value,
  (visible) => {
    if (visible) {
      refreshTaskQueue()
      startPolling()
    } else {
      stopPolling()
    }
  },
)

onMounted(() => {
  startPolling()
})

onBeforeUnmount(() => {
  stopPolling()
})
</script>

<template>
  <button
    type="button"
    class="assistant-fab"
    @click="togglePanel"
  >
    <el-badge
      :value="pendingTaskCount"
      :hidden="pendingTaskCount <= 0"
      class="assistant-badge"
    >
      <span>AI 助手</span>
    </el-badge>
  </button>

  <transition name="assistant-slide">
    <section
      v-if="panelVisible"
      class="assistant-panel"
    >
      <header class="assistant-header">
        <div>
          <h4>沉浸式 AI 助手</h4>
          <p>对话 + 异步任务队列实时可见</p>
        </div>
        <el-button type="primary" plain @click="togglePanel">收起</el-button>
      </header>

      <div class="assistant-form">
        <el-select
          v-model="currentQuestionId"
          placeholder="选择题目"
        >
          <el-option
            v-for="optionItem in questionIdOptions"
            :key="optionItem.questionId"
            :label="optionItem.label"
            :value="optionItem.questionId"
          />
        </el-select>
        <el-radio-group v-model="mode">
          <el-radio-button label="AI_TUTOR">答疑</el-radio-button>
          <el-radio-button label="AI_MARKING">批改</el-radio-button>
        </el-radio-group>
        <el-input
          v-if="mode === 'AI_TUTOR'"
          v-model="prompt"
          type="textarea"
          :rows="3"
          placeholder="输入你的疑问，支持多轮追问"
        />
        <el-input
          v-else
          v-model="aiMarkingAnswer"
          type="textarea"
          :rows="3"
          :placeholder="canUseAiMarking ? '输入主观题答案用于 AI 批改' : '当前题型不支持 AI 批改'"
          :disabled="!canUseAiMarking"
        />
        <el-button
          type="primary"
          :loading="sending"
          @click="sendMessage"
        >
          发送任务
        </el-button>
      </div>

      <section class="conversation">
        <h5>对话区</h5>
        <el-empty
          v-if="!conversationRows.length"
          description="还没有对话，发送首条消息开始"
        />
        <article
          v-for="(conversationItem, index) in conversationRows"
          :key="`${conversationItem.createTime}-${index}`"
          :class="['bubble', conversationItem.role]"
        >
          {{ conversationItem.content }}
        </article>
      </section>

      <section class="task-queue">
        <header class="task-header">
          <h5>AI 异步任务队列</h5>
          <el-button
            text
            :loading="refreshingTasks"
            @click="refreshTaskQueue"
          >
            刷新
          </el-button>
        </header>
        <el-empty
          v-if="!taskRows.length"
          description="暂无任务"
        />
        <article
          v-for="taskItem in taskRows"
          :key="taskItem.id"
          class="task-card"
        >
          <div class="task-top">
            <strong>{{ taskItem.type }}</strong>
            <el-tag size="small" :type="taskItem.status === 'COMPLETED' ? 'success' : 'warning'">
              {{ taskStatusLabel(taskItem.status) }}
            </el-tag>
          </div>
          <el-progress :percentage="Number(taskItem.progress || 0)" :stroke-width="10" />
          <p>任务ID：{{ taskItem.id }}</p>
          <p>队列：{{ taskItem.queueName || '-' }}</p>
          <p>摘要：{{ taskItem.resultSummary || '任务进行中...' }}</p>
        </article>
      </section>
    </section>
  </transition>
</template>

<style scoped>
.assistant-fab {
  position: fixed;
  right: 26px;
  bottom: 26px;
  z-index: 1200;
  border: none;
  border-radius: 999px;
  padding: 12px 18px;
  background: linear-gradient(140deg, var(--el-color-primary), var(--el-color-primary));
  color: var(--qb-bg-card);
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 10px 24px rgba(37, 99, 235, 0.35);
}

.assistant-panel {
  position: fixed;
  top: 20px;
  right: 20px;
  bottom: 20px;
  width: min(420px, calc(100vw - 40px));
  z-index: 1199;
  border-radius: 16px;
  border: 1px solid var(--qb-primary-soft-border);
  background: linear-gradient(180deg, var(--qb-bg-card), var(--qb-primary-soft-bg));
  box-shadow: 0 18px 36px rgba(15, 23, 42, 0.2);
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow-y: auto;
}

.assistant-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.assistant-header h4,
.assistant-header p {
  margin: 0;
}

.assistant-header p {
  margin-top: 4px;
  color: var(--qb-text-secondary);
  font-size: 12px;
}

.assistant-form {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.conversation,
.task-queue {
  border-radius: 12px;
  border: 1px solid var(--qb-primary-soft-border);
  background: var(--qb-bg-card);
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.conversation h5,
.task-queue h5 {
  margin: 0;
  color: var(--qb-text-heading);
}

.bubble {
  padding: 8px 10px;
  border-radius: 12px;
  font-size: 13px;
  line-height: 1.5;
}

.bubble.user {
  align-self: flex-end;
  background: var(--qb-primary-soft-border);
  color: var(--el-color-primary);
}

.bubble.assistant {
  align-self: flex-start;
  background: var(--qb-primary-soft-bg);
  color: var(--el-color-primary);
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.task-card {
  border-radius: 10px;
  border: 1px solid var(--qb-border-muted);
  background: var(--qb-bg-muted);
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.task-card p {
  margin: 0;
  color: var(--qb-text-secondary);
  font-size: 12px;
}

.task-top {
  display: flex;
  justify-content: space-between;
  gap: 8px;
}

.assistant-slide-enter-active,
.assistant-slide-leave-active {
  transition: transform 0.2s ease, opacity 0.2s ease;
}

.assistant-slide-enter-from,
.assistant-slide-leave-to {
  transform: translateX(16px);
  opacity: 0;
}

@media (max-width: 860px) {
  .assistant-panel {
    top: 0;
    right: 0;
    bottom: 0;
    width: min(460px, 100vw);
    border-radius: 0;
    border-right: none;
  }
}
</style>
